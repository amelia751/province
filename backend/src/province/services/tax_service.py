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
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from strands import Agent, tool

from ..core.config import get_settings
from ..agents.tax.tools.ingest_documents import ingest_documents
from ..agents.tax.tools.calc_1040 import calc_1040
from ..agents.tax.tools.form_filler import fill_tax_form
from ..agents.tax.tools.save_document import save_document

logger = logging.getLogger(__name__)

# Global conversation state storage
conversation_state = {}


@tool
async def ingest_documents_tool(s3_key: str, taxpayer_name: str = "Test User", tax_year: int = 2024, document_type: str = None) -> str:
    """
    Process tax documents from S3 bucket to extract tax information.
    Supports W-2, 1099-INT, 1099-MISC, and other tax documents.
    
    Args:
        s3_key: S3 key of the tax document
        taxpayer_name: Name of the taxpayer
        tax_year: Tax year
        document_type: Type of document ('W-2', '1099-INT', '1099-MISC', or None for auto-detection)
    
    Returns:
        String describing the document processing result
    """
    try:
        logger.info(f"Processing tax document: {s3_key} (type: {document_type or 'auto-detect'})")
        
        # Note: ingest_documents will wait for Bedrock processing to complete (up to 3 minutes)
        # This ensures we always have the data before continuing
        result = await ingest_documents(s3_key, taxpayer_name, tax_year, document_type)
        
        if result.get('success'):
            # Store document data in conversation state
            session_id = conversation_state.get('current_session_id', 'default')
            if session_id not in conversation_state:
                conversation_state[session_id] = {}
            
            # Store the extracted data based on document type
            doc_type = result.get('document_type', 'unknown')
            if doc_type == 'W-2':
                conversation_state[session_id]['w2_data'] = result['w2_extract']
                logger.info(f"✅ Stored W-2 data in session '{session_id}'")
                
                # Log extracted employee info
                if 'forms' in result['w2_extract'] and len(result['w2_extract']['forms']) > 0:
                    employee = result['w2_extract']['forms'][0].get('employee', {})
                    logger.info(f"   Employee: {employee.get('name', 'Unknown')}")
                    logger.info(f"   SSN: {employee.get('SSN', 'Not found')}")
                    if employee.get('address'):
                        logger.info(f"   Address: {employee.get('address')}")
                    
            elif doc_type in ['1099-INT', '1099-MISC']:
                if 'tax_documents' not in conversation_state[session_id]:
                    conversation_state[session_id]['tax_documents'] = []
                conversation_state[session_id]['tax_documents'].append(result)
            
            return f"Successfully processed {doc_type} document! Found {result['forms_count']} form(s) with total wages/income of ${result['total_wages']:,.2f} and federal withholding of ${result['total_withholding']:,.2f}."
        else:
            return f"Failed to process tax document: {result.get('error', 'Unknown error')}"
    except Exception as e:
        logger.error(f"Error in document ingestion: {e}")
        import traceback
        traceback.print_exc()
        return f"Error processing tax document: {str(e)}"


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
        
        logger.info(f"🔍 DEBUG fill_form_tool:")
        logger.info(f"   Current session_id: {session_id}")
        logger.info(f"   Session data keys: {list(session_data.keys())}")
        logger.info(f"   All conversation_state keys: {list(conversation_state.keys())}")
        logger.info(f"   filing_status param: {filing_status}")
        logger.info(f"   session filing_status: {session_data.get('filing_status', 'NOT SET')}")
        
        # Use calculation data if available
        calc_data = session_data.get('tax_calculation', {})
        w2_data = session_data.get('w2_data', {})
        
        logger.info(f"   Has w2_data: {bool(w2_data)}")
        if w2_data:
            logger.info(f"   W2 data keys: {list(w2_data.keys())}")
        
        # Extract employee info from W-2 if available
        employee_info = {}
        if w2_data and 'forms' in w2_data and len(w2_data['forms']) > 0:
            employee_info = w2_data['forms'][0].get('employee', {})
            logger.info(f"✅ Found W-2 employee data: {employee_info}")
        else:
            logger.warning(f"⚠️  NO W-2 DATA FOUND in session '{session_id}' - will use fallback values!")
        
        # Get SSN from W-2 (capital SSN key from Bedrock) and remove dashes
        ssn_raw = employee_info.get('SSN') or employee_info.get('ssn') or session_data.get('ssn', '123-45-6789')
        ssn = ssn_raw.replace('-', '') if ssn_raw else '123456789'  # Remove dashes for PDF form digit boxes
        
        # Parse taxpayer name from W-2 'name' field (full name)
        if employee_info.get('name'):
            full_name = employee_info.get('name')
            logger.info(f"📝 Parsing W-2 name: {full_name}")
            name_parts = full_name.split()
            first_name = name_parts[0] if len(name_parts) > 0 else 'John'
            last_name = name_parts[-1] if len(name_parts) > 1 else 'Smith'
            middle_initial = name_parts[1][0] if len(name_parts) > 2 else ''
        else:
            # Fallback to session data
            taxpayer_name = session_data.get('taxpayer_name', 'John A. Smith')
            name_parts = taxpayer_name.split()
            first_name = name_parts[0] if len(name_parts) > 0 else 'John'
            middle_initial = name_parts[1][0] if len(name_parts) > 2 and name_parts[1] else ''
            last_name = name_parts[-1] if len(name_parts) > 1 else 'Smith'
        
        # Get address from W-2 if available (extracted from Bedrock markdown)
        if employee_info.get('address'):
            # W-2 has full address extracted from markdown
            address_full = employee_info.get('address')
            street = employee_info.get('street', '123 Main St')
            apt_no = employee_info.get('apt_no', '')
            city = employee_info.get('city', 'Anytown')
            state = employee_info.get('state', 'CA')
            zip_code = employee_info.get('zip', '90210')
            logger.info(f"📍 Using address from W-2: {address_full}")
            if apt_no:
                logger.info(f"   Apt/Unit: {apt_no}")
        elif session_data.get('address'):
            # Use address from session
            address_full = session_data.get('address')
            address_parts = address_full.split(',') if ',' in address_full else address_full.split()
            street = address_parts[0].strip() if len(address_parts) > 0 else '123 Main St'
            city = address_parts[1].strip() if len(address_parts) > 1 else 'Anytown'
            state_zip_part = address_parts[2].strip() if len(address_parts) > 2 else 'CA 90210'
            state_zip_components = state_zip_part.split()
            state = state_zip_components[0] if state_zip_components else 'CA'
            zip_code = state_zip_components[1] if len(state_zip_components) > 1 else '90210'
        else:
            # Fallback: use state from W-2 box 15 if available
            boxes = w2_data.get('forms', [{}])[0].get('boxes', {}) if w2_data else {}
            state_from_w2 = boxes.get('15', 'CA')  # Box 15 is state
            street = '123 Main St'
            city = 'Anytown'
            state = state_from_w2
            zip_code = '90210'
            logger.info(f"📍 Using fallback address with state from W-2 box 15: {state}")

        
        logger.info(f"📝 Form filling with: {first_name} {last_name}, SSN: {ssn}, Address: {street}, {city}, {state} {zip_code}")
        
        # Get filing status for checkbox mapping (normalize case)
        filing_status_value = filing_status or session_data.get('filing_status', 'Single')
        filing_status_normalized = filing_status_value.strip().lower()
        
        logger.info(f"📋 Filing status: '{filing_status_value}' (normalized: '{filing_status_normalized}')")
        
        # Debug: Show ALL checkbox states
        is_single = filing_status_normalized == 'single'
        is_married_joint = filing_status_normalized in ['married filing jointly', 'married jointly', 'married']
        is_married_separate = filing_status_normalized in ['married filing separately', 'married separately']
        is_head_household = filing_status_normalized in ['head of household', 'head household']
        is_qualifying_widow = filing_status_normalized in ['qualifying widow', 'qualifying widow(er)', 'qualifying surviving spouse']
        
        logger.info(f"   Filing status checkboxes:")
        logger.info(f"     - single: {is_single}")
        logger.info(f"     - married_joint: {is_married_joint}")
        logger.info(f"     - married_separate: {is_married_separate}")
        logger.info(f"     - head_household: {is_head_household}")
        logger.info(f"     - qualifying_widow: {is_qualifying_widow}")
        
        # Calculate refund/owe outside dict
        refund_or_due = calc_data.get('refund_or_due', 0)
        is_refund = refund_or_due > 0
        
        # Prepare comprehensive form data using SEMANTIC names from DynamoDB mapping
        form_data = {
            # === PERSONAL INFORMATION === (from 'personal_info' section)
            'taxpayer_first_name': first_name,
            'taxpayer_last_name': last_name,
            'taxpayer_ssn': ssn,  # Already formatted without dashes
            
            # === ADDRESS === (from 'address' section)
            'street_address': street,
            'apt_no': apt_no if 'apt_no' in locals() else '',
            'city': city,
            'state': state,
            'zip_code': zip_code,
            
            # === FILING STATUS === (from 'filing_status' section)
            # Use normalized comparison and explicitly set ALL checkboxes
            # Only ONE should be True, all others MUST be False
            'single': is_single,
            'married_joint': is_married_joint,
            'married_separate': is_married_separate,
            'head_household': is_head_household,
            'qualifying_widow': is_qualifying_widow,
            
            # === TAX YEAR === (from 'header' section)
            # For calendar year (Jan 1 - Dec 31, 2024), these fields should be BLANK
            # Only fill these for fiscal/other tax years
            # 'tax_year': '',  # Blank for calendar year
            # 'year_suffix': '',  # Blank for calendar year
            
            # === INCOME === (from 'income_page1' section)
            'wages_line_1a': wages or calc_data.get('agi', 0),  # Line 1a - Wages
            'total_income_9': wages or calc_data.get('agi', 0),  # Line 9 - Total income
            
            # === ADJUSTMENTS === (from 'adjustments' section)
            'adjusted_gross_income_11': calc_data.get('agi', wages or 0),  # Line 11 - AGI
            
            # === DEDUCTIONS === (from 'income_page1' section)
            'total_deductions_line_14_computed': calc_data.get('standard_deduction', 0),  # Line 12 - Standard deduction
            
            # === PAYMENTS === (from 'payments' section)
            'withholding': withholding or calc_data.get('withholding', 0),  # Line 25a - Federal withholding
            'total_payments': withholding or calc_data.get('withholding', 0),  # Line 33 - Total payments
            
            # === REFUND === (from 'refund_or_amount_owed' section)
            'overpayment': abs(refund_or_due) if is_refund else 0,  # Line 34 - Refund
            'amount_owed': abs(refund_or_due) if not is_refund else 0,  # Line 37 - Amount owed
            
            # === METADATA ===
            'filing_status': filing_status_value,
            'dependents': dependents or session_data.get('dependents', 0),
        }
        
        # Get user_id from session for PII-safe storage
        user_id = session_data.get('user_id')
        logger.info(f"🔑 Filling form with user_id: {user_id} (from session: {session_id})")
        logger.info(f"📦 Session data keys: {list(session_data.keys())}")
        
        # Skip questions when called from tool - we have all the data we need
        result = await fill_tax_form(form_type, form_data, user_id=user_id, skip_questions=True)
        
        if result.get('success'):
            # Store filled form info in conversation state with versioning
            conversation_state[session_id]['filled_form'] = {
                'form_type': form_type,
                'form_url': result.get('filled_form_url'),
                'form_data': form_data,
                'filled_at': datetime.now().isoformat(),
                'versioning': result.get('versioning', {})
            }
            
            # Add versioning information to response
            versioning = result.get('versioning', {})
            version_info = ""
            if versioning:
                if versioning.get('is_new_document'):
                    version_info = f" (New document - Version {versioning.get('version', 'v1')})"
                else:
                    version_info = f" (Updated to Version {versioning.get('version', 'v1')} - Total versions: {versioning.get('total_versions', 1)})"
            
            return f"Successfully filled {form_type} form{version_info}! The form has been prepared with your information and is available at: {result.get('filled_form_url')}. Ready to save it to your documents."
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
    Save supporting documents (W2s, receipts, etc) to engagement folder.
    
    NOTE: Filled tax forms are ALREADY SAVED by fill_form_tool with versioning!
    This tool is for OTHER documents like source documents, workpapers, etc.
    
    Args:
        document_type: Type of document (e.g., 'w2', 'receipt', 'workpaper')
        description: Document description
    
    Returns:
        String describing the save result
    """
    try:
        logger.info(f"Saving {document_type} document")
        
        session_id = conversation_state.get('current_session_id', 'default')
        session_data = conversation_state.get(session_id, {})
        filled_form = session_data.get('filled_form', {})
        
        # If trying to save a tax return, inform that it's already saved by fill_form
        if document_type == "tax_return" or "tax" in document_type.lower():
            if filled_form:
                versioning = filled_form.get('versioning', {})
                form_url = filled_form.get('form_url', '')
                version = versioning.get('version', 'v1')
                total_versions = versioning.get('total_versions', 1)
                
                return f"""🎉 Great news! Your tax return is already saved!

📋 Form Information:
   - Form Type: {filled_form.get('form_type', 'Form 1040')}
   - Version: {version} (Total versions: {total_versions})
   - Location: S3 filled_forms folder
   - Filled At: {filled_form.get('filled_at', 'just now')}

✅ The form was automatically saved with versioning when you filled it out.
   All {total_versions} version(s) are preserved and available for download.
   
💡 The fill_form tool automatically saves your completed forms with full version history!"""
        
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
        content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        result = await save_document(
            engagement_id=session_id,
            path=f"{document_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            content_b64=content_b64,
            mime_type="text/plain"
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


@tool
async def list_version_history_tool(document_id: str = None) -> str:
    """
    List version history for a tax document.
    
    Args:
        document_id: Document ID to get history for (optional, uses current session if not provided)
    
    Returns:
        String describing the version history
    """
    try:
        session_id = conversation_state.get('current_session_id', 'default')
        session_data = conversation_state.get(session_id, {})
        
        # If no document_id provided, try to get from current session
        if not document_id:
            filled_form = session_data.get('filled_form', {})
            versioning = filled_form.get('versioning', {})
            document_id = versioning.get('document_id')
        
        if not document_id:
            return "No document ID available. Please fill a form first or provide a document ID."
        
        # Get version history from form filler
        from ..agents.tax.tools.form_filler import TaxFormFiller
        filler = TaxFormFiller()
        versions = await filler.get_version_history(document_id)
        
        if not versions:
            return f"No version history found for document {document_id}"
        
        # Format version history
        history = f"📋 Version History for {document_id}:\n"
        history += f"{'='*50}\n\n"
        
        for i, version in enumerate(versions):
            history += f"Version {version['version']}:\n"
            history += f"  📅 Created: {version['last_modified']}\n"
            history += f"  📁 Size: {version['size']:,} bytes\n"
            history += f"  🔗 S3 Key: {version['s3_key']}\n"
            if i < len(versions) - 1:
                history += "\n"
        
        history += f"\n📊 Total Versions: {len(versions)}"
        return history
        
    except Exception as e:
        logger.error(f"Error listing version history: {e}")
        return f"Error getting version history: {str(e)}"


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
                ingest_documents_tool,
                calc_1040_tool,
                fill_form_tool,
                save_document_tool,
                manage_state_tool,
                list_version_history_tool
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
- **CRITICAL: When user tells you their filing status (single, married filing jointly, etc.), IMMEDIATELY use manage_state_tool to save it as 'filing_status'**
- Only handle simple W2 employee returns (no complex situations)
- When user provides information, acknowledge it and move to the next logical step

TOOL USAGE:
- Use ingest_w2_tool when user mentions W2 or you need to process W2 data
- Use calc_1040_tool when you have enough information to calculate taxes
- Use fill_form_tool to progressively fill out tax forms (MUST pass filing_status parameter explicitly)
- Use save_document_tool to save completed forms
- Use manage_state_tool to track conversation progress
- **IMPORTANT: Always save filing_status to state: manage_state_tool(action="set", key="filing_status", value="Single") when user says they are single**

EXAMPLE CONVERSATION FLOW:
1. "Hi! I'm here to help you file your tax return. Let's start with the basics - what's your filing status? Are you single, married filing jointly, or have another status?"
2. [User responds "I am single"] → IMMEDIATELY call: manage_state_tool(action="set", key="filing_status", value="Single")
   Then respond: "Great! I've noted that you're filing as Single. Do you have any dependents you'd like to claim?"
3. [User responds] "Perfect! Now I'll need to process your W2 form. I can access W2 documents from our system. Let me check what's available..."
4. [Process W2] "I found your W2 showing wages of $X and withholding of $Y. Is this correct?"
5. [When filling form] Call fill_form_tool with filing_status="Single" parameter explicitly
6. Continue gathering info and filling form step by step...

Remember: Be helpful, patient, and guide the user through each step clearly.
"""
    
    async def start_conversation(self, session_id: str = None, user_id: str = None) -> str:
        """Start a new tax filing conversation."""
        if not session_id:
            session_id = f"tax_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Set current session ID for tools to use
        conversation_state['current_session_id'] = session_id
        conversation_state[session_id] = {
            'started_at': datetime.now().isoformat(),
            'status': 'started',
            'user_id': user_id  # Store user_id for form filling
        }
        
        logger.info(f"🎬 Started conversation - session_id: {session_id}, user_id: {user_id}")
        logger.info(f"   Current session ID in state: {conversation_state.get('current_session_id')}")
        
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
    
    async def continue_conversation(self, user_message: str, session_id: str = None, user_id: str = None) -> str:
        """Continue the conversation with user input."""
        if not session_id:
            session_id = conversation_state.get('current_session_id', 'default')
        
        logger.info(f"🔄 continue_conversation called:")
        logger.info(f"   session_id: {session_id}")
        logger.info(f"   user_id: {user_id}")
        logger.info(f"   message: {user_message[:100]}")
        
        try:
            # Update current session ID for tools to use
            conversation_state['current_session_id'] = session_id
            logger.info(f"   Set current_session_id to: {session_id}")
            
            # Update user_id if provided
            if user_id and session_id in conversation_state:
                conversation_state[session_id]['user_id'] = user_id
                logger.info(f"   Updated user_id in session to: {user_id}")
            
            # Debug: Show what's in this session
            if session_id in conversation_state:
                logger.info(f"   Session '{session_id}' has keys: {list(conversation_state[session_id].keys())}")
            
            # Get response from Strands agent
            response = await self.agent.invoke_async(user_message)
            
            # Extract text from AgentResult object
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
            
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