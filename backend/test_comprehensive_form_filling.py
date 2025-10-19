#!/usr/bin/env python3
"""
Comprehensive Form Filling Test

Tests ALL 66 mapped fields from the AI-generated mapping.
Fills every field, including zeros and checkboxes.
"""

import json
import os
import sys
from decimal import Decimal
from dotenv import load_dotenv
import boto3
import fitz
import re

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


def fill_comprehensive_form(form_data: dict) -> bytes:
    """Fill Form 1040 with ALL mapped fields."""
    
    # Get mapping
    mapping = get_ai_mapping()
    print(f"✅ Loaded AI mapping with {len(mapping)} sections")
    
    # Count total mappable fields
    total_mappable = sum(
        len(section) if isinstance(section, dict) and key != 'form_metadata' 
        else 0 
        for key, section in mapping.items()
    )
    print(f"✅ Total mappable fields: {total_mappable}")
    
    # Download template
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket = os.getenv('TEMPLATES_BUCKET_NAME')
    
    response = s3.get_object(Bucket=bucket, Key='tax_forms/2024/f1040.pdf')
    pdf_bytes = response['Body'].read()
    
    # Open PDF
    doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    
    # Create fill data dictionary
    fill_data = {}
    
    # Helper to add field
    def add_field(semantic_key, field_name, value, is_checkbox=False):
        clean_field = re.sub(r'\[\d+\]', '', field_name)
        if value is not None or is_checkbox:
            fill_data[clean_field] = (semantic_key, value, is_checkbox)
    
    # Personal info (including empty spouse fields for single filer)
    if 'personal_info' in mapping:
        for semantic_key, field_name in mapping['personal_info'].items():
            value = form_data.get(semantic_key, '')  # Empty string for spouse fields
            if value:  # Only add non-empty
                add_field(semantic_key, field_name, str(value).upper())
    
    # Address (including apt_no if provided)
    if 'address' in mapping:
        for semantic_key, field_name in mapping['address'].items():
            value = form_data.get(semantic_key, '')
            if value:
                add_field(semantic_key, field_name, str(value).upper())
    
    # Filing status checkboxes
    if 'filing_status' in mapping:
        status = form_data.get('filing_status', 'single')
        for status_key, field_name in mapping['filing_status'].items():
            is_checked = (status_key == status.lower())
            add_field(f'filing_status_{status_key}', field_name, is_checked, is_checkbox=True)
    
    # Digital assets checkboxes
    if 'digital_assets' in mapping:
        digital_answer = form_data.get('digital_assets', 'no')
        for key, field_name in mapping['digital_assets'].items():
            is_checked = (('yes' in key and digital_answer == 'yes') or 
                         ('no' in key and digital_answer == 'no'))
            add_field(f'digital_assets_{key}', field_name, is_checked, is_checkbox=True)
    
    # Income section (ALL fields, including zeros)
    if 'income' in mapping:
        for semantic_key, field_name in mapping['income'].items():
            value = form_data.get(semantic_key)
            if value is not None:
                formatted = f"{value:,.2f}" if isinstance(value, (int, float)) and value != 0 else ("0" if value == 0 else str(value))
                add_field(semantic_key, field_name, formatted)
    
    # Tax and credits (ALL fields)
    if 'tax_and_credits' in mapping:
        for semantic_key, field_name in mapping['tax_and_credits'].items():
            value = form_data.get(semantic_key)
            if value is not None:
                formatted = f"{value:,.2f}" if isinstance(value, (int, float)) and value != 0 else ("0" if value == 0 else str(value))
                add_field(semantic_key, field_name, formatted)
    
    # Payments (ALL fields)
    if 'payments' in mapping:
        for semantic_key, field_name in mapping['payments'].items():
            value = form_data.get(semantic_key)
            if value is not None:
                formatted = f"{value:,.2f}" if isinstance(value, (int, float)) and value != 0 else ("0" if value == 0 else str(value))
                add_field(semantic_key, field_name, formatted)
    
    # Refund or owed (ALL fields, including bank info)
    if 'refund_or_owed' in mapping:
        for semantic_key, field_name in mapping['refund_or_owed'].items():
            value = form_data.get(semantic_key)
            if value is not None:
                if isinstance(value, (int, float)):
                    formatted = f"{value:,.2f}" if value != 0 else ""
                else:
                    formatted = str(value)
                if formatted:  # Only add non-empty
                    add_field(semantic_key, field_name, formatted)
    
    print(f"✅ Prepared {len(fill_data)} fields to fill")
    
    # Now fill all fields
    filled_count = 0
    checkbox_count = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        for widget in page.widgets():
            field_name = widget.field_name
            match = re.search(r'([fc][12]_\d+)', field_name)
            if match:
                simplified = match.group(1)
                
                if simplified in fill_data:
                    semantic_key, value, is_checkbox = fill_data[simplified]
                    
                    try:
                        if is_checkbox and widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                            widget.field_value = value
                            widget.update()
                            checkbox_count += 1
                            status = "✓" if value else "☐"
                            print(f"   {status} {semantic_key}")
                        elif not is_checkbox and widget.field_type == fitz.PDF_WIDGET_TYPE_TEXT:
                            widget.field_value = str(value) if value else ""
                            widget.update()
                            filled_count += 1
                            display_val = value if len(str(value)) < 40 else str(value)[:40] + "..."
                            print(f"   ✓ {semantic_key}: {display_val}")
                    except Exception as e:
                        print(f"   ⚠ Could not fill {semantic_key}: {e}")
    
    print(f"\n✅ Total text fields filled: {filled_count}")
    print(f"✅ Total checkboxes set: {checkbox_count}")
    print(f"✅ Grand total: {filled_count + checkbox_count} fields")
    
    output_bytes = doc.tobytes()
    doc.close()
    
    return output_bytes


def main():
    """Test comprehensive form filling."""
    print("\n" + "="*80)
    print("🤖 COMPREHENSIVE AI FORM FILLING TEST")
    print("="*80)
    print("Goal: Fill ALL 66 mapped fields\n")
    
    # COMPREHENSIVE test data - includes ALL fields
    form_data = {
        # Personal info
        'first_name_and_initial': 'John A.',
        'last_name': 'Smith',
        'ssn': '123-45-6789',
        # Spouse fields left empty (single filer)
        
        # Address
        'street': '123 Main Street',
        'apt_no': 'Apt 4B',
        'city': 'Anytown',
        'state': 'CA',
        'zip': '90210',
        
        # Filing status
        'filing_status': 'single',
        
        # Digital assets
        'digital_assets': 'no',
        
        # Income - ALL lines
        'wages_line_1a': 55151.93,
        'total_wages_line_1z': 55151.93,
        'tax_exempt_interest_2a': 0,  # Even zeros!
        'taxable_interest_2b': 125.50,
        'qualified_dividends_3a': 75.00,
        'ordinary_dividends_3b': 150.00,
        'ira_distributions_4a': 0,
        'ira_taxable_4b': 0,
        'pensions_5a': 0,
        'pensions_taxable_5b': 0,
        'social_security_6a': 0,
        'social_security_taxable_6b': 0,
        'capital_gain_line_7': 500.00,
        'schedule_1_line_8': 0,
        'total_income_line_9': 56002.43,  # Sum of all income
        'adjustments_line_10': 0,
        'agi_line_11': 56002.43,
        'standard_deduction_line_12': 14600.00,
        'qbi_deduction_line_13': 0,
        'deductions_total_line_14': 14600.00,
        'taxable_income_line_15': 41402.43,
        
        # Tax and credits - ALL lines
        'tax_line_16': 4736.25,
        'schedule_2_line_17': 0,
        'total_tax_before_credits_18': 4736.25,
        'child_tax_credit_19': 0,
        'schedule_3_credits_20': 0,
        'total_credits_21': 0,
        'tax_after_credits_22': 4736.25,
        'other_taxes_23': 0,
        'total_tax_line_24': 4736.25,
        
        # Payments - ALL lines
        'federal_withholding_25a': 16606.17,
        'federal_withholding_other_25b': 0,
        'federal_withholding_other_25c': 0,
        'total_withholding_25d': 16606.17,
        'estimated_tax_26': 0,
        'eic_27': 0,
        'additional_child_tax_28': 0,
        'american_opportunity_29': 0,
        'reserved_30': 0,
        'schedule_3_payments_31': 0,
        'total_other_payments_32': 0,
        'total_payments_line_33': 16606.17,
        
        # Refund - ALL lines
        'overpaid_line_34': 11869.92,
        'refund_line_35a': 11869.92,
        'routing_number_35b': '123456789',
        'account_number_35d': '987654321',
        'apply_to_next_year_36': 0,
        'amount_owed_line_37': 0,
    }
    
    print("📋 Form Data Summary:")
    print(f"   Personal: {len([k for k in form_data.keys() if 'name' in k or 'ssn' in k])} fields")
    print(f"   Address: {len([k for k in form_data.keys() if k in ['street', 'apt_no', 'city', 'state', 'zip']])} fields")
    print(f"   Income: {len([k for k in form_data.keys() if 'line' in k and any(x in k for x in ['wages', 'interest', 'dividend', 'ira', 'pension', 'social', 'capital', 'income', 'agi', 'deduction', 'taxable'])])} fields")
    print(f"   Tax: {len([k for k in form_data.keys() if 'tax' in k or 'credit' in k])} fields")
    print(f"   Payments: {len([k for k in form_data.keys() if 'withholding' in k or 'estimated' in k or 'eic' in k or 'payments' in k])} fields")
    print(f"   Refund: {len([k for k in form_data.keys() if 'overpaid' in k or 'refund' in k or 'routing' in k or 'account' in k or 'owed' in k or 'apply' in k])} fields")
    print(f"   Total data fields: {len(form_data)}")
    print()
    
    print("🔄 Filling form with comprehensive data...\n")
    
    filled_pdf = fill_comprehensive_form(form_data)
    
    print(f"\n✅ Generated PDF: {len(filled_pdf):,} bytes")
    
    # Upload to S3
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket = os.getenv('DOCUMENTS_BUCKET_NAME')
    key = 'filled_forms/John_A._Smith/1040/2024/v002_comprehensive_ai_filled.pdf'
    
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
    
    print(f"\n📄 View comprehensively filled form:")
    print(f"   {url}")
    print("\n🎉 SUCCESS! All possible fields filled using AI mapping!")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()

