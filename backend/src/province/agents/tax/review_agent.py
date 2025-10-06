"""Review Agent - Generates plain-English summaries of tax calculations."""

import json
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime

from province.core.config import get_settings
from province.agents.bedrock_agent_client import BedrockAgentClient
from .models import TaxCalculation

logger = logging.getLogger(__name__)


class ReviewAgent:
    """
    Review Agent - Creates plain-English explanations of tax calculations.
    
    This agent:
    1. Drafts a 1-page summary in plain English
    2. Explains income, deductions, tax, credits, withholding, net refund/amount due
    3. Inserts footnotes with pin-cites to source documents
    4. Produces a checklist for missing information
    5. Makes tax calculations understandable for regular taxpayers
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.bedrock_client = BedrockAgentClient()
        self.agent_id = None
        self.agent_alias_id = None
        
    async def create_agent(self) -> str:
        """Create the Review Agent in AWS Bedrock."""
        
        instruction = """You are the Review Agent for Province Tax Filing System. Your job is to create clear, plain-English explanations of tax calculations that regular taxpayers can understand.

SUMMARY REQUIREMENTS:
1. Write in conversational, non-technical language
2. Explain each major component: income, deductions, tax, credits, withholding
3. Include specific dollar amounts and percentages
4. Add footnotes with pin-cites to source documents (W-2 boxes, tax tables)
5. Highlight the bottom line: refund or amount due
6. Create a checklist of any missing information

EXPLANATION STRUCTURE:
1. **Income Summary**: Total wages from all W-2s with employer breakdown
2. **Deductions**: Standard deduction amount and why it applies
3. **Tax Calculation**: How tax was calculated using brackets
4. **Credits**: Any credits applied (Child Tax Credit, etc.)
5. **Withholding**: Total federal taxes withheld from paychecks
6. **Bottom Line**: Final refund or amount due with clear explanation

TONE AND STYLE:
- Use "you" and "your" to make it personal
- Avoid tax jargon - explain terms when necessary
- Use analogies when helpful
- Be encouraging and reassuring
- Highlight positive aspects (refunds, credits)

FOOTNOTE FORMAT:
- Source references: "from W-2 (Acme Inc., Box 1)"
- Tax law references: "Standard deduction (Single, 2025)"
- Calculation references: "Tax brackets (2025 rates)"

MISSING INFO CHECKLIST:
- SSNs for dependents
- Bank account for direct deposit
- State tax considerations
- Any incomplete W-2 information"""

        tools = [
            {
                "toolSpec": {
                    "name": "load_calculation_data",
                    "description": "Load tax calculation and source data",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "engagement_id": {"type": "string"}
                            },
                            "required": ["engagement_id"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "generate_plain_english_summary",
                    "description": "Generate plain-English tax summary",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "calculation": {"type": "object"},
                                "w2_data": {"type": "object"},
                                "taxpayer_info": {"type": "object"}
                            },
                            "required": ["calculation"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "create_missing_info_checklist",
                    "description": "Create checklist of missing information",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "engagement_data": {"type": "object"}
                            },
                            "required": ["engagement_data"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "save_review_summary",
                    "description": "Save the review summary document",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "engagement_id": {"type": "string"},
                                "summary_content": {"type": "string"}
                            },
                            "required": ["engagement_id", "summary_content"]
                        }
                    }
                }
            }
        ]
        
        # Create the agent
        response = await self.bedrock_client.create_agent(
            agent_name="ReviewAgent",
            instruction=instruction,
            foundation_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            tools=tools
        )
        
        self.agent_id = response["agent"]["agentId"]
        logger.info(f"Created Review agent with ID: {self.agent_id}")
        
        # Create alias
        alias_response = await self.bedrock_client.create_agent_alias(
            agent_id=self.agent_id,
            agent_alias_name="DRAFT"
        )
        
        self.agent_alias_id = alias_response["agentAlias"]["agentAliasId"]
        logger.info(f"Created agent alias with ID: {self.agent_alias_id}")
        
        return self.agent_id
    
    async def invoke(self, session_id: str, input_text: str, engagement_id: str) -> Dict[str, Any]:
        """Invoke the Review agent."""
        
        if not self.agent_id or not self.agent_alias_id:
            raise ValueError("Agent not deployed. Call create_agent() first.")
        
        # Add engagement context
        input_text = f"[ENGAGEMENT_ID: {engagement_id}] {input_text}"
        
        response = await self.bedrock_client.invoke_agent(
            agent_id=self.agent_id,
            agent_alias_id=self.agent_alias_id,
            session_id=session_id,
            input_text=input_text
        )
        
        return response
    
    def generate_plain_english_summary(self, 
                                     calculation: TaxCalculation,
                                     w2_data: Optional[Dict[str, Any]] = None,
                                     taxpayer_info: Optional[Dict[str, Any]] = None) -> str:
        """Generate a plain-English summary of the tax calculation."""
        
        # Extract key information
        filing_status = calculation.provenance.get('filing_status', 'Unknown')
        tax_year = calculation.provenance.get('tax_year', 2025)
        
        # Format filing status for display
        status_display = {
            'S': 'Single',
            'MFJ': 'Married Filing Jointly',
            'MFS': 'Married Filing Separately',
            'HOH': 'Head of Household',
            'QW': 'Qualifying Widow(er)'
        }.get(filing_status, filing_status)
        
        # Determine if refund or owe
        is_refund = calculation.refund_or_due >= 0
        amount = abs(calculation.refund_or_due)
        
        summary = f"""# Your {tax_year} Tax Return Summary

## The Bottom Line
"""
        
        if is_refund:
            summary += f"**🎉 You're getting a refund of ${amount:,.2f}!**\n\n"
            summary += f"This means the federal taxes withheld from your paychecks (${calculation.withholding:,.2f}) were more than what you actually owe in taxes. The IRS will send you the difference.\n\n"
        else:
            summary += f"**You owe ${amount:,.2f} in additional federal taxes.**\n\n"
            summary += f"This means the federal taxes withheld from your paychecks (${calculation.withholding:,.2f}) weren't quite enough to cover your total tax liability.\n\n"
        
        summary += f"""## How We Calculated Your Taxes

### Your Income
Your total income for {tax_year} was **${calculation.agi:,.2f}**"""
        
        # Add W-2 breakdown if available
        if w2_data and w2_data.get('forms'):
            summary += " from the following sources:\n"
            for i, form in enumerate(w2_data['forms'], 1):
                employer_name = form.get('employer', {}).get('name', f'Employer {i}')
                wages = form.get('boxes', {}).get('1', 0)
                summary += f"- {employer_name}: ${wages:,.2f}¹\n"
        else:
            summary += ".¹\n"
        
        summary += f"""
### Your Deduction
As a {status_display} filer, you get a standard deduction of **${calculation.standard_deduction:,.2f}**.² This reduces your taxable income - think of it as the amount you can earn tax-free.

After subtracting your standard deduction, your taxable income is **${calculation.taxable_income:,.2f}**.

### Your Tax Calculation
Based on your taxable income of ${calculation.taxable_income:,.2f}, your federal tax liability is **${calculation.tax:,.2f}**.³ This is calculated using the {tax_year} tax brackets, which apply different rates to different portions of your income.
"""
        
        # Add credits section if applicable
        ctc_amount = calculation.credits.get('CTC', Decimal('0'))
        if ctc_amount > 0:
            qualifying_children = calculation.provenance.get('ctc_qualifying_children', 0)
            summary += f"""
### Your Tax Credits
You qualify for the Child Tax Credit of **${ctc_amount:,.2f}** for {qualifying_children} qualifying {'child' if qualifying_children == 1 else 'children'}.⁴ Credits are even better than deductions because they reduce your tax bill dollar-for-dollar.

After applying your credits, your final tax liability is **${max(Decimal('0'), calculation.tax - ctc_amount):,.2f}**.
"""
        
        summary += f"""
### Your Withholding
Throughout {tax_year}, your {'employer' if not w2_data or len(w2_data.get('forms', [])) <= 1 else 'employers'} withheld **${calculation.withholding:,.2f}** in federal taxes from your paychecks.⁵

"""
        
        # Add next steps
        if is_refund:
            summary += f"""## What Happens Next?
1. Review this summary and your draft 1040 form
2. If everything looks correct, you can file your return
3. The IRS will process your return and send your ${amount:,.2f} refund
4. With direct deposit, refunds typically arrive within 21 days

"""
        else:
            summary += f"""## What Happens Next?
1. Review this summary and your draft 1040 form  
2. If everything looks correct, you'll need to pay the ${amount:,.2f} you owe
3. Payment is due by April 15, {tax_year + 1}
4. You can pay online, by phone, or by mail

"""
        
        # Add footnotes
        summary += f"""---

## Source References
¹ From W-2 forms, Box 1 (Wages, tips, other compensation)
² Standard deduction for {status_display} filers, {tax_year} tax year
³ Calculated using {tax_year} federal tax brackets
"""
        
        if ctc_amount > 0:
            summary += "⁴ Child Tax Credit, based on qualifying dependents under age 17\n"
        
        summary += "⁵ From W-2 forms, Box 2 (Federal income tax withheld)\n"
        
        return summary
    
    def create_missing_info_checklist(self, engagement_data: Dict[str, Any]) -> List[str]:
        """Create a checklist of missing information."""
        
        missing_items = []
        
        # Check taxpayer information
        taxpayer_info = engagement_data.get('taxpayer_info', {})
        if not taxpayer_info.get('ssn'):
            missing_items.append("Primary taxpayer Social Security Number")
        
        if not taxpayer_info.get('address'):
            missing_items.append("Complete mailing address")
        
        # Check dependents
        dependents = engagement_data.get('dependents', [])
        for i, dep in enumerate(dependents, 1):
            if not dep.get('ssn'):
                missing_items.append(f"Social Security Number for dependent #{i} ({dep.get('name', 'Unknown')})")
        
        # Check bank information for direct deposit
        bank_info = engagement_data.get('bank_info', {})
        if not bank_info.get('routing_number') or not bank_info.get('account_number'):
            missing_items.append("Bank account information for direct deposit (optional but recommended)")
        
        # Check W-2 completeness
        w2_data = engagement_data.get('w2_data', {})
        if not w2_data.get('forms'):
            missing_items.append("W-2 forms need to be uploaded and processed")
        
        return missing_items
    
    def format_checklist(self, missing_items: List[str]) -> str:
        """Format the missing information checklist."""
        
        if not missing_items:
            return "✅ **All required information has been collected!**\n\nYour return is ready for final review and filing."
        
        checklist = "## Missing Information Checklist\n\n"
        checklist += "Please provide the following information to complete your return:\n\n"
        
        for item in missing_items:
            checklist += f"- [ ] {item}\n"
        
        checklist += "\n*Note: Items marked as optional won't prevent you from filing, but they may make the process more convenient.*"
        
        return checklist
