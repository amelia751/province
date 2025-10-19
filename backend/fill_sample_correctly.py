#!/usr/bin/env python3
"""
Fill sample Form 1040 CORRECTLY by reading the actual semantic names from mapping.
"""

import json
import os
import boto3
import fitz
import re
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv('.env.local')


def decimal_to_number(obj):
    if isinstance(obj, list):
        return [decimal_to_number(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_number(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj


def get_mapping():
    """Get mapping from DynamoDB."""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('province-form-mappings')
    
    response = table.get_item(Key={'form_type': 'F1040', 'tax_year': '2024'})
    return decimal_to_number(response['Item']['mapping'])


def create_sample_data_from_mapping(mapping):
    """
    Create comprehensive sample data that exactly matches the semantic names in the mapping.
    This ensures we fill the RIGHT fields with the RIGHT data.
    """
    # First, collect all semantic field names
    semantic_fields = {}
    
    def collect_fields(obj, section=''):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and 'topmostSubform' in value:
                    semantic_fields[key] = (value, section)
                elif isinstance(value, dict):
                    collect_fields(value, key)
    
    collect_fields(mapping)
    
    print(f"📋 Found {len(semantic_fields)} semantic fields in mapping")
    print("\nSample semantic fields:")
    for i, (key, (field, section)) in enumerate(list(semantic_fields.items())[:10], 1):
        print(f"  {i}. {key} (from {section})")
    
    # Now create sample data matching these EXACT semantic names
    sample_data = {}
    
    for semantic_name in semantic_fields.keys():
        # Determine appropriate value based on semantic name
        name_lower = semantic_name.lower()
        
        # Personal info
        if 'first_name' in name_lower and 'spouse' not in name_lower:
            sample_data[semantic_name] = 'JOHN'
        elif 'last_name' in name_lower and 'spouse' not in name_lower:
            sample_data[semantic_name] = 'SMITH'
        elif 'ssn' in name_lower and 'spouse' not in name_lower:
            sample_data[semantic_name] = '123-45-6789'
        elif 'spouse' in name_lower:
            sample_data[semantic_name] = ''  # Single filer
        
        # Address
        elif 'street' in name_lower or 'address' in name_lower:
            sample_data[semantic_name] = '123 MAIN STREET'
        elif 'apt' in name_lower or 'apartment' in name_lower:
            sample_data[semantic_name] = 'APT 4B'
        elif 'city' in name_lower:
            sample_data[semantic_name] = 'ANYTOWN'
        elif 'state' in name_lower and 'foreign' not in name_lower:
            sample_data[semantic_name] = 'CA'
        elif 'zip' in name_lower or 'postal' in name_lower:
            sample_data[semantic_name] = '90210'
        
        # Filing status checkboxes
        elif 'filing_status' in name_lower:
            sample_data[semantic_name] = 'single' in name_lower  # True for single, False for others
        
        # Digital assets checkboxes
        elif 'digital' in name_lower:
            sample_data[semantic_name] = 'no' in name_lower  # True for no, False for yes
        
        # Income fields - use realistic amounts
        elif 'wage' in name_lower and 'line' in name_lower:
            sample_data[semantic_name] = 55151.93
        elif 'interest' in name_lower and ('tax' in name_lower and 'exempt' in name_lower):
            sample_data[semantic_name] = 0
        elif 'interest' in name_lower and 'taxable' in name_lower:
            sample_data[semantic_name] = 125.50
        elif 'dividend' in name_lower and 'qualified' in name_lower:
            sample_data[semantic_name] = 75.00
        elif 'dividend' in name_lower and 'ordinary' in name_lower:
            sample_data[semantic_name] = 150.00
        elif 'capital' in name_lower and 'gain' in name_lower:
            sample_data[semantic_name] = 500.00
        elif 'agi' in name_lower or ('adjusted' in name_lower and 'gross' in name_lower):
            sample_data[semantic_name] = 56002.43
        elif 'total_income' in name_lower:
            sample_data[semantic_name] = 56002.43
        elif 'standard_deduction' in name_lower or ('deduction' in name_lower and 'standard' in name_lower):
            sample_data[semantic_name] = 14600.00
        elif 'taxable_income' in name_lower:
            sample_data[semantic_name] = 41402.43
        
        # Tax fields
        elif 'tax' in name_lower and 'line' in name_lower and 'total' not in name_lower:
            sample_data[semantic_name] = 4736.25
        elif 'total_tax' in name_lower:
            sample_data[semantic_name] = 4736.25
        
        # Payments
        elif 'withholding' in name_lower or 'withheld' in name_lower:
            if 'total' in name_lower:
                sample_data[semantic_name] = 16606.17
            else:
                sample_data[semantic_name] = 16606.17
        elif 'total_payment' in name_lower or ('payment' in name_lower and 'total' in name_lower):
            sample_data[semantic_name] = 16606.17
        
        # Refund
        elif 'overpay' in name_lower or 'overpaid' in name_lower:
            sample_data[semantic_name] = 11869.92
        elif 'refund' in name_lower and 'amount' in name_lower:
            sample_data[semantic_name] = 11869.92
        elif 'routing' in name_lower:
            sample_data[semantic_name] = '123456789'
        elif 'account' in name_lower and 'number' in name_lower:
            sample_data[semantic_name] = '987654321'
        elif 'account_type' in name_lower and 'checking' in name_lower:
            sample_data[semantic_name] = True
        elif 'account_type' in name_lower and 'saving' in name_lower:
            sample_data[semantic_name] = False
        
        # Default zeros for any remaining numeric fields
        elif any(word in name_lower for word in ['line', 'amount', 'credit', 'deduction', 'adjustment']):
            if semantic_name not in sample_data:
                sample_data[semantic_name] = 0
    
    print(f"\n✅ Created sample data for {len(sample_data)} fields")
    return sample_data, semantic_fields


def fill_form_correctly():
    """Fill form using EXACT semantic name matching."""
    print("\n🎯 FILLING FORM 1040 CORRECTLY")
    print("="*80)
    
    # Get mapping
    mapping = get_mapping()
    print(f"✅ Loaded mapping from DynamoDB")
    
    # Create sample data that matches semantic names
    sample_data, semantic_fields = create_sample_data_from_mapping(mapping)
    
    # Download template
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket = os.getenv('TEMPLATES_BUCKET_NAME')
    
    response = s3.get_object(Bucket=bucket, Key='tax_forms/2024/f1040.pdf')
    pdf_bytes = response['Body'].read()
    print(f"✅ Downloaded template PDF")
    
    # Open PDF
    doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    
    # Build fill map: PDF field name -> (semantic name, value)
    fill_map = {}
    for semantic_name, (pdf_field_name, section) in semantic_fields.items():
        if semantic_name in sample_data:
            fill_map[pdf_field_name] = (semantic_name, sample_data[semantic_name])
    
    print(f"✅ Prepared fill map for {len(fill_map)} fields")
    
    # Fill all fields
    filled_count = 0
    checkbox_count = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        for widget in page.widgets():
            field_name = widget.field_name
            
            if field_name in fill_map:
                semantic_name, value = fill_map[field_name]
                
                try:
                    if widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                        # Boolean value for checkboxes
                        is_checked = bool(value) if isinstance(value, bool) else False
                        widget.field_value = is_checked
                        widget.update()
                        checkbox_count += 1
                        status = "✓" if is_checked else "☐"
                        print(f"   {status} {semantic_name}")
                        
                    elif widget.field_type == fitz.PDF_WIDGET_TYPE_TEXT:
                        # Text or numeric value
                        if value is not None and value != '' and value != 0:
                            if isinstance(value, (int, float)):
                                widget.field_value = f"{value:,.2f}"
                            else:
                                widget.field_value = str(value).upper()
                            
                            widget.update()
                            filled_count += 1
                            display = str(value) if len(str(value)) < 40 else str(value)[:40] + "..."
                            print(f"   ✓ {semantic_name}: {display}")
                except Exception as e:
                    print(f"   ⚠️  {semantic_name}: {e}")
    
    print(f"\n✅ Filled {filled_count} text fields")
    print(f"✅ Set {checkbox_count} checkboxes")
    print(f"✅ Total: {filled_count + checkbox_count} fields")
    
    # Save
    output_bytes = doc.tobytes()
    doc.close()
    
    # Upload to S3
    docs_bucket = os.getenv('DOCUMENTS_BUCKET_NAME')
    key = 'filled_forms/SAMPLE_CORRECT/1040/2024/v001_correctly_mapped.pdf'
    
    s3.put_object(
        Bucket=docs_bucket,
        Key=key,
        Body=output_bytes,
        ContentType='application/pdf'
    )
    
    # Generate URL
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': docs_bucket, 'Key': key},
        ExpiresIn=604800
    )
    
    print(f"\n📄 CORRECTLY FILLED FORM:")
    print(f"   Location: s3://{docs_bucket}/{key}")
    print(f"\n🔗 VIEW LINK (expires in 7 days):")
    print(f"   {url}")
    print("\n" + "="*80)
    print("✅ DONE! This form uses EXACT semantic name matching.")
    print("="*80)


if __name__ == "__main__":
    fill_form_correctly()

