#!/usr/bin/env python3
"""Complete deployment script for tax system including IAM roles, Lambda, and agents."""

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


def create_bedrock_agent_role():
    """Create IAM role for Bedrock agents."""
    
    iam = boto3.client('iam')
    
    # Trust policy for Bedrock
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Policy for Bedrock agent permissions
    agent_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "lambda:InvokeFunction"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::province-documents-storage",
                    "arn:aws:s3:::province-documents-storage/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                "Resource": [
                    "arn:aws:dynamodb:*:*:table/province-tax-*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "textract:AnalyzeDocument",
                    "textract:DetectDocumentText"
                ],
                "Resource": "*"
            }
        ]
    }
    
    role_name = "ProvinceBedrockAgentRole"
    
    try:
        # Create the role
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="IAM role for Bedrock agents"
        )
        
        # Attach the policy
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="BedrockAgentPolicy",
            PolicyDocument=json.dumps(agent_policy)
        )
        
        logger.info(f"✅ Created IAM role: {role_name}")
        
        # Get the role ARN
        response = iam.get_role(RoleName=role_name)
        return response['Role']['Arn']
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            logger.info(f"IAM role {role_name} already exists")
            response = iam.get_role(RoleName=role_name)
            return response['Role']['Arn']
        else:
            logger.error(f"❌ Error creating IAM role: {e}")
            raise


def create_lambda_execution_role():
    """Create IAM role for Lambda function execution."""
    
    iam = boto3.client('iam')
    
    # Trust policy for Lambda
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Policy for Lambda execution
    lambda_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::province-documents-storage",
                    "arn:aws:s3:::province-documents-storage/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                "Resource": [
                    "arn:aws:dynamodb:*:*:table/province-tax-*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "textract:AnalyzeDocument",
                    "textract:DetectDocumentText"
                ],
                "Resource": "*"
            }
        ]
    }
    
    role_name = "ProvinceTaxFilingLambdaRole"
    
    try:
        # Create the role
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="IAM role for tax filing Lambda function"
        )
        
        # Attach the policy
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="TaxFilingLambdaPolicy",
            PolicyDocument=json.dumps(lambda_policy)
        )
        
        logger.info(f"✅ Created Lambda IAM role: {role_name}")
        
        # Get the role ARN
        response = iam.get_role(RoleName=role_name)
        return response['Role']['Arn']
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            logger.info(f"Lambda IAM role {role_name} already exists")
            response = iam.get_role(RoleName=role_name)
            return response['Role']['Arn']
        else:
            logger.error(f"❌ Error creating Lambda IAM role: {e}")
            raise


def create_lambda_function(lambda_role_arn):
    """Create Lambda function for tax filing tools."""
    
    lambda_client = boto3.client('lambda', region_name='us-east-2')
    
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
    return {'success': True, 'message': 'Document saved (placeholder)'}

def handle_get_signed_url(params):
    """Handle get_signed_url tool call."""
    return {'success': True, 'url': 'https://example.com/signed-url'}

def handle_ingest_w2_pdf(params):
    """Handle ingest_w2_pdf tool call."""
    return {'success': True, 'message': 'W-2 ingested (placeholder)'}

def handle_calc_1040(params):
    """Handle calc_1040 tool call."""
    return {'success': True, 'refund_or_due': 1500.00}

def handle_render_1040_draft(params):
    """Handle render_1040_draft tool call."""
    return {'success': True, 'pdf_path': '/Returns/1040_Draft.pdf'}

def handle_create_deadline(params):
    """Handle create_deadline tool call."""
    return {'success': True, 'deadline_created': True}

def handle_pii_scan(params):
    """Handle pii_scan tool call."""
    return {'success': True, 'risk_level': 'low', 'findings_count': 0}
'''
    
    function_name = "province-tax-filing-tools"
    
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
                    'TAX_SYSTEM_VERSION': '1.0'
                }
            }
        )
        
        logger.info(f"✅ Created Lambda function: {function_name}")
        return response['FunctionArn']
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceConflictException':
            logger.info(f"Lambda function {function_name} already exists")
            response = lambda_client.get_function(FunctionName=function_name)
            return response['Configuration']['FunctionArn']
        else:
            logger.error(f"❌ Error creating Lambda function: {e}")
            raise


async def deploy_tax_agents(bedrock_role_arn, lambda_function_arn):
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
    
    # Update the bedrock client to use the correct role ARN
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
    
    print("🚀 Starting complete tax system deployment...")
    print("=" * 60)
    
    try:
        # Step 1: Create IAM roles
        print("📋 Step 1: Creating IAM roles...")
        bedrock_role_arn = create_bedrock_agent_role()
        lambda_role_arn = create_lambda_execution_role()
        
        # Wait a bit for IAM eventual consistency
        import time
        time.sleep(10)
        
        # Step 2: Create Lambda function
        print("📋 Step 2: Creating Lambda function...")
        lambda_function_arn = create_lambda_function(lambda_role_arn)
        
        # Step 3: Deploy agents
        print("📋 Step 3: Deploying Bedrock agents...")
        deployed_agents = await deploy_tax_agents(bedrock_role_arn, lambda_function_arn)
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎉 DEPLOYMENT SUMMARY")
        print("=" * 60)
        
        print(f"🔐 Bedrock Agent Role: {bedrock_role_arn}")
        print(f"🔐 Lambda Role: {lambda_role_arn}")
        print(f"⚡ Lambda Function: {lambda_function_arn}")
        print()
        
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
        else:
            print("⚠️  Some agents failed to deploy. Check the errors above.")
        
        return deployed_agents
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        raise


if __name__ == "__main__":
    print("Deploying complete tax system...")
    print("This will create IAM roles, Lambda function, and deploy all agents...")
    
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
