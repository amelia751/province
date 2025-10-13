#!/usr/bin/env python3
"""
Test PyMuPDF checkbox filling - focusing on Type 2 fields (checkboxes).
This will show how to properly tick boxes in the 1040 form.
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

async def test_checkbox_filling():
    """Test checkbox filling with PyMuPDF."""
    
    # Load environment variables
    load_dotenv('.env.local')
    
    logger.info("🧪 Testing checkbox filling with PyMuPDF")
    
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
        
        # Separate text fields and checkboxes
        text_fields = [w for w in widgets if w.field_type == 7]  # Text fields
        checkboxes = [w for w in widgets if w.field_type == 2]   # Checkboxes
        
        logger.info(f"📝 Text fields: {len(text_fields)}")
        logger.info(f"☑️ Checkboxes: {len(checkboxes)}")
        
        # Display all checkboxes first
        logger.info("\n☑️ Available checkboxes:")
        for i, checkbox in enumerate(checkboxes):
            field_name = checkbox.field_name
            current_value = checkbox.field_value
            logger.info(f"   {i+1:2d}. {field_name} = '{current_value}'")
        
        # Fill some basic text fields first
        basic_text_data = {
            'f1_01': 'JOHN',
            'f1_02': 'DOE', 
            'f1_03': '123456789',  # SSN
            'f1_07': '123 MAIN STREET',  # Address
            'f1_11': '75000',     # Wages
        }
        
        logger.info(f"\n📝 Filling basic text fields...")
        text_filled = 0
        for widget in text_fields:
            field_name = widget.field_name
            if field_name:
                for data_key, value in basic_text_data.items():
                    if (data_key in field_name or 
                        field_name.endswith(data_key) or
                        field_name.endswith(f"{data_key}[0]")):
                        try:
                            widget.field_value = str(value)
                            widget.update()
                            text_filled += 1
                            logger.info(f"   ✅ Filled {field_name}: '{value}'")
                            break
                        except Exception as e:
                            logger.warning(f"   ⚠️ Could not fill {field_name}: {e}")
        
        # Now focus on checkboxes - try different approaches
        logger.info(f"\n☑️ Filling checkboxes with different methods...")
        
        # Checkbox data - mapping checkbox names to whether they should be checked
        checkbox_data = {
            # Filing Status - let's check "Married filing jointly" (usually c1_3[1])
            'c1_3[1]': True,  # Married filing jointly
            'c1_1': False,    # Single (uncheck if checked)
            'c1_2': False,    # Married filing separately
            
            # Presidential Election Campaign Fund
            'c1_4': True,     # Check the $3 campaign fund box
            
            # Dependents checkboxes (if we have dependents)
            'c1_14': True,    # Child tax credit checkbox for dependent 1
            'c1_15': False,   # Credit for other dependents for dependent 1
            'c1_16': True,    # Child tax credit checkbox for dependent 2
            'c1_17': False,   # Credit for other dependents for dependent 2
            
            # Other common checkboxes
            'c1_5': False,    # Spouse itemizes
            'c1_6': False,    # You were born before Jan 2, 1960
            'c1_7': False,    # You are blind
            'c1_8': False,    # Spouse born before Jan 2, 1960
            'c1_9': False,    # Spouse is blind
            'c1_10': False,   # More than four dependents
        }
        
        checkbox_filled = 0
        
        for checkbox in checkboxes:
            field_name = checkbox.field_name
            if field_name:
                # Try to match checkbox name to our data
                for checkbox_key, should_check in checkbox_data.items():
                    if (checkbox_key in field_name or 
                        field_name.endswith(checkbox_key) or
                        field_name.endswith(f"{checkbox_key}[0]")):
                        try:
                            # Try different values for checking/unchecking
                            if should_check:
                                # Try different "checked" values
                                for check_value in ["Yes", "On", "1", "True", "Checked", checkbox_key]:
                                    try:
                                        checkbox.field_value = check_value
                                        checkbox.update()
                                        checkbox_filled += 1
                                        logger.info(f"   ✅ CHECKED {field_name}: '{check_value}'")
                                        break
                                    except Exception as e:
                                        logger.debug(f"      Failed with '{check_value}': {e}")
                                        continue
                            else:
                                # Try different "unchecked" values
                                for uncheck_value in ["", "Off", "0", "False", "No"]:
                                    try:
                                        checkbox.field_value = uncheck_value
                                        checkbox.update()
                                        checkbox_filled += 1
                                        logger.info(f"   ✅ UNCHECKED {field_name}: '{uncheck_value}'")
                                        break
                                    except Exception as e:
                                        logger.debug(f"      Failed with '{uncheck_value}': {e}")
                                        continue
                            break
                        except Exception as e:
                            logger.warning(f"   ⚠️ Could not set checkbox {field_name}: {e}")
        
        # Try alternative checkbox approach - using button_state
        logger.info(f"\n🔘 Trying alternative checkbox approach...")
        
        alt_checkbox_filled = 0
        for checkbox in checkboxes:
            field_name = checkbox.field_name
            if field_name and 'c1_3[1]' in field_name:  # Focus on married filing jointly
                try:
                    # Try using button_state property
                    if hasattr(checkbox, 'button_state'):
                        checkbox.button_state = True  # Set to checked
                        checkbox.update()
                        alt_checkbox_filled += 1
                        logger.info(f"   ✅ ALT METHOD - CHECKED {field_name} using button_state")
                    elif hasattr(checkbox, 'is_checked'):
                        checkbox.is_checked = True
                        checkbox.update()
                        alt_checkbox_filled += 1
                        logger.info(f"   ✅ ALT METHOD - CHECKED {field_name} using is_checked")
                except Exception as e:
                    logger.warning(f"   ⚠️ Alt method failed for {field_name}: {e}")
        
        total_filled = text_filled + checkbox_filled + alt_checkbox_filled
        logger.info(f"\n🎯 FILLING SUMMARY:")
        logger.info(f"   • Text fields filled: {text_filled}")
        logger.info(f"   • Checkboxes filled: {checkbox_filled}")
        logger.info(f"   • Alt method checkboxes: {alt_checkbox_filled}")
        logger.info(f"   • Total filled: {total_filled}")
        
        # Save the form with checkboxes
        output_bytes = doc.tobytes()
        doc.close()
        os.unlink(temp_path)
        
        logger.info(f"✅ Created form with checkboxes: {len(output_bytes):,} bytes")
        
        # Upload to S3
        timestamp = int(asyncio.get_event_loop().time())
        output_key = f"filled_forms/checkboxes/1040_2024_CHECKBOXES_{timestamp}.pdf"
        
        logger.info(f"📤 Uploading to s3://{documents_bucket}/{output_key}")
        
        s3_client.put_object(
            Bucket=documents_bucket,
            Key=output_key,
            Body=output_bytes,
            ContentType='application/pdf',
            Metadata={
                'form_type': '1040',
                'tax_year': '2024',
                'taxpayer_name': 'John Doe',
                'filing_status': 'married_filing_jointly',
                'text_fields_filled': str(text_filled),
                'checkboxes_filled': str(checkbox_filled + alt_checkbox_filled),
                'total_filled': str(total_filled),
                'filled_by': 'checkbox_test',
                'filling_method': 'pymupdf_checkboxes'
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
        
        logger.info("✅ Successfully uploaded form with checkboxes")
        logger.info(f"🔗 Download URL: {download_url}")
        
        # Summary
        logger.info("\n🎉 CHECKBOX FILLING TEST COMPLETED!")
        logger.info("=" * 60)
        logger.info("✅ CHECKBOX EXPERIMENTS:")
        logger.info("   • Tried multiple checkbox values (Yes, On, 1, True, etc.)")
        logger.info("   • Tested unchecking with (Off, 0, False, etc.)")
        logger.info("   • Attempted alternative methods (button_state, is_checked)")
        logger.info("   • Focused on filing status and common checkboxes")
        logger.info(f"\n📊 RESULTS:")
        logger.info(f"   • Available checkboxes: {len(checkboxes)}")
        logger.info(f"   • Successfully modified: {checkbox_filled + alt_checkbox_filled}")
        logger.info(f"   • Success rate: {((checkbox_filled + alt_checkbox_filled)/len(checkboxes)*100):.1f}%")
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
    success = asyncio.run(test_checkbox_filling())
    
    if success:
        print("\n🎯 SUCCESS: Checkbox filling test completed!")
        print("   • Tested multiple checkbox values and methods")
        print("   • Focused on filing status and common form checkboxes")
        print("   • Download the form to see which checkboxes were successfully ticked")
        print("   • This will help determine the correct checkbox values for PyMuPDF")
    else:
        print("\n💥 Checkbox test failed")
        exit(1)
