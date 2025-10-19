#!/usr/bin/env python3
"""
Comprehensive tool testing script to identify which tax agent tools are failing.
This will test each tool individually to isolate the problematic one.
"""

import asyncio
import json
import sys
import traceback
from datetime import datetime
import os

# Add the src directory to Python path
sys.path.insert(0, '/Users/anhlam/province/backend/src')

# Import all the tax tools
try:
    from province.agents.tax.tools.save_document import save_document
    from province.agents.tax.tools.ingest_documents import ingest_documents
    from province.agents.tax.tools.calc_1040 import calc_1040
    from province.agents.tax.tools.form_filler import fill_tax_form
    # Note: process_document doesn't seem to exist as a separate tool
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the backend directory with the virtual environment activated")
    sys.exit(1)

class ToolTester:
    def __init__(self):
        self.results = {}
        self.test_engagement_id = "test-tool-validation-" + datetime.now().strftime("%Y%m%d-%H%M%S")
        
    async def test_save_document(self):
        """Test the save_document tool"""
        print("🧪 Testing save_document tool...")
        try:
            # Create a simple test document
            test_content = "This is a test document for tool validation"
            import base64
            content_b64 = base64.b64encode(test_content.encode()).decode()
            
            result = await save_document(
                engagement_id=self.test_engagement_id,
                path="test-tools/validation-doc.txt",
                content_b64=content_b64,
                mime_type="text/plain"
            )
            
            if result.get('success'):
                print(f"✅ save_document: SUCCESS - {result.get('message', 'Document saved')}")
                return True, result
            else:
                print(f"❌ save_document: FAILED - {result.get('error', 'Unknown error')}")
                return False, result
                
        except Exception as e:
            error_msg = f"Exception in save_document: {str(e)}"
            print(f"❌ save_document: EXCEPTION - {error_msg}")
            return False, {"error": error_msg, "traceback": traceback.format_exc()}

    async def test_ingest_documents(self):
        """Test the ingest_documents tool"""
        print("🧪 Testing ingest_documents tool...")
        try:
            # Use a known test W-2 document
            s3_key = "datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_1000.pdf"
            
            result = await ingest_documents(
                s3_key=s3_key,
                taxpayer_name="April Hensley",
                tax_year=2024,
                document_type="W-2"
            )
            
            if result.get('success'):
                total_wages = result.get('total_wages', 0)
                print(f"✅ ingest_documents: SUCCESS - Processed W-2 with wages: ${total_wages:,.2f}")
                return True, result
            else:
                print(f"❌ ingest_documents: FAILED - {result.get('error', 'Unknown error')}")
                return False, result
                
        except Exception as e:
            error_msg = f"Exception in ingest_documents: {str(e)}"
            print(f"❌ ingest_documents: EXCEPTION - {error_msg}")
            return False, {"error": error_msg, "traceback": traceback.format_exc()}

    async def test_calc_1040(self):
        """Test the calc_1040 tool"""
        print("🧪 Testing calc_1040 tool...")
        try:
            # First we need to save some W-2 data for the engagement
            # The calc_1040 function loads W-2 data from the engagement
            result = await calc_1040(
                engagement_id=self.test_engagement_id,
                filing_status="S",  # Single
                dependents_count=0
            )
            
            if result.get('success'):
                tax_owed = result.get('tax_owed', 0)
                refund = result.get('refund', 0)
                print(f"✅ calc_1040: SUCCESS - Tax owed: ${tax_owed:,.2f}, Refund: ${refund:,.2f}")
                return True, result
            else:
                print(f"❌ calc_1040: FAILED - {result.get('error', 'Unknown error')}")
                return False, result
                
        except Exception as e:
            error_msg = f"Exception in calc_1040: {str(e)}"
            print(f"❌ calc_1040: EXCEPTION - {error_msg}")
            return False, {"error": error_msg, "traceback": traceback.format_exc()}

    async def test_form_filler(self):
        """Test the fill_tax_form tool"""
        print("🧪 Testing fill_tax_form tool...")
        try:
            # Test with sample form data
            form_data = {
                "taxpayer_name": "April Hensley",
                "filing_status": "S",
                "total_income": 55000.00,
                "taxable_income": 42000.00,
                "tax_owed": 4620.00,
                "withholding": 8250.00,
                "refund": 3630.00,
                "ssn": "123-45-6789",
                "address": "123 Test St, Test City, TS 12345"
            }
            
            result = await fill_tax_form(
                form_type="1040",
                form_data=form_data
            )
            
            if result.get('success'):
                form_url = result.get('filled_form_url', 'N/A')
                print(f"✅ form_filler: SUCCESS - Form filled: {form_url}")
                return True, result
            else:
                print(f"❌ form_filler: FAILED - {result.get('error', 'Unknown error')}")
                return False, result
                
        except Exception as e:
            error_msg = f"Exception in form_filler: {str(e)}"
            print(f"❌ form_filler: EXCEPTION - {error_msg}")
            return False, {"error": error_msg, "traceback": traceback.format_exc()}


    async def run_all_tests(self):
        """Run all tool tests"""
        print("🔧 COMPREHENSIVE TAX AGENT TOOL TESTING")
        print("=" * 60)
        print(f"Test Engagement ID: {self.test_engagement_id}")
        print("=" * 60)
        
        # Define all tests
        tests = [
            ("save_document", self.test_save_document),
            ("ingest_documents", self.test_ingest_documents),
            ("calc_1040", self.test_calc_1040),
            ("fill_tax_form", self.test_form_filler),
        ]
        
        # Run each test
        for test_name, test_func in tests:
            print(f"\n📝 Running: {test_name}")
            print("-" * 40)
            
            try:
                success, result = await test_func()
                self.results[test_name] = {
                    "success": success,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                print(f"❌ {test_name}: CRASHED - {str(e)}")
                self.results[test_name] = {
                    "success": False,
                    "result": {"error": str(e), "traceback": traceback.format_exc()},
                    "timestamp": datetime.now().isoformat()
                }
            
            # Brief pause between tests
            await asyncio.sleep(1)
        
        # Generate summary
        self.print_summary()
        self.save_results()

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 TOOL TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for tool_name, result in self.results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} - {tool_name}")
            
            if result["success"]:
                passed += 1
            else:
                failed += 1
                # Show error details for failed tests
                error = result["result"].get("error", "Unknown error")
                print(f"      Error: {error}")
        
        print(f"\n🎯 Overall: {passed}/{len(self.results)} tools passed")
        
        if failed == 0:
            print("🎉 All tools are working correctly!")
            print("   The throttling issue may be related to:")
            print("   - Bedrock agent configuration")
            print("   - Tool orchestration logic")
            print("   - Session management")
        else:
            print(f"⚠️  {failed} tool(s) failed - these are likely causing the agent errors!")
            print("\n🔍 PROBLEMATIC TOOLS:")
            for tool_name, result in self.results.items():
                if not result["success"]:
                    print(f"   - {tool_name}: {result['result'].get('error', 'Unknown error')}")

    def save_results(self):
        """Save detailed results to file"""
        results_file = f"tool_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            print(f"\n💾 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️  Could not save results file: {e}")

async def main():
    """Main test runner"""
    tester = ToolTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    # Check if we're in the right environment
    if not os.path.exists("/Users/anhlam/province/backend/src/province"):
        print("❌ Error: Please run this script from the backend directory")
        print("   cd /Users/anhlam/province/backend")
        print("   source venv/bin/activate")
        print("   python test_individual_tools.py")
        sys.exit(1)
    
    # Run the tests
    asyncio.run(main())
