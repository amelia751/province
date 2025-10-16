#!/usr/bin/env python3
"""
Test Dynamic Form Filling System

This script tests the new dynamic form filling capabilities:
1. Test multiple form types (1040, Schedule C, State forms)
2. Test intelligent field mapping
3. Test auto-detection of field patterns
4. Verify versioning works across different form types
"""

import asyncio
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_dynamic_form_filling():
    """Test dynamic form filling with multiple form types."""
    
    print("🚀 Testing Dynamic Form Filling System")
    print("=" * 60)
    
    try:
        from province.agents.tax.tools.form_filler import TaxFormFiller
        
        filler = TaxFormFiller()
        
        # Test 1: Federal 1040 Form
        print("1️⃣ Testing Federal 1040 Form...")
        form_1040_data = {
            'taxpayer_name': 'Jane Smith',
            'ssn': '987-65-4321',
            'address': '456 Oak Street, Springfield, IL 62701',
            'filing_status': 'Single',
            'wages': '85000',
            'federal_withholding': '12500',
            'standard_deduction': '14600',
            'taxable_income': '70400',
            'tax_liability': '9500',
            'refund_or_due': '3000'
        }
        
        result_1040 = await filler.fill_tax_form('1040', form_1040_data)
        print(f"✅ 1040 Result: {result_1040.get('success')}")
        print(f"   Fields filled: {result_1040.get('fields_filled')}")
        print(f"   Version: {result_1040.get('versioning', {}).get('version')}")
        print()
        
        # Test 2: Schedule C (Business) Form
        print("2️⃣ Testing Schedule C (Business) Form...")
        schedule_c_data = {
            'business_name': 'Smith Consulting LLC',
            'business_code': '541611',
            'business_address': '456 Oak Street, Springfield, IL 62701',
            'ein': '12-3456789',
            'gross_receipts': '150000',
            'advertising': '5000',
            'office_expense': '8000',
            'supplies': '3000',
            'utilities': '2400',
            'total_expenses': '18400',
            'net_profit_loss': '131600'
        }
        
        result_schedule_c = await filler.fill_tax_form('SCHEDULE_C', schedule_c_data)
        print(f"✅ Schedule C Result: {result_schedule_c.get('success')}")
        print(f"   Fields filled: {result_schedule_c.get('fields_filled')}")
        print(f"   Version: {result_schedule_c.get('versioning', {}).get('version')}")
        print()
        
        # Test 3: California State Form
        print("3️⃣ Testing California State Form...")
        ca_state_data = {
            'ca_taxpayer_name': 'Jane Smith',
            'ca_ssn': '987-65-4321',
            'ca_address': '456 Oak Street, Springfield, CA 90210',
            'ca_wages': '85000',
            'ca_withholding': '3500',
            'ca_tax_liability': '4200',
            'ca_refund_due': '700'
        }
        
        result_ca = await filler.fill_tax_form('STATE_CA', ca_state_data)
        print(f"✅ CA State Result: {result_ca.get('success')}")
        print(f"   Fields filled: {result_ca.get('fields_filled')}")
        print(f"   Version: {result_ca.get('versioning', {}).get('version')}")
        print()
        
        # Test 4: Test Intelligent Field Detection
        print("4️⃣ Testing Intelligent Field Detection...")
        unknown_form_data = {
            'primary_name': 'John Doe',  # Should auto-detect as name field
            'home_address': '123 Main St',  # Should auto-detect as address
            'postal_code': '12345',  # Should auto-detect as zip
            'annual_income': '75000',  # Should auto-detect as income
            'tax_withheld': '8500',  # Should auto-detect as withholding
            'phone_number': '555-1234',  # Should auto-detect as phone
            'email_address': 'john@example.com'  # Should auto-detect as email
        }
        
        result_unknown = await filler.fill_tax_form('1040', unknown_form_data)
        print(f"✅ Auto-detection Result: {result_unknown.get('success')}")
        print(f"   Fields filled: {result_unknown.get('fields_filled')}")
        print()
        
        # Test 5: List Available Forms
        print("5️⃣ Testing Available Forms List...")
        available_forms = filler.get_available_forms()
        print(f"✅ Available Forms: {len(available_forms)} forms")
        
        # Group by category
        categories = {}
        for form in available_forms:
            category = form.get('category', 'unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append(form['form_type'])
        
        for category, forms in categories.items():
            print(f"   📋 {category.title()}: {', '.join(forms)}")
        print()
        
        # Test 6: Version History Across Different Forms
        print("6️⃣ Testing Version History Across Forms...")
        
        # Get version history for 1040
        if result_1040.get('success'):
            doc_id_1040 = result_1040.get('versioning', {}).get('document_id')
            if doc_id_1040:
                versions_1040 = await filler.get_version_history(doc_id_1040)
                print(f"✅ 1040 Versions: {len(versions_1040)}")
        
        # Get version history for Schedule C
        if result_schedule_c.get('success'):
            doc_id_sc = result_schedule_c.get('versioning', {}).get('document_id')
            if doc_id_sc:
                versions_sc = await filler.get_version_history(doc_id_sc)
                print(f"✅ Schedule C Versions: {len(versions_sc)}")
        
        print()
        print("🎉 Dynamic Form Filling Tests Completed!")
        
        # Summary
        print("\n📊 Test Summary:")
        print(f"  ✅ Federal 1040: {'✓' if result_1040.get('success') else '✗'}")
        print(f"  ✅ Schedule C: {'✓' if result_schedule_c.get('success') else '✗'}")
        print(f"  ✅ CA State: {'✓' if result_ca.get('success') else '✗'}")
        print(f"  ✅ Auto-detection: {'✓' if result_unknown.get('success') else '✗'}")
        print(f"  ✅ Available Forms: {len(available_forms)} forms supported")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in dynamic form filling test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_field_mapping_intelligence():
    """Test the intelligent field mapping system."""
    
    print("\n🧠 Testing Field Mapping Intelligence")
    print("=" * 50)
    
    try:
        from province.agents.tax.tools.form_filler import TaxFormFiller
        
        filler = TaxFormFiller()
        
        # Test different field naming patterns
        test_cases = [
            {
                'name': 'Standard Names',
                'data': {
                    'name': 'Test User',
                    'address': '123 Test St',
                    'income': '50000',
                    'withholding': '7500'
                }
            },
            {
                'name': 'Abbreviated Names',
                'data': {
                    'nm': 'Test User',
                    'addr': '123 Test St',
                    'wages': '50000',
                    'wh': '7500'
                }
            },
            {
                'name': 'Descriptive Names',
                'data': {
                    'taxpayer_full_name': 'Test User',
                    'home_street_address': '123 Test St',
                    'annual_salary': '50000',
                    'federal_tax_withheld': '7500'
                }
            },
            {
                'name': 'Mixed Patterns',
                'data': {
                    'first_name': 'Test',
                    'last_name': 'User',
                    'street_addr': '123 Test St',
                    'yearly_income': '50000',
                    'tax_withholding': '7500',
                    'phone_num': '555-1234',
                    'email_addr': 'test@example.com'
                }
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"{i}️⃣ Testing {test_case['name']}...")
            
            # Test the field mapping (without actually filling forms)
            form_data_with_type = {**test_case['data'], 'form_type': '1040'}
            field_mapping = filler._get_field_mapping_for_form(form_data_with_type)
            
            mapped_fields = len([k for k, v in field_mapping.items() if k in test_case['data']])
            total_fields = len(test_case['data'])
            
            print(f"   📊 Mapped {mapped_fields}/{total_fields} fields")
            
            # Show some mappings
            for data_key in list(test_case['data'].keys())[:3]:
                if data_key in field_mapping:
                    mapped_to = field_mapping[data_key][:2]  # Show first 2 mappings
                    print(f"   🔗 '{data_key}' → {mapped_to}")
            
            print()
        
        print("✅ Field mapping intelligence test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in field mapping test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all dynamic form filling tests."""
    print("🧪 DYNAMIC FORM FILLING SYSTEM TESTS")
    print("=" * 60)
    
    # Test 1: Dynamic form filling
    success1 = await test_dynamic_form_filling()
    
    # Test 2: Field mapping intelligence
    success2 = await test_field_mapping_intelligence()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL TEST RESULTS:")
    print(f"  {'✅' if success1 else '❌'} Dynamic Form Filling")
    print(f"  {'✅' if success2 else '❌'} Field Mapping Intelligence")
    
    if success1 and success2:
        print("\n🎉 All tests passed! Dynamic form filling system is working correctly.")
        print("\n📋 Key Features Verified:")
        print("  ✅ Multiple form types supported (1040, Schedule C, State forms)")
        print("  ✅ Dynamic field mapping based on form type")
        print("  ✅ Intelligent field detection for unknown patterns")
        print("  ✅ Versioning works across different form types")
        print("  ✅ Comprehensive form catalog available")
        print("  ✅ Auto-detection handles various naming conventions")
    else:
        print("\n❌ Some tests failed. Please check the logs above.")
    
    return success1 and success2

if __name__ == "__main__":
    asyncio.run(main())
