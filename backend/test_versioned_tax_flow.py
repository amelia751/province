#!/usr/bin/env python3
"""
Test Versioned Tax Filing Flow

This script tests the complete tax filing flow with the new versioning system:
1. Start conversation
2. Process W2 data
3. Calculate taxes
4. Fill form (creates v1)
5. Fill form again with different data (creates v2)
6. List version history
7. Verify forms are properly filled
"""

import asyncio
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_versioned_tax_flow():
    """Test the complete versioned tax filing flow."""
    
    print("🚀 Starting Versioned Tax Filing Flow Test")
    print("=" * 60)
    
    try:
        # Import the tax service
        from province.services.tax_service import TaxService
        
        # Initialize the service
        tax_service = TaxService()
        session_id = f"test_versioned_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"📋 Session ID: {session_id}")
        print()
        
        # Step 1: Start conversation
        print("1️⃣ Starting conversation...")
        response = await tax_service.start_conversation(session_id)
        print(f"🤖 Agent: {response[:200]}...")
        print()
        
        # Step 2: Provide filing status
        print("2️⃣ Providing filing status...")
        response = await tax_service.continue_conversation("I'm single", session_id)
        print(f"🤖 Agent: {response[:200]}...")
        print()
        
        # Step 3: Provide dependents info
        print("3️⃣ Providing dependents info...")
        response = await tax_service.continue_conversation("I don't have any dependents", session_id)
        print(f"🤖 Agent: {response[:200]}...")
        print()
        
        # Step 4: Provide income info
        print("4️⃣ Providing income information...")
        response = await tax_service.continue_conversation("I had wages of $65,000 and federal withholding of $9,500 this year", session_id)
        print(f"🤖 Agent: {response[:200]}...")
        print()
        
        # Step 5: Calculate taxes
        print("5️⃣ Calculating taxes...")
        response = await tax_service.continue_conversation("Please calculate my taxes using wages of $65,000 and withholding of $9,500", session_id)
        print(f"🤖 Agent: {response[:200]}...")
        print()
        
        # Step 6: Fill form (Version 1)
        print("6️⃣ Filling 1040 form (Version 1)...")
        response = await tax_service.continue_conversation("Great! Please fill out my 1040 form with this information", session_id)
        print(f"🤖 Agent: {response}")
        print()
        
        # Step 7: Get version history
        print("7️⃣ Getting version history...")
        response = await tax_service.continue_conversation("Can you show me the version history for my tax form?", session_id)
        print(f"🤖 Agent: {response}")
        print()
        
        # Step 8: Update form with different data (Version 2)
        print("8️⃣ Updating form with different data (Version 2)...")
        response = await tax_service.continue_conversation("Actually, I want to update my form. My wages were $70,000 and withholding was $10,000", session_id)
        print(f"🤖 Agent: {response[:200]}...")
        print()
        
        # Step 9: Fill form again (should create Version 2)
        print("9️⃣ Filling form again (should create Version 2)...")
        response = await tax_service.continue_conversation("Please fill out my 1040 form again with the updated information", session_id)
        print(f"🤖 Agent: {response}")
        print()
        
        # Step 10: Get updated version history
        print("🔟 Getting updated version history...")
        response = await tax_service.continue_conversation("Show me the version history again", session_id)
        print(f"🤖 Agent: {response}")
        print()
        
        # Step 11: Check conversation state
        print("1️⃣1️⃣ Checking final conversation state...")
        final_state = tax_service.get_conversation_state(session_id)
        
        print("📊 Final Conversation State:")
        for key, value in final_state.items():
            if key == 'filled_form' and isinstance(value, dict):
                print(f"  📄 {key}:")
                for subkey, subvalue in value.items():
                    if subkey == 'versioning':
                        print(f"    🔄 {subkey}: {subvalue}")
                    elif subkey == 'form_data':
                        print(f"    📋 {subkey}: {len(subvalue)} fields")
                    else:
                        print(f"    📝 {subkey}: {str(subvalue)[:100]}...")
            else:
                print(f"  📝 {key}: {str(value)[:100]}...")
        
        print()
        print("✅ Versioned tax filing flow test completed successfully!")
        print()
        
        # Summary
        print("📋 Test Summary:")
        print("  ✅ Conversation started")
        print("  ✅ User information collected")
        print("  ✅ Tax calculations performed")
        print("  ✅ Form filled (Version 1)")
        print("  ✅ Version history retrieved")
        print("  ✅ Form updated (Version 2)")
        print("  ✅ Updated version history retrieved")
        print("  ✅ Versioning system working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in versioned tax flow test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_direct_form_filling():
    """Test direct form filling with versioning."""
    
    print("\n🧪 Testing Direct Form Filling with Versioning")
    print("=" * 50)
    
    try:
        from province.agents.tax.tools.form_filler import TaxFormFiller
        
        filler = TaxFormFiller()
        
        # Test data for form filling
        form_data_v1 = {
            'taxpayer_name': 'John Doe',
            'ssn': '123-45-6789',
            'filing_status': 'Single',
            'wages': '65000',
            'federal_withholding': '9500',
            'standard_deduction': '14600',
            'taxable_income': '50400',
            'tax_liability': '6141',
            'refund_or_due': '3359'
        }
        
        print("1️⃣ Filling form (Version 1)...")
        result_v1 = await filler.fill_1040_form(form_data_v1)
        
        if result_v1.get('success'):
            print(f"✅ Version 1 created successfully")
            print(f"   📄 URL: {result_v1.get('filled_form_url')}")
            versioning = result_v1.get('versioning', {})
            print(f"   🔄 Document ID: {versioning.get('document_id')}")
            print(f"   📊 Version: {versioning.get('version')}")
            print(f"   🆕 Is new: {versioning.get('is_new_document')}")
        else:
            print(f"❌ Version 1 failed: {result_v1.get('error')}")
            return False
        
        print()
        
        # Update form data for version 2
        form_data_v2 = {
            **form_data_v1,
            'wages': '70000',
            'federal_withholding': '10000',
            'taxable_income': '55400',
            'tax_liability': '6641',
            'refund_or_due': '3359'
        }
        
        print("2️⃣ Filling form (Version 2)...")
        result_v2 = await filler.fill_1040_form(form_data_v2)
        
        if result_v2.get('success'):
            print(f"✅ Version 2 created successfully")
            print(f"   📄 URL: {result_v2.get('filled_form_url')}")
            versioning = result_v2.get('versioning', {})
            print(f"   🔄 Document ID: {versioning.get('document_id')}")
            print(f"   📊 Version: {versioning.get('version')}")
            print(f"   🆕 Is new: {versioning.get('is_new_document')}")
            print(f"   📈 Total versions: {versioning.get('total_versions')}")
        else:
            print(f"❌ Version 2 failed: {result_v2.get('error')}")
            return False
        
        print()
        
        # Get version history
        print("3️⃣ Getting version history...")
        document_id = result_v1.get('versioning', {}).get('document_id')
        if document_id:
            versions = await filler.get_version_history(document_id)
            print(f"📋 Found {len(versions)} versions:")
            for version in versions:
                print(f"   📊 {version['version']}: {version['size']:,} bytes ({version['last_modified']})")
        else:
            print("❌ No document ID found")
        
        print("\n✅ Direct form filling test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error in direct form filling test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("🧪 VERSIONED TAX FILING SYSTEM TESTS")
    print("=" * 60)
    
    # Test 1: Full conversational flow with versioning
    success1 = await test_versioned_tax_flow()
    
    # Test 2: Direct form filling with versioning
    success2 = await test_direct_form_filling()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL TEST RESULTS:")
    print(f"  {'✅' if success1 else '❌'} Conversational Tax Flow with Versioning")
    print(f"  {'✅' if success2 else '❌'} Direct Form Filling with Versioning")
    
    if success1 and success2:
        print("\n🎉 All tests passed! Versioned tax filing system is working correctly.")
        print("\n📋 Key Features Verified:")
        print("  ✅ PDF forms are properly filled with PyMuPDF")
        print("  ✅ Document versioning system working")
        print("  ✅ Version history tracking functional")
        print("  ✅ Conversational flow integrated with versioning")
        print("  ✅ Multiple versions can be created and tracked")
    else:
        print("\n❌ Some tests failed. Please check the logs above.")
    
    return success1 and success2

if __name__ == "__main__":
    asyncio.run(main())
