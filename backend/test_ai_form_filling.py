#!/usr/bin/env python3
"""
Test Form Filling with AI-Generated Mapping

This tests that we can successfully fill Form 1040 using the AI-generated 
semantic mapping from DynamoDB.
"""

import json
import os
import sys
from decimal import Decimal
from dotenv import load_dotenv
import boto3
import fitz

sys.path.insert(0, 'src')

load_dotenv('.env.local')


def decimal_to_number(obj):
    """Convert DynamoDB Decimals to standard types."""
    if isinstance(obj, list):
        return [decimal_to_number(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_number(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj


def get_ai_mapping():
    """Retrieve AI-generated mapping from DynamoDB."""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('province-form-mappings')
    
    response = table.get_item(
        Key={'form_type': 'F1040', 'tax_year': '2024'}
    )
    
    if 'Item' not in response:
        raise ValueError("No mapping found for F1040-2024")
    
    return decimal_to_number(response['Item']['mapping'])


def fill_form_with_ai_mapping(form_data: dict) -> bytes:
    """Fill Form 1040 using AI-generated semantic mapping."""
    
    # Get mapping
    mapping = get_ai_mapping()
    print(f"✅ Loaded AI mapping with {len(mapping)} sections")
    
    # Download template
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket = os.getenv('TEMPLATES_BUCKET_NAME')
    
    response = s3.get_object(Bucket=bucket, Key='tax_forms/2024/f1040.pdf')
    pdf_bytes = response['Body'].read()
    
    # Open PDF
    doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    
    # Create mapping: semantic_key -> (field_name, value, is_checkbox)
    fill_data = {}
    
    # Collect all data to fill
    if 'personal_info' in mapping:
        for semantic_key, field_name in mapping['personal_info'].items():
            value = form_data.get(semantic_key)
            if value:
                clean_field = field_name.replace('[0]', '').replace('[1]', '').replace('[2]', '')
                fill_data[clean_field] = (semantic_key, str(value).upper(), False)
    
    if 'address' in mapping:
        for semantic_key, field_name in mapping['address'].items():
            value = form_data.get(semantic_key)
            if value:
                clean_field = field_name.replace('[0]', '').replace('[1]', '').replace('[2]', '')
                fill_data[clean_field] = (semantic_key, str(value).upper(), False)
    
    # Filing status
    if 'filing_status' in mapping:
        status = form_data.get('filing_status', 'single')
        status_field = mapping['filing_status'].get(status.lower())
        if status_field:
            clean_field = status_field.replace('[0]', '').replace('[1]', '').replace('[2]', '')
            fill_data[clean_field] = (f'filing_status_{status}', True, True)
    
    # Income, tax, payments, refund sections
    for section in ['income', 'tax_and_credits', 'payments', 'refund_or_owed']:
        if section in mapping:
            for semantic_key, field_name in mapping[section].items():
                value = form_data.get(semantic_key)
                if value is not None:
                    clean_field = field_name.replace('[0]', '').replace('[1]', '').replace('[2]', '')
                    formatted = f"{value:,.2f}" if isinstance(value, (int, float)) else str(value)
                    fill_data[clean_field] = (semantic_key, formatted, False)
    
    # Now fill all fields by iterating through pages
    import re
    filled_count = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        for widget in page.widgets():
            field_name = widget.field_name
            # Extract simplified name
            match = re.search(r'([fc][12]_\d+)', field_name)
            if match:
                simplified = match.group(1)
                
                if simplified in fill_data:
                    semantic_key, value, is_checkbox = fill_data[simplified]
                    
                    try:
                        if is_checkbox and widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                            widget.field_value = value
                            widget.update()
                            filled_count += 1
                            print(f"   ✓ {semantic_key}: checked")
                        elif not is_checkbox and widget.field_type == fitz.PDF_WIDGET_TYPE_TEXT:
                            widget.field_value = value
                            widget.update()
                            filled_count += 1
                            print(f"   ✓ {semantic_key}: {value}")
                    except Exception as e:
                        print(f"   ⚠ Could not fill {semantic_key}: {e}")
    
    print(f"\n✅ Total fields filled: {filled_count}")
    
    output_bytes = doc.tobytes()
    doc.close()
    
    return output_bytes


def main():
    """Test AI-powered form filling."""
    print("\n" + "="*80)
    print("🤖 AI-POWERED FORM FILLING TEST")
    print("="*80)
    print()
    
    # Test data with semantic field names
    form_data = {
        # Personal info
        'first_name_and_initial': 'John A.',
        'last_name': 'Smith',
        'ssn': '123-45-6789',
        
        # Address
        'street': '123 Main Street',
        'city': 'Anytown',
        'state': 'CA',
        'zip': '90210',
        
        # Filing status
        'filing_status': 'single',
        
        # Income
        'wages_line_1a': 55151.93,
        'total_wages_line_1z': 55151.93,
        'total_income_line_9': 55151.93,
        'agi_line_11': 55151.93,
        'standard_deduction_line_12': 14600.00,
        'taxable_income_line_15': 40551.93,
        
        # Tax
        'tax_line_16': 4634.23,
        'total_tax_line_24': 4634.23,
        
        # Payments
        'federal_withholding_25a': 16606.17,
        'total_withholding_25d': 16606.17,
        'total_payments_line_33': 16606.17,
        
        # Refund
        'overpaid_line_34': 11971.94,
        'refund_line_35a': 11971.94,
    }
    
    print("📋 Form Data:")
    for key, value in form_data.items():
        print(f"   {key}: {value}")
    print()
    
    print("🔄 Filling form using AI-generated mapping...")
    print()
    
    filled_pdf = fill_form_with_ai_mapping(form_data)
    
    print(f"\n✅ Generated PDF: {len(filled_pdf):,} bytes")
    
    # Upload to S3
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket = os.getenv('DOCUMENTS_BUCKET_NAME')
    key = 'filled_forms/John_A._Smith/1040/2024/v001_ai_filled.pdf'
    
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=filled_pdf,
        ContentType='application/pdf'
    )
    
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': key},
        ExpiresIn=604800
    )
    
    print(f"\n📄 View AI-filled form:")
    print(f"   {url}")
    print("\n🎉 SUCCESS! Form filled using AI-generated semantic mapping!")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()

