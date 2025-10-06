"""Return Render Agent - Generates PDF 1040 forms from calculation data."""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from province.core.config import get_settings
from province.agents.bedrock_agent_client import BedrockAgentClient

logger = logging.getLogger(__name__)


class ReturnRenderAgent:
    """
    Return Render Agent - Creates PDF 1040 forms from tax calculations.
    
    This agent:
    1. Loads calculation data from Calc_1040_Simple.json
    2. Fills a 1040 PDF template with calculated values
    3. Embeds provenance information (calculation hash, tool versions)
    4. Saves the draft PDF to /Returns/1040_Draft.pdf
    5. Ensures the PDF is ready for review and filing
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.bedrock_client = BedrockAgentClient()
        self.agent_id = None
        self.agent_alias_id = None
        
    async def create_agent(self) -> str:
        """Create the Return Render Agent in AWS Bedrock."""
        
        instruction = """You are the Return Render Agent for Province Tax Filing System. Your job is to generate accurate, properly formatted PDF 1040 tax returns from calculation data.

RENDERING WORKFLOW:
1. Load tax calculation data from Calc_1040_Simple.json
2. Load W-2 extract data for detailed information
3. Load taxpayer information from intake data
4. Fill PDF 1040 template with all calculated values
5. Add metadata and provenance information
6. Save as /Returns/1040_Draft.pdf

KEY 1040 FORM FIELDS TO POPULATE:
- Line 1a: Total wages from W-2s (Box 1)
- Line 11b: Adjusted Gross Income
- Line 12: Standard deduction amount
- Line 15: Taxable income
- Line 16: Tax liability
- Line 19: Child Tax Credit (if applicable)
- Line 24: Total tax after credits
- Line 25a-d: Federal withholding from W-2s
- Line 34: Refund amount (if applicable)
- Line 37: Amount you owe (if applicable)

FORM REQUIREMENTS:
- Use official IRS 1040 form layout
- Ensure all monetary amounts are properly formatted
- Include taxpayer name, SSN, address
- Add spouse information if married filing jointly
- Include dependent information if applicable
- Sign and date the return (electronically)

QUALITY CHECKS:
- Verify all calculations match the Calc_1040_Simple.json
- Ensure no fields are left blank that should have values
- Check that refund/owe amounts are correct
- Validate SSN and EIN formats
- Confirm filing status is properly indicated"""

        tools = [
            {
                "toolSpec": {
                    "name": "load_return_data",
                    "description": "Load all data needed for return generation",
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
                    "name": "fill_1040_template",
                    "description": "Fill PDF 1040 template with tax data",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "template_path": {"type": "string"},
                                "tax_data": {"type": "object"},
                                "taxpayer_info": {"type": "object"}
                            },
                            "required": ["template_path", "tax_data"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "add_pdf_metadata",
                    "description": "Add metadata and provenance to PDF",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "pdf_path": {"type": "string"},
                                "metadata": {"type": "object"}
                            },
                            "required": ["pdf_path", "metadata"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "validate_1040_pdf",
                    "description": "Validate the generated 1040 PDF",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "pdf_path": {"type": "string"},
                                "expected_values": {"type": "object"}
                            },
                            "required": ["pdf_path", "expected_values"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "save_draft_return",
                    "description": "Save the draft return PDF",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "engagement_id": {"type": "string"},
                                "pdf_content": {"type": "string"},
                                "metadata": {"type": "object"}
                            },
                            "required": ["engagement_id", "pdf_content"]
                        }
                    }
                }
            }
        ]
        
        # Create the agent
        response = await self.bedrock_client.create_agent(
            agent_name="ReturnRenderAgent",
            instruction=instruction,
            foundation_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            tools=tools
        )
        
        self.agent_id = response["agent"]["agentId"]
        logger.info(f"Created Return Render agent with ID: {self.agent_id}")
        
        # Create alias
        alias_response = await self.bedrock_client.create_agent_alias(
            agent_id=self.agent_id,
            agent_alias_name="DRAFT"
        )
        
        self.agent_alias_id = alias_response["agentAlias"]["agentAliasId"]
        logger.info(f"Created agent alias with ID: {self.agent_alias_id}")
        
        return self.agent_id
    
    async def invoke(self, session_id: str, input_text: str, engagement_id: str) -> Dict[str, Any]:
        """Invoke the Return Render agent."""
        
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
