#!/usr/bin/env python3
"""Update Bedrock action groups to use the new ingest_documents function."""

import boto3
import json
import os
import sys
import logging
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.local'))

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_bedrock_client():
    """Get Bedrock client with appropriate credentials."""
    
    # Use Bedrock credentials
    bedrock_access_key = os.getenv('BEDROCK_AWS_ACCESS_KEY_ID')
    bedrock_secret_key = os.getenv('BEDROCK_AWS_SECRET_ACCESS_KEY')
    
    if bedrock_access_key and bedrock_secret_key:
        return boto3.client(
            'bedrock-agent',
            region_name='us-east-2',
            aws_access_key_id=bedrock_access_key,
            aws_secret_access_key=bedrock_secret_key
        )
    else:
        return boto3.client('bedrock-agent', region_name='us-east-2')


def list_agents():
    """List all Bedrock agents."""
    
    bedrock_client = get_bedrock_client()
    
    try:
        response = bedrock_client.list_agents()
        agents = response.get('agentSummaries', [])
        
        logger.info(f"Found {len(agents)} agents:")
        for agent in agents:
            logger.info(f"  - {agent['agentName']} (ID: {agent['agentId']}, Status: {agent['agentStatus']})")
        
        return agents
    except ClientError as e:
        logger.error(f"Error listing agents: {e}")
        return []


def list_action_groups(agent_id):
    """List action groups for a specific agent."""
    
    bedrock_client = get_bedrock_client()
    
    try:
        response = bedrock_client.list_agent_action_groups(
            agentId=agent_id,
            agentVersion='DRAFT'  # Use DRAFT version
        )
        action_groups = response.get('actionGroupSummaries', [])
        
        logger.info(f"Agent {agent_id} has {len(action_groups)} action groups:")
        for ag in action_groups:
            logger.info(f"  - {ag['actionGroupName']} (ID: {ag['actionGroupId']}, State: {ag['actionGroupState']})")
        
        return action_groups
    except ClientError as e:
        logger.error(f"Error listing action groups for agent {agent_id}: {e}")
        return []


def get_action_group_details(agent_id, action_group_id):
    """Get detailed information about an action group."""
    
    bedrock_client = get_bedrock_client()
    
    try:
        response = bedrock_client.get_agent_action_group(
            agentId=agent_id,
            agentVersion='DRAFT',
            actionGroupId=action_group_id
        )
        return response.get('agentActionGroup', {})
    except ClientError as e:
        logger.error(f"Error getting action group details: {e}")
        return {}


def update_action_group_schema(agent_id, action_group_id, current_schema):
    """Update action group schema to include ingest_documents function."""
    
    bedrock_client = get_bedrock_client()
    
    # Parse current schema
    if isinstance(current_schema, str):
        try:
            schema_dict = json.loads(current_schema)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON schema for action group {action_group_id}")
            return False
    else:
        schema_dict = current_schema
    
    # Check if we need to update the schema
    functions = schema_dict.get('functions', [])
    has_ingest_w2 = any(f.get('name') == 'ingest_w2_pdf' for f in functions)
    has_ingest_documents = any(f.get('name') == 'ingest_documents' for f in functions)
    
    if not has_ingest_w2 and not has_ingest_documents:
        logger.info(f"Action group {action_group_id} doesn't have W2 ingestion functions, skipping...")
        return True
    
    if has_ingest_documents and not has_ingest_w2:
        logger.info(f"Action group {action_group_id} already has ingest_documents, no update needed")
        return True
    
    # Add ingest_documents function if it doesn't exist
    if not has_ingest_documents:
        ingest_documents_function = {
            "name": "ingest_documents",
            "description": "Process tax documents (W-2, 1099-INT, 1099-MISC, etc.) from S3 bucket to extract tax information using AWS Bedrock Data Automation. Supports multiple document types with auto-detection.",
            "parameters": {
                "s3_key": {
                    "description": "S3 key of the tax document (PDF or JPEG)",
                    "required": True,
                    "type": "string"
                },
                "taxpayer_name": {
                    "description": "Name of the taxpayer for validation",
                    "required": True,
                    "type": "string"
                },
                "tax_year": {
                    "description": "Tax year for the document (e.g., 2024)",
                    "required": True,
                    "type": "integer"
                },
                "document_type": {
                    "description": "Type of document ('W-2', '1099-INT', '1099-MISC', or null for auto-detection)",
                    "required": False,
                    "type": "string"
                }
            }
        }
        
        functions.append(ingest_documents_function)
        logger.info(f"Added ingest_documents function to action group {action_group_id}")
    
    # Update the schema
    schema_dict['functions'] = functions
    
    try:
        # Get current action group details to preserve executor info
        current_details = get_action_group_details(agent_id, action_group_id)
        
        # Preserve the current executor configuration
        executor_config = current_details.get('actionGroupExecutor', {})
        
        # Update the action group
        update_params = {
            'agentId': agent_id,
            'agentVersion': 'DRAFT',
            'actionGroupId': action_group_id,
            'actionGroupName': current_details.get('actionGroupName', f"updated_tax_tools_{action_group_id[:8]}"),
            'description': "Updated tax tools with multi-document support",
            'functionSchema': {
                'functions': functions
            }
        }
        
        # Add executor if it exists
        if executor_config:
            update_params['actionGroupExecutor'] = executor_config
        
        response = bedrock_client.update_agent_action_group(**update_params)
        
        logger.info(f"✅ Updated action group {action_group_id} successfully")
        return True
        
    except ClientError as e:
        logger.error(f"❌ Error updating action group {action_group_id}: {e}")
        return False


def main():
    """Main function to update all action groups."""
    
    print("\n🔄 UPDATING BEDROCK ACTION GROUPS")
    print("=" * 50)
    print("🎯 Adding ingest_documents function to existing action groups")
    print("🔧 Maintaining backward compatibility with ingest_w2_pdf")
    print("")
    
    try:
        # List all agents
        agents = list_agents()
        
        if not agents:
            print("❌ No agents found or unable to access agents")
            return
        
        updated_count = 0
        total_action_groups = 0
        
        for agent in agents:
            agent_id = agent['agentId']
            agent_name = agent['agentName']
            
            print(f"\n📋 Processing agent: {agent_name} ({agent_id})")
            print("-" * 40)
            
            # List action groups for this agent
            action_groups = list_action_groups(agent_id)
            total_action_groups += len(action_groups)
            
            for ag in action_groups:
                action_group_id = ag['actionGroupId']
                action_group_name = ag['actionGroupName']
                
                print(f"  🔍 Checking action group: {action_group_name}")
                
                # Get action group details
                details = get_action_group_details(agent_id, action_group_id)
                
                if details and 'functionSchema' in details:
                    schema = details['functionSchema']
                    
                    # Update the schema
                    if update_action_group_schema(agent_id, action_group_id, schema):
                        updated_count += 1
                        print(f"    ✅ Updated successfully")
                    else:
                        print(f"    ❌ Update failed")
                else:
                    print(f"    ⚠️ No function schema found, skipping...")
        
        print(f"\n{'=' * 50}")
        print("📊 UPDATE SUMMARY:")
        print(f"   • Total agents processed: {len(agents)}")
        print(f"   • Total action groups found: {total_action_groups}")
        print(f"   • Action groups updated: {updated_count}")
        print("")
        print("✅ Action group update completed!")
        print("")
        print("🎯 Next Steps:")
        print("   1. Prepare and deploy updated agents")
        print("   2. Test the new ingest_documents function")
        print("   3. Verify multi-document support works")
        
    except Exception as e:
        logger.error(f"❌ Update failed: {e}")
        print(f"\n❌ UPDATE FAILED: {e}")


if __name__ == "__main__":
    main()
