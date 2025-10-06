#!/usr/bin/env python3
"""Create action groups with minimal valid OpenAPI schema."""

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


def create_minimal_schema():
    """Create minimal OpenAPI schema that Bedrock accepts."""
    
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Tax Tools",
            "version": "1.0.0"
        },
        "paths": {
            "/save_document": {
                "post": {
                    "summary": "Save document",
                    "operationId": "save_document",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "engagement_id": {"type": "string"},
                                        "path": {"type": "string"},
                                        "content_b64": {"type": "string"},
                                        "mime_type": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            },
            "/get_signed_url": {
                "post": {
                    "summary": "Get signed URL",
                    "operationId": "get_signed_url",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "engagement_id": {"type": "string"},
                                        "path": {"type": "string"},
                                        "mode": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            },
            "/ingest_w2_pdf": {
                "post": {
                    "summary": "Process W-2",
                    "operationId": "ingest_w2_pdf",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "s3_key": {"type": "string"},
                                        "taxpayer_name": {"type": "string"},
                                        "tax_year": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            },
            "/calc_1040": {
                "post": {
                    "summary": "Calculate 1040",
                    "operationId": "calc_1040",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "engagement_id": {"type": "string"},
                                        "filing_status": {"type": "string"},
                                        "dependents_count": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            },
            "/render_1040_draft": {
                "post": {
                    "summary": "Render PDF",
                    "operationId": "render_1040_draft",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "engagement_id": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            },
            "/create_deadline": {
                "post": {
                    "summary": "Create deadline",
                    "operationId": "create_deadline",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "engagement_id": {"type": "string"},
                                        "title": {"type": "string"},
                                        "due_at_iso": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            },
            "/pii_scan": {
                "post": {
                    "summary": "Scan PII",
                    "operationId": "pii_scan",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "s3_key": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Success"}
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
            if group['actionGroupName'] == 'TaxTools':
                logger.info(f"✅ {agent_name} already has TaxTools action group")
                return group['actionGroupId']
        
        # Create the action group with minimal schema
        schema = create_minimal_schema()
        
        response = bedrock_agent.create_agent_action_group(
            agentId=agent_id,
            agentVersion="DRAFT",
            actionGroupName="TaxTools",
            description="Tax filing tools",
            actionGroupExecutor={
                'lambda': lambda_arn
            },
            apiSchema={
                'payload': json.dumps(schema)
            }
        )
        
        action_group_id = response['agentActionGroup']['actionGroupId']
        logger.info(f"✅ Created TaxTools action group for {agent_name}: {action_group_id}")
        
        return action_group_id
        
    except ClientError as e:
        logger.error(f"❌ Failed to create action group for {agent_name}: {e}")
        return None


def prepare_agent_after_action_group(bedrock_agent, agent_id: str, agent_name: str):
    """Prepare agent after adding action group."""
    
    try:
        bedrock_agent.prepare_agent(agentId=agent_id)
        logger.info(f"✅ Prepared {agent_name}")
        return True
    except ClientError as e:
        logger.error(f"❌ Failed to prepare {agent_name}: {e}")
        return False


def main():
    """Create action groups for all agents."""
    
    print("🛠️  Creating minimal action groups...")
    print("=" * 50)
    
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
        print(f"Processing {agent_name}...")
        
        action_group_id = create_action_group_for_agent(
            bedrock_agent, agent_id, agent_name, lambda_arn
        )
        
        if action_group_id:
            prepared = prepare_agent_after_action_group(bedrock_agent, agent_id, agent_name)
            results[agent_name] = {
                'success': True,
                'action_group_id': action_group_id,
                'prepared': prepared
            }
        else:
            results[agent_name] = {'success': False}
    
    # Print summary
    print("\n" + "=" * 50)
    print("🎉 SUMMARY")
    print("=" * 50)
    
    success_count = 0
    for agent_name, result in results.items():
        if result.get('success') and result.get('prepared'):
            print(f"✅ {agent_name}: Ready with tools")
            success_count += 1
        elif result.get('success'):
            print(f"⚠️  {agent_name}: Created but not prepared")
        else:
            print(f"❌ {agent_name}: Failed")
    
    print("=" * 50)
    
    if success_count == len(results):
        print("🎉 ALL AGENTS ARE INTERACTIVE!")
        print("🔥 Tax system fully operational!")
    else:
        print(f"✅ {success_count}/{len(results)} agents ready")
    
    return results


if __name__ == "__main__":
    main()
