#!/usr/bin/env python3
"""Test script for AI template generation functionality."""

import asyncio
import sys
import os
import getpass
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ai_legal_os.services.ai_template_generator import AITemplateGenerator
from ai_legal_os.services.template_parser import TemplateParser


def setup_aws_credentials():
    """Check for AWS credentials or Bedrock API key."""
    
    # Check if Bedrock API key is available
    if os.environ.get("BEDROCK_API_KEY"):
        print("✅ Found Bedrock API key in environment")
        return True
    
    # Check if standard AWS credentials are available
    if (os.environ.get("AWS_ACCESS_KEY_ID") or 
        os.environ.get("AWS_PROFILE") or 
        os.path.exists(os.path.expanduser("~/.aws/credentials"))):
        print("✅ Found AWS credentials")
        return True
    
    print("🔐 AWS Credentials Setup")
    print("=" * 30)
    print("AWS credentials or Bedrock API key are required for AI template generation.")
    print("You can either:")
    print("1. Enter credentials now (temporary for this session)")
    print("2. Set up AWS CLI with 'aws configure'")
    print("3. Set environment variables AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
    print("4. Set BEDROCK_API_KEY environment variable")
    print()
    
    choice = input("Enter credentials now? (y/n): ").lower().strip()
    
    if choice == 'y' or choice == 'yes':
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
    else:
        print("❌ AWS credentials required to test Bedrock functionality")
        return False


async def test_ai_template_generation():
    """Test AI-powered template generation."""
    
    print("🤖 Testing AI Template Generation with Claude on Bedrock")
    print("=" * 60)
    
    # Initialize the AI generator
    try:
        generator = AITemplateGenerator()
        print("✅ AI Template Generator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize AI generator: {e}")
        return False
    
    # Test case 1: Personal Injury Template
    print("\n📋 Test Case 1: Personal Injury Template")
    print("-" * 40)
    
    try:
        template = await generator.generate_template_from_description(
            description="A comprehensive template for personal injury cases involving motor vehicle accidents, including medical records management, insurance correspondence, and settlement negotiations.",
            practice_area="Personal Injury",
            matter_type="Motor Vehicle Accident",
            jurisdiction="US-CA",
            user_id="test_user",
            additional_context="Focus on California-specific statute of limitations and discovery rules"
        )
        
        print(f"✅ Generated template: {template.name}")
        print(f"   Description: {template.description}")
        print(f"   Folders: {len(template.folders)} folders")
        print(f"   Starter Docs: {len(template.starter_docs)} documents")
        print(f"   Deadlines: {len(template.deadlines)} deadline rules")
        print(f"   Agents: {len(template.agents)} agents")
        
        # Validate the template structure
        if template.name and template.folders and template.applies_to:
            print("✅ Template structure validation passed")
        else:
            print("❌ Template structure validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Failed to generate personal injury template: {e}")
        return False
    
    # Test case 2: Corporate Contract Template
    print("\n📋 Test Case 2: Corporate Contract Template")
    print("-" * 40)
    
    try:
        template2 = await generator.generate_template_from_description(
            description="Template for managing corporate contract negotiations and reviews, including due diligence, compliance checks, and contract lifecycle management.",
            practice_area="Corporate Law",
            matter_type="Contract Review",
            jurisdiction="US-NY",
            user_id="test_user"
        )
        
        print(f"✅ Generated template: {template2.name}")
        print(f"   Folders: {len(template2.folders)} folders")
        print(f"   Starter Docs: {len(template2.starter_docs)} documents")
        
    except Exception as e:
        print(f"❌ Failed to generate corporate template: {e}")
        return False
    
    # Test case 3: Template Enhancement
    print("\n🔧 Test Case 3: Template Enhancement")
    print("-" * 40)
    
    try:
        enhanced_template = await generator.enhance_existing_template(
            template=template,
            enhancement_request="Add specific folders for expert witness reports and add deadlines for medical record requests",
            user_id="test_user"
        )
        
        print(f"✅ Enhanced template: {enhanced_template.name}")
        print(f"   Original folders: {len(template.folders)}")
        print(f"   Enhanced folders: {len(enhanced_template.folders)}")
        
    except Exception as e:
        print(f"❌ Failed to enhance template: {e}")
        return False
    
    # Test case 4: Template Analysis
    print("\n📊 Test Case 4: Template Analysis")
    print("-" * 40)
    
    try:
        suggestions = await generator.suggest_template_improvements(
            template=template,
            usage_analytics={"usage_count": 15, "avg_matter_duration": 180}
        )
        
        print(f"✅ Generated {len(suggestions)} improvement suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
            
    except Exception as e:
        print(f"❌ Failed to analyze template: {e}")
        return False
    
    # Test case 5: YAML Export and Validation
    print("\n📄 Test Case 5: YAML Export and Validation")
    print("-" * 40)
    
    try:
        yaml_content = TemplateParser.template_to_yaml(template)
        print("✅ Successfully exported template to YAML")
        
        # Validate by parsing back
        parsed_template = TemplateParser.parse_yaml_template(yaml_content, "test_user")
        
        if parsed_template.name == template.name:
            print("✅ YAML round-trip validation passed")
        else:
            print("❌ YAML round-trip validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Failed YAML export/validation: {e}")
        return False
    
    print("\n🎉 All AI Template Generation Tests Passed!")
    print("=" * 60)
    return True


async def main():
    """Main test function."""
    
    # Setup AWS credentials if needed
    if not setup_aws_credentials():
        print("\n❌ Cannot proceed without AWS credentials")
        sys.exit(1)
    
    # Check Bedrock access
    print("\n🔍 Checking Bedrock Access...")
    try:
        generator = AITemplateGenerator()
        # Test with a simple prompt
        await generator._call_claude("Hello, can you respond with 'OK'?")
        print("✅ Bedrock access confirmed")
    except Exception as e:
        print(f"❌ Bedrock access failed: {e}")
        print("\nPossible issues:")
        print("1. Bedrock service not available in your region")
        print("2. Claude model not enabled in your AWS account")
        print("3. Insufficient IAM permissions for bedrock:InvokeModel")
        print("4. Model ID might be incorrect for your region")
        sys.exit(1)
    
    success = await test_ai_template_generation()
    
    if success:
        print("\n✅ AI Template Generation is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ AI Template Generation tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())