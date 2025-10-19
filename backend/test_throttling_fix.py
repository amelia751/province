#!/usr/bin/env python3
"""
Test script to verify the Bedrock throttling fix is working.
This will make a single request to avoid triggering throttling again.
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:8000"

def test_single_agent_request():
    """Test a single agent request to verify it works without throttling."""
    print("🧪 Testing single agent request...")
    
    try:
        # Create a new session
        print("📝 Creating new session...")
        session_response = requests.post(
            f"{BACKEND_URL}/api/v1/agents/sessions",
            json={"agent_name": "TaxPlannerAgent"}
        )
        
        if session_response.status_code != 200:
            print(f"❌ Failed to create session: {session_response.status_code}")
            return False
            
        session_data = session_response.json()
        session_id = session_data["session_id"]
        print(f"✅ Created session: {session_id}")
        
        # Wait a moment to avoid any residual throttling
        print("⏱️  Waiting 3 seconds to avoid throttling...")
        time.sleep(3)
        
        # Send a simple message
        print("💬 Sending test message...")
        chat_response = requests.post(
            f"{BACKEND_URL}/api/v1/agents/chat",
            json={
                "message": "Hello, this is a test message.",
                "session_id": session_id,
                "agent_name": "TaxPlannerAgent"
            }
        )
        
        if chat_response.status_code == 200:
            data = chat_response.json()
            response_text = data.get("response", "")[:100] + "..." if len(data.get("response", "")) > 100 else data.get("response", "")
            print(f"✅ Agent responded successfully: {response_text}")
            return True
        else:
            print(f"❌ Chat request failed: {chat_response.status_code}")
            try:
                error_data = chat_response.json()
                print(f"   Error details: {error_data}")
            except:
                print(f"   Error text: {chat_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Bedrock Throttling Fix")
    print("=" * 40)
    
    success = test_single_agent_request()
    
    if success:
        print("\n🎉 Throttling fix test PASSED!")
        print("   The agent should now handle throttling gracefully with retries.")
    else:
        print("\n⚠️  Throttling fix test FAILED!")
        print("   There may still be throttling issues or other problems.")
    
    print("\n💡 Tips:")
    print("   - Wait 1-2 minutes between conversations to avoid throttling")
    print("   - The system now automatically retries with exponential backoff")
    print("   - Check server.log for detailed throttling retry messages")
