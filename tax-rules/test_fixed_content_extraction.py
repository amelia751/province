#!/usr/bin/env python3
"""Test extracting real content with fixed selectors."""

import sys
import os
import logging
from datetime import date, datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tax_rules_connector.http_client import IRSHttpClient

# Reduce logging noise
logging.basicConfig(level=logging.WARNING)


def extract_actual_content(soup):
    """Extract actual article content from IRS page."""
    
    # Try selectors in order of preference
    content_selectors = [
        'article',  # This worked in our debug
        'div.field-item',
        'main',
        'div[class*="field-items"]',
        'div.content-area',
        'div.node-content'
    ]
    
    for selector in content_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text(strip=True)
            # Look for substantial content (not just navigation)
            if (len(text) > 300 and 
                'official website' not in text.lower()[:100] and
                'skip to main content' not in text.lower()[:100]):
                return ' '.join(text.split())  # Clean whitespace
    
    # Fallback: look for paragraphs with substantial content
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


def test_newsroom_content_extraction():
    """Test extracting real newsroom content."""
    print("🗞️  TESTING FIXED NEWSROOM EXTRACTION")
    print("=" * 50)
    
    client = IRSHttpClient()
    
    # Test specific releases we know exist
    test_releases = [
        ('Treasury, IRS issue final regulations for the Advanced Manufacturing Production Credit',
         'https://www.irs.gov/newsroom/treasury-irs-issue-final-regulations-for-the-advanced-manufacturing-production-credit'),
        ('Treasury and IRS issue guidance for the Energy Efficient Home Improvement Credit',
         'https://www.irs.gov/newsroom/treasury-and-irs-issue-guidance-for-the-energy-efficient-home-improvement-credit'),
        ('Tax relief in disaster situations',
         'https://www.irs.gov/newsroom/tax-relief-in-disaster-situations')
    ]
    
    extracted_content = []
    
    for i, (title, url) in enumerate(test_releases):
        print(f"\n📄 Release {i+1}: {title[:50]}...")
        
        try:
            soup = client.get_soup(url)
            content_text = extract_actual_content(soup)
            
            if content_text:
                extracted_content.append({
                    'title': title,
                    'url': url,
                    'content_length': len(content_text),
                    'content_preview': content_text[:500] + "..." if len(content_text) > 500 else content_text,
                    'full_content': content_text
                })
                
                print(f"   ✅ Extracted {len(content_text)} characters")
                print(f"   📝 Preview: {content_text[:150]}...")
            else:
                print(f"   ❌ No substantial content found")
                
        except Exception as e:
            print(f"   ❌ Failed to extract: {e}")
    
    return extracted_content


def test_gemini_with_fixed_content(content_samples):
    """Test Gemini with properly extracted content."""
    print(f"\n🤖 TESTING GEMINI WITH FIXED CONTENT")
    print("=" * 50)
    
    try:
        from dotenv import load_dotenv
        import google.generativeai as genai
        
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        for i, content in enumerate(content_samples):
            print(f"\n🔍 Testing content {i+1}: {content['title'][:50]}...")
            print(f"   Content length: {content['content_length']} chars")
            
            # Test with different approaches
            test_approaches = [
                {
                    'name': 'Simple question',
                    'prompt': f"Is this about tax regulations? Answer YES or NO: {content['content_preview'][:200]}",
                    'max_tokens': 5
                },
                {
                    'name': 'Neutral analysis',
                    'prompt': f"Summarize this government document in one sentence: {content['content_preview'][:300]}",
                    'max_tokens': 50
                },
                {
                    'name': 'Topic identification',
                    'prompt': f"What is the main topic of this text? {content['content_preview'][:200]}",
                    'max_tokens': 20
                }
            ]
            
            for approach in test_approaches:
                try:
                    response = model.generate_content(
                        approach['prompt'],
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.1,
                            max_output_tokens=approach['max_tokens']
                        )
                    )
                    
                    print(f"      ✅ {approach['name']}: {response.text.strip()}")
                    break  # If one works, move to next content
                    
                except Exception as e:
                    print(f"      ❌ {approach['name']}: {str(e)[:60]}...")
                    
                    # Check response details for debugging
                    try:
                        if hasattr(response, 'candidates') and response.candidates:
                            candidate = response.candidates[0]
                            print(f"         Finish reason: {candidate.finish_reason}")
                            if hasattr(candidate, 'safety_ratings') and candidate.safety_ratings:
                                print(f"         Safety ratings: {len(candidate.safety_ratings)} ratings")
                    except:
                        pass
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini testing setup failed: {e}")
        return False


def test_simple_gemini_bypass():
    """Test if we can bypass Gemini safety filters with different content."""
    print(f"\n🔧 TESTING GEMINI SAFETY BYPASS")
    print("=" * 50)
    
    try:
        from dotenv import load_dotenv
        import google.generativeai as genai
        
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Test with completely neutral content
        neutral_tests = [
            "The weather is sunny today. Is this about weather?",
            "This document discusses tax policy changes. What is the topic?",
            "Government announces new regulations. Summarize in 5 words.",
            "IRS updates tax forms for 2024. Is this tax-related?"
        ]
        
        for i, test_prompt in enumerate(neutral_tests):
            print(f"\n🔍 Test {i+1}: {test_prompt[:40]}...")
            
            try:
                response = model.generate_content(
                    test_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=20
                    )
                )
                
                print(f"   ✅ Success: {response.text.strip()}")
                
            except Exception as e:
                print(f"   ❌ Failed: {str(e)[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Bypass testing failed: {e}")
        return False


def main():
    """Main test function."""
    print("🚀 FIXED CONTENT EXTRACTION & GEMINI TEST")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Extract real content with fixed selectors
    newsroom_content = test_newsroom_content_extraction()
    
    # Test Gemini with properly extracted content
    if newsroom_content:
        test_gemini_with_fixed_content(newsroom_content)
    
    # Test Gemini safety bypass
    test_simple_gemini_bypass()
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 FIXED EXTRACTION SUMMARY")
    print(f"{'='*60}")
    
    if newsroom_content:
        print(f"✅ Successfully extracted {len(newsroom_content)} pieces of real content")
        
        for i, content in enumerate(newsroom_content):
            print(f"\n{i+1}. {content['title'][:60]}...")
            print(f"   Length: {content['content_length']} characters")
            print(f"   Preview: {content['content_preview'][:100]}...")
        
        avg_length = sum(c['content_length'] for c in newsroom_content) / len(newsroom_content)
        print(f"\nAverage content length: {avg_length:.0f} characters")
        
        if avg_length > 500:
            print("🎉 Content extraction is working properly!")
        else:
            print("⚠️  Content extraction may still need improvement")
    else:
        print("❌ No content was successfully extracted")
    
    return len(newsroom_content) > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
