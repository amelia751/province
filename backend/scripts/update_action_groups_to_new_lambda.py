#!/usr/bin/env python3
"""Update Bedrock action groups to use the new Lambda function with ingest_documents."""

import os
import json
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.local'))

def get_bedrock_clients():
    """Get Bedrock clients with proper credentials."""
    
    # Use Bedrock-specific credentials
    bedrock_access_key = os.getenv('BEDROCK_AWS_ACCESS_KEY_ID')
    bedrock_secret_key = os.getenv('BEDROCK_AWS_SECRET_ACCESS_KEY')
    
    if bedrock_access_key and bedrock_secret_key:
        print("✅ Using Bedrock credentials for action group updates")
        bedrock_agent = boto3.client(
            'bedrock-agent',
            region_name='us-east-1',
            aws_access_key_id=bedrock_access_key,
            aws_secret_access_key=bedrock_secret_key
        )
    else:
        print("⚠️ Using default credentials for action group updates")
        bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
    
    return bedrock_agent

def list_agents(bedrock_agent):
    """List all Bedrock agents."""
    
    try:
        response = bedrock_agent.list_agents()
        agents = response.get('agentSummaries', [])
        
        print(f"\n📋 Found {len(agents)} agents:")
        for agent in agents:
            print(f"   • {agent['agentName']} (ID: {agent['agentId']})")
        
        return agents
    except Exception as e:
        print(f"❌ Error listing agents: {e}")
        return []

def list_action_groups(bedrock_agent, agent_id):
    """List action groups for a specific agent."""
    
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

def get_action_group_details(bedrock_agent, agent_id, action_group_id):
    """Get detailed information about an action group."""
    
    try:
        response = bedrock_agent.get_agent_action_group(
            agentId=agent_id,
            agentVersion='DRAFT',
            actionGroupId=action_group_id
        )
        return response.get('agentActionGroup', {})
    except Exception as e:
        print(f"❌ Error getting action group details: {e}")
        return {}

def update_action_group_lambda(bedrock_agent, agent_id, action_group_id, action_group_name):
    """Update an action group to use the new Lambda function."""
    
    new_lambda_arn = "arn:aws:lambda:us-east-2:[REDACTED-ACCOUNT-ID]:function:province-tax-tools-ingest-documents"
    
    print(f"\n🔄 Updating action group: {action_group_name}")
    
    # First, get the current action group configuration
    current_config = get_action_group_details(bedrock_agent, agent_id, action_group_id)
    
    if not current_config:
        print(f"❌ Could not get current configuration for {action_group_name}")
        return False
    
    try:
        # Update the action group with new Lambda ARN
        response = bedrock_agent.update_agent_action_group(
            agentId=agent_id,
            agentVersion='DRAFT',
            actionGroupId=action_group_id,
            actionGroupName=action_group_name,
            description=current_config.get('description', 'Updated to use ingest_documents Lambda'),
            actionGroupExecutor={
                'lambda': new_lambda_arn
            },
            functionSchema=current_config.get('functionSchema', {}),
            actionGroupState='ENABLED'
        )
        
        print(f"✅ Successfully updated {action_group_name} to use new Lambda")
        print(f"   📦 New Lambda ARN: {new_lambda_arn}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating action group {action_group_name}: {e}")
        return False

def prepare_agent(bedrock_agent, agent_id, agent_name):
    """Prepare agent after updating action groups."""
    
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
    """Main function to update all action groups."""
    
    print("🔥 UPDATE ACTION GROUPS TO NEW LAMBDA")
    print("This will update Bedrock action groups to use the new ingest_documents Lambda")
    print("=" * 70)
    
    # Get Bedrock client
    bedrock_agent = get_bedrock_clients()
    
    # List all agents
    agents = list_agents(bedrock_agent)
    
    if not agents:
        print("❌ No agents found")
        return
    
    updated_agents = []
    
    for agent in agents:
        agent_id = agent['agentId']
        agent_name = agent['agentName']
        
        print(f"\n{'=' * 50}")
        print(f"🤖 Processing Agent: {agent_name}")
        print(f"{'=' * 50}")
        
        # List action groups for this agent
        action_groups = list_action_groups(bedrock_agent, agent_id)
        
        if not action_groups:
            print(f"⚠️ No action groups found for {agent_name}")
            continue
        
        updated_action_groups = 0
        
        for ag in action_groups:
            action_group_id = ag['actionGroupId']
            action_group_name = ag['actionGroupName']
            
            # Update this action group to use the new Lambda
            success = update_action_group_lambda(
                bedrock_agent, 
                agent_id, 
                action_group_id, 
                action_group_name
            )
            
            if success:
                updated_action_groups += 1
        
        if updated_action_groups > 0:
            # Prepare the agent after updating action groups
            prepare_success = prepare_agent(bedrock_agent, agent_id, agent_name)
            if prepare_success:
                updated_agents.append(agent_name)
        
        print(f"\n📊 Agent {agent_name} Summary:")
        print(f"   ✅ Updated action groups: {updated_action_groups}")
        print(f"   📋 Total action groups: {len(action_groups)}")
    
    # Final summary
    print(f"\n{'=' * 70}")
    print(f"📊 FINAL SUMMARY:")
    print(f"   🤖 Total agents processed: {len(agents)}")
    print(f"   ✅ Agents successfully updated: {len(updated_agents)}")
    
    if updated_agents:
        print(f"\n🎉 Successfully updated agents:")
        for agent_name in updated_agents:
            print(f"   • {agent_name}")
        
        print(f"\n🔧 New Lambda Function:")
        print(f"   📦 ARN: arn:aws:lambda:us-east-2:[REDACTED-ACCOUNT-ID]:function:province-tax-tools-ingest-documents")
        print(f"   🎯 Features: ingest_documents, fill_tax_form, enhanced error handling")
        
        print(f"\n🎯 Next Steps:")
        print(f"   1. Test your agents in the Bedrock dashboard")
        print(f"   2. Look for different wage values (85k vs 75k) to confirm new Lambda is working")
        print(f"   3. Try calling 'ingest_documents' function - it should work now!")
        print(f"   4. Old 'ingest_w2_pdf' calls will be automatically redirected to 'ingest_documents'")
    else:
        print(f"\n❌ No agents were successfully updated")
        print(f"Check the error messages above for details")

if __name__ == "__main__":
    main()
