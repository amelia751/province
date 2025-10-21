#!/usr/bin/env python3
"""Update Bedrock agents in us-east-1 to use the correct Lambda function."""

import os
import json
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.local'))

def get_bedrock_clients():
    """Get Bedrock clients with proper credentials for us-east-1."""
    
    # Use Bedrock-specific credentials
    bedrock_access_key = os.getenv('BEDROCK_AWS_ACCESS_KEY_ID')
    bedrock_secret_key = os.getenv('BEDROCK_AWS_SECRET_ACCESS_KEY')
    
    if bedrock_access_key and bedrock_secret_key:
        print("✅ Using Bedrock credentials for us-east-1 agent updates")
        bedrock_agent = boto3.client(
            'bedrock-agent',
            region_name='us-east-1',  # Correct region
            aws_access_key_id=bedrock_access_key,
            aws_secret_access_key=bedrock_secret_key
        )
    else:
        print("⚠️ Using default credentials for us-east-1 agent updates")
        bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
    
    return bedrock_agent

def list_agents_us_east_1(bedrock_agent):
    """List all Bedrock agents in us-east-1."""
    
    try:
        response = bedrock_agent.list_agents()
        agents = response.get('agentSummaries', [])
        
        print(f"\n📋 Found {len(agents)} agents in us-east-1:")
        for agent in agents:
            print(f"   • {agent['agentName']} (ID: {agent['agentId']})")
        
        return agents
    except Exception as e:
        print(f"❌ Error listing agents in us-east-1: {e}")
        return []

def list_action_groups_us_east_1(bedrock_agent, agent_id):
    """List action groups for a specific agent in us-east-1."""
    
    try:
        response = bedrock_agent.list_agent_action_groups(
            agentId=agent_id,
            agentVersion='DRAFT'
        )
        action_groups = response.get('actionGroupSummaries', [])
        
        print(f"\n📋 Found {len(action_groups)} action groups for agent {agent_id}:")
        for ag in action_groups:
            print(f"   • {ag['actionGroupName']} (ID: {ag['actionGroupId']})")
        
        return action_groups
    except Exception as e:
        print(f"❌ Error listing action groups for agent {agent_id}: {e}")
        return []

def get_action_group_details_us_east_1(bedrock_agent, agent_id, action_group_id):
    """Get detailed information about an action group in us-east-1."""
    
    try:
        response = bedrock_agent.get_agent_action_group(
            agentId=agent_id,
            agentVersion='DRAFT',
            actionGroupId=action_group_id
        )
        action_group = response.get('agentActionGroup', {})
        
        # Check current Lambda ARN
        executor = action_group.get('actionGroupExecutor', {})
        current_lambda = executor.get('lambda', 'Not set')
        print(f"   📦 Current Lambda: {current_lambda}")
        
        return action_group
    except Exception as e:
        print(f"❌ Error getting action group details: {e}")
        return {}

def update_action_group_lambda_us_east_1(bedrock_agent, agent_id, action_group_id, action_group_name):
    """Update an action group to use the correct us-east-1 Lambda function."""
    
    # Correct Lambda ARN for us-east-1
    correct_lambda_arn = "arn:aws:lambda:us-east-1:[REDACTED-ACCOUNT-ID]:function:province-tax-filing-tools"
    
    print(f"\n🔄 Updating action group: {action_group_name}")
    print(f"   🎯 Target Lambda: {correct_lambda_arn}")
    
    # First, get the current action group configuration
    current_config = get_action_group_details_us_east_1(bedrock_agent, agent_id, action_group_id)
    
    if not current_config:
        print(f"❌ Could not get current configuration for {action_group_name}")
        return False
    
    try:
        # Update the action group with correct us-east-1 Lambda ARN
        response = bedrock_agent.update_agent_action_group(
            agentId=agent_id,
            agentVersion='DRAFT',
            actionGroupId=action_group_id,
            actionGroupName=action_group_name,
            description=current_config.get('description', 'Updated to use us-east-1 ingest_documents Lambda'),
            actionGroupExecutor={
                'lambda': correct_lambda_arn
            },
            functionSchema=current_config.get('functionSchema', {}),
            actionGroupState='ENABLED'
        )
        
        print(f"✅ Successfully updated {action_group_name} to use us-east-1 Lambda")
        print(f"   📦 New Lambda ARN: {correct_lambda_arn}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating action group {action_group_name}: {e}")
        return False

def prepare_agent_us_east_1(bedrock_agent, agent_id, agent_name):
    """Prepare agent after updating action groups in us-east-1."""
    
    print(f"\n🔄 Preparing agent: {agent_name}")
    
    try:
        response = bedrock_agent.prepare_agent(
            agentId=agent_id
        )
        
        preparation_state = response.get('agentStatus', 'Unknown')
        print(f"✅ Agent preparation initiated: {preparation_state}")
        return True
        
    except Exception as e:
        print(f"❌ Error preparing agent {agent_name}: {e}")
        return False

def main():
    """Main function to update all agents in us-east-1."""
    
    print("🔥 UPDATE BEDROCK AGENTS IN US-EAST-1")
    print("This will update all Bedrock agents to use the correct us-east-1 Lambda")
    print("=" * 70)
    
    # Get Bedrock client for us-east-1
    bedrock_agent = get_bedrock_clients()
    
    # List all agents in us-east-1
    agents = list_agents_us_east_1(bedrock_agent)
    
    if not agents:
        print("❌ No agents found in us-east-1")
        return
    
    updated_agents = []
    correct_lambda_arn = "arn:aws:lambda:us-east-1:[REDACTED-ACCOUNT-ID]:function:province-tax-filing-tools"
    
    for agent in agents:
        agent_id = agent['agentId']
        agent_name = agent['agentName']
        
        print(f"\n{'=' * 50}")
        print(f"🤖 Processing Agent: {agent_name}")
        print(f"{'=' * 50}")
        
        # List action groups for this agent
        action_groups = list_action_groups_us_east_1(bedrock_agent, agent_id)
        
        if not action_groups:
            print(f"⚠️ No action groups found for {agent_name}")
            continue
        
        updated_action_groups = 0
        
        for ag in action_groups:
            action_group_id = ag['actionGroupId']
            action_group_name = ag['actionGroupName']
            
            # Check current configuration first
            print(f"\n🔍 Checking action group: {action_group_name}")
            current_config = get_action_group_details_us_east_1(bedrock_agent, agent_id, action_group_id)
            
            if current_config:
                executor = current_config.get('actionGroupExecutor', {})
                current_lambda = executor.get('lambda', 'Not set')
                
                if current_lambda == correct_lambda_arn:
                    print(f"✅ {action_group_name} already using correct Lambda")
                    updated_action_groups += 1
                else:
                    print(f"🔄 {action_group_name} needs update:")
                    print(f"   📦 Current: {current_lambda}")
                    print(f"   🎯 Target:  {correct_lambda_arn}")
                    
                    # Update this action group to use the correct Lambda
                    success = update_action_group_lambda_us_east_1(
                        bedrock_agent, 
                        agent_id, 
                        action_group_id, 
                        action_group_name
                    )
                    
                    if success:
                        updated_action_groups += 1
        
        if updated_action_groups > 0:
            # Prepare the agent after updating action groups
            prepare_success = prepare_agent_us_east_1(bedrock_agent, agent_id, agent_name)
            if prepare_success:
                updated_agents.append(agent_name)
        
        print(f"\n📊 Agent {agent_name} Summary:")
        print(f"   ✅ Action groups using correct Lambda: {updated_action_groups}")
        print(f"   📋 Total action groups: {len(action_groups)}")
    
    # Final summary
    print(f"\n{'=' * 70}")
    print(f"📊 FINAL SUMMARY:")
    print(f"   🤖 Total agents processed: {len(agents)}")
    print(f"   ✅ Agents successfully updated: {len(updated_agents)}")
    
    if updated_agents:
        print(f"\n🎉 Successfully updated agents in us-east-1:")
        for agent_name in updated_agents:
            print(f"   • {agent_name}")
        
        print(f"\n🔧 Correct Lambda Function (us-east-1):")
        print(f"   📦 ARN: {correct_lambda_arn}")
        print(f"   🌍 Region: us-east-1 (matches Bedrock agents)")
        print(f"   🎯 Features: Clean ingest_documents, fill_tax_form, enhanced error handling")
        
        print(f"\n🎯 Next Steps:")
        print(f"   1. Test your agents in the Bedrock dashboard")
        print(f"   2. Look for wage values: $95,000 (confirms us-east-1 Lambda)")
        print(f"   3. Look for 'US-EAST-1' in response messages")
        print(f"   4. Both 'ingest_documents' and 'ingest_w2_pdf' should work")
        print(f"   5. All responses should include 'region': 'us-east-1'")
        
        print(f"\n✨ YOUR BEDROCK AGENTS NOW USE THE CORRECT US-EAST-1 LAMBDA!")
    else:
        print(f"\n⚠️ No agents needed updates (they may already be correct)")
        print(f"All agents are already using the correct us-east-1 Lambda function")

if __name__ == "__main__":
    main()

