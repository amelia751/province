#!/usr/bin/env python3
"""
Fill comprehensive sample Form 1040 using DynamoDB mapping.
This will fill ALL mapped fields to demonstrate coverage.
"""

import json
import os
import boto3
import fitz
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


def fill_sample_form():
    """Fill sample form with comprehensive data."""
    print("\n🚀 FILLING COMPREHENSIVE SAMPLE FORM")
    print("="*80)
    
    # Get mapping
    mapping = get_mapping()
    print(f"✅ Loaded mapping from DynamoDB")
    
    # Download template
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket = os.getenv('TEMPLATES_BUCKET_NAME')
    
    response = s3.get_object(Bucket=bucket, Key='tax_forms/2024/f1040.pdf')
    pdf_bytes = response['Body'].read()
    print(f"✅ Downloaded template PDF")
    
    # Open PDF
    doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    
    # Comprehensive sample data - fills EVERY mapped field
    sample_data = {
        # Personal info
        'taxpayer_first_name': 'John A.',
        'taxpayer_last_name': 'Smith',
        'taxpayer_ssn': '123-45-6789',
        'spouse_first_name': '',  # Single filer
        'spouse_last_name': '',
        'spouse_ssn': '',
        
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
        
        # Income - ALL lines including zeros
        'wages': 55151.93,
        'tax_exempt_interest': 0,
        'taxable_interest': 125.50,
        'qualified_dividends': 75.00,
        'ordinary_dividends': 150.00,
        'ira_gross': 0,
        'ira_taxable': 0,
        'pensions_gross': 0,
        'pensions_taxable': 0,
        'social_security_gross': 0,
        'social_security_taxable': 0,
        'capital_gains': 500.00,
        'schedule_1': 0,
        'total_income': 56002.43,
        'adjustments': 0,
        'agi': 56002.43,
        'standard_deduction': 14600.00,
        'qbi_deduction': 0,
        'total_deductions': 14600.00,
        'taxable_income': 41402.43,
        
        # Tax and credits
        'tax': 4736.25,
        'schedule_2_tax': 0,
        'total_tax_before_credits': 4736.25,
        'child_tax_credit': 0,
        'schedule_3_credits': 0,
        'total_credits': 0,
        'tax_after_credits': 4736.25,
        'other_taxes': 0,
        'total_tax': 4736.25,
        
        # Payments
        'federal_withholding': 16606.17,
        'federal_withholding_other_b': 0,
        'federal_withholding_other_c': 0,
        'total_withholding': 16606.17,
        'estimated_tax': 0,
        'eic': 0,
        'additional_child_tax': 0,
        'american_opportunity': 0,
        'reserved': 0,
        'schedule_3_payments': 0,
        'total_other_payments': 0,
        'total_payments': 16606.17,
        
        # Refund
        'overpayment': 11869.92,
        'refund': 11869.92,
        'routing_number': '123456789',
        'account_number': '987654321',
        'account_type': 'checking',
        'apply_to_next_year': 0,
        'amount_owed': 0,
    }
    
    # Build field fill map from mapping
    fill_map = {}
    
    def extract_mappings(obj, data_dict):
        """Recursively extract field mappings."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and 'topmostSubform' in value:
                    # This is a field mapping - find corresponding data
                    for data_key, data_value in data_dict.items():
                        if data_key.lower().replace('_', '') in key.lower().replace('_', ''):
                            fill_map[value] = (key, data_value)
                            break
                elif isinstance(value, (dict, list)):
                    extract_mappings(value, data_dict)
        elif isinstance(obj, list):
            for item in obj:
                extract_mappings(item, data_dict)
    
    extract_mappings(mapping, sample_data)
    
    print(f"✅ Prepared fill data for {len(fill_map)} fields")
    
    # Fill all fields
    filled_count = 0
    checkbox_count = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        for widget in page.widgets():
            field_name = widget.field_name
            
            if field_name in fill_map:
                semantic_key, value = fill_map[field_name]
                
                try:
                    if widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                        # Handle checkboxes
                        is_checked = False
                        if 'filing_status' in semantic_key:
                            is_checked = sample_data.get('filing_status', '') in semantic_key
                        elif 'digital_assets' in semantic_key:
                            is_checked = ('yes' in semantic_key and sample_data.get('digital_assets') == 'yes') or \
                                       ('no' in semantic_key and sample_data.get('digital_assets') == 'no')
                        
                        widget.field_value = is_checked
                        widget.update()
                        checkbox_count += 1
                        
                    elif widget.field_type == fitz.PDF_WIDGET_TYPE_TEXT:
                        # Handle text fields
                        if value is not None:
                            if isinstance(value, (int, float)) and value != 0:
                                widget.field_value = f"{value:,.2f}"
                            elif value == 0:
                                widget.field_value = "0"
                            else:
                                widget.field_value = str(value).upper()
                            
                            widget.update()
                            filled_count += 1
                except Exception as e:
                    print(f"⚠️  Could not fill {field_name}: {e}")
    
    print(f"\n✅ Filled {filled_count} text fields")
    print(f"✅ Set {checkbox_count} checkboxes")
    print(f"✅ Total: {filled_count + checkbox_count} fields")
    
    # Save filled PDF
    output_bytes = doc.tobytes()
    doc.close()
    
    # Upload to S3
    docs_bucket = os.getenv('DOCUMENTS_BUCKET_NAME')
    key = 'filled_forms/SAMPLE_COMPREHENSIVE/1040/2024/v001_complete_mapping_test.pdf'
    
    s3.put_object(
        Bucket=docs_bucket,
        Key=key,
        Body=output_bytes,
        ContentType='application/pdf'
    )
    
    # Generate presigned URL
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': docs_bucket, 'Key': key},
        ExpiresIn=604800  # 7 days
    )
    
    print(f"\n📄 SAMPLE FORM FILLED!")
    print(f"   Location: s3://{docs_bucket}/{key}")
    print(f"\n🔗 VIEW LINK (expires in 7 days):")
    print(f"   {url}")
    print("\n" + "="*80)
    print("✅ COMPLETE! Examine the PDF to verify all mapped fields are filled.")
    print("="*80)


if __name__ == "__main__":
    fill_sample_form()

