#!/usr/bin/env python3
"""
Complete end-to-end test simulating a real user conversation.
Tests the full flow: W2 upload → data extraction → conversation → form filling.
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from province.services.tax_service import TaxService


async def simulate_user_conversation():
    """Simulate a complete user conversation with the tax agent."""
    
    print("\n" + "="*80)
    print("🧪 SIMULATING COMPLETE USER CONVERSATION")
    print("="*80)
    
    # Initialize the tax service
    tax_service = TaxService()
    
    # User info
    user_id = "user_33w9KAn1gw3xXSa6MnBsySAQIIm"
    engagement_id = "ea3b3a4f-c877-4d29-bd66-2cff2aa77476"
    
    print(f"\n👤 User: {user_id}")
    print(f"📋 Engagement: {engagement_id}")
    
    # Step 1: Start conversation
    print("\n" + "-"*80)
    print("STEP 1: Starting conversation")
    print("-"*80)
    
    # Start conversation (generates session_id if not provided)
    initial_message = await tax_service.start_conversation(session_id=None, user_id=user_id)
    
    # Get the generated session_id from tax_service conversation_state
    from province.services.tax_service import conversation_state
    session_id = conversation_state.get('current_session_id')
    
    print(f"✅ Session started: {session_id}")
    print(f"🤖 Agent: {initial_message}")
    
    # Step 2: Upload W-2 document
    print("\n" + "-"*80)
    print("STEP 2: Uploading W-2 document")
    print("-"*80)
    
    # First, upload the W2 to S3
    import boto3
    s3_client = boto3.client('s3')
    
    w2_local_path = "/Users/anhlam/Downloads/W2_XL_input_clean_1000.pdf"
    s3_key = f"tax-engagements/{engagement_id}/chat-uploads/W2_XL_input_clean_1000.pdf"
    bucket = "province-documents-[REDACTED-ACCOUNT-ID]-us-east-1"
    
    print(f"📤 Uploading W-2 to S3...")
    print(f"   Local: {w2_local_path}")
    print(f"   S3: s3://{bucket}/{s3_key}")
    
    with open(w2_local_path, 'rb') as f:
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=f,
            ContentType='application/pdf'
        )
    
    print(f"✅ W-2 uploaded to S3")
    
    # Now tell the agent to process it
    print(f"\n💬 User: I've uploaded my W-2 form. Can you process it?")
    
    process_result = await tax_service.continue_conversation(
        user_message=f"I've uploaded my W-2 form at {s3_key}. Please process it and extract my information.",
        session_id=session_id,
        user_id=user_id
    )
    
    print(f"🤖 Agent: {process_result}")
    
    # Wait for processing (if Bedrock takes time)
    print("\n⏳ Waiting for Bedrock processing...")
    await asyncio.sleep(5)
    
    # Step 3: Answer agent's questions
    print("\n" + "-"*80)
    print("STEP 3: Answering agent's questions")
    print("-"*80)
    
    # Question 1: Filing status
    print(f"\n💬 User: I am single.")
    
    filing_status_result = await tax_service.continue_conversation(
        user_message="I am single.",
        session_id=session_id,
        user_id=user_id
    )
    
    print(f"🤖 Agent: {filing_status_result}")
    
    # Question 2: Dependents
    print(f"\n💬 User: I have 2 dependents.")
    
    dependents_result = await tax_service.continue_conversation(
        user_message="Yes, I have 2 dependents.",
        session_id=session_id,
        user_id=user_id
    )
    
    print(f"🤖 Agent: {dependents_result}")
    
    # Question 3: Dependent details
    print(f"\n💬 User: My first dependent is my daughter Alice Smith (SSN 123-45-6789)")
    
    dep1_result = await tax_service.continue_conversation(
        user_message="My first dependent is my daughter Alice Smith, SSN 123-45-6789.",
        session_id=session_id,
        user_id=user_id
    )
    
    print(f"🤖 Agent: {dep1_result}")
    
    print(f"\n💬 User: My second dependent is my son Bob Smith (SSN 987-65-4321)")
    
    dep2_result = await tax_service.continue_conversation(
        user_message="My second dependent is my son Bob Smith, SSN 987-65-4321.",
        session_id=session_id,
        user_id=user_id
    )
    
    print(f"🤖 Agent: {dep2_result}")
    
    # Question 4: Digital assets
    print(f"\n💬 User: No, I don't have any digital assets.")
    
    digital_assets_result = await tax_service.continue_conversation(
        user_message="No, I don't have any digital assets.",
        session_id=session_id,
        user_id=user_id
    )
    
    print(f"🤖 Agent: {digital_assets_result}")
    
    # Question 5: Standard deduction
    print(f"\n💬 User: No one can claim me as a dependent.")
    
    deduction_result = await tax_service.continue_conversation(
        user_message="No one can claim me as a dependent.",
        session_id=session_id,
        user_id=user_id
    )
    
    print(f"🤖 Agent: {deduction_result}")
    
    # Question 6: Banking info for refund
    print(f"\n💬 User: For my refund, use routing number 123456789, account number 987654321, checking account.")
    
    banking_result = await tax_service.continue_conversation(
        user_message="For my refund, please direct deposit to routing number 123456789, account number 987654321, checking account.",
        session_id=session_id,
        user_id=user_id
    )
    
    print(f"🤖 Agent: {banking_result}")
    
    # Step 4: Request form filling
    print("\n" + "-"*80)
    print("STEP 4: Requesting form fill")
    print("-"*80)
    
    print(f"\n💬 User: Please fill out my Form 1040 and show me the completed form.")
    
    fill_result = await tax_service.continue_conversation(
        user_message="That's all the information. Please fill out my Form 1040 and show me the completed form.",
        session_id=session_id,
        user_id=user_id
    )
    
    print(f"🤖 Agent: {fill_result}")
    
    # Step 5: Check the filled form in S3
    print("\n" + "-"*80)
    print("STEP 5: Verifying filled form in S3")
    print("-"*80)
    
    # List forms for this user
    prefix = f"filled_forms/{user_id}/1040/2024/"
    print(f"\n📁 Checking S3 for filled forms: s3://{bucket}/{prefix}")
    
    response = s3_client.list_objects_v2(
        Bucket=bucket,
        Prefix=prefix,
        MaxKeys=10
    )
    
    if 'Contents' in response:
        print(f"✅ Found {len(response['Contents'])} filled form(s):")
        for obj in response['Contents']:
            print(f"   - {obj['Key']}")
            print(f"     Size: {obj['Size']} bytes")
            print(f"     Modified: {obj['LastModified']}")
            
            # Generate presigned URL
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': obj['Key']},
                ExpiresIn=3600
            )
            print(f"     URL: {url[:100]}...")
    else:
        print(f"❌ No filled forms found!")
    
    # Step 6: Verify conversation state
    print("\n" + "-"*80)
    print("STEP 6: Verifying conversation state")
    print("-"*80)
    
    state = tax_service.get_conversation_state(session_id)
    print(f"\n📊 Final conversation state:")
    print(json.dumps({
        'session_id': session_id,
        'user_id': state.get('user_id'),
        'engagement_id': state.get('engagement_id'),
        'filing_status': state.get('filing_status'),
        'dependents': state.get('dependents'),
        'dependents_list': state.get('dependents_list'),
        'routing_number': state.get('routing_number'),
        'account_number': state.get('account_number'),
        'account_type': state.get('account_type'),
        'digital_assets': state.get('digital_assets'),
        'w2_processed': 'w2_data' in state,
        'tax_calculated': 'calc_1040_data' in state,
    }, indent=2))
    
    print("\n" + "="*80)
    print("✅ CONVERSATION TEST COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(simulate_user_conversation())

