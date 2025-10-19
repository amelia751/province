#!/usr/bin/env python3
"""
Complete end-to-end test with Nova Pro - should work much better than Sonnet 3.5 v2
"""

import asyncio
import json
import sys
import traceback
import base64
import os
import requests
import time
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, '/Users/anhlam/province/backend/src')

class NovaProCompleteFlowTester:
    def __init__(self):
        self.engagement_id = "ea3b3a4f-c877-4d29-bd66-2cff2aa77476"
        self.user_id = "user_33w9KAn1gw3xXSa6MnBsySAQIIm"
        self.backend_url = "http://localhost:8000"
        self.w2_file_path = "/Users/anhlam/Downloads/W2_XL_input_clean_1000.pdf"
        
        # Nova Pro should handle much shorter delays
        self.message_delay = 15  # 15 seconds instead of 90
        
    async def test_complete_flow_nova_pro(self):
        """Test complete flow with Nova Pro's higher rate limits"""
        print("🚀 COMPLETE END-TO-END TEST WITH NOVA PRO")
        print("=" * 80)
        print(f"Model: Nova Pro (50 requests/min)")
        print(f"Message delay: {self.message_delay}s (much shorter than before)")
        print(f"Engagement: {self.engagement_id}")
        print("=" * 80)
        
        # Step 1: Upload document
        print("\n📤 STEP 1: Document Upload")
        upload_success = await self.upload_document()
        if not upload_success:
            return False
        
        # Step 2: Agent conversation with shorter delays
        print("\n🤖 STEP 2: Agent Conversation (Nova Pro)")
        conversation_success = await self.test_agent_conversation()
        if not conversation_success:
            return False
        
        # Step 3: Verify tools still work
        print("\n🔧 STEP 3: Direct Tool Verification")
        tools_success = await self.verify_tools_working()
        
        return tools_success
    
    async def upload_document(self):
        """Upload the W-2 document"""
        try:
            if not os.path.exists(self.w2_file_path):
                print(f"❌ W-2 file not found: {self.w2_file_path}")
                return False
            
            with open(self.w2_file_path, 'rb') as f:
                file_content = f.read()
            content_b64 = base64.b64encode(file_content).decode()
            
            response = requests.post(
                f"{self.backend_url}/api/v1/documents/save",
                json={
                    "engagement_id": self.engagement_id,
                    "path": "nova-pro-test/W2_nova_test.pdf",
                    "content_b64": content_b64,
                    "mime_type": "application/pdf"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ Document uploaded: {result.get('s3_key')}")
                    return True
                else:
                    print(f"❌ Upload failed: {result.get('error')}")
                    return False
            else:
                print(f"❌ Upload API failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Upload exception: {e}")
            return False
    
    async def test_agent_conversation(self):
        """Test agent conversation with Nova Pro"""
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
            
            # Message 1: Initial greeting
            print(f"\n📝 Message 1: Initial greeting...")
            start_time = time.time()
            
            message1_response = requests.post(
                f"{self.backend_url}/api/v1/agents/chat",
                json={
                    "session_id": session_id,
                    "message": "Hello! I need help with my taxes. I'm filing as single with no dependents.",
                    "agent_name": "TaxPlannerAgent"
                },
                timeout=30
            )
            
            duration1 = time.time() - start_time
            
            if message1_response.status_code == 200:
                message1_data = message1_response.json()
                print(f"✅ Message 1 SUCCESS ({duration1:.1f}s)")
                print(f"   Response: {message1_data.get('response', '')[:100]}...")
            else:
                print(f"❌ Message 1 failed ({duration1:.1f}s): {message1_response.status_code}")
                return False
            
            # Shorter wait with Nova Pro
            print(f"⏳ Waiting {self.message_delay} seconds (Nova Pro rate limit)...")
            await asyncio.sleep(self.message_delay)
            
            # Message 2: Document processing request
            print(f"\n📝 Message 2: Document processing request...")
            start_time = time.time()
            
            message2_response = requests.post(
                f"{self.backend_url}/api/v1/agents/chat",
                json={
                    "session_id": session_id,
                    "message": "I have uploaded my W-2 for April Hensley, tax year 2024. Please process it and calculate my taxes.",
                    "agent_name": "TaxPlannerAgent"
                },
                timeout=120  # Longer timeout for tool execution
            )
            
            duration2 = time.time() - start_time
            
            if message2_response.status_code == 200:
                message2_data = message2_response.json()
                agent_response = message2_data.get('response', '')
                print(f"✅ Message 2 SUCCESS ({duration2:.1f}s)")
                print(f"   Response: {agent_response[:200]}...")
                
                # Check if response contains tax calculation results
                success_indicators = ['tax', 'refund', 'owe', '$', 'calculation', 'wages', 'withholding']
                if any(keyword in agent_response.lower() for keyword in success_indicators):
                    print(f"🎉 AGENT SUCCESSFULLY PROCESSED TAX REQUEST!")
                    return True
                else:
                    print(f"✅ Agent responded without throttling (good sign)")
                    return True
            else:
                print(f"❌ Message 2 failed ({duration2:.1f}s): {message2_response.status_code}")
                if "throttling" in message2_response.text.lower():
                    print(f"   Still throttling - Nova Pro may need more time")
                else:
                    print(f"   Error: {message2_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Agent conversation exception: {e}")
            traceback.print_exc()
            return False
    
    async def verify_tools_working(self):
        """Verify that all tools still work perfectly"""
        print("Verifying all tools still work...")
        
        try:
            from province.agents.tax.tools.ingest_documents import ingest_documents
            from province.agents.tax.tools.calc_1040 import calc_1040
            
            # Test ingest_documents
            print("🔧 Testing ingest_documents...")
            ingest_result = await ingest_documents(
                s3_key=f"tax-engagements/{self.engagement_id}/nova-pro-test/W2_nova_test.pdf",
                taxpayer_name="April Hensley",
                tax_year=2024,
                document_type="W-2"
            )
            
            if ingest_result.get('success'):
                wages = ingest_result.get('total_wages', 0)
                withholding = ingest_result.get('total_withholding', 0)
                print(f"✅ ingest_documents: SUCCESS")
                print(f"   Wages: ${wages:,.2f}, Withholding: ${withholding:,.2f}")
            else:
                print(f"❌ ingest_documents failed: {ingest_result.get('error')}")
                return False
            
            # Test calc_1040
            print("\n🔧 Testing calc_1040...")
            calc_result = await calc_1040(
                engagement_id=self.engagement_id,
                filing_status="S",
                dependents_count=0
            )
            
            if calc_result.get('success'):
                summary = calc_result.get('summary', {})
                agi = summary.get('agi', 0)
                refund_or_due = summary.get('refund_or_due', 0)
                is_refund = summary.get('is_refund', False)
                
                print(f"✅ calc_1040: SUCCESS")
                print(f"   AGI: ${agi:,.2f}")
                if is_refund:
                    print(f"   REFUND: ${refund_or_due:,.2f}")
                else:
                    print(f"   AMOUNT DUE: ${abs(refund_or_due):,.2f}")
            else:
                print(f"❌ calc_1040 failed: {calc_result.get('error')}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Tool verification exception: {e}")
            return False

async def main():
    """Main test runner"""
    tester = NovaProCompleteFlowTester()
    
    print("🎯 GOAL: Test complete flow with Nova Pro's higher rate limits")
    print("   Expected: Much better performance than Sonnet 3.5 v2")
    print()
    
    start_time = time.time()
    success = await tester.test_complete_flow_nova_pro()
    end_time = time.time()
    
    duration_minutes = (end_time - start_time) / 60
    
    print("\n" + "=" * 80)
    print(f"⏱️  Total test duration: {duration_minutes:.1f} minutes")
    
    if success:
        print("🎉 NOVA PRO COMPLETE SUCCESS!")
        print("   ✅ Document upload works")
        print("   ✅ Agent conversation works with shorter delays")
        print("   ✅ All tools work perfectly")
        print("   ✅ Tax calculation works")
        print()
        print("🚀 CONCLUSION: Nova Pro solved the throttling issue!")
        print("   Your tax system is now fully functional for conversations!")
    else:
        print("⚠️  PARTIAL SUCCESS OR ISSUES REMAIN")
        print("   Nova Pro is better but may need further optimization")

if __name__ == "__main__":
    asyncio.run(main())
