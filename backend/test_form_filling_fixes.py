#!/usr/bin/env python3
"""
Comprehensive test for two form filling issues:
1. Filing status: "Married filing jointly" checkbox still checked despite selecting "Single"
2. Address parsing: Need to split "Suite 863" into apt_no field
"""

import asyncio
import sys
import os
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from province.services.tax_service import (
    TaxService,
    conversation_state,
    manage_state_tool,
    fill_form_tool
)


def parse_address_with_unit(full_address: str) -> dict:
    """
    Parse address to extract street, unit number, city, state, zip.
    
    Handles patterns like:
    - "123 Main St Apt 456 New York NY 10001"
    - "123 Main St Suite 456 New York NY 10001"
    - "123 Main St #456 New York NY 10001"
    - "123 Main St Room 456 New York NY 10001"
    - "123 Main St Unit 456 New York NY 10001"
    """
    # Pattern for unit designators
    unit_patterns = [
        r'(Apt\.?|Apartment)\s+(\S+)',
        r'(Suite|Ste\.?)\s+(\S+)',
        r'(Unit|#)\s*(\S+)',
        r'(Room|Rm\.?)\s+(\S+)',
        r'(Bldg\.?|Building)\s+(\S+)',
        r'(Floor|Fl\.?)\s+(\S+)',
    ]
    
    # Extract ZIP code first (5 or 9 digits)
    zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\s*$', full_address)
    if not zip_match:
        print(f"⚠️  No ZIP code found in: {full_address}")
        return {'raw': full_address}
    
    zip_code = zip_match.group(1)
    address_without_zip = full_address[:zip_match.start()].strip()
    
    # Extract state (2-letter code before ZIP)
    state_match = re.search(r'\b([A-Z]{2})\s*$', address_without_zip)
    if not state_match:
        print(f"⚠️  No state found in: {address_without_zip}")
        return {'raw': full_address, 'zip': zip_code}
    
    state = state_match.group(1)
    address_without_state = address_without_zip[:state_match.start()].strip()
    
    # Try to find unit designator
    unit_found = False
    unit_type = None
    unit_number = None
    street = None
    city = None
    
    for pattern in unit_patterns:
        match = re.search(pattern, address_without_state, re.IGNORECASE)
        if match:
            unit_type = match.group(1)
            unit_number = match.group(2)
            
            # Everything before unit is street, everything after is city
            before_unit = address_without_state[:match.start()].strip()
            after_unit = address_without_state[match.end():].strip()
            
            street = before_unit
            city = after_unit
            unit_found = True
            print(f"   ✅ Found unit: {unit_type} {unit_number}")
            break
    
    if not unit_found:
        # No unit found - split by last space to separate city from street
        parts = address_without_state.rsplit(' ', 1)
        if len(parts) == 2:
            street = parts[0].strip()
            city = parts[1].strip()
        else:
            street = address_without_state
            city = "Unknown"
    
    result = {
        'street': street,
        'apt_no': unit_number if unit_found else '',
        'city': city,
        'state': state,
        'zip': zip_code,
        'full': full_address
    }
    
    return result


async def test_complete_fixes():
    """Test both filing status and address parsing fixes"""
    print("=" * 80)
    print("🧪 COMPREHENSIVE FORM FILLING FIXES TEST")
    print("=" * 80)
    
    user_id = "user_33w9KAn1gw3xXSa6MnBsySAQIIm"
    
    # Test 1: Address Parsing
    print("\n1️⃣ TESTING ADDRESS PARSING")
    print("=" * 80)
    
    test_addresses = [
        "31403 David Circles Suite 863 West Erinfort WY 45881-3334",
        "123 Main Street Apt 4B New York NY 10001",
        "456 Oak Ave #789 Los Angeles CA 90210",
        "789 Elm St Room 101 Chicago IL 60601",
        "321 Pine Rd Unit 2C Boston MA 02101",
        "555 Maple Dr Austin TX 78701",  # No unit
    ]
    
    for addr in test_addresses:
        print(f"\n📍 Input: {addr}")
        parsed = parse_address_with_unit(addr)
        print(f"   Street: {parsed.get('street', 'N/A')}")
        print(f"   Apt/Unit: {parsed.get('apt_no', 'N/A')}")
        print(f"   City: {parsed.get('city', 'N/A')}")
        print(f"   State: {parsed.get('state', 'N/A')}")
        print(f"   ZIP: {parsed.get('zip', 'N/A')}")
    
    # Test 2: Filing Status Mapping
    print("\n\n2️⃣ TESTING FILING STATUS MAPPING")
    print("=" * 80)
    
    # Check DynamoDB mapping
    import boto3
    from dotenv import load_dotenv
    
    load_dotenv('.env.local')
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('province-form-mappings')
    
    response = table.get_item(Key={'form_type': 'F1040', 'tax_year': '2024'})
    if 'Item' in response:
        mapping = response['Item'].get('mapping', {})
        
        print("\n📋 Current DynamoDB Mapping:")
        for key in ['single', 'married_joint', 'married_separate', 'head_household']:
            if key in mapping:
                pdf_path = mapping[key].get('pdf_field_path', 'N/A')
                print(f"   {key}: {pdf_path}")
    
    # Test 3: Full Form Fill
    print("\n\n3️⃣ TESTING FULL FORM FILL WITH FIXES")
    print("=" * 80)
    
    # Start conversation
    service = TaxService()
    response = await service.start_conversation(user_id=user_id)
    session_id = conversation_state.get('current_session_id')
    
    # Set filing status
    await manage_state_tool(
        action="set",
        key="filing_status",
        value="Single",
        session_id=session_id
    )
    
    # Parse the test address
    full_address = "31403 David Circles Suite 863 West Erinfort WY 45881-3334"
    parsed_address = parse_address_with_unit(full_address)
    
    print(f"\n📝 Using address:")
    print(f"   Street: {parsed_address['street']}")
    print(f"   Apt: {parsed_address['apt_no']}")
    print(f"   City: {parsed_address['city']}")
    print(f"   State: {parsed_address['state']}")
    print(f"   ZIP: {parsed_address['zip']}")
    
    # Add mock data to session
    session_data = conversation_state.get(session_id, {})
    session_data['w2_data'] = {
        'forms': [{
            'employee': {
                'name': 'April Hensley',
                'SSN': '077-49-4905',
                'address': full_address,
                'street': parsed_address['street'],
                'apt_no': parsed_address['apt_no'],
                'city': parsed_address['city'],
                'state': parsed_address['state'],
                'zip': parsed_address['zip'],
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
    
    # Fill form
    print(f"\n🎯 Filling form with filing_status='Single'...")
    result = await fill_form_tool(
        form_type="1040",
        filing_status="Single",
        wages=55151.93,
        withholding=16606.17,
        dependents=0
    )
    
    print(f"   Result: {result[:150]}...")
    
    # Test 4: Verify the PDF
    print("\n\n4️⃣ VERIFYING FILLED PDF")
    print("=" * 80)
    
    import fitz
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
        
        # Check filing status
        print("\n✅ Filing Status Verification:")
        checkboxes = []
        for widget in page.widgets():
            if 'c1_3' in widget.field_name and 'FilingStatus' in widget.field_name:
                checkboxes.append((widget.field_name, widget.field_value))
        
        checkboxes.sort()
        checkbox_names = ['Married Filing Jointly', 'Single', 'Married Filing Separately']
        
        for i, (field_name, field_value) in enumerate(checkboxes):
            checkbox_type = checkbox_names[i] if i < len(checkbox_names) else 'Unknown'
            is_checked = field_value in ['Yes', '1', '3', 1, 3]
            
            if checkbox_type == 'Single':
                status = '✅ CORRECT' if is_checked else '❌ WRONG - SHOULD BE CHECKED'
            else:
                status = '✅ CORRECT' if not is_checked else '❌ WRONG - SHOULD BE UNCHECKED'
            
            check_mark = '☑' if is_checked else '☐'
            print(f"   {check_mark} {checkbox_type}: {field_value} {status}")
        
        # Check address fields
        print("\n✅ Address Fields Verification:")
        address_fields = {}
        for widget in page.widgets():
            field_name = widget.field_name
            if 'f1_10' in field_name:  # Street
                address_fields['Street'] = widget.field_value or 'EMPTY'
            elif 'f1_11' in field_name:  # Apt
                address_fields['Apt'] = widget.field_value or 'EMPTY'
            elif 'f1_12' in field_name:  # City
                address_fields['City'] = widget.field_value or 'EMPTY'
            elif 'f1_13' in field_name:  # State
                address_fields['State'] = widget.field_value or 'EMPTY'
            elif 'f1_14' in field_name:  # ZIP
                address_fields['ZIP'] = widget.field_value or 'EMPTY'
        
        expected = {
            'Street': parsed_address['street'],
            'Apt': parsed_address['apt_no'] if parsed_address['apt_no'] else 'EMPTY',
            'City': parsed_address['city'],
            'State': parsed_address['state'],
            'ZIP': parsed_address['zip']
        }
        
        for field, actual_value in address_fields.items():
            expected_value = expected.get(field, 'N/A')
            status = '✅ CORRECT' if actual_value == expected_value else f'❌ WRONG (expected: {expected_value})'
            print(f"   {field}: \"{actual_value}\" {status}")
        
        pdf_doc.close()
    else:
        print("   ❌ No forms found!")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_complete_fixes())

