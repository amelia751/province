"""
AWS Bedrock Agents Client

This client interfaces with AWS Bedrock Agents managed service.
It does NOT implement custom orchestration - it uses AWS's AgentCore.
"""

import boto3
import json
import logging
import os
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
        
        # Use Bedrock-specific credentials if available
        bedrock_access_key = os.getenv("BEDROCK_AWS_ACCESS_KEY_ID")
        bedrock_secret_key = os.getenv("BEDROCK_AWS_SECRET_ACCESS_KEY")
        
        logger.info(f"Bedrock credentials check - Access Key: {'***' + bedrock_access_key[-4:] if bedrock_access_key else 'NOT_FOUND'}")
        
        if bedrock_access_key and bedrock_secret_key:
            # Use Bedrock-specific credentials
            logger.info("Using Bedrock-specific credentials")
            self.bedrock_agent_runtime = boto3.client(
                'bedrock-agent-runtime',
                region_name=region_name,
                aws_access_key_id=bedrock_access_key,
                aws_secret_access_key=bedrock_secret_key
            )
            self.bedrock_agent = boto3.client(
                'bedrock-agent',
                region_name=region_name,
                aws_access_key_id=bedrock_access_key,
                aws_secret_access_key=bedrock_secret_key
            )
        else:
            # Fall back to default credentials
            logger.warning("Falling back to default AWS credentials")
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
    
    async def create_agent(self, agent_name: str, instruction: str, foundation_model: str, tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new Bedrock Agent"""
        try:
            # Create the agent
            response = self.bedrock_agent.create_agent(
                agentName=agent_name,
                instruction=instruction,
                foundationModel=foundation_model,
                description=f"Tax filing agent: {agent_name}",
                idleSessionTTLInSeconds=1800,  # 30 minutes
                agentResourceRoleArn=self._get_agent_role_arn()
            )
            
            agent_id = response['agent']['agentId']
            
            # If tools are provided, create action groups
            if tools:
                await self._create_action_groups(agent_id, tools)
            
            # Prepare the agent
            self.bedrock_agent.prepare_agent(agentId=agent_id)
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise
    
    async def create_agent_alias(self, agent_id: str, agent_alias_name: str) -> Dict[str, Any]:
        """Create an alias for a Bedrock Agent"""
        try:
            response = self.bedrock_agent.create_agent_alias(
                agentId=agent_id,
                agentAliasName=agent_alias_name,
                description=f"Alias for agent {agent_id}"
            )
            return response
        except Exception as e:
            logger.error(f"Error creating agent alias: {str(e)}")
            raise
    
    def _get_agent_role_arn(self) -> str:
        """Get the IAM role ARN for Bedrock agents"""
        # Check if role ARN is provided in environment
        role_arn = os.getenv('BEDROCK_AGENT_ROLE_ARN')
        if role_arn:
            return role_arn
        
        # Fall back to constructing the ARN
        account_id = boto3.client('sts').get_caller_identity()['Account']
        return f"arn:aws:iam::{account_id}:role/ProvinceBedrockAgentRole"
    
    async def _create_action_groups(self, agent_id: str, tools: List[Dict[str, Any]]):
        """Create action groups for the agent tools"""
        try:
            # Create a single action group with all tools
            action_group_name = "TaxFilingTools"
            
            # Convert tools to action group format
            api_schema = {
                "openapi": "3.0.0",
                "info": {
                    "title": "Tax Filing Tools API",
                    "version": "1.0.0"
                },
                "paths": {}
            }
            
            for tool in tools:
                tool_spec = tool.get('toolSpec', {})
                tool_name = tool_spec.get('name')
                tool_description = tool_spec.get('description')
                input_schema = tool_spec.get('inputSchema', {})
                
                api_schema['paths'][f"/{tool_name}"] = {
                    "post": {
                        "summary": tool_description,
                        "operationId": tool_name,
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": input_schema.get('json', {})
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            
            # Create the action group
            self.bedrock_agent.create_agent_action_group(
                agentId=agent_id,
                agentVersion="DRAFT",
                actionGroupName=action_group_name,
                description="Tools for tax filing operations",
                actionGroupExecutor={
                    'lambda': self._get_lambda_function_arn()
                },
                apiSchema={
                    'payload': json.dumps(api_schema)
                }
            )
            
        except Exception as e:
            logger.error(f"Error creating action groups: {str(e)}")
            raise
    
    def _get_lambda_function_arn(self) -> str:
        """Get the Lambda function ARN for action group execution"""
        # Check if Lambda ARN is provided in environment
        lambda_arn = os.getenv('LAMBDA_FUNCTION_ARN')
        if lambda_arn:
            return lambda_arn
        
        # Fall back to constructing the ARN
        account_id = boto3.client('sts').get_caller_identity()['Account']
        return f"arn:aws:lambda:{self.region_name}:{account_id}:function:province-tax-filing-tools"