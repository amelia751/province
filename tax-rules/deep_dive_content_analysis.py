#!/usr/bin/env python3
"""Deep dive analysis of content completeness and accuracy."""

import sys
sys.path.append('src')
import re
from tax_rules_connector.streams.newsroom_releases import NewsroomReleasesStream
from tax_rules_connector.http_client import IRSHttpClient

print('🔍 DEEP DIVE: Content Completeness Analysis')
print('=' * 60)

http_client = IRSHttpClient(timeout=30, max_retries=2)
stream = NewsroomReleasesStream(
    http_client,
    'https://www.irs.gov/newsroom',
    'federal',
    'US'
)

# Test the specific inflation announcement
inflation_url = 'https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2025'

print(f'🎯 Testing: {inflation_url}')
print()

# Get the FULL content without limits
try:
    soup = http_client.get_soup(inflation_url)
    if soup:
        # Get ALL content areas
        content_areas = soup.find_all(['div', 'article', 'main'], 
                                    class_=['content', 'main-content', 'article-content', 'field-item'])
        
        if not content_areas:
            content_areas = soup.find_all('p')
        
        # Extract ALL text content (no limits)
        full_text = ""
        for area in content_areas:
            text = area.get_text(separator=' ', strip=True)
            if len(text) > 50:
                full_text += text + " "
        
        print(f'📊 FULL CONTENT ANALYSIS:')
        print(f'   Total content length: {len(full_text):,} characters')
        print(f'   Previous limit was: 2,000 characters')
        if len(full_text) > 2000:
            print(f'   We were missing: {len(full_text) - 2000:,} characters ({((len(full_text) - 2000) / len(full_text) * 100):.1f}% of content)')
        print()
        
        # Extract ALL tax amounts from full content
        dollar_pattern = r'\$([0-9,]+(?:\.[0-9]{2})?)'
        dollar_matches = list(re.finditer(dollar_pattern, full_text))
        
        print(f'💰 TAX AMOUNTS IN FULL CONTENT:')
        print(f'   Total dollar amounts found: {len(dollar_matches)}')
        
        # Show all amounts with context
        for i, match in enumerate(dollar_matches):
            amount_str = match.group(1).replace(',', '')
            try:
                amount = float(amount_str)
                # Get more context around the amount
                start = max(0, match.start() - 100)
                end = min(len(full_text), match.end() + 100)
                context = full_text[start:end].strip()
                
                print(f'   {i+1:2d}. ${amount_str:>10} - {context}')
                
            except ValueError:
                continue
        
        print()
        
        # Look for specific tax terms in full content
        tax_terms = [
            'standard deduction', 'tax bracket', 'earned income tax credit',
            'child tax credit', 'estate tax', 'gift tax', 'hsa', 'ira',
            'foreign earned income', 'adoption credit', 'alternative minimum tax'
        ]
        
        print(f'🔍 TAX TERMS ANALYSIS:')
        found_terms = []
        for term in tax_terms:
            if term.lower() in full_text.lower():
                found_terms.append(term)
                # Find sentences containing this term
                sentences = full_text.split('.')
                term_sentences = [s.strip() for s in sentences if term.lower() in s.lower()]
                print(f'   ✅ {term.upper()}: {len(term_sentences)} mentions')
                for sentence in term_sentences[:2]:  # Show first 2 sentences
                    print(f'      "{sentence[:120]}..."')
        
        print(f'\n📋 SUMMARY:')
        print(f'   Terms found: {len(found_terms)}/{len(tax_terms)}')
        missing_terms = [t for t in tax_terms if t not in found_terms]
        if missing_terms:
            print(f'   Missing terms: {missing_terms}')
        else:
            print(f'   All major tax terms found!')
        
        # Check for standard deduction amounts specifically
        print(f'\n🎯 STANDARD DEDUCTION SEARCH:')
        std_ded_pattern = r'standard deduction[^.]*\$([0-9,]+)'
        std_matches = re.findall(std_ded_pattern, full_text, re.IGNORECASE)
        if std_matches:
            print(f'   Found standard deduction amounts: {std_matches}')
        else:
            print(f'   No standard deduction amounts found in this announcement')
        
        # Check for tax bracket information
        print(f'\n🎯 TAX BRACKET SEARCH:')
        bracket_pattern = r'tax bracket[^.]*\$([0-9,]+)'
        bracket_matches = re.findall(bracket_pattern, full_text, re.IGNORECASE)
        if bracket_matches:
            print(f'   Found tax bracket amounts: {bracket_matches}')
        else:
            print(f'   No tax bracket amounts found in this announcement')
        
    else:
        print('❌ Could not fetch content')
        
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()

print('\n' + '='*60)
print('🔍 TESTING OTHER ANNOUNCEMENTS')
print('='*60)

# Test a few more announcements to see what we're getting
test_urls = [
    'https://www.irs.gov/newsroom/treasury-and-irs-issue-guidance-for-the-energy-efficient-home-improvement-credit',
    'https://www.irs.gov/newsroom/irs-announces-2024-tax-year-inflation-adjustments'
]

for url in test_urls:
    print(f'\n🎯 Testing: {url.split("/")[-1][:60]}...')
    try:
        soup = http_client.get_soup(url)
        if soup:
            # Get content
            content_areas = soup.find_all('p')
            full_text = ""
            for area in content_areas:
                text = area.get_text(separator=' ', strip=True)
                if len(text) > 50:
                    full_text += text + " "
            
            print(f'   Content length: {len(full_text):,} characters')
            
            # Count dollar amounts
            dollar_matches = re.findall(r'\$([0-9,]+)', full_text)
            print(f'   Dollar amounts found: {len(dollar_matches)}')
            if dollar_matches:
                print(f'   Sample amounts: {dollar_matches[:5]}')
            
            # Check for key tax terms
            key_terms = ['standard deduction', 'tax bracket', 'credit', 'deduction']
            found = [term for term in key_terms if term.lower() in full_text.lower()]
            print(f'   Key tax terms: {found}')
            
        else:
            print('   ❌ Could not fetch')
    except Exception as e:
        print(f'   ❌ Error: {e}')
