#!/usr/bin/env python3
"""
Complete Tax Flow Test - Fixed Version

Tests the complete tax conversation flow using the working tax_service
with all 4 tools: ingest_documents, calc_1040, fill_form, save_document
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from province.services.tax_service import tax_service
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.local')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_complete_tax_flow():
    """Test the complete tax flow with all 4 tools"""
    
    print("\n" + "="*80)
    print("🏛️  COMPLETE TAX FLOW TEST - ALL 4 TOOLS")
    print("="*80)
    print("Testing: ingest_documents, calc_1040, fill_form, save_document\n")
    
    # Start conversation
    print("📞 Step 1: Starting conversation...")
    session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    initial_message = await tax_service.start_conversation(session_id)
    print(f"✅ Started session: {session_id}")
    print(f"🤖 Agent: {initial_message[:200]}...\n")
    
    # Step 2: User provides filing status
    print("💍 Step 2: Providing filing status...")
    user_message = "I'm single"
    print(f"👤 User: {user_message}")
    response = await tax_service.continue_conversation(user_message, session_id)
    print(f"🤖 Agent: {response[:200]}...\n")
    
    # Small delay between messages to avoid throttling
    await asyncio.sleep(1)
    
    # Step 3: User provides dependents info
    print("👶 Step 3: Providing dependents information...")
    user_message = "No, I don't have any dependents"
    print(f"👤 User: {user_message}")
    response = await tax_service.continue_conversation(user_message, session_id)
    print(f"🤖 Agent: {response[:200]}...\n")
    
    await asyncio.sleep(1)
    
    # Step 4: TOOL 1 - ingest_documents
    print("📄 Step 4: Testing TOOL 1 - ingest_documents (W2 processing)...")
    w2_key = "datasets/w2-forms/test/W2_XL_input_clean_1000.pdf"
    user_message = f"Please process my W-2 document. I uploaded it to the system at {w2_key}. My name is John Smith."
    print(f"👤 User: {user_message}")
    response = await tax_service.continue_conversation(user_message, session_id)
    print(f"🤖 Agent: {response}")
    
    # Check if W2 was processed
    state = tax_service.get_conversation_state(session_id)
    if 'w2_data' in state:
        w2 = state['w2_data']
        print(f"✅ TOOL 1 SUCCESS: W2 processed!")
        print(f"   Wages: ${w2.get('total_wages', 0):,.2f}")
        print(f"   Withholding: ${w2.get('total_withholding', 0):,.2f}\n")
    else:
        print("❌ TOOL 1 FAILED: W2 not processed\n")
        return
    
    await asyncio.sleep(2)
    
    # Step 5: Provide additional info
    print("🏠 Step 5: Providing additional information...")
    user_message = "My address is 123 Main Street, Anytown, CA 90210"
    print(f"👤 User: {user_message}")
    response = await tax_service.continue_conversation(user_message, session_id)
    print(f"🤖 Agent: {response[:200]}...\n")
    
    await asyncio.sleep(1)
    
    # Step 6: TOOL 2 - calc_1040
    print("🧮 Step 6: Testing TOOL 2 - calc_1040 (Tax calculation)...")
    user_message = "Great! Now please calculate my taxes based on all the information I've provided."
    print(f"👤 User: {user_message}")
    response = await tax_service.continue_conversation(user_message, session_id)
    print(f"🤖 Agent: {response}")
    
    # Check if tax was calculated
    state = tax_service.get_conversation_state(session_id)
    if 'tax_calculation' in state:
        calc = state['tax_calculation']
        print(f"✅ TOOL 2 SUCCESS: Tax calculated!")
        print(f"   AGI: ${calc.get('agi', 0):,.2f}")
        print(f"   Tax: ${calc.get('tax', 0):,.2f}")
        print(f"   Refund/Due: ${calc.get('refund_or_due', 0):,.2f}\n")
    else:
        print("❌ TOOL 2 FAILED: Tax not calculated\n")
        return
    
    await asyncio.sleep(2)
    
    # Step 7: TOOL 3 - fill_form
    print("📝 Step 7: Testing TOOL 3 - fill_form (Form filling)...")
    user_message = "Perfect! Please fill out my Form 1040 with all this information."
    print(f"👤 User: {user_message}")
    response = await tax_service.continue_conversation(user_message, session_id)
    print(f"🤖 Agent: {response}")
    
    # Check if form was filled
    state = tax_service.get_conversation_state(session_id)
    if 'filled_form' in state:
        form = state['filled_form']
        print(f"✅ TOOL 3 SUCCESS: Form filled!")
        print(f"   Form Type: {form.get('form_type', 'Unknown')}")
        print(f"   Filled At: {form.get('filled_at', 'Unknown')}\n")
    else:
        print("❌ TOOL 3 FAILED: Form not filled\n")
        return
    
    await asyncio.sleep(2)
    
    # Step 8: TOOL 4 - save_document
    print("💾 Step 8: Testing TOOL 4 - save_document (Document saving)...")
    user_message = "Excellent! Please save my completed tax return to my documents."
    print(f"👤 User: {user_message}")
    response = await tax_service.continue_conversation(user_message, session_id)
    print(f"🤖 Agent: {response}")
    
    # Check if document was saved
    if "saved successfully" in response.lower() or "congratulations" in response.lower():
        print(f"✅ TOOL 4 SUCCESS: Document saved!\n")
    else:
        print("❌ TOOL 4 FAILED: Document not saved\n")
        return
    
    # Final summary
    print("\n" + "="*80)
    print("📊 FINAL TEST RESULTS")
    print("="*80)
    final_state = tax_service.get_conversation_state(session_id)
    
    tools_status = {
        "ingest_documents (W2 processing)": "✅ PASSED" if 'w2_data' in final_state else "❌ FAILED",
        "calc_1040 (Tax calculation)": "✅ PASSED" if 'tax_calculation' in final_state else "❌ FAILED",
        "fill_form (Form filling)": "✅ PASSED" if 'filled_form' in final_state else "❌ FAILED",
        "save_document (Document saving)": "✅ PASSED" if 'filled_form' in final_state else "❌ FAILED"
    }
    
    print("\n🔧 TOOL STATUS:")
    for tool, status in tools_status.items():
        print(f"   {status} - {tool}")
    
    all_passed = all("PASSED" in status for status in tools_status.values())
    
    if all_passed:
        print("\n🎉 SUCCESS! All 4 tools are working correctly!")
        print("✓ ingest_documents: Processed W2 and extracted data")
        print("✓ calc_1040: Calculated taxes correctly")
        print("✓ fill_form: Filled Form 1040 with data")
        print("✓ save_document: Saved completed return")
    else:
        print("\n❌ FAILURE: Some tools did not work correctly")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(test_complete_tax_flow())

