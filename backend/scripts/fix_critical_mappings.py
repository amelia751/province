#!/usr/bin/env python3
"""
Fix critical field mappings that are currently wrong or missing:
1. Filing status (already fixed but verify)
2. Digital assets
3. Standard deduction checkboxes (c1_8 - c1_12)
4. Dependent fields (f1_18 - f1_31 and checkboxes)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import boto3
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env.local')

def main():
    print("=" * 80)
    print("🔧 FIXING CRITICAL FIELD MAPPINGS")
    print("=" * 80)
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('province-form-mappings')
    
    # Get current mapping
    response = table.get_item(Key={'form_type': 'F1040', 'tax_year': '2024'})
    mapping = response['Item']['mapping']
    
    print("\n📝 Applying critical fixes...")
    
    # 1. FILING STATUS (verify/fix)
    print("\n1️⃣ Filing Status:")
    filing_fixes = {
        'single': 'topmostSubform[0].Page1[0].c1_1[0]',
        'married_joint': 'topmostSubform[0].Page1[0].c1_2[0]',
        'married_separate': 'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[0]',
        'head_household': 'topmostSubform[0].Page1[0].FilingStatus_ReadOrder[0].c1_3[1]',
        'qualifying_widow': 'topmostSubform[0].Page1[0].c1_4[0]',
    }
    
    for semantic, pdf_path in filing_fixes.items():
        old = mapping.get(semantic, {}).get('pdf_field_path', 'NOT SET')
        mapping[semantic] = {
            'semantic_name': semantic,
            'pdf_field_path': pdf_path,
            'section': 'filing_status'
        }
        if old != pdf_path:
            print(f"   ✅ {semantic}: {old} → {pdf_path}")
        else:
            print(f"   ✓  {semantic}: {pdf_path}")
    
    # 2. DIGITAL ASSETS
    print("\n2️⃣ Digital Assets:")
    digital_fixes = {
        'digital_assets_yes_checkbox': 'topmostSubform[0].Page1[0].c1_5[1]',
        'digital_assets_no': 'topmostSubform[0].Page1[0].c1_6[0]',
    }
    
    for semantic, pdf_path in digital_fixes.items():
        old = mapping.get(semantic, {}).get('pdf_field_path', 'NOT SET')
        mapping[semantic] = {
            'semantic_name': semantic,
            'pdf_field_path': pdf_path,
            'section': 'digital_assets'
        }
        if old != pdf_path:
            print(f"   ✅ {semantic}: {old} → {pdf_path}")
        else:
            print(f"   ✓  {semantic}: {pdf_path}")
    
    # 3. STANDARD DEDUCTION CHECKBOXES
    print("\n3️⃣ Standard Deduction Checkboxes:")
    std_ded_fixes = {
        'standard_deduction_you_dependent': 'topmostSubform[0].Page1[0].c1_8[0]',
        'standard_deduction_spouse_dependent': 'topmostSubform[0].Page1[0].c1_9[0]',
        'standard_deduction_spouse_itemizes': 'topmostSubform[0].Page1[0].c1_10[0]',
        'standard_deduction_dual_status_alien': 'topmostSubform[0].Page1[0].c1_11[0]',
        'standard_deduction_you_born_before': 'topmostSubform[0].Page1[0].c1_12[0]',  # Age/blindness indicator
    }
    
    for semantic, pdf_path in std_ded_fixes.items():
        old = mapping.get(semantic, {}).get('pdf_field_path', 'NOT SET')
        mapping[semantic] = {
            'semantic_name': semantic,
            'pdf_field_path': pdf_path,
            'section': 'standard_deduction'
        }
        print(f"   ✅ {semantic}: {old} → {pdf_path}")
    
    # 4. DEPENDENT FIELDS
    print("\n4️⃣ Dependent Fields:")
    
    # Dependent text fields (names, SSN, relationship)
    dependent_text_fields = {
        # f1_18, f1_19 appear to be dependent count fields
        'dependent_count_qualifying': 'topmostSubform[0].Page1[0].f1_18[0]',
        'dependent_count_other': 'topmostSubform[0].Page1[0].f1_19[0]',
        
        # Row 1 (Dependent 1): f1_20-22
        'dependent_1_first_last_name': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row1[0].f1_20[0]',
        'dependent_1_ssn': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row1[0].f1_21[0]',
        'dependent_1_relationship': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row1[0].f1_22[0]',
        'dependent_1_child_tax_credit': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row1[0].c1_14[0]',
        'dependent_1_other_credit': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row1[0].c1_15[0]',
        
        # Row 2 (Dependent 2): f1_23-25
        'dependent_2_first_last_name': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row2[0].f1_23[0]',
        'dependent_2_ssn': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row2[0].f1_24[0]',
        'dependent_2_relationship': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row2[0].f1_25[0]',
        'dependent_2_child_tax_credit': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row2[0].c1_16[0]',
        'dependent_2_other_credit': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row2[0].c1_17[0]',
        
        # Row 3 (Dependent 3): f1_26-28
        'dependent_3_first_last_name': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row3[0].f1_26[0]',
        'dependent_3_ssn': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row3[0].f1_27[0]',
        'dependent_3_relationship': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row3[0].f1_28[0]',
        'dependent_3_child_tax_credit': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row3[0].c1_18[0]',
        'dependent_3_other_credit': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row3[0].c1_19[0]',
        
        # Row 4 (Dependent 4): f1_29-31
        'dependent_4_first_last_name': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row4[0].f1_29[0]',
        'dependent_4_ssn': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row4[0].f1_30[0]',
        'dependent_4_relationship': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row4[0].f1_31[0]',
        'dependent_4_child_tax_credit': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row4[0].c1_20[0]',
        'dependent_4_other_credit': 'topmostSubform[0].Page1[0].Table_Dependents[0].Row4[0].c1_21[0]',
    }
    
    for semantic, pdf_path in dependent_text_fields.items():
        mapping[semantic] = {
            'semantic_name': semantic,
            'pdf_field_path': pdf_path,
            'section': 'dependents'
        }
        print(f"   ✅ {semantic}")
    
    print(f"\n   Total dependent fields: {len(dependent_text_fields)}")
    
    # 5. Update DynamoDB
    print("\n5️⃣ Updating DynamoDB...")
    table.put_item(Item={
        'form_type': 'F1040',
        'tax_year': '2024',
        'mapping': mapping,
        'last_updated': 'critical_fixes_script',
        'total_fields': len(mapping)
    })
    
    print(f"   ✅ DynamoDB updated with {len(mapping)} total mappings")
    
    print("\n" + "=" * 80)
    print("✅ CRITICAL FIXES COMPLETE")
    print("=" * 80)
    
    print("\n📊 Summary:")
    print(f"   - Filing Status: 5 fields")
    print(f"   - Digital Assets: 2 fields")
    print(f"   - Standard Deduction: {len(std_ded_fixes)} fields")
    print(f"   - Dependents: {len(dependent_text_fields)} fields")
    print(f"   - TOTAL NEW/FIXED: {5 + 2 + len(std_ded_fixes) + len(dependent_text_fields)} fields")


if __name__ == "__main__":
    main()

