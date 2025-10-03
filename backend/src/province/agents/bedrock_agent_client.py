"""
AWS Bedrock Agents Client

This client interfaces with AWS Bedrock Agents managed service.
It does NOT implement custom orchestration - it uses AWS's AgentCore.
"""

import boto3
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AgentSession:
    """Represents a session with AWS Bedrock Agent"""
    session_id: str
    agent_id: str
    agent_alias_id: str
    created_at: datetime
    
    
@dataclass
class AgentResponse:
    """Response from AWS Bedrock Agent"""
    response_text: str
    session_id: str
    citations: List[Dict[str, Any]]
    trace: Optional[Dict[str, Any]] = None


class BedrockAgentClient:
    """
    Client for AWS Bedrock Agents managed service.
    
    This uses AWS's native AgentCore orchestrator and Action Groups,
    not custom orchestration logic.
    """
    
    def __init__(self, region_name: str = "us-east-1"):
        self.region_name = region_name
        self.bedrock_agent_runtime = boto3.client(
            'bedrock-agent-runtime',
            region_name=region_name
        )
        self.bedrock_agent = boto3.client(
            'bedrock-agent',
            region_name=region_name
        )
        
    def invoke_agent(
        self,
        agent_id: str,
        agent_alias_id: str,
        session_id: str,
        input_text: str,
        enable_trace: bool = False
    ) -> AgentResponse:
        """
        Invoke AWS Bedrock Agent using the managed service.
        
        This calls AWS's AgentCore orchestrator directly - no custom logic.
        """
        try:
            response = self.bedrock_agent_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=input_text,
                enableTrace=enable_trace
            )
            
            # Process the streaming response
            response_text = ""
            citations = []
            trace_data = None
            
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        response_text += chunk['bytes'].decode('utf-8')
                    if 'attribution' in chunk:
                        citations.extend(chunk['attribution'].get('citations', []))
                        
                if 'trace' in event and enable_trace:
                    trace_data = event['trace']
                    
            return AgentResponse(
                response_text=response_text,
                session_id=session_id,
                citations=citations,
                trace=trace_data
            )
            
        except Exception as e:
            logger.error(f"Error invoking Bedrock Agent: {str(e)}")
            raise
            
    def create_session(self, agent_id: str, agent_alias_id: str) -> AgentSession:
        """Create a new session with the Bedrock Agent"""
        import uuid
        session_id = str(uuid.uuid4())
        
        return AgentSession(
            session_id=session_id,
            agent_id=agent_id,
            agent_alias_id=agent_alias_id,
            created_at=datetime.utcnow()
        )
        
    def get_agent_info(self, agent_id: str) -> Dict[str, Any]:
        """Get information about a Bedrock Agent"""
        try:
            response = self.bedrock_agent.get_agent(agentId=agent_id)
            return response['agent']
        except Exception as e:
            logger.error(f"Error getting agent info: {str(e)}")
            raise
            
    def list_agent_action_groups(self, agent_id: str, agent_version: str = "DRAFT") -> List[Dict[str, Any]]:
        """List Action Groups for a Bedrock Agent"""
        try:
            response = self.bedrock_agent.list_agent_action_groups(
                agentId=agent_id,
                agentVersion=agent_version
            )
            return response['actionGroupSummaries']
        except Exception as e:
            logger.error(f"Error listing action groups: {str(e)}")
            raise
            
    def list_agent_knowledge_bases(self, agent_id: str, agent_version: str = "DRAFT") -> List[Dict[str, Any]]:
        """List Knowledge Bases associated with a Bedrock Agent"""
        try:
            response = self.bedrock_agent.list_agent_knowledge_bases(
                agentId=agent_id,
                agentVersion=agent_version
            )
            return response['agentKnowledgeBaseSummaries']
        except Exception as e:
            logger.error(f"Error listing knowledge bases: {str(e)}")
            raise