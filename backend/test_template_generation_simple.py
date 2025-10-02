#!/usr/bin/env python3
"""Simple test for AI template generation using environment configuration."""

import asyncio
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Load environment variables from .env.local
from dotenv import load_dotenv
load_dotenv('.env.local')

from ai_legal_os.services.ai_template_generator import AITemplateGenerator


async def test_simple_generation():
    """Test simple AI template generation."""
    
    print("🤖 Testing AI Template Generation")
    print("=" * 50)
    
    # Show configuration
    bedrock_region = os.environ.get("BEDROCK_REGION", "us-east-1")
    bedrock_model = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
    
    print(f"🌍 Bedrock Region: {bedrock_region}")
    print(f"🤖 Model ID: {bedrock_model}")
    print(f"🔑 API Key: {'✅ Found' if os.environ.get('BEDROCK_API_KEY') else '❌ Not found'}")
    print()
    
    # Initialize generator
    try:
        generator = AITemplateGenerator()
        print("✅ AI Generator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False
    
    # Test generation
    print("\n📋 Generating Contract Law Template...")
    
    try:
        template = await generator.generate_template_from_description(
            description="A template for commercial contract review and negotiation, including due diligence checklists and compliance requirements.",
            practice_area="Contract Law",
            matter_type="Commercial Agreement",
            jurisdiction="US-NY",
            user_id="test_user"
        )
        
        print("✅ Template generated successfully!")
        print(f"📝 Name: {template.name}")
        print(f"📁 Folders: {len(template.folders)}")
        print(f"📄 Documents: {len(template.starter_docs)}")
        print(f"⏰ Deadlines: {len(template.deadlines)}")
        
        # Show folder structure
        print("\n📁 Folder Structure:")
        for folder in template.folders[:5]:  # Show first 5 folders
            print(f"   • {folder.name}")
            if folder.subfolders:
                for subfolder in folder.subfolders[:3]:  # Show first 3 subfolders
                    print(f"     └── {subfolder}")
        
        return True
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return False


async def main():
    """Main function."""
    
    success = await test_simple_generation()
    
    if success:
        print("\n🎉 AI Template Generation Test PASSED!")
    else:
        print("\n❌ AI Template Generation Test FAILED!")
        print("💡 Possible issues:")
        print("   - Bedrock not available in your region")
        print("   - Missing AWS permissions for Bedrock")
        print("   - Model not enabled in your account")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)