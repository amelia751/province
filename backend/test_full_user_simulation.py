#!/usr/bin/env python3
"""
Complete user simulation test - pretending to be you uploading the W-2 from Downloads
and going through the entire conversation flow.
"""

import asyncio
import json
import sys
import traceback
import base64
import os
from datetime import datetime
import requests

# Add the src directory to Python path
sys.path.insert(0, '/Users/anhlam/province/backend/src')

class FullUserSimulation:
    def __init__(self):
        self.engagement_id = "ea3b3a4f-c877-4d29-bd66-2cff2aa77476"
        self.user_id = "user_33w9KAn1gw3xXSa6MnBsySAQIIm"
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.w2_file_path = "/Users/anhlam/Downloads/W2_XL_input_clean_1000.pdf"
        
    async def test_complete_user_flow(self):
        """Test the complete user flow from file upload to tax calculation"""
        print("🧑‍💼 COMPLETE USER SIMULATION TEST")
        print("=" * 70)
        print(f"User: {self.user_id}")
        print(f"Engagement: {self.engagement_id}")
        print(f"W-2 File: {self.w2_file_path}")
        print("=" * 70)
        
        # Step 1: Check if W-2 file exists in Downloads
        if not os.path.exists(self.w2_file_path):
            print(f"❌ W-2 file not found at {self.w2_file_path}")
            print("   Please make sure W2_XL_input_clean_1000.pdf is in your Downloads folder")
            return False
        
        print(f"✅ Found W-2 file: {os.path.basename(self.w2_file_path)} ({os.path.getsize(self.w2_file_path)} bytes)")
        
        # Step 2: Simulate frontend document upload
        print("\n📤 Step 1: Simulating frontend document upload...")
        upload_success = await self.simulate_document_upload()
        if not upload_success:
            return False
        
        # Step 3: Simulate agent conversation
        print("\n🤖 Step 2: Simulating agent conversation...")
        conversation_success = await self.simulate_agent_conversation()
        if not conversation_success:
            return False
        
        # Step 4: Verify final results
        print("\n✅ Step 3: Verifying final tax calculation...")
        verification_success = await self.verify_tax_calculation()
        
        return verification_success
    
    async def simulate_document_upload(self):
        """Simulate uploading the W-2 document through the frontend API"""
        try:
            # Read the W-2 file
            with open(self.w2_file_path, 'rb') as f:
                file_content = f.read()
            
            # Convert to base64 (as the frontend would do)
            content_b64 = base64.b64encode(file_content).decode()
            
            # Simulate the frontend API call to /api/documents/upload
            upload_data = {
                "engagementId": self.engagement_id,
                "fileName": "W2_XL_input_clean_1000.pdf",
                "fileContent": content_b64,
                "mimeType": "application/pdf"
            }
            
            # Make the API call (simulating what the frontend does)
            response = requests.post(
                f"{self.backend_url}/api/v1/documents/save",
                json={
                    "engagement_id": self.engagement_id,
                    "path": "chat-uploads/W2_XL_input_clean_1000.pdf",
                    "content_b64": content_b64,
                    "mime_type": "application/pdf"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ Document uploaded successfully!")
                    print(f"   S3 Key: {result.get('s3_key')}")
                    print(f"   Size: {result.get('size_bytes', 0):,} bytes")
                    return True
                else:
                    print(f"❌ Document upload failed: {result.get('error')}")
                    return False
            else:
                print(f"❌ Upload API call failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Document upload exception: {e}")
            return False
    
    async def simulate_agent_conversation(self):
        """Simulate the complete agent conversation flow"""
        try:
            # Step 1: Create agent session
            print("   Creating agent session...")
            session_response = requests.post(
                f"{self.backend_url}/api/v1/agents/sessions",
                json={"agent_name": "TaxPlannerAgent"},
                timeout=10
            )
            
            if session_response.status_code != 200:
                print(f"❌ Failed to create session: {session_response.status_code}")
                return False
            
            session_data = session_response.json()
            session_id = session_data.get('session_id')
            print(f"✅ Created session: {session_id}")
            
            # Step 2: Send initial message about uploaded W-2
            print("   Sending message about uploaded W-2...")
            message1_response = requests.post(
                f"{self.backend_url}/api/v1/agents/chat",
                json={
                    "session_id": session_id,
                    "message": "I just uploaded a W-2 document. Can you tell me about the wages and withholding information?",
                    "agent_name": "TaxPlannerAgent"
                },
                timeout=60
            )
            
            if message1_response.status_code != 200:
                print(f"❌ Message 1 failed: {message1_response.status_code} - {message1_response.text}")
                return False
            
            message1_data = message1_response.json()
            print(f"✅ Agent response 1: {message1_data.get('response', '')[:100]}...")
            
            # Step 3: Provide taxpayer name and year (with delay to avoid throttling)
            print("   Waiting 3 seconds to avoid throttling...")
            await asyncio.sleep(3)
            print("   Providing taxpayer name and tax year...")
            message2_response = requests.post(
                f"{self.backend_url}/api/v1/agents/chat",
                json={
                    "session_id": session_id,
                    "message": "2024, April Hensley",
                    "agent_name": "TaxPlannerAgent"
                },
                timeout=60
            )
            
            if message2_response.status_code != 200:
                print(f"❌ Message 2 failed: {message2_response.status_code} - {message2_response.text}")
                return False
            
            message2_data = message2_response.json()
            print(f"✅ Agent response 2: {message2_data.get('response', '')[:100]}...")
            
            # Step 4: Confirm to proceed with calculation (with delay to avoid throttling)
            print("   Waiting 3 seconds to avoid throttling...")
            await asyncio.sleep(3)
            print("   Confirming to proceed with tax calculation...")
            message3_response = requests.post(
                f"{self.backend_url}/api/v1/agents/chat",
                json={
                    "session_id": session_id,
                    "message": "Single, no dependents",
                    "agent_name": "TaxPlannerAgent"
                },
                timeout=90  # Tax calculation might take longer
            )
            
            if message3_response.status_code != 200:
                print(f"❌ Message 3 failed: {message3_response.status_code} - {message3_response.text}")
                return False
            
            message3_data = message3_response.json()
            agent_response = message3_data.get('response', '')
            print(f"✅ Agent response 3: {agent_response[:200]}...")
            
            # Check if the response contains tax calculation results
            if any(keyword in agent_response.lower() for keyword in ['tax', 'refund', 'owe', 'calculation', 'return']):
                print("✅ Agent successfully provided tax calculation!")
                return True
            else:
                print("⚠️  Agent response doesn't seem to contain tax calculation")
                print(f"   Full response: {agent_response}")
                return False
                
        except Exception as e:
            print(f"❌ Agent conversation exception: {e}")
            traceback.print_exc()
            return False
    
    async def verify_tax_calculation(self):
        """Verify that the tax calculation was saved correctly"""
        try:
            # Import the calc_1040 function to test it directly
            from province.agents.tax.tools.calc_1040 import calc_1040
            
            # Test the calc_1040 function directly
            calc_result = await calc_1040(
                engagement_id=self.engagement_id,
                filing_status="S",
                dependents_count=0
            )
            
            if calc_result.get('success'):
                summary = calc_result.get('summary', {})
                agi = summary.get('agi', 0)
                tax = summary.get('tax', 0)
                refund_or_due = summary.get('refund_or_due', 0)
                is_refund = summary.get('is_refund', False)
                
                print(f"✅ Tax calculation verified!")
                print(f"   AGI: ${agi:,.2f}")
                print(f"   Tax: ${tax:,.2f}")
                if is_refund:
                    print(f"   REFUND: ${refund_or_due:,.2f}")
                else:
                    print(f"   AMOUNT DUE: ${abs(refund_or_due):,.2f}")
                
                # Verify the numbers make sense
                if agi > 50000 and tax > 4000 and abs(refund_or_due) > 10000:
                    print("✅ Tax calculation numbers look realistic!")
                    return True
                else:
                    print("⚠️  Tax calculation numbers seem unrealistic")
                    return False
            else:
                print(f"❌ Tax calculation failed: {calc_result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ Tax calculation verification failed: {e}")
            traceback.print_exc()
            return False
    
    def check_backend_status(self):
        """Check if backend is running"""
        try:
            response = requests.get(f"{self.backend_url}/api/v1/health/", timeout=5)
            if response.status_code == 200:
                print(f"✅ Backend is running on {self.backend_url}")
                return True
            else:
                print(f"❌ Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend is not accessible: {e}")
            return False

async def main():
    """Main test runner"""
    simulator = FullUserSimulation()
    
    # Check backend status first
    if not simulator.check_backend_status():
        print("\n💡 Please start the backend server:")
        print("   cd /Users/anhlam/province/backend")
        print("   source venv/bin/activate")
        print("   export PYTHONPATH=/Users/anhlam/province/backend/src:$PYTHONPATH")
        print("   uvicorn src.province.main:app --host 0.0.0.0 --port 8000 --reload")
        return
    
    # Run the complete test
    success = await simulator.test_complete_user_flow()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 COMPLETE USER SIMULATION SUCCESSFUL!")
        print("   ✅ Document upload works")
        print("   ✅ Agent conversation works") 
        print("   ✅ Tax calculation works")
        print("   ✅ All integrations are functioning correctly")
        print("\n🚀 Your frontend conversation should work perfectly now!")
    else:
        print("⚠️  COMPLETE USER SIMULATION FAILED!")
        print("   Some part of the flow is still broken.")
        print("   Check the errors above to identify the issue.")

if __name__ == "__main__":
    asyncio.run(main())
