"""
API Integration Test for Tax Conversation System

This script demonstrates how the frontend can interact with the 
conversational tax filing API endpoints.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any


class TaxConversationAPIClient:
    """Client for interacting with the tax conversation API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
    
    async def start_conversation(self) -> Dict[str, Any]:
        """Start a new tax filing conversation."""
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/api/v1/tax-service/start") as response:
                if response.status == 200:
                    data = await response.json()
                    self.session_id = data.get('session_id')
                    return data
                else:
                    raise Exception(f"Failed to start conversation: {response.status}")
    
    async def continue_conversation(self, user_message: str) -> Dict[str, Any]:
        """Continue the conversation with user input."""
        if not self.session_id:
            raise Exception("No active session. Please start a conversation first.")
        
        payload = {
            "session_id": self.session_id,
            "user_message": user_message
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/tax-service/continue",
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to continue conversation: {response.status}")
    
    async def get_conversation_state(self) -> Dict[str, Any]:
        """Get current conversation state."""
        if not self.session_id:
            raise Exception("No active session.")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/v1/tax-service/state/{self.session_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get conversation state: {response.status}")
    
    async def list_available_w2s(self) -> list:
        """List available W2 documents."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/v1/tax-service/w2s") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to list W2s: {response.status}")


async def test_api_conversation_flow():
    """Test the complete API conversation flow."""
    
    print("🌐 Testing Tax Conversation API Integration")
    print("=" * 50)
    
    try:
        # Initialize client
        client = TaxConversationAPIClient()
        
        # Step 1: Start conversation
        print("\n1. Starting conversation...")
        start_response = await client.start_conversation()
        print(f"   Session ID: {start_response['session_id']}")
        print(f"   Initial Message: {start_response['message'][:100]}...")
        print(f"   Available W2s: {len(start_response.get('available_w2s', []))}")
        
        # Step 2: User says they're single
        print("\n2. User responds: 'I'm single'")
        response1 = await client.continue_conversation("I'm single")
        print(f"   Agent Response: {response1['agent_response'][:150]}...")
        
        # Step 3: User says no dependents
        print("\n3. User responds: 'I don't have any dependents'")
        response2 = await client.continue_conversation("I don't have any dependents")
        print(f"   Agent Response: {response2['agent_response'][:150]}...")
        
        # Step 4: User provides income info
        print("\n4. User provides income: 'I had wages of $75,000 and federal withholding of $11,000'")
        response3 = await client.continue_conversation(
            "I had wages of $75,000 and federal withholding of $11,000 this year. Please use the manage_state_tool to set wages to 75000 and withholding to 11000."
        )
        print(f"   Agent Response: {response3['agent_response'][:150]}...")
        
        # Step 5: Calculate taxes
        print("\n5. User requests calculation: 'Please calculate my taxes'")
        response4 = await client.continue_conversation(
            "Please calculate my taxes using the calc_1040_tool with filing_status 'Single', wages 75000, and withholding 11000."
        )
        print(f"   Agent Response: {response4['agent_response'][:200]}...")
        
        # Step 6: Fill form
        print("\n6. User requests form filling: 'Please fill out my 1040 form'")
        response5 = await client.continue_conversation(
            "Great! Please fill out my 1040 form using the fill_form_tool with the calculated information."
        )
        print(f"   Agent Response: {response5['agent_response'][:150]}...")
        
        # Step 7: Get final state
        print("\n7. Getting final conversation state...")
        final_state = await client.get_conversation_state()
        state_data = final_state['state']
        
        if 'tax_calculation' in state_data:
            calc = state_data['tax_calculation']
            print(f"   💰 AGI: ${calc.get('agi', 0):,.2f}")
            print(f"   💸 Taxable Income: ${calc.get('taxable_income', 0):,.2f}")
            print(f"   🧾 Tax Liability: ${calc.get('tax', 0):,.2f}")
            refund_or_due = calc.get('refund_or_due', 0)
            if refund_or_due >= 0:
                print(f"   🎉 Refund: ${refund_or_due:,.2f}")
            else:
                print(f"   💳 Amount Due: ${abs(refund_or_due):,.2f}")
        
        print("\n✅ API conversation flow completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error in API conversation flow: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_individual_endpoints():
    """Test individual API endpoints."""
    
    print("\n🔧 Testing Individual API Endpoints")
    print("=" * 40)
    
    try:
        client = TaxConversationAPIClient()
        
        # Test W2 listing
        print("\n1. Testing W2 listing endpoint...")
        w2s = await client.list_available_w2s()
        print(f"   Found {len(w2s)} W2 documents")
        
        # Test conversation start
        print("\n2. Testing conversation start endpoint...")
        start_data = await client.start_conversation()
        print(f"   Session created: {start_data['session_id']}")
        
        # Test state retrieval
        print("\n3. Testing state retrieval endpoint...")
        state_data = await client.get_conversation_state()
        print(f"   State keys: {len(state_data['state'])}")
        
        print("\n✅ Individual endpoint tests completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing individual endpoints: {str(e)}")
        return False


async def main():
    """Main test function."""
    
    print("🚀 Starting API Integration Tests")
    print("Make sure the backend server is running on http://localhost:8000")
    
    # Wait a moment for server to be ready
    await asyncio.sleep(2)
    
    # Test individual endpoints
    endpoints_success = await test_individual_endpoints()
    
    # Test full conversation flow
    conversation_success = await test_api_conversation_flow()
    
    if endpoints_success and conversation_success:
        print("\n🎉 All API tests passed!")
        print("\n📋 Frontend Integration Guide:")
        print("  1. Use POST /api/v1/tax-service/start to begin")
        print("  2. Use POST /api/v1/tax-service/continue for each user message")
        print("  3. Use GET /api/v1/tax-service/state/{session_id} to check progress")
        print("  4. Use GET /api/v1/tax-service/w2s to list available W2s")
        print("\n🚀 Ready for frontend implementation!")
    else:
        print("\n❌ Some API tests failed. Check server status and try again.")


if __name__ == "__main__":
    asyncio.run(main())
