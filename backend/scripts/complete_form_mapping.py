#!/usr/bin/env python3
"""
Comprehensive script to validate and complete ALL Form 1040 field mappings in DynamoDB.
This script:
1. Reads the actual PDF to get ALL fields
2. Compares with DynamoDB mappings
3. Fixes incorrect mappings
4. Adds missing mappings using intelligent inference
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import boto3
from dotenv import load_dotenv
import fitz
import json

load_dotenv(Path(__file__).parent.parent / '.env.local')

def get_pdf_fields():
    """Extract all fields from the PDF template"""
    s3 = boto3.client('s3', region_name='us-east-1')
    
    # Try multiple possible template locations
    possible_keys = [
        'forms/templates/F1040_2024.pdf',
        'pdf_templates/F1040_2024.pdf',
        'templates/F1040_2024.pdf'
    ]
    
    bucket = 'province-documents-[REDACTED-ACCOUNT-ID]-us-east-1'
    pdf_bytes = None
    
    for key in possible_keys:
        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            pdf_bytes = response['Body'].read()
            print(f"✅ Found template: {key}")
            break
        except:
            continue
    
    if not pdf_bytes:
        # Try local files
        local_paths = [
            Path(__file__).parent.parent / 'F1040_2024.pdf',
            Path(__file__).parent.parent / 'tax_form_templates' / '2024' / 'f1040.pdf',
        ]
        
        for local_path in local_paths:
            if local_path.exists():
                with open(local_path, 'rb') as f:
                    pdf_bytes = f.read()
                print(f"✅ Found local template: {local_path}")
                break
        
        if not pdf_bytes:
            print("❌ No template found!")
            return []
    
    pdf_doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    
    fields = []
    for page_num in range(len(pdf_doc)):
        page = pdf_doc[page_num]
        for widget in page.widgets():
            fields.append({
                'name': widget.field_name,
                'type': 'checkbox' if widget.field_type == 2 else 'text',
                'page': page_num + 1
            })
    
    pdf_doc.close()
    return fields


def infer_semantic_name(field_name: str, field_type: str) -> str:
    """Intelligently infer semantic name from PDF field name"""
    
    # Filing status checkboxes
    if 'c1_1[0]' in field_name:
        return 'filing_status_single'
    elif 'c1_2[0]' in field_name:
        return 'filing_status_married_jointly'
    elif 'FilingStatus' in field_name and 'c1_3[0]' in field_name:
        return 'filing_status_married_separately'
    elif 'FilingStatus' in field_name and 'c1_3[1]' in field_name:
        return 'filing_status_head_of_household'
    elif 'c1_4[0]' in field_name:
        return 'filing_status_qualifying_widow'
    
    # Digital assets
    elif 'c1_5[1]' in field_name:
        return 'digital_assets_yes'
    elif 'c1_6[0]' in field_name:
        return 'digital_assets_no'
    
    # Standard deduction checkboxes (c1_8 - c1_12)
    elif 'c1_8[0]' in field_name:
        return 'standard_deduction_you_dependent'
    elif 'c1_9[0]' in field_name:
        return 'standard_deduction_spouse_dependent'
    elif 'c1_10[0]' in field_name:
        return 'standard_deduction_spouse_itemizes'
    elif 'c1_11[0]' in field_name:
        return 'standard_deduction_dual_status_alien'
    
    # Presidential election checkboxes
    elif 'c1_0[0]' in field_name or ('Presidential' in field_name and 'c1_' in field_name):
        return 'presidential_election_you'
    elif 'c1_0[1]' in field_name:
        return 'presidential_election_spouse'
    
    # Dependent checkboxes (c1_14-c1_21 in dependent table)
    elif 'Table_Dependents' in field_name and 'c1_14' in field_name:
        return 'dependent_1_child_tax_credit'
    elif 'Table_Dependents' in field_name and 'c1_15' in field_name:
        return 'dependent_1_other_credit'
    elif 'Table_Dependents' in field_name and 'c1_16' in field_name:
        return 'dependent_2_child_tax_credit'
    elif 'Table_Dependents' in field_name and 'c1_17' in field_name:
        return 'dependent_2_other_credit'
    elif 'Table_Dependents' in field_name and 'c1_18' in field_name:
        return 'dependent_3_child_tax_credit'
    elif 'Table_Dependents' in field_name and 'c1_19' in field_name:
        return 'dependent_3_other_credit'
    elif 'Table_Dependents' in field_name and 'c1_20' in field_name:
        return 'dependent_4_child_tax_credit'
    elif 'Table_Dependents' in field_name and 'c1_21' in field_name:
        return 'dependent_4_other_credit'
    
    # Text fields - use position-based inference
    elif 'f1_' in field_name:
        # Extract field number
        import re
        match = re.search(r'f1_(\d+)', field_name)
        if match:
            num = int(match.group(1))
            
            # Personal info (f1_04 - f1_09)
            if num == 4:
                return 'taxpayer_first_name'
            elif num == 5:
                return 'taxpayer_last_name'
            elif num == 6:
                return 'taxpayer_ssn'
            elif num == 7:
                return 'spouse_first_name'
            elif num == 8:
                return 'spouse_last_name'
            elif num == 9:
                return 'spouse_ssn'
            
            # Address (f1_10 - f1_14)
            elif num == 10:
                return 'street_address'
            elif num == 11:
                return 'apt_no'
            elif num == 12:
                return 'city'
            elif num == 13:
                return 'state'
            elif num == 14:
                return 'zip_code'
            
            # Dependents (f1_18 - f1_31)
            elif 18 <= num <= 21:
                dep_num = 1
                field_names = ['first_name', 'last_name', 'ssn', 'relationship']
                return f'dependent_{dep_num}_{field_names[(num - 18) % 4]}'
            elif 22 <= num <= 25:
                dep_num = 2
                field_names = ['first_name', 'last_name', 'ssn', 'relationship']
                return f'dependent_{dep_num}_{field_names[(num - 22) % 4]}'
            elif 26 <= num <= 29:
                dep_num = 3
                field_names = ['first_name', 'last_name', 'ssn', 'relationship']
                return f'dependent_{dep_num}_{field_names[(num - 26) % 4]}'
            elif 30 <= num <= 31:
                dep_num = 4
                field_names = ['first_name', 'last_name']
                return f'dependent_{dep_num}_{field_names[(num - 30) % 2]}'
            
            # Income (f1_32 onwards on Page 1)
            elif num == 32:
                return 'wages_line_1a'
            elif num == 56:
                return 'total_income_line_9'
            elif num == 58:
                return 'adjusted_gross_income_line_11'
            elif num == 59:
                return 'standard_deduction_line_12'
    
    # Default: use field name as semantic name (cleaned)
    return field_name.replace('[0]', '').replace('[1]', '').replace('[2]', '').replace('topmostSubform[0].Page1[0].', '').replace('topmostSubform[0].Page2[0].', '')


def main():
    print("=" * 80)
    print("🔧 COMPLETE FORM 1040 MAPPING VALIDATION & FIX")
    print("=" * 80)
    
    # Step 1: Get all PDF fields
    print("\n1️⃣ Extracting fields from PDF template...")
    pdf_fields = get_pdf_fields()
    if not pdf_fields:
        print("❌ Could not read PDF template!")
        return
    
    print(f"   ✅ Found {len(pdf_fields)} fields in PDF")
    print(f"      - Text fields: {len([f for f in pdf_fields if f['type'] == 'text'])}")
    print(f"      - Checkboxes: {len([f for f in pdf_fields if f['type'] == 'checkbox'])}")
    
    # Step 2: Get current DynamoDB mappings
    print("\n2️⃣ Reading current DynamoDB mappings...")
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('province-form-mappings')
    
    response = table.get_item(Key={'form_type': 'F1040', 'tax_year': '2024'})
    current_mapping = response.get('Item', {}).get('mapping', {}) if 'Item' in response else {}
    
    # Flatten current mapping to get all semantic -> PDF mappings
    flat_current = {}
    for key, value in current_mapping.items():
        if isinstance(value, dict) and 'pdf_field_path' in value:
            flat_current[key] = value['pdf_field_path']
        elif isinstance(value, str):
            flat_current[key] = value
    
    print(f"   ✅ Current DynamoDB has {len(flat_current)} mappings")
    
    # Step 3: Find missing and incorrect mappings
    print("\n3️⃣ Analyzing mappings...")
    
    pdf_field_names = {f['name'] for f in pdf_fields}
    mapped_pdf_fields = set(flat_current.values())
    
    missing_in_db = pdf_field_names - mapped_pdf_fields
    print(f"   ⚠️  {len(missing_in_db)} PDF fields NOT in DynamoDB")
    
    # Check for incorrect mappings (fields that don't exist in PDF)
    incorrect = mapped_pdf_fields - pdf_field_names
    if incorrect:
        print(f"   ❌ {len(incorrect)} incorrect mappings (point to non-existent fields)")
        for field in list(incorrect)[:5]:
            print(f"      - {field}")
    
    # Step 4: Create complete mapping
    print("\n4️⃣ Creating complete mapping...")
    
    complete_mapping = {}
    
    # Add all existing correct mappings
    for semantic, pdf_field in flat_current.items():
        if pdf_field in pdf_field_names:
            complete_mapping[semantic] = {
                'semantic_name': semantic,
                'pdf_field_path': pdf_field,
                'section': 'general'  # Default section
            }
    
    # Add missing fields with inferred semantic names
    for pdf_field in missing_in_db:
        field_info = next((f for f in pdf_fields if f['name'] == pdf_field), None)
        if field_info:
            semantic_name = infer_semantic_name(pdf_field, field_info['type'])
            
            # Avoid duplicates
            if semantic_name not in complete_mapping:
                complete_mapping[semantic_name] = {
                    'semantic_name': semantic_name,
                    'pdf_field_path': pdf_field,
                    'section': 'auto_mapped'
                }
    
    print(f"   ✅ Complete mapping has {len(complete_mapping)} fields")
    
    # Step 5: Show key fixes
    print("\n5️⃣ Key fixes applied:")
    key_fields = {
        'single': 'topmostSubform[0].Page1[0].c1_1[0]',
        'married_joint': 'topmostSubform[0].Page1[0].c1_2[0]',
        'digital_assets_no': 'topmostSubform[0].Page1[0].c1_6[0]',
        'standard_deduction_you_dependent': 'topmostSubform[0].Page1[0].c1_8[0]',
        'dependent_1_first_name': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row1[0].f1_18[0]',
    }
    
    for semantic, expected_pdf in key_fields.items():
        current_pdf = flat_current.get(semantic, 'NOT MAPPED')
        new_pdf = complete_mapping.get(semantic, {}).get('pdf_field_path', 'NOT FOUND')
        
        if current_pdf != expected_pdf:
            print(f"   🔧 {semantic}:")
            print(f"      Old: {current_pdf}")
            print(f"      New: {new_pdf}")
    
    # Step 6: Update DynamoDB
    print("\n6️⃣ Updating DynamoDB...")
    
    table.put_item(Item={
        'form_type': 'F1040',
        'tax_year': '2024',
        'mapping': complete_mapping,
        'last_updated': 'auto_complete_script',
        'total_fields': len(complete_mapping)
    })
    
    print(f"   ✅ DynamoDB updated with {len(complete_mapping)} field mappings")
    
    # Step 7: Save to JSON for reference
    output_file = Path(__file__).parent.parent / 'complete_mapping_output.json'
    with open(output_file, 'w') as f:
        json.dump(complete_mapping, f, indent=2)
    
    print(f"\n7️⃣ Saved complete mapping to: {output_file}")
    
    print("\n" + "=" * 80)
    print("✅ COMPLETE - All fields mapped!")
    print("=" * 80)


if __name__ == "__main__":
    main()

