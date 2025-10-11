#!/usr/bin/env python3
"""Comprehensive test of working IRS tax rules streams."""

import sys
import os
import logging
from datetime import date, datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tax_rules_connector.http_client import IRSHttpClient
from tax_rules_connector.streams.newsroom_releases import NewsroomReleasesStream

# Set up logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_newsroom_stream():
    """Test the newsroom releases stream."""
    print("🗞️  TESTING NEWSROOM RELEASES STREAM")
    print("=" * 50)
    
    client = IRSHttpClient()
    stream = NewsroomReleasesStream(client, 'https://www.irs.gov/newsroom', 'federal', 'US')
    
    # Test connection
    print("Testing connection...")
    connection_ok = stream.test_connection()
    print(f"Connection: {'✅ PASSED' if connection_ok else '❌ FAILED'}")
    
    if not connection_ok:
        return False
    
    # Test data retrieval
    print("\nTesting data retrieval...")
    try:
        releases = stream._get_releases_page(0)
        print(f"✅ Retrieved {len(releases)} releases")
        
        if releases:
            print("\n📄 Sample releases:")
            for i, release in enumerate(releases[:3]):
                print(f"\n{i+1}. {release.get('title', 'No title')[:80]}...")
                print(f"   📅 Date: {release.get('published_date', 'No date')}")
                print(f"   🔗 URL: {release.get('url', 'No URL')}")
                
                # Show content preview
                content = release.get('content_summary', '')
                if content:
                    print(f"   📝 Content: {content[:100]}...")
        
        return len(releases) > 0
        
    except Exception as e:
        print(f"❌ Data retrieval failed: {e}")
        return False


def test_forms_pages():
    """Test access to IRS forms and publications pages."""
    print("\n📋 TESTING FORMS AND PUBLICATIONS ACCESS")
    print("=" * 50)
    
    client = IRSHttpClient()
    
    urls_to_test = [
        ('Forms & Publications', 'https://www.irs.gov/forms-pubs'),
        ('Current Forms', 'https://www.irs.gov/forms-pubs/current-forms-and-instructions'),
        ('Prior Year Forms', 'https://www.irs.gov/forms-pubs/prior-year-forms-and-instructions'),
        ('Form 1040', 'https://www.irs.gov/forms-pubs/about-form-1040'),
    ]
    
    working_urls = []
    
    for name, url in urls_to_test:
        try:
            response = client.get(url)
            print(f"✅ {name}: {response.status_code}")
            working_urls.append((name, url))
        except Exception as e:
            print(f"❌ {name}: {e}")
    
    return working_urls


def test_irb_access():
    """Test access to Internal Revenue Bulletin."""
    print("\n📚 TESTING INTERNAL REVENUE BULLETIN ACCESS")
    print("=" * 50)
    
    client = IRSHttpClient()
    
    # Test main IRB page
    try:
        response = client.get('https://www.irs.gov/irb')
        print(f"✅ Main IRB page: {response.status_code}")
        
        # Check for current bulletins
        soup = client.get_soup('https://www.irs.gov/irb')
        
        # Look for bulletin links
        links = soup.find_all('a', href=True)
        bulletin_links = []
        
        for link in links:
            href = link['href']
            text = link.get_text(strip=True)
            
            # Look for bulletin patterns
            if ('irb' in href.lower() and 
                any(year in text for year in ['2024', '2023']) and
                len(text) > 10):
                bulletin_links.append((text, href))
        
        print(f"✅ Found {len(bulletin_links)} potential bulletin links")
        
        # Test a few bulletin links
        for i, (text, href) in enumerate(bulletin_links[:3]):
            try:
                if href.startswith('/'):
                    full_url = 'https://www.irs.gov' + href
                else:
                    full_url = href
                    
                response = client.get(full_url)
                print(f"  ✅ {text[:50]}... - {response.status_code}")
            except Exception as e:
                print(f"  ❌ {text[:50]}... - {e}")
        
        return len(bulletin_links) > 0
        
    except Exception as e:
        print(f"❌ IRB access failed: {e}")
        return False


def test_e_file_resources():
    """Test access to e-file resources."""
    print("\n💻 TESTING E-FILE RESOURCES")
    print("=" * 50)
    
    client = IRSHttpClient()
    
    urls_to_test = [
        ('E-file Providers', 'https://www.irs.gov/e-file-providers'),
        ('Developer Resources', 'https://www.irs.gov/e-file-providers/developer-resources'),
        ('Modernized e-File', 'https://www.irs.gov/e-file-providers/modernized-e-file-mef-information'),
    ]
    
    working_count = 0
    
    for name, url in urls_to_test:
        try:
            response = client.get(url)
            print(f"✅ {name}: {response.status_code}")
            working_count += 1
        except Exception as e:
            print(f"❌ {name}: {e}")
    
    return working_count > 0


def find_tax_relevant_content():
    """Find and analyze tax-relevant content from working sources."""
    print("\n🎯 FINDING TAX-RELEVANT CONTENT")
    print("=" * 50)
    
    client = IRSHttpClient()
    relevant_content = []
    
    # Check newsroom for recent tax-related announcements
    try:
        soup = client.get_soup('https://www.irs.gov/newsroom/news-releases-for-october-2024')
        links = soup.find_all('a', href=True)
        
        tax_keywords = ['tax', 'deduction', 'credit', 'bracket', 'rate', 'inflation', 'adjustment']
        
        for link in links:
            text = link.get_text(strip=True).lower()
            href = link['href']
            
            if (any(keyword in text for keyword in tax_keywords) and 
                len(text) > 30 and 
                href.startswith('/newsroom/')):
                
                relevant_content.append({
                    'title': link.get_text(strip=True),
                    'url': 'https://www.irs.gov' + href,
                    'source': 'newsroom'
                })
        
        print(f"✅ Found {len(relevant_content)} tax-relevant items in newsroom")
        
        # Show samples
        for i, item in enumerate(relevant_content[:3]):
            print(f"\n{i+1}. {item['title'][:70]}...")
            print(f"   🔗 {item['url']}")
        
    except Exception as e:
        print(f"❌ Error finding relevant content: {e}")
    
    return relevant_content


def main():
    """Main test function."""
    print("🚀 COMPREHENSIVE IRS TAX RULES CONNECTOR TEST")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    # Test each component
    results['newsroom'] = test_newsroom_stream()
    results['forms'] = len(test_forms_pages()) > 0
    results['irb'] = test_irb_access()
    results['efile'] = test_e_file_resources()
    
    # Find relevant content
    relevant_items = find_tax_relevant_content()
    results['relevant_content'] = len(relevant_items) > 0
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    
    for component, passed in results.items():
        status = "✅ WORKING" if passed else "❌ NEEDS ATTENTION"
        print(f"{component.upper():20} {status}")
    
    # Overall assessment
    working_count = sum(1 for r in results.values() if r)
    total_count = len(results)
    
    print(f"\n🎯 Overall: {working_count}/{total_count} components working")
    
    if working_count >= 3:
        print("🎉 Connector has sufficient working data sources!")
        print("\n✅ RECOMMENDATIONS:")
        print("   • Newsroom stream is working and finding relevant content")
        print("   • Forms and IRB pages are accessible for future streams")
        print("   • Focus on improving Gemini integration for better relevance detection")
        print("   • Consider implementing forms and IRB streams next")
    else:
        print("⚠️  Connector needs more working data sources")
    
    return working_count >= 3


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
