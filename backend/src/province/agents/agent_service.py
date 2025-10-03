"""
AWS Bedrock Agent Service

This service orchestrates interactions with AWS Bedrock Agents managed service.
It uses AWS's AgentCore, not custom orchestration.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from .bedrock_agent_client import BedrockAgentClient, AgentSession, AgentResponse
from .knowledge_bases import knowledge_base_manager
from .models import model_registry
from .action_groups import action_group_registry

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


class LegalAgentService:
    """
    Service for managing legal AI agents using AWS Bedrock Agents.
    
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
            raise ValueError(f"Session {session_id} not found")
            
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
legal_agent_service = LegalAgentService()


def register_legal_agents():
    """Register the legal OS agents"""
    
    # Legal Drafting Agent
    drafting_agent = LegalAgentConfig(
        agent_id="AGENT_DRAFTING_ID",  # Will be set during deployment
        agent_alias_id="TSTALIASID",  # Test alias
        name="legal_drafting",
        description="AI agent specialized in legal document drafting and review",
        instruction="""You are a legal drafting assistant specialized in creating and reviewing legal documents. 
        
        Your capabilities include:
        - Drafting contracts, briefs, motions, and other legal documents
        - Reviewing documents for legal accuracy and completeness
        - Ensuring proper legal citations and formatting
        - Providing legal research and precedent analysis
        
        Always:
        - Use proper legal terminology and formatting
        - Include accurate citations when referencing case law or statutes
        - Maintain professional legal writing standards
        - Ask for clarification when requirements are ambiguous
        - Validate all citations before including them
        
        You have access to:
        - Legal document corpus through Knowledge Bases
        - Document storage and retrieval tools
        - Citation validation tools
        - Deadline management tools""",
        foundation_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
        knowledge_bases=["legal_corpus"],
        action_groups=["search_matter_corpus", "save_document", "validate_citations", "create_deadline"]
    )
    legal_agent_service.register_agent(drafting_agent)
    
    # Legal Research Agent
    research_agent = LegalAgentConfig(
        agent_id="AGENT_RESEARCH_ID",  # Will be set during deployment
        agent_alias_id="TSTALIASID",  # Test alias
        name="legal_research",
        description="AI agent specialized in legal research and analysis",
        instruction="""You are a legal research assistant specialized in finding and analyzing legal precedents, statutes, and case law.
        
        Your capabilities include:
        - Comprehensive legal research across multiple jurisdictions
        - Case law analysis and precedent identification
        - Statute and regulation interpretation
        - Legal trend analysis and pattern recognition
        
        Always:
        - Provide comprehensive research with multiple sources
        - Include proper legal citations for all references
        - Analyze the strength and relevance of precedents
        - Consider jurisdictional differences and applicability
        - Summarize key findings clearly and concisely
        
        You have access to:
        - Extensive legal database through Knowledge Bases
        - Search tools for matter-specific research
        - Citation validation capabilities""",
        foundation_model="amazon.nova-pro-v1:0",
        knowledge_bases=["legal_corpus", "matter_specific"],
        action_groups=["search_matter_corpus", "validate_citations"]
    )
    legal_agent_service.register_agent(research_agent)
    
    # Case Management Agent
    case_mgmt_agent = LegalAgentConfig(
        agent_id="AGENT_CASE_MGMT_ID",  # Will be set during deployment
        agent_alias_id="TSTALIASID",  # Test alias
        name="case_management",
        description="AI agent specialized in case and matter management",
        instruction="""You are a case management assistant specialized in organizing and tracking legal matters.
        
        Your capabilities include:
        - Matter organization and document management
        - Deadline tracking and calendar management
        - Task prioritization and workflow optimization
        - Progress tracking and status reporting
        
        Always:
        - Maintain accurate matter records and timelines
        - Set appropriate deadlines with sufficient lead time
        - Organize documents logically within matter structure
        - Provide clear status updates and progress reports
        - Alert to potential scheduling conflicts or missed deadlines
        
        You have access to:
        - Document storage and organization tools
        - Deadline creation and management tools
        - Matter search and retrieval capabilities""",
        foundation_model="amazon.nova-lite-v1:0",
        knowledge_bases=["matter_specific"],
        action_groups=["save_document", "create_deadline", "search_matter_corpus"]
    )
    legal_agent_service.register_agent(case_mgmt_agent)


# Initialize legal agents
register_legal_agents()