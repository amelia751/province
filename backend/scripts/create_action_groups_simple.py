#!/usr/bin/env python3
"""Create action groups for all tax agents with simplified schema."""

import boto3
import json
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


def get_lambda_arn():
    """Get the Lambda function ARN."""
    account_id = boto3.client('sts').get_caller_identity()['Account']
    return f"arn:aws:lambda:us-east-2:{account_id}:function:province-tax-filing-tools"


def create_simple_tax_tools_schema():
    """Create a simplified OpenAPI schema for tax filing tools."""
    
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Tax Filing Tools",
            "version": "1.0.0"
        },
        "paths": {
            "/save_document": {
                "post": {
                    "summary": "Save document",
                    "operationId": "save_document",
                    "parameters": [
                        {
                            "name": "engagement_id",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Tax engagement ID"
                        },
                        {
                            "name": "path",
                            "in": "query", 
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Document path"
                        },
                        {
                            "name": "content_b64",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Base64 content"
                        },
                        {
                            "name": "mime_type",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "MIME type"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success"
                        }
                    }
                }
            },
            "/get_signed_url": {
                "post": {
                    "summary": "Get signed URL",
                    "operationId": "get_signed_url",
                    "parameters": [
                        {
                            "name": "engagement_id",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "path",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "mode",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "enum": ["put", "get"]}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success"
                        }
                    }
                }
            },
            "/ingest_w2_pdf": {
                "post": {
                    "summary": "Process W-2 PDF",
                    "operationId": "ingest_w2_pdf",
                    "parameters": [
                        {
                            "name": "s3_key",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "taxpayer_name",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "tax_year",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success"
                        }
                    }
                }
            },
            "/calc_1040": {
                "post": {
                    "summary": "Calculate 1040",
                    "operationId": "calc_1040",
                    "parameters": [
                        {
                            "name": "engagement_id",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "filing_status",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "dependents_count",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success"
                        }
                    }
                }
            },
            "/render_1040_draft": {
                "post": {
                    "summary": "Render 1040 PDF",
                    "operationId": "render_1040_draft",
                    "parameters": [
                        {
                            "name": "engagement_id",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success"
                        }
                    }
                }
            },
            "/create_deadline": {
                "post": {
                    "summary": "Create deadline",
                    "operationId": "create_deadline",
                    "parameters": [
                        {
                            "name": "engagement_id",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "title",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "due_at_iso",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success"
                        }
                    }
                }
            },
            "/pii_scan": {
                "post": {
                    "summary": "Scan for PII",
                    "operationId": "pii_scan",
                    "parameters": [
                        {
                            "name": "s3_key",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success"
                        }
                    }
                }
            }
        }
    }


def create_action_group_for_agent(bedrock_agent, agent_id: str, agent_name: str, lambda_arn: str):
    """Create action group for a specific agent."""
    
    try:
        # Check if action group already exists
        existing_groups = bedrock_agent.list_agent_action_groups(
            agentId=agent_id,
            agentVersion="DRAFT"
        )
        
        for group in existing_groups.get('actionGroupSummaries', []):
            if group['actionGroupName'] == 'TaxFilingTools':
                logger.info(f"✅ {agent_name} already has TaxFilingTools action group")
                return group['actionGroupId']
        
        # Create the action group
        schema = create_simple_tax_tools_schema()
        
        response = bedrock_agent.create_agent_action_group(
            agentId=agent_id,
            agentVersion="DRAFT",
            actionGroupName="TaxFilingTools",
            description="Tools for tax filing operations",
            actionGroupExecutor={
                'lambda': lambda_arn
            },
            apiSchema={
                'payload': json.dumps(schema)
            }
        )
        
        action_group_id = response['agentActionGroup']['actionGroupId']
        logger.info(f"✅ Created TaxFilingTools action group for {agent_name}: {action_group_id}")
        
        return action_group_id
        
    except ClientError as e:
        logger.error(f"❌ Failed to create action group for {agent_name}: {e}")
        return None


def prepare_agent_after_action_group(bedrock_agent, agent_id: str, agent_name: str):
    """Prepare agent after adding action group."""
    
    try:
        bedrock_agent.prepare_agent(agentId=agent_id)
        logger.info(f"✅ Prepared {agent_name} with new action group")
        return True
    except ClientError as e:
        logger.error(f"❌ Failed to prepare {agent_name}: {e}")
        return False


def main():
    """Create action groups for all agents."""
    
    print("🛠️  Creating simplified action groups for tax agents...")
    print("=" * 60)
    
    bedrock_agent = get_bedrock_client()
    lambda_arn = get_lambda_arn()
    
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
    
    # Create action groups
    for agent_name, agent_id in agents.items():
        logger.info(f"Processing {agent_name}...")
        
        action_group_id = create_action_group_for_agent(
            bedrock_agent, agent_id, agent_name, lambda_arn
        )
        
        if action_group_id:
            # Prepare agent with new action group
            prepared = prepare_agent_after_action_group(bedrock_agent, agent_id, agent_name)
            results[agent_name] = {
                'agent_id': agent_id,
                'action_group_id': action_group_id,
                'prepared': prepared
            }
        else:
            results[agent_name] = {
                'agent_id': agent_id,
                'action_group_id': None,
                'prepared': False
            }
    
    # Print summary
    print("\n" + "=" * 60)
    print("🎉 ACTION GROUPS DEPLOYMENT SUMMARY")
    print("=" * 60)
    
    success_count = 0
    for agent_name, result in results.items():
        if result['action_group_id'] and result['prepared']:
            print(f"✅ {agent_name}: Action group created and prepared")
            success_count += 1
        elif result['action_group_id']:
            print(f"⚠️  {agent_name}: Action group created but not prepared")
        else:
            print(f"❌ {agent_name}: Failed to create action group")
    
    print("=" * 60)
    print(f"🎯 Successfully configured {success_count}/{len(results)} agents")
    
    if success_count == len(results):
        print("🎉 ALL AGENTS NOW HAVE TOOLS AND CAN ASK FOLLOW-UP QUESTIONS!")
        print("🔥 Tax system is fully interactive and operational!")
    else:
        print("⚠️  Some agents may need manual preparation.")
        print("💡 Run the script again in a few minutes to retry.")
    
    return results


if __name__ == "__main__":
    main()
