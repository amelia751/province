#!/usr/bin/env python3
"""Real AI template generation test using Claude on Bedrock."""

import asyncio
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ai_legal_os.services.ai_template_generator import AITemplateGenerator
from ai_legal_os.services.template_parser import TemplateParser


async def test_real_ai_generation():
    """Test real AI template generation with Claude on Bedrock."""
    
    print("🤖 Testing REAL AI Template Generation with Claude on Bedrock")
    print("=" * 70)
    
    # Set AWS region for Bedrock
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    
    # Initialize the real AI generator (no mock)
    try:
        generator = AITemplateGenerator(model_id="anthropic.claude-3-5-sonnet-20241022-v2:0")
        print("✅ Real AI Template Generator initialized")
    except Exception as e:
        print(f"❌ Failed to initialize AI generator: {e}")
        return False
    
    # Test Case: Employment Law Template
    print("\n📋 Generating Employment Law Template")
    print("-" * 50)
    
    try:
        template = await generator.generate_template_from_description(
            description="A comprehensive template for employment law cases involving wrongful termination, discrimination, and wage disputes. Should include EEOC procedures, documentation requirements, and settlement negotiations.",
            practice_area="Employment Law",
            matter_type="Wrongful Termination",
            jurisdiction="US-CA",
            user_id="test_user",
            additional_context="Focus on California Labor Code requirements and FEHA compliance"
        )
        
        print(f"✅ Successfully generated template!")
        print(f"📝 Template Name: {template.name}")
        print(f"📄 Description: {template.description}")
        print(f"📁 Number of folders: {len(template.folders)}")
        print(f"📋 Starter documents: {len(template.starter_docs)}")
        print(f"⏰ Deadlines: {len(template.deadlines)}")
        print(f"🤖 Agents: {len(template.agents)}")
        
        # Print folder structure
        print(f"\n📁 Folder Structure:")
        for i, folder in enumerate(template.folders, 1):
            print(f"   {i}. {folder.name}")
            if folder.subfolders:
                for subfolder in folder.subfolders:
                    print(f"      └── {subfolder}")
        
        # Print starter documents
        if template.starter_docs:
            print(f"\n📋 Starter Documents:")
            for i, doc in enumerate(template.starter_docs, 1):
                print(f"   {i}. {doc.path}")
                if doc.auto_generate:
                    print(f"      (Auto-generated)")
        
        # Print deadlines
        if template.deadlines:
            print(f"\n⏰ Deadlines:")
            for i, deadline in enumerate(template.deadlines, 1):
                print(f"   {i}. {deadline.name}")
                print(f"      Required: {deadline.required}")
        
        # Print agents
        if template.agents:
            print(f"\n🤖 AI Agents:")
            for i, agent in enumerate(template.agents, 1):
                print(f"   {i}. {agent.name}")
                print(f"      Skills: {', '.join(agent.skills)}")
        
        # Validate template structure
        if not template.name:
            print("❌ Template missing name")
            return False
        
        if not template.folders:
            print("❌ Template missing folders")
            return False
        
        if not template.applies_to:
            print("❌ Template missing applies_to criteria")
            return False
        
        print("\n✅ Template structure validation passed")
        
        # Test YAML export
        print("\n📄 Testing YAML Export...")
        yaml_content = TemplateParser.template_to_yaml(template)
        
        if len(yaml_content) > 100:  # Basic validation
            print("✅ YAML export successful")
            
            # Show first few lines of YAML
            yaml_lines = yaml_content.split('\n')[:10]
            print("📄 YAML Preview:")
            for line in yaml_lines:
                print(f"   {line}")
            if len(yaml_content.split('\n')) > 10:
                print("   ...")
        else:
            print("❌ YAML export failed - content too short")
            return False
        
        # Test YAML parsing back
        try:
            parsed_template = TemplateParser.parse_yaml_template(yaml_content, "test_user")
            if parsed_template.name == template.name:
                print("✅ YAML round-trip validation passed")
            else:
                print("❌ YAML round-trip validation failed")
                return False
        except Exception as e:
            print(f"❌ YAML parsing failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate template: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False


async def main():
    """Main test function."""
    
    print("🔍 Checking AWS Configuration...")
    
    # Check AWS region
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    print(f"   AWS Region: {region}")
    
    # Check credentials
    if os.environ.get("AWS_ACCESS_KEY_ID"):
        print("   ✅ AWS Access Key found")
    elif os.environ.get("AWS_PROFILE"):
        print(f"   ✅ AWS Profile: {os.environ.get('AWS_PROFILE')}")
    else:
        print("   ⚠️  No explicit AWS credentials found (using default)")
    
    print()
    
    success = await test_real_ai_generation()
    
    if success:
        print("\n🎉 REAL AI Template Generation Test PASSED!")
        print("✅ Claude on Bedrock is working correctly for template generation")
        sys.exit(0)
    else:
        print("\n❌ REAL AI Template Generation Test FAILED!")
        print("💡 Check AWS Bedrock permissions and model access")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())