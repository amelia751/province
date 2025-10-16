#!/usr/bin/env python3
"""Create RevProc items from extracted tax amounts in newsroom releases."""

import json
from datetime import datetime, date

print('📊 Creating RevProc items from extracted tax amounts...')

# Query the enhanced newsroom data to extract tax amounts
revproc_items = []

# Load the enhanced newsroom data
with open('newsroom_releases_enhanced.json', 'r') as f:
    for line in f:
        record = json.loads(line)
        
        # Parse tax amounts
        try:
            tax_amounts = json.loads(record.get('tax_amounts_json', '[]'))
            if tax_amounts:
                print(f'Processing: {record["title"][:60]}...')
                print(f'  Found {len(tax_amounts)} tax amounts')
                
                for amount_data in tax_amounts:
                    amount = amount_data['amount']
                    context = amount_data['context'].lower()
                    
                    # Determine what type of tax item this is
                    section = 'other'
                    key = 'unknown'
                    filing_status = None
                    
                    if 'deductible' in context and 'hsa' in context:
                        section = 'hsa_limits'
                        if 'family' in context:
                            key = 'family_deductible'
                            filing_status = 'family'
                        else:
                            key = 'individual_deductible'
                            filing_status = 'individual'
                    elif 'foreign earned income' in context:
                        section = 'exclusions'
                        key = 'foreign_earned_income'
                    elif 'estate' in context and 'exclusion' in context:
                        section = 'estate_tax'
                        key = 'basic_exclusion'
                    elif 'gift' in context and 'annual' in context:
                        section = 'gift_tax'
                        key = 'annual_exclusion'
                    elif 'adoption' in context:
                        section = 'credits'
                        key = 'adoption_credit'
                    elif 'out-of-pocket' in context:
                        section = 'hsa_limits'
                        if 'family' in context:
                            key = 'family_out_of_pocket'
                            filing_status = 'family'
                        else:
                            key = 'individual_out_of_pocket'
                            filing_status = 'individual'
                    
                    # Create RevProc item
                    revproc_item = {
                        'tax_year': 2025,  # From the announcement
                        'section': section,
                        'key': key,
                        'value': str(int(amount)),
                        'value_numeric': amount,
                        'units': 'dollars',
                        'data_type': 'amount',
                        'filing_status': filing_status,
                        'income_range_min': None,
                        'income_range_max': None,
                        'tax_rate': None,
                        'source_url': record['url'],
                        'revproc_number': 'newsroom-2025',
                        'published_date': record['published_date'],
                        'description': f'Extracted from: {context[:100]}',
                        'extraction_method': 'enhanced_connector',
                        'confidence_score': 0.8,
                        'jurisdiction_level': 'federal',
                        'jurisdiction_code': 'US'
                    }
                    
                    revproc_items.append(revproc_item)
                    
        except Exception as e:
            print(f'Error processing record: {e}')

print(f'\n✅ Created {len(revproc_items)} RevProc items from extracted tax amounts')

# Show summary
sections = {}
for item in revproc_items:
    section = item['section']
    if section not in sections:
        sections[section] = []
    sections[section].append(item)

print('\n📋 Summary by section:')
for section, items in sections.items():
    print(f'  {section}: {len(items)} items')
    for item in items[:2]:  # Show first 2 items per section
        print(f'    - {item["key"]}: ${item["value"]} ({item["description"][:50]}...)')

# Save to JSON file
with open('revproc_items_enhanced.json', 'w') as f:
    for item in revproc_items:
        f.write(json.dumps(item) + '\n')

print(f'\n✅ Saved to revproc_items_enhanced.json')
