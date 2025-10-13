import asyncio
import os
from dotenv import load_dotenv
from src.province.agents.tax.tools.ingest_w2 import ingest_w2

# Load environment variables from .env.local
load_dotenv('.env.local')

# Set the Data Automation credentials
os.environ['DATA_AUTOMATION_AWS_ACCESS_KEY_ID'] = os.getenv('DATA_AUTOMATION_AWS_ACCESS_KEY_ID')
os.environ['DATA_AUTOMATION_AWS_SECRET_ACCESS_KEY'] = os.getenv('DATA_AUTOMATION_AWS_SECRET_ACCESS_KEY')

async def test_env_w2():
    print("Testing W2 processing with environment variables...")
    print(f"Project ARN: {os.getenv('BEDROCK_DATA_AUTOMATION_PROJECT_ARN')}")
    print(f"Profile ARN: {os.getenv('BEDROCK_DATA_AUTOMATION_PROFILE_ARN')}")
    print(f"Output Bucket: {os.getenv('BEDROCK_OUTPUT_BUCKET_NAME')}")
    
    # Use the existing file that we know has results
    result = await ingest_w2(
        s3_key='datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_1000.pdf',
        taxpayer_name='April Hensley',
        tax_year=2010
    )
    
    print('=== W2 PROCESSING RESULT ===')
    print(f'Success: {result["success"]}')
    print(f'Processing Method: {result.get("processing_method", "unknown")}')
    
    if result['success']:
        print(f'Forms Count: {result["forms_count"]}')
        print(f'Total Wages: ${result["total_wages"]:,.2f}')
        print(f'Total Withholding: ${result["total_withholding"]:,.2f}')
        
        # Show Box 13 and multi-state data
        w2_extract = result['w2_extract']
        if w2_extract['forms']:
            form = w2_extract['forms'][0]
            boxes = form["boxes"]
            print(f'Box 13 (Checkboxes): {boxes.get("13", "Not found")}')
            print(f'State 1 (Box 15): {boxes.get("15", "Not found")}')
            print(f'State 2 (Box 15_a): {boxes.get("15_a", "Not found")}')
            print(f'Total boxes extracted: {len(boxes)}')
    else:
        print(f'Error: {result["error"]}')

asyncio.run(test_env_w2())
