#!/usr/bin/env python3
"""
Update all tax agents to use the inference profile instead of direct model ID
"""

import boto3
import os
import logging
from botocore.exceptions import ClientError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_agent_model(bedrock_agent, agent_id, agent_name):
    """Update an agent to use the inference profile"""
    try:
        # Get current agent configuration
        response = bedrock_agent.get_agent(
            agentId=agent_id
        )
        
        current_config = response['agent']
        
        # Update the foundation model to use inference profile
        inference_profile_arn = "arn:aws:bedrock:us-east-2:[REDACTED-ACCOUNT-ID]:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        
        logger.info(f"Updating {agent_name} ({agent_id}) to use inference profile...")
        
        # Update the agent
        bedrock_agent.update_agent(
            agentId=agent_id,
            agentName=current_config['agentName'],
            description=current_config.get('description', ''),
            instruction=current_config.get('instruction', ''),
            foundationModel=inference_profile_arn,  # Use inference profile
            agentResourceRoleArn=current_config['agentResourceRoleArn']
        )
        
        logger.info(f"✅ Updated {agent_name} to use inference profile")
        
        # Prepare the agent
        logger.info(f"Preparing {agent_name}...")
        bedrock_agent.prepare_agent(agentId=agent_id)
        logger.info(f"✅ {agent_name} preparation initiated")
        
        return True
        
    except ClientError as e:
        logger.error(f"❌ Failed to update {agent_name}: {e}")
        return False

def main():
    """Update all tax agents to use inference profile"""
    
    # Use environment variables for AWS credentials
    session = boto3.Session(
        aws_access_key_id=os.getenv('BEDROCK_AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('BEDROCK_AWS_SECRET_ACCESS_KEY'),
        region_name='us-east-2'
    )
    
    bedrock_agent = session.client('bedrock-agent')
    
    # Tax agents to update
    tax_agents = [
        {"id": "DM6OT8QW8S", "name": "TaxPlannerAgent"},
        {"id": "BXETK7XKYI", "name": "TaxIntakeAgent"},
        {"id": "XLGLV9KLZ6", "name": "W2IngestAgent"},
        {"id": "SX3FV20GED", "name": "Calc1040Agent"},
        {"id": "Q5CLGMRDN4", "name": "ReviewAgent"},
        {"id": "0JQ5T0ZKYR", "name": "ReturnRenderAgent"},
        {"id": "HKGOFHHYJB", "name": "DeadlinesAgent"},
        {"id": "3KPZH7DQMU", "name": "ComplianceAgent"}
    ]
    
    logger.info("🚀 Starting agent model updates...")
    
    successful_updates = 0
    for agent in tax_agents:
        if update_agent_model(bedrock_agent, agent["id"], agent["name"]):
            successful_updates += 1
    
    logger.info(f"✅ Successfully updated {successful_updates}/{len(tax_agents)} agents")
    
    if successful_updates == len(tax_agents):
        logger.info("🎉 All agents updated successfully!")
        logger.info("⏳ Agents are now preparing. This may take a few minutes.")
        logger.info("💡 You can check status with: python scripts/quick_agent_status.py")
    else:
        logger.warning("⚠️  Some agents failed to update. Check the logs above.")

if __name__ == "__main__":
    main()
