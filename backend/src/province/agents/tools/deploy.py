"""
AWS Lambda Tools Deployment

This module handles deployment of all Lambda tools for Bedrock Agents.
"""

import boto3
import json
import logging
import os
import zipfile
import tempfile
from typing import Dict, Any, List
from .registry import tool_registry, LambdaTool

logger = logging.getLogger(__name__)

lambda_client = boto3.client('lambda')
iam_client = boto3.client('iam')


def create_lambda_execution_role(tool_name: str, permissions: List[str]) -> str:
    """Create IAM role for Lambda function execution"""
    
    role_name = f"province-{tool_name}-lambda-role"
    
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
    
    # Create role
    try:
        role_response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=f"Execution role for {tool_name} Lambda function"
        )
        
        role_arn = role_response['Role']['Arn']
        logger.info(f"Created IAM role: {role_name}")
        
    except iam_client.exceptions.EntityAlreadyExistsException:
        # Role already exists, get its ARN
        role_response = iam_client.get_role(RoleName=role_name)
        role_arn = role_response['Role']['Arn']
        logger.info(f"Using existing IAM role: {role_name}")
    
    # Attach basic Lambda execution policy
    try:
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
    except Exception as e:
        logger.warning(f"Could not attach basic execution policy: {str(e)}")
    
    # Create and attach custom policy for tool-specific permissions
    if permissions:
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": permissions,
                    "Resource": "*"
                }
            ]
        }
        
        policy_name = f"province-{tool_name}-policy"
        
        try:
            iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document)
            )
            logger.info(f"Attached custom policy to {role_name}")
        except Exception as e:
            logger.error(f"Failed to attach custom policy: {str(e)}")
    
    return role_arn


def create_deployment_package(tool: LambdaTool) -> bytes:
    """Create deployment package for Lambda function"""
    
    # Get the tool's Python file
    tool_file_path = os.path.join(
        os.path.dirname(__file__), 
        f"{tool.name}.py"
    )
    
    if not os.path.exists(tool_file_path):
        raise FileNotFoundError(f"Tool file not found: {tool_file_path}")
    
    # Create temporary zip file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add the main Lambda function file
            zip_file.write(tool_file_path, 'lambda_function.py')
            
            # Add requirements if they exist
            requirements_path = os.path.join(
                os.path.dirname(__file__), 
                f"{tool.name}_requirements.txt"
            )
            
            if os.path.exists(requirements_path):
                zip_file.write(requirements_path, 'requirements.txt')
        
        # Read the zip file content
        with open(temp_zip.name, 'rb') as f:
            zip_content = f.read()
        
        # Clean up temporary file
        os.unlink(temp_zip.name)
        
    return zip_content


def deploy_lambda_function(tool: LambdaTool) -> str:
    """Deploy a single Lambda function"""
    
    logger.info(f"Deploying Lambda function: {tool.lambda_function_name}")
    
    # Create IAM role
    role_arn = create_lambda_execution_role(tool.name, tool.required_permissions)
    
    # Create deployment package
    zip_content = create_deployment_package(tool)
    
    # Check if function already exists
    function_exists = False
    try:
        lambda_client.get_function(FunctionName=tool.lambda_function_name)
        function_exists = True
        logger.info(f"Function {tool.lambda_function_name} already exists, updating...")
    except lambda_client.exceptions.ResourceNotFoundException:
        logger.info(f"Creating new function: {tool.lambda_function_name}")
    
    if function_exists:
        # Update existing function
        try:
            # Update function code
            lambda_client.update_function_code(
                FunctionName=tool.lambda_function_name,
                ZipFile=zip_content
            )
            
            # Update function configuration
            lambda_client.update_function_configuration(
                FunctionName=tool.lambda_function_name,
                Runtime=tool.runtime,
                Handler=tool.handler,
                Timeout=tool.timeout,
                MemorySize=tool.memory_size,
                Environment={
                    'Variables': tool.environment_variables
                }
            )
            
            logger.info(f"Updated function: {tool.lambda_function_name}")
            
        except Exception as e:
            logger.error(f"Failed to update function {tool.lambda_function_name}: {str(e)}")
            raise
    else:
        # Create new function
        try:
            response = lambda_client.create_function(
                FunctionName=tool.lambda_function_name,
                Runtime=tool.runtime,
                Role=role_arn,
                Handler=tool.handler,
                Code={'ZipFile': zip_content},
                Description=tool.description,
                Timeout=tool.timeout,
                MemorySize=tool.memory_size,
                Environment={
                    'Variables': tool.environment_variables
                },
                Tags={
                    'Project': 'Province-Legal-OS',
                    'Component': 'Agent-Tools',
                    'Tool': tool.name
                }
            )
            
            logger.info(f"Created function: {tool.lambda_function_name}")
            
        except Exception as e:
            logger.error(f"Failed to create function {tool.lambda_function_name}: {str(e)}")
            raise
    
    # Get function ARN
    function_info = lambda_client.get_function(FunctionName=tool.lambda_function_name)
    function_arn = function_info['Configuration']['FunctionArn']
    
    return function_arn


def deploy_all_tools() -> Dict[str, str]:
    """Deploy all registered Lambda tools"""
    
    logger.info("Starting deployment of all Lambda tools...")
    
    deployed_functions = {}
    
    for tool_name, tool in tool_registry.tools.items():
        try:
            function_arn = deploy_lambda_function(tool)
            deployed_functions[tool_name] = function_arn
            logger.info(f"✓ Successfully deployed {tool_name}")
            
        except Exception as e:
            logger.error(f"✗ Failed to deploy {tool_name}: {str(e)}")
            deployed_functions[tool_name] = f"ERROR: {str(e)}"
    
    logger.info(f"Deployment completed. {len([v for v in deployed_functions.values() if not v.startswith('ERROR')])} successful, {len([v for v in deployed_functions.values() if v.startswith('ERROR')])} failed")
    
    return deployed_functions


def test_lambda_function(tool_name: str, test_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Test a deployed Lambda function"""
    
    tool = tool_registry.get_tool(tool_name)
    
    try:
        response = lambda_client.invoke(
            FunctionName=tool.lambda_function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        response_payload = json.loads(response['Payload'].read())
        
        return {
            'success': True,
            'status_code': response['StatusCode'],
            'response': response_payload
        }
        
    except Exception as e:
        logger.error(f"Failed to test function {tool_name}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def test_all_tools() -> Dict[str, Dict[str, Any]]:
    """Test all deployed Lambda tools"""
    
    test_payloads = {
        'save_document': {
            'matter_id': 'test-matter-123',
            'document_name': 'test-document.txt',
            'content': 'This is a test document for validation.',
            'document_type': 'test'
        },
        'create_deadline': {
            'title': 'Test Deadline',
            'due_date': '2024-12-31T17:00:00Z',
            'description': 'Test deadline for validation',
            'priority': 'medium'
        }
    }
    
    test_results = {}
    
    for tool_name in tool_registry.tools.keys():
        if tool_name in test_payloads:
            logger.info(f"Testing {tool_name}...")
            result = test_lambda_function(tool_name, test_payloads[tool_name])
            test_results[tool_name] = result
        else:
            test_results[tool_name] = {
                'success': False,
                'error': 'No test payload defined'
            }
    
    return test_results


def get_deployment_status() -> Dict[str, Any]:
    """Get status of all deployed tools"""
    
    status = {
        'total_tools': len(tool_registry.tools),
        'deployed_functions': {},
        'deployment_summary': {
            'successful': 0,
            'failed': 0,
            'not_deployed': 0
        }
    }
    
    for tool_name, tool in tool_registry.tools.items():
        try:
            function_info = lambda_client.get_function(FunctionName=tool.lambda_function_name)
            status['deployed_functions'][tool_name] = {
                'status': 'deployed',
                'function_arn': function_info['Configuration']['FunctionArn'],
                'runtime': function_info['Configuration']['Runtime'],
                'last_modified': function_info['Configuration']['LastModified']
            }
            status['deployment_summary']['successful'] += 1
            
        except lambda_client.exceptions.ResourceNotFoundException:
            status['deployed_functions'][tool_name] = {
                'status': 'not_deployed',
                'error': 'Function not found'
            }
            status['deployment_summary']['not_deployed'] += 1
            
        except Exception as e:
            status['deployed_functions'][tool_name] = {
                'status': 'error',
                'error': str(e)
            }
            status['deployment_summary']['failed'] += 1
    
    return status


if __name__ == "__main__":
    # Deploy all tools
    results = deploy_all_tools()
    
    print("\nDeployment Results:")
    print("=" * 50)
    for tool_name, result in results.items():
        status = "✓" if not result.startswith("ERROR") else "✗"
        print(f"{status} {tool_name}: {result}")
    
    # Test all tools
    print("\nTesting Tools:")
    print("=" * 50)
    test_results = test_all_tools()
    
    for tool_name, result in test_results.items():
        status = "✓" if result['success'] else "✗"
        print(f"{status} {tool_name}: {'Success' if result['success'] else result.get('error', 'Failed')}")