import asyncio
import os
from src.province.agents.tax.tools.ingest_w2 import ingest_w2

# Set the Data Automation credentials
os.environ['DATA_AUTOMATION_AWS_ACCESS_KEY_ID'] = '[REDACTED-AWS-KEY-3]'
os.environ['DATA_AUTOMATION_AWS_SECRET_ACCESS_KEY'] = '[REDACTED-AWS-SECRET-3]'

async def test_realtime_w2():
    print("Testing real-time W2 processing with Bedrock Data Automation...")
    
    # Use a different file that might not have existing results
    result = await ingest_w2(
        s3_key='datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_1001.jpg',  # Different file
        taxpayer_name='Test User',
        tax_year=2024
    )
    
    print('=== REAL-TIME W2 PROCESSING RESULT ===')
    print(f'Success: {result["success"]}')
    print(f'Processing Method: {result.get("processing_method", "unknown")}')
    
    if result['success']:
        print(f'Forms Count: {result["forms_count"]}')
        print(f'Total Wages: ${result["total_wages"]:,.2f}')
        print(f'Total Withholding: ${result["total_withholding"]:,.2f}')
        
        # Show some extracted data
        w2_extract = result['w2_extract']
        if w2_extract['forms']:
            form = w2_extract['forms'][0]
            print(f'Employer: {form["employer"].get("name", "Unknown")}')
            print(f'Employee: {form["employee"].get("name", "Unknown")}')
            print(f'Boxes extracted: {len(form["boxes"])}')
    else:
        print(f'Error: {result["error"]}')

asyncio.run(test_realtime_w2())
