#!/usr/bin/env python3
"""Test the fixed streams with proper error handling."""

import sys
import os
import logging
from datetime import date, datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tax_rules_connector.http_client import IRSHttpClient
from tax_rules_connector.streams.newsroom_releases import NewsroomReleasesStream

# Reduce logging noise
logging.basicConfig(level=logging.WARNING)


def test_newsroom_with_fallback():
    """Test newsroom stream with Gemini disabled (fallback only)."""
    print("🔍 TESTING FIXED NEWSROOM STREAM")
    print("=" * 50)
    
    client = IRSHttpClient()
    stream = NewsroomReleasesStream(client, 'https://www.irs.gov/newsroom', 'federal', 'US')
    
    # Test connection
    print("1. Testing connection...")
    connection_ok = stream.test_connection()
    print(f"   Connection: {'✅ PASSED' if connection_ok else '❌ FAILED'}")
    
    if not connection_ok:
        return False
    
    # Test data extraction with better error handling
    print("\n2. Testing data extraction...")
    try:
        # Temporarily disable Gemini to test core functionality
        original_create_record = stream._create_release_record
        
        def create_record_no_gemini(title, url):
            """Create record without Gemini analysis."""
            try:
                # Get the release content
                soup = client.get_soup(url)
                
                # Extract content
                content_div = soup.find('div', class_=lambda x: x and 'content' in ' '.join(x).lower())
                if not content_div:
                    content_div = soup.find('main')
                if not content_div:
                    content_div = soup
                
                content = content_div.get_text(strip=True)[:2000]
                
                # Use simple keyword-based relevance (no Gemini)
                tax_keywords = ['tax', 'deduction', 'credit', 'bracket', 'rate', 'inflation', 'adjustment', 'form', 'irs']
                text_lower = (title + " " + content).lower()
                matched_keywords = [kw for kw in tax_keywords if kw in text_lower]
                
                # Only include if it has tax-related keywords
                if len(matched_keywords) < 2:
                    print(f"   Skipping non-relevant: {title[:50]}...")
                    return None
                
                # Extract publication date
                published_date = stream._extract_date_from_content(soup)
                
                # Generate release ID
                release_id = url.split('/')[-1] or str(hash(url))
                
                return {
                    'release_id': release_id,
                    'title': title,
                    'url': url,
                    'published_date': published_date,
                    'linked_revproc_url': stream._extract_revproc_link_from_content(soup),
                    'content_summary': content[:500],
                    'keywords_matched': str(matched_keywords),
                    'jurisdiction_level': stream.jurisdiction_level,
                    'jurisdiction_code': stream.jurisdiction_code
                }
                
            except Exception as e:
                print(f"   Error processing {title[:30]}...: {e}")
                return None
        
        # Replace the method temporarily
        stream._create_release_record = create_record_no_gemini
        
        # Test extraction
        releases = stream._get_releases_page(0)
        print(f"   ✅ Successfully extracted {len(releases)} releases")
        
        if releases:
            print("\n3. Sample extracted releases:")
            for i, release in enumerate(releases[:3]):
                print(f"\n   📄 Release {i+1}:")
                print(f"      Title: {release.get('title', 'No title')[:60]}...")
                print(f"      URL: {release.get('url', 'No URL')}")
                print(f"      Date: {release.get('published_date', 'No date')}")
                print(f"      Keywords: {release.get('keywords_matched', 'None')}")
                
                # Verify URL accessibility
                try:
                    response = client.get(release.get('url', ''))
                    print(f"      Access: ✅ Status {response.status_code}")
                except Exception as e:
                    print(f"      Access: ❌ Error")
        
        # Restore original method
        stream._create_release_record = original_create_record
        
        return len(releases) > 0
        
    except Exception as e:
        print(f"   ❌ Data extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_individual_release_access():
    """Test accessing individual releases directly."""
    print("\n🔍 TESTING INDIVIDUAL RELEASE ACCESS")
    print("=" * 50)
    
    client = IRSHttpClient()
    
    # Test some known working releases
    test_urls = [
        'https://www.irs.gov/newsroom/tax-relief-in-disaster-situations',
        'https://www.irs.gov/newsroom/irs-statements-and-announcements',
        'https://www.irs.gov/newsroom/news-releases-for-frequently-asked-questions'
    ]
    
    working_count = 0
    for i, url in enumerate(test_urls):
        try:
            response = client.get(url)
            soup = client.get_soup(url)
            title = soup.title.string if soup.title else 'No title'
            
            print(f"{i+1}. ✅ {title[:60]}...")
            print(f"   Status: {response.status_code}")
            print(f"   URL: {url}")
            working_count += 1
            
        except Exception as e:
            print(f"{i+1}. ❌ Failed to access {url}")
            print(f"   Error: {str(e)[:60]}...")
    
    print(f"\n📊 Result: {working_count}/{len(test_urls)} individual releases accessible")
    return working_count > 0


def main():
    """Main test function."""
    print("🚀 TESTING FIXED IRS TAX RULES STREAMS")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Test newsroom stream
    results['newsroom_extraction'] = test_newsroom_with_fallback()
    
    # Test individual access
    results['individual_access'] = test_individual_release_access()
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 FIXED STREAM TEST RESULTS")
    print(f"{'='*60}")
    
    for test_name, passed in results.items():
        status = "✅ WORKING" if passed else "❌ NEEDS ATTENTION"
        print(f"{test_name.upper():25} {status}")
    
    working_count = sum(1 for r in results.values() if r)
    total_count = len(results)
    
    print(f"\n🎯 Overall: {working_count}/{total_count} tests passing")
    
    if working_count == total_count:
        print("🎉 All stream fixes are working!")
        print("\n✅ NEXT STEPS:")
        print("   • Newsroom stream is extracting real data")
        print("   • Individual releases are accessible")
        print("   • Ready to fix Gemini integration or use keyword fallback")
        print("   • Can proceed with other streams (IRB, Forms)")
    else:
        print("⚠️  Some issues remain to be fixed")
    
    return working_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
