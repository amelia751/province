#!/usr/bin/env python3
"""Quick agent status check and prepare agents that need it."""

import boto3
import os
from botocore.exceptions import ClientError

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

def main():
    """Check agent status and prepare if needed."""
    
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
    
    print("🔍 Checking agent status...")
    print("=" * 60)
    
    for agent_name, agent_id in agents.items():
        try:
            response = bedrock_agent.get_agent(agentId=agent_id)
            status = response['agent']['agentStatus']
            
            print(f"{agent_name}: {status}")
            
            # Try to prepare if not prepared
            if status == 'NOT_PREPARED':
                try:
                    bedrock_agent.prepare_agent(agentId=agent_id)
                    print(f"  ✅ Initiated preparation for {agent_name}")
                except ClientError as e:
                    print(f"  ❌ Could not prepare {agent_name}: {e}")
            
            # Try to create alias if prepared
            elif status == 'PREPARED':
                try:
                    # Check if alias exists
                    aliases = bedrock_agent.list_agent_aliases(agentId=agent_id)
                    has_draft = any(alias['agentAliasName'] == 'DRAFT' for alias in aliases.get('agentAliasSummaries', []))
                    
                    if not has_draft:
                        alias_response = bedrock_agent.create_agent_alias(
                            agentId=agent_id,
                            agentAliasName="DRAFT",
                            description=f"Draft alias for {agent_name}"
                        )
                        print(f"  ✅ Created DRAFT alias: {alias_response['agentAlias']['agentAliasId']}")
                    else:
                        print(f"  ✅ DRAFT alias already exists")
                        
                except ClientError as e:
                    print(f"  ❌ Could not create alias for {agent_name}: {e}")
                    
        except ClientError as e:
            print(f"{agent_name}: ERROR - {e}")
    
    print("=" * 60)
    print("✅ Status check complete!")

if __name__ == "__main__":
    main()
