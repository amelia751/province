#!/usr/bin/env python3
"""Clean up duplicate agents that don't have proper action groups."""

import boto3
import os
import logging
import time
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


def get_agent_action_groups(bedrock_agent, agent_id: str):
    """Get action groups for an agent."""
    
    try:
        response = bedrock_agent.list_agent_action_groups(
            agentId=agent_id,
            agentVersion="DRAFT"
        )
        return response.get('actionGroupSummaries', [])
    except ClientError:
        return []


def delete_agent_aliases(bedrock_agent, agent_id: str):
    """Delete all aliases for an agent."""
    
    try:
        response = bedrock_agent.list_agent_aliases(agentId=agent_id)
        aliases = response.get('agentAliasSummaries', [])
        
        for alias in aliases:
            alias_id = alias['agentAliasId']
            alias_name = alias['agentAliasName']
            
            # Skip test aliases that can't be deleted
            if alias_id == 'TSTALIASID':
                continue
                
            try:
                bedrock_agent.delete_agent_alias(
                    agentId=agent_id,
                    agentAliasId=alias_id
                )
                logger.info(f"🗑️  Deleted alias {alias_name} ({alias_id})")
            except ClientError as e:
                logger.error(f"❌ Failed to delete alias {alias_name}: {e}")
        
        return True
    except ClientError as e:
        logger.error(f"❌ Failed to list aliases: {e}")
        return False


def delete_duplicate_agent(bedrock_agent, agent_id: str, agent_name: str):
    """Delete a duplicate agent after removing its aliases."""
    
    try:
        # First delete aliases
        delete_agent_aliases(bedrock_agent, agent_id)
        
        # Wait a moment for aliases to be deleted
        time.sleep(3)
        
        # Then delete the agent
        bedrock_agent.delete_agent(agentId=agent_id)
        logger.info(f"🗑️  Deleted duplicate agent {agent_name} ({agent_id})")
        return True
        
    except ClientError as e:
        logger.error(f"❌ Failed to delete agent {agent_name}: {e}")
        return False


def main():
    """Find and delete duplicate agents without proper action groups."""
    
    print("🧹 CLEANING UP DUPLICATE AGENTS")
    print("=" * 50)
    
    bedrock_agent = get_bedrock_client()
    
    # Our official tax agents with their expected action groups
    official_agents = {
        'TaxPlannerAgent': 'DM6OT8QW8S',
        'TaxIntakeAgent': 'BXETK7XKYI',
        'W2IngestAgent': 'XLGLV9KLZ6',
        'Calc1040Agent': 'SX3FV20GED',
        'ReviewAgent': 'Q5CLGMRDN4',
        'ReturnRenderAgent': '0JQ5T0ZKYR',
        'DeadlinesAgent': 'HKGOFHHYJB',
        'ComplianceAgent': '3KPZH7DQMU'
    }
    
    try:
        # List all agents
        response = bedrock_agent.list_agents()
        all_agents = response.get('agentSummaries', [])
        
        duplicates_found = []
        
        # Find duplicates
        for agent in all_agents:
            agent_name = agent['agentName']
            agent_id = agent['agentId']
            
            # Check if this is a tax-related agent
            if 'Tax' in agent_name:
                # Check if it's NOT in our official list
                if agent_id not in official_agents.values():
                    # Check if it has no action groups (indicating it's a duplicate)
                    action_groups = get_agent_action_groups(bedrock_agent, agent_id)
                    
                    if len(action_groups) == 0:
                        duplicates_found.append((agent_name, agent_id))
                        print(f"🔍 Found duplicate: {agent_name} ({agent_id}) - No action groups")
        
        if not duplicates_found:
            print("✅ No duplicate agents found!")
            return
        
        # Delete duplicates
        print(f"\n🗑️  Deleting {len(duplicates_found)} duplicate agents...")
        
        deleted_count = 0
        for agent_name, agent_id in duplicates_found:
            if delete_duplicate_agent(bedrock_agent, agent_id, agent_name):
                deleted_count += 1
        
        print(f"\n✅ Deleted {deleted_count}/{len(duplicates_found)} duplicate agents")
        
        # Show remaining official agents
        print(f"\n📋 Official Tax Agents Remaining:")
        print("-" * 40)
        
        for name, agent_id in official_agents.items():
            try:
                response = bedrock_agent.get_agent(agentId=agent_id)
                status = response['agent']['agentStatus']
                action_groups = get_agent_action_groups(bedrock_agent, agent_id)
                print(f"✅ {name}: {status} ({len(action_groups)} action groups)")
            except ClientError:
                print(f"❌ {name}: NOT FOUND")
        
    except ClientError as e:
        logger.error(f"❌ Failed to list agents: {e}")


if __name__ == "__main__":
    main()
