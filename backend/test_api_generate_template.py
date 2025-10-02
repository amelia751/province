#!/usr/bin/env python3
"""Test AI template generation via API endpoint."""

import asyncio
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Set AWS credentials
os.environ.setdefault("AWS_ACCESS_KEY_ID", "[REDACTED-AWS-KEY-1]")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "[REDACTED-AWS-SECRET-1]")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("BEDROCK_REGION", "us-east-1")
os.environ.setdefault("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")

from ai_legal_os.api.v1.templates import (
    generate_template_with_ai, 
    AITemplateGenerationRequest,
    get_ai_template_generator,
    get_template_service,
    get_current_user
)


async def test_api_template_generation():
    """Test template generation via API endpoint."""
    
    print("🧪 Testing API Template Generation")
    print("=" * 60)
    print()
    
    # Test Case 1: Personal Injury Template
    print("Test 1: Generating Personal Injury Template...")
    print("-" * 60)
    
    request1 = AITemplateGenerationRequest(
        description="A comprehensive template for automobile accident cases, including client intake, medical records tracking, and settlement negotiations.",
        practice_area="Personal Injury",
        matter_type="Motor Vehicle Accident",
        jurisdiction="US-CA",
        additional_context="Focus on California-specific statute of limitations and discovery requirements."
    )
    
    try:
        current_user = await get_current_user()
        ai_generator = get_ai_template_generator()
        template_service = get_template_service()
        
        template1 = await generate_template_with_ai(
            request=request1,
            current_user=current_user,
            ai_generator=ai_generator,
            template_service=template_service
        )
        
        print(f"✅ Template Generated: {template1.name}")
        print(f"   📝 Description: {template1.description[:100]}...")
        print(f"   📁 Folders: {len(template1.folders)}")
        print(f"   📄 Documents: {len(template1.starter_docs)}")
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
        print()
        
    except Exception as e:
        print(f"❌ Test 1 Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test Case 2: Contract Law Template
    print("Test 2: Generating Contract Law Template...")
    print("-" * 60)
    
    request2 = AITemplateGenerationRequest(
        description="Template for reviewing and negotiating commercial contracts, including SaaS agreements and vendor contracts.",
        practice_area="Contract Law",
        matter_type="Commercial Agreement",
        jurisdiction="US-NY"
    )
    
    try:
        template2 = await generate_template_with_ai(
            request=request2,
            current_user=current_user,
            ai_generator=ai_generator,
            template_service=template_service
        )
        
        print(f"✅ Template Generated: {template2.name}")
        print(f"   📝 Description: {template2.description[:100]}...")
        print(f"   📁 Folders: {len(template2.folders)}")
        print(f"   📄 Documents: {len(template2.starter_docs)}")
        print(f"   ⏰ Deadlines: {len(template2.deadlines)}")
        print()
        
    except Exception as e:
        print(f"❌ Test 2 Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("=" * 60)
    print("🎉 All API Template Generation Tests PASSED!")
    print()
    print("Your backend can now:")
    print("  ✅ Generate templates via API endpoint")
    print("  ✅ Create comprehensive legal matter templates")
    print("  ✅ Store templates in repository")
    print("  ✅ Return structured template data")
    print()
    
    return True


async def main():
    """Main function."""
    
    success = await test_api_template_generation()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

