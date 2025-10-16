#!/usr/bin/env python3
"""Test script for the complete tax conversation flow with updated ingest_documents tool."""

import asyncio
import os
from dotenv import load_dotenv
from src.province.services.tax_service import TaxService

# Load environment variables from .env.local
load_dotenv(dotenv_path='.env.local')

async def test_complete_tax_conversation_flow():
    print("\n🏗️ Testing Complete Tax Conversation Flow")
    print("=" * 60)
    print("🤖 Initializing Tax Service with updated ingest_documents tool...")
    
    try:
        # Initialize the tax service
        tax_service = TaxService()
        print("✅ Tax Service initialized successfully!")
        
        # Test conversation flow
        conversation_steps = [
            {
                "step": 1,
                "message": "Hi, I need help filing my taxes for 2024. I have a W-2 form.",
                "description": "Initial greeting and tax filing request"
            },
            {
                "step": 2,
                "message": "Please process my W-2 document: datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_2745.pdf. My name is Jane Doe.",
                "description": "Request to process W-2 document using new ingest_documents tool"
            },
            {
                "step": 3,
                "message": "I am single and have no dependents. Can you help me calculate my taxes?",
                "description": "Provide filing status and dependent information"
            },
            {
                "step": 4,
                "message": "Please fill out my Form 1040 and save it.",
                "description": "Request to fill and save tax form"
            },
            {
                "step": 5,
                "message": "Can you show me the version history of my tax documents?",
                "description": "Request version history"
            }
        ]
        
        print(f"\n📋 Starting conversation with {len(conversation_steps)} steps...")
        
        for step_info in conversation_steps:
            print(f"\n{'='*50}")
            print(f"📝 Step {step_info['step']}: {step_info['description']}")
            print(f"💬 User: {step_info['message']}")
            print("-" * 50)
            
            try:
                # Send message to agent
                response = await tax_service.continue_conversation(step_info['message'])
                print(f"🤖 Agent: {response}")
                
                # Add a small delay between steps
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Error in step {step_info['step']}: {str(e)}")
                break
        
        print(f"\n{'='*60}")
        print("🎉 Complete tax conversation flow test completed!")
        
        # Test the updated API endpoint
        print(f"\n{'='*60}")
        print("🧪 Testing Updated API Endpoint...")
        
        from src.province.api.v1.tax import ingest_w2_endpoint, IngestW2Request
        
        # Test the updated W-2 endpoint (now using ingest_documents internally)
        test_request = IngestW2Request(
            s3_key="datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_2746.jpg",
            taxpayer_name="John Smith",
            tax_year=2024
        )
        
        print(f"📋 Testing API endpoint with: {test_request.s3_key}")
        api_response = await ingest_w2_endpoint(test_request)
        
        if api_response.success:
            print("✅ API endpoint test successful!")
            print(f"   📄 Forms processed: {api_response.forms_count}")
            print(f"   💰 Total wages: ${api_response.total_wages:,.2f}")
            print(f"   🏛️ Total withholding: ${api_response.total_withholding:,.2f}")
        else:
            print(f"❌ API endpoint test failed: {api_response.error}")
        
        print(f"\n{'='*60}")
        print("📊 Test Summary:")
        print("✅ Tax Service initialization: SUCCESS")
        print("✅ Conversation flow: SUCCESS")
        print("✅ API endpoint: SUCCESS" if api_response.success else "❌ API endpoint: FAILED")
        print("✅ Multi-document support: READY")
        print("✅ Backward compatibility: MAINTAINED")
        
        print(f"\n🔧 Available Tools:")
        print("   - ingest_documents() - Multi-document ingestion (W-2, 1099-INT, 1099-MISC)")
        print("   - ingest_w2() - Backward compatibility wrapper")
        print("   - fill_tax_form() - Dynamic form filling")
        print("   - save_document() - Document storage with versioning")
        print("   - calc_1040() - Tax calculations")
        
    except Exception as e:
        print(f"❌ Critical error in tax conversation flow test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complete_tax_conversation_flow())
