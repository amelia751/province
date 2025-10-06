#!/usr/bin/env python3
"""Check Bedrock permissions and try a simple agent creation."""

import boto3
from botocore.exceptions import ClientError


def check_bedrock_permissions():
    """Check if we have the necessary Bedrock permissions."""
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-2')
    
    print("🔍 Checking Bedrock permissions...")
    
    # Test 1: List agents
    try:
        response = bedrock_agent.list_agents()
        print("✅ bedrock:ListAgents - OK")
    except ClientError as e:
        print(f"❌ bedrock:ListAgents - {e}")
        return False
    
    # Test 2: Try to create a simple agent (we'll delete it right after)
    try:
        # Get account ID for role ARN
        account_id = boto3.client('sts').get_caller_identity()['Account']
        role_arn = f"arn:aws:iam::{account_id}:role/ProvinceBedrockAgentRole"
        
        response = bedrock_agent.create_agent(
            agentName="TestAgent",
            instruction="This is a test agent",
            foundationModel="anthropic.claude-3-5-sonnet-20241022-v2:0",
            description="Test agent for permission check",
            agentResourceRoleArn=role_arn
        )
        
        agent_id = response['agent']['agentId']
        print(f"✅ bedrock:CreateAgent - OK (created {agent_id})")
        
        # Clean up - delete the test agent
        try:
            bedrock_agent.delete_agent(agentId=agent_id)
            print("✅ Test agent cleaned up")
        except:
            print("⚠️  Could not clean up test agent")
        
        return True
        
    except ClientError as e:
        print(f"❌ bedrock:CreateAgent - {e}")
        return False


def main():
    """Main function."""
    
    print("🚀 Checking Bedrock permissions for province user...")
    print("=" * 60)
    
    if check_bedrock_permissions():
        print("\n✅ All Bedrock permissions are working!")
        print("🎯 Ready to deploy tax agents!")
    else:
        print("\n❌ Missing Bedrock permissions")
        print("📋 You need to add these permissions to the province user:")
        print("""
{
    "Effect": "Allow",
    "Action": [
        "bedrock:*"
    ],
    "Resource": "*"
}
        """)


if __name__ == "__main__":
    main()
