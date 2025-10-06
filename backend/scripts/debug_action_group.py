#!/usr/bin/env python3
"""Debug action group creation with the simplest possible schema."""

import boto3
import json
import os
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_bedrock_client():
    """Get Bedrock client using the Bedrock-specific credentials."""
    
    bedrock_access_key = os.getenv("BEDROCK_AWS_ACCESS_KEY_ID")
    bedrock_secret_key = os.getenv("BEDROCK_AWS_SECRET_ACCESS_KEY")
    
    return boto3.client(
        'bedrock-agent',
        region_name='us-east-2',
        aws_access_key_id=bedrock_access_key,
        aws_secret_access_key=bedrock_secret_key
    )


def get_lambda_arn():
    """Get the Lambda function ARN."""
    account_id = boto3.client('sts').get_caller_identity()['Account']
    return f"arn:aws:lambda:us-east-2:{account_id}:function:province-tax-filing-tools"


def create_super_minimal_schema():
    """Create the absolute minimal OpenAPI schema."""
    
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Tax Tools",
            "version": "1.0.0"
        },
        "paths": {
            "/hello": {
                "post": {
                    "summary": "Hello world",
                    "operationId": "hello",
                    "responses": {
                        "200": {
                            "description": "Success"
                        }
                    }
                }
            }
        }
    }


def test_schema_creation():
    """Test creating a single action group with minimal schema."""
    
    bedrock_agent = get_bedrock_client()
    lambda_arn = get_lambda_arn()
    agent_id = 'DM6OT8QW8S'  # TaxPlanner
    
    try:
        # First, let's check if Lambda function exists
        lambda_client = boto3.client('lambda', region_name='us-east-2')
        try:
            lambda_client.get_function(FunctionName='province-tax-filing-tools')
            print("✅ Lambda function exists")
        except ClientError as e:
            print(f"❌ Lambda function issue: {e}")
            return
        
        # Check current action groups
        existing_groups = bedrock_agent.list_agent_action_groups(
            agentId=agent_id,
            agentVersion="DRAFT"
        )
        print(f"Current action groups: {len(existing_groups.get('actionGroupSummaries', []))}")
        
        # Try to create with minimal schema
        schema = create_super_minimal_schema()
        print("Schema to be used:")
        print(json.dumps(schema, indent=2))
        
        response = bedrock_agent.create_agent_action_group(
            agentId=agent_id,
            agentVersion="DRAFT",
            actionGroupName="TestTools",
            description="Test tools",
            actionGroupExecutor={
                'lambda': lambda_arn
            },
            apiSchema={
                'payload': json.dumps(schema)
            }
        )
        
        print("✅ SUCCESS! Action group created:")
        print(f"Action Group ID: {response['agentActionGroup']['actionGroupId']}")
        
        # Now prepare the agent
        bedrock_agent.prepare_agent(agentId=agent_id)
        print("✅ Agent prepared successfully")
        
    except ClientError as e:
        print(f"❌ Error: {e}")
        print(f"Error code: {e.response['Error']['Code']}")
        print(f"Error message: {e.response['Error']['Message']}")


if __name__ == "__main__":
    test_schema_creation()
