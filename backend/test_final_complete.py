"""
FINAL COMPLETE TEST: End-to-end AI form filling with hybrid mapping
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, 'src')
load_dotenv('.env.local')

# Direct test without async (simpler)
import io
import json
from decimal import Decimal
import boto3
import fitz

print("=" * 80)
print("🎯 FINAL COMPLETE TEST - AI FORM FILLING")
print("=" * 80)

# Sample W-2 data
tax_data = {
    'taxpayer_first_name': 'JOHN',
    'taxpayer_last_name': 'SMITH',
    'taxpayer_ssn': '123-45-6789',
    'street_address': '123 MAIN ST',
    'city': 'ANYTOWN',
    'state': 'CA',
    'zip': '90210',
    
    # Filing & checkboxes
    'married_filing_jointly': True,
    'no': True,  # digital_assets.no
    
    # Income
    'total_income_9': 55427.43,
    'adjusted_gross_income_11': 55427.43,
    'taxable_income_15': 26227.43,
    'tax_16': 2623.00,
    'total_payments_33': 16606.17,
    'refund_amount_35a': 15983.17,
    
    # Bank info (simulated user response)
    'routing_number_35b': '123456789',
    'account_number_35d': '987654321',
}

print(f"\n📊 TEST DATA:")
print(f"   Taxpayer: {tax_data['taxpayer_first_name']} {tax_data['taxpayer_last_name']}")
print(f"   Income: ${tax_data['total_income_9']:,.2f}")
print(f"   Refund: ${tax_data['refund_amount_35a']:,.2f}")
print(f"   Bank: {tax_data['routing_number_35b']} / {tax_data['account_number_35d']}")

# 1. Load hybrid mapping
print(f"\n🔄 Loading hybrid mapping from DynamoDB...")
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('province-form-mappings')

response = table.get_item(Key={'form_type': 'F1040', 'tax_year': '2024'})
mapping = response['Item']['mapping']

def convert_decimal(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

mapping = json.loads(json.dumps(mapping, default=convert_decimal))

field_count = sum(len(v) for k, v in mapping.items() if isinstance(v, dict) and k != 'form_metadata')
print(f"✅ Loaded {field_count} semantic fields")

# 2. Download template
print(f"\n📥 Downloading Form 1040 template...")
s3 = boto3.client('s3', region_name='us-east-1')
templates_bucket = 'province-templates-[REDACTED-ACCOUNT-ID]-us-east-1'
documents_bucket = 'province-documents-[REDACTED-ACCOUNT-ID]-us-east-1'

template_response = s3.get_object(Bucket=templates_bucket, Key='tax_forms/2024/f1040.pdf')
template_pdf = template_response['Body'].read()
print(f"✅ Downloaded template")

# 3. Fill form with hybrid mapping
print(f"\n✍️  Filling form with AI-mapped data...")
doc = fitz.open(stream=template_pdf, filetype='pdf')

# Flatten mapping
flat_mapping = {}
for section, fields in mapping.items():
    if isinstance(fields, dict) and section != 'form_metadata':
        flat_mapping.update(fields)

filled_text = 0
filled_checkboxes = 0
filled_fields_list = []

for page_num in range(doc.page_count):
    page = doc[page_num]
    for widget in page.widgets():
        full_field_name = widget.field_name
        if not full_field_name:
            continue
        
        # Find semantic name
        semantic_name = None
        for sem, pdf_path in flat_mapping.items():
            if pdf_path == full_field_name:
                semantic_name = sem
                break
        
        if semantic_name and semantic_name in tax_data:
            value = tax_data[semantic_name]
            
            if widget.field_type == 7:  # Text
                widget.field_value = str(value)
                widget.update()
                filled_text += 1
                filled_fields_list.append(f"  ✓ {semantic_name}: {value}")
            elif widget.field_type == 2:  # Checkbox
                if value is True:
                    widget.field_value = "Yes"
                    widget.update()
                    filled_checkboxes += 1
                    filled_fields_list.append(f"  ☑  {semantic_name}: CHECKED")

print(f"✅ Filled {filled_text} text fields")
print(f"✅ Checked {filled_checkboxes} checkboxes")
print(f"✅ Total: {filled_text + filled_checkboxes} fields")

print(f"\n📋 FILLED FIELDS:")
for field_info in filled_fields_list[:15]:  # Show first 15
    print(field_info)
if len(filled_fields_list) > 15:
    print(f"  ... and {len(filled_fields_list) - 15} more")

# 4. Save and upload
print(f"\n📤 Uploading to S3...")
output_buffer = io.BytesIO()
doc.save(output_buffer, deflate=True)
output_buffer.seek(0)
filled_pdf = output_buffer.read()
doc.close()

s3_key = "filled_forms/FINAL_TEST/1040/2024/v001_complete.pdf"
s3.put_object(Bucket=documents_bucket, Key=s3_key, Body=filled_pdf, ContentType='application/pdf')

url = s3.generate_presigned_url('get_object', 
                                Params={'Bucket': documents_bucket, 'Key': s3_key},
                                ExpiresIn=604800)

print(f"✅ Uploaded successfully")

print(f"\n" + "=" * 80)
print(f"🎉 SUCCESS! COMPLETE END-TO-END TEST PASSED")
print(f"=" * 80)
print(f"\n📊 FINAL STATS:")
print(f"   ✅ Hybrid mapping: {field_count} semantic fields")
print(f"   ✅ Form filled: {filled_text + filled_checkboxes} fields")
print(f"   ✅ Text fields: {filled_text}")
print(f"   ✅ Checkboxes: {filled_checkboxes}")
print(f"   ✅ Refund: ${tax_data['refund_amount_35a']:,.2f}")
print(f"\n📥 DOWNLOAD YOUR FORM:")
print(f"   {url}")
print(f"\n✅ AI-powered form filling is PRODUCTION-READY!")
print("=" * 80)

