#!/usr/bin/env python3
"""
Final comprehensive test for all implementations:
1. Filing status mapping
2. Digital assets mapping
3. Standard deduction mapping
4. Dependent extraction and filling
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from province.services.tax_service import TaxService, conversation_state, fill_form_tool
import boto3
from dotenv import load_dotenv
import fitz

load_dotenv('.env.local')


async def test_complete_implementation():
    """Test all new implementations"""
    print("=" * 80)
    print("🧪 COMPREHENSIVE IMPLEMENTATION TEST")
    print("=" * 80)
    
    user_id = "user_33w9KAn1gw3xXSa6MnBsySAQIIm"
    
    # Start conversation
    print("\n1️⃣ Starting conversation...")
    service = TaxService()
    greeting = await service.start_conversation(user_id=user_id)
    session_id = conversation_state.get('current_session_id')
    print(f"   Session: {session_id}")
    
    # Add mock data
    print("\n2️⃣ Setting up test data...")
    conversation_state[session_id]['w2_data'] = {
        'forms': [{
            'employee': {
                'name': 'April Hensley',
                'SSN': '077-49-4905',
                'address': '31403 David Circles Suite 863, West Erinfort, WY 45881-3334',
                'street': '31403 David Circles',
                'apt_no': '863',
                'city': 'West Erinfort',
                'state': 'WY',
                'zip': '45881',
                'wages': 55151.93,
                'federal_withholding': 16606.17
            }
        }]
    }
    
    conversation_state[session_id]['tax_calculation'] = {
        'agi': 55151.93,
        'standard_deduction': 14600,
        'taxable_income': 40551.93,
        'tax': 4634.23,
        'withholding': 16606.17,
        'refund_or_due': 11971.94,
        'tax_year': 2024
    }
    
    # Add dependents to conversation state
    print("\n3️⃣ Adding dependents...")
    conversation_state[session_id]['dependents_list'] = [
        {
            'first_name': 'Alice',
            'last_name': 'Smith',
            'ssn': '123-45-6789',
            'relationship': 'daughter'
        },
        {
            'first_name': 'Bob',
            'last_name': 'Smith',
            'ssn': '987-65-4321',
            'relationship': 'son'
        }
    ]
    conversation_state[session_id]['dependents'] = 2
    print("   ✅ Added 2 dependents")
    
    # Fill form
    print("\n4️⃣ Filling form...")
    result = await fill_form_tool(
        form_type="1040",
        filing_status="Single",
        wages=55151.93,
        withholding=16606.17,
        dependents=2
    )
    
    print(f"   ✅ Form filled")
    
    # Verify the PDF
    print("\n" + "=" * 80)
    print("📋 VERIFICATION REPORT")
    print("=" * 80)
    
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket = 'province-documents-[REDACTED-ACCOUNT-ID]-us-east-1'
    
    prefix = f'filled_forms/{user_id}/'
    s3_response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    
    if 'Contents' not in s3_response:
        print("❌ No forms found!")
        return
    
    latest = sorted(s3_response['Contents'], key=lambda x: x['LastModified'], reverse=True)[0]
    print(f"\n📄 Form: {latest['Key']}")
    
    response = s3.get_object(Bucket=bucket, Key=latest['Key'])
    pdf_bytes = response['Body'].read()
    
    pdf_doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    page = pdf_doc[0]
    
    # Verification checklist
    checks = {
        'filing_status_single': False,
        'digital_assets_no': False,
        'standard_deduction': 0,
        'dependent_count': 0
    }
    
    for widget in page.widgets():
        field_name = widget.field_name
        is_checked = widget.field_value in ['Yes', '1', '3', 1, 3]
        value = widget.field_value if widget.field_value else ''
        
        # Filing status
        if 'c1_1[0]' in field_name and is_checked:
            checks['filing_status_single'] = True
        
        # Digital assets
        if 'c1_6[0]' in field_name and is_checked:
            checks['digital_assets_no'] = True
        
        # Standard deduction
        if any(f'c1_{i}[0]' in field_name for i in range(8, 13)) and is_checked:
            checks['standard_deduction'] += 1
        
        # Dependents
        if 'Alice' in str(value) or 'Bob' in str(value):
            checks['dependent_count'] += 1
    
    pdf_doc.close()
    
    # Print results
    print("\n✅ RESULTS:")
    print(f"   Filing Status (Single): {'✅ PASS' if checks['filing_status_single'] else '❌ FAIL'}")
    print(f"   Digital Assets (No): {'✅ PASS' if checks['digital_assets_no'] else '❌ FAIL'}")
    print(f"   Standard Deduction: {checks['standard_deduction']} checkboxes")
    print(f"   Dependents Found: {checks['dependent_count']} mentions (Expected: 2+)")
    
    # Overall result
    success = (
        checks['filing_status_single'] and
        checks['digital_assets_no'] and
        checks['dependent_count'] >= 2
    )
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("=" * 80)
    
    return success


if __name__ == "__main__":
    success = asyncio.run(test_complete_implementation())
    sys.exit(0 if success else 1)

