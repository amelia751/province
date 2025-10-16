#!/usr/bin/env python3
"""Search for standard deduction announcements."""

import sys
sys.path.append('src')
import re
from tax_rules_connector.streams.newsroom_releases import NewsroomReleasesStream
from tax_rules_connector.http_client import IRSHttpClient

print('🔍 SEARCHING FOR STANDARD DEDUCTION ANNOUNCEMENTS')
print('=' * 60)

http_client = IRSHttpClient(timeout=30, max_retries=2)
stream = NewsroomReleasesStream(
    http_client,
    'https://www.irs.gov/newsroom',
    'federal',
    'US'
)

# Get more records and search for standard deduction content
print('📊 Searching through ALL newsroom records for standard deduction...')
count = 0
std_ded_records = []

for record in stream.read_records():
    count += 1
    title = record['title'].lower()
    
    # Look for standard deduction or tax bracket related titles
    if any(term in title for term in ['standard deduction', 'tax bracket', 'inflation adjustment', 'tax year']):
        std_ded_records.append(record)
        print(f'   {len(std_ded_records)}. {record["title"]}')
        print(f'      URL: {record["url"]}')
    
    # Stop after checking 50 records
    if count >= 50:
        break

print(f'\n📋 RESULTS:')
print(f'   Total records checked: {count}')
print(f'   Potential standard deduction records: {len(std_ded_records)}')

# Test the most promising ones
if std_ded_records:
    print(f'\n🎯 TESTING MOST PROMISING RECORDS:')
    
    for i, record in enumerate(std_ded_records[:3]):  # Test first 3
        print(f'\n--- Record {i+1}: {record["title"]} ---')
        
        try:
            # Get full content
            soup = http_client.get_soup(record['url'])
            if soup:
                content_areas = soup.find_all('p')
                full_text = ""
                for area in content_areas:
                    text = area.get_text(separator=' ', strip=True)
                    if len(text) > 50:
                        full_text += text + " "
                
                print(f'Content length: {len(full_text):,} characters')
                
                # Search for standard deduction
                std_ded_matches = re.findall(r'standard deduction[^.]*\$([0-9,]+)', full_text, re.IGNORECASE)
                if std_ded_matches:
                    print(f'✅ FOUND STANDARD DEDUCTION: ${", $".join(std_ded_matches)}')
                
                # Search for tax brackets
                bracket_matches = re.findall(r'(?:tax bracket|bracket)[^.]*\$([0-9,]+)', full_text, re.IGNORECASE)
                if bracket_matches:
                    print(f'✅ FOUND TAX BRACKETS: ${", $".join(bracket_matches)}')
                
                # Search for any dollar amounts
                all_amounts = re.findall(r'\$([0-9,]+)', full_text)
                print(f'Total dollar amounts: {len(all_amounts)}')
                if all_amounts:
                    print(f'Sample amounts: ${", $".join(all_amounts[:10])}')
                
                # Look for specific phrases
                key_phrases = ['married filing jointly', 'single filer', 'head of household', 'married filing separately']
                found_phrases = [phrase for phrase in key_phrases if phrase.lower() in full_text.lower()]
                if found_phrases:
                    print(f'✅ FILING STATUS TERMS: {found_phrases}')
                
                # Show content preview if it contains tax terms
                if any(term in full_text.lower() for term in ['standard deduction', 'tax bracket', 'filing status']):
                    print(f'📄 CONTENT PREVIEW:')
                    sentences = full_text.split('.')
                    tax_sentences = [s.strip() for s in sentences if 
                                   any(term in s.lower() for term in ['standard deduction', 'tax bracket', 'filing'])]
                    for sentence in tax_sentences[:3]:
                        print(f'   "{sentence}"')
                
            else:
                print('❌ Could not fetch content')
                
        except Exception as e:
            print(f'❌ Error: {e}')

else:
    print('\n❌ No standard deduction related records found')
    print('   This suggests we may need to look at:')
    print('   1. Different time periods (earlier months)')
    print('   2. IRB bulletins for Revenue Procedures')
    print('   3. Different IRS announcement categories')

# Let's also check what we actually have in our current data
print('\n' + '='*60)
print('🔍 ANALYZING CURRENT EXTRACTED DATA')
print('='*60)

# Check what tax data we actually extracted
import json
try:
    with open('newsroom_releases_enhanced.json', 'r') as f:
        for line_num, line in enumerate(f):
            record = json.loads(line)
            tax_amounts = json.loads(record.get('tax_amounts_json', '[]'))
            
            if tax_amounts:
                print(f'\nRecord {line_num + 1}: {record["title"][:60]}...')
                print(f'   Tax amounts: {len(tax_amounts)}')
                for amount in tax_amounts[:3]:
                    print(f'   - ${amount["amount"]:,}: {amount["context"][:80]}...')
                
                # Check if this might contain standard deduction info
                full_content = record.get('full_content', '')
                if 'standard deduction' in full_content.lower():
                    print('   ✅ Contains "standard deduction" in content!')
                if 'tax bracket' in full_content.lower():
                    print('   ✅ Contains "tax bracket" in content!')
                    
except FileNotFoundError:
    print('No enhanced newsroom data file found')
except Exception as e:
    print(f'Error reading enhanced data: {e}')
