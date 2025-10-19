#!/usr/bin/env python3
"""
Test the actual conversation fix by simulating the exact flow that happens
when a user uploads a document through the chat interface.
"""

import asyncio
import json
import sys
import traceback
from datetime import datetime
import os
import uuid
import base64

# Add the src directory to Python path
sys.path.insert(0, '/Users/anhlam/province/backend/src')

try:
    from province.agents.tax.tools.save_document import save_document
    from province.agents.tax.tools.ingest_documents import ingest_documents
    from province.agents.tax.tools.calc_1040 import calc_1040
    from province.core.config import get_settings
    import boto3
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class ConversationFixTester:
    def __init__(self):
        self.settings = get_settings()
        # Use the actual engagement ID from your conversation
        self.engagement_id = "ea3b3a4f-c877-4d29-bd66-2cff2aa77476"
        self.user_id = "user_33w9KAn1gw3xXSa6MnBsySAQIIm"
        
    async def test_conversation_fix(self):
        """Test the complete conversation fix"""
        print("🔧 TESTING CONVERSATION FIX")
        print("=" * 60)
        print(f"Engagement ID: {self.engagement_id}")
        print(f"User ID: {self.user_id}")
        print("=" * 60)
        
        # Step 1: Simulate uploading a W-2 document through chat
        print("\n📝 Step 1: Uploading W-2 document through chat...")
        
        # Get the actual W-2 content from S3
        s3_client = boto3.client('s3', region_name=self.settings.aws_region)
        try:
            response = s3_client.get_object(
                Bucket=self.settings.documents_bucket_name,
                Key="datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_1000.pdf"
            )
            w2_content = response['Body'].read()
            content_b64 = base64.b64encode(w2_content).decode()
            
            # Save it as if uploaded through chat
            save_result = await save_document(
                engagement_id=self.engagement_id,
                path="chat-uploads/W2_XL_input_clean_1000.pdf",
                content_b64=content_b64,
                mime_type="application/pdf"
            )
            
            if save_result.get('success'):
                uploaded_s3_key = save_result.get('s3_key')
                print(f"✅ W-2 uploaded: {uploaded_s3_key}")
            else:
                print(f"❌ W-2 upload failed: {save_result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ W-2 upload exception: {e}")
            return False
        
        # Step 2: Process the uploaded W-2 (this should now save extract data for calc_1040)
        print("\n📝 Step 2: Processing uploaded W-2...")
        try:
            ingest_result = await ingest_documents(
                s3_key=uploaded_s3_key,  # Use the uploaded document
                taxpayer_name="April Hensley",
                tax_year=2024,
                document_type="W-2"
            )
            
            if ingest_result.get('success'):
                total_wages = ingest_result.get('total_wages', 0)
                print(f"✅ W-2 processed: ${total_wages:,.2f} in wages")
                print(f"   Extract data should now be saved for calc_1040")
            else:
                print(f"❌ W-2 processing failed: {ingest_result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ W-2 processing exception: {e}")
            return False
        
        # Step 3: Verify the extract data was saved correctly
        print("\n📝 Step 3: Verifying extract data for calc_1040...")
        try:
            dynamodb = boto3.resource('dynamodb', region_name=self.settings.aws_region)
            table = dynamodb.Table(self.settings.tax_documents_table_name)
            
            # Check if the extract data exists
            expected_key = {
                'tenant_id#engagement_id': f"{self.user_id}#{self.engagement_id}",
                'doc#path': 'doc#/Workpapers/W2_Extracts.json'
            }
            
            response = table.get_item(Key=expected_key)
            
            if 'Item' in response:
                print("✅ W-2 extract data found for calc_1040!")
                item = response['Item']
                print(f"   S3 Key: {item.get('s3_key')}")
                print(f"   Total Wages: ${item.get('total_wages', 0):,.2f}")
                print(f"   Total Withholding: ${item.get('total_withholding', 0):,.2f}")
            else:
                print("❌ W-2 extract data NOT found for calc_1040")
                return False
                
        except Exception as e:
            print(f"❌ Verification exception: {e}")
            return False
        
        # Step 4: Test calc_1040 (this should now work)
        print("\n📝 Step 4: Testing calc_1040...")
        try:
            calc_result = await calc_1040(
                engagement_id=self.engagement_id,
                filing_status="S",  # Single
                dependents_count=0
            )
            
            if calc_result.get('success'):
                summary = calc_result.get('summary', {})
                refund_or_due = summary.get('refund_or_due', 0)
                is_refund = summary.get('is_refund', False)
                tax = summary.get('tax', 0)
                agi = summary.get('agi', 0)
                
                print(f"✅ calc_1040 SUCCESS!")
                print(f"   AGI: ${agi:,.2f}")
                print(f"   Tax: ${tax:,.2f}")
                if is_refund:
                    print(f"   REFUND: ${refund_or_due:,.2f}")
                else:
                    print(f"   AMOUNT DUE: ${abs(refund_or_due):,.2f}")
                return True
            else:
                print(f"❌ calc_1040 failed: {calc_result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ calc_1040 exception: {e}")
            return False

async def main():
    """Main test runner"""
    tester = ConversationFixTester()
    
    success = await tester.test_conversation_fix()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 CONVERSATION FIX SUCCESSFUL!")
        print("   Your agent conversation should now work without 'Internal Server Error'")
        print("\n🚀 NEXT STEPS:")
        print("   1. Try your conversation again in the frontend")
        print("   2. Upload a W-2 document")
        print("   3. Provide: '2024, April Hensley'")
        print("   4. Confirm with 'Yes'")
        print("   5. The agent should now calculate taxes successfully!")
    else:
        print("⚠️  CONVERSATION FIX FAILED!")
        print("   There are still issues that need to be resolved.")

if __name__ == "__main__":
    asyncio.run(main())
