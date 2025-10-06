#!/usr/bin/env python3
"""Create action groups for all tax agents to enable tool usage."""

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


def create_tax_tools_schema():
    """Create the OpenAPI schema for tax filing tools."""
    
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Tax Filing Tools API",
            "version": "1.0.0",
            "description": "Tools for tax filing operations"
        },
        "paths": {
            "/save_document": {
                "post": {
                    "summary": "Save a document to S3 and update metadata",
                    "operationId": "save_document",
                    "requestBody": {
                        "required": true,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "engagement_id": {"type": "string", "description": "Tax engagement ID"},
                                        "path": {"type": "string", "description": "Document path within engagement folder"},
                                        "content_b64": {"type": "string", "description": "Base64 encoded document content"},
                                        "mime_type": {"type": "string", "description": "MIME type of document"}
                                    },
                                    "required": ["engagement_id", "path", "content_b64", "mime_type"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Document saved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            },
            "/get_signed_url": {
                "post": {
                    "summary": "Generate pre-signed S3 URL for upload or download",
                    "operationId": "get_signed_url",
                    "requestBody": {
                        "required": true,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "engagement_id": {"type": "string", "description": "Tax engagement ID"},
                                        "path": {"type": "string", "description": "Document path"},
                                        "mode": {"type": "string", "enum": ["put", "get"], "description": "Upload or download mode"},
                                        "mime_type": {"type": "string", "description": "MIME type (required for uploads)"}
                                    },
                                    "required": ["engagement_id", "path", "mode"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Signed URL generated",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            },
            "/ingest_w2_pdf": {
                "post": {
                    "summary": "Extract W-2 data from PDF using OCR",
                    "operationId": "ingest_w2_pdf",
                    "requestBody": {
                        "required": true,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "s3_key": {"type": "string", "description": "S3 key of W-2 PDF"},
                                        "taxpayer_name": {"type": "string", "description": "Taxpayer name for validation"},
                                        "tax_year": {"type": "integer", "description": "Tax year"}
                                    },
                                    "required": ["s3_key", "taxpayer_name", "tax_year"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "W-2 data extracted",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            },
            "/calc_1040": {
                "post": {
                    "summary": "Calculate 1040 tax return",
                    "operationId": "calc_1040",
                    "requestBody": {
                        "required": true,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "engagement_id": {"type": "string", "description": "Tax engagement ID"},
                                        "filing_status": {"type": "string", "description": "Filing status (S, MFJ, MFS, HOH, QW)"},
                                        "dependents_count": {"type": "integer", "description": "Number of dependents"}
                                    },
                                    "required": ["engagement_id", "filing_status", "dependents_count"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Tax calculation completed",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            },
            "/render_1040_draft": {
                "post": {
                    "summary": "Generate draft 1040 PDF",
                    "operationId": "render_1040_draft",
                    "requestBody": {
                        "required": true,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "engagement_id": {"type": "string", "description": "Tax engagement ID"}
                                    },
                                    "required": ["engagement_id"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "PDF generated",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            },
            "/create_deadline": {
                "post": {
                    "summary": "Create tax filing deadline calendar event",
                    "operationId": "create_deadline",
                    "requestBody": {
                        "required": true,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "engagement_id": {"type": "string", "description": "Tax engagement ID"},
                                        "title": {"type": "string", "description": "Deadline title"},
                                        "due_at_iso": {"type": "string", "description": "Due date in ISO format"},
                                        "reminders": {"type": "array", "items": {"type": "integer"}, "description": "Reminder days"}
                                    },
                                    "required": ["engagement_id", "title", "due_at_iso", "reminders"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Deadline created",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            },
            "/pii_scan": {
                "post": {
                    "summary": "Scan document for PII and assess risk",
                    "operationId": "pii_scan",
                    "requestBody": {
                        "required": true,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "s3_key": {"type": "string", "description": "S3 key of document to scan"}
                                    },
                                    "required": ["s3_key"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "PII scan completed",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
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
        schema = create_tax_tools_schema()
        
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
    
    print("🛠️  Creating action groups for tax agents...")
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
