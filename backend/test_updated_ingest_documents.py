#!/usr/bin/env python3
"""Test script for the updated ingest_documents tool."""

import asyncio
import os
from dotenv import load_dotenv
from src.province.agents.tax.tools.ingest_documents import ingest_documents

# Load environment variables from .env.local
load_dotenv(dotenv_path='.env.local')

async def test_updated_ingest_tools():
    print("\n🏗️ Testing Updated Document Ingestion Tools")
    print("=" * 60)
    
    # Test data
    test_cases = [
        {
            "name": "Test 1: New ingest_documents function with W-2",
            "function": ingest_documents,
            "s3_key": "datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_2745.pdf",
            "taxpayer_name": "Jane Doe",
            "tax_year": 2024,
            "document_type": "W-2"
        },
        {
            "name": "Test 2: W-2 document with explicit type",
            "function": ingest_documents,
            "s3_key": "datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_2746.jpg",
            "taxpayer_name": "John Smith",
            "tax_year": 2024,
            "document_type": "W-2"
        },
        {
            "name": "Test 3: 1099-INT document type",
            "function": ingest_documents,
            "s3_key": "test_1099_int_sample.pdf",
            "taxpayer_name": "Alice Johnson",
            "tax_year": 2024,
            "document_type": "1099-INT"
        },
        {
            "name": "Test 4: Auto-detection with ingest_documents",
            "function": ingest_documents,
            "s3_key": "datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_2746.jpg",
            "taxpayer_name": "Bob Wilson",
            "tax_year": 2024,
            "document_type": None  # Auto-detect
        }
    ]
    
    successful_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 {test_case['name']}")
        print("-" * 50)
        
        try:
            # Call ingest_documents function
            result = await test_case['function'](
                test_case['s3_key'],
                test_case['taxpayer_name'],
                test_case['tax_year'],
                test_case['document_type']
            )
            
            if result['success']:
                print(f"   ✅ Success: {result['success']}")
                print(f"   📄 Document Type: {result.get('document_type', 'Unknown')}")
                print(f"   💰 Total Wages: ${result.get('total_wages', 0):,.2f}")
                print(f"   🏛️ Total Withholding: ${result.get('total_withholding', 0):,.2f}")
                print(f"   ✅ Validation: {result.get('validation_results', {}).get('status', 'Unknown')}")
                successful_tests += 1
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results Summary:")
    print(f"   ✅ Successful: {successful_tests}/{total_tests}")
    print(f"   ❌ Failed: {total_tests - successful_tests}/{total_tests}")
    
    if successful_tests == total_tests:
        print("\n🎉 All tests passed! The updated ingest_documents tool is working correctly.")
    else:
        print(f"\n⚠️ {total_tests - successful_tests} test(s) failed. Please check the errors above.")
    
    print("\n🔧 Tool Functions Available:")
    print("   - ingest_documents() - Unified function for multi-document ingestion")
    print("   - Supports: W-2, 1099-INT, 1099-MISC, and auto-detection")
    print("   - Clean, single API for all tax document processing")

if __name__ == "__main__":
    asyncio.run(test_updated_ingest_tools())
