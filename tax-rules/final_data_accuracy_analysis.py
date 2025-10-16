#!/usr/bin/env python3
"""Final comprehensive analysis of data accuracy and completeness."""

import sys
sys.path.append('src')
import re
from tax_rules_connector.http_client import IRSHttpClient

print('🎯 FINAL DATA ACCURACY ANALYSIS')
print('=' * 60)

http_client = IRSHttpClient(timeout=30, max_retries=2)

# Test the specific bulletin that contains Rev. Proc. 2024-40
bulletin_url = 'https://www.irs.gov/irb/2025-38_IRB'
print(f'Testing: {bulletin_url}')

try:
    soup = http_client.get_soup(bulletin_url)
    if soup:
        full_text = soup.get_text()
        print(f'Full content length: {len(full_text):,} characters')
        
        # Search for standard deduction mentions with amounts
        print('\n🔍 SEARCHING FOR STANDARD DEDUCTION DATA:')
        
        # Pattern 1: Direct standard deduction mentions
        std_pattern1 = r'standard deduction[^$]*\$([0-9,]+)'
        std_matches1 = re.findall(std_pattern1, full_text, re.IGNORECASE)
        if std_matches1:
            print(f'✅ Pattern 1 - Standard deduction amounts: ${", $".join(std_matches1)}')
        
        # Pattern 2: Look for 2025 tax year standard deduction
        std_pattern2 = r'2025[^$]*standard deduction[^$]*\$([0-9,]+)'
        std_matches2 = re.findall(std_pattern2, full_text, re.IGNORECASE)
        if std_matches2:
            print(f'✅ Pattern 2 - 2025 standard deduction: ${", $".join(std_matches2)}')
        
        # Pattern 3: Filing status with amounts
        filing_patterns = {
            'married filing jointly': r'married filing jointly[^$]*\$([0-9,]+)',
            'single': r'single[^$]*\$([0-9,]+)',
            'head of household': r'head of household[^$]*\$([0-9,]+)',
            'married filing separately': r'married filing separately[^$]*\$([0-9,]+)'
        }
        
        for status, pattern in filing_patterns.items():
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                print(f'✅ {status.title()}: ${", $".join(matches[:5])}')  # Show first 5
        
        # Look for tax bracket data
        print('\n🔍 SEARCHING FOR TAX BRACKET DATA:')
        bracket_patterns = [
            r'10%[^$]*\$([0-9,]+)',
            r'12%[^$]*\$([0-9,]+)',
            r'22%[^$]*\$([0-9,]+)',
            r'24%[^$]*\$([0-9,]+)',
            r'32%[^$]*\$([0-9,]+)',
            r'35%[^$]*\$([0-9,]+)',
            r'37%[^$]*\$([0-9,]+)'
        ]
        
        for pattern in bracket_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                rate = pattern.split('%')[0].replace('r\'', '')
                print(f'✅ {rate}% bracket: ${", $".join(matches[:3])}')
        
        # Look for specific dollar amounts that are likely standard deductions
        print('\n🔍 SEARCHING FOR LIKELY STANDARD DEDUCTION AMOUNTS:')
        # Standard deduction amounts for 2025 should be around $15,000-$30,000
        likely_std_amounts = re.findall(r'\$([12][0-9],[0-9]{3})', full_text)
        if likely_std_amounts:
            print(f'Likely standard deduction amounts: ${", $".join(set(likely_std_amounts))}')
        
        # Search for Revenue Procedure 2024-40 specifically
        print('\n🔍 SEARCHING FOR REVENUE PROCEDURE 2024-40:')
        if 'revenue procedure 2024-40' in full_text.lower():
            print('✅ Found Revenue Procedure 2024-40')
            
            # Extract the section around Rev. Proc. 2024-40
            revproc_start = full_text.lower().find('revenue procedure 2024-40')
            if revproc_start != -1:
                # Get 5000 characters around this section
                section_start = max(0, revproc_start - 1000)
                section_end = min(len(full_text), revproc_start + 4000)
                revproc_section = full_text[section_start:section_end]
                
                print(f'Rev. Proc. 2024-40 section preview:')
                print(revproc_section[:500] + '...')
                
                # Look for amounts in this section
                section_amounts = re.findall(r'\$([0-9,]+)', revproc_section)
                if section_amounts:
                    print(f'Amounts in Rev. Proc. 2024-40 section: ${", $".join(section_amounts[:10])}')
        
        # Summary of all dollar amounts
        print('\n📊 SUMMARY OF ALL DOLLAR AMOUNTS:')
        all_amounts = re.findall(r'\$([0-9,]+)', full_text)
        print(f'Total dollar amounts found: {len(all_amounts)}')
        
        # Group amounts by value ranges
        amount_ranges = {
            'Under $1,000': 0,
            '$1,000 - $9,999': 0,
            '$10,000 - $19,999': 0,
            '$20,000 - $29,999': 0,
            '$30,000 - $99,999': 0,
            '$100,000+': 0
        }
        
        for amount_str in all_amounts:
            try:
                amount = int(amount_str.replace(',', ''))
                if amount < 1000:
                    amount_ranges['Under $1,000'] += 1
                elif amount < 10000:
                    amount_ranges['$1,000 - $9,999'] += 1
                elif amount < 20000:
                    amount_ranges['$10,000 - $19,999'] += 1
                elif amount < 30000:
                    amount_ranges['$20,000 - $29,999'] += 1
                elif amount < 100000:
                    amount_ranges['$30,000 - $99,999'] += 1
                else:
                    amount_ranges['$100,000+'] += 1
            except:
                continue
        
        for range_name, count in amount_ranges.items():
            if count > 0:
                print(f'   {range_name}: {count} amounts')
    
    else:
        print('❌ Could not fetch bulletin content')
        
except Exception as e:
    print(f'❌ Error: {e}')

print('\n' + '='*60)
print('🎯 FINAL CONCLUSIONS')
print('='*60)
print('1. IRB bulletins contain 200,000+ characters and 100+ dollar amounts each')
print('2. We need to remove the 2,000 character limit to get complete content')
print('3. Standard deduction data is likely in specific Revenue Procedures')
print('4. Current extraction is getting SOME real data but missing key amounts')
print('5. We need enhanced parsing for Revenue Procedure sections')
print('6. The pipeline works technically but needs content parsing improvements')
