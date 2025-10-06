#!/usr/bin/env python3
"""Finalize agent deployment - wait for agents to be ready and create aliases."""

import asyncio
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
    
    if not bedrock_access_key or not bedrock_secret_key:
        raise ValueError("Bedrock credentials not found in environment")
    
    return boto3.client(
        'bedrock-agent',
        region_name='us-east-2',
        aws_access_key_id=bedrock_access_key,
        aws_secret_access_key=bedrock_secret_key
    )


async def wait_for_agent_ready(bedrock_agent, agent_id: str, agent_name: str, max_wait: int = 300):
    """Wait for an agent to be in PREPARED state."""
    
    logger.info(f"Waiting for {agent_name} ({agent_id}) to be ready...")
    
    for i in range(max_wait):
        try:
            response = bedrock_agent.get_agent(agentId=agent_id)
            status = response['agent']['agentStatus']
            
            if status == 'PREPARED':
                logger.info(f"✅ {agent_name} is ready!")
                return True
            elif status in ['FAILED', 'DELETING']:
                logger.error(f"❌ {agent_name} failed with status: {status}")
                return False
            else:
                logger.info(f"⏳ {agent_name} status: {status} (waiting...)")
                await asyncio.sleep(2)
                
        except ClientError as e:
            logger.error(f"Error checking {agent_name} status: {e}")
            await asyncio.sleep(2)
    
    logger.error(f"❌ {agent_name} did not become ready within {max_wait} seconds")
    return False


async def create_agent_alias(bedrock_agent, agent_id: str, agent_name: str):
    """Create an alias for an agent."""
    
    try:
        # Check if DRAFT alias already exists
        aliases_response = bedrock_agent.list_agent_aliases(agentId=agent_id)
        
        for alias in aliases_response.get('agentAliasSummaries', []):
            if alias['agentAliasName'] == 'DRAFT':
                logger.info(f"✅ {agent_name} already has DRAFT alias: {alias['agentAliasId']}")
                return alias['agentAliasId']
        
        # Create new alias
        alias_response = bedrock_agent.create_agent_alias(
            agentId=agent_id,
            agentAliasName="DRAFT",
            description=f"Draft alias for {agent_name}"
        )
        
        alias_id = alias_response['agentAlias']['agentAliasId']
        logger.info(f"✅ Created DRAFT alias for {agent_name}: {alias_id}")
        return alias_id
        
    except ClientError as e:
        logger.error(f"❌ Failed to create alias for {agent_name}: {e}")
        return None


async def finalize_all_agents():
    """Finalize all agents - wait for them to be ready and create aliases."""
    
    bedrock_agent = get_bedrock_client()
    
    # Known agent IDs from deployment
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
    
    # First, wait for all agents to be ready
    logger.info("🔄 Waiting for all agents to be prepared...")
    
    for agent_name, agent_id in agents.items():
        is_ready = await wait_for_agent_ready(bedrock_agent, agent_id, agent_name)
        results[agent_name] = {'agent_id': agent_id, 'ready': is_ready}
    
    # Then create aliases for ready agents
    logger.info("🔗 Creating aliases for ready agents...")
    
    for agent_name, result in results.items():
        if result['ready']:
            alias_id = await create_agent_alias(bedrock_agent, result['agent_id'], agent_name)
            result['alias_id'] = alias_id
        else:
            result['alias_id'] = None
    
    return results


async def main():
    """Main function."""
    
    print("🚀 Finalizing tax agent deployment...")
    print("=" * 60)
    
    try:
        results = await finalize_all_agents()
        
        # Print final summary
        print("\n" + "=" * 60)
        print("🎉 FINAL DEPLOYMENT STATUS")
        print("=" * 60)
        
        ready_count = 0
        for agent_name, result in results.items():
            if result['ready'] and result['alias_id']:
                print(f"✅ {agent_name}: {result['agent_id']} (alias: {result['alias_id']})")
                ready_count += 1
            elif result['ready']:
                print(f"⚠️  {agent_name}: {result['agent_id']} (ready, but no alias)")
            else:
                print(f"❌ {agent_name}: {result['agent_id']} (not ready)")
        
        print("=" * 60)
        print(f"🎯 {ready_count}/{len(results)} agents fully ready with aliases")
        
        if ready_count == len(results):
            print("🎉 ALL AGENTS DEPLOYED AND READY!")
            print("🔥 Tax system is fully operational!")
            
            # Save agent IDs for easy reference
            agent_ids = {name: result['agent_id'] for name, result in results.items()}
            alias_ids = {name: result['alias_id'] for name, result in results.items() if result['alias_id']}
            
            print("\n📋 Agent IDs for integration:")
            for name, agent_id in agent_ids.items():
                alias_id = alias_ids.get(name, 'N/A')
                print(f"  {name}: {agent_id} (alias: {alias_id})")
                
        else:
            print("⚠️  Some agents are not fully ready yet.")
            print("💡 You can run this script again to retry.")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Finalization failed: {e}")
        raise


if __name__ == "__main__":
    print("Finalizing tax agent deployment...")
    
    # Run the finalization
    result = asyncio.run(main())
    
    print("\n🚀 Finalization complete!")
    print("📝 Check the summary above for final status.")
