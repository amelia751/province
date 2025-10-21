#!/usr/bin/env python3
"""
Add missing refund field mappings to DynamoDB.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import boto3
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env.local')

def main():
    print("=" * 80)
    print("💰 ADDING REFUND FIELD MAPPINGS")
    print("=" * 80)
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('province-form-mappings')
    
    # Get current mapping
    response = table.get_item(Key={'form_type': 'F1040', 'tax_year': '2024'})
    mapping = response['Item']['mapping']
    
    print(f"\n📊 Current mapping has {len(mapping)} fields")
    
    # Add refund fields
    new_mappings = {
        'refund_amount': 'topmostSubform[0].Page2[0].f2_24[0]',  # Line 35a - Amount to be refunded
        'estimated_tax_payment': 'topmostSubform[0].Page2[0].f2_27[0]',  # Line 36 - Apply to estimated tax
    }
    
    print(f"\n✅ Adding {len(new_mappings)} refund mappings:")
    for key, value in new_mappings.items():
        mapping[key] = value
        print(f"   {key}: {value}")
    
    print(f"\n✅ New mapping has {len(mapping)} fields")
    
    # Update DynamoDB
    table.put_item(Item={
        'form_type': 'F1040',
        'tax_year': '2024',
        'mapping': mapping,
        'last_updated': 'add_refund_mappings',
        'total_fields': len(mapping)
    })
    
    print("\n" + "=" * 80)
    print("✅ REFUND MAPPINGS ADDED")
    print("=" * 80)


if __name__ == "__main__":
    main()

