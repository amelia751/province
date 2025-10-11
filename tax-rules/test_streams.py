#!/usr/bin/env python3
"""Test script to verify each stream actually retrieves real data from IRS sources."""

import sys
import os
import logging
from datetime import date, datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tax_rules_connector.http_client import IRSHttpClient
from tax_rules_connector.streams.newsroom_releases import NewsroomReleasesStream
from tax_rules_connector.streams.irb_bulletins import IRBBulletinsStream
from tax_rules_connector.streams.draft_forms import DraftFormsStream
from tax_rules_connector.streams.mef_summaries import MeFSummariesStream
from tax_rules_connector.streams.revproc_items import RevProcItemsStream
from tax_rules_connector.gemini_service import get_gemini_service

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_stream_connection(stream_name: str, stream) -> bool:
    """Test if a stream can connect to its source."""
    print(f"\n{'='*60}")
    print(f"Testing {stream_name} Connection")
    print(f"{'='*60}")
    
    try:
        result = stream.test_connection()
        print(f"✅ Connection test: {'PASSED' if result else 'FAILED'}")
        return result
    except Exception as e:
        print(f"❌ Connection test FAILED: {e}")
        return False


def test_stream_data_retrieval(stream_name: str, stream, max_items: int = 3) -> list:
    """Test if a stream can retrieve actual data."""
    print(f"\n📊 Testing {stream_name} Data Retrieval")
    print("-" * 40)
    
    try:
        # Get some sample data
        if hasattr(stream, '_get_releases_page'):
            # Newsroom releases
            data = stream._get_releases_page(0)
        elif hasattr(stream, '_get_bulletins_for_year'):
            # IRB bulletins
            data = stream._get_bulletins_for_year(2024)
        elif hasattr(stream, '_get_draft_forms'):
            # Draft forms
            data = stream._get_draft_forms()
        elif hasattr(stream, '_get_mef_summaries'):
            # MeF summaries
            data = stream._get_mef_summaries()
        elif hasattr(stream, '_find_inflation_revprocs'):
            # RevProc items
            revproc_urls = stream._find_inflation_revprocs()
            data = list(revproc_urls.keys())[:max_items]
        else:
            print("❌ No data retrieval method found")
            return []
        
        if not data:
            print("❌ No data retrieved")
            return []
        
        print(f"✅ Retrieved {len(data)} items")
        
        # Show sample data
        for i, item in enumerate(data[:max_items]):
            print(f"\n📄 Item {i+1}:")
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"  {key}: {value}")
            else:
                print(f"  {item}")
        
        return data
        
    except Exception as e:
        print(f"❌ Data retrieval FAILED: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_gemini_relevance(data_items: list, stream_name: str) -> None:
    """Test Gemini AI relevance detection on retrieved data."""
    print(f"\n🤖 Testing Gemini AI Relevance for {stream_name}")
    print("-" * 40)
    
    try:
        gemini = get_gemini_service()
        
        for i, item in enumerate(data_items[:2]):  # Test first 2 items
            if isinstance(item, dict):
                title = item.get('title', item.get('form_number', 'Unknown'))
                content = item.get('content_summary', item.get('notes', str(item)))
                url = item.get('url', item.get('source_url', ''))
            else:
                title = str(item)
                content = str(item)
                url = str(item) if 'http' in str(item) else ''
            
            print(f"\n🔍 Analyzing item {i+1}: {title[:50]}...")
            
            analysis = gemini.is_tax_relevant(title, content, url)
            
            relevant = analysis.get('relevant', False)
            confidence = analysis.get('confidence', 0.0)
            reason = analysis.get('reason', 'No reason provided')
            
            status = "✅ RELEVANT" if relevant else "❌ NOT RELEVANT"
            print(f"  {status} (confidence: {confidence:.2f})")
            print(f"  Reason: {reason}")
            
            if analysis.get('key_topics'):
                print(f"  Key topics: {', '.join(analysis['key_topics'][:3])}")
    
    except Exception as e:
        print(f"❌ Gemini analysis FAILED: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main test function."""
    print("🚀 Starting IRS Tax Rules Connector Stream Tests")
    print("=" * 60)
    
    # Initialize HTTP client
    http_client = IRSHttpClient()
    
    # Test streams
    streams_to_test = [
        ("Newsroom Releases", NewsroomReleasesStream(
            http_client, 
            "https://www.irs.gov/newsroom", 
            "federal", 
            "US"
        )),
        ("IRB Bulletins", IRBBulletinsStream(
            http_client,
            "https://www.irs.gov/irb",
            "federal",
            "US"
        )),
        ("Draft Forms", DraftFormsStream(
            http_client,
            "https://www.irs.gov/forms-pubs/draft-tax-forms",
            "federal",
            "US"
        )),
        ("MeF Summaries", MeFSummariesStream(
            http_client,
            "https://www.irs.gov/modernized-e-file-mf-business-rules-and-schemas",
            "federal",
            "US"
        )),
        ("RevProc Items", RevProcItemsStream(
            http_client,
            "federal",
            "US"
        ))
    ]
    
    results = {}
    
    for stream_name, stream in streams_to_test:
        try:
            # Test connection
            connection_ok = test_stream_connection(stream_name, stream)
            
            if connection_ok:
                # Test data retrieval
                data = test_stream_data_retrieval(stream_name, stream)
                
                if data:
                    # Test Gemini relevance
                    test_gemini_relevance(data, stream_name)
                    results[stream_name] = "✅ PASSED"
                else:
                    results[stream_name] = "❌ NO DATA"
            else:
                results[stream_name] = "❌ CONNECTION FAILED"
                
        except Exception as e:
            print(f"❌ {stream_name} test failed with error: {e}")
            results[stream_name] = f"❌ ERROR: {e}"
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    
    for stream_name, result in results.items():
        print(f"{stream_name:20} {result}")
    
    # Overall result
    passed = sum(1 for r in results.values() if "✅" in r)
    total = len(results)
    
    print(f"\n🎯 Overall: {passed}/{total} streams working")
    
    if passed == total:
        print("🎉 All streams are working correctly!")
    else:
        print("⚠️  Some streams need attention")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
