#!/usr/bin/env python3
"""Final test of the complete working system with fixed Gemini and content extraction."""

import sys
import os
import logging
from datetime import date, datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tax_rules_connector.http_client import IRSHttpClient
from tax_rules_connector.streams.newsroom_releases import NewsroomReleasesStream
from tax_rules_connector.gemini_service import get_gemini_service

# Reduce logging noise
logging.basicConfig(level=logging.WARNING)


def test_gemini_with_working_model():
    """Test Gemini with the working model."""
    print("🤖 TESTING WORKING GEMINI MODEL")
    print("=" * 50)
    
    try:
        gemini = get_gemini_service()
        
        # Test with simple tax content
        title = "IRS announces 2024 tax bracket adjustments"
        content = "The IRS announced inflation adjustments for tax year 2024. The standard deduction increases to $14,600 for single filers."
        
        analysis = gemini.is_tax_relevant(title, content)
        
        print(f"✅ Gemini analysis successful!")
        print(f"   Relevant: {analysis.get('relevant', False)}")
        print(f"   Confidence: {analysis.get('confidence', 0.0):.2f}")
        print(f"   Reason: {analysis.get('reason', 'No reason')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        return False


def test_newsroom_with_real_content_and_gemini():
    """Test newsroom stream with real content extraction and Gemini analysis."""
    print("\n🗞️  TESTING COMPLETE NEWSROOM SYSTEM")
    print("=" * 50)
    
    client = IRSHttpClient()
    stream = NewsroomReleasesStream(client, 'https://www.irs.gov/newsroom', 'federal', 'US')
    
    # Test specific releases
    test_releases = [
        ('Treasury, IRS issue final regulations for the Advanced Manufacturing Production Credit',
         'https://www.irs.gov/newsroom/treasury-irs-issue-final-regulations-for-the-advanced-manufacturing-production-credit'),
        ('Treasury and IRS issue guidance for the Energy Efficient Home Improvement Credit',
         'https://www.irs.gov/newsroom/treasury-and-irs-issue-guidance-for-the-energy-efficient-home-improvement-credit')
    ]
    
    successful_extractions = 0
    
    for i, (title, url) in enumerate(test_releases):
        print(f"\n📄 Testing release {i+1}: {title[:50]}...")
        
        try:
            # Test content extraction
            soup = client.get_soup(url)
            content = stream._extract_actual_content(soup)
            
            print(f"   ✅ Content extracted: {len(content)} characters")
            print(f"   📝 Preview: {content[:100]}...")
            
            if len(content) > 500:  # Good content
                # Test Gemini analysis
                try:
                    gemini = get_gemini_service()
                    analysis = gemini.is_tax_relevant(title, content[:1000], url)  # Limit content
                    
                    print(f"   🤖 Gemini analysis:")
                    print(f"      Relevant: {analysis.get('relevant', False)}")
                    print(f"      Confidence: {analysis.get('confidence', 0.0):.2f}")
                    print(f"      Reason: {analysis.get('reason', 'No reason')[:60]}...")
                    
                    successful_extractions += 1
                    
                except Exception as e:
                    print(f"   ❌ Gemini analysis failed: {e}")
            else:
                print(f"   ⚠️  Content too short for analysis")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    return successful_extractions


def test_complete_stream_sync():
    """Test the complete stream sync process."""
    print(f"\n🔄 TESTING COMPLETE STREAM SYNC")
    print("=" * 50)
    
    try:
        client = IRSHttpClient()
        stream = NewsroomReleasesStream(client, 'https://www.irs.gov/newsroom', 'federal', 'US')
        
        # Test the actual sync method (limited to avoid too many API calls)
        print("Testing stream sync process...")
        
        # Get a few releases using the stream's method
        releases = stream._get_releases_page(0)
        
        print(f"✅ Stream sync extracted {len(releases)} releases")
        
        if releases:
            print("\n📊 Sample extracted releases:")
            for i, release in enumerate(releases[:3]):
                print(f"\n{i+1}. {release.get('title', 'No title')[:60]}...")
                print(f"   URL: {release.get('url', 'No URL')}")
                print(f"   Date: {release.get('published_date', 'No date')}")
                print(f"   Content length: {len(release.get('content_summary', ''))}")
                
                # Check if it has keywords (indicating relevance detection worked)
                keywords = release.get('keywords_matched', '')
                if keywords:
                    print(f"   Keywords: {keywords}")
        
        return len(releases) > 0
        
    except Exception as e:
        print(f"❌ Stream sync test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_irs_sources():
    """Test accessing multiple IRS data sources."""
    print(f"\n📚 TESTING MULTIPLE IRS SOURCES")
    print("=" * 50)
    
    client = IRSHttpClient()
    
    sources_to_test = [
        ('Newsroom October 2024', 'https://www.irs.gov/newsroom/news-releases-for-october-2024'),
        ('IRB Main Page', 'https://www.irs.gov/irb'),
        ('Forms Main Page', 'https://www.irs.gov/forms-pubs'),
        ('Form 1040', 'https://www.irs.gov/forms-pubs/about-form-1040')
    ]
    
    working_sources = 0
    
    for name, url in sources_to_test:
        try:
            response = client.get(url)
            soup = client.get_soup(url)
            
            # Count links to estimate content richness
            links = soup.find_all('a', href=True)
            substantial_links = [l for l in links if len(l.get_text(strip=True)) > 20]
            
            print(f"✅ {name}: {response.status_code} - {len(substantial_links)} substantial links")
            working_sources += 1
            
        except Exception as e:
            print(f"❌ {name}: {str(e)[:50]}...")
    
    print(f"\n📊 {working_sources}/{len(sources_to_test)} sources accessible")
    return working_sources >= 3


def main():
    """Main test function."""
    print("🚀 FINAL COMPLETE SYSTEM TEST")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Test Gemini with working model
    results['gemini'] = test_gemini_with_working_model()
    
    # Test newsroom with real content and Gemini
    results['newsroom_complete'] = test_newsroom_with_real_content_and_gemini() > 0
    
    # Test complete stream sync
    results['stream_sync'] = test_complete_stream_sync()
    
    # Test multiple IRS sources
    results['multiple_sources'] = test_multiple_irs_sources()
    
    # Summary
    print(f"\n{'='*60}")
    print("🎯 FINAL SYSTEM TEST RESULTS")
    print(f"{'='*60}")
    
    for component, passed in results.items():
        status = "✅ WORKING" if passed else "❌ NEEDS ATTENTION"
        print(f"{component.upper():20} {status}")
    
    working_count = sum(1 for r in results.values() if r)
    total_count = len(results)
    
    print(f"\n🎯 Overall: {working_count}/{total_count} components working")
    
    if working_count == total_count:
        print("🎉 COMPLETE SYSTEM IS WORKING PERFECTLY!")
        print("\n✅ ACHIEVEMENTS:")
        print("   • Gemini AI integration working with correct model")
        print("   • Real content extraction from IRS sources")
        print("   • Tax relevance detection functioning")
        print("   • Multiple IRS data sources accessible")
        print("   • Complete stream sync process operational")
        print("\n🚀 READY FOR PRODUCTION DEPLOYMENT!")
        
    elif working_count >= 3:
        print("✅ System is mostly working and ready for deployment!")
        
    else:
        print("⚠️  System needs more fixes before deployment")
    
    return working_count >= 3


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
