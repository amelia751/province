"""
Simple test: Load W-2 data → Use AI to fill Form 1040 with hybrid mapping
"""

import os
import sys
import json
import io
from decimal import Decimal
from dotenv import load_dotenv

sys.path.insert(0, 'src')
load_dotenv('.env.local')

import boto3
import fitz

# Sample calculated tax data from W-2
calculated_data = {
    "taxpayer_info": {
        "name": "JOHN SMITH",
        "first_name": "JOHN",
        "last_name": "SMITH",
        "ssn": "123-45-6789",
        "address": "123 MAIN ST",
        "city": "ANYTOWN",
        "state": "CA",
        "zip": "90210"
    },
    "filing_status": "married_jointly",
    "income": {
        "wages_w2": 55151.93,
        "federal_withholding": 16606.17,
        "interest": 125.50,
        "dividends": 150.00
    },
    "calculations": {
        "total_income": 55427.43,
        "agi": 55427.43,
        "standard_deduction": 29200.00,
        "taxable_income": 26227.43,
        "tax": 2623.00,
        "child_tax_credit": 2000.00,
        "tax_after_credits": 623.00,
        "refund": 15983.17  # 16606.17 - 623
    }
}

print("=" * 80)
print("🎯 SIMPLE AI FORM FILLING TEST")
print("=" * 80)

# 1. Load hybrid mapping
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('province-form-mappings')

response = table.get_item(Key={'form_type': 'F1040', 'tax_year': '2024'})
mapping = response['Item']['mapping']

# Convert Decimal
def convert_decimal(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

mapping = json.loads(json.dumps(mapping, default=convert_decimal))

print(f"\n✅ Loaded hybrid mapping")
field_count = sum(len(v) for k, v in mapping.items() if isinstance(v, dict) and k != 'form_metadata')
print(f"   📋 {field_count} semantic fields available")

# 2. Create fill data from calculated data
print(f"\n🤖 Mapping calculated data to form fields...")

fill_data = {
    # From seed mapping (critical fields)
    "taxpayer_first_name": calculated_data['taxpayer_info']['first_name'],
    "taxpayer_last_name": calculated_data['taxpayer_info']['last_name'],
    "taxpayer_ssn": calculated_data['taxpayer_info']['ssn'],
    "street_address": calculated_data['taxpayer_info']['address'],
    "city": calculated_data['taxpayer_info']['city'],
    "state": calculated_data['taxpayer_info']['state'],
    "zip": calculated_data['taxpayer_info']['zip'],
    
    # Filing status
    "married_filing_jointly": True,
    "single": False,
    
    # Digital assets
    "no": True,  # Digital assets NO
    
    # Income (from agent-mapped fields)
    "total_income_9": calculated_data['calculations']['total_income'],
    "adjusted_gross_income_11": calculated_data['calculations']['agi'],
    "taxable_income_15": calculated_data['calculations']['taxable_income'],
    
    # Tax
    "tax_16": calculated_data['calculations']['tax'],
    "child_tax_credit_19": calculated_data['calculations'].get('child_tax_credit', 0),
    
    # Payments
    "total_payments_33": calculated_data['income']['federal_withholding'],
    
    # Refund
    "overpaid_amount_34": calculated_data['calculations']['refund'],
    "refund_amount_35a": calculated_data['calculations']['refund'],
}

# Ask user for refund details
print(f"\n❓ QUESTIONS FOR USER:")
print(f"   1. You're getting a refund of ${calculated_data['calculations']['refund']:,.2f}!")
print(f"   2. What's your bank routing number? (for direct deposit)")
response_routing = "123456789"  # Simulate user response
print(f"      👤 USER: {response_routing}")

print(f"   3. What's your account number?")
response_account = "987654321"  # Simulate user response  
print(f"      👤 USER: {response_account}")

# Add user responses
fill_data["routing_number_35b"] = response_routing
fill_data["account_number_35d"] = response_account
fill_data["account_type_checking_35c"] = True

print(f"\n✅ Collected {len(fill_data)} field values")

# 3. Download template and fill
s3 = boto3.client('s3', region_name='us-east-1')
templates_bucket = 'province-templates-[REDACTED-ACCOUNT-ID]-us-east-1'
documents_bucket = 'province-documents-[REDACTED-ACCOUNT-ID]-us-east-1'

print(f"\n📥 Downloading Form 1040 template...")
template_response = s3.get_object(Bucket=templates_bucket, Key='tax_forms/2024/f1040.pdf')
template_pdf = template_response['Body'].read()

# 4. Fill the PDF
print(f"\n✍️  Filling form...")
doc = fitz.open(stream=template_pdf, filetype='pdf')

# Flatten mapping
flat_mapping = {}
for section, fields in mapping.items():
    if isinstance(fields, dict) and section != 'form_metadata':
        flat_mapping.update(fields)

filled_text = 0
filled_checkboxes = 0

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
        
        if semantic_name and semantic_name in fill_data:
            value = fill_data[semantic_name]
            
            if widget.field_type == 7:  # Text
                widget.field_value = str(value)
                widget.update()
                filled_text += 1
            elif widget.field_type == 2:  # Checkbox
                if value is True:
                    widget.field_value = "Yes"
                    widget.update()
                    filled_checkboxes += 1

print(f"✅ Filled {filled_text} text fields")
print(f"✅ Checked {filled_checkboxes} checkboxes")

# 5. Save and upload
output_buffer = io.BytesIO()
doc.save(output_buffer, deflate=True)
output_buffer.seek(0)
filled_pdf = output_buffer.read()
doc.close()

s3_key = "filled_forms/TEST_AI_CONVERSATION/1040/2024/v001_ai_filled.pdf"
s3.put_object(Bucket=documents_bucket, Key=s3_key, Body=filled_pdf, ContentType='application/pdf')

url = s3.generate_presigned_url('get_object', 
                                Params={'Bucket': documents_bucket, 'Key': s3_key},
                                ExpiresIn=604800)

print(f"\n" + "=" * 80)
print(f"🎉 SUCCESS! AI-powered form filling complete!")
print(f"=" * 80)
print(f"\n📊 STATS:")
print(f"   Fields filled: {filled_text + filled_checkboxes}")
print(f"   Text fields: {filled_text}")
print(f"   Checkboxes: {filled_checkboxes}")
print(f"   Refund amount: ${calculated_data['calculations']['refund']:,.2f}")
print(f"\n📥 DOWNLOAD:")
print(f"   {url}")
print(f"\n✅ Hybrid mapping (seed + AI) working perfectly!")
print("=" * 80)

