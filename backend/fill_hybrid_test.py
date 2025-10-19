import fitz
import json
import boto3
import os
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv('.env.local')

# Configuration
FORM_TYPE = "F1040"
TAX_YEAR = "2024"
TEMPLATES_BUCKET = os.getenv('TEMPLATES_BUCKET_NAME', 'province-templates-[REDACTED-ACCOUNT-ID]-us-east-1')
DOCUMENTS_BUCKET = os.getenv('DOCUMENTS_BUCKET_NAME', 'province-documents-[REDACTED-ACCOUNT-ID]-us-east-1')
MAPPINGS_TABLE_NAME = os.getenv('FORM_MAPPINGS_TABLE_NAME', 'province-form-mappings')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

s3_client = boto3.client('s3', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
mappings_table = dynamodb.Table(MAPPINGS_TABLE_NAME)

def get_mapping_from_dynamodb(form_type: str, tax_year: str) -> dict:
    """Fetches the hybrid mapping from DynamoDB."""
    try:
        response = mappings_table.get_item(Key={'form_type': form_type, 'tax_year': tax_year})
        item = response.get('Item')
        if item:
            def convert_decimal(obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
            return json.loads(json.dumps(item['mapping'], default=convert_decimal))
        return {}
    except Exception as e:
        print(f"Error fetching mapping from DynamoDB: {e}")
        return {}

def download_pdf_template(form_type: str, tax_year: str) -> bytes:
    """Downloads the PDF template from S3."""
    key = f"tax_forms/{tax_year}/{form_type.lower()}.pdf"
    try:
        response = s3_client.get_object(Bucket=TEMPLATES_BUCKET, Key=key)
        return response['Body'].read()
    except Exception as e:
        print(f"Error downloading PDF template: {e}")
        raise

def upload_filled_pdf(pdf_bytes: bytes, form_type: str, tax_year: str, version: str) -> str:
    """Uploads the filled PDF to S3."""
    s3_key = f"filled_forms/TEST_HYBRID/{form_type}/{tax_year}/{version}_hybrid.pdf"
    try:
        s3_client.put_object(Bucket=DOCUMENTS_BUCKET, Key=s3_key, Body=pdf_bytes, ContentType='application/pdf')
        print(f"📄 HYBRID FILLED FORM:\n   Location: s3://{DOCUMENTS_BUCKET}/{s3_key}")
        
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': DOCUMENTS_BUCKET, 'Key': s3_key},
            ExpiresIn=604800  # 7 days
        )
        return presigned_url
    except Exception as e:
        print(f"Error uploading filled PDF: {e}")
        raise

def fill_form_with_hybrid_mapping(pdf_bytes: bytes, mapping: dict) -> bytes:
    """Fills the form using the hybrid seed+agent mapping."""
    doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    
    # Sample data using EXACT semantic names from hybrid mapping
    # This includes ALL available fields from seed + agent
    sample_data = {
        # Tax year (seed)
        "tax_year_begin": "2024",
        "tax_year_end": "",
        "tax_year_end_year": "20",
        
        # Personal info (seed)
        "taxpayer_first_name": "JOHN",
        "taxpayer_last_name": "SMITH",
        "taxpayer_ssn": "123-45-6789",
        "spouse_first_name": "JANE",
        "spouse_last_name": "DOE",
        "spouse_ssn": "987-65-4321",
        
        # Address (seed)
        "street_address": "123 MAIN STREET",
        "apt_no": "APT 4B",
        "city": "ANYTOWN",
        "state": "CA",
        "zip": "90210",
        
        # Filing status (seed) - checkboxes
        "single": False,
        "married_filing_jointly": True,
        "married_filing_separately": False,
        "head_of_household": False,
        "qualifying_widow": False,
        
        # Digital assets (seed) - checkboxes
        "yes": False,  # digital_assets.yes
        "no": True,    # digital_assets.no
        
        # Dependents (seed)
        "dependent_1_first_name": "EMMA",
        "dependent_1_last_name": "SMITH",
        "dependent_1_ssn": "111-22-3333",
        "dependent_1_relationship": "Daughter",
        "dependent_1_child_tax_credit": True,  # checkbox
        "dependent_1_other_credit": False,     # checkbox
        
        # Income (agent-mapped) - ALL income fields
        "wages_line_1a": 55151.93,
        "wages_line_1z": 55151.93,
        "household_employee_wages_1b": 0.00,
        "tip_income_1c": 0.00,
        "medicaid_waiver_1d": 0.00,
        "dependent_care_benefits_1e": 0.00,
        "employer_adoption_benefits_1f": 0.00,
        "wages_other_1g": 0.00,
        "other_earned_income_1h": 0.00,
        "nontaxable_combat_pay_1i": 0.00,
        "total_additional_income_1i": 0.00,
        "taxable_interest_2b": 125.50,
        "qualified_dividends_3a": 75.00,
        "ordinary_dividends_3b": 150.00,
        "ira_distributions_4a": 0.00,
        "ira_taxable_amount_4b": 0.00,
        "pensions_5a": 0.00,
        "pensions_taxable_5b": 0.00,
        "social_security_5a": 0.00,
        "social_security_taxable_5b": 0.00,
        "capital_gain_loss_7": 500.00,
        "schedule_1_additional_income_8": 0.00,
        "total_income_9": 56002.43,
        "adjustments_10": 0.00,
        "adjusted_gross_income_11": 56002.43,
        
        # Deductions
        "standard_deduction_12": 29200.00,  # MFJ 2024
        "qbi_deduction_13": 0.00,
        "total_deductions_14": 29200.00,
        "taxable_income_15": 26802.43,
        
        # Tax and Credits
        "tax_16": 2680.00,
        "schedule_2_additional_tax_17": 0.00,
        "total_tax_18": 2680.00,
        "child_tax_credit_19": 2000.00,
        "schedule_3_credits_20": 0.00,
        "total_credits_21": 2000.00,
        "tax_after_credits_22": 680.00,
        "schedule_2_other_taxes_23": 0.00,
        "total_tax_24": 680.00,
        
        # Payments
        "federal_tax_withheld_w2_25a": 16606.17,
        "federal_tax_withheld_1099_25b": 0.00,
        "federal_tax_withheld_other_25c": 0.00,
        "total_federal_tax_withheld_25d": 16606.17,
        "estimated_tax_payments_26": 0.00,
        "earned_income_credit_27": 0.00,
        "additional_child_tax_credit_28": 0.00,
        "american_opportunity_credit_29": 0.00,
        "schedule_3_payments_31": 0.00,
        "total_other_payments_32": 0.00,
        "total_payments_33": 16606.17,
        
        # Refund or Amount Owed
        "overpaid_amount_34": 15926.17,
        "refund_amount_35a": 15926.17,
        "routing_number_35b": "123456789",
        "account_type_checking_35c": True,
        "account_number_35d": "987654321",
        "apply_to_2025_36": 0.00,
        "amount_you_owe_37": 0.00,
        "estimated_tax_penalty_38": 0.00,
    }
    
    # Flatten mapping
    flat_mapping = {}
    for section, fields in mapping.items():
        if isinstance(fields, dict) and section != 'form_metadata':
            flat_mapping.update(fields)
    
    print(f"\n📋 Hybrid mapping has {len(flat_mapping)} semantic fields")
    print(f"📝 Sample data has {len(sample_data)} values")
    
    filled_text = 0
    filled_checkboxes = 0
    
    for page_num in range(doc.page_count):
        page = doc[page_num]
        for widget in page.widgets():
            full_field_name = widget.field_name
            if not full_field_name:
                continue
            
            # Find semantic name for this PDF field
            semantic_name = None
            for sem, pdf_path in flat_mapping.items():
                if pdf_path == full_field_name:
                    semantic_name = sem
                    break
            
            if semantic_name and semantic_name in sample_data:
                value = sample_data[semantic_name]
                
                if widget.field_type == 7:  # Text field
                    widget.field_value = str(value)
                    widget.update()
                    filled_text += 1
                    print(f"  ✓ {semantic_name}: {value}")
                    
                elif widget.field_type == 2:  # Checkbox
                    if value is True:
                        widget.field_value = "Yes"
                        widget.update()
                        filled_checkboxes += 1
                        print(f"  ☑  {semantic_name}: CHECKED")
                    elif value is False:
                        widget.field_value = "Off"
                        widget.update()
    
    print(f"\n✅ Filled {filled_text} text fields")
    print(f"✅ Checked {filled_checkboxes} checkboxes")
    print(f"✅ Total: {filled_text + filled_checkboxes} fields")
    
    # Save to bytes buffer
    import io
    output_buffer = io.BytesIO()
    doc.save(output_buffer, deflate=True)
    output_buffer.seek(0)
    pdf_bytes_output = output_buffer.read()
    doc.close()
    return pdf_bytes_output

def main():
    print("=" * 80)
    print("🎯 HYBRID MAPPING TEST (Seed + Agent)")
    print("=" * 80)
    
    # 1. Get hybrid mapping
    mapping = get_mapping_from_dynamodb(FORM_TYPE, TAX_YEAR)
    if not mapping:
        print("❌ No mapping found in DynamoDB")
        return
    print("✅ Loaded hybrid mapping from DynamoDB")
    
    # 2. Download template
    pdf_bytes = download_pdf_template(FORM_TYPE, TAX_YEAR)
    print("✅ Downloaded template PDF")
    
    # 3. Fill form
    filled_pdf_bytes = fill_form_with_hybrid_mapping(pdf_bytes, mapping)
    
    # 4. Upload
    presigned_url = upload_filled_pdf(filled_pdf_bytes, FORM_TYPE, TAX_YEAR, "v001")
    
    print("\n🔗 VIEW LINK (expires in 7 days):\n  ", presigned_url)
    print("\n" + "=" * 80)
    print("✅ DONE! Hybrid mapping with seed (critical) + agent (remaining)")
    print("=" * 80)

if __name__ == "__main__":
    main()

