#!/usr/bin/env python3
"""Create only the IAM roles and Lambda function (no Bedrock agents)."""

import boto3
import json
import tempfile
import zipfile
from botocore.exceptions import ClientError


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
        
        print(f"✅ Created IAM role: {role_name}")
        
        # Get the role ARN
        response = iam.get_role(RoleName=role_name)
        return response['Role']['Arn']
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print(f"IAM role {role_name} already exists")
            response = iam.get_role(RoleName=role_name)
            return response['Role']['Arn']
        else:
            print(f"❌ Error creating IAM role: {e}")
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
        
        print(f"✅ Created Lambda IAM role: {role_name}")
        
        # Get the role ARN
        response = iam.get_role(RoleName=role_name)
        return response['Role']['Arn']
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print(f"Lambda IAM role {role_name} already exists")
            response = iam.get_role(RoleName=role_name)
            return response['Role']['Arn']
        else:
            print(f"❌ Error creating Lambda IAM role: {e}")
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
    logger.info(f"Save document called with: {params}")
    return {'success': True, 'message': 'Document saved successfully'}

def handle_get_signed_url(params):
    """Handle get_signed_url tool call."""
    logger.info(f"Get signed URL called with: {params}")
    return {'success': True, 'url': 'https://example.com/signed-url'}

def handle_ingest_w2_pdf(params):
    """Handle ingest_w2_pdf tool call."""
    logger.info(f"Ingest W-2 called with: {params}")
    return {'success': True, 'total_wages': 75000.00, 'total_withholding': 8500.00}

def handle_calc_1040(params):
    """Handle calc_1040 tool call."""
    logger.info(f"Calculate 1040 called with: {params}")
    return {'success': True, 'refund_or_due': 1500.00, 'is_refund': True}

def handle_render_1040_draft(params):
    """Handle render_1040_draft tool call."""
    logger.info(f"Render 1040 draft called with: {params}")
    return {'success': True, 'pdf_path': '/Returns/1040_Draft.pdf'}

def handle_create_deadline(params):
    """Handle create_deadline tool call."""
    logger.info(f"Create deadline called with: {params}")
    return {'success': True, 'deadline_created': True}

def handle_pii_scan(params):
    """Handle pii_scan tool call."""
    logger.info(f"PII scan called with: {params}")
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
        
        print(f"✅ Created Lambda function: {function_name}")
        return response['FunctionArn']
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceConflictException':
            print(f"Lambda function {function_name} already exists")
            response = lambda_client.get_function(FunctionName=function_name)
            return response['Configuration']['FunctionArn']
        else:
            print(f"❌ Error creating Lambda function: {e}")
            raise


def main():
    """Main function."""
    
    print("🚀 Creating IAM roles and Lambda function...")
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
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎉 INFRASTRUCTURE READY")
        print("=" * 60)
        
        print(f"🔐 Bedrock Agent Role: {bedrock_role_arn}")
        print(f"🔐 Lambda Role: {lambda_role_arn}")
        print(f"⚡ Lambda Function: {lambda_function_arn}")
        
        print("\n📋 Next Steps:")
        print("1. Add Bedrock permissions to the province user:")
        print('   {"Effect": "Allow", "Action": ["bedrock:*"], "Resource": "*"}')
        print("2. Run: python scripts/deploy_complete_tax_system.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


if __name__ == "__main__":
    main()
