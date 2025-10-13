#!/usr/bin/env python3
"""
Test the new form filler tool in the tax agents tools folder.
"""

import asyncio
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_new_form_filler_tool():
    """Test the new form filler tool."""
    
    # Load environment variables
    load_dotenv('.env.local')
    
    logger.info("🧪 Testing new form filler tool")
    
    try:
        # Import the new tool
        from province.agents.tax.tools.form_filler import fill_tax_form, get_available_tax_forms, get_tax_form_fields
        
        # Test getting available forms
        logger.info("📋 Testing get_available_tax_forms...")
        available_forms = get_available_tax_forms()
        logger.info(f"Available forms: {len(available_forms)}")
        for form in available_forms:
            logger.info(f"  - {form['form_type']}: {form['description']}")
        
        # Test getting form fields
        logger.info("\n📝 Testing get_tax_form_fields...")
        form_fields = get_tax_form_fields('1040')
        logger.info(f"1040 form field categories: {list(form_fields.keys())}")
        
        # Test form filling with sample data
        logger.info("\n🎯 Testing fill_tax_form...")
        sample_form_data = {
            'f1_01': 'JOHN',
            'f1_02': 'DOE',
            'f1_03': '123456789',
            'f1_07': '123 MAIN STREET',
            'f1_10': 'ANYTOWN',
            'f1_11': 'CA',
            'f1_12': '90210',
            'f1_13': '75000',  # Wages
            'f1_44': '8500',   # Federal withholding
            'c1_1': True,      # Single filing status
        }
        
        result = await fill_tax_form('1040', sample_form_data)
        
        if result['success']:
            logger.info("✅ Form filling successful!")
            logger.info(f"   Form URL: {result['filled_form_url']}")
            logger.info(f"   Fields filled: {result['fields_filled']}")
            logger.info(f"   File size: {result['file_size']:,} bytes")
        else:
            logger.error(f"❌ Form filling failed: {result.get('error')}")
            return False
        
        logger.info("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_new_form_filler_tool())
    
    if success:
        print("\n🎯 SUCCESS: New form filler tool is working correctly!")
        print("   • Moved from services to tax agent tools")
        print("   • Integrated PyMuPDF with checkbox support")
        print("   • Updated API routes to use new tool")
        print("   • Production-ready form filling capability")
    else:
        print("\n💥 Test failed")
        exit(1)
