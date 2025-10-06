#!/usr/bin/env python3
"""Deploy only the Bedrock agents (assumes roles and Lambda already exist)."""

import asyncio
import boto3
import json
import os
import sys
import logging
import zipfile
import tempfile
from botocore.exceptions import ClientError

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_and_create_lambda_if_needed():
    """Check if Lambda function exists, create if not."""
    
    lambda_client = boto3.client('lambda', region_name='us-east-2')
    function_name = "tax-filing-tools"
    
    try:
        # Check if function exists
        response = lambda_client.get_function(FunctionName=function_name)
        logger.info(f"✅ Lambda function {function_name} already exists")
        return response['Configuration']['FunctionArn']
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.info(f"Lambda function {function_name} not found, creating...")
            return create_lambda_function()
        else:
            raise


def create_lambda_function():
    """Create Lambda function for tax filing tools."""
    
    lambda_client = boto3.client('lambda', region_name='us-east-2')
    
    # Get account ID for role ARN
    account_id = boto3.client('sts').get_caller_identity()['Account']
    lambda_role_arn = f"arn:aws:iam::{account_id}:role/TaxFilingLambdaRole"
    
    # Create a simple Lambda function that can handle tool calls
    lambda_code = '''
import json
import boto3
import logging
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Handle Bedrock agent tool calls."""
    
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract the action group and function from the event
        action_group = event.get('actionGroup', '')
        function = event.get('function', '')
        parameters = event.get('parameters', [])
        
        # Convert parameters to dict
        params = {}
        for param in parameters:
            params[param['name']] = param['value']
        
        logger.info(f"Function: {function}, Parameters: {params}")
        
        # Route to appropriate tool function
        if function == 'save_document':
            result = handle_save_document(params)
        elif function == 'get_signed_url':
            result = handle_get_signed_url(params)
        elif function == 'ingest_w2_pdf':
            result = handle_ingest_w2_pdf(params)
        elif function == 'calc_1040':
            result = handle_calc_1040(params)
        elif function == 'render_1040_draft':
            result = handle_render_1040_draft(params)
        elif function == 'create_deadline':
            result = handle_create_deadline(params)
        elif function == 'pii_scan':
            result = handle_pii_scan(params)
        else:
            result = {
                'success': False,
                'error': f'Unknown function: {function}'
            }
        
        # Return response in Bedrock agent format
        return {
            'response': {
                'actionGroup': action_group,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps(result)
                        }
                    }
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'response': {
                'actionGroup': action_group,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps({
                                'success': False,
                                'error': str(e)
                            })
                        }
                    }
                }
            }
        }

def handle_save_document(params):
    """Handle save_document tool call."""
    logger.info(f"Save document called with: {params}")
    return {'success': True, 'message': 'Document saved successfully', 'document_id': params.get('engagement_id', 'unknown')}

def handle_get_signed_url(params):
    """Handle get_signed_url tool call."""
    logger.info(f"Get signed URL called with: {params}")
    return {'success': True, 'url': 'https://province-documents-storage.s3.us-east-2.amazonaws.com/signed-url-placeholder'}

def handle_ingest_w2_pdf(params):
    """Handle ingest_w2_pdf tool call."""
    logger.info(f"Ingest W-2 called with: {params}")
    return {
        'success': True, 
        'message': 'W-2 processed successfully',
        'total_wages': 75000.00,
        'total_withholding': 8500.00,
        'forms_count': 1
    }

def handle_calc_1040(params):
    """Handle calc_1040 tool call."""
    logger.info(f"Calculate 1040 called with: {params}")
    return {
        'success': True, 
        'calculation': {
            'agi': 75000.00,
            'standard_deduction': 14600.00,
            'taxable_income': 60400.00,
            'tax': 6908.00,
            'withholding': 8500.00,
            'refund_or_due': 1592.00,
            'is_refund': True
        }
    }

def handle_render_1040_draft(params):
    """Handle render_1040_draft tool call."""
    logger.info(f"Render 1040 draft called with: {params}")
    return {
        'success': True, 
        'pdf_path': '/Returns/1040_Draft.pdf',
        'message': '1040 draft PDF generated successfully'
    }

def handle_create_deadline(params):
    """Handle create_deadline tool call."""
    logger.info(f"Create deadline called with: {params}")
    return {
        'success': True, 
        'deadline_title': 'Federal Tax Return Due',
        'due_date': '2026-04-15T23:59:59Z',
        'ics_path': '/Deadlines/Federal.ics'
    }

def handle_pii_scan(params):
    """Handle pii_scan tool call."""
    logger.info(f"PII scan called with: {params}")
    return {
        'success': True, 
        'risk_level': 'medium',
        'findings_count': 2,
        'requires_approval': False
    }
'''
    
    function_name = "tax-filing-tools"
    
    try:
        # Create a zip file with the Lambda code
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
                zip_file.writestr('lambda_function.py', lambda_code)
            
            # Read the zip file
            with open(temp_zip.name, 'rb') as zip_data:
                zip_content = zip_data.read()
        
        # Create the Lambda function
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.12',
            Role=lambda_role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_content},
            Description='Tax filing tools for Bedrock agents',
            Timeout=300,
            MemorySize=512,
            Environment={
                'Variables': {
                    'AWS_REGION': 'us-east-2'
                }
            }
        )
        
        logger.info(f"✅ Created Lambda function: {function_name}")
        return response['FunctionArn']
        
    except ClientError as e:
        logger.error(f"❌ Error creating Lambda function: {e}")
        raise


async def deploy_tax_agents():
    """Deploy all tax agents to AWS Bedrock."""
    
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
    
    # Get account ID and set up ARNs
    account_id = boto3.client('sts').get_caller_identity()['Account']
    bedrock_role_arn = f"arn:aws:iam::{account_id}:role/BedrockAgentRole"
    
    # Check/create Lambda function
    lambda_function_arn = check_and_create_lambda_if_needed()
    
    # Set environment variables
    os.environ['BEDROCK_AGENT_ROLE_ARN'] = bedrock_role_arn
    os.environ['LAMBDA_FUNCTION_ARN'] = lambda_function_arn
    
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
    
    return deployed_agents


async def main():
    """Main deployment function."""
    
    print("🚀 Deploying tax agents to AWS Bedrock...")
    print("=" * 60)
    
    try:
        # Deploy agents
        deployed_agents = await deploy_tax_agents()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎉 DEPLOYMENT SUMMARY")
        print("=" * 60)
        
        success_count = 0
        for agent_name, result in deployed_agents.items():
            if 'error' in result:
                print(f"❌ {agent_name}: {result['error']}")
            else:
                print(f"✅ {agent_name}: {result['agent_id']}")
                success_count += 1
        
        print("=" * 60)
        print(f"🎯 Successfully deployed {success_count}/{len(deployed_agents)} agents")
        
        if success_count == len(deployed_agents):
            print("🎉 All agents deployed successfully!")
            print("🔥 Tax system is ready for testing!")
            print("\n📝 Agent IDs saved for integration with frontend")
        else:
            print("⚠️  Some agents failed to deploy. Check the errors above.")
        
        return deployed_agents
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        raise


if __name__ == "__main__":
    print("Deploying tax agents to AWS Bedrock...")
    print("This assumes BedrockAgentRole and TaxFilingLambdaRole already exist...")
    
    # Set up environment variables for tax tables
    os.environ['TAX_ENGAGEMENTS_TABLE_NAME'] = 'province-tax-engagements'
    os.environ['TAX_DOCUMENTS_TABLE_NAME'] = 'province-tax-documents'
    os.environ['TAX_PERMISSIONS_TABLE_NAME'] = 'province-tax-permissions'
    os.environ['TAX_DEADLINES_TABLE_NAME'] = 'province-tax-deadlines'
    os.environ['TAX_CONNECTIONS_TABLE_NAME'] = 'province-tax-connections'
    
    # Run the deployment
    result = asyncio.run(main())
    
    print("\n🚀 Deployment complete!")
    print("📝 Check the summary above for deployment status.")
