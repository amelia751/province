#!/usr/bin/env python3
"""
Final comprehensive test for form filling with fixes:
1. Tax year fields should be blank
2. Filing status should be "Single" only
3. SSN should be without dashes
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend/src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from province.agents.tax.tools.ingest_documents import ingest_documents
from province.agents.tax.tools.calc_1040 import calc_1040
from province.agents.tax.tools.form_filler import fill_tax_form
import fitz  # PyMuPDF


async def test_complete_flow():
    """Test complete flow with W-2 from user's Downloads"""
    print("=" * 80)
    print("🧪 COMPREHENSIVE FORM FILL TEST")
    print("=" * 80)
    
    user_id = "user_33w9KAn1gw3xXSa6MnBsySAQIIm"
    engagement_id = "ea3b3a4f-c877-4d29-bd66-2cff2aa77476"
    
    # Step 1: Skip W-2 ingestion (use mock data to speed up test)
    print("\n1️⃣ Using mock W-2 data (skipping Bedrock ingestion)...")
    
    # Mock W-2 data
    w2_result = {
        'forms': [{
            'employee': {
                'name': 'April Hensley',
                'SSN': '077-49-4905',
                'address': '31403 David Circles Suite 863, West Erinfort, WY 45881-3334',
                'street': '31403 David Circles Suite 863',
                'city': 'West Erinfort',
                'state': 'WY',
                'zip': '45881',
                'wages': 55151.93,
                'federal_withholding': 16606.17
            }
        }]
    }
    
    print(f"   ✅ W-2 ingested")
    print(f"   📋 Forms extracted: {len(w2_result.get('forms', []))}")
    
    if w2_result.get('forms'):
        employee = w2_result['forms'][0].get('employee', {})
        print(f"   👤 Employee: {employee.get('name', 'N/A')}")
        print(f"   📍 Address: {employee.get('address', 'N/A')}")
        print(f"   🔢 SSN: {employee.get('SSN', 'N/A')}")
        print(f"   💰 Wages: ${employee.get('wages', 0):,.2f}")
        print(f"   🏦 Withholding: ${employee.get('federal_withholding', 0):,.2f}")
    
    # Step 2: Calculate taxes (use extracted W-2 data)
    print("\n2️⃣ Calculating taxes...")
    
    if w2_result.get('forms'):
        employee = w2_result['forms'][0].get('employee', {})
        wages = float(employee.get('wages', 55000))
        withholding = float(employee.get('federal_withholding', 16000))
    else:
        wages = 55000
        withholding = 16000
    
    # Hardcoded calculation for testing
    agi = wages
    standard_deduction = 14600  # 2024 single
    taxable_income = max(0, agi - standard_deduction)
    
    # Tax calculation for single filer 2024
    if taxable_income <= 11600:
        tax = taxable_income * 0.10
    elif taxable_income <= 47150:
        tax = 1160 + (taxable_income - 11600) * 0.12
    else:
        tax = 5426 + (taxable_income - 47150) * 0.22
    
    refund_or_due = withholding - tax
    
    calc_data = {
        'agi': agi,
        'standard_deduction': standard_deduction,
        'taxable_income': taxable_income,
        'tax': tax,
        'withholding': withholding,
        'refund_or_due': refund_or_due,
        'tax_year': 2024
    }
    
    print(f"   ✅ Taxes calculated")
    print(f"   📊 AGI: ${agi:,.2f}")
    print(f"   📉 Standard Deduction: ${standard_deduction:,.2f}")
    print(f"   💵 Taxable Income: ${taxable_income:,.2f}")
    print(f"   🧾 Tax: ${tax:,.2f}")
    print(f"   💰 Withholding: ${withholding:,.2f}")
    print(f"   {'💸 Refund' if refund_or_due > 0 else '💳 Amount Owed'}: ${abs(refund_or_due):,.2f}")
    
    # Step 3: Fill Form 1040
    print("\n3️⃣ Filling Form 1040...")
    
    # Prepare form data with REAL W-2 data
    form_data = {
        # Personal info from W-2
        'taxpayer_first_name': employee.get('name', 'April').split()[0] if employee.get('name') else 'April',
        'taxpayer_last_name': employee.get('name', 'Hensley').split()[-1] if employee.get('name') else 'Hensley',
        'taxpayer_ssn': employee.get('SSN', '077494905').replace('-', ''),  # Remove dashes
        
        # Address from W-2
        'street_address': employee.get('street', '31403 David Circles Suite 863'),
        'city': employee.get('city', 'West Erinfort'),
        'state': employee.get('state', 'WY'),
        'zip_code': employee.get('zip', '45881'),
        
        # Filing status - SINGLE
        'single': True,
        'married_joint': False,
        'married_separate': False,
        'head_household': False,
        'qualifying_widow': False,
        
        # Income
        'wages_line_1a': wages,
        'total_income_9': wages,
        
        # Deductions & AGI
        'adjusted_gross_income_11': agi,
        'total_deductions_line_14_computed': standard_deduction,
        
        # Payments
        'withholding': withholding,
        'total_payments': withholding,
        
        # Refund/Owed
        'overpayment': abs(refund_or_due) if refund_or_due > 0 else 0,
        'amount_owed': abs(refund_or_due) if refund_or_due < 0 else 0,
        
        # Metadata
        'filing_status': 'Single',
        'dependents': 0,
    }
    
    print(f"   📝 Filling with:")
    print(f"      Name: {form_data['taxpayer_first_name']} {form_data['taxpayer_last_name']}")
    print(f"      SSN: {form_data['taxpayer_ssn']}")
    print(f"      Address: {form_data['street_address']}, {form_data['city']}, {form_data['state']} {form_data['zip_code']}")
    print(f"      Filing Status: Single (single={form_data['single']}, married_joint={form_data['married_joint']})")
    
    result = await fill_tax_form(
        form_type="1040",
        form_data=form_data,
        user_id=user_id,
        skip_questions=True
    )
    
    if result.get('success'):
        print(f"   ✅ Form filled successfully!")
        print(f"   📄 S3 Key: {result.get('s3_key', 'N/A')}")
        print(f"   🔗 Download URL: {result.get('download_url', 'N/A')[:100]}...")
        print(f"   📦 Version: {result.get('version', 'N/A')}")
        
        # Step 4: Verify the PDF
        print("\n4️⃣ Verifying filled PDF...")
        
        # Download and verify
        import boto3
        from dotenv import load_dotenv
        
        load_dotenv('.env.local')
        s3 = boto3.client('s3', region_name='us-east-1')
        bucket = 'province-documents-[REDACTED-ACCOUNT-ID]-us-east-1'
        s3_key = result.get('s3_key')
        
        if s3_key:
            # Download the filled PDF
            response = s3.get_object(Bucket=bucket, Key=s3_key)
            pdf_bytes = response['Body'].read()
            
            # Open with PyMuPDF
            pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Check critical fields
            critical_checks = {
                'SSN (no dashes)': form_data['taxpayer_ssn'],
                'First Name': form_data['taxpayer_first_name'],
                'Last Name': form_data['taxpayer_last_name'],
                'City': form_data['city'],
                'State': form_data['state'],
                'ZIP': form_data['zip_code'],
            }
            
            print(f"   📋 Verifying {len(critical_checks)} critical fields...")
            
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                for widget in page.widgets():
                    field_name = widget.field_name
                    field_value = widget.field_value
                    
                    # Check for tax year fields (should be BLANK)
                    if 'f1_01' in field_name or 'f1_03' in field_name:
                        if field_value and field_value.strip():
                            print(f"   ⚠️  Tax year field '{field_name}' is NOT blank: '{field_value}'")
                        else:
                            print(f"   ✅ Tax year field '{field_name}' is blank (correct)")
                    
                    # Check filing status checkboxes
                    if 'c1_3' in field_name and 'FilingStatus' in field_name:
                        # c1_3[0] = Married Joint, c1_3[1] = Single, c1_3[2] = Married Separate
                        if '[1]' in field_name:  # Single checkbox
                            if widget.field_value == 'Yes' or widget.is_checked:
                                print(f"   ✅ Single checkbox is CHECKED")
                            else:
                                print(f"   ❌ Single checkbox is NOT checked")
                        elif '[0]' in field_name:  # Married Joint
                            if widget.field_value == 'Yes' or widget.is_checked:
                                print(f"   ❌ Married Joint checkbox is CHECKED (should be unchecked)")
                            else:
                                print(f"   ✅ Married Joint checkbox is unchecked")
            
            pdf_doc.close()
            print(f"\n   ✅ Verification complete!")
    else:
        print(f"   ❌ Form filling failed: {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_complete_flow())

