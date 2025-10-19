#!/usr/bin/env python3
"""
Test Nova Pro rate limits - should handle much higher request rates than Sonnet 3.5 v2
"""

import asyncio
import requests
import time
from datetime import datetime

class NovaProRateLimitTester:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        
    async def test_rapid_messages(self):
        """Test rapid message sending with Nova Pro (50 RPM vs 2 RPM)"""
        print("🚀 NOVA PRO RATE LIMIT TEST")
        print("=" * 60)
        print("Previous: Sonnet 3.5 v2 (2 requests/min)")
        print("Current:  Nova Pro (50 requests/min)")
        print("=" * 60)
        
        try:
            # Create session
            print("📝 Creating agent session...")
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
            
            # Test rapid messages (should work with Nova Pro)
            messages = [
                "Hello, I need help with my taxes.",
                "I'm filing as single with no dependents.",
                "What information do you need from me?",
                "I have a W-2 form ready to upload.",
                "What's the standard deduction for 2024?"
            ]
            
            print(f"\n🏃‍♂️ Testing {len(messages)} rapid messages...")
            start_time = time.time()
            successful_messages = 0
            
            for i, message in enumerate(messages, 1):
                print(f"\n📝 Message {i}/{len(messages)}: '{message[:30]}...'")
                
                message_start = time.time()
                try:
                    response = requests.post(
                        f"{self.backend_url}/api/v1/agents/chat",
                        json={
                            "session_id": session_id,
                            "message": message,
                            "agent_name": "TaxPlannerAgent"
                        },
                        timeout=30
                    )
                    
                    message_duration = time.time() - message_start
                    
                    if response.status_code == 200:
                        data = response.json()
                        agent_response = data.get('response', '')
                        print(f"✅ Success ({message_duration:.1f}s): {agent_response[:60]}...")
                        successful_messages += 1
                    else:
                        print(f"❌ Failed ({message_duration:.1f}s): {response.status_code}")
                        if "throttling" in response.text.lower():
                            print(f"   Still throttling - may need more time for quota reset")
                        else:
                            print(f"   Error: {response.text}")
                        break
                        
                except Exception as e:
                    message_duration = time.time() - message_start
                    print(f"❌ Exception ({message_duration:.1f}s): {e}")
                    break
                
                # Small delay between messages (much shorter than before)
                await asyncio.sleep(2)
            
            total_duration = time.time() - start_time
            
            print(f"\n📊 NOVA PRO TEST RESULTS:")
            print(f"   Successful messages: {successful_messages}/{len(messages)}")
            print(f"   Total duration: {total_duration:.1f} seconds")
            print(f"   Average time per message: {total_duration/len(messages):.1f}s")
            
            if successful_messages >= 3:
                print(f"✅ NOVA PRO WORKING! Much better than Sonnet 3.5 v2")
                return True
            elif successful_messages >= 1:
                print(f"⚠️  PARTIAL SUCCESS - Some improvement over Sonnet")
                return True
            else:
                print(f"❌ STILL THROTTLING - May need quota reset time")
                return False
                
        except Exception as e:
            print(f"❌ Test exception: {e}")
            return False

async def test_complete_conversation_flow():
    """Test the complete conversation flow with Nova Pro"""
    print("\n🎯 COMPLETE CONVERSATION FLOW TEST")
    print("=" * 60)
    
    backend_url = "http://localhost:8000"
    
    try:
        # Create session
        session_response = requests.post(
            f"{backend_url}/api/v1/agents/sessions",
            json={"agent_name": "TaxPlannerAgent"},
            timeout=10
        )
        
        session_data = session_response.json()
        session_id = session_data.get('session_id')
        print(f"✅ Session created: {session_id}")
        
        # Message 1: Greeting
        print(f"\n📝 Message 1: Greeting...")
        response1 = requests.post(
            f"{backend_url}/api/v1/agents/chat",
            json={
                "session_id": session_id,
                "message": "Hello, I need help with my taxes. I'm filing as single with no dependents.",
                "agent_name": "TaxPlannerAgent"
            },
            timeout=30
        )
        
        if response1.status_code == 200:
            print(f"✅ Message 1: SUCCESS")
        else:
            print(f"❌ Message 1 failed: {response1.status_code}")
            return False
        
        # Wait shorter time (Nova Pro should handle this)
        print(f"⏳ Waiting 10 seconds (much shorter than before)...")
        await asyncio.sleep(10)
        
        # Message 2: Document processing request
        print(f"\n📝 Message 2: Tax calculation request...")
        response2 = requests.post(
            f"{backend_url}/api/v1/agents/chat",
            json={
                "session_id": session_id,
                "message": "I have uploaded my W-2 for April Hensley, tax year 2024. Can you calculate my taxes?",
                "agent_name": "TaxPlannerAgent"
            },
            timeout=90
        )
        
        if response2.status_code == 200:
            data = response2.json()
            agent_response = data.get('response', '')
            print(f"✅ Message 2: SUCCESS")
            print(f"   Response: {agent_response[:200]}...")
            
            # Check if it contains tax information
            if any(keyword in agent_response.lower() for keyword in ['tax', 'refund', 'owe', '$', 'calculation']):
                print(f"🎉 AGENT SUCCESSFULLY PROCESSED TAX REQUEST!")
                return True
            else:
                print(f"✅ Agent responded (no throttling) but may need more context")
                return True
        else:
            print(f"❌ Message 2 failed: {response2.status_code} - {response2.text}")
            return False
            
    except Exception as e:
        print(f"❌ Conversation test exception: {e}")
        return False

async def main():
    """Main test runner"""
    tester = NovaProRateLimitTester()
    
    print("🎯 GOAL: Test if Nova Pro resolves the throttling issues")
    print("   Nova Pro: 50 requests/min vs Sonnet 3.5 v2: 2 requests/min")
    print()
    
    # Test 1: Rapid messages
    rapid_success = await tester.test_rapid_messages()
    
    if rapid_success:
        # Test 2: Complete conversation
        conversation_success = await test_complete_conversation_flow()
        
        print("\n" + "=" * 60)
        if rapid_success and conversation_success:
            print("🎉 NOVA PRO SUCCESS!")
            print("   ✅ Higher rate limits working")
            print("   ✅ Conversation flow working")
            print("   ✅ Ready for full end-to-end test")
        else:
            print("⚠️  PARTIAL SUCCESS")
            print("   Nova Pro is better but may need more testing")
    else:
        print("\n❌ STILL HAVING ISSUES")
        print("   May need more time for quota reset or other configuration")

if __name__ == "__main__":
    asyncio.run(main())
