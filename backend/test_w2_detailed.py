import asyncio
import os
import json
from src.province.agents.tax.tools.ingest_w2 import ingest_w2

# Set the Data Automation credentials
os.environ['DATA_AUTOMATION_AWS_ACCESS_KEY_ID'] = '[REDACTED-AWS-KEY-3]'
os.environ['DATA_AUTOMATION_AWS_SECRET_ACCESS_KEY'] = '[REDACTED-AWS-SECRET-3]'

async def test_w2_detailed():
    result = await ingest_w2(
        s3_key='datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_1000.pdf',
        taxpayer_name='April Hensley',
        tax_year=2010
    )
    
    print('=== DETAILED W2 INGESTION RESULTS ===')
    print(f'Success: {result["success"]}')
    print(f'Processing Method: {result["processing_method"]}')
    
    if result['success']:
        w2_extract = result['w2_extract']
        form = w2_extract['forms'][0]
        
        print('\n--- EMPLOYER INFO ---')
        for key, value in form['employer'].items():
            print(f'{key}: {value}')
        
        print('\n--- EMPLOYEE INFO ---')
        for key, value in form['employee'].items():
            print(f'{key}: {value}')
        
        print('\n--- W-2 BOXES ---')
        for box_num, value in form['boxes'].items():
            print(f'Box {box_num}: {value}')
        
        print(f'\n--- SUMMARY ---')
        print(f'Total Forms: {result["forms_count"]}')
        print(f'Total Wages: ${result["total_wages"]:,.2f}')
        print(f'Total Withholding: ${result["total_withholding"]:,.2f}')
    else:
        print(f'Error: {result["error"]}')

asyncio.run(test_w2_detailed())
