#!/usr/bin/env python3
"""Clean up old action groups and keep only comprehensive ones."""

import boto3
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


def cleanup_agent_action_groups(bedrock_agent, agent_id: str, agent_name: str):
    """Remove old action groups and keep only comprehensive ones."""
    
    try:
        # List all action groups
        existing_groups = bedrock_agent.list_agent_action_groups(
            agentId=agent_id,
            agentVersion="DRAFT"
        )
        
        groups_to_delete = []
        comprehensive_group = None
        
        for group in existing_groups.get('actionGroupSummaries', []):
            group_name = group['actionGroupName']
            group_id = group['actionGroupId']
            
            if group_name == 'TaxTools':
                # This is the old simple action group
                groups_to_delete.append((group_id, group_name))
            elif group_name == 'ComprehensiveTaxTools':
                # This is the new comprehensive action group
                comprehensive_group = group_id
        
        # Delete old action groups
        for group_id, group_name in groups_to_delete:
            try:
                # Directly delete the action group (no need to disable first)
                bedrock_agent.delete_agent_action_group(
                    agentId=agent_id,
                    agentVersion="DRAFT",
                    actionGroupId=group_id
                )
                logger.info(f"🗑️  Deleted old action group {group_name} for {agent_name}")
                
            except ClientError as e:
                if "cannot be deleted when it is Enabled" in str(e):
                    logger.info(f"⚠️  {group_name} for {agent_name} is enabled, skipping deletion")
                else:
                    logger.error(f"❌ Failed to delete {group_name} for {agent_name}: {e}")
        
        # Prepare agent after cleanup
        bedrock_agent.prepare_agent(agentId=agent_id)
        logger.info(f"✅ Prepared {agent_name} after cleanup")
        
        return comprehensive_group is not None
        
    except ClientError as e:
        logger.error(f"❌ Failed to cleanup action groups for {agent_name}: {e}")
        return False


def main():
    """Clean up old action groups for all agents."""
    
    print("🧹 CLEANING UP OLD ACTION GROUPS")
    print("=" * 50)
    print("Removing old 'TaxTools' action groups")
    print("Keeping 'ComprehensiveTaxTools' action groups")
    print("=" * 50)
    
    bedrock_agent = get_bedrock_client()
    
    agents = {
        'TaxPlannerAgent': 'DM6OT8QW8S',
        'TaxIntakeAgent': 'BXETK7XKYI',
        'W2IngestAgent': 'XLGLV9KLZ6',
        'Calc1040Agent': 'SX3FV20GED',
        'ReviewAgent': 'Q5CLGMRDN4',
        'ReturnRenderAgent': '0JQ5T0ZKYR',
        'DeadlinesAgent': 'HKGOFHHYJB',
        'ComplianceAgent': '3KPZH7DQMU'
    }
    
    results = {}
    
    # Clean up each agent
    for agent_name, agent_id in agents.items():
        print(f"\n🧹 Cleaning up {agent_name}...")
        
        success = cleanup_agent_action_groups(bedrock_agent, agent_id, agent_name)
        results[agent_name] = success
    
    # Print summary
    print("\n" + "=" * 50)
    print("🧹 CLEANUP SUMMARY")
    print("=" * 50)
    
    success_count = 0
    for agent_name, success in results.items():
        if success:
            print(f"✅ {agent_name}: Cleaned up successfully")
            success_count += 1
        else:
            print(f"❌ {agent_name}: Cleanup failed")
    
    print("=" * 50)
    
    if success_count == len(results):
        print("🎉 ALL AGENTS CLEANED UP!")
        print("🔥 Only comprehensive action groups remain")
        print("💡 Run verification script to confirm status")
    else:
        print(f"⚠️  {success_count}/{len(results)} agents cleaned up")
        print("💡 Some agents may need manual cleanup")
    
    return results


if __name__ == "__main__":
    main()
