"""
AWS Infrastructure for Bedrock Agents

This module contains the infrastructure code for deploying AWS Bedrock Agents
with Action Groups and Knowledge Bases.
"""

import boto3
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AgentInfrastructureConfig:
    """Configuration for agent infrastructure deployment"""
    agent_name: str
    description: str
    instruction: str
    foundation_model_arn: str
    agent_role_arn: str
    knowledge_base_ids: List[str]
    action_group_configs: List[Dict[str, Any]]


class BedrockAgentInfrastructure:
    """
    Infrastructure manager for AWS Bedrock Agents.
    
    This creates and manages the AWS resources needed for Bedrock Agents:
    - Bedrock Agents
    - Action Groups
    - Knowledge Bases
    - IAM roles and policies
    """
    
    def __init__(self, region_name: str = "us-east-1"):
        self.region_name = region_name
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=region_name)
        self.iam = boto3.client('iam', region_name=region_name)
        self.lambda_client = boto3.client('lambda', region_name=region_name)
        
    def create_agent_role(self, agent_name: str) -> str:
        """Create IAM role for Bedrock Agent"""
        role_name = f"BedrockAgent-{agent_name}-Role"
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:Retrieve",
                        "bedrock:RetrieveAndGenerate"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "lambda:InvokeFunction"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            # Create role
            role_response = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"IAM role for Bedrock Agent {agent_name}"
            )
            
            # Attach inline policy
            self.iam.put_role_policy(
                RoleName=role_name,
                PolicyName=f"BedrockAgent-{agent_name}-Policy",
                PolicyDocument=json.dumps(policy_document)
            )
            
            logger.info(f"Created IAM role: {role_name}")
            return role_response['Role']['Arn']
            
        except Exception as e:
            logger.error(f"Error creating agent role: {str(e)}")
            raise
            
    def create_bedrock_agent(self, config: AgentInfrastructureConfig) -> str:
        """Create a Bedrock Agent"""
        try:
            response = self.bedrock_agent.create_agent(
                agentName=config.agent_name,
                description=config.description,
                instruction=config.instruction,
                foundationModel=config.foundation_model_arn,
                agentResourceRoleArn=config.agent_role_arn,
                idleSessionTTLInSeconds=1800,  # 30 minutes
                tags={
                    'Project': 'Province-Legal-OS',
                    'Environment': 'development'
                }
            )
            
            agent_id = response['agent']['agentId']
            logger.info(f"Created Bedrock Agent: {config.agent_name} (ID: {agent_id})")
            
            return agent_id
            
        except Exception as e:
            logger.error(f"Error creating Bedrock Agent: {str(e)}")
            raise
            
    def create_action_group(
        self,
        agent_id: str,
        action_group_name: str,
        description: str,
        lambda_function_arn: str,
        api_schema: Dict[str, Any]
    ) -> str:
        """Create an Action Group for a Bedrock Agent"""
        try:
            response = self.bedrock_agent.create_agent_action_group(
                agentId=agent_id,
                agentVersion="DRAFT",
                actionGroupName=action_group_name,
                description=description,
                actionGroupExecutor={
                    'lambda': lambda_function_arn
                },
                apiSchema={
                    'payload': json.dumps(api_schema)
                }
            )
            
            action_group_id = response['agentActionGroup']['actionGroupId']
            logger.info(f"Created Action Group: {action_group_name} (ID: {action_group_id})")
            
            return action_group_id
            
        except Exception as e:
            logger.error(f"Error creating Action Group: {str(e)}")
            raise
            
    def associate_knowledge_base(
        self,
        agent_id: str,
        knowledge_base_id: str,
        description: str
    ) -> str:
        """Associate a Knowledge Base with a Bedrock Agent"""
        try:
            response = self.bedrock_agent.associate_agent_knowledge_base(
                agentId=agent_id,
                agentVersion="DRAFT",
                knowledgeBaseId=knowledge_base_id,
                description=description,
                knowledgeBaseState="ENABLED"
            )
            
            association_id = response['agentKnowledgeBase']['agentId']
            logger.info(f"Associated Knowledge Base {knowledge_base_id} with Agent {agent_id}")
            
            return association_id
            
        except Exception as e:
            logger.error(f"Error associating Knowledge Base: {str(e)}")
            raise
            
    def prepare_agent(self, agent_id: str) -> str:
        """Prepare (build) a Bedrock Agent"""
        try:
            response = self.bedrock_agent.prepare_agent(agentId=agent_id)
            
            preparation_id = response['agentId']
            logger.info(f"Started preparation for Agent {agent_id}")
            
            return preparation_id
            
        except Exception as e:
            logger.error(f"Error preparing agent: {str(e)}")
            raise
            
    def create_agent_alias(
        self,
        agent_id: str,
        alias_name: str,
        description: str
    ) -> str:
        """Create an alias for a Bedrock Agent"""
        try:
            response = self.bedrock_agent.create_agent_alias(
                agentId=agent_id,
                agentAliasName=alias_name,
                description=description,
                tags={
                    'Project': 'Province-Legal-OS',
                    'Environment': 'development'
                }
            )
            
            alias_id = response['agentAlias']['agentAliasId']
            logger.info(f"Created Agent Alias: {alias_name} (ID: {alias_id})")
            
            return alias_id
            
        except Exception as e:
            logger.error(f"Error creating agent alias: {str(e)}")
            raise
            
    def deploy_complete_agent(self, config: AgentInfrastructureConfig) -> Dict[str, str]:
        """Deploy a complete Bedrock Agent with all components"""
        try:
            # Create agent
            agent_id = self.create_bedrock_agent(config)
            
            # Create action groups
            action_group_ids = []
            for ag_config in config.action_group_configs:
                ag_id = self.create_action_group(
                    agent_id=agent_id,
                    action_group_name=ag_config['name'],
                    description=ag_config['description'],
                    lambda_function_arn=ag_config['lambda_arn'],
                    api_schema=ag_config['api_schema']
                )
                action_group_ids.append(ag_id)
                
            # Associate knowledge bases
            kb_associations = []
            for kb_id in config.knowledge_base_ids:
                assoc_id = self.associate_knowledge_base(
                    agent_id=agent_id,
                    knowledge_base_id=kb_id,
                    description=f"Knowledge base for {config.agent_name}"
                )
                kb_associations.append(assoc_id)
                
            # Prepare agent
            self.prepare_agent(agent_id)
            
            # Create alias
            alias_id = self.create_agent_alias(
                agent_id=agent_id,
                alias_name="development",
                description=f"Development alias for {config.agent_name}"
            )
            
            return {
                'agent_id': agent_id,
                'alias_id': alias_id,
                'action_group_ids': action_group_ids,
                'knowledge_base_associations': kb_associations
            }
            
        except Exception as e:
            logger.error(f"Error deploying complete agent: {str(e)}")
            raise


def create_legal_agent_infrastructure():
    """Create infrastructure for all legal agents"""
    
    infrastructure = BedrockAgentInfrastructure()
    
    # Legal Drafting Agent
    drafting_role_arn = infrastructure.create_agent_role("LegalDrafting")
    
    drafting_config = AgentInfrastructureConfig(
        agent_name="LegalDraftingAgent",
        description="AI agent for legal document drafting and review",
        instruction="""You are a legal drafting assistant specialized in creating and reviewing legal documents...""",
        foundation_model_arn="arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
        agent_role_arn=drafting_role_arn,
        knowledge_base_ids=["KB_LEGAL_CORPUS_ID"],
        action_group_configs=[
            {
                'name': 'LegalTools',
                'description': 'Tools for legal document operations',
                'lambda_arn': 'arn:aws:lambda:us-east-1:ACCOUNT:function:legal-tools',
                'api_schema': {
                    "openapi": "3.0.0",
                    "info": {"title": "Legal Tools", "version": "1.0.0"},
                    "paths": {
                        "/search_matter_corpus": {
                            "post": {
                                "operationId": "search_matter_corpus",
                                "summary": "Search legal documents",
                                "requestBody": {
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object",
                                                "properties": {
                                                    "query": {"type": "string"},
                                                    "matter_id": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ]
    )
    
    drafting_result = infrastructure.deploy_complete_agent(drafting_config)
    
    logger.info(f"Deployed Legal Drafting Agent: {drafting_result}")
    
    return {
        'legal_drafting': drafting_result
    }