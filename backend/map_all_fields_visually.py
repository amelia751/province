#!/usr/bin/env python3
"""
Visual Field Mapping Tool

Fills each field with its own field name so we can visually see which field is which
"""

import os
from dotenv import load_dotenv
import boto3
import fitz

load_dotenv('.env.local')

# Download template
s3 = boto3.client('s3', region_name='us-east-1')
bucket = os.getenv('TEMPLATES_BUCKET_NAME')
key = 'tax_forms/2024/f1040.pdf'

response = s3.get_object(Bucket=bucket, Key=key)
pdf_bytes = response['Body'].read()

doc = fitz.open(stream=pdf_bytes, filetype='pdf')

filled_count = 0

# Fill each field with its own name
for page_num in range(len(doc)):
    page = doc[page_num]
    
    for widget in page.widgets():
        field_name = widget.field_name
        
        if widget.field_type == fitz.PDF_WIDGET_TYPE_TEXT:
            # Extract the field number (e.g., f1_32 from topmostSubform[0].Page1[0].f1_32[0])
            if 'f1_' in field_name or 'f2_' in field_name:
                # Extract just the f1_XX or f2_XX part
                import re
                match = re.search(r'(f[12]_\d+)', field_name)
                if match:
                    short_name = match.group(1)
                    widget.field_value = short_name
                    widget.update()
                    filled_count += 1
                    print(f"✅ {field_name} → {short_name}")

print(f"\n✅ Total fields labeled: {filled_count}")

# Save
output_bytes = doc.tobytes()
doc.close()

# Upload
output_key = 'filled_forms/VISUAL_MAPPING/1040_field_map_visual.pdf'
s3.put_object(
    Bucket=os.getenv('DOCUMENTS_BUCKET_NAME'),
    Key=output_key,
    Body=output_bytes,
    ContentType='application/pdf'
)

url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': os.getenv('DOCUMENTS_BUCKET_NAME'), 'Key': output_key},
    ExpiresIn=604800
)

print(f"\n📄 Visual Field Map:")
print(f"   {url}")
print("\n🎯 Now you can open this PDF and see exactly which field name (f1_32, f1_33, etc.) corresponds to which line!")

