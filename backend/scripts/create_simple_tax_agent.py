#!/usr/bin/env python3
"""Script to create a simple tax agent for testing."""

import boto3
import os
import json
from botocore.exceptions import ClientError


def create_bedrock_agent_role():
    """Create IAM role for Bedrock agents."""
    
    iam = boto3.client('iam')
    
    # Trust policy for Bedrock
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
    
    # Policy for Bedrock agent permissions
    agent_policy = {
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
                    "lambda:InvokeFunction"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                "Resource": "arn:aws:s3:::province-documents-storage/*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                "Resource": [
                    "arn:aws:dynamodb:*:*:table/province-tax-*"
                ]
            }
        ]
    }
    
    role_name = "BedrockAgentRole"
    
    try:
        # Create the role
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="IAM role for Bedrock agents"
        )
        
        # Attach the policy
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="BedrockAgentPolicy",
            PolicyDocument=json.dumps(agent_policy)
        )
        
        print(f"✅ Created IAM role: {role_name}")
        
        # Get the role ARN
        response = iam.get_role(RoleName=role_name)
        return response['Role']['Arn']
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print(f"IAM role {role_name} already exists")
            response = iam.get_role(RoleName=role_name)
            return response['Role']['Arn']
        else:
            print(f"❌ Error creating IAM role: {e}")
            raise


def create_simple_tax_planner():
    """Create a simple tax planner agent."""
    
    # First create the IAM role
    role_arn = create_bedrock_agent_role()
    
    # Create Bedrock agent
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-2')
    
    instruction = """You are the Tax Planner Agent for Province Tax Filing System. You help users with simple W-2 employee tax returns.

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

Always maintain a helpful, professional tone and explain what you're doing at each step."""

    try:
        response = bedrock_agent.create_agent(
            agentName="TaxPlannerAgent",
            instruction=instruction,
            foundationModel="anthropic.claude-3-5-sonnet-20241022-v2:0",
            description="Tax filing agent for simple W-2 returns",
            idleSessionTTLInSeconds=1800,
            agentResourceRoleArn=role_arn
        )
        
        agent_id = response['agent']['agentId']
        print(f"✅ Created agent: {agent_id}")
        
        # Prepare the agent
        bedrock_agent.prepare_agent(agentId=agent_id)
        print("✅ Agent prepared")
        
        # Create alias
        alias_response = bedrock_agent.create_agent_alias(
            agentId=agent_id,
            agentAliasName="DRAFT",
            description="Draft alias for tax planner agent"
        )
        
        alias_id = alias_response['agentAlias']['agentAliasId']
        print(f"✅ Created alias: {alias_id}")
        
        return {
            'agent_id': agent_id,
            'alias_id': alias_id
        }
        
    except ClientError as e:
        print(f"❌ Error creating agent: {e}")
        raise


if __name__ == "__main__":
    print("Creating simple tax planner agent...")
    result = create_simple_tax_planner()
    print(f"Agent ID: {result['agent_id']}")
    print(f"Alias ID: {result['alias_id']}")
    print("Done!")
