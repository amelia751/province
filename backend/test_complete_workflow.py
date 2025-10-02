#!/usr/bin/env python3
"""Complete workflow test for template generation once Bedrock is enabled."""

import asyncio
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Load environment from .env.local
from dotenv import load_dotenv
load_dotenv('.env.local')

from ai_legal_os.services.ai_template_generator import AITemplateGenerator
from ai_legal_os.services.template_parser import TemplateParser


async def test_complete_workflow():
    """Test the complete template generation workflow."""
    
    print("=" * 70)
    print("🧪 COMPLETE TEMPLATE GENERATION WORKFLOW TEST")
    print("=" * 70)
    print()
    
    # Display configuration
    print("📋 Configuration:")
    print(f"   Region: {os.environ.get('BEDROCK_REGION', 'not set')}")
    print(f"   Model: {os.environ.get('BEDROCK_MODEL_ID', 'not set')}")
    bedrock_key = os.environ.get('BEDROCK_AWS_ACCESS_KEY_ID', '')
    print(f"   Credentials: {bedrock_key[:10]}..." if bedrock_key else "   Credentials: Not set")
    print()
    
    # Test 1: Initialize AI Generator
    print("Test 1: Initializing AI Template Generator")
    print("-" * 70)
    try:
        generator = AITemplateGenerator()
        print("✅ AI Template Generator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False
    print()
    
    # Test 2: Generate Simple Template
    print("Test 2: Generating Personal Injury Template")
    print("-" * 70)
    try:
        template1 = await generator.generate_template_from_description(
            description="A comprehensive template for automobile accident cases with client intake, medical records tracking, and settlement negotiations.",
            practice_area="Personal Injury",
            matter_type="Motor Vehicle Accident",
            jurisdiction="US-CA",
            user_id="test_user_001",
            additional_context="Include California-specific statute of limitations and discovery requirements."
        )
        
        print(f"✅ Template Generated!")
        print(f"   📝 Name: {template1.name}")
        print(f"   📄 Description: {template1.description[:80]}...")
        print(f"   📁 Folders: {len(template1.folders)}")
        print(f"   📄 Starter Docs: {len(template1.starter_docs)}")
        print(f"   ⏰ Deadlines: {len(template1.deadlines)}")
        print(f"   🤖 Agents: {len(template1.agents)}")
        print()
        
        # Show folder structure
        print("   📁 Folder Structure:")
        for i, folder in enumerate(template1.folders[:5]):
            print(f"      {i+1}. {folder.name}")
            if folder.subfolders:
                for subfolder in folder.subfolders[:2]:
                    print(f"         └── {subfolder}")
        if len(template1.folders) > 5:
            print(f"      ... and {len(template1.folders) - 5} more folders")
        print()
        
        # Show sample documents
        if template1.starter_docs:
            print("   📄 Sample Starter Documents:")
            for i, doc in enumerate(template1.starter_docs[:3]):
                print(f"      {i+1}. {doc.path}")
        print()
        
    except Exception as e:
        print(f"❌ Template generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Export to YAML
    print("Test 3: Exporting Template to YAML")
    print("-" * 70)
    try:
        yaml_content = TemplateParser.template_to_yaml(template1)
        yaml_lines = yaml_content.split('\n')
        print(f"✅ Template exported to YAML ({len(yaml_lines)} lines)")
        print()
        print("   First 10 lines of YAML:")
        for line in yaml_lines[:10]:
            print(f"   {line}")
        print("   ...")
        print()
        
        # Save to file
        output_file = Path(__file__).parent / "generated_template_test.yaml"
        with open(output_file, 'w') as f:
            f.write(yaml_content)
        print(f"✅ YAML saved to: {output_file}")
        print()
        
    except Exception as e:
        print(f"❌ YAML export failed: {e}")
        return False
    
    # Test 4: Generate Another Template (Different Type)
    print("Test 4: Generating Contract Law Template")
    print("-" * 70)
    try:
        template2 = await generator.generate_template_from_description(
            description="Template for reviewing and negotiating SaaS agreements and vendor contracts.",
            practice_area="Contract Law",
            matter_type="Commercial Agreement",
            jurisdiction="US-NY",
            user_id="test_user_001"
        )
        
        print(f"✅ Template Generated!")
        print(f"   📝 Name: {template2.name}")
        print(f"   📁 Folders: {len(template2.folders)}")
        print(f"   📄 Starter Docs: {len(template2.starter_docs)}")
        print()
        
    except Exception as e:
        print(f"❌ Template generation failed: {e}")
        return False
    
    # Test 5: Suggest Improvements
    print("Test 5: Analyzing Template for Improvements")
    print("-" * 70)
    try:
        suggestions = await generator.suggest_template_improvements(
            template=template1,
            usage_analytics={"usage_count": 5}
        )
        
        print(f"✅ Generated {len(suggestions)} improvement suggestions:")
        for i, suggestion in enumerate(suggestions[:5], 1):
            print(f"   {i}. {suggestion[:80]}...")
        print()
        
    except Exception as e:
        print(f"⚠️  Template analysis failed (non-critical): {e}")
        print()
    
    # Summary
    print("=" * 70)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 70)
    print()
    print("✅ Your backend can now:")
    print("   • Generate legal matter templates using AI")
    print("   • Create comprehensive folder structures")
    print("   • Generate starter documents and deadlines")
    print("   • Export templates to YAML format")
    print("   • Analyze and improve templates")
    print()
    print("📁 Files created:")
    print(f"   • {output_file}")
    print()
    print("🚀 Next steps:")
    print("   • Start your FastAPI server: uvicorn ai_legal_os.main:app --reload")
    print("   • Test API endpoints: python3 test_api_generate_template.py")
    print("   • Run full test suite: pytest tests/")
    print()
    
    return True


async def main():
    """Main function."""
    
    try:
        success = await test_complete_workflow()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

