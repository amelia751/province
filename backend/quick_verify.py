#!/usr/bin/env python3
"""Quick verification - direct form fill test"""
import sys, asyncio
sys.path.insert(0, 'src')
from dotenv import load_dotenv
load_dotenv('.env.local')
from province.agents.tax.tools.form_filler import fill_tax_form
import boto3

async def quick_test():
    USER_ID = "user_33w9KAn1gw3xXSa6MnBsySAQIIm"
    
    # Direct form data with semantic names
    form_data = {
        'taxpayer_first_name': 'John',
        'taxpayer_last_name': 'Smith',
        'taxpayer_ssn': '123-45-6789',
        'street_address': '123 Main St',
        'city': 'Columbus',
        'state': 'OH',
        'zip_code': '45881',
        'single': True,
        'tax_year': '2024',
        'wages_line_1a': 55151.93,
        'total_income_9': 55151.93,
        'adjusted_gross_income_11': 55151.93,
        'total_deductions_line_14_computed': 14600.00,
        'withholding': 16606.17,
        'total_payments': 16606.17,
        'overpayment': 11971.94,
    }
    
    print("Filling form with semantic names...")
    result = await fill_tax_form('1040', form_data, user_id=USER_ID, skip_questions=True)
    
    if result.get('success'):
        print(f"✅ SUCCESS!")
        
        # Get the S3 URL
        s3 = boto3.client('s3', region_name='us-east-1')
        bucket = 'province-documents-[REDACTED-ACCOUNT-ID]-us-east-1'
        prefix = f"filled_forms/{USER_ID}/1040/2024/"
        
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if 'Contents' in response:
            latest = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)[0]
            url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': latest['Key']}, ExpiresIn=3600)
            
            # Quick verify
            s3.download_file(bucket, latest['Key'], '/tmp/verify.pdf')
            import fitz
            doc = fitz.open('/tmp/verify.pdf')
            filled = {}
            for p in range(doc.page_count):
                for w in doc[p].widgets():
                    if w.field_value and w.field_value not in ['Off', '']:
                        filled[w.field_name] = w.field_value
            doc.close()
            
            print(f"\n📊 Verification:")
            print(f"   Total fields filled: {len(filled)}/88")
            print(f"\n   Sample filled fields:")
            for field, val in list(filled.items())[:10]:
                print(f"      {field[:50]:50} = {val}")
            
            print(f"\n🔗 Download URL:\n{url}\n")
            return url
    else:
        print(f"❌ Failed: {result.get('error')}")
        return None

asyncio.run(quick_test())

