#!/usr/bin/env python3
"""Direct test of AI template generation without full service dependencies."""

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


async def test_direct_generation():
    """Test direct AI template generation."""
    
    print("=" * 70)
    print("🧪 DIRECT AI TEMPLATE GENERATION TEST")
    print("=" * 70)
    print()
    
    # Initialize generator
    generator = AITemplateGenerator()
    print("✅ AI Template Generator initialized")
    print()
    
    # Test cases
    test_cases = [
        {
            "name": "Employment Law - Wrongful Termination",
            "description": "Template for wrongful termination cases including documentation, evidence gathering, and EEOC filing.",
            "practice_area": "Employment Law",
            "matter_type": "Wrongful Termination",
            "jurisdiction": "US-CA"
        },
        {
            "name": "Real Estate - Commercial Lease",
            "description": "Template for commercial lease transactions including due diligence, negotiations, and closing documents.",
            "practice_area": "Real Estate",
            "matter_type": "Commercial Lease",
            "jurisdiction": "US-NY"
        },
        {
            "name": "Family Law - Divorce",
            "description": "Template for contested divorce cases with child custody, property division, and support calculations.",
            "practice_area": "Family Law",
            "matter_type": "Divorce",
            "jurisdiction": "US-TX"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print("-" * 70)
        
        try:
            template = await generator.generate_template_from_description(
                description=test_case["description"],
                practice_area=test_case["practice_area"],
                matter_type=test_case["matter_type"],
                jurisdiction=test_case["jurisdiction"],
                user_id="test_user"
            )
            
            print(f"✅ Generated: {template.name}")
            print(f"   • Folders: {len(template.folders)}")
            print(f"   • Documents: {len(template.starter_docs)}")
            print(f"   • Deadlines: {len(template.deadlines)}")
            print(f"   • Agents: {len(template.agents)}")
            
            # Save to YAML
            from ai_legal_os.services.template_parser import TemplateParser
            yaml_content = TemplateParser.template_to_yaml(template)
            output_file = Path(__file__).parent / f"generated_{i}_{test_case['practice_area'].replace(' ', '_').lower()}.yaml"
            with open(output_file, 'w') as f:
                f.write(yaml_content)
            print(f"   • Saved to: {output_file.name}")
            
            results.append({
                "test": test_case['name'],
                "status": "✅ PASS",
                "template": template.name
            })
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            results.append({
                "test": test_case['name'],
                "status": "❌ FAIL",
                "error": str(e)
            })
        
        print()
    
    # Summary
    print("=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for r in results if "PASS" in r["status"])
    failed = sum(1 for r in results if "FAIL" in r["status"])
    
    for result in results:
        if "PASS" in result["status"]:
            print(f"{result['status']} {result['test']}")
            print(f"         → {result['template']}")
        else:
            print(f"{result['status']} {result['test']}")
            print(f"         → {result.get('error', 'Unknown error')}")
    
    print()
    print(f"Results: {passed} passed, {failed} failed out of {len(results)} tests")
    
    if passed == len(results):
        print()
        print("🎉 ALL TESTS PASSED!")
        print()
        print("Your backend is FULLY FUNCTIONAL for AI template generation!")
        return True
    else:
        return False


if __name__ == "__main__":
    success = asyncio.run(test_direct_generation())
    sys.exit(0 if success else 1)

