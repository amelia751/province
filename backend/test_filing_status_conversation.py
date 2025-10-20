#!/usr/bin/env python3
"""
Test filing status handling in conversation.
This simulates what should happen when user says "I am single"
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from province.services.tax_service import (
    TaxService,
    conversation_state,
    manage_state_tool,
    fill_form_tool
)


async def test_filing_status_conversation():
    """Test that filing status is properly handled"""
    print("=" * 80)
    print("🧪 TESTING FILING STATUS CONVERSATION HANDLING")
    print("=" * 80)
    
    user_id = "user_33w9KAn1gw3xXSa6MnBsySAQIIm"
    
    # Step 1: Start conversation
    print("\n1️⃣ Starting conversation...")
    service = TaxService()
    response = await service.start_conversation(user_id=user_id)
    
    # Extract session_id from conversation_state (the response is just the greeting message)
    session_id = conversation_state.get('current_session_id')
    print(f"   ✅ Session started: {session_id}")
    print(f"   Response: {response[:100]}...")
    
    # Step 2: Simulate user saying "I am single"
    print("\n2️⃣ User says: 'I am single'")
    print("   Agent should call: manage_state_tool(action='set', key='filing_status', value='Single')")
    
    # Manually call manage_state_tool to simulate what agent should do
    result = await manage_state_tool(
        action="set",
        key="filing_status",
        value="Single",
        session_id=session_id
    )
    print(f"   ✅ {result}")
    
    # Step 3: Verify it's saved
    print("\n3️⃣ Verifying filing_status is saved in session...")
    session_data = conversation_state.get(session_id, {})
    saved_status = session_data.get('filing_status', 'NOT FOUND')
    print(f"   filing_status in session: '{saved_status}'")
    
    if saved_status == 'Single':
        print(f"   ✅ CORRECT: Filing status saved properly")
    else:
        print(f"   ❌ WRONG: Expected 'Single', got '{saved_status}'")
        return
    
    # Step 4: Add mock W-2 data
    print("\n4️⃣ Adding mock W-2 data to session...")
    session_data['w2_data'] = {
        'forms': [{
            'employee': {
                'name': 'April Hensley',
                'SSN': '077-49-4905',
                'address': '31403 David Circles Suite 863, West Erinfort, WY 45881-3334',
                'street': '31403 David Circles Suite 863',
                'city': 'West Erinfort',
                'state': 'WY',
                'zip': '45881',
                'wages': 55151.93,
                'federal_withholding': 16606.17
            }
        }]
    }
    print("   ✅ W-2 data added")
    
    # Step 5: Add tax calculation
    print("\n5️⃣ Adding tax calculation to session...")
    session_data['tax_calculation'] = {
        'agi': 55151.93,
        'standard_deduction': 14600,
        'taxable_income': 40551.93,
        'tax': 4634.23,
        'withholding': 16606.17,
        'refund_or_due': 11971.94,
        'tax_year': 2024
    }
    print("   ✅ Tax calculation added")
    
    # Step 6: Call fill_form_tool (what agent should do)
    print("\n6️⃣ Calling fill_form_tool...")
    print("   Agent should pass: filing_status='Single'")
    
    result = await fill_form_tool(
        form_type="1040",
        filing_status="Single",  # EXPLICITLY PASSING THIS
        wages=55151.93,
        withholding=16606.17,
        dependents=0
    )
    
    print(f"\n   Result: {result[:200]}...")
    
    # Step 7: Check the actual form
    print("\n7️⃣ Verifying the filled form...")
    import boto3
    from dotenv import load_dotenv
    import fitz
    
    load_dotenv('.env.local')
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket = 'province-documents-[REDACTED-ACCOUNT-ID]-us-east-1'
    
    prefix = f'filled_forms/{user_id}/'
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    
    if 'Contents' in response:
        latest = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)[0]
        
        response = s3.get_object(Bucket=bucket, Key=latest['Key'])
        pdf_bytes = response['Body'].read()
        
        pdf_doc = fitz.open(stream=pdf_bytes, filetype='pdf')
        page = pdf_doc[0]
        
        print("\n   📋 Filing Status Checkboxes:")
        checkboxes = []
        for widget in page.widgets():
            if 'c1_3' in widget.field_name and 'FilingStatus' in widget.field_name:
                checkboxes.append((widget.field_name, widget.field_value))
        
        # Sort by index [0], [1], [2]
        checkboxes.sort()
        
        checkbox_names = ['Married Filing Jointly', 'Single', 'Married Filing Separately']
        expected_values = [False, True, False]  # Single should be checked
        
        for i, (field_name, field_value) in enumerate(checkboxes):
            checkbox_type = checkbox_names[i] if i < len(checkbox_names) else 'Unknown'
            expected = expected_values[i] if i < len(expected_values) else None
            
            is_checked = field_value in ['Yes', '1', '3', 1, 3]
            status = '✅ CORRECT' if is_checked == expected else '❌ WRONG'
            check_mark = '☑' if is_checked else '☐'
            print(f"      {check_mark} {checkbox_type}: value={field_value} {status}")
        
        pdf_doc.close()
        
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETE - Check results above")
        print("=" * 80)
    else:
        print("   ❌ No forms found in S3")


if __name__ == "__main__":
    asyncio.run(test_filing_status_conversation())

