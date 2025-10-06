#!/usr/bin/env python3
"""Verify that the complete tax system is properly deployed."""

import boto3
import os
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_dynamodb_tables():
    """Check if all required DynamoDB tables exist."""
    
    dynamodb = boto3.client('dynamodb', region_name='us-east-2')
    
    required_tables = [
        'province-tax-engagements',
        'province-tax-documents', 
        'province-tax-permissions',
        'province-tax-deadlines',
        'province-tax-connections'
    ]
    
    print("📊 Checking DynamoDB Tables...")
    print("-" * 40)
    
    all_tables_exist = True
    
    for table_name in required_tables:
        try:
            response = dynamodb.describe_table(TableName=table_name)
            status = response['Table']['TableStatus']
            print(f"✅ {table_name}: {status}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"❌ {table_name}: NOT FOUND")
                all_tables_exist = False
            else:
                print(f"⚠️  {table_name}: ERROR - {e}")
                all_tables_exist = False
    
    return all_tables_exist


def check_iam_roles():
    """Check if required IAM roles exist."""
    
    iam = boto3.client('iam', region_name='us-east-2')
    
    required_roles = [
        'ProvinceBedrockAgentRole',
        'ProvinceTaxFilingLambdaRole'
    ]
    
    print("\n🔐 Checking IAM Roles...")
    print("-" * 40)
    
    all_roles_exist = True
    
    for role_name in required_roles:
        try:
            iam.get_role(RoleName=role_name)
            print(f"✅ {role_name}: EXISTS")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                print(f"❌ {role_name}: NOT FOUND")
                all_roles_exist = False
            else:
                print(f"⚠️  {role_name}: ERROR - {e}")
                all_roles_exist = False
    
    return all_roles_exist


def check_lambda_function():
    """Check if the Lambda function exists."""
    
    lambda_client = boto3.client('lambda', region_name='us-east-2')
    
    print("\n⚡ Checking Lambda Function...")
    print("-" * 40)
    
    try:
        response = lambda_client.get_function(FunctionName='province-tax-filing-tools')
        state = response['Configuration']['State']
        print(f"✅ province-tax-filing-tools: {state}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("❌ province-tax-filing-tools: NOT FOUND")
        else:
            print(f"⚠️  province-tax-filing-tools: ERROR - {e}")
        return False


def check_bedrock_agents():
    """Check if all Bedrock agents exist and are prepared."""
    
    bedrock_access_key = os.getenv("BEDROCK_AWS_ACCESS_KEY_ID")
    bedrock_secret_key = os.getenv("BEDROCK_AWS_SECRET_ACCESS_KEY")
    
    if not bedrock_access_key or not bedrock_secret_key:
        print("\n🤖 Checking Bedrock Agents...")
        print("-" * 40)
        print("❌ BEDROCK_AWS_ACCESS_KEY_ID or BEDROCK_AWS_SECRET_ACCESS_KEY not set")
        print("   Set credentials and re-run verification")
        return False
    
    bedrock_agent = boto3.client(
        'bedrock-agent',
        region_name='us-east-2',
        aws_access_key_id=bedrock_access_key,
        aws_secret_access_key=bedrock_secret_key
    )
    
    expected_agents = {
        'TaxPlannerAgent': 'DM6OT8QW8S',
        'TaxIntakeAgent': 'BXETK7XKYI',
        'W2IngestAgent': 'XLGLV9KLZ6',
        'Calc1040Agent': 'SX3FV20GED',
        'ReviewAgent': 'Q5CLGMRDN4',
        'ReturnRenderAgent': '0JQ5T0ZKYR',
        'DeadlinesAgent': 'HKGOFHHYJB',
        'ComplianceAgent': '3KPZH7DQMU'
    }
    
    print("\n🤖 Checking Bedrock Agents...")
    print("-" * 40)
    
    all_agents_ready = True
    
    for agent_name, agent_id in expected_agents.items():
        try:
            response = bedrock_agent.get_agent(agentId=agent_id)
            status = response['agent']['agentStatus']
            
            # Check if agent has action groups
            action_groups = bedrock_agent.list_agent_action_groups(
                agentId=agent_id,
                agentVersion="DRAFT"
            )
            
            action_group_count = len(action_groups.get('actionGroupSummaries', []))
            
            if status == 'PREPARED' and action_group_count > 0:
                print(f"✅ {agent_name}: {status} ({action_group_count} action groups)")
            else:
                print(f"⚠️  {agent_name}: {status} ({action_group_count} action groups)")
                all_agents_ready = False
                
        except ClientError as e:
            print(f"❌ {agent_name}: ERROR - {e}")
            all_agents_ready = False
    
    return all_agents_ready


def main():
    """Run complete deployment verification."""
    
    print("🔍 TAX SYSTEM DEPLOYMENT VERIFICATION")
    print("=" * 50)
    
    # Check all components
    tables_ok = check_dynamodb_tables()
    roles_ok = check_iam_roles()
    lambda_ok = check_lambda_function()
    agents_ok = check_bedrock_agents()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 DEPLOYMENT VERIFICATION SUMMARY")
    print("=" * 50)
    
    components = [
        ("DynamoDB Tables", tables_ok),
        ("IAM Roles", roles_ok),
        ("Lambda Function", lambda_ok),
        ("Bedrock Agents", agents_ok)
    ]
    
    all_ok = True
    for component, status in components:
        if status:
            print(f"✅ {component}: READY")
        else:
            print(f"❌ {component}: ISSUES FOUND")
            all_ok = False
    
    print("=" * 50)
    
    if all_ok:
        print("🎉 TAX SYSTEM FULLY DEPLOYED AND OPERATIONAL!")
        print("🚀 Ready for production use")
    else:
        print("⚠️  DEPLOYMENT INCOMPLETE")
        print("💡 Run deployment scripts to fix issues")
        print("📖 See TAX_SYSTEM_DEPLOYMENT.md for instructions")
    
    return all_ok


if __name__ == "__main__":
    main()
