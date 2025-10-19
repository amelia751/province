#!/usr/bin/env python3
"""
Identify Correct Field Mappings by Matching Labels with Field Positions
"""

import json
import sys
import os
from dotenv import load_dotenv
import boto3
import fitz

sys.path.insert(0, 'src')
load_dotenv('.env.local')

# Download template
s3 = boto3.client('s3', region_name='us-east-1')
bucket = os.getenv('TEMPLATES_BUCKET_NAME')
key = 'tax_forms/2024/f1040.pdf'

response = s3.get_object(Bucket=bucket, Key=key)
pdf_bytes = response['Body'].read()

doc = fitz.open(stream=pdf_bytes, filetype='pdf')
page = doc[0]

# Get all text positions
text_dict = page.get_text('dict')

# Get all form fields
widgets = list(page.widgets())

print('🎯 CORRECT FIELD IDENTIFICATION')
print('=' * 80)
print()

# Extract labels
labels = []
for block in text_dict['blocks']:
    if block['type'] == 0:  # Text block
        for line in block.get('lines', []):
            text = ''.join([span['text'] for span in line.get('spans', [])])
            if text.strip():
                labels.append({
                    'text': text.strip(),
                    'bbox': line['bbox'],
                    'x': line['bbox'][0],
                    'y': line['bbox'][1]
                })

# Match fields to labels (field should be BELOW and near the label)
def find_label_for_field(field_rect, labels):
    """Find the label above a field."""
    field_x = field_rect.x0
    field_y = field_rect.y0
    
    # Look for labels within 50 pixels above and 100 pixels horizontally
    candidates = []
    for label in labels:
        label_x = label['x']
        label_y = label['y']
        
        # Label should be above field (smaller y) and nearby horizontally
        if (label_y < field_y and 
            field_y - label_y < 50 and  # Within 50 pixels vertically
            abs(label_x - field_x) < 100):  # Within 100 pixels horizontally
            
            distance = ((label_x - field_x)**2 + (label_y - field_y)**2)**0.5
            candidates.append((distance, label))
    
    # Return closest label
    if candidates:
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]['text']
    return None

# Analyze first 30 text fields
text_fields = [w for w in widgets if w.field_type == fitz.PDF_WIDGET_TYPE_TEXT]
text_fields_sorted = sorted(text_fields, key=lambda w: (w.rect.y0, w.rect.x0))

print('📋 FIELD MAPPINGS (First 30 fields):')
print()

field_map = {}

for i, field in enumerate(text_fields_sorted[:30]):
    label = find_label_for_field(field.rect, labels)
    field_map[field.field_name] = {
        'position': f"({field.rect.x0:.0f}, {field.rect.y0:.0f})",
        'likely_for': label[:60] if label else 'Unknown',
        'field_number': i
    }
    
    print(f'{i+1}. {field.field_name}')
    print(f'   Position: x={field.rect.x0:.0f}, y={field.rect.y0:.0f}')
    print(f'   Likely for: {label[:60] if label else "Unknown"}')
    print()

# Save mapping
with open('correct_field_mapping.json', 'w') as f:
    json.dump(field_map, f, indent=2)

print('💾 Saved to: correct_field_mapping.json')

doc.close()

