import asyncio
import os
from dotenv import load_dotenv
from src.province.agents.tax.tools.ingest_w2 import ingest_w2

# Load environment variables from .env.local
load_dotenv('.env.local')

# Set the Data Automation credentials
os.environ['DATA_AUTOMATION_AWS_ACCESS_KEY_ID'] = os.getenv('DATA_AUTOMATION_AWS_ACCESS_KEY_ID')
os.environ['DATA_AUTOMATION_AWS_SECRET_ACCESS_KEY'] = os.getenv('DATA_AUTOMATION_AWS_SECRET_ACCESS_KEY')

async def test_error_handling():
    print("Testing W2 processing error handling...")
    
    # Test with a non-existent file
    result = await ingest_w2(
        s3_key='non-existent-file.pdf',
        taxpayer_name='Test User',
        tax_year=2024
    )
    
    print('=== ERROR HANDLING TEST ===')
    print(f'Success: {result["success"]}')
    print(f'Error: {result.get("error", "No error message")}')
    
    # Test with unsupported file format
    result2 = await ingest_w2(
        s3_key='test-file.txt',
        taxpayer_name='Test User', 
        tax_year=2024
    )
    
    print('\n=== UNSUPPORTED FORMAT TEST ===')
    print(f'Success: {result2["success"]}')
    print(f'Error: {result2.get("error", "No error message")}')

asyncio.run(test_error_handling())
