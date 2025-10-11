#!/usr/bin/env python3
"""Test Gemini API key and functionality separately."""

import sys
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

def test_gemini_api_key():
    """Test if Gemini API key is working."""
    print("🤖 TESTING GEMINI API KEY")
    print("=" * 50)
    
    # Check if API key exists
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        print("✅ Gemini configured successfully")
        
        # List available models
        print("\n📋 Available models:")
        models = list(genai.list_models())
        for i, model in enumerate(models[:5]):  # Show first 5
            if 'generateContent' in model.supported_generation_methods:
                print(f"   {i+1}. {model.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini configuration failed: {e}")
        return False


def test_gemini_simple_request():
    """Test a simple Gemini request."""
    print("\n🧠 TESTING SIMPLE GEMINI REQUEST")
    print("=" * 50)
    
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        
        # Try different models
        models_to_try = [
            'gemini-2.5-flash',
            'gemini-pro-latest',
            'gemini-flash-latest'
        ]
        
        for model_name in models_to_try:
            try:
                print(f"\n🔍 Testing model: {model_name}")
                model = genai.GenerativeModel(model_name)
                
                response = model.generate_content(
                    "Hello! Please respond with just the word 'SUCCESS' if you can understand this message.",
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=50
                    )
                )
                
                print(f"   ✅ Response: {response.text.strip()}")
                return True
                
            except Exception as e:
                print(f"   ❌ Model {model_name} failed: {e}")
                continue
        
        print("❌ All models failed")
        return False
        
    except Exception as e:
        print(f"❌ Simple request failed: {e}")
        return False


def test_gemini_tax_analysis():
    """Test Gemini with tax-specific content."""
    print("\n📊 TESTING GEMINI TAX ANALYSIS")
    print("=" * 50)
    
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Test with clear tax content
        test_content = """
        Title: IRS announces 2024 tax brackets and standard deduction amounts
        Content: The IRS announced inflation adjustments for tax year 2024. The standard deduction for single filers increases to $14,600. The 10% tax bracket applies to income up to $11,000 for single filers.
        """
        
        prompt = """
        Analyze this tax content and respond with ONLY this JSON format:
        {"relevant": true, "confidence": 0.95, "reason": "explanation"}
        
        Content: """ + test_content
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=200
            )
        )
        
        print(f"✅ Raw response: {response.text}")
        
        # Try to parse JSON
        import json
        try:
            # Clean response
            clean_text = response.text.strip()
            if clean_text.startswith('```json'):
                clean_text = clean_text[7:]
            if clean_text.endswith('```'):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            result = json.loads(clean_text)
            print(f"✅ Parsed JSON: {result}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Tax analysis test failed: {e}")
        return False


def test_gemini_with_long_content():
    """Test Gemini with longer content (like real IRS pages)."""
    print("\n📄 TESTING GEMINI WITH LONG CONTENT")
    print("=" * 50)
    
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Simulate long IRS content
        long_content = """
        Title: Treasury and IRS issue guidance for the Energy Efficient Home Improvement Credit
        
        Content: The Treasury Department and Internal Revenue Service today issued guidance for the Energy Efficient Home Improvement Credit under section 25C of the Internal Revenue Code. This credit allows taxpayers to claim up to $3,200 annually for qualifying energy efficiency improvements to their homes.
        
        The guidance clarifies eligibility requirements for various home improvements including:
        - Heat pumps and heat pump water heaters
        - Biomass stoves and boilers  
        - Energy-efficient windows and doors
        - Insulation and air sealing materials
        - Central air conditioning systems
        - Natural gas, propane, or oil water heaters
        
        For tax year 2024, taxpayers can claim:
        - Up to $2,000 for heat pumps and heat pump water heaters
        - Up to $600 for other qualifying equipment
        - Up to $500 for windows and skylights
        - Up to $150 for home energy audits
        
        The credit is non-refundable and applies to the tax year in which the improvements are made and placed in service. Taxpayers must retain receipts and manufacturer certifications to claim the credit.
        """ * 3  # Make it longer
        
        prompt = f"""
        Analyze this IRS content for tax relevance. Respond with ONLY valid JSON:
        {{"relevant": true/false, "confidence": 0.0-1.0, "reason": "brief explanation"}}
        
        Content: {long_content[:1500]}...
        """
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=300
            )
        )
        
        print(f"✅ Response received (length: {len(response.text)})")
        print(f"   First 200 chars: {response.text[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Long content test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("🚀 GEMINI API COMPREHENSIVE TEST")
    print("=" * 60)
    
    results = {}
    
    # Test API key
    results['api_key'] = test_gemini_api_key()
    
    if results['api_key']:
        # Test simple request
        results['simple_request'] = test_gemini_simple_request()
        
        # Test tax analysis
        results['tax_analysis'] = test_gemini_tax_analysis()
        
        # Test long content
        results['long_content'] = test_gemini_with_long_content()
    else:
        results['simple_request'] = False
        results['tax_analysis'] = False
        results['long_content'] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 GEMINI TEST RESULTS")
    print(f"{'='*60}")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.upper():15} {status}")
    
    working_count = sum(1 for r in results.values() if r)
    total_count = len(results)
    
    print(f"\n🎯 Overall: {working_count}/{total_count} tests passed")
    
    if working_count == total_count:
        print("🎉 Gemini API is working perfectly!")
    elif working_count >= 2:
        print("✅ Gemini API is mostly working")
    else:
        print("❌ Gemini API has significant issues")
    
    return working_count >= 2


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
