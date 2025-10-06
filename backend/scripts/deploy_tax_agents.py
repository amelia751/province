#!/usr/bin/env python3
"""Script to deploy all tax agents to AWS Bedrock."""

import asyncio
import os
import sys
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from province.agents.tax import (
    TaxPlanner,
    TaxIntakeAgent,
    W2IngestAgent,
    Calc1040Agent,
    ReviewAgent,
    ReturnRenderAgent,
    DeadlinesAgent,
    ComplianceAgent
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def deploy_all_agents():
    """Deploy all tax agents to AWS Bedrock."""
    
    agents = [
        ("TaxPlannerAgent", TaxPlanner()),
        ("TaxIntakeAgent", TaxIntakeAgent()),
        ("W2IngestAgent", W2IngestAgent()),
        ("Calc1040Agent", Calc1040Agent()),
        ("ReviewAgent", ReviewAgent()),
        ("ReturnRenderAgent", ReturnRenderAgent()),
        ("DeadlinesAgent", DeadlinesAgent()),
        ("ComplianceAgent", ComplianceAgent())
    ]
    
    deployed_agents = {}
    
    for agent_name, agent_instance in agents:
        try:
            logger.info(f"Deploying {agent_name}...")
            agent_id = await agent_instance.create_agent()
            deployed_agents[agent_name] = {
                'agent_id': agent_id,
                'agent_alias_id': agent_instance.agent_alias_id
            }
            logger.info(f"✅ {agent_name} deployed successfully: {agent_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to deploy {agent_name}: {e}")
            deployed_agents[agent_name] = {'error': str(e)}
    
    # Print summary
    print("\n" + "="*60)
    print("DEPLOYMENT SUMMARY")
    print("="*60)
    
    for agent_name, result in deployed_agents.items():
        if 'error' in result:
            print(f"❌ {agent_name}: {result['error']}")
        else:
            print(f"✅ {agent_name}: {result['agent_id']}")
    
    print("="*60)
    
    return deployed_agents


if __name__ == "__main__":
    print("Deploying tax agents to AWS Bedrock...")
    print("This may take several minutes...")
    
    # Set up environment variables for tax tables
    os.environ['TAX_ENGAGEMENTS_TABLE_NAME'] = 'province-tax-engagements'
    os.environ['TAX_DOCUMENTS_TABLE_NAME'] = 'province-tax-documents'
    os.environ['TAX_PERMISSIONS_TABLE_NAME'] = 'province-tax-permissions'
    os.environ['TAX_DEADLINES_TABLE_NAME'] = 'province-tax-deadlines'
    os.environ['TAX_CONNECTIONS_TABLE_NAME'] = 'province-tax-connections'
    
    # Run the deployment
    result = asyncio.run(deploy_all_agents())
    
    print("\nDeployment complete!")
