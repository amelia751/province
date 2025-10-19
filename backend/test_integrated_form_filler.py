"""
Test the integrated AI form filler (no separate tools)
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.insert(0, 'src')
load_dotenv('.env.local')

from province.agents.tax.tools.form_filler import TaxFormFiller

async def test_ai_form_filling():
    """Test AI form filling with hybrid mapping."""
    
    print("=" * 80)
    print("🧪 TESTING INTEGRATED AI FORM FILLER")
    print("=" * 80)
    
    # Initialize filler
    filler = TaxFormFiller()
    
    # Simulated tax data from W-2
    form_data = {
        'tax_year': '2024',
        'form_type': '1040',
        'taxpayer_name': 'JOHN SMITH',
        
        # Seed mapping fields
        'taxpayer_first_name': 'JOHN',
        'taxpayer_last_name': 'SMITH',
        'taxpayer_ssn': '123-45-6789',
        'street_address': '123 MAIN ST',
        'city': 'ANYTOWN',
        'state': 'CA',
        'zip': '90210',
        
        # Filing status
        'married_filing_jointly': True,
        'single': False,
        
        # Digital assets
        'no': True,  # digital_assets.no
        
        # Income/tax (agent fields)
        'total_income_9': 55427.43,
        'adjusted_gross_income_11': 55427.43,
        'taxable_income_15': 26227.43,
        'tax_16': 2623.00,
        'child_tax_credit_19': 2000.00,
        'total_payments_33': 16606.17,
        'overpaid_amount_34': 15983.17,
        'refund_amount_35a': 15983.17,
    }
    
    print("\n📊 TEST 1: Initial fill (should ask for bank info)")
    print("-" * 80)
    
    result1 = await filler.fill_tax_form('1040', form_data)
    
    if result1.get('needs_input'):
        print(f"\n✅ AI asked questions:")
        for q in result1.get('questions', []):
            print(f"   • {q.get('question')}")
            print(f"     Field: {q.get('field')}")
        
        # Simulate user responses
        print("\n👤 USER RESPONDS:")
        user_responses = {
            'routing_number_35b': '123456789',
            'account_number_35d': '987654321',
            'account_type_checking_35c': True
        }
        for field, value in user_responses.items():
            print(f"   ✓ {field}: {value}")
        
        # Fill again with responses
        print("\n📊 TEST 2: Fill with user responses")
        print("-" * 80)
        
        result2 = await filler.fill_tax_form('1040', form_data, user_responses=user_responses)
        
        if result2.get('success'):
            print(f"\n🎉 SUCCESS!")
            print(f"   ✅ Form filled: {result2.get('message')}")
            print(f"   ✅ Fields filled: {result2.get('fields_filled', 'N/A')}")
            print(f"   📥 Download: {result2.get('filled_form_url', 'N/A')[:100]}...")
        else:
            print(f"\n❌ Failed: {result2.get('message')}")
    
    elif result1.get('success'):
        print(f"\n✅ Form filled without questions!")
        print(f"   📥 Download: {result1.get('filled_form_url')[:100]}...")
    
    else:
        print(f"\n❌ Error: {result1.get('message')}")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_ai_form_filling())

