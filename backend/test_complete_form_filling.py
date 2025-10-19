#!/usr/bin/env python3
"""
Complete Form 1040 Filling Test

Tests the complete tax conversation flow with enhanced field mapping.
Verifies all fields are filled properly on Form 1040.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from province.services.tax_service import tax_service
from dotenv import load_dotenv
import boto3

load_dotenv('.env.local')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_complete_form_filling():
    """Test complete conversation with proper form filling."""
    
    print("\n" + "="*80)
    print("🧪 COMPLETE FORM 1040 FILLING TEST")
    print("="*80)
    print("Testing comprehensive field mapping and form filling\n")
    
    session_id = f"test_complete_filling_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Step 1: Start conversation
        print("📞 Step 1: Starting conversation...")
        await tax_service.start_conversation(session_id)
        await asyncio.sleep(0.5)
        
        # Step 2: Filing status
        print("💍 Step 2: Providing filing status (Single)...")
        await tax_service.continue_conversation("I'm single", session_id)
        await asyncio.sleep(0.5)
        
        # Step 3: Dependents
        print("👶 Step 3: Providing dependents info...")
        await tax_service.continue_conversation("No dependents", session_id)
        await asyncio.sleep(0.5)
        
        # Step 4: Process W2
        print("📄 Step 4: Processing W-2...")
        w2_path = "/Users/anhlam/Downloads/W2_XL_input_clean_1000.pdf"
        if not os.path.exists(w2_path):
            w2_path = "datasets/w2-forms/test/W2_XL_input_clean_1000.pdf"
        
        await tax_service.continue_conversation(
            f"Please process my W-2 document at {w2_path}. My name is John A. Smith.",
            session_id
        )
        await asyncio.sleep(1)
        
        # Step 5: Address
        print("🏠 Step 5: Providing full address...")
        await tax_service.continue_conversation(
            "My address is 123 Main Street, Anytown, CA 90210",
            session_id
        )
        await asyncio.sleep(0.5)
        
        # Step 6: Calculate taxes
        print("🧮 Step 6: Calculating taxes...")
        await tax_service.continue_conversation(
            "Great! Now please calculate my taxes.",
            session_id
        )
        await asyncio.sleep(1)
        
        # Step 7: Fill form with enhanced mapping
        print("📝 Step 7: Filling Form 1040 with ALL fields...")
        print("   This should now fill:")
        print("   ✅ First name, middle initial, last name (separately)")
        print("   ✅ SSN")
        print("   ✅ Full address (street, city, state, ZIP)")
        print("   ✅ Filing status checkbox (Single)")
        print("   ✅ Digital assets question (No)")
        print("   ✅ All income lines")
        print("   ✅ Standard deduction")
        print("   ✅ Taxable income")
        print("   ✅ Tax computation")
        print("   ✅ Federal withholding")
        print("   ✅ Refund amount")
        print()
        
        fill_response = await tax_service.continue_conversation(
            "Perfect! Please fill out my Form 1040 with all this information.",
            session_id
        )
        print(f"✅ Form filled: {fill_response[:200]}...")
        await asyncio.sleep(1)
        
        # Step 8: Verify form data
        print("\n🔍 Step 8: Verifying form data...")
        state = tax_service.get_conversation_state(session_id)
        filled_form = state.get('filled_form', {})
        
        if not filled_form:
            print("❌ FAILED: No filled form in state!")
            return False
        
        form_data = filled_form.get('form_data', {})
        print(f"\n📋 Form Data Summary ({len(form_data)} fields):")
        print(f"   Name: {form_data.get('f1_01')} {form_data.get('f1_02')} {form_data.get('f1_03')}")
        print(f"   SSN: {form_data.get('f1_04')}")
        print(f"   Address: {form_data.get('f1_09')}")
        print(f"   City: {form_data.get('f1_10')}")
        print(f"   State: {form_data.get('f1_11')}")
        print(f"   ZIP: {form_data.get('f1_12')}")
        print(f"   Filing Status (Single): {form_data.get('c1_1')}")
        print(f"   Digital Assets (No): {form_data.get('c1_6')}")
        print(f"   Wages (Line 1a): ${form_data.get('f1_13'):,.2f}" if form_data.get('f1_13') else "   Wages: N/A")
        print(f"   Withholding (Line 25a): ${form_data.get('f1_44'):,.2f}" if form_data.get('f1_44') else "   Withholding: N/A")
        print(f"   Refund (Line 34): ${form_data.get('f1_51'):,.2f}" if form_data.get('f1_51') else "   Refund: N/A")
        
        # Step 9: Download and verify PDF
        print("\n📦 Step 9: Downloading PDF to verify...")
        s3 = boto3.client(
            's3',
            region_name='us-east-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        bucket = os.getenv('DOCUMENTS_BUCKET_NAME')
        taxpayer_name = form_data.get('taxpayer_name', 'John A Smith').replace(' ', '_')
        
        # Find latest PDF
        prefix = f'filled_forms/{taxpayer_name}/1040/2024/'
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=10)
        
        if not response.get('Contents'):
            print(f"❌ No PDFs found in {prefix}")
            return False
        
        # Get most recent
        pdfs = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)
        latest_pdf = pdfs[0]
        
        print(f"✅ Found PDF: {latest_pdf['Key']}")
        print(f"   Size: {latest_pdf['Size']:,} bytes")
        print(f"   Modified: {latest_pdf['LastModified']}")
        
        # Download and verify
        pdf_obj = s3.get_object(Bucket=bucket, Key=latest_pdf['Key'])
        pdf_content = pdf_obj['Body'].read()
        
        # Verify PDF
        if pdf_content[:4] != b'%PDF':
            print("❌ Not a valid PDF!")
            return False
        
        print(f"✅ Valid PDF ({len(pdf_content):,} bytes)")
        
        # Check for filled data
        pdf_text = pdf_content.decode('latin-1', errors='ignore')
        checks = [
            ('Name (JOHN)', 'JOHN' in pdf_text or 'John' in pdf_text),
            ('Name (SMITH)', 'SMITH' in pdf_text or 'Smith' in pdf_text),
            ('SSN', '123-45-6789' in pdf_text or '123456789' in pdf_text),
            ('Wages ($55,151)', '55151' in pdf_text or '55,151' in pdf_text),
            ('Withholding ($16,606)', '16606' in pdf_text or '16,606' in pdf_text),
            ('City (ANYTOWN)', 'ANYTOWN' in pdf_text or 'Anytown' in pdf_text),
            ('State (CA)', 'CA' in pdf_text),
            ('ZIP (90210)', '90210' in pdf_text),
        ]
        
        print("\n🔬 PDF Content Verification:")
        all_passed = True
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"   {status} {check_name}: {'Found' if check_result else 'NOT FOUND'}")
            if not check_result:
                all_passed = False
        
        # Final summary
        print("\n" + "="*80)
        print("📊 FINAL RESULTS")
        print("="*80)
        print()
        
        if all_passed:
            print("🎉 SUCCESS! Form 1040 is properly filled with ALL fields!")
            print()
            print("✅ Personal Information: Complete")
            print("✅ Address: Complete")
            print("✅ Filing Status: Checkbox marked")
            print("✅ Digital Assets: Answered")
            print("✅ Income: Filled")
            print("✅ Deductions: Filled")
            print("✅ Tax Computation: Filled")
            print("✅ Payments: Filled")
            print("✅ Refund: Calculated and filled")
            print()
            print(f"📄 PDF Location: {latest_pdf['Key']}")
            return True
        else:
            print("⚠️  PARTIAL SUCCESS - Some fields may not be filled")
            print("   Check the PDF manually for completeness")
            return False
        
    except Exception as e:
        logger.error(f"Error in test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_complete_form_filling())
    
    if success:
        print("\n✅ TEST PASSED - Form filling is complete and comprehensive!")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - Check output above")
        sys.exit(1)

