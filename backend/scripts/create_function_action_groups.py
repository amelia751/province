#!/usr/bin/env python3
"""Create action groups using function definitions instead of OpenAPI schema."""

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


def create_function_definitions():
    """Create function definitions for action group."""
    
    return [
        {
            "name": "save_document",
            "description": "Save a document to S3 storage",
            "parameters": {
                "engagement_id": {
                    "description": "Tax engagement ID",
                    "type": "string",
                    "required": True
                },
                "path": {
                    "description": "Document path within engagement folder",
                    "type": "string",
                    "required": True
                },
                "content_b64": {
                    "description": "Base64 encoded document content",
                    "type": "string",
                    "required": True
                },
                "mime_type": {
                    "description": "MIME type of the document",
                    "type": "string",
                    "required": True
                }
            }
        },
        {
            "name": "get_signed_url",
            "description": "Generate pre-signed S3 URL for upload or download",
            "parameters": {
                "engagement_id": {
                    "description": "Tax engagement ID",
                    "type": "string",
                    "required": True
                },
                "path": {
                    "description": "Document path",
                    "type": "string",
                    "required": True
                },
                "mode": {
                    "description": "Upload or download mode",
                    "type": "string",
                    "required": True
                }
            }
        },
        {
            "name": "ingest_w2_pdf",
            "description": "Extract W-2 data from PDF using OCR",
            "parameters": {
                "s3_key": {
                    "description": "S3 key of W-2 PDF",
                    "type": "string",
                    "required": True
                },
                "taxpayer_name": {
                    "description": "Taxpayer name for validation",
                    "type": "string",
                    "required": True
                },
                "tax_year": {
                    "description": "Tax year",
                    "type": "number",
                    "required": True
                }
            }
        },
        {
            "name": "calc_1040",
            "description": "Calculate 1040 tax return",
            "parameters": {
                "engagement_id": {
                    "description": "Tax engagement ID",
                    "type": "string",
                    "required": True
                },
                "filing_status": {
                    "description": "Filing status",
                    "type": "string",
                    "required": True
                },
                "dependents_count": {
                    "description": "Number of dependents",
                    "type": "number",
                    "required": True
                }
            }
        },
        {
            "name": "render_1040_draft",
            "description": "Generate draft 1040 PDF",
            "parameters": {
                "engagement_id": {
                    "description": "Tax engagement ID",
                    "type": "string",
                    "required": True
                }
            }
        },
        {
            "name": "create_deadline",
            "description": "Create tax filing deadline calendar event",
            "parameters": {
                "engagement_id": {
                    "description": "Tax engagement ID",
                    "type": "string",
                    "required": True
                },
                "title": {
                    "description": "Deadline title",
                    "type": "string",
                    "required": True
                },
                "due_at_iso": {
                    "description": "Due date in ISO format",
                    "type": "string",
                    "required": True
                }
            }
        },
        {
            "name": "pii_scan",
            "description": "Scan document for PII and assess risk",
            "parameters": {
                "s3_key": {
                    "description": "S3 key of document to scan",
                    "type": "string",
                    "required": True
                }
            }
        }
    ]


def create_action_group_for_agent(bedrock_agent, agent_id: str, agent_name: str, lambda_arn: str):
    """Create action group for a specific agent using function definitions."""
    
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
        
        # Create the action group using function definitions
        functions = create_function_definitions()
        
        response = bedrock_agent.create_agent_action_group(
            agentId=agent_id,
            agentVersion="DRAFT",
            actionGroupName="TaxTools",
            description="Tax filing tools",
            actionGroupExecutor={
                'lambda': lambda_arn
            },
            functionSchema={
                'functions': functions
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
    """Create action groups for all agents using function definitions."""
    
    print("🛠️  Creating action groups with function definitions...")
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
    print("\n" + "=" * 60)
    print("🎉 ACTION GROUPS DEPLOYMENT SUMMARY")
    print("=" * 60)
    
    success_count = 0
    for agent_name, result in results.items():
        if result.get('success') and result.get('prepared'):
            print(f"✅ {agent_name}: Ready with tools")
            success_count += 1
        elif result.get('success'):
            print(f"⚠️  {agent_name}: Created but not prepared")
        else:
            print(f"❌ {agent_name}: Failed")
    
    print("=" * 60)
    
    if success_count == len(results):
        print("🎉 ALL AGENTS ARE NOW INTERACTIVE!")
        print("🔥 Tax system fully operational with tools!")
        print("\n🎯 Agents can now:")
        print("   • Ask follow-up questions")
        print("   • Process W-2 documents")
        print("   • Calculate taxes")
        print("   • Generate PDFs")
        print("   • Create deadlines")
        print("   • Scan for PII")
    else:
        print(f"✅ {success_count}/{len(results)} agents ready")
        print("💡 Some agents may need manual preparation")
    
    return results


if __name__ == "__main__":
    main()
