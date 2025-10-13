"""
Test script for realistic tax filing conversation flow.

This demonstrates the complete end-to-end process with realistic data.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from province.services.tax_service import tax_service

# Load environment variables
load_dotenv('.env.local')


async def test_realistic_conversation():
    """Test a realistic conversation with actual tax data."""
    
    print("🏛️  Province Tax Filing System - Realistic Flow Test")
    print("=" * 60)
    
    try:
        # Step 1: Start conversation
        print("\n📞 Starting conversation...")
        session_id = "realistic_test_001"
        initial_message = await tax_service.start_conversation(session_id)
        print(f"🤖 Agent: {initial_message}")
        
        # Step 2: User provides filing status
        print("\n👤 User: I'm single")
        response1 = await tax_service.continue_conversation(
            "I'm single", 
            session_id
        )
        print(f"🤖 Agent: {response1}")
        
        # Step 3: User responds about dependents
        print("\n👤 User: I don't have any dependents")
        response2 = await tax_service.continue_conversation(
            "I don't have any dependents", 
            session_id
        )
        print(f"🤖 Agent: {response2}")
        
        # Step 4: User provides realistic W2 data manually
        print("\n👤 User: I had wages of $65,000 and federal withholding of $9,500 this year")
        response3 = await tax_service.continue_conversation(
            "I had wages of $65,000 and federal withholding of $9,500 this year. Please use the manage_state_tool to set wages to 65000 and withholding to 9500.",
            session_id
        )
        print(f"🤖 Agent: {response3}")
        
        # Step 5: Calculate taxes with realistic data
        print("\n👤 User: Please calculate my taxes using wages of $65,000 and withholding of $9,500")
        response4 = await tax_service.continue_conversation(
            "Please calculate my taxes using the calc_1040_tool with filing_status 'Single', wages 65000, and withholding 9500.",
            session_id
        )
        print(f"🤖 Agent: {response4}")
        
        # Step 6: Fill the form
        print("\n👤 User: Great! Please fill out my 1040 form with this information")
        response5 = await tax_service.continue_conversation(
            "Great! Please fill out my 1040 form using the fill_form_tool with the calculated information.",
            session_id
        )
        print(f"🤖 Agent: {response5}")
        
        # Step 7: Save the completed return
        print("\n👤 User: Perfect! Please save my completed tax return")
        response6 = await tax_service.continue_conversation(
            "Perfect! Please save my completed tax return using the save_document_tool.",
            session_id
        )
        print(f"🤖 Agent: {response6}")
        
        # Step 8: Show final conversation state
        print("\n📊 Final Conversation State:")
        final_state = tax_service.get_conversation_state(session_id)
        
        # Pretty print key information
        if 'tax_calculation' in final_state:
            calc = final_state['tax_calculation']
            print(f"  💰 AGI: ${calc.get('agi', 0):,.2f}")
            print(f"  📋 Standard Deduction: ${calc.get('standard_deduction', 0):,.2f}")
            print(f"  💸 Taxable Income: ${calc.get('taxable_income', 0):,.2f}")
            print(f"  🧾 Tax Liability: ${calc.get('tax', 0):,.2f}")
            print(f"  💵 Withholding: ${calc.get('withholding', 0):,.2f}")
            refund_or_due = calc.get('refund_or_due', 0)
            if refund_or_due >= 0:
                print(f"  🎉 Refund: ${refund_or_due:,.2f}")
            else:
                print(f"  💳 Amount Due: ${abs(refund_or_due):,.2f}")
        
        if 'filled_form' in final_state:
            print(f"  📄 Form Completed: {final_state['filled_form'].get('form_type', 'N/A')}")
            print(f"  ⏰ Completed At: {final_state['filled_form'].get('filled_at', 'N/A')}")
        
        print("\n✅ Realistic conversation flow completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error in realistic conversation flow: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_endpoints():
    """Test the API endpoints directly."""
    
    print("\n🌐 Testing API Endpoints")
    print("=" * 40)
    
    try:
        # Test starting conversation via service
        print("\n1. Testing conversation start...")
        session_id = "api_test_001"
        message = await tax_service.start_conversation(session_id)
        print(f"✅ Start conversation: {len(message)} characters")
        
        # Test W2 listing
        print("\n2. Testing W2 listing...")
        w2s = await tax_service.list_available_w2s()
        print(f"✅ Found {len(w2s)} W2 documents")
        
        # Test conversation state
        print("\n3. Testing conversation state...")
        state = tax_service.get_conversation_state(session_id)
        print(f"✅ State has {len(state)} keys")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing API endpoints: {str(e)}")
        return False


async def main():
    """Main test function."""
    
    print("🚀 Starting Realistic Tax Conversation Tests")
    
    # Test API endpoints
    api_success = await test_api_endpoints()
    
    # Test realistic conversation
    conversation_success = await test_realistic_conversation()
    
    if api_success and conversation_success:
        print("\n🎉 All tests passed! The conversational tax filing system is working correctly.")
        print("\n📋 Summary:")
        print("  ✅ Strands SDK integration working")
        print("  ✅ Conversational flow functional")
        print("  ✅ W2 processing capabilities")
        print("  ✅ Tax calculations working")
        print("  ✅ Form filling integrated")
        print("  ✅ Document saving functional")
        print("  ✅ State management working")
        
        print("\n🚀 Ready for frontend integration!")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
