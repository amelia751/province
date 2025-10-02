#!/usr/bin/env python3
"""Simple test to verify Bedrock Claude access."""

import asyncio
import sys
import os
import getpass
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ai_legal_os.services.ai_template_generator import AITemplateGenerator


def setup_aws_credentials():
    """Prompt user for AWS credentials if not already configured."""
    
    # Check if credentials are already available
    if (os.environ.get("AWS_ACCESS_KEY_ID") or 
        os.environ.get("AWS_PROFILE") or 
        os.path.exists(os.path.expanduser("~/.aws/credentials"))):
        print("✅ AWS credentials found")
        return True
    
    print("🔐 AWS Credentials Required")
    print("=" * 30)
    print("Please enter your AWS credentials:")
    print()
    
    access_key = input("AWS Access Key ID: ").strip()
    secret_key = getpass.getpass("AWS Secret Access Key: ").strip()
    region = input("AWS Region (default: us-east-1): ").strip() or "us-east-1"
    
    if access_key and secret_key:
        os.environ["AWS_ACCESS_KEY_ID"] = access_key
        os.environ["AWS_SECRET_ACCESS_KEY"] = secret_key
        os.environ["AWS_DEFAULT_REGION"] = region
        print("✅ Credentials set for this session")
        return True
    else:
        print("❌ Invalid credentials provided")
        return False


async def test_claude_simple():
    """Simple test of Claude on Bedrock."""
    
    print("🤖 Testing Claude on Bedrock")
    print("=" * 30)
    
    try:
        # Create generator without validation
        generator = AITemplateGenerator()
        
        # Skip validation and try direct call
        print("🔄 Calling Claude...")
        
        response = await generator._call_claude("Hello! Please respond with 'AI is working' to confirm you're functioning correctly.")
        
        print(f"✅ Claude Response: {response}")
        
        # Now try a simple template generation
        print("\n🔄 Testing template generation...")
        
        template = await generator.generate_template_from_description(
            description="A simple personal injury case template for testing",
            practice_area="Personal Injury",
            matter_type="Motor Vehicle Accident", 
            jurisdiction="US-CA",
            user_id="test_user"
        )
        
        print(f"✅ Generated template: {template.name}")
        print(f"   Folders: {len(template.folders)}")
        print(f"   Documents: {len(template.starter_docs)}")
        print(f"   Deadlines: {len(template.deadlines)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def main():
    """Main function."""
    
    if not setup_aws_credentials():
        print("❌ Cannot proceed without AWS credentials")
        sys.exit(1)
    
    success = await test_claude_simple()
    
    if success:
        print("\n🎉 Bedrock Claude is working correctly!")
    else:
        print("\n❌ Bedrock Claude test failed!")
        print("\nTroubleshooting tips:")
        print("1. Make sure Bedrock is available in your region")
        print("2. Check that Claude models are enabled in your AWS account")
        print("3. Verify IAM permissions for bedrock:InvokeModel")
        print("4. Try a different region (us-east-1 or us-west-2)")


if __name__ == "__main__":
    asyncio.run(main())