"""Tax Intake Agent - Collects filing information from taxpayers."""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from province.core.config import get_settings
from province.agents.bedrock_agent_client import BedrockAgentClient
from .models import FilingStatus, Dependent

logger = logging.getLogger(__name__)


class TaxIntakeAgent:
    """
    Tax Intake Agent - Collects essential filing information from taxpayers.
    
    This agent:
    1. Collects filing status, dependents, address/ZIP, bank info
    2. Validates information completeness and accuracy
    3. Writes /Intake/Organizer.md from chat answers
    4. Ensures all required information is gathered before proceeding
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.bedrock_client = BedrockAgentClient()
        self.agent_id = None
        self.agent_alias_id = None
        
    async def create_agent(self) -> str:
        """Create the Tax Intake Agent in AWS Bedrock."""
        
        instruction = """You are the Tax Intake Agent for Province Tax Filing System. Your job is to collect essential information needed for tax filing in a conversational, friendly manner, and assist with W-2 document processing.

INFORMATION TO COLLECT:
1. Filing Status (Single, Married Filing Jointly, Married Filing Separately, Head of Household, Qualifying Widow)
2. Dependents (count and basic info: name, SSN, relationship, birth date)
3. Address and ZIP code
4. Bank information for direct deposit (optional but recommended)
5. State of residence (for future state return preparation)
6. W-2 documents (process via OCR when uploaded)

ADDITIONAL CAPABILITIES:
- Process W-2 documents using OCR tools when users upload them
- Validate W-2 data against IRS requirements
- Help users understand their W-2 information
- Assist with tax calculations when intake is complete

CONVERSATION GUIDELINES:
- Ask one question at a time to avoid overwhelming the user
- Explain why you need each piece of information
- Validate responses and ask for clarification if needed
- Be patient and helpful - tax information can be confusing
- Offer examples when helpful (e.g., "Head of Household means you're unmarried and pay more than half the cost of keeping up a home for yourself and a qualifying person")

VALIDATION RULES:
- Filing status must be one of the 5 valid options
- SSNs should be in XXX-XX-XXXX format (but don't require full SSN if user is uncomfortable)
- ZIP codes should be 5 digits
- Bank routing numbers should be 9 digits
- Account numbers vary in length

Once you have all required information, create an Organizer.md file with the collected data."""

        tools = [
            {
                "toolSpec": {
                    "name": "save_intake_organizer",
                    "description": "Save the intake organizer markdown file",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "engagement_id": {"type": "string"},
                                "organizer_content": {"type": "string"},
                                "filing_status": {"type": "string"},
                                "dependents_count": {"type": "integer"},
                                "dependents_info": {"type": "array"},
                                "address": {"type": "object"},
                                "bank_info": {"type": "object"}
                            },
                            "required": ["engagement_id", "organizer_content", "filing_status"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "validate_filing_status",
                    "description": "Validate the provided filing status",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "filing_status": {"type": "string"}
                            },
                            "required": ["filing_status"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "validate_ssn_format",
                    "description": "Validate SSN format",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "ssn": {"type": "string"}
                            },
                            "required": ["ssn"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "calculate_dependent_eligibility",
                    "description": "Calculate if dependent qualifies for Child Tax Credit",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "birth_date": {"type": "string"},
                                "relationship": {"type": "string"},
                                "tax_year": {"type": "integer"}
                            },
                            "required": ["birth_date", "relationship", "tax_year"]
                        }
                    }
                }
            }
        ]
        
        # Create the agent
        response = await self.bedrock_client.create_agent(
            agent_name="TaxIntakeAgent",
            instruction=instruction,
            foundation_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            tools=tools
        )
        
        self.agent_id = response["agent"]["agentId"]
        logger.info(f"Created Tax Intake agent with ID: {self.agent_id}")
        
        # Create alias
        alias_response = await self.bedrock_client.create_agent_alias(
            agent_id=self.agent_id,
            agent_alias_name="DRAFT"
        )
        
        self.agent_alias_id = alias_response["agentAlias"]["agentAliasId"]
        logger.info(f"Created agent alias with ID: {self.agent_alias_id}")
        
        return self.agent_id
    
    async def invoke(self, session_id: str, input_text: str, engagement_id: str) -> Dict[str, Any]:
        """Invoke the Tax Intake agent."""
        
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
    
    def validate_filing_status(self, status: str) -> tuple[bool, Optional[str]]:
        """Validate filing status."""
        
        status_mapping = {
            "single": FilingStatus.SINGLE,
            "s": FilingStatus.SINGLE,
            "married filing jointly": FilingStatus.MARRIED_FILING_JOINTLY,
            "mfj": FilingStatus.MARRIED_FILING_JOINTLY,
            "married jointly": FilingStatus.MARRIED_FILING_JOINTLY,
            "married filing separately": FilingStatus.MARRIED_FILING_SEPARATELY,
            "mfs": FilingStatus.MARRIED_FILING_SEPARATELY,
            "married separately": FilingStatus.MARRIED_FILING_SEPARATELY,
            "head of household": FilingStatus.HEAD_OF_HOUSEHOLD,
            "hoh": FilingStatus.HEAD_OF_HOUSEHOLD,
            "qualifying widow": FilingStatus.QUALIFYING_WIDOW,
            "qw": FilingStatus.QUALIFYING_WIDOW,
            "qualifying widower": FilingStatus.QUALIFYING_WIDOW,
        }
        
        normalized_status = status.lower().strip()
        
        if normalized_status in status_mapping:
            return True, status_mapping[normalized_status].value
        
        return False, "Please choose from: Single, Married Filing Jointly, Married Filing Separately, Head of Household, or Qualifying Widow(er)"
    
    def validate_ssn_format(self, ssn: str) -> tuple[bool, str]:
        """Validate SSN format."""
        
        # Remove any spaces or dashes
        clean_ssn = ssn.replace("-", "").replace(" ", "")
        
        if len(clean_ssn) != 9 or not clean_ssn.isdigit():
            return False, "SSN should be 9 digits in format XXX-XX-XXXX"
        
        # Format as XXX-XX-XXXX
        formatted_ssn = f"{clean_ssn[:3]}-{clean_ssn[3:5]}-{clean_ssn[5:]}"
        return True, formatted_ssn
    
    def calculate_dependent_eligibility(self, birth_date: str, relationship: str, tax_year: int) -> Dict[str, Any]:
        """Calculate dependent eligibility for Child Tax Credit."""
        
        try:
            birth_dt = datetime.strptime(birth_date, "%Y-%m-%d")
            age_at_year_end = tax_year - birth_dt.year
            
            # Adjust if birthday hasn't occurred yet in tax year
            if birth_dt.month > 12 or (birth_dt.month == 12 and birth_dt.day > 31):
                age_at_year_end -= 1
            
            qualifying_child = (
                age_at_year_end < 17 and 
                relationship.lower() in ["son", "daughter", "child", "stepchild", "adopted child"]
            )
            
            return {
                "age_at_year_end": age_at_year_end,
                "qualifying_child": qualifying_child,
                "eligible_for_ctc": qualifying_child,
                "ctc_amount": 2000 if qualifying_child else 0
            }
            
        except ValueError:
            return {
                "error": "Invalid birth date format. Please use YYYY-MM-DD"
            }
    
    def generate_organizer_content(self, intake_data: Dict[str, Any]) -> str:
        """Generate the Organizer.md content from collected intake data."""
        
        content = f"""# Tax Organizer - {intake_data.get('tax_year', 2025)}

## Taxpayer Information

**Filing Status:** {intake_data.get('filing_status', 'Not specified')}

**Address:**
{intake_data.get('address', {}).get('street', 'Not provided')}
{intake_data.get('address', {}).get('city', '')}, {intake_data.get('address', {}).get('state', '')} {intake_data.get('address', {}).get('zip', '')}

## Dependents

**Number of Dependents:** {intake_data.get('dependents_count', 0)}

"""
        
        dependents = intake_data.get('dependents_info', [])
        if dependents:
            for i, dep in enumerate(dependents, 1):
                content += f"""### Dependent {i}
- **Name:** {dep.get('name', 'Not provided')}
- **SSN:** {dep.get('ssn', 'Not provided')}
- **Relationship:** {dep.get('relationship', 'Not provided')}
- **Birth Date:** {dep.get('birth_date', 'Not provided')}
- **Qualifying Child for CTC:** {'Yes' if dep.get('qualifying_child', False) else 'No'}

"""
        
        bank_info = intake_data.get('bank_info', {})
        if bank_info:
            content += f"""## Direct Deposit Information

**Bank Name:** {bank_info.get('bank_name', 'Not provided')}
**Routing Number:** {bank_info.get('routing_number', 'Not provided')}
**Account Number:** {bank_info.get('account_number', 'Not provided')}
**Account Type:** {bank_info.get('account_type', 'Checking')}

"""
        
        content += f"""## Collection Date

This organizer was completed on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}.

## Next Steps

1. Upload W-2 forms
2. Review and calculate tax liability
3. Generate draft 1040
4. Review and approve for filing
"""
        
        return content
