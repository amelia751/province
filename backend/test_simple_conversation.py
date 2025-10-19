#!/usr/bin/env python3
"""
Test a simple conversation flow that doesn't trigger complex tool orchestration
to see if the throttling is related to tool calling complexity.
"""

import asyncio
import requests
import time

class SimpleConversationTester:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        
    async def test_simple_conversation(self):
        """Test a simple conversation without complex tool calls"""
        print("🗣️  SIMPLE CONVERSATION TEST")
        print("=" * 50)
        
        try:
            # Create session
            print("📝 Creating session...")
            session_response = requests.post(
                f"{self.backend_url}/api/v1/agents/sessions",
                json={"agent_name": "TaxPlannerAgent"},
                timeout=10
            )
            
            if session_response.status_code != 200:
                print(f"❌ Session creation failed: {session_response.status_code}")
                return False
            
            session_data = session_response.json()
            session_id = session_data.get('session_id')
            print(f"✅ Session created: {session_id}")
            
            # Test simple messages that shouldn't trigger tools
            simple_messages = [
                "Hello, I need help with my taxes.",
                "What information do you need from me?",
                "I'm filing as single with no dependents.",
                "What's the standard deduction for 2024?"
            ]
            
            for i, message in enumerate(simple_messages, 1):
                print(f"\n📝 Message {i}: '{message}'")
                
                start_time = time.time()
                response = requests.post(
                    f"{self.backend_url}/api/v1/agents/chat",
                    json={
                        "session_id": session_id,
                        "message": message,
                        "agent_name": "TaxPlannerAgent"
                    },
                    timeout=30
                )
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    agent_response = data.get('response', '')
                    print(f"✅ Response ({duration:.1f}s): {agent_response[:100]}...")
                else:
                    print(f"❌ Failed ({duration:.1f}s): {response.status_code} - {response.text}")
                    return False
                
                # Small delay between messages
                await asyncio.sleep(2)
            
            print(f"\n✅ Simple conversation completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Simple conversation failed: {e}")
            return False
    
    async def test_document_mention(self):
        """Test mentioning documents without actually processing them"""
        print("\n🗣️  DOCUMENT MENTION TEST")
        print("=" * 50)
        
        try:
            # Create new session
            session_response = requests.post(
                f"{self.backend_url}/api/v1/agents/sessions",
                json={"agent_name": "TaxPlannerAgent"},
                timeout=10
            )
            
            session_data = session_response.json()
            session_id = session_data.get('session_id')
            print(f"✅ Session created: {session_id}")
            
            # Test mentioning documents without triggering processing
            print(f"\n📝 Message: 'I have a W-2 form. What should I do with it?'")
            
            start_time = time.time()
            response = requests.post(
                f"{self.backend_url}/api/v1/agents/chat",
                json={
                    "session_id": session_id,
                    "message": "I have a W-2 form. What should I do with it?",
                    "agent_name": "TaxPlannerAgent"
                },
                timeout=30
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                agent_response = data.get('response', '')
                print(f"✅ Response ({duration:.1f}s): {agent_response[:200]}...")
                return True
            else:
                print(f"❌ Failed ({duration:.1f}s): {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Document mention test failed: {e}")
            return False

async def main():
    """Main test runner"""
    tester = SimpleConversationTester()
    
    print("🎯 GOAL: Test if throttling is related to tool complexity")
    print("   Test 1: Simple conversation (no tools)")
    print("   Test 2: Mention documents (might trigger tools)")
    print()
    
    # Test simple conversation
    simple_success = await tester.test_simple_conversation()
    
    if simple_success:
        # Test document mention
        doc_success = await tester.test_document_mention()
        
        print("\n" + "=" * 50)
        if simple_success and doc_success:
            print("✅ BOTH TESTS PASSED")
            print("   Throttling might be intermittent or load-related")
        elif simple_success and not doc_success:
            print("⚠️  DOCUMENT MENTION TRIGGERS THROTTLING")
            print("   The issue is related to tool orchestration")
        else:
            print("❌ GENERAL THROTTLING ISSUE")
    else:
        print("\n❌ BASIC CONVERSATION FAILING")
        print("   Bedrock agent has general throttling issues")

if __name__ == "__main__":
    asyncio.run(main())
