#!/usr/bin/env python3
"""
Simulate what the agent actually does when processing a conversation.
This will help identify the exact tool call that's failing.
"""

import asyncio
import json
import sys
import traceback
from datetime import datetime
import os
import uuid

# Add the src directory to Python path
sys.path.insert(0, '/Users/anhlam/province/backend/src')

try:
    from province.agents.tax.tools.save_document import save_document
    from province.agents.tax.tools.ingest_documents import ingest_documents
    from province.agents.tax.tools.calc_1040 import calc_1040
    from province.core.config import get_settings
    import boto3
    import base64
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class AgentSimulator:
    def __init__(self):
        self.settings = get_settings()
        # Use the actual engagement ID from your conversation
        self.engagement_id = "ea3b3a4f-c877-4d29-bd66-2cff2aa77476"
        self.user_id = "user_33w9KAn1gw3xXSa6MnBsySAQIIm"
        
    async def simulate_agent_conversation(self):
        """Simulate the exact conversation flow that's failing"""
        print("🤖 SIMULATING AGENT CONVERSATION FLOW")
        print("=" * 60)
        print(f"Engagement ID: {self.engagement_id}")
        print(f"User ID: {self.user_id}")
        print("=" * 60)
        
        # The conversation flow based on your debug info:
        # 1. User uploads W-2 document
        # 2. Agent processes it
        # 3. User provides: "2024, April Hensley"
        # 4. Agent confirms tax year
        # 5. User says "Yes"
        # 6. Agent tries to calculate taxes -> FAILS HERE
        
        print("\n📝 Step 1: Check if W-2 document exists...")
        w2_exists = await self.check_w2_document_exists()
        
        if not w2_exists:
            print("⚠️  No W-2 document found. Let me ingest one...")
            await self.ingest_test_w2()
        
        print("\n📝 Step 2: Simulate agent trying to calculate 1040...")
        try:
            # This is what the agent tries to do when user says "Yes" to confirm tax year
            calc_result = await calc_1040(
                engagement_id=self.engagement_id,
                filing_status="S",  # Single
                dependents_count=0
            )
            
            if calc_result.get('success'):
                print(f"✅ Agent calculation succeeded!")
                print(f"   Tax owed: ${calc_result.get('tax_owed', 0):,.2f}")
                print(f"   Refund: ${calc_result.get('refund', 0):,.2f}")
                return True
            else:
                print(f"❌ Agent calculation failed: {calc_result.get('error')}")
                print("   This is likely what's causing the 'Internal Server Error'")
                return False
                
        except Exception as e:
            print(f"❌ Agent calculation exception: {e}")
            print(f"   Traceback: {traceback.format_exc()}")
            return False
    
    async def check_w2_document_exists(self):
        """Check if W-2 document exists for this engagement"""
        try:
            dynamodb = boto3.resource('dynamodb', region_name=self.settings.aws_region)
            table = dynamodb.Table(self.settings.tax_documents_table_name)
            
            # Check for any W-2 related documents
            response = table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('tenant_id#engagement_id').eq(f"{self.user_id}#{self.engagement_id}")
            )
            
            items = response.get('Items', [])
            print(f"   Found {len(items)} documents for this engagement")
            
            for item in items:
                doc_type = item.get('document_type', 'Unknown')
                doc_path = item.get('doc#path', 'Unknown')
                print(f"   - {doc_type}: {doc_path}")
            
            # Look for W-2 extracts specifically
            w2_extracts = [item for item in items if 'W2' in item.get('document_type', '')]
            return len(w2_extracts) > 0
            
        except Exception as e:
            print(f"   Error checking documents: {e}")
            return False
    
    async def ingest_test_w2(self):
        """Ingest a test W-2 to see what happens"""
        try:
            print("   Ingesting test W-2...")
            result = await ingest_documents(
                s3_key="datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_1000.pdf",
                taxpayer_name="April Hensley",
                tax_year=2024,
                document_type="W-2"
            )
            
            if result.get('success'):
                print(f"   ✅ W-2 ingested: ${result.get('total_wages', 0):,.2f} in wages")
            else:
                print(f"   ❌ W-2 ingest failed: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ W-2 ingest exception: {e}")
    
    async def debug_calc_1040_requirements(self):
        """Debug what calc_1040 is actually looking for"""
        print("\n🔍 DEBUGGING calc_1040 REQUIREMENTS")
        print("-" * 40)
        
        try:
            dynamodb = boto3.resource('dynamodb', region_name=self.settings.aws_region)
            table = dynamodb.Table(self.settings.tax_documents_table_name)
            
            # This is what calc_1040 is looking for:
            expected_key = {
                'tenant_id#engagement_id': f"{self.user_id}#{self.engagement_id}",
                'doc#path': 'doc#/Workpapers/W2_Extracts.json'
            }
            
            print(f"calc_1040 is looking for:")
            print(f"  Key: {expected_key}")
            
            response = table.get_item(Key=expected_key)
            
            if 'Item' in response:
                print("✅ Found the document calc_1040 needs!")
                item = response['Item']
                print(f"   S3 Key: {item.get('s3_key')}")
                print(f"   Document Type: {item.get('document_type')}")
            else:
                print("❌ calc_1040 cannot find the required document!")
                print("   This explains why the agent is failing.")
                
                # Show what documents actually exist
                print("\n📋 Documents that actually exist:")
                all_docs = table.scan(
                    FilterExpression=boto3.dynamodb.conditions.Attr('tenant_id#engagement_id').eq(f"{self.user_id}#{self.engagement_id}")
                )
                
                for item in all_docs.get('Items', []):
                    print(f"   - {item.get('doc#path')}: {item.get('document_type')}")
                
        except Exception as e:
            print(f"❌ Debug error: {e}")

async def main():
    """Main test runner"""
    simulator = AgentSimulator()
    
    # Run the simulation
    success = await simulator.simulate_agent_conversation()
    
    # Debug the requirements
    await simulator.debug_calc_1040_requirements()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 AGENT SIMULATION SUCCESSFUL!")
        print("   The agent conversation flow is working correctly.")
    else:
        print("⚠️  AGENT SIMULATION FAILED!")
        print("   This explains the 'Internal Server Error' in your conversation.")
        print("\n💡 LIKELY SOLUTION:")
        print("   The ingest_documents tool needs to save W-2 data in the format")
        print("   that calc_1040 expects: 'doc#/Workpapers/W2_Extracts.json'")

if __name__ == "__main__":
    asyncio.run(main())
