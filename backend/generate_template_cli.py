#!/usr/bin/env python3
"""CLI tool for generating legal templates using AI."""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ai_legal_os.services.ai_template_generator import AITemplateGenerator
from ai_legal_os.services.template_parser import TemplateParser


async def generate_template(args):
    """Generate a template using AI."""
    
    print(f"🤖 Generating {args.practice_area} template using Claude on Bedrock")
    print("=" * 60)
    
    # Initialize AI generator
    try:
        generator = AITemplateGenerator(model_id=args.model_id)
        print("✅ AI Generator initialized")
    except Exception as e:
        print(f"❌ Failed to initialize AI generator: {e}")
        return False
    
    # Generate template
    try:
        template = await generator.generate_template_from_description(
            description=args.description,
            practice_area=args.practice_area,
            matter_type=args.matter_type,
            jurisdiction=args.jurisdiction,
            user_id="cli_user",
            additional_context=args.context
        )
        
        print(f"✅ Generated template: {template.name}")
        print(f"📄 Description: {template.description}")
        print(f"📁 Folders: {len(template.folders)}")
        print(f"📋 Starter docs: {len(template.starter_docs)}")
        print(f"⏰ Deadlines: {len(template.deadlines)}")
        print(f"🤖 Agents: {len(template.agents)}")
        
        # Export to YAML
        yaml_content = TemplateParser.template_to_yaml(template)
        
        # Save to file if requested
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(yaml_content)
            print(f"💾 Saved template to: {output_path}")
        else:
            print("\n📄 Generated YAML Template:")
            print("-" * 40)
            print(yaml_content)
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate template: {e}")
        return False


def main():
    """Main CLI function."""
    
    parser = argparse.ArgumentParser(
        description="Generate legal matter templates using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a personal injury template
  python generate_template_cli.py \\
    --practice-area "Personal Injury" \\
    --matter-type "Motor Vehicle Accident" \\
    --jurisdiction "US-CA" \\
    --description "Template for car accident cases with medical records and insurance claims"
  
  # Generate a corporate contract template
  python generate_template_cli.py \\
    --practice-area "Corporate Law" \\
    --matter-type "Contract Review" \\
    --jurisdiction "US-NY" \\
    --description "Template for reviewing and negotiating commercial contracts" \\
    --output "corporate_contract_template.yaml"
        """
    )
    
    parser.add_argument(
        "--practice-area",
        required=True,
        help="Practice area (e.g., 'Personal Injury', 'Corporate Law', 'Family Law')"
    )
    
    parser.add_argument(
        "--matter-type", 
        required=True,
        help="Specific matter type (e.g., 'Motor Vehicle Accident', 'Contract Review')"
    )
    
    parser.add_argument(
        "--jurisdiction",
        required=True,
        help="Jurisdiction (e.g., 'US-CA', 'US-NY', 'UK')"
    )
    
    parser.add_argument(
        "--description",
        required=True,
        help="Detailed description of the template requirements"
    )
    
    parser.add_argument(
        "--context",
        help="Additional context or specific requirements"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file path for the generated YAML template"
    )
    
    parser.add_argument(
        "--model-id",
        default="anthropic.claude-3-5-sonnet-20241022-v2:0",
        help="Bedrock model ID to use (default: Claude 3.5 Sonnet)"
    )
    
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region for Bedrock (default: us-east-1)"
    )
    
    args = parser.parse_args()
    
    # Set AWS region
    os.environ["AWS_DEFAULT_REGION"] = args.region
    
    # Check AWS configuration
    print("🔍 AWS Configuration:")
    print(f"   Region: {args.region}")
    print(f"   Model: {args.model_id}")
    
    if os.environ.get("AWS_ACCESS_KEY_ID"):
        print("   ✅ AWS credentials found")
    elif os.environ.get("AWS_PROFILE"):
        print(f"   ✅ AWS profile: {os.environ.get('AWS_PROFILE')}")
    else:
        print("   ⚠️  Using default AWS credentials")
    
    print()
    
    # Run the generation
    success = asyncio.run(generate_template(args))
    
    if success:
        print("\n🎉 Template generation completed successfully!")
    else:
        print("\n❌ Template generation failed!")
        print("💡 Make sure you have:")
        print("   - AWS credentials configured")
        print("   - Bedrock access permissions")
        print("   - The specified model enabled in your AWS account")
        sys.exit(1)


if __name__ == "__main__":
    main()