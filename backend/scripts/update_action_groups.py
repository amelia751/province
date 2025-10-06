#!/usr/bin/env python3
"""Update existing action groups to comprehensive versions instead of deleting/recreating."""

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


def create_comprehensive_function_definitions():
    """Create comprehensive function definitions matching the original specification."""
    
    return [
        {
            "name": "save_document",
            "description": "Save a document to S3 storage and update metadata. Writes to S3 (versioned), updates documents table, emits index event.",
            "parameters": {
                "engagement_id": {
                    "description": "Tax engagement ID in format tenant_id#engagement_id",
                    "type": "string",
                    "required": True
                },
                "path": {
                    "description": "Document path within engagement folder (e.g., /Documents/W2/W2_Acme.pdf, /Returns/1040_Draft.pdf)",
                    "type": "string",
                    "required": True
                },
                "content_b64": {
                    "description": "Base64 encoded document content",
                    "type": "string",
                    "required": True
                },
                "mime": {
                    "description": "MIME type of the document (e.g., application/pdf, application/json, text/markdown)",
                    "type": "string",
                    "required": True
                }
            }
        },
        {
            "name": "get_signed_url",
            "description": "Generate pre-signed S3 URL for uploads or downloads. Returns secure URL for client-side file operations.",
            "parameters": {
                "engagement_id": {
                    "description": "Tax engagement ID in format tenant_id#engagement_id",
                    "type": "string",
                    "required": True
                },
                "path": {
                    "description": "Document path within engagement folder",
                    "type": "string",
                    "required": True
                },
                "mode": {
                    "description": "Operation mode: 'put' for upload, 'get' for download",
                    "type": "string",
                    "required": True
                },
                "mime": {
                    "description": "MIME type (required for uploads, optional for downloads)",
                    "type": "string",
                    "required": False
                }
            }
        },
        {
            "name": "ingest_w2_pdf",
            "description": "Extract W-2 data from PDF using AWS Textract OCR. Produces structured W-2 JSON with pin-cites (filename + page + bbox). Aggregates multi-employer W-2s automatically. Validates totals and flags anomalies.",
            "parameters": {
                "s3_key": {
                    "description": "S3 key of the W-2 PDF document to process",
                    "type": "string",
                    "required": True
                },
                "taxpayer_name": {
                    "description": "Taxpayer name for validation against W-2 employee name",
                    "type": "string",
                    "required": True
                },
                "tax_year": {
                    "description": "Tax year (e.g., 2025) for validation and processing",
                    "type": "number",
                    "required": True
                }
            }
        },
        {
            "name": "calc_1040",
            "description": "Calculate 1040 tax return using deterministic computation. Loads W2_Extracts.json, applies standard deduction table + tax brackets, computes credits (CTC if eligible), yields /Workpapers/Calc_1040_Simple.json with provenance.",
            "parameters": {
                "engagement_id": {
                    "description": "Tax engagement ID to load W-2 data and save calculations",
                    "type": "string",
                    "required": True
                },
                "filing_status": {
                    "description": "Filing status: 'S' (Single), 'MFJ' (Married Filing Jointly), 'MFS' (Married Filing Separately), 'HOH' (Head of Household), 'QW' (Qualifying Widow)",
                    "type": "string",
                    "required": True
                },
                "dependents_count": {
                    "description": "Number of qualifying dependents for Child Tax Credit calculation",
                    "type": "number",
                    "required": True
                }
            }
        },
        {
            "name": "render_1040_draft",
            "description": "Generate draft 1040 PDF from calculation workpapers. Fills a 1040 PDF overlay from Calc JSON and saves to /Returns/1040_Draft.pdf with embedded provenance (calculation hash + tool versions).",
            "parameters": {
                "engagement_id": {
                    "description": "Tax engagement ID to load calculation data and save PDF",
                    "type": "string",
                    "required": True
                }
            }
        },
        {
            "name": "create_deadline",
            "description": "Create tax filing deadline calendar event. Generates /Deadlines/Federal.ics with filing deadline, multiple reminders, and extension fallback note. Sets EventBridge/SNS reminders.",
            "parameters": {
                "engagement_id": {
                    "description": "Tax engagement ID for deadline association",
                    "type": "string",
                    "required": True
                },
                "title": {
                    "description": "Deadline title (e.g., 'Federal Tax Filing Deadline - TY2025')",
                    "type": "string",
                    "required": True
                },
                "due_at_iso": {
                    "description": "Due date in ISO 8601 format (e.g., '2026-04-15T23:59:59Z'). Adjusted for weekends/holidays.",
                    "type": "string",
                    "required": True
                },
                "reminders": {
                    "description": "Array of reminder days before deadline (e.g., [30, 7, 1] for 30-day, 7-day, and 1-day reminders)",
                    "type": "array",
                    "required": True
                }
            }
        },
        {
            "name": "pii_scan",
            "description": "Scan document for Personally Identifiable Information (PII) and assess risk. Flags SSNs, bank numbers, suggests redaction (SSN to last-4), blocks sharing if high-risk. Required approval gate before document release.",
            "parameters": {
                "s3_key": {
                    "description": "S3 key of document to scan for PII (SSN, bank routing numbers, etc.)",
                    "type": "string",
                    "required": True
                }
            }
        }
    ]


def get_existing_action_group_id(bedrock_agent, agent_id: str):
    """Get the existing action group ID for an agent."""
    
    try:
        existing_groups = bedrock_agent.list_agent_action_groups(
            agentId=agent_id,
            agentVersion="DRAFT"
        )
        
        for group in existing_groups.get('actionGroupSummaries', []):
            if group['actionGroupName'] in ['TaxTools', 'ComprehensiveTaxTools']:
                return group['actionGroupId']
        
        return None
        
    except ClientError as e:
        logger.error(f"❌ Failed to list action groups: {e}")
        return None


def update_action_group(bedrock_agent, agent_id: str, agent_name: str, action_group_id: str, lambda_arn: str):
    """Update existing action group with comprehensive functions."""
    
    try:
        functions = create_comprehensive_function_definitions()
        
        response = bedrock_agent.update_agent_action_group(
            agentId=agent_id,
            agentVersion="DRAFT",
            actionGroupId=action_group_id,
            actionGroupName="ComprehensiveTaxTools",
            description="Comprehensive tax filing tools with full parameter specifications, validation, and provenance tracking",
            actionGroupExecutor={
                'lambda': lambda_arn
            },
            functionSchema={
                'functions': functions
            }
        )
        
        logger.info(f"✅ Updated action group for {agent_name}: {action_group_id}")
        return True
        
    except ClientError as e:
        logger.error(f"❌ Failed to update action group for {agent_name}: {e}")
        return False


def prepare_agent_after_update(bedrock_agent, agent_id: str, agent_name: str):
    """Prepare agent after updating action group."""
    
    try:
        bedrock_agent.prepare_agent(agentId=agent_id)
        logger.info(f"✅ Prepared {agent_name} with updated tools")
        return True
    except ClientError as e:
        logger.error(f"❌ Failed to prepare {agent_name}: {e}")
        return False


def main():
    """Update existing action groups with comprehensive specifications."""
    
    print("🔄 UPDATING ACTION GROUPS TO COMPREHENSIVE VERSIONS")
    print("=" * 70)
    print("📋 Updating existing action groups with:")
    print("   • save_document: 'mime' parameter (was 'mime_type')")
    print("   • get_signed_url: optional 'mime' parameter")
    print("   • create_deadline: 'reminders' array parameter")
    print("   • Enhanced descriptions with provenance & validation details")
    print("   • Proper parameter types and requirements")
    print("=" * 70)
    
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
    
    # Update action groups
    for agent_name, agent_id in agents.items():
        print(f"\n🔄 Updating {agent_name}...")
        
        # Get existing action group ID
        action_group_id = get_existing_action_group_id(bedrock_agent, agent_id)
        
        if not action_group_id:
            print(f"❌ No existing action group found for {agent_name}")
            results[agent_name] = {'success': False}
            continue
        
        # Update the action group
        updated = update_action_group(
            bedrock_agent, agent_id, agent_name, action_group_id, lambda_arn
        )
        
        if updated:
            prepared = prepare_agent_after_update(bedrock_agent, agent_id, agent_name)
            results[agent_name] = {
                'success': True,
                'action_group_id': action_group_id,
                'prepared': prepared
            }
        else:
            results[agent_name] = {'success': False}
    
    # Print summary
    print("\n" + "=" * 70)
    print("🎉 COMPREHENSIVE ACTION GROUPS UPDATE SUMMARY")
    print("=" * 70)
    
    success_count = 0
    for agent_name, result in results.items():
        if result.get('success') and result.get('prepared'):
            print(f"✅ {agent_name}: Updated to comprehensive tools")
            success_count += 1
        elif result.get('success'):
            print(f"⚠️  {agent_name}: Updated but not prepared")
        else:
            print(f"❌ {agent_name}: Update failed")
    
    print("=" * 70)
    
    if success_count == len(results):
        print("🎉 ALL AGENTS UPDATED TO COMPREHENSIVE TOOLS!")
        print("🔥 Tax system now has FULL specification compliance!")
        print("\n🎯 Enhanced capabilities:")
        print("   • Complete parameter validation")
        print("   • Provenance tracking")
        print("   • Multi-reminder deadline system")
        print("   • Enhanced PII scanning")
        print("   • Proper MIME type handling")
        print("   • Comprehensive error handling")
    else:
        print(f"✅ {success_count}/{len(results)} agents updated")
        print("💡 Some agents may need manual preparation")
    
    return results


if __name__ == "__main__":
    main()
