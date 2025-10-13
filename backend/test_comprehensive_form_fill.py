#!/usr/bin/env python3
"""
Comprehensive test to fill out as many 1040 form fields as possible using PyMuPDF.
This will show the full capability of the PyMuPDF solution.
"""

import asyncio
import logging
import os
import boto3
import tempfile
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_comprehensive_form_fill():
    """Test comprehensive form filling with PyMuPDF."""
    
    # Load environment variables
    load_dotenv('.env.local')
    
    logger.info("🧪 Testing comprehensive 1040 form filling with PyMuPDF")
    
    try:
        import fitz  # PyMuPDF
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            region_name='us-east-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Download template
        template_bucket = 'province-templates-[REDACTED-ACCOUNT-ID]-us-east-1'
        documents_bucket = 'province-documents-[REDACTED-ACCOUNT-ID]-us-east-1'
        template_key = 'tax_forms/2024/f1040.pdf'
        
        logger.info(f"📥 Downloading template from s3://{template_bucket}/{template_key}")
        
        response = s3_client.get_object(Bucket=template_bucket, Key=template_key)
        template_data = response['Body'].read()
        logger.info(f"✅ Downloaded template: {len(template_data):,} bytes")
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(template_data)
            temp_path = temp_file.name
        
        # Open with PyMuPDF
        doc = fitz.open(temp_path)
        page = doc[0]  # First page
        
        # Get all form widgets
        widgets = list(page.widgets())
        logger.info(f"📊 Found {len(widgets)} total form widgets")
        
        # Comprehensive form data - filling as many fields as possible
        comprehensive_data = {
            # Personal Information
            'f1_01': 'JOHN',
            'f1_02': 'MICHAEL', 
            'f1_03': 'DOE',
            'f1_04': '123456789',  # SSN
            'f1_05': 'JANE',
            'f1_06': 'ELIZABETH',
            'f1_07': 'DOE', 
            'f1_08': '987654321',  # Spouse SSN
            'f1_09': '123 MAIN STREET APT 4B',  # Address
            'f1_10': 'ANYTOWN',  # City
            'f1_11': 'CA',  # State
            'f1_12': '90210',  # ZIP
            
            # Income Section (Lines 1-11)
            'f1_13': '85000',    # Line 1 - Wages
            'f1_14': '1250',     # Line 2a - Tax-exempt interest
            'f1_15': '750',      # Line 2b - Taxable interest
            'f1_16': '500',      # Line 3a - Qualified dividends
            'f1_17': '500',      # Line 3b - Ordinary dividends
            'f1_18': '0',        # Line 4a - IRA distributions
            'f1_19': '0',        # Line 4b - Taxable IRA
            'f1_20': '0',        # Line 5a - Pensions
            'f1_21': '0',        # Line 5b - Taxable pensions
            'f1_22': '0',        # Line 6a - Social security
            'f1_23': '0',        # Line 6b - Taxable social security
            'f1_24': '0',        # Line 7 - Capital gain
            'f1_25': '2500',     # Line 8a - Other income
            'f1_26': '89000',    # Line 9 - Total income
            
            # Adjustments to Income
            'f1_27': '0',        # Line 10a - Adjustments
            'f1_28': '89000',    # Line 11 - Adjusted gross income
            
            # Standard/Itemized Deductions
            'f1_29': '29200',    # Line 12a - Standard deduction
            'f1_30': '0',        # Line 12b - Itemized deductions
            'f1_31': '29200',    # Line 12c - Deduction amount
            'f1_32': '0',        # Line 13 - Qualified business income
            'f1_33': '29200',    # Line 14 - Total deductions
            'f1_34': '59800',    # Line 15 - Taxable income
            
            # Tax Computation
            'f1_35': '6708',     # Line 16 - Tax
            'f1_36': '0',        # Line 17 - Amount from Schedule 2
            'f1_37': '6708',     # Line 18 - Add lines 16 and 17
            'f1_38': '0',        # Line 19 - Child tax credit
            'f1_39': '0',        # Line 20 - Amount from Schedule 3
            'f1_40': '0',        # Line 21 - Add lines 19 and 20
            'f1_41': '6708',     # Line 22 - Subtract line 21 from 18
            'f1_42': '0',        # Line 23 - Other taxes
            'f1_43': '6708',     # Line 24 - Total tax
            
            # Payments
            'f1_44': '8500',     # Line 25a - Federal withholding
            'f1_45': '0',        # Line 25b - 2023 estimated tax
            'f1_46': '0',        # Line 25c - Earned income credit
            'f1_47': '0',        # Line 25d - Additional child tax credit
            'f1_48': '0',        # Line 26 - Amount from Schedule 3
            'f1_49': '8500',     # Line 33 - Total payments
            
            # Refund or Amount Owed
            'f1_50': '1792',     # Line 34 - Overpayment (refund)
            'f1_51': '1792',     # Line 35a - Amount to be refunded
            
            # Dependents (if any)
            'f1_52': 'EMILY DOE',           # Dependent 1 name
            'f1_53': '123456780',           # Dependent 1 SSN
            'f1_54': 'DAUGHTER',            # Dependent 1 relationship
            'f1_55': 'MICHAEL DOE JR',      # Dependent 2 name
            'f1_56': '123456781',           # Dependent 2 SSN
            'f1_57': 'SON',                 # Dependent 2 relationship
        }
        
        # Display all available widgets first
        logger.info("\n📋 Available form widgets:")
        for i, widget in enumerate(widgets):
            field_name = widget.field_name
            field_type = widget.field_type
            current_value = widget.field_value
            logger.info(f"   {i+1:2d}. {field_name} (Type: {field_type}) = '{current_value}'")
        
        # Fill widgets with comprehensive data
        filled_count = 0
        logger.info(f"\n📝 Filling form with comprehensive data...")
        
        for widget in widgets:
            field_name = widget.field_name
            if field_name:
                # Try to match field name to our comprehensive data
                for data_key, value in comprehensive_data.items():
                    if (data_key in field_name or 
                        field_name.endswith(data_key) or
                        field_name.endswith(f"{data_key}[0]")):
                        try:
                            # Format the value appropriately
                            formatted_value = str(value)
                            
                            # Special formatting for different field types
                            if widget.field_type == 2:  # Checkbox
                                # For checkboxes, use "Yes" or "1" for true values
                                formatted_value = "Yes" if value and str(value) != "0" else ""
                            elif data_key in ['f1_13', 'f1_14', 'f1_15', 'f1_16', 'f1_17', 'f1_25', 'f1_26', 'f1_28', 'f1_29', 'f1_34', 'f1_35', 'f1_41', 'f1_43', 'f1_44', 'f1_49', 'f1_50', 'f1_51']:
                                # Format currency fields
                                try:
                                    num_value = float(str(value).replace(',', ''))
                                    if num_value > 0:
                                        formatted_value = f"{int(num_value):,}"
                                    else:
                                        formatted_value = ""
                                except:
                                    formatted_value = str(value)
                            
                            widget.field_value = formatted_value
                            widget.update()
                            filled_count += 1
                            logger.info(f"   ✅ Filled {field_name}: '{formatted_value}'")
                            break
                        except Exception as e:
                            logger.warning(f"   ⚠️ Could not fill {field_name}: {e}")
        
        logger.info(f"\n🎯 Successfully filled {filled_count} out of {len(widgets)} form widgets")
        
        # Save the comprehensive filled form
        output_bytes = doc.tobytes()
        doc.close()
        os.unlink(temp_path)
        
        logger.info(f"✅ Created comprehensive filled form: {len(output_bytes):,} bytes")
        
        # Upload to S3
        timestamp = int(asyncio.get_event_loop().time())
        output_key = f"filled_forms/comprehensive/1040_2024_COMPREHENSIVE_{timestamp}.pdf"
        
        logger.info(f"📤 Uploading to s3://{documents_bucket}/{output_key}")
        
        s3_client.put_object(
            Bucket=documents_bucket,
            Key=output_key,
            Body=output_bytes,
            ContentType='application/pdf',
            Metadata={
                'form_type': '1040',
                'tax_year': '2024',
                'taxpayer_name': 'John Michael Doe',
                'spouse_name': 'Jane Elizabeth Doe',
                'total_income': '89000',
                'taxable_income': '59800',
                'tax_owed': '6708',
                'refund_amount': '1792',
                'filled_fields': str(filled_count),
                'filled_by': 'comprehensive_pymupdf_test',
                'filling_method': 'pymupdf_comprehensive'
            }
        )
        
        # Generate download URL
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': documents_bucket,
                'Key': output_key
            },
            ExpiresIn=3600
        )
        
        logger.info("✅ Successfully uploaded comprehensive filled form")
        logger.info(f"🔗 Download URL: {download_url}")
        
        # Summary
        logger.info("\n🎉 COMPREHENSIVE FORM FILLING COMPLETED!")
        logger.info("=" * 60)
        logger.info("✅ COMPREHENSIVE DATA FILLED:")
        logger.info("   • Personal Info: Names, SSNs, Address")
        logger.info("   • Income: Wages, Interest, Dividends, Other Income")
        logger.info("   • Deductions: Standard Deduction")
        logger.info("   • Tax Calculation: Taxable Income, Tax Owed")
        logger.info("   • Payments: Federal Withholding")
        logger.info("   • Refund: Calculated Refund Amount")
        logger.info("   • Dependents: Children Information")
        logger.info(f"\n📊 STATISTICS:")
        logger.info(f"   • Total Widgets: {len(widgets)}")
        logger.info(f"   • Fields Filled: {filled_count}")
        logger.info(f"   • Fill Rate: {(filled_count/len(widgets)*100):.1f}%")
        logger.info(f"   • File Size: {len(output_bytes):,} bytes")
        logger.info(f"\n📁 DOWNLOAD:")
        logger.info(f"   {download_url}")
        
        return True
        
    except ImportError:
        logger.error("❌ PyMuPDF not available - please install: pip install pymupdf")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_comprehensive_form_fill())
    
    if success:
        print("\n🎯 SUCCESS: Comprehensive 1040 form filling completed!")
        print("   • Filled personal information, income, deductions, tax calculations")
        print("   • Included dependents, payments, and refund information")
        print("   • Used proper PyMuPDF form widget filling")
        print("   • Download the form to see all filled fields!")
    else:
        print("\n💥 Comprehensive test failed")
        exit(1)
