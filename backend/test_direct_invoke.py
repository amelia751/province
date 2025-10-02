#!/usr/bin/env python3
"""Test direct Bedrock model invocation without listing models."""

import boto3
import json
import os

def test_direct_invoke():
    """Test invoking Claude directly."""
    
    print("🧪 Testing direct Bedrock invocation")
    print("=" * 50)
    
    region = os.environ.get("BEDROCK_REGION", "us-east-1")
    model_id = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
    
    # Check for Bedrock-specific credentials
    bedrock_access_key = os.environ.get("BEDROCK_AWS_ACCESS_KEY_ID")
    bedrock_secret_key = os.environ.get("BEDROCK_AWS_SECRET_ACCESS_KEY")
    
    print(f"Region: {region}")
    print(f"Model: {model_id}")
    if bedrock_access_key:
        print(f"Using Bedrock-specific credentials: {bedrock_access_key[:10]}...")
    else:
        print(f"Using standard AWS credentials")
    print()
    
    try:
        if bedrock_access_key and bedrock_secret_key:
            client = boto3.client(
                "bedrock-runtime",
                region_name=region,
                aws_access_key_id=bedrock_access_key,
                aws_secret_access_key=bedrock_secret_key
            )
        else:
            client = boto3.client("bedrock-runtime", region_name=region)
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": "Please respond with 'Working!' to confirm the connection."
                }
            ]
        }
        
        print("🔄 Calling Claude...")
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response["body"].read())
        
        if "content" in response_body and len(response_body["content"]) > 0:
            claude_response = response_body["content"][0]["text"]
            print(f"✅ SUCCESS! Claude responded: {claude_response}")
            return True
        else:
            print(f"❌ Unexpected response format: {response_body}")
            return False
            
    except Exception as e:
        error_str = str(e)
        print(f"❌ Error: {error_str}")
        
        if "AccessDeniedException" in error_str:
            print("\n⚠️  IAM Permissions Issue Detected!")
            print("\nYou need to add Bedrock permissions to your IAM user.")
            print("\nRequired IAM Policy:")
            print("-" * 50)
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "BedrockInvokeModel",
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:InvokeModel",
                            "bedrock:InvokeModelWithResponseStream"
                        ],
                        "Resource": [
                            f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-*",
                            f"arn:aws:bedrock:*::foundation-model/anthropic.claude-*"
                        ]
                    }
                ]
            }
            print(json.dumps(policy, indent=2))
            print("-" * 50)
            print("\nSteps to fix:")
            print("1. Go to AWS IAM Console")
            print("2. Find user: province")
            print("3. Click 'Add permissions' -> 'Create inline policy'")
            print("4. Switch to JSON tab and paste the policy above")
            print("5. Name it 'BedrockAccess' and save")
            
        elif "ResourceNotFoundException" in error_str or "ValidationException" in error_str:
            print("\n⚠️  Model Access Issue!")
            print(f"\nThe model {model_id} might not be available in {region}.")
            print("\nSteps to fix:")
            print("1. Go to AWS Bedrock Console")
            print("2. Click 'Model access' in the left sidebar")
            print("3. Click 'Manage model access'")
            print("4. Enable 'Claude 3.5 Sonnet v2'")
            print("5. Save changes and wait for access to be granted")
        
        return False

if __name__ == "__main__":
    success = test_direct_invoke()
    
    if success:
        print("\n🎉 Bedrock is working! Template generation should work now.")
    else:
        print("\n❌ Bedrock access issue - follow the steps above to fix.")

