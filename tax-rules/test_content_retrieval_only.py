#!/usr/bin/env python3
"""Test retrieving actual article content from all IRS sources - no filtering."""

import sys
import os
import logging
from datetime import date, datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tax_rules_connector.http_client import IRSHttpClient

# Reduce logging noise
logging.basicConfig(level=logging.WARNING)


def extract_article_content(soup):
    """Extract actual article content from any IRS page."""
    
    # Try different content selectors in order of preference
    content_selectors = [
        'article',  # Main article content
        'div.field-item',
        'main',
        'div[class*="field-items"]',
        'div.content-area',
        'div.node-content',
        'div[class*="content"]'
    ]
    
    for selector in content_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text(strip=True)
            # Look for substantial content (not navigation/header)
            if (len(text) > 300 and 
                'official website' not in text.lower()[:100] and
                'skip to main content' not in text.lower()[:100]):
                return ' '.join(text.split())  # Clean whitespace
    
    # Fallback: collect substantial paragraphs
    paragraphs = soup.find_all('p')
    substantial_content = []
    
    for p in paragraphs:
        text = p.get_text(strip=True)
        if (len(text) > 50 and 
            'official website' not in text.lower() and
            'skip to main' not in text.lower() and
            '.gov website' not in text.lower()):
            substantial_content.append(text)
    
    if substantial_content:
        return ' '.join(substantial_content)
    
    return ""


def test_newsroom_content_retrieval():
    """Test retrieving actual content from newsroom releases."""
    print("🗞️  NEWSROOM CONTENT RETRIEVAL")
    print("=" * 50)
    
    client = IRSHttpClient()
    
    # Get October 2024 releases
    soup = client.get_soup('https://www.irs.gov/newsroom/news-releases-for-october-2024')
    links = soup.find_all('a', href=True)
    
    # Find all newsroom releases (no filtering)
    newsroom_releases = []
    for link in links:
        href = link['href']
        text = link.get_text(strip=True)
        if href.startswith('/newsroom/') and len(text) > 20:
            newsroom_releases.append((text, 'https://www.irs.gov' + href))
    
    print(f"Found {len(newsroom_releases)} newsroom releases")
    
    # Extract content from first 5 releases
    successful_extractions = 0
    for i, (title, url) in enumerate(newsroom_releases[:5]):
        print(f"\n📄 Release {i+1}: {title[:60]}...")
        
        try:
            release_soup = client.get_soup(url)
            content = extract_article_content(release_soup)
            
            if content and len(content) > 200:
                successful_extractions += 1
                print(f"   ✅ Content: {len(content)} chars")
                print(f"   📝 Preview: {content[:150]}...")
            else:
                print(f"   ⚠️  Limited content: {len(content)} chars")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    print(f"\n📊 Successfully extracted content from {successful_extractions}/{min(5, len(newsroom_releases))} releases")
    return successful_extractions


def test_irb_content_retrieval():
    """Test retrieving actual content from IRB bulletins."""
    print("\n📚 IRB BULLETIN CONTENT RETRIEVAL")
    print("=" * 50)
    
    client = IRSHttpClient()
    
    # Get main IRB page
    soup = client.get_soup('https://www.irs.gov/irb')
    links = soup.find_all('a', href=True)
    
    # Find bulletin links
    import re
    bulletin_links = []
    for link in links:
        href = link['href']
        text = link.get_text(strip=True)
        if re.search(r'202[34]-\d+', href) and 'bulletin' in text.lower():
            bulletin_links.append((text, href))
    
    print(f"Found {len(bulletin_links)} bulletin links")
    
    # Extract content from first 3 bulletins
    successful_extractions = 0
    for i, (title, href) in enumerate(bulletin_links[:3]):
        print(f"\n📄 Bulletin {i+1}: {title[:60]}...")
        
        try:
            full_url = 'https://www.irs.gov' + href if href.startswith('/') else href
            bulletin_soup = client.get_soup(full_url)
            content = extract_article_content(bulletin_soup)
            
            if content and len(content) > 200:
                successful_extractions += 1
                print(f"   ✅ Content: {len(content)} chars")
                print(f"   📝 Preview: {content[:150]}...")
            else:
                print(f"   ⚠️  Limited content: {len(content)} chars")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    print(f"\n📊 Successfully extracted content from {successful_extractions}/{min(3, len(bulletin_links))} bulletins")
    return successful_extractions


def test_forms_content_retrieval():
    """Test retrieving actual content from forms pages."""
    print("\n📋 FORMS CONTENT RETRIEVAL")
    print("=" * 50)
    
    client = IRSHttpClient()
    
    # Test key forms pages
    key_forms = [
        ('Form 1040', '/forms-pubs/about-form-1040'),
        ('Form 1040-X', '/forms-pubs/about-form-1040x'),
        ('Schedule A', '/forms-pubs/about-schedule-a-form-1040'),
        ('Form W-2', '/forms-pubs/about-form-w2'),
        ('Form 1099', '/forms-pubs/about-form-1099-misc')
    ]
    
    successful_extractions = 0
    for name, path in key_forms:
        print(f"\n📄 Form: {name}")
        
        try:
            full_url = f'https://www.irs.gov{path}'
            form_soup = client.get_soup(full_url)
            content = extract_article_content(form_soup)
            
            if content and len(content) > 200:
                successful_extractions += 1
                print(f"   ✅ Content: {len(content)} chars")
                print(f"   📝 Preview: {content[:150]}...")
            else:
                print(f"   ⚠️  Limited content: {len(content)} chars")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    print(f"\n📊 Successfully extracted content from {successful_extractions}/{len(key_forms)} forms")
    return successful_extractions


def test_efile_content_retrieval():
    """Test retrieving actual content from e-file resources."""
    print("\n💻 E-FILE CONTENT RETRIEVAL")
    print("=" * 50)
    
    client = IRSHttpClient()
    
    # Get e-file page
    soup = client.get_soup('https://www.irs.gov/e-file-providers')
    links = soup.find_all('a', href=True)
    
    # Find e-file resource links
    efile_links = []
    for link in links:
        href = link['href']
        text = link.get_text(strip=True).lower()
        if (href.startswith('/e-file') and len(text) > 15 and
            ('modernized' in text or 'provider' in text or 'business' in text)):
            efile_links.append((link.get_text(strip=True), href))
    
    print(f"Found {len(efile_links)} e-file resource links")
    
    # Extract content from first 3 resources
    successful_extractions = 0
    for i, (title, href) in enumerate(efile_links[:3]):
        print(f"\n📄 E-file resource {i+1}: {title[:60]}...")
        
        try:
            full_url = f'https://www.irs.gov{href}'
            efile_soup = client.get_soup(full_url)
            content = extract_article_content(efile_soup)
            
            if content and len(content) > 200:
                successful_extractions += 1
                print(f"   ✅ Content: {len(content)} chars")
                print(f"   📝 Preview: {content[:150]}...")
            else:
                print(f"   ⚠️  Limited content: {len(content)} chars")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    print(f"\n📊 Successfully extracted content from {successful_extractions}/{min(3, len(efile_links))} e-file resources")
    return successful_extractions


def test_additional_tax_sources():
    """Test retrieving content from additional tax-related sources."""
    print("\n📖 ADDITIONAL TAX SOURCES")
    print("=" * 50)
    
    client = IRSHttpClient()
    
    # Test additional IRS sources
    additional_sources = [
        ('Tax Code Regulations', '/regulations'),
        ('Tax Topics', '/taxtopics'),
        ('Publications', '/publications'),
        ('Instructions', '/instructions'),
        ('Tax Law Changes', '/tax-reform')
    ]
    
    successful_extractions = 0
    for name, path in additional_sources:
        print(f"\n📄 Source: {name}")
        
        try:
            full_url = f'https://www.irs.gov{path}'
            source_soup = client.get_soup(full_url)
            content = extract_article_content(source_soup)
            
            if content and len(content) > 200:
                successful_extractions += 1
                print(f"   ✅ Content: {len(content)} chars")
                print(f"   📝 Preview: {content[:150]}...")
            else:
                print(f"   ⚠️  Limited/No content: {len(content)} chars")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    print(f"\n📊 Successfully extracted content from {successful_extractions}/{len(additional_sources)} additional sources")
    return successful_extractions


def main():
    """Main test function."""
    print("🚀 IRS CONTENT RETRIEVAL TEST (NO FILTERING)")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nGoal: Retrieve actual article content from all IRS sources")
    print("Note: No filtering or relevance detection - just pure content extraction")
    
    # Test all sources
    results = {
        'newsroom': test_newsroom_content_retrieval(),
        'irb_bulletins': test_irb_content_retrieval(),
        'forms': test_forms_content_retrieval(),
        'efile': test_efile_content_retrieval(),
        'additional': test_additional_tax_sources()
    }
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 CONTENT RETRIEVAL SUMMARY")
    print(f"{'='*60}")
    
    total_successful = 0
    for source, count in results.items():
        print(f"{source.upper():15} {count} successful extractions")
        total_successful += count
    
    print(f"\n🎯 Total: {total_successful} successful content extractions")
    
    if total_successful >= 10:
        print("🎉 EXCELLENT! Content retrieval is working across multiple sources")
        print("\n✅ NEXT STEPS:")
        print("   • Content extraction is working properly")
        print("   • Ready to implement stream classes")
        print("   • Can add relevance filtering later")
        
    elif total_successful >= 5:
        print("✅ GOOD! Content retrieval is working for most sources")
        print("   • Core functionality is operational")
        
    else:
        print("⚠️  Content retrieval needs improvement")
        print("   • Check content extraction selectors")
        print("   • Verify IRS page structures")
    
    return total_successful >= 5


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
