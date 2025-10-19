#!/usr/bin/env python3
"""
Extract AcroForm Fields from PDF

Uses PyMuPDF to enumerate all form fields with their names, types, positions, and labels.
"""

import json
import sys
import os
from dotenv import load_dotenv
import boto3
import fitz  # PyMuPDF
import tempfile

sys.path.insert(0, 'src')

load_dotenv('.env.local')


def extract_form_fields(pdf_path_or_bytes):
    """Extract all AcroForm fields from a PDF."""
    
    # Open PDF
    if isinstance(pdf_path_or_bytes, bytes):
        doc = fitz.open(stream=pdf_path_or_bytes, filetype="pdf")
    else:
        doc = fitz.open(pdf_path_or_bytes)
    
    all_fields = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Get all widgets (form fields) on this page
        widgets = page.widgets()
        
        for widget in widgets:
            field_info = {
                'field_name': widget.field_name,
                'field_type': widget.field_type_string,
                'field_value': widget.field_value,
                'page_number': page_num + 1,
                'rect': {
                    'x0': widget.rect.x0,
                    'y0': widget.rect.y0,
                    'x1': widget.rect.x1,
                    'y1': widget.rect.y1,
                    'width': widget.rect.width,
                    'height': widget.rect.height
                },
                'field_label': widget.field_label or "",
                'field_flags': widget.field_flags,
                'choice_values': widget.choice_values if hasattr(widget, 'choice_values') else None,
            }
            
            # Try to extract nearby text labels (for context)
            # Get text near the field
            field_rect = widget.rect
            # Expand rect slightly to capture labels
            search_rect = fitz.Rect(
                field_rect.x0 - 200,  # Look 200 points to the left
                field_rect.y0 - 10,   # Look 10 points up
                field_rect.x0,         # To the left edge of field
                field_rect.y1 + 10    # And 10 points down
            )
            
            nearby_text = page.get_text("text", clip=search_rect).strip()
            if nearby_text:
                # Clean up the text
                nearby_text = ' '.join(nearby_text.split())
                if len(nearby_text) > 100:
                    nearby_text = nearby_text[:100] + "..."
                field_info['nearby_label'] = nearby_text
            
            all_fields.append(field_info)
    
    doc.close()
    
    return all_fields


def main():
    """Extract fields from Form 1040 template."""
    
    print("🔍 Extracting AcroForm fields from Form 1040...")
    
    # Download template from S3
    s3 = boto3.client(
        's3',
        region_name='us-east-1',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    bucket = os.getenv('TEMPLATES_BUCKET_NAME')
    key = 'tax_forms/2024/f1040.pdf'
    
    print(f"📥 Downloading: s3://{bucket}/{key}")
    
    response = s3.get_object(Bucket=bucket, Key=key)
    pdf_bytes = response['Body'].read()
    
    print(f"✅ Downloaded {len(pdf_bytes):,} bytes")
    
    # Extract fields
    print("\n🔎 Extracting form fields...")
    fields = extract_form_fields(pdf_bytes)
    
    print(f"✅ Found {len(fields)} form fields\n")
    
    # Group by type
    by_type = {}
    for field in fields:
        field_type = field['field_type']
        if field_type not in by_type:
            by_type[field_type] = []
        by_type[field_type].append(field)
    
    print("📊 Field Types:")
    for field_type, field_list in by_type.items():
        print(f"   {field_type}: {len(field_list)} fields")
    
    # Save to JSON
    output_file = 'form_1040_fields.json'
    with open(output_file, 'w') as f:
        json.dump(fields, f, indent=2)
    
    print(f"\n💾 Saved to: {output_file}")
    
    # Show sample fields
    print("\n📋 Sample Fields (first 10):")
    for i, field in enumerate(fields[:10]):
        print(f"\n{i+1}. {field['field_name']}")
        print(f"   Type: {field['field_type']}")
        print(f"   Page: {field['page_number']}")
        print(f"   Position: ({field['rect']['x0']:.1f}, {field['rect']['y0']:.1f})")
        if field.get('nearby_label'):
            print(f"   Label: {field['nearby_label'][:60]}...")
    
    # Create a simplified mapping
    print("\n\n🗺️  Creating simplified field mapping...")
    
    simplified = {}
    for field in fields:
        name = field['field_name']
        simplified[name] = {
            'type': field['field_type'],
            'page': field['page_number'],
            'label': field.get('nearby_label', ''),
            'position': f"({field['rect']['x0']:.0f}, {field['rect']['y0']:.0f})"
        }
    
    mapping_file = 'form_1040_field_mapping.json'
    with open(mapping_file, 'w') as f:
        json.dump(simplified, f, indent=2)
    
    print(f"💾 Saved simplified mapping to: {mapping_file}")
    
    print("\n🎉 Done! Use these field names to fill the form accurately.")
    
    return fields


if __name__ == "__main__":
    fields = main()

