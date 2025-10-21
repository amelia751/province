#!/usr/bin/env python3
"""
Fix duplicate/inconsistent mappings in DynamoDB.
Remove old 'row*' mappings and ensure only 'dependent_*' mappings exist.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import boto3
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env.local')

def main():
    print("=" * 80)
    print("🔧 FIXING DUPLICATE DEPENDENT MAPPINGS")
    print("=" * 80)
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('province-form-mappings')
    
    # Get current mapping
    response = table.get_item(Key={'form_type': 'F1040', 'tax_year': '2024'})
    mapping = response['Item']['mapping']
    
    print(f"\n📊 Current mapping has {len(mapping)} fields")
    
    # Find all row* fields
    row_fields = {k: v for k, v in mapping.items() if k.startswith('row')}
    print(f"\n🔍 Found {len(row_fields)} 'row*' fields:")
    for k in sorted(row_fields.keys()):
        print(f"   {k}")
    
    # Find all dependent_* fields
    dependent_fields = {k: v for k, v in mapping.items() if 'dependent' in k}
    print(f"\n✅ Found {len(dependent_fields)} 'dependent*' fields")
    
    # Remove row* fields
    print(f"\n🗑️  Removing {len(row_fields)} 'row*' fields...")
    for k in row_fields.keys():
        del mapping[k]
    
    print(f"\n✅ New mapping has {len(mapping)} fields")
    
    # Update DynamoDB
    table.put_item(Item={
        'form_type': 'F1040',
        'tax_year': '2024',
        'mapping': mapping,
        'last_updated': 'remove_duplicate_mappings',
        'total_fields': len(mapping)
    })
    
    print("\n" + "=" * 80)
    print("✅ DUPLICATE MAPPINGS REMOVED")
    print("=" * 80)


if __name__ == "__main__":
    main()

