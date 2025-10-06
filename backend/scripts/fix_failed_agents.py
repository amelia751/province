#!/usr/bin/env python3
"""Fix agents in FAILED status by preparing them."""

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


def fix_agent(bedrock_agent, agent_id: str, agent_name: str):
    """Fix an agent in FAILED status."""
    
    try:
        # Get current agent status
        response = bedrock_agent.get_agent(agentId=agent_id)
        current_status = response['agent']['agentStatus']
        
        logger.info(f"🔍 {agent_name} current status: {current_status}")
        
        if current_status == 'FAILED':
            # Try to prepare the agent
            bedrock_agent.prepare_agent(agentId=agent_id)
            logger.info(f"🔄 Initiated preparation for {agent_name}")
            
            # Wait a moment and check status
            time.sleep(2)
            
            response = bedrock_agent.get_agent(agentId=agent_id)
            new_status = response['agent']['agentStatus']
            logger.info(f"✅ {agent_name} new status: {new_status}")
            
            return new_status != 'FAILED'
        else:
            logger.info(f"✅ {agent_name} is already in good status: {current_status}")
            return True
            
    except ClientError as e:
        logger.error(f"❌ Failed to fix {agent_name}: {e}")
        return False


def main():
    """Fix all agents in FAILED status."""
    
    print("🔧 FIXING FAILED AGENTS")
    print("=" * 40)
    
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
    
    # Fix each agent
    for agent_name, agent_id in agents.items():
        print(f"\n🔧 Fixing {agent_name}...")
        
        success = fix_agent(bedrock_agent, agent_id, agent_name)
        results[agent_name] = success
    
    # Print summary
    print("\n" + "=" * 40)
    print("🔧 FIX SUMMARY")
    print("=" * 40)
    
    success_count = 0
    for agent_name, success in results.items():
        if success:
            print(f"✅ {agent_name}: Fixed or already working")
            success_count += 1
        else:
            print(f"❌ {agent_name}: Still has issues")
    
    print("=" * 40)
    
    if success_count == len(results):
        print("🎉 ALL AGENTS FIXED!")
        print("💡 Run verification script to confirm")
    else:
        print(f"⚠️  {success_count}/{len(results)} agents fixed")
        print("💡 Some agents may need manual intervention")
    
    return results


if __name__ == "__main__":
    main()
