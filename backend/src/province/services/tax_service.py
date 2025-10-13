"""
Tax Conversation Service using Strands SDK

This service orchestrates the conversational tax filing flow:
1. Agent asks questions gradually
2. Processes W2 data from existing bucket datasets
3. Fills forms progressively based on user responses
4. Handles document versioning
5. Saves completed forms to documents bucket
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from strands import Agent, tool

from ..core.config import get_settings
from ..agents.tax.tools.ingest_w2 import ingest_w2
from ..agents.tax.tools.calc_1040 import calc_1040
from ..agents.tax.tools.form_filler import fill_tax_form
from ..agents.tax.tools.save_document import save_document

logger = logging.getLogger(__name__)

# Global conversation state storage
conversation_state = {}


@tool
async def ingest_w2_tool(s3_key: str, taxpayer_name: str = "Test User", tax_year: int = 2024) -> str:
    """
    Process W2 document from S3 bucket to extract wage and tax information.
    
    Args:
        s3_key: S3 key of the W2 document
        taxpayer_name: Name of the taxpayer
        tax_year: Tax year
    
    Returns:
        String describing the W2 processing result
    """
    try:
        logger.info(f"Processing W2: {s3_key}")
        result = await ingest_w2(s3_key, taxpayer_name, tax_year)
        
        if result.get('success'):
            # Store W2 data in conversation state
            session_id = conversation_state.get('current_session_id', 'default')
            if session_id not in conversation_state:
                conversation_state[session_id] = {}
            
            conversation_state[session_id]['w2_data'] = result['w2_extract']
            
            return f"Successfully processed W2! Found {result['forms_count']} form(s) with total wages of ${result['total_wages']:,.2f} and federal withholding of ${result['total_withholding']:,.2f}."
        else:
            return f"Failed to process W2: {result.get('error', 'Unknown error')}"
    except Exception as e:
        logger.error(f"Error in W2 ingestion: {e}")
        return f"Error processing W2: {str(e)}"


@tool
async def calc_1040_tool(
    filing_status: str,
    wages: float,
    withholding: float,
    dependents: int = 0,
    zip_code: str = "12345"
) -> str:
    """
    Calculate tax liability and refund/amount due based on user information.
    
    Args:
        filing_status: Filing status (Single, Married Filing Jointly, etc.)
        wages: Total wages from W2
        withholding: Federal tax withholding from W2
        dependents: Number of dependents
        zip_code: ZIP code for state tax purposes
    
    Returns:
        String describing the tax calculation results
    """
    try:
        logger.info(f"Calculating taxes for {filing_status} with wages ${wages:,.2f}")
        
        # Simplified tax calculation for demo purposes
        # In production, this would use the full calc_1040 function
        
        # Standard deductions for 2024
        standard_deductions = {
            'Single': 14600,
            'Married Filing Jointly': 29200,
            'Married Filing Separately': 14600,
            'Head of Household': 21900
        }
        
        standard_deduction = standard_deductions.get(filing_status, 14600)
        
        # Calculate AGI (simplified - just wages for W2 employees)
        agi = wages
        
        # Calculate taxable income
        taxable_income = max(0, agi - standard_deduction)
        
        # Simplified tax calculation (2024 tax brackets for single filers)
        if filing_status == 'Single':
            if taxable_income <= 11600:
                tax = taxable_income * 0.10
            elif taxable_income <= 47150:
                tax = 1160 + (taxable_income - 11600) * 0.12
            elif taxable_income <= 100525:
                tax = 5426 + (taxable_income - 47150) * 0.22
            else:
                tax = 17168.5 + (taxable_income - 100525) * 0.24
        else:
            # Simplified calculation for other filing statuses
            tax = taxable_income * 0.15  # Rough estimate
        
        # Child Tax Credit (simplified)
        child_tax_credit = min(dependents * 2000, tax)  # Up to $2000 per child
        
        # Final tax after credits
        final_tax = max(0, tax - child_tax_credit)
        
        # Calculate refund or amount due
        refund_or_due = withholding - final_tax
        
        # Store calculation results in conversation state
        session_id = conversation_state.get('current_session_id', 'default')
        if session_id not in conversation_state:
            conversation_state[session_id] = {}
        
        calc_result = {
            'agi': agi,
            'standard_deduction': standard_deduction,
            'taxable_income': taxable_income,
            'tax': final_tax,
            'withholding': withholding,
            'child_tax_credit': child_tax_credit,
            'refund_or_due': refund_or_due
        }
        
        conversation_state[session_id]['tax_calculation'] = calc_result
        
        if refund_or_due >= 0:
            message = f"Great news! Based on your information, you're entitled to a refund of ${refund_or_due:,.2f}."
        else:
            message = f"Based on your information, you owe ${abs(refund_or_due):,.2f} in taxes."
        
        message += f"\n\nHere's the breakdown:\n"
        message += f"- Adjusted Gross Income: ${agi:,.2f}\n"
        message += f"- Standard Deduction: ${standard_deduction:,.2f}\n"
        message += f"- Taxable Income: ${taxable_income:,.2f}\n"
        message += f"- Tax Liability: ${final_tax:,.2f}\n"
        message += f"- Federal Withholding: ${withholding:,.2f}"
        
        if child_tax_credit > 0:
            message += f"\n- Child Tax Credit: ${child_tax_credit:,.2f}"
        
        return message
        
    except Exception as e:
        logger.error(f"Error in tax calculation: {e}")
        return f"Error calculating taxes: {str(e)}"


@tool
async def fill_form_tool(
    form_type: str = "1040",
    filing_status: str = None,
    wages: float = None,
    withholding: float = None,
    dependents: int = 0
) -> str:
    """
    Fill tax form with provided information progressively.
    
    Args:
        form_type: Type of form to fill
        filing_status: Filing status
        wages: Total wages
        withholding: Federal withholding
        dependents: Number of dependents
    
    Returns:
        String describing the form filling result
    """
    try:
        logger.info(f"Filling {form_type} form")
        
        # Get data from conversation state if not provided
        session_id = conversation_state.get('current_session_id', 'default')
        session_data = conversation_state.get(session_id, {})
        
        # Use calculation data if available
        calc_data = session_data.get('tax_calculation', {})
        w2_data = session_data.get('w2_data', {})
        
        # Prepare form data
        form_data = {
            'filing_status': filing_status or session_data.get('filing_status'),
            'wages': wages or calc_data.get('agi', 0),
            'federal_withholding': withholding or calc_data.get('withholding', 0),
            'dependents': dependents or session_data.get('dependents', 0),
            'standard_deduction': calc_data.get('standard_deduction', 0),
            'taxable_income': calc_data.get('taxable_income', 0),
            'tax_liability': calc_data.get('tax', 0),
            'refund_or_due': calc_data.get('refund_or_due', 0),
            'taxpayer_name': session_data.get('taxpayer_name', 'Test User'),
            'ssn': session_data.get('ssn', '123-45-6789'),
            'address': session_data.get('address', '123 Main St, Anytown, ST 12345')
        }
        
        result = await fill_tax_form(form_type, form_data)
        
        if result.get('success'):
            # Store filled form info in conversation state
            conversation_state[session_id]['filled_form'] = {
                'form_type': form_type,
                'form_url': result.get('form_url'),
                'form_data': form_data,
                'filled_at': datetime.now().isoformat()
            }
            
            return f"Successfully filled {form_type} form! The form has been prepared with your information. Ready to save it to your documents."
        else:
            return f"Failed to fill form: {result.get('error', 'Unknown error')}"
    except Exception as e:
        logger.error(f"Error filling form: {e}")
        return f"Error filling form: {str(e)}"


@tool
async def save_document_tool(
    document_type: str = "tax_return",
    description: str = "Completed Tax Return"
) -> str:
    """
    Save completed tax document to documents bucket.
    
    Args:
        document_type: Type of document
        description: Document description
    
    Returns:
        String describing the save result
    """
    try:
        logger.info(f"Saving {document_type} document")
        
        session_id = conversation_state.get('current_session_id', 'default')
        session_data = conversation_state.get(session_id, {})
        filled_form = session_data.get('filled_form', {})
        
        if not filled_form:
            return "No completed form found. Please fill out the form first."
        
        # Prepare document data
        doc_data = {
            'document_type': document_type,
            'description': description,
            'form_type': filled_form.get('form_type', '1040'),
            'tax_year': 2024,
            'taxpayer_name': filled_form.get('form_data', {}).get('taxpayer_name', 'Test User'),
            'filing_status': filled_form.get('form_data', {}).get('filing_status'),
            'refund_or_due': filled_form.get('form_data', {}).get('refund_or_due', 0),
            'completed_at': datetime.now().isoformat()
        }
        
        # Generate document content (simplified for demo)
        content = _generate_tax_document_content(filled_form['form_data'])
        
        result = await save_document(
            content=content,
            document_type=document_type,
            metadata=doc_data
        )
        
        if result.get('success'):
            return f"🎉 Congratulations! Your tax return has been completed and saved successfully. Document ID: {result.get('document_id', 'N/A')}"
        else:
            return f"Failed to save document: {result.get('error', 'Unknown error')}"
    except Exception as e:
        logger.error(f"Error saving document: {e}")
        return f"Error saving document: {str(e)}"


@tool
async def manage_state_tool(
    action: str,
    key: str = None,
    value: str = None,
    session_id: str = "default"
) -> str:
    """
    Manage conversation state (set, get, clear, list).
    
    Args:
        action: Action to perform (set, get, clear, list)
        key: State key
        value: Value to set
        session_id: Session ID
    
    Returns:
        String describing the state management result
    """
    try:
        if session_id not in conversation_state:
            conversation_state[session_id] = {}
        
        if action == "set" and key and value is not None:
            # Try to convert value to appropriate type
            try:
                if value.isdigit():
                    value = int(value)
                elif value.replace('.', '').isdigit():
                    value = float(value)
            except:
                pass  # Keep as string
            
            conversation_state[session_id][key] = value
            return f"Set {key} to {value} in conversation state"
        
        elif action == "get" and key:
            value = conversation_state[session_id].get(key)
            return f"Retrieved {key}: {value}"
        
        elif action == "clear":
            if key:
                conversation_state[session_id].pop(key, None)
                return f"Cleared {key} from state"
            else:
                conversation_state[session_id] = {}
                return "Cleared all conversation state"
        
        elif action == "list":
            keys = list(conversation_state[session_id].keys())
            return f"State keys: {keys}"
        
        else:
            return "Invalid action or missing parameters"
            
    except Exception as e:
        logger.error(f"Error managing state: {e}")
        return f"Error managing state: {str(e)}"


def _generate_tax_document_content(form_data: Dict[str, Any]) -> str:
    """Generate tax document content for saving."""
    return f"""
FORM 1040 - U.S. INDIVIDUAL INCOME TAX RETURN
Tax Year: 2024

TAXPAYER INFORMATION:
Name: {form_data.get('taxpayer_name', 'Unknown')}
SSN: {form_data.get('ssn', 'Unknown')}
Address: {form_data.get('address', 'Unknown')}
Filing Status: {form_data.get('filing_status', 'Unknown')}

INCOME:
Line 1a - Total wages: ${form_data.get('wages', 0):,.2f}

DEDUCTIONS:
Line 12 - Standard deduction: ${form_data.get('standard_deduction', 0):,.2f}

TAXABLE INCOME:
Line 15 - Taxable income: ${form_data.get('taxable_income', 0):,.2f}

TAX:
Line 16 - Tax: ${form_data.get('tax_liability', 0):,.2f}

PAYMENTS:
Line 25a - Federal income tax withheld: ${form_data.get('federal_withholding', 0):,.2f}

REFUND OR AMOUNT OWED:
{'Line 34 - Refund' if form_data.get('refund_or_due', 0) >= 0 else 'Line 37 - Amount you owe'}: ${abs(form_data.get('refund_or_due', 0)):,.2f}

Generated by Province Tax Filing System on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
"""


class TaxService:
    """
    Conversational tax filing service using Strands SDK.
    
    Manages the complete flow from initial conversation to form completion.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.agent = None
        self.setup_agent()
    
    def setup_agent(self):
        """Set up the Strands agent with Bedrock model and tax tools."""
        
        # Get system prompt for tax filing
        system_prompt = self._get_agent_instructions()
        
        # Create agent with Bedrock model (default)
        self.agent = Agent(
            model=os.getenv('BEDROCK_MODEL_ID', 'us.anthropic.claude-3-5-sonnet-20240620-v1:0'),
            system_prompt=system_prompt,
            tools=[
                ingest_w2_tool,
                calc_1040_tool,
                fill_form_tool,
                save_document_tool,
                manage_state_tool
            ],
            name="TaxFilingAgent",
            description="AI agent that guides users through tax filing process step by step"
        )
        
        logger.info("Tax conversation agent initialized with Strands SDK")
    
    def _get_agent_instructions(self) -> str:
        """Get comprehensive agent instructions for tax filing conversation."""
        return """
You are a helpful tax filing assistant that guides users through completing their tax return step by step.

CONVERSATION FLOW:
1. Start by greeting the user and explaining the process
2. Ask about their filing status (Single, Married Filing Jointly, etc.)
3. Ask about dependents if applicable
4. Request W2 information (you can process existing W2s from the system)
5. Gather additional required information (address, bank info for refund, etc.)
6. Calculate taxes using the provided information
7. Fill out the tax form progressively
8. Save the completed form to the documents bucket

IMPORTANT GUIDELINES:
- Ask ONE question at a time to avoid overwhelming the user
- Be conversational and friendly, not robotic
- Explain what you're doing at each step
- Use the tools provided to process W2s, calculate taxes, and fill forms
- Keep track of conversation state using the manage_state_tool
- Only handle simple W2 employee returns (no complex situations)
- When user provides information, acknowledge it and move to the next logical step

TOOL USAGE:
- Use ingest_w2_tool when user mentions W2 or you need to process W2 data
- Use calc_1040_tool when you have enough information to calculate taxes
- Use fill_form_tool to progressively fill out tax forms
- Use save_document_tool to save completed forms
- Use manage_state_tool to track conversation progress

EXAMPLE CONVERSATION FLOW:
1. "Hi! I'm here to help you file your tax return. Let's start with the basics - what's your filing status? Are you single, married filing jointly, or have another status?"
2. [User responds] "Great! Do you have any dependents you'd like to claim?"
3. [User responds] "Perfect! Now I'll need to process your W2 form. I can access W2 documents from our system. Let me check what's available..."
4. [Process W2] "I found your W2 showing wages of $X and withholding of $Y. Is this correct?"
5. Continue gathering info and filling form step by step...

Remember: Be helpful, patient, and guide the user through each step clearly.
"""
    
    async def start_conversation(self, session_id: str = None) -> str:
        """Start a new tax filing conversation."""
        if not session_id:
            session_id = f"tax_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Set current session ID for tools to use
        conversation_state['current_session_id'] = session_id
        conversation_state[session_id] = {
            'started_at': datetime.now().isoformat(),
            'status': 'started'
        }
        
        # Initial greeting message
        initial_message = """Hi! I'm your AI tax filing assistant. I'm here to help you complete your tax return step by step. 

I can help you with simple W-2 employee tax returns. The process is straightforward:
1. I'll ask about your filing status and basic information
2. I'll process your W-2 form data
3. I'll calculate your taxes
4. I'll fill out your tax form
5. I'll save your completed return

Let's get started! What's your filing status? Are you:
- Single
- Married Filing Jointly  
- Married Filing Separately
- Head of Household

Just let me know which one applies to you."""
        
        return initial_message
    
    async def continue_conversation(self, user_message: str, session_id: str = None) -> str:
        """Continue the conversation with user input."""
        if not session_id:
            session_id = conversation_state.get('current_session_id', 'default')
        
        try:
            # Update current session ID for tools to use
            conversation_state['current_session_id'] = session_id
            
            # Get response from Strands agent
            response = await self.agent.invoke_async(user_message)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in conversation: {e}")
            return f"I apologize, but I encountered an error: {str(e)}. Let's try again."
    
    def get_conversation_state(self, session_id: str = None) -> Dict[str, Any]:
        """Get current conversation state."""
        if not session_id:
            session_id = conversation_state.get('current_session_id', 'default')
        
        return conversation_state.get(session_id, {})
    
    async def list_available_w2s(self) -> List[str]:
        """List available W2 documents in the datasets bucket."""
        import boto3
        
        try:
            s3_client = boto3.client(
                's3',
                region_name=self.settings.aws_region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            
            bucket_name = self.settings.documents_bucket_name
            prefix = "datasets/w2-forms/"
            
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=10  # Limit for demo
            )
            
            w2_files = []
            for obj in response.get('Contents', []):
                key = obj['Key']
                if key.endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                    w2_files.append(key)
            
            return w2_files[:5]  # Return first 5 for demo
            
        except Exception as e:
            logger.error(f"Error listing W2 files: {e}")
            return []


# Global service instance
tax_service = TaxService()