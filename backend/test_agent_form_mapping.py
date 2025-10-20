#!/usr/bin/env python3
"""
Test agent conversation inputs vs form filling.
Focus on fields that come from agent conversation (not W-2):
1. Filing status
2. Digital assets
3. Standard deduction checkboxes
4. Dependents
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from province.services.tax_service import (
    TaxService,
    conversation_state,
    manage_state_tool,
    fill_form_tool
)


async def test_agent_conversation_fields():
    """Test fields that come from agent conversation"""
    print("=" * 80)
    print("🧪 TESTING AGENT CONVERSATION → FORM MAPPING")
    print("=" * 80)
    
    user_id = "user_33w9KAn1gw3xXSa6MnBsySAQIIm"
    
    # Start conversation
    print("\n1️⃣ Starting conversation...")
    service = TaxService()
    response = await service.start_conversation(user_id=user_id)
    session_id = conversation_state.get('current_session_id')
    print(f"   Session: {session_id}")
    
    # Simulate agent conversation: User says "I am single"
    print("\n2️⃣ User says: 'I am single'")
    await manage_state_tool(
        action="set",
        key="filing_status",
        value="Single",
        session_id=session_id
    )
    print(f"   ✅ Set filing_status='Single' in session")
    
    # User says "No digital assets"
    print("\n3️⃣ User says: 'No, I did not have digital assets'")
    await manage_state_tool(
        action="set",
        key="digital_assets",
        value="No",
        session_id=session_id
    )
    print(f"   ✅ Set digital_assets='No' in session")
    
    # User says "I have 2 dependents"
    print("\n4️⃣ User says: 'I have 2 dependents: Alice (daughter, SSN 123-45-6789) and Bob (son, SSN 987-65-4321)'")
    await manage_state_tool(
        action="set",
        key="dependents",
        value="2",
        session_id=session_id
    )
    print(f"   ✅ Set dependents='2' in session")
    
    # Add mock W-2 and calculation data
    session_data = conversation_state.get(session_id, {})
    session_data['w2_data'] = {
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
    
    session_data['tax_calculation'] = {
        'agi': 55151.93,
        'standard_deduction': 14600,
        'taxable_income': 40551.93,
        'tax': 4634.23,
        'withholding': 16606.17,
        'refund_or_due': 11971.94,
        'tax_year': 2024
    }
    
    # Check what's in session before filling
    print("\n5️⃣ Checking session state before form fill:")
    print(f"   filing_status: {session_data.get('filing_status', 'NOT SET')}")
    print(f"   digital_assets: {session_data.get('digital_assets', 'NOT SET')}")
    print(f"   dependents: {session_data.get('dependents', 'NOT SET')}")
    
    # Fill form - THIS IS WHERE THE ISSUE MIGHT BE
    print("\n6️⃣ Calling fill_form_tool with filing_status='Single'...")
    print(f"   (Agent should pass filing_status parameter explicitly)")
    
    result = await fill_form_tool(
        form_type="1040",
        filing_status="Single",  # EXPLICITLY passing this
        wages=55151.93,
        withholding=16606.17,
        dependents=2  # Passing dependents count
    )
    
    print(f"   Result: {result[:150]}...")
    
    # Verify the PDF
    print("\n7️⃣ VERIFYING FILLED PDF")
    print("=" * 80)
    
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
        
        # Check Page 1
        page = pdf_doc[0]
        
        # === FILING STATUS ===
        print("\n✅ FILING STATUS (c1_3):")
        filing_checkboxes = []
        for widget in page.widgets():
            if 'FilingStatus' in widget.field_name and 'c1_3' in widget.field_name:
                filing_checkboxes.append((widget.field_name, widget.field_value))
        
        filing_checkboxes.sort()
        if filing_checkboxes:
            checkbox_names = ['Married Filing Jointly', 'Single', 'Married Filing Separately']
            for i, (field_name, field_value) in enumerate(filing_checkboxes):
                checkbox_type = checkbox_names[i] if i < len(checkbox_names) else 'Unknown'
                is_checked = field_value in ['Yes', '1', '3', 1, 3]
                
                if checkbox_type == 'Single':
                    status = '✅ CORRECT' if is_checked else '❌ WRONG - SHOULD BE CHECKED'
                else:
                    status = '✅ CORRECT' if not is_checked else '❌ WRONG - SHOULD BE UNCHECKED'
                
                check_mark = '☑' if is_checked else '☐'
                print(f"   {check_mark} {checkbox_type}: {field_value} {status}")
        else:
            print("   ⚠️  No filing status checkboxes found!")
        
        # === DIGITAL ASSETS ===
        print("\n✅ DIGITAL ASSETS (c1_6/c1_7):")
        for widget in page.widgets():
            field_name = widget.field_name
            if 'c1_6' in field_name or 'c1_7' in field_name:
                is_checked = widget.field_value in ['Yes', '1', '3', 1, 3]
                check_mark = '☑' if is_checked else '☐'
                
                if 'c1_6' in field_name:
                    # This might be "Yes" checkbox
                    status = '✅ CORRECT' if not is_checked else '❌ WRONG - Should be No'
                    print(f"   {check_mark} Digital Assets YES (c1_6): {widget.field_value} {status}")
                elif 'c1_7' in field_name:
                    # This might be "No" checkbox
                    status = '✅ CORRECT' if is_checked else '❌ WRONG - Should be checked'
                    print(f"   {check_mark} Digital Assets NO (c1_7): {widget.field_value} {status}")
        
        # === STANDARD DEDUCTION ===
        print("\n✅ STANDARD DEDUCTION CHECKBOXES:")
        for widget in page.widgets():
            field_name = widget.field_name
            # Look for standard deduction checkboxes
            if 'c1_' in field_name and 'Page1' in field_name:
                # Check if it's related to standard deduction
                if any(x in field_name for x in ['c1_8', 'c1_9', 'c1_10', 'c1_11', 'c1_12']):
                    is_checked = widget.field_value in ['Yes', '1', '3', 1, 3]
                    check_mark = '☑' if is_checked else '☐'
                    print(f"   {check_mark} {field_name}: {widget.field_value}")
        
        # === DEPENDENTS ===
        print("\n✅ DEPENDENTS:")
        dependents_fields = {}
        for widget in page.widgets():
            field_name = widget.field_name
            # Look for dependent fields (f1_18 onwards are usually dependents)
            if any(f'f1_{i}' in field_name for i in range(18, 32)):  # Dependent fields range
                value = widget.field_value if widget.field_value else 'EMPTY'
                dependents_fields[field_name] = value
        
        if dependents_fields:
            for field, value in sorted(dependents_fields.items())[:10]:  # Show first 10
                print(f"   {field}: \"{value}\"")
        else:
            print("   ⚠️  No dependent fields filled")
        
        pdf_doc.close()
    else:
        print("   ❌ No forms found!")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)
    
    # Summary
    print("\n📊 SUMMARY:")
    print("   This test reveals:")
    print("   1. Whether agent conversation data reaches the form filler")
    print("   2. Whether field mappings match agent's understanding")
    print("   3. Which fields work vs which don't")


if __name__ == "__main__":
    asyncio.run(test_agent_conversation_fields())

