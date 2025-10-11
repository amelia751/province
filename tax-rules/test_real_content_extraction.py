#!/usr/bin/env python3
"""Test retrieving real content from each IRS stream source."""

import sys
import os
import logging
from datetime import date, datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tax_rules_connector.http_client import IRSHttpClient

# Reduce logging noise
logging.basicConfig(level=logging.WARNING)


def extract_newsroom_content():
    """Extract real content from newsroom releases."""
    print("🗞️  EXTRACTING NEWSROOM CONTENT")
    print("=" * 50)
    
    client = IRSHttpClient()
    
    # Get October 2024 releases
    soup = client.get_soup('https://www.irs.gov/newsroom/news-releases-for-october-2024')
    links = soup.find_all('a', href=True)
    
    # Find tax-relevant releases
    tax_keywords = ['tax', 'credit', 'deduction', 'regulation', 'guidance']
    relevant_releases = []
    
    for link in links:
        text = link.get_text(strip=True)
        href = link['href']
        
        if (href.startswith('/newsroom/') and 
            any(keyword in text.lower() for keyword in tax_keywords) and
            len(text) > 30):
            relevant_releases.append((text, 'https://www.irs.gov' + href))
    
    print(f"Found {len(relevant_releases)} tax-relevant releases")
    
    # Extract full content from first 3 releases
    extracted_content = []
    for i, (title, url) in enumerate(relevant_releases[:3]):
        print(f"\n📄 Release {i+1}: {title[:60]}...")
        
        try:
            # Get the full page content
            release_soup = client.get_soup(url)
            
            # Extract main content (try different selectors)
            content_selectors = [
                'div[class*="content"]',
                'main',
                'article',
                'div[class*="body"]',
                '.field-item'
            ]
            
            content_text = ""
            for selector in content_selectors:
                content_div = release_soup.select_one(selector)
                if content_div:
                    content_text = content_div.get_text(strip=True)
                    if len(content_text) > 200:  # Found substantial content
                        break
            
            if not content_text:
                # Fallback: get all text from body
                body = release_soup.find('body')
                if body:
                    content_text = body.get_text(strip=True)
            
            # Clean up the content
            content_text = ' '.join(content_text.split())  # Remove extra whitespace
            
            extracted_content.append({
                'title': title,
                'url': url,
                'content_length': len(content_text),
                'content_preview': content_text[:500] + "..." if len(content_text) > 500 else content_text,
                'full_content': content_text
            })
            
            print(f"   ✅ Extracted {len(content_text)} characters")
            print(f"   📝 Preview: {content_text[:150]}...")
            
        except Exception as e:
            print(f"   ❌ Failed to extract content: {e}")
    
    return extracted_content


def extract_irb_content():
    """Extract real content from IRB bulletins."""
    print("\n📚 EXTRACTING IRB BULLETIN CONTENT")
    print("=" * 50)
    
    client = IRSHttpClient()
    
    # Get main IRB page
    soup = client.get_soup('https://www.irs.gov/irb')
    links = soup.find_all('a', href=True)
    
    # Find recent bulletin links
    import re
    bulletin_links = []
    for link in links:
        href = link['href']
        text = link.get_text(strip=True)
        if re.search(r'202[34]-\d+', href) and 'bulletin' in text.lower():
            bulletin_links.append((text, href))
    
    print(f"Found {len(bulletin_links)} bulletin links")
    
    # Extract content from first 2 bulletins
    extracted_content = []
    for i, (title, href) in enumerate(bulletin_links[:2]):
        print(f"\n📄 Bulletin {i+1}: {title[:60]}...")
        
        try:
            full_url = 'https://www.irs.gov' + href if href.startswith('/') else href
            bulletin_soup = client.get_soup(full_url)
            
            # Extract bulletin content
            content_text = ""
            
            # Try to find the main content area
            content_selectors = [
                'div[class*="content"]',
                'main',
                '.irb-content',
                'div[class*="body"]'
            ]
            
            for selector in content_selectors:
                content_div = bulletin_soup.select_one(selector)
                if content_div:
                    content_text = content_div.get_text(strip=True)
                    if len(content_text) > 200:
                        break
            
            if not content_text:
                # Fallback
                body = bulletin_soup.find('body')
                if body:
                    content_text = body.get_text(strip=True)
            
            content_text = ' '.join(content_text.split())
            
            extracted_content.append({
                'title': title,
                'url': full_url,
                'content_length': len(content_text),
                'content_preview': content_text[:500] + "..." if len(content_text) > 500 else content_text,
                'full_content': content_text
            })
            
            print(f"   ✅ Extracted {len(content_text)} characters")
            print(f"   📝 Preview: {content_text[:150]}...")
            
        except Exception as e:
            print(f"   ❌ Failed to extract content: {e}")
    
    return extracted_content


def extract_forms_content():
    """Extract real content from forms pages."""
    print("\n📋 EXTRACTING FORMS CONTENT")
    print("=" * 50)
    
    client = IRSHttpClient()
    
    # Test key forms
    key_forms = [
        ('Form 1040', '/forms-pubs/about-form-1040'),
        ('Form 1040-X', '/forms-pubs/about-form-1040x'),
        ('Schedule A', '/forms-pubs/about-schedule-a-form-1040')
    ]
    
    extracted_content = []
    for name, path in key_forms:
        print(f"\n📄 Form: {name}")
        
        try:
            full_url = f'https://www.irs.gov{path}'
            form_soup = client.get_soup(full_url)
            
            # Extract form information
            content_text = ""
            
            content_selectors = [
                'div[class*="content"]',
                'main',
                '.form-content',
                'div[class*="body"]'
            ]
            
            for selector in content_selectors:
                content_div = form_soup.select_one(selector)
                if content_div:
                    content_text = content_div.get_text(strip=True)
                    if len(content_text) > 200:
                        break
            
            if not content_text:
                body = form_soup.find('body')
                if body:
                    content_text = body.get_text(strip=True)
            
            content_text = ' '.join(content_text.split())
            
            extracted_content.append({
                'title': name,
                'url': full_url,
                'content_length': len(content_text),
                'content_preview': content_text[:500] + "..." if len(content_text) > 500 else content_text,
                'full_content': content_text
            })
            
            print(f"   ✅ Extracted {len(content_text)} characters")
            print(f"   📝 Preview: {content_text[:150]}...")
            
        except Exception as e:
            print(f"   ❌ Failed to extract content: {e}")
    
    return extracted_content


def test_gemini_with_real_content(content_samples):
    """Test Gemini with real extracted content."""
    print(f"\n🤖 TESTING GEMINI WITH REAL CONTENT")
    print("=" * 50)
    
    try:
        from dotenv import load_dotenv
        import google.generativeai as genai
        
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        for i, content in enumerate(content_samples[:2]):  # Test first 2
            print(f"\n🔍 Testing content {i+1}: {content['title'][:50]}...")
            
            # Use shorter content to avoid issues
            test_content = content['content_preview']
            
            simple_prompt = f"Is this tax-related content? Answer YES or NO: {test_content[:300]}"
            
            try:
                response = model.generate_content(
                    simple_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=10
                    )
                )
                
                print(f"   ✅ Gemini response: {response.text.strip()}")
                
            except Exception as e:
                print(f"   ❌ Gemini failed: {e}")
                
                # Check response details
                try:
                    print(f"   📊 Response candidates: {len(response.candidates) if hasattr(response, 'candidates') else 'N/A'}")
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        print(f"   📊 Finish reason: {candidate.finish_reason}")
                        print(f"   📊 Safety ratings: {candidate.safety_ratings}")
                except:
                    pass
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini testing failed: {e}")
        return False


def main():
    """Main test function."""
    print("🚀 REAL CONTENT EXTRACTION TEST")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_content = []
    
    # Extract content from each source
    newsroom_content = extract_newsroom_content()
    all_content.extend(newsroom_content)
    
    irb_content = extract_irb_content()
    all_content.extend(irb_content)
    
    forms_content = extract_forms_content()
    all_content.extend(forms_content)
    
    # Test Gemini with real content
    if all_content:
        test_gemini_with_real_content(all_content)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 CONTENT EXTRACTION SUMMARY")
    print(f"{'='*60}")
    
    print(f"Newsroom releases: {len(newsroom_content)} extracted")
    print(f"IRB bulletins: {len(irb_content)} extracted")
    print(f"Forms pages: {len(forms_content)} extracted")
    print(f"Total content pieces: {len(all_content)}")
    
    if all_content:
        avg_length = sum(c['content_length'] for c in all_content) / len(all_content)
        print(f"Average content length: {avg_length:.0f} characters")
        
        print("\n📄 Sample extracted content:")
        for i, content in enumerate(all_content[:3]):
            print(f"\n{i+1}. {content['title'][:60]}...")
            print(f"   Length: {content['content_length']} chars")
            print(f"   Preview: {content['content_preview'][:100]}...")
    
    return len(all_content) > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
