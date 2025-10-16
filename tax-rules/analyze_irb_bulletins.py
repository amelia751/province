#!/usr/bin/env python3
"""Analyze IRB bulletins for standard deduction data."""

import sys
sys.path.append('src')
import re
from tax_rules_connector.streams.irb_bulletins import IRBBulletinsStream
from tax_rules_connector.http_client import IRSHttpClient

print('🔍 DEEP DIVE: IRB Bulletins for Standard Deduction Data')
print('=' * 60)

http_client = IRSHttpClient(timeout=30, max_retries=2)
stream = IRBBulletinsStream(
    http_client,
    'https://www.irs.gov/irb',
    'federal',
    'US'
)

# Get IRB bulletins and look for Revenue Procedures
print('📊 Analyzing IRB bulletins for Revenue Procedures...')
bulletins = list(stream.read_records())
print(f'Total bulletins found: {len(bulletins)}')

# Test a few recent bulletins
for i, bulletin in enumerate(bulletins[:3]):
    print(f'\n🎯 Testing Bulletin {i+1}: {bulletin["bulletin_no"]}')
    print(f'   HTML URL: {bulletin["url_html"]}')
    print(f'   PDF URL: {bulletin["url_pdf"]}')
    
    try:
        # Get the HTML content
        soup = http_client.get_soup(bulletin['url_html'])
        if soup:
            # Get all text content
            full_text = soup.get_text(separator=' ', strip=True)
            print(f'   Content length: {len(full_text):,} characters')
            
            # Look for Revenue Procedures
            revproc_matches = re.findall(r'Revenue Procedure ([0-9]{4}-[0-9]+)', full_text, re.IGNORECASE)
            if revproc_matches:
                print(f'   ✅ Revenue Procedures found: {revproc_matches}')
            
            # Look for standard deduction mentions
            if 'standard deduction' in full_text.lower():
                print(f'   ✅ Contains "standard deduction"')
                # Find sentences with standard deduction
                sentences = full_text.split('.')
                std_sentences = [s.strip() for s in sentences if 'standard deduction' in s.lower()]
                for sentence in std_sentences[:2]:
                    print(f'      "{sentence[:120]}..."')
            
            # Look for tax bracket mentions
            if 'tax bracket' in full_text.lower():
                print(f'   ✅ Contains "tax bracket"')
            
            # Look for inflation adjustment mentions
            if 'inflation' in full_text.lower():
                print(f'   ✅ Contains "inflation"')
            
            # Count dollar amounts
            dollar_amounts = re.findall(r'\$([0-9,]+)', full_text)
            if dollar_amounts:
                print(f'   💰 Dollar amounts found: {len(dollar_amounts)}')
                print(f'      Sample amounts: ${", $".join(dollar_amounts[:10])}')
            
            # Look for specific Revenue Procedure titles about inflation
            inflation_revprocs = re.findall(r'Revenue Procedure [0-9]{4}-[0-9]+[^.]*inflation[^.]*', full_text, re.IGNORECASE)
            if inflation_revprocs:
                print(f'   🎯 INFLATION REVENUE PROCEDURES:')
                for revproc in inflation_revprocs:
                    print(f'      {revproc}')
                    
            # Look for tables or structured data
            tables = soup.find_all('table')
            if tables:
                print(f'   📊 Tables found: {len(tables)}')
                # Check if any tables contain tax data
                for table in tables[:2]:  # Check first 2 tables
                    table_text = table.get_text(strip=True)
                    if any(term in table_text.lower() for term in ['deduction', 'bracket', 'filing', 'married', 'single']):
                        print(f'      ✅ Table contains tax terms')
                        # Show table structure
                        rows = table.find_all('tr')
                        if rows:
                            print(f'         Rows: {len(rows)}')
                            # Show first row as sample
                            first_row = rows[0].get_text(separator=' | ', strip=True)
                            print(f'         Sample: {first_row[:100]}...')
        else:
            print('   ❌ Could not fetch HTML content')
            
    except Exception as e:
        print(f'   ❌ Error: {e}')

print('\n' + '='*60)
print('🔍 SEARCHING FOR SPECIFIC REVENUE PROCEDURES')
print('='*60)

# Look for specific Revenue Procedures that typically contain standard deduction info
target_revprocs = ['2024-40', '2024-41', '2024-42', '2025-01', '2025-02']

for bulletin in bulletins[:10]:  # Check first 10 bulletins
    try:
        soup = http_client.get_soup(bulletin['url_html'])
        if soup:
            full_text = soup.get_text()
            
            for target in target_revprocs:
                if target in full_text:
                    print(f'\n🎯 FOUND Rev. Proc. {target} in {bulletin["bulletin_no"]}')
                    print(f'   URL: {bulletin["url_html"]}')
                    
                    # Look for standard deduction in this specific context
                    revproc_pattern = f'Revenue Procedure {target}[^.]*'
                    matches = re.findall(revproc_pattern, full_text, re.IGNORECASE | re.DOTALL)
                    if matches:
                        print(f'   Context: {matches[0][:200]}...')
                    
                    # Check if this bulletin contains standard deduction amounts
                    std_amounts = re.findall(r'standard deduction[^.]*\$([0-9,]+)', full_text, re.IGNORECASE)
                    if std_amounts:
                        print(f'   ✅ STANDARD DEDUCTION AMOUNTS: ${", $".join(std_amounts)}')
                    
                    break
    except Exception as e:
        continue

print('\n' + '='*60)
print('🔍 CONCLUSION AND RECOMMENDATIONS')
print('='*60)
print('Based on this analysis:')
print('1. The "tax inflation adjustments" announcement focuses on HSA, estate tax, etc.')
print('2. Standard deduction amounts are typically in specific Revenue Procedures')
print('3. We need to look for Rev. Proc. 2024-40 or similar for 2025 tax year')
print('4. These are usually published in IRB bulletins in October/November')
print('5. We may need to enhance our RevProc stream to parse PDF content')
print('6. The current approach is getting SOME real tax data, but missing key items')
