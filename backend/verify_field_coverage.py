#!/usr/bin/env python3
"""
Field Coverage Verification Script

Counts fields directly from PDF AcroForm and verifies that ALL fields are mapped.
This ensures 100% accuracy and completeness.
"""

import json
import os
import sys
from typing import Dict, List, Any, Set
import fitz  # PyMuPDF
import boto3
from decimal import Decimal
from dotenv import load_dotenv

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


def count_fields_in_pdf(pdf_path: str) -> Dict[str, Any]:
    """Count all AcroForm fields directly from PDF."""
    print(f"\n📄 Reading PDF: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    
    all_fields = []
    text_fields = []
    checkboxes = []
    radio_buttons = []
    other_fields = []
    
    for page_num in range(doc.page_count):
        page = doc[page_num]
        widgets = page.widgets()
        
        for widget in widgets:
            field_name = widget.field_name
            if not field_name:
                continue
            
            field_info = {
                'field_name': field_name,
                'page': page_num + 1,
                'type': widget.field_type
            }
            
            all_fields.append(field_info)
            
            if widget.field_type == fitz.PDF_WIDGET_TYPE_TEXT:
                text_fields.append(field_info)
            elif widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                checkboxes.append(field_info)
            elif widget.field_type == fitz.PDF_WIDGET_TYPE_RADIOBUTTON:
                radio_buttons.append(field_info)
            else:
                other_fields.append(field_info)
    
    doc.close()
    
    return {
        'total': len(all_fields),
        'text': len(text_fields),
        'checkbox': len(checkboxes),
        'radio': len(radio_buttons),
        'other': len(other_fields),
        'all_fields': all_fields,
        'text_fields': text_fields,
        'checkboxes': checkboxes
    }


def get_mapping_from_dynamodb() -> Dict[str, Any]:
    """Get AI-generated mapping from DynamoDB."""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('province-form-mappings')
    
    try:
        response = table.get_item(Key={'form_type': 'F1040', 'tax_year': '2024'})
        
        if 'Item' in response:
            return decimal_to_number(response['Item']['mapping'])
        else:
            print("⚠️  No mapping found in DynamoDB")
            return None
    except Exception as e:
        print(f"❌ Error fetching mapping: {e}")
        return None


def extract_mapped_fields(mapping: Dict[str, Any]) -> Set[str]:
    """Extract all field names from the AI-generated mapping."""
    mapped = set()
    
    def extract(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and 'topmostSubform' in value:
                    mapped.add(value)
                elif isinstance(value, (dict, list)):
                    extract(value)
        elif isinstance(obj, list):
            for item in obj:
                extract(item)
    
    extract(mapping)
    return mapped


def verify_coverage(pdf_path: str, mapping: Dict[str, Any] = None) -> Dict[str, Any]:
    """Verify that ALL PDF fields are mapped."""
    
    print("\n" + "="*80)
    print("🔍 FIELD COVERAGE VERIFICATION")
    print("="*80)
    
    # Count fields in PDF
    pdf_fields = count_fields_in_pdf(pdf_path)
    
    print(f"\n📊 PDF FIELD COUNT:")
    print(f"   Total fields:    {pdf_fields['total']}")
    print(f"   - Text:          {pdf_fields['text']}")
    print(f"   - Checkbox:      {pdf_fields['checkbox']}")
    print(f"   - Radio:         {pdf_fields['radio']}")
    print(f"   - Other:         {pdf_fields['other']}")
    
    # Get all field names from PDF
    pdf_field_names = {f['field_name'] for f in pdf_fields['all_fields']}
    
    # Get mapping
    if mapping is None:
        print("\n🔄 Fetching mapping from DynamoDB...")
        mapping = get_mapping_from_dynamodb()
    
    if mapping:
        # Extract mapped fields
        mapped_fields = extract_mapped_fields(mapping)
        
        print(f"\n📊 MAPPING COVERAGE:")
        print(f"   Fields in PDF:   {len(pdf_field_names)}")
        print(f"   Fields mapped:   {len(mapped_fields)}")
        
        # Calculate coverage
        coverage_pct = (len(mapped_fields) / len(pdf_field_names)) * 100 if pdf_field_names else 0
        print(f"   Coverage:        {coverage_pct:.1f}%")
        
        # Find unmapped fields
        unmapped = pdf_field_names - mapped_fields
        
        if unmapped:
            print(f"\n❌ UNMAPPED FIELDS ({len(unmapped)}):")
            for i, field in enumerate(sorted(list(unmapped))[:20], 1):
                field_info = next((f for f in pdf_fields['all_fields'] if f['field_name'] == field), None)
                if field_info:
                    print(f"   {i}. {field} (Page {field_info['page']}, Type: {field_info['type']})")
            if len(unmapped) > 20:
                print(f"   ... and {len(unmapped) - 20} more")
        else:
            print(f"\n✅ ALL FIELDS MAPPED! ({len(mapped_fields)}/{len(pdf_field_names)})")
        
        # Check for extra mapped fields (shouldn't happen)
        extra_mapped = mapped_fields - pdf_field_names
        if extra_mapped:
            print(f"\n⚠️  WARNING: {len(extra_mapped)} fields in mapping but not in PDF:")
            for field in list(extra_mapped)[:10]:
                print(f"   - {field}")
        
        # Summary
        print("\n" + "="*80)
        if coverage_pct >= 100:
            print("✅ VERIFICATION PASSED: 100% field coverage!")
        elif coverage_pct >= 90:
            print(f"⚠️  VERIFICATION WARNING: {coverage_pct:.1f}% coverage (target: 100%)")
        else:
            print(f"❌ VERIFICATION FAILED: Only {coverage_pct:.1f}% coverage")
        print("="*80)
        
        return {
            'pdf_fields': pdf_fields,
            'mapped_count': len(mapped_fields),
            'unmapped': list(unmapped),
            'coverage_pct': coverage_pct,
            'passed': coverage_pct >= 100
        }
    else:
        print("\n❌ No mapping available to verify")
        return {
            'pdf_fields': pdf_fields,
            'mapped_count': 0,
            'unmapped': list(pdf_field_names),
            'coverage_pct': 0,
            'passed': False
        }


def main():
    """Run verification."""
    # Use Form 1040 as example
    pdf_path = 'tax_form_templates/2024/f1040.pdf'
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        sys.exit(1)
    
    result = verify_coverage(pdf_path)
    
    # Save detailed results
    output_file = 'field_coverage_verification.json'
    with open(output_file, 'w') as f:
        json.dump({
            'pdf_path': pdf_path,
            'verification_time': datetime.now().isoformat(),
            **result
        }, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    # Exit with appropriate code
    sys.exit(0 if result['passed'] else 1)


if __name__ == "__main__":
    from datetime import datetime
    main()

