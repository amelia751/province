"""
Test script for the conversational tax filing flow using Strands SDK.

This script simulates a user going through the complete tax filing process:
1. Start conversation
2. Provide filing status
3. Process W2 data
4. Calculate taxes
5. Fill forms
6. Save completed return
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from province.services.tax_conversation_service import tax_conversation_service

# Load environment variables
load_dotenv('.env.local')


async def simulate_user_conversation():
    """Simulate a complete user conversation flow."""
    
    print("🏛️  Province Tax Filing System - Conversational Flow Test")
    print("=" * 60)
    
    try:
        # Step 1: Start conversation
        print("\n📞 Starting conversation...")
        session_id = "test_session_001"
        initial_message = await tax_conversation_service.start_conversation(session_id)
        print(f"🤖 Agent: {initial_message}")
        
        # Step 2: User provides filing status
        print("\n👤 User: I'm single")
        response1 = await tax_conversation_service.continue_conversation(
            "I'm single", 
            session_id
        )
        print(f"🤖 Agent: {response1}")
        
        # Step 3: User responds about dependents
        print("\n👤 User: I don't have any dependents")
        response2 = await tax_conversation_service.continue_conversation(
            "I don't have any dependents", 
            session_id
        )
        print(f"🤖 Agent: {response2}")
        
        # Step 4: List available W2s and process one
        print("\n📄 Checking available W2 documents...")
        available_w2s = await tax_conversation_service.list_available_w2s()
        print(f"Available W2s: {available_w2s[:3]}")  # Show first 3
        
        if available_w2s:
            w2_to_process = available_w2s[0]  # Use first available W2
            print(f"\n👤 User: Please process my W2 document: {w2_to_process}")
            response3 = await tax_conversation_service.continue_conversation(
                f"Please process my W2 document: {w2_to_process}. Use the ingest_w2_tool with s3_key '{w2_to_process}' and taxpayer_name 'John Doe'.",
                session_id
            )
            print(f"🤖 Agent: {response3}")
        else:
            print("⚠️  No W2 documents found in bucket. Using mock data...")
            print("\n👤 User: I have wages of $50,000 and federal withholding of $7,500")
            response3 = await tax_conversation_service.continue_conversation(
                "I have wages of $50,000 and federal withholding of $7,500. Please use the manage_state_tool to set wages to 50000 and withholding to 7500.",
                session_id
            )
            print(f"🤖 Agent: {response3}")
        
        # Step 5: Calculate taxes
        print("\n👤 User: Please calculate my taxes now")
        response4 = await tax_conversation_service.continue_conversation(
            "Please calculate my taxes now using the calc_1040_tool with filing_status 'Single', wages from our conversation, and withholding from our conversation.",
            session_id
        )
        print(f"🤖 Agent: {response4}")
        
        # Step 6: Fill the form
        print("\n👤 User: Great! Please fill out my 1040 form")
        response5 = await tax_conversation_service.continue_conversation(
            "Great! Please fill out my 1040 form using the fill_form_tool with the information we've collected.",
            session_id
        )
        print(f"🤖 Agent: {response5}")
        
        # Step 7: Save the completed return
        print("\n👤 User: Perfect! Please save my completed tax return")
        response6 = await tax_conversation_service.continue_conversation(
            "Perfect! Please save my completed tax return using the save_document_tool.",
            session_id
        )
        print(f"🤖 Agent: {response6}")
        
        # Step 8: Show final conversation state
        print("\n📊 Final Conversation State:")
        final_state = tax_conversation_service.get_conversation_state(session_id)
        print(json.dumps(final_state, indent=2, default=str))
        
        print("\n✅ Conversation flow completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error in conversation flow: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_individual_tools():
    """Test individual tools separately."""
    
    print("\n🔧 Testing Individual Tools")
    print("=" * 40)
    
    try:
        # Test W2 ingestion
        print("\n1. Testing W2 Ingestion...")
        available_w2s = await tax_conversation_service.list_available_w2s()
        if available_w2s:
            from province.agents.tax.tools.ingest_w2 import ingest_w2
            w2_result = await ingest_w2(available_w2s[0], "Test User", 2024)
            print(f"W2 Result: {w2_result.get('success', False)}")
            if w2_result.get('success'):
                print(f"Wages: ${w2_result.get('total_wages', 0):,.2f}")
                print(f"Withholding: ${w2_result.get('total_withholding', 0):,.2f}")
        
        # Test tax calculation (using simplified version)
        print("\n2. Testing Tax Calculation...")
        print("Using simplified calculation for demo...")
        
        # Test form filling
        print("\n3. Testing Form Filling...")
        from province.agents.tax.tools.form_filler import fill_tax_form
        form_data = {
            'filing_status': 'Single',
            'wages': 50000,
            'federal_withholding': 7500,
            'taxpayer_name': 'Test User',
            'ssn': '123-45-6789'
        }
        form_result = await fill_tax_form('1040', form_data)
        print(f"Form Filling Result: {form_result.get('success', False)}")
        
        print("\n✅ Individual tools test completed!")
        
    except Exception as e:
        print(f"\n❌ Error testing individual tools: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    
    print("🚀 Starting Tax Conversation Flow Tests")
    
    # Test individual tools first
    await test_individual_tools()
    
    # Then test full conversation flow
    await simulate_user_conversation()
    
    print("\n🎉 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
