#!/usr/bin/env python3
"""Check Bedrock access and available models."""

import boto3
import json
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
import sys
sys.path.insert(0, str(src_path))

def check_bedrock_access():
    """Check what Bedrock resources are accessible."""
    
    print("🔍 Checking Bedrock Access")
    print("=" * 40)
    
    # Check environment
    print("Environment variables:")
    print(f"  AWS_REGION: {os.environ.get('AWS_REGION', 'Not set')}")
    print(f"  AWS_DEFAULT_REGION: {os.environ.get('AWS_DEFAULT_REGION', 'Not set')}")
    print(f"  BEDROCK_REGION: {os.environ.get('BEDROCK_REGION', 'Not set')}")
    print(f"  BEDROCK_API_KEY: {'Set' if os.environ.get('BEDROCK_API_KEY') else 'Not set'}")
    print()
    
    # Try different regions
    regions = ["us-east-1", "us-west-2", "eu-west-1"]
    
    for region in regions:
        print(f"Trying region: {region}")
        try:
            client = boto3.client("bedrock", region_name=region)
            
            # Try to list foundation models
            response = client.list_foundation_models()
            models = response.get('modelSummaries', [])
            
            print(f"  ✅ Found {len(models)} models in {region}")
            
            # Show Claude models specifically
            claude_models = [m for m in models if 'claude' in m.get('modelId', '').lower()]
            if claude_models:
                print(f"  📝 Claude models available:")
                for model in claude_models[:3]:  # Show first 3
                    print(f"    - {model.get('modelId')}")
            
            # Try bedrock-runtime
            runtime_client = boto3.client("bedrock-runtime", region_name=region)
            print(f"  ✅ Bedrock runtime client created for {region}")
            
            return region, claude_models
            
        except Exception as e:
            print(f"  ❌ Error in {region}: {e}")
    
    return None, []

def test_simple_invoke():
    """Test a simple model invocation."""
    
    region, models = check_bedrock_access()
    
    if not region or not models:
        print("\n❌ No accessible Bedrock regions found")
        return False
    
    print(f"\n🧪 Testing model invocation in {region}")
    
    # Use the first available Claude model
    model_id = models[0]['modelId']
    print(f"Using model: {model_id}")
    
    try:
        client = boto3.client("bedrock-runtime", region_name=region)
        
        # Prepare request based on model type
        if "claude-3" in model_id:
            # Claude 3 format
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "temperature": 0.1,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello! Please respond with just 'OK' to confirm you're working."
                    }
                ]
            }
        else:
            # Older Claude format
            body = {
                "prompt": "\n\nHuman: Hello! Please respond with just 'OK' to confirm you're working.\n\nAssistant:",
                "max_tokens_to_sample": 100,
                "temperature": 0.1
            }
        
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response["body"].read())
        print(f"✅ Model response: {response_body}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model invocation failed: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_invoke()
    if success:
        print("\n🎉 Bedrock is working!")
    else:
        print("\n❌ Bedrock access issues detected")