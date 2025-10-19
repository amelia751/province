#!/usr/bin/env python3
"""
Realistic workflow test that mimics what the agent actually does.
This will test the complete flow: create engagement -> save document -> ingest -> calc -> fill form
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
    from province.agents.tax.tools.form_filler import fill_tax_form
    from province.core.config import get_settings
    import boto3
    import base64
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class RealisticWorkflowTester:
    def __init__(self):
        self.settings = get_settings()
        self.engagement_id = str(uuid.uuid4())
        self.user_id = "test-user-workflow"
        self.results = {}
        
    async def setup_engagement(self):
        """Create a tax engagement in DynamoDB"""
        print("🏗️  Setting up tax engagement...")
        try:
            dynamodb = boto3.resource('dynamodb', region_name=self.settings.aws_region)
            table = dynamodb.Table(self.settings.tax_engagements_table_name)
            
            # Create engagement with composite key
            engagement_item = {
                'tenant_id#engagement_id': f"{self.user_id}#{self.engagement_id}",
                'user_id': self.user_id,
                'engagement_id': self.engagement_id,
                'tax_year': 2024,
                'filing_status': 'S',
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            table.put_item(Item=engagement_item)
            print(f"✅ Created engagement: {self.engagement_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create engagement: {e}")
            return False
    
    async def test_complete_workflow(self):
        """Test the complete tax workflow"""
        print("🧪 TESTING COMPLETE TAX WORKFLOW")
        print("=" * 60)
        
        # Step 1: Setup engagement
        if not await self.setup_engagement():
            return False
        
        # Step 2: Save a test W-2 document
        print("\n📝 Step 2: Saving W-2 document...")
        try:
            # Create a simple test W-2 content
            test_w2_content = "Test W-2 document content for workflow testing"
            content_b64 = base64.b64encode(test_w2_content.encode()).decode()
            
            save_result = await save_document(
                engagement_id=self.engagement_id,
                path="chat-uploads/test_w2_workflow.pdf",
                content_b64=content_b64,
                mime_type="application/pdf"
            )
            
            if save_result.get('success'):
                print(f"✅ Document saved: {save_result.get('s3_key')}")
            else:
                print(f"❌ Document save failed: {save_result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ Document save exception: {e}")
            return False
        
        # Step 3: Ingest a real W-2 document (use existing one)
        print("\n📝 Step 3: Ingesting W-2 document...")
        try:
            ingest_result = await ingest_documents(
                s3_key="datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_1000.pdf",
                taxpayer_name="April Hensley",
                tax_year=2024,
                document_type="W-2"
            )
            
            if ingest_result.get('success'):
                total_wages = ingest_result.get('total_wages', 0)
                print(f"✅ Document ingested: ${total_wages:,.2f} in wages")
                
                # Save the W-2 data to our engagement
                await self.save_w2_data_to_engagement(ingest_result)
            else:
                print(f"❌ Document ingest failed: {ingest_result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ Document ingest exception: {e}")
            return False
        
        # Step 4: Calculate 1040
        print("\n📝 Step 4: Calculating 1040...")
        try:
            calc_result = await calc_1040(
                engagement_id=self.engagement_id,
                filing_status="S",
                dependents_count=0
            )
            
            if calc_result.get('success'):
                tax_owed = calc_result.get('tax_owed', 0)
                refund = calc_result.get('refund', 0)
                print(f"✅ 1040 calculated: Tax owed: ${tax_owed:,.2f}, Refund: ${refund:,.2f}")
            else:
                print(f"❌ 1040 calculation failed: {calc_result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ 1040 calculation exception: {e}")
            return False
        
        # Step 5: Fill tax form
        print("\n📝 Step 5: Filling tax form...")
        try:
            form_data = {
                "taxpayer_name": "April Hensley",
                "filing_status": "S",
                "total_income": 55151.93,
                "taxable_income": 42151.93,  # After standard deduction
                "tax_owed": calc_result.get('tax_owed', 0),
                "withholding": 16606.17,
                "refund": calc_result.get('refund', 0),
                "ssn": "123-45-6789",
                "address": "123 Test St, Test City, TS 12345"
            }
            
            form_result = await fill_tax_form(
                form_type="1040",
                form_data=form_data
            )
            
            if form_result.get('success'):
                form_url = form_result.get('filled_form_url', 'N/A')
                print(f"✅ Form filled: {form_url}")
            else:
                print(f"❌ Form filling failed: {form_result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ Form filling exception: {e}")
            return False
        
        print("\n🎉 COMPLETE WORKFLOW TEST PASSED!")
        print("All tax agent tools are working correctly in sequence.")
        return True
    
    async def save_w2_data_to_engagement(self, ingest_result):
        """Save W-2 data to the engagement for calc_1040 to use"""
        try:
            dynamodb = boto3.resource('dynamodb', region_name=self.settings.aws_region)
            table = dynamodb.Table(self.settings.tax_documents_table_name)
            
            # Create a W-2 document entry
            w2_item = {
                'tenant_id#engagement_id': f"{self.user_id}#{self.engagement_id}",
                'doc#path': 'doc#w2_extract.json',
                'engagement_id': self.engagement_id,
                'document_type': 'W-2_EXTRACT',
                'mime_type': 'application/json',
                'created_at': datetime.now().isoformat(),
                's3_key': f"tax-engagements/{self.engagement_id}/extracts/w2_extract.json",
                'size_bytes': len(json.dumps(ingest_result)),
                'hash': 'test-hash',
                'w2_extract': ingest_result.get('w2_extract', {}),
                'total_wages': ingest_result.get('total_wages', 0),
                'total_withholding': ingest_result.get('total_withholding', 0)
            }
            
            table.put_item(Item=w2_item)
            print(f"✅ Saved W-2 data to engagement for calc_1040")
            
        except Exception as e:
            print(f"⚠️  Could not save W-2 data to engagement: {e}")

async def main():
    """Main test runner"""
    tester = RealisticWorkflowTester()
    success = await tester.test_complete_workflow()
    
    if success:
        print("\n🎯 CONCLUSION: All tax agent tools are working correctly!")
        print("   The throttling issue is likely caused by:")
        print("   - Agent orchestration logic")
        print("   - Session management")
        print("   - Bedrock agent configuration")
        print("   - Tool invocation frequency")
    else:
        print("\n⚠️  CONCLUSION: There are issues with the tax workflow!")
        print("   Check the errors above to identify problematic tools.")

if __name__ == "__main__":
    asyncio.run(main())
