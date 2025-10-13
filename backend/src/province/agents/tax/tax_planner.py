"""Tax Planner Agent - Router and orchestrator for tax filing workflow."""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from province.core.config import get_settings
from province.agents.bedrock_agent_client import BedrockAgentClient
from .models import TaxEngagement, EngagementStatus, FilingStatus

logger = logging.getLogger(__name__)


class TaxPlanner:
    """
    Tax Planner Agent - Routes user requests and orchestrates the tax filing workflow.
    
    This agent acts as the main router that:
    1. Reads user utterances and chooses the appropriate tool path
    2. Enforces tenant permissions and "simple W-2-only" guard rails
    3. Streams updates back to UI and logs tool calls for audit
    4. Orchestrates the overall tax filing workflow
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.bedrock_client = BedrockAgentClient()
        self.agent_id = None  # Will be set after deployment
        self.agent_alias_id = None
        
    async def create_agent(self) -> str:
        """Create the Tax Planner agent in AWS Bedrock."""
        
        instruction = """You are the Tax Planner Agent for Province Tax Filing System. You are the main router and orchestrator for tax filing workflows.

Your primary responsibilities:
1. Route user requests to appropriate specialized agents and tools
2. Enforce scope limitations - ONLY handle simple W-2 employee tax returns (no side gigs, investments, etc.)
3. Maintain engagement state and workflow progression
4. Provide clear, helpful guidance to users throughout the process
5. Stream progress updates and log all tool calls for audit
6. Handle W-2 document ingestion and OCR processing
7. Perform tax calculations for Form 1040
8. Generate PDF tax returns
9. Create tax filing deadlines and calendar events
10. Scan for PII and handle compliance checks

SCOPE LIMITATIONS - You MUST reject requests for:
- Self-employment income (1099-NEC, Schedule C)
- Investment income (1099-DIV, 1099-INT, Schedule D)
- Rental income (Schedule E)
- Business deductions beyond standard deduction
- Complex tax situations

WORKFLOW ORCHESTRATION:
1. When user uploads W-2 → Use ingest_w2 tool for OCR processing
2. If intake incomplete → Route to TaxIntakeAgent for filing status, dependents, ZIP
3. When ready → Use calc_1040 tool for tax calculation
4. After calculation → Route to ReviewAgent for plain-English summary
5. If approved → Use render_1040_pdf tool for PDF generation
6. Create deadlines → Use create_deadline tool for calendar events
7. Final compliance → Use scan_pii and compliance_check tools for approval

Always maintain a helpful, professional tone and explain what you're doing at each step."""

        tools = [
            {
                "toolSpec": {
                    "name": "create_tax_engagement",
                    "description": "Create a new tax engagement/matter",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "tenant_id": {"type": "string"},
                                "tax_year": {"type": "integer"},
                                "taxpayer_name": {"type": "string"}
                            },
                            "required": ["tenant_id", "tax_year", "taxpayer_name"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "get_engagement_status",
                    "description": "Get current status of a tax engagement",
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
                    "name": "update_engagement_status",
                    "description": "Update tax engagement status",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "engagement_id": {"type": "string"},
                                "status": {"type": "string"},
                                "notes": {"type": "string"}
                            },
                            "required": ["engagement_id", "status"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "route_to_intake_agent",
                    "description": "Route user to intake agent for collecting filing information",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "engagement_id": {"type": "string"},
                                "message": {"type": "string"}
                            },
                            "required": ["engagement_id"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "route_to_w2_ingest",
                    "description": "Route to W-2 ingestion agent for document processing",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "engagement_id": {"type": "string"},
                                "document_s3_key": {"type": "string"}
                            },
                            "required": ["engagement_id", "document_s3_key"]
                        }
                    }
                }
            },
            {
                "toolSpec": {
                    "name": "route_to_calculation",
                    "description": "Route to 1040 calculation agent",
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
                    "name": "route_to_review",
                    "description": "Route to review agent for generating plain-English summary",
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
            }
        ]
        
        # Create the agent
        response = await self.bedrock_client.create_agent(
            agent_name="TaxPlannerAgent",
            instruction=instruction,
            foundation_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            tools=tools
        )
        
        self.agent_id = response["agent"]["agentId"]
        logger.info(f"Created Tax Planner agent with ID: {self.agent_id}")
        
        # Create alias
        alias_response = await self.bedrock_client.create_agent_alias(
            agent_id=self.agent_id,
            agent_alias_name="DRAFT"
        )
        
        self.agent_alias_id = alias_response["agentAlias"]["agentAliasId"]
        logger.info(f"Created agent alias with ID: {self.agent_alias_id}")
        
        return self.agent_id
    
    async def invoke(self, session_id: str, input_text: str, engagement_id: Optional[str] = None) -> Dict[str, Any]:
        """Invoke the Tax Planner agent."""
        
        if not self.agent_id or not self.agent_alias_id:
            raise ValueError("Agent not deployed. Call create_agent() first.")
        
        # Add engagement context if available
        if engagement_id:
            input_text = f"[ENGAGEMENT_ID: {engagement_id}] {input_text}"
        
        response = await self.bedrock_client.invoke_agent(
            agent_id=self.agent_id,
            agent_alias_id=self.agent_alias_id,
            session_id=session_id,
            input_text=input_text
        )
        
        return response
    
    def validate_scope(self, user_input: str) -> tuple[bool, Optional[str]]:
        """
        Validate that the user request is within scope (simple W-2 only).
        
        Returns:
            tuple: (is_valid, rejection_reason)
        """
        
        # Keywords that indicate out-of-scope requests
        out_of_scope_keywords = [
            "1099", "schedule c", "self-employed", "business", "rental", 
            "investment", "stock", "crypto", "dividend", "interest",
            "freelance", "contractor", "side gig", "uber", "lyft",
            "airbnb", "schedule d", "schedule e", "itemize", "deductions"
        ]
        
        user_lower = user_input.lower()
        
        for keyword in out_of_scope_keywords:
            if keyword in user_lower:
                return False, f"I can only help with simple W-2 employee tax returns. {keyword.title()} income/deductions are outside my current scope. Please consult a tax professional for complex situations."
        
        return True, None
    
    async def create_engagement(self, tenant_id: str, tax_year: int, taxpayer_name: str) -> str:
        """Create a new tax engagement."""
        
        engagement_id = f"{taxpayer_name.replace(' ', '_')}_{tax_year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        engagement = TaxEngagement(
            engagement_id=engagement_id,
            tenant_id=tenant_id,
            tax_year=tax_year,
            status=EngagementStatus.DRAFT,
            created_by=tenant_id,  # For now, use tenant_id as user_id
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Save to DynamoDB (implementation needed)
        # await self._save_engagement(engagement)
        
        logger.info(f"Created tax engagement: {engagement_id}")
        return engagement_id
    
    async def get_workflow_status(self, engagement_id: str) -> Dict[str, Any]:
        """Get the current workflow status for an engagement."""
        
        # This would query DynamoDB to get current status
        # For now, return a placeholder
        return {
            "engagement_id": engagement_id,
            "status": "draft",
            "steps_completed": [],
            "next_steps": ["upload_w2", "collect_intake_info"]
        }
