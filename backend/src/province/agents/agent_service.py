"""
AWS Bedrock Agent Service

This service orchestrates interactions with AWS Bedrock Agents managed service.
It uses AWS's AgentCore, not custom orchestration.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .bedrock_agent_client import BedrockAgentClient, AgentSession, AgentResponse
from .models import model_registry

logger = logging.getLogger(__name__)


@dataclass
class LegalAgentConfig:
    """Configuration for a legal agent"""
    agent_id: str
    agent_alias_id: str
    name: str
    description: str
    instruction: str
    foundation_model: str
    knowledge_bases: List[str]
    action_groups: List[str]


class AgentService:
    """
    Service for managing AI agents using AWS Bedrock Agents.
    
    This service uses AWS's managed AgentCore orchestrator and does not
    implement custom agent logic.
    """
    
    def __init__(self):
        self.bedrock_client = BedrockAgentClient()
        self.agents: Dict[str, LegalAgentConfig] = {}
        self.active_sessions: Dict[str, AgentSession] = {}
        
    def register_agent(self, config: LegalAgentConfig):
        """Register a legal agent configuration"""
        self.agents[config.name] = config
        logger.info(f"Registered legal agent: {config.name}")
        
    def create_session(self, agent_name: str) -> AgentSession:
        """Create a new session with a legal agent"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
            
        config = self.agents[agent_name]
        session = self.bedrock_client.create_session(
            agent_id=config.agent_id,
            agent_alias_id=config.agent_alias_id
        )
        
        self.active_sessions[session.session_id] = session
        logger.info(f"Created session {session.session_id} for agent {agent_name}")
        
        return session
        
    def chat_with_agent(
        self,
        session_id: str,
        message: str,
        enable_trace: bool = False
    ) -> AgentResponse:
        """
        Send a message to an agent and get response.
        
        This uses AWS's AgentCore orchestrator - no custom logic.
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found. Please create a new session first.")
            
        session = self.active_sessions[session_id]
        config = self.agents.get(session.agent_id)
        
        if not config:
            # Find config by agent_id
            for agent_config in self.agents.values():
                if agent_config.agent_id == session.agent_id:
                    config = agent_config
                    break
                    
        if not config:
            raise ValueError(f"Agent configuration not found for session {session_id}")
            
        try:
            # Use real Bedrock agent invocation (no mock responses)
            logger.info(f"Invoking Bedrock agent: {config.agent_id}")
            
            response = self.bedrock_client.invoke_agent(
                agent_id=config.agent_id,
                agent_alias_id=config.agent_alias_id,
                session_id=session_id,
                input_text=message,
                enable_trace=enable_trace
            )
            
            logger.info(f"Agent response for session {session_id}: {len(response.response_text)} characters")
            return response
            
        except Exception as e:
            logger.error(f"Error in agent chat: {str(e)}")
            raise
            
    def get_agent_info(self, agent_name: str) -> Dict[str, Any]:
        """Get information about an agent"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
            
        config = self.agents[agent_name]
        
        try:
            agent_info = self.bedrock_client.get_agent_info(config.agent_id)
            action_groups = self.bedrock_client.list_agent_action_groups(config.agent_id)
            knowledge_bases = self.bedrock_client.list_agent_knowledge_bases(config.agent_id)
            
            return {
                "config": config,
                "agent_info": agent_info,
                "action_groups": action_groups,
                "knowledge_bases": knowledge_bases
            }
            
        except Exception as e:
            logger.error(f"Error getting agent info: {str(e)}")
            raise
            
    def list_active_sessions(self) -> List[AgentSession]:
        """List all active sessions"""
        return list(self.active_sessions.values())
        
    def close_session(self, session_id: str):
        """Close an agent session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Closed session {session_id}")


# Global agent service instance
agent_service = AgentService()


def register_tax_agents():
    """Register the tax filing agents"""
    
    # TaxPlannerAgent
    tax_planner_agent = LegalAgentConfig(
        agent_id="YLNFZM0YEM",  # us-east-1 agent ID
        agent_alias_id="TSTALIASID",  # Test alias that should work
        name="TaxPlannerAgent",
        description="AI agent specialized in tax planning and filing coordination",
        instruction="""You are the Tax Planner Agent for Province Tax Filing System. You help users with simple W-2 employee tax returns.

        Your responsibilities:
        1. Guide users through the tax filing process
        2. Only handle simple W-2 employee returns (no complex situations)
        3. Collect basic information: filing status, dependents, W-2 forms
        4. Provide clear, helpful guidance throughout the process

        SCOPE LIMITATIONS - You MUST reject requests for:
        - Self-employment income
        - Investment income  
        - Rental income
        - Complex tax situations

        Always maintain a helpful, professional tone and explain what you're doing at each step.""",
        foundation_model="arn:aws:bedrock:us-east-1:[REDACTED-ACCOUNT-ID]:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        knowledge_bases=["tax_code"],
        action_groups=["save_document", "get_signed_url", "ingest_w2", "calc_1040", "render_1040_draft", "create_deadline", "pii_scan"]
    )
    agent_service.register_agent(tax_planner_agent)
    
    # TaxIntakeAgent
    tax_intake_agent = LegalAgentConfig(
        agent_id="ZHQN5UJYEV",  # us-east-1 agent ID
        agent_alias_id="TSTALIASID",
        name="TaxIntakeAgent",
        description="AI agent specialized in collecting tax filing information",
        instruction="""You are the Tax Intake Agent. Your role is to collect essential information for tax filing.

        Collect:
        - Filing status (Single, Married Filing Jointly, etc.)
        - Number of dependents and basic info
        - Address and ZIP code
        - Bank information for refund (optional)
        - State information

        Always be thorough but friendly in collecting this information.""",
        foundation_model="arn:aws:bedrock:us-east-1:[REDACTED-ACCOUNT-ID]:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        knowledge_bases=["tax_code"],
        action_groups=["save_document", "get_signed_url", "ingest_w2", "calc_1040"]
    )
    agent_service.register_agent(tax_intake_agent)
    
    # ReviewAgent
    review_agent = LegalAgentConfig(
        agent_id="66F6XWZQ9C",  # us-east-1 agent ID
        agent_alias_id="TSTALIASID",
        name="ReviewAgent",
        description="AI agent specialized in reviewing tax calculations, generating PDFs, and final compliance",
        instruction="""You are the Review Agent. You create plain-English summaries of tax calculations and handle final processing.

        Your responsibilities:
        - Generate clear, understandable summaries
        - Explain how refund/amount due was calculated
        - Include proper citations to source documents
        - Create checklists for missing information
        - Generate PDF tax returns using render_1040_draft tool
        - Create tax filing deadlines and calendar events
        - Perform final compliance checks and PII scanning
        - Ensure accuracy and completeness""",
        foundation_model="arn:aws:bedrock:us-east-1:[REDACTED-ACCOUNT-ID]:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        knowledge_bases=["tax_code"],
        action_groups=["save_document", "render_1040_draft", "create_deadline", "pii_scan"]
    )
    agent_service.register_agent(review_agent)


def register_legal_agents():
    """Register the legal OS agents (deprecated - use register_tax_agents)"""
    # This function is deprecated in favor of register_tax_agents
    pass


# Initialize tax agents (replaces legal agents)
# register_tax_agents() is called from main.py during startup