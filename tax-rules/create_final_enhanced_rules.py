#!/usr/bin/env python3
"""Create final enhanced rules.json from BigQuery export."""

import json
from datetime import datetime

print('🎯 Creating Final Enhanced Rules.json')
print('=' * 50)

# Load the exported data
with open('rules_packages_enhanced_export.json', 'r') as f:
    raw_data = json.load(f)

for row in raw_data:
    # Parse the tax items
    tax_items = json.loads(row['all_tax_items_json'])
    
    # Organize tax items by section
    organized_rules = {}
    for item in tax_items:
        section = item['section']
        if section not in organized_rules:
            organized_rules[section] = {}
        
        key = item['key']
        organized_rules[section][key] = {
            'amount': item['value_numeric'],
            'filing_status': item.get('filing_status'),
            'description': item['description']
        }
    
    # Create the enhanced rules.json structure
    enhanced_rules_json = {
        'metadata': {
            'package_id': row['package_id'],
            'version': row['package_version'],
            'jurisdiction': {
                'level': row['jurisdiction_level'],
                'code': row['jurisdiction_code']
            },
            'tax_year': row['tax_year'],
            'effective_date': row['effective_date'],
            'last_updated': row['last_updated'],
            'checksum_sha256': row['checksum_sha256'],
            'exported_at': datetime.now().isoformat() + 'Z',
            'extraction_method': 'enhanced_direct_connector',
            'total_items': row['total_items']
        },
        'rules': organized_rules,
        'sources': json.loads(row['sources_json']),
        'format_version': '2.0',
        'enhancements': {
            'content_extraction': True,
            'tax_amount_parsing': True,
            'real_irs_data': True,
            'comprehensive_analysis': True
        }
    }
    
    # Save to file
    filename = f'{row["jurisdiction_code"]}_{row["tax_year"]}_enhanced_rules.json'
    with open(filename, 'w') as f:
        json.dump(enhanced_rules_json, f, indent=2)
    
    print(f'✅ Created {filename}')
    print(f'   Tax Year: {row["tax_year"]}')
    print(f'   Total Items: {row["total_items"]}')
    print(f'   Sections: {list(organized_rules.keys())}')
    
    # Show sample items
    print(f'   Sample Tax Items:')
    for section, items in organized_rules.items():
        print(f'     {section}:')
        for key, data in list(items.items())[:2]:  # Show first 2 per section
            print(f'       - {key}: ${data["amount"]:,}')
            print(f'         {data["description"][:60]}...')
    
    print()

print('🎉 Enhanced rules.json created with REAL extracted IRS tax data!')
