#!/usr/bin/env python3
"""
Test the actual agent tool calling flow to identify what's causing the throttling.
The issue is likely in how tools are being called, not the tools themselves.
"""

import asyncio
import json
import sys
import traceback
import requests
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, '/Users/anhlam/province/backend/src')

class AgentToolFlowTester:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.engagement_id = "ea3b3a4f-c877-4d29-bd66-2cff2aa77476"
        
    async def test_agent_tool_calling(self):
        """Test what happens during agent tool calling"""
        print("🔍 AGENT TOOL CALLING INVESTIGATION")
        print("=" * 60)
        
        # Step 1: Create a fresh session
        print("📝 Step 1: Creating fresh agent session...")
        try:
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
            print(f"✅ Created session: {session_id}")
            
        except Exception as e:
            print(f"❌ Session creation exception: {e}")
            return False
        
        # Step 2: Send a simple message first (should work)
        print("\n📝 Step 2: Testing simple message (no tools)...")
        try:
            simple_response = requests.post(
                f"{self.backend_url}/api/v1/agents/chat",
                json={
                    "session_id": session_id,
                    "message": "Hello, I need help with my taxes.",
                    "agent_name": "TaxPlannerAgent"
                },
                timeout=30
            )
            
            if simple_response.status_code == 200:
                simple_data = simple_response.json()
                print(f"✅ Simple message worked: {simple_data.get('response', '')[:100]}...")
            else:
                print(f"❌ Simple message failed: {simple_response.status_code} - {simple_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Simple message exception: {e}")
            return False
        
        # Step 3: Test message that might trigger tool calling
        print("\n📝 Step 3: Testing message that triggers tool calling...")
        try:
            print("   Sending: 'I uploaded a W-2 document for April Hensley, tax year 2024'")
            
            tool_response = requests.post(
                f"{self.backend_url}/api/v1/agents/chat",
                json={
                    "session_id": session_id,
                    "message": "I uploaded a W-2 document for April Hensley, tax year 2024. Can you process it?",
                    "agent_name": "TaxPlannerAgent"
                },
                timeout=60
            )
            
            print(f"   Response status: {tool_response.status_code}")
            
            if tool_response.status_code == 200:
                tool_data = tool_response.json()
                response_text = tool_data.get('response', '')
                print(f"✅ Tool message response: {response_text[:200]}...")
                
                # Check if it mentions any tool execution
                if any(keyword in response_text.lower() for keyword in ['process', 'analyze', 'extract', 'calculate']):
                    print("✅ Agent seems to be processing the request")
                else:
                    print("⚠️  Agent response doesn't indicate tool execution")
                
                return True
                
            elif tool_response.status_code == 500:
                error_text = tool_response.text
                print(f"❌ Tool message failed with 500 error:")
                print(f"   Error: {error_text}")
                
                # Parse the error to understand what's happening
                try:
                    error_data = json.loads(error_text)
                    detail = error_data.get('detail', '')
                    
                    if 'throttlingException' in detail:
                        print("🔍 THROTTLING DETECTED - Let's investigate why...")
                        await self.investigate_throttling_cause(session_id)
                    elif 'tool' in detail.lower():
                        print("🔍 TOOL ERROR DETECTED - Let's investigate...")
                        await self.investigate_tool_error(detail)
                    else:
                        print(f"🔍 OTHER ERROR: {detail}")
                        
                except json.JSONDecodeError:
                    print(f"🔍 RAW ERROR: {error_text}")
                
                return False
            else:
                print(f"❌ Unexpected status code: {tool_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Tool message exception: {e}")
            traceback.print_exc()
            return False
    
    async def investigate_throttling_cause(self, session_id):
        """Investigate what's causing the throttling"""
        print("\n🔍 INVESTIGATING THROTTLING CAUSE...")
        
        # Check if there are multiple rapid tool calls happening
        print("   Possible causes of throttling:")
        print("   1. Agent is making too many rapid Bedrock calls")
        print("   2. Tool is calling Bedrock multiple times in sequence")
        print("   3. Agent is retrying failed tool calls too quickly")
        print("   4. Multiple tools are being called simultaneously")
        
        # Let's check the backend logs for more details
        print("\n   Checking recent backend activity...")
        try:
            # Check agent stats
            stats_response = requests.get(f"{self.backend_url}/api/v1/agents/stats", timeout=5)
            if stats_response.status_code == 200:
                stats = stats_response.json()
                print(f"   Active sessions: {len(stats.get('active_sessions', []))}")
                print(f"   Recent activity: {stats.get('recent_activity', 'None')}")
        except:
            print("   Could not retrieve agent stats")
    
    async def investigate_tool_error(self, error_detail):
        """Investigate tool-specific errors"""
        print(f"\n🔍 INVESTIGATING TOOL ERROR: {error_detail}")
        
        # Test individual tools to see which one is failing
        print("   Testing individual tools...")
        
        try:
            from province.agents.tax.tools.ingest_documents import ingest_documents
            from province.agents.tax.tools.calc_1040 import calc_1040
            
            # Test ingest_documents with the uploaded file
            print("   Testing ingest_documents...")
            ingest_result = await ingest_documents(
                s3_key=f"tax-engagements/{self.engagement_id}/chat-uploads/W2_XL_input_clean_1000.pdf",
                taxpayer_name="April Hensley",
                tax_year=2024,
                document_type="W-2"
            )
            
            if ingest_result.get('success'):
                print("   ✅ ingest_documents works fine")
            else:
                print(f"   ❌ ingest_documents failed: {ingest_result.get('error')}")
            
            # Test calc_1040
            print("   Testing calc_1040...")
            calc_result = await calc_1040(
                engagement_id=self.engagement_id,
                filing_status="S",
                dependents_count=0
            )
            
            if calc_result.get('success'):
                print("   ✅ calc_1040 works fine")
            else:
                print(f"   ❌ calc_1040 failed: {calc_result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ Tool testing failed: {e}")
    
    async def test_bedrock_agent_directly(self):
        """Test the Bedrock agent client directly"""
        print("\n🔍 TESTING BEDROCK AGENT CLIENT DIRECTLY...")
        
        try:
            from province.agents.bedrock_agent_client import BedrockAgentClient
            
            client = BedrockAgentClient()
            
            # Test with a simple message
            response = client.invoke_agent(
                agent_id="YLNFZM0YEM",
                agent_alias_id="TSTALIASID",
                session_id="test-session-123",
                input_text="Hello, can you help me with taxes?",
                enable_trace=False
            )
            
            print(f"✅ Bedrock agent direct call worked: {response.response_text[:100]}...")
            return True
            
        except Exception as e:
            print(f"❌ Bedrock agent direct call failed: {e}")
            traceback.print_exc()
            return False

async def main():
    """Main test runner"""
    tester = AgentToolFlowTester()
    
    print("🎯 GOAL: Identify why agent conversation triggers throttling")
    print("   Hypothesis: It's not the tools themselves, but how they're called")
    print()
    
    # Test the agent tool calling flow
    success = await tester.test_agent_tool_calling()
    
    # Test Bedrock agent directly
    await tester.test_bedrock_agent_directly()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ AGENT TOOL FLOW WORKING")
        print("   The issue might be intermittent or load-related")
    else:
        print("❌ AGENT TOOL FLOW ISSUES IDENTIFIED")
        print("   Check the investigation results above")

if __name__ == "__main__":
    asyncio.run(main())
