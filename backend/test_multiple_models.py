#!/usr/bin/env python3
"""Test multiple Claude model IDs to find which ones work."""

import boto3
import json
import os

def test_model(client, model_id, region):
    """Test a specific model ID."""
    
    print(f"Testing: {model_id}")
    
    try:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "user",
                    "content": "Say 'Working!' to confirm."
                }
            ]
        }
        
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response["body"].read())
        
        if "content" in response_body and len(response_body["content"]) > 0:
            claude_response = response_body["content"][0]["text"]
            print(f"  ✅ SUCCESS! Response: {claude_response}")
            return True
        else:
            print(f"  ❌ Unexpected response format")
            return False
            
    except Exception as e:
        error_str = str(e)
        if "ValidationException" in error_str:
            print(f"  ⚠️  Model not available for on-demand use")
        elif "AccessDeniedException" in error_str:
            print(f"  ⚠️  Access denied - needs model access enabled")
        elif "ResourceNotFoundException" in error_str:
            print(f"  ⚠️  Model not found")
        else:
            print(f"  ❌ Error: {error_str[:100]}...")
        return False


def main():
    """Test multiple model IDs."""
    
    print("🧪 Testing Multiple Claude Models")
    print("=" * 60)
    
    region = os.environ.get("BEDROCK_REGION", "us-east-1")
    bedrock_access_key = os.environ.get("BEDROCK_AWS_ACCESS_KEY_ID")
    bedrock_secret_key = os.environ.get("BEDROCK_AWS_SECRET_ACCESS_KEY")
    
    print(f"Region: {region}")
    print(f"Credentials: {bedrock_access_key[:10] if bedrock_access_key else 'Standard'}...")
    print()
    
    # Create client
    if bedrock_access_key and bedrock_secret_key:
        client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            aws_access_key_id=bedrock_access_key,
            aws_secret_access_key=bedrock_secret_key
        )
    else:
        client = boto3.client("bedrock-runtime", region_name=region)
    
    # Model IDs to test (ordered by likelihood of working)
    model_ids = [
        # Claude 3.5 Sonnet (most recent)
        "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "us.anthropic.claude-3-5-sonnet-20240620-v1:0",
        
        # Claude 3 Sonnet
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "us.anthropic.claude-3-sonnet-20240229-v1:0",
        
        # Claude 3 Haiku (cheaper, faster)
        "anthropic.claude-3-haiku-20240307-v1:0",
        "us.anthropic.claude-3-haiku-20240307-v1:0",
        
        # Claude 3.5 v2 (newer, might need special access)
        "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    ]
    
    working_models = []
    
    for model_id in model_ids:
        if test_model(client, model_id, region):
            working_models.append(model_id)
        print()
    
    print("=" * 60)
    if working_models:
        print(f"🎉 Found {len(working_models)} working model(s):")
        for model in working_models:
            print(f"  ✅ {model}")
        print()
        print(f"Update your .env.local with:")
        print(f"BEDROCK_MODEL_ID={working_models[0]}")
    else:
        print("❌ No working models found")
        print()
        print("Next steps:")
        print("1. Go to AWS Bedrock Console")
        print("2. Enable Claude model access")
        print("3. Wait 5-10 minutes for access to be granted")
        print("4. Run this script again")


if __name__ == "__main__":
    main()

