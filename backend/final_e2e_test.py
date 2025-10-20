#!/usr/bin/env python3
"""
FINAL END-TO-END TEST
Verifies complete workflow with REAL W-2 data extraction (name, SSN, address, wages)
"""
import sys
import asyncio
import os
from datetime import datetime
import boto3

sys.path.insert(0, 'src')
from dotenv import load_dotenv
load_dotenv('.env.local')

from province.services.tax_service import TaxService

USER_ID = "user_33w9KAn1gw3xXSa6MnBsySAQIIm"
ENGAGEMENT_ID = "ea3b3a4f-c877-4d29-bd66-2cff2aa77476"

async def run_complete_e2e_test():
    print("\n" + "="*80)
    print("🚀 FINAL COMPLETE END-TO-END TEST")
    print("="*80 + "\n")
    
    tax_service = TaxService()
    session_id = f"final_e2e_{int(datetime.now().timestamp())}"
    
    try:
        # Step 1: Start conversation
        print("Step 1: Starting conversation...")
        await tax_service.start_conversation(session_id=session_id, user_id=USER_ID)
        print("✅ Session started\n")
        
        # Step 2: Upload W-2
        print("Step 2: Uploading W-2 from Downloads...")
        w2_path = os.path.expanduser("~/Downloads/W2_XL_input_clean_1000.pdf")
        if not os.path.exists(w2_path):
            print(f"❌ W-2 not found at {w2_path}")
            return False
        
        s3 = boto3.client('s3', region_name='us-east-1')
        bucket = 'province-documents-[REDACTED-ACCOUNT-ID]-us-east-1'
        s3_key = f"documents/{USER_ID}/w2_final_e2e_test.pdf"
        
        with open(w2_path, 'rb') as f:
            s3.put_object(Bucket=bucket, Key=s3_key, Body=f.read())
        print(f"   📤 Uploaded to: {s3_key}\n")
        
        # Step 3: Process W-2
        print("Step 3: Processing W-2 with Bedrock...")
        w2_response = await tax_service.continue_conversation(
            user_message=f"I uploaded my W-2 at {s3_key}",
            session_id=session_id,
            user_id=USER_ID
        )
        print("✅ W-2 processed\n")
        
        # Step 4: Set filing status
        print("Step 4: Setting filing status...")
        await tax_service.continue_conversation(
            user_message="I'm filing as Single",
            session_id=session_id,
            user_id=USER_ID
        )
        print("✅ Filing status: Single\n")
        
        # Step 5: Set dependents
        print("Step 5: Setting dependents...")
        await tax_service.continue_conversation(
            user_message="I have no dependents",
            session_id=session_id,
            user_id=USER_ID
        )
        print("✅ Dependents: 0\n")
        
        # Step 6: Calculate taxes
        print("Step 6: Calculating taxes...")
        await tax_service.continue_conversation(
            user_message="Please calculate my taxes",
            session_id=session_id,
            user_id=USER_ID
        )
        print("✅ Tax calculation complete\n")
        
        # Step 7: Fill Form 1040
        print("Step 7: Filling Form 1040...")
        await tax_service.continue_conversation(
            user_message="Please fill out my Form 1040",
            session_id=session_id,
            user_id=USER_ID
        )
        print("✅ Form 1040 filled\n")
        
        # Step 8: Verify the filled form
        print("Step 8: Verifying filled form with REAL data...")
        await asyncio.sleep(2)
        
        prefix = f"filled_forms/{USER_ID}/1040/2024/"
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        
        if 'Contents' not in response:
            print(f"❌ No filled form found")
            return False
        
        # Get latest file
        files = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)
        latest_file = files[0]
        
        print(f"   📁 Form saved: {latest_file['Key']}")
        print(f"   📦 Size: {latest_file['Size']:,} bytes\n")
        
        # Download and verify
        local_path = '/tmp/final_e2e_form.pdf'
        s3.download_file(bucket, latest_file['Key'], local_path)
        
        import fitz
        doc = fitz.open(local_path)
        
        # Extract all filled fields
        filled_fields = {}
        for page_num in range(doc.page_count):
            page = doc[page_num]
            for widget in page.widgets():
                if widget.field_value and widget.field_value not in ['Off', '']:
                    filled_fields[widget.field_name] = widget.field_value
        
        doc.close()
        
        print(f"   📊 Verification Results:")
        print(f"      Total fields filled: {len(filled_fields)}/88\n")
        
        # Verify REAL data from W-2 (this W-2 has April Hensley from West Erinfort WY)
        checks = {
            '✅ Real Name (April Hensley)': any('April' in str(v) or 'Hensley' in str(v) for v in filled_fields.values()),
            '✅ Real SSN (077-49-4905)': any('077-49-4905' in str(v) for v in filled_fields.values()),
            '✅ Real Address (31403 David Circles)': any('31403' in str(v) or 'David' in str(v) for v in filled_fields.values()),
            '✅ Real City (West Erinfort)': any('Erinfort' in str(v) for v in filled_fields.values()),
            '✅ Real State (WY)': any(v == 'WY' for v in filled_fields.values()),
            '✅ Real ZIP (45881-3334)': any('45881' in str(v) for v in filled_fields.values()),
            '✅ Real Wages ($55,151.93)': any('55151' in str(v).replace(',', '') for v in filled_fields.values()),
            '✅ Real Withholding ($16,606.17)': any('16606' in str(v).replace(',', '') for v in filled_fields.values()),
            '✅ Calculated Refund ($11,971.94)': any('11971' in str(v).replace(',', '') for v in filled_fields.values()),
        }
        
        print("      Critical field checks:")
        for check, passed in checks.items():
            icon = "✅" if passed else "❌"
            print(f"         {icon} {check}")
        
        # Show all filled fields
        print(f"\n      All filled fields:")
        for field, val in filled_fields.items():
            print(f"         {field[:60]:60} = {val}")
        
        all_passed = all(checks.values())
        
        # Generate URL
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': latest_file['Key']},
            ExpiresIn=3600
        )
        
        print(f"\n{'='*80}")
        if all_passed:
            print("✅ ✅ ✅  END-TO-END TEST PASSED - ALL REAL W-2 DATA!  ✅ ✅ ✅")
        else:
            print("⚠️  TEST COMPLETED WITH SOME MISSING DATA")
        print(f"{'='*80}")
        print(f"\n🔗 Final Form URL (valid for 1 hour):")
        print(url)
        print()
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_complete_e2e_test())
    sys.exit(0 if success else 1)

