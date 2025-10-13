"""
Tax Form Filler Tool

This tool handles filling PDF tax forms using PyMuPDF for precise form field filling.
Supports both text fields and checkboxes with proper formatting.
"""

import json
import logging
import os
import tempfile
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from province.core.config import get_settings

logger = logging.getLogger(__name__)

class TaxFormFiller:
    """Tax form filling tool using PyMuPDF for precise field filling."""
    
    def __init__(self):
        self.settings = get_settings()
        self.s3_client = boto3.client(
            's3',
            region_name=self.settings.aws_region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.templates_bucket = self.settings.templates_bucket_name
        self.documents_bucket = self.settings.documents_bucket_name

    async def fill_1040_form(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fill a 1040 tax form with provided data.
        
        Args:
            form_data: Dictionary containing form field data
            
        Returns:
            Dictionary with filled form URL and metadata
        """
        try:
            logger.info("Starting 1040 form filling process")
            
            # Download the 1040 template
            template_key = 'tax_forms/2024/f1040.pdf'
            template_data = await self._download_pdf_template(template_key)
            
            # Fill the form using PyMuPDF
            filled_pdf_bytes = self._fill_pdf_with_pymupdf(template_data, form_data)
            
            # Upload the filled form
            upload_url = await self._upload_filled_pdf(
                file_content=filled_pdf_bytes,
                form_type='1040',
                tax_year=2024,
                metadata={
                    'form_type': '1040',
                    'tax_year': '2024',
                    'filled_by': 'tax_form_filler_tool',
                    'filling_method': 'pymupdf_production',
                    'fields_filled': str(len(form_data))
                }
            )
            
            logger.info("Successfully filled 1040 form")
            
            return {
                'success': True,
                'filled_form_url': upload_url,
                'form_type': '1040',
                'tax_year': 2024,
                'fields_filled': len(form_data),
                'file_size': len(filled_pdf_bytes),
                'message': 'Form filled successfully with PyMuPDF'
            }
            
        except Exception as e:
            logger.error(f"Error filling 1040 form: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to fill form'
            }

    def _fill_pdf_with_pymupdf(self, pdf_data: bytes, form_data: Dict[str, Any]) -> bytes:
        """
        Fill PDF form using PyMuPDF with support for text fields and checkboxes.
        
        Args:
            pdf_data: Original PDF template bytes
            form_data: Form data to fill
            
        Returns:
            Filled PDF bytes
        """
        try:
            import fitz  # PyMuPDF
            
            logger.info("Filling PDF using PyMuPDF with text fields and checkboxes")
            
            # Save PDF to temp file (fitz works with file paths)
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_data)
                temp_path = temp_file.name
            
            # Open with fitz
            doc = fitz.open(temp_path)
            page = doc[0]  # First page
            
            # Get form widgets
            widgets = list(page.widgets())
            logger.info(f"Found {len(widgets)} form widgets in PDF")
            
            # Separate text fields and checkboxes
            text_fields = [w for w in widgets if w.field_type == 7]  # Text fields
            checkboxes = [w for w in widgets if w.field_type == 2]   # Checkboxes
            
            logger.info(f"Text fields: {len(text_fields)}, Checkboxes: {len(checkboxes)}")
            
            filled_count = 0
            
            # Fill text fields
            for widget in text_fields:
                field_name = widget.field_name
                if field_name:
                    # Try to match field name to our data
                    for data_key, value in form_data.items():
                        # Clean up field names for matching
                        clean_data_key = data_key.replace('[0]', '')
                        
                        if (clean_data_key in field_name or 
                            field_name.endswith(clean_data_key) or
                            field_name.endswith(f"{clean_data_key}[0]")):
                            try:
                                # Format the value appropriately
                                formatted_value = self._format_field_value(clean_data_key, value)
                                
                                widget.field_value = formatted_value
                                widget.update()
                                filled_count += 1
                                logger.info(f"✅ Filled text field {field_name}: {formatted_value}")
                                break
                            except Exception as e:
                                logger.warning(f"Could not fill text field {field_name}: {e}")
            
            # Fill checkboxes
            for widget in checkboxes:
                field_name = widget.field_name
                if field_name:
                    # Try to match checkbox name to our data
                    for data_key, value in form_data.items():
                        clean_data_key = data_key.replace('[0]', '')
                        
                        if (clean_data_key in field_name or 
                            field_name.endswith(clean_data_key) or
                            field_name.endswith(f"{clean_data_key}[0]")):
                            try:
                                # Handle checkbox values
                                if self._should_check_box(clean_data_key, value):
                                    widget.field_value = "Yes"  # Checked
                                    logger.info(f"✅ CHECKED {field_name}")
                                else:
                                    widget.field_value = ""     # Unchecked
                                    logger.info(f"☐ UNCHECKED {field_name}")
                                
                                widget.update()
                                filled_count += 1
                                break
                            except Exception as e:
                                logger.warning(f"Could not fill checkbox {field_name}: {e}")
            
            logger.info(f"Successfully filled {filled_count} form widgets using PyMuPDF")
            
            # Save result to bytes
            output_bytes = doc.tobytes()
            
            # Cleanup
            doc.close()
            os.unlink(temp_path)
            
            logger.info(f"Created filled PDF: {len(output_bytes):,} bytes")
            return output_bytes
            
        except ImportError:
            logger.error("PyMuPDF not available - please install: pip install pymupdf")
            raise Exception("PyMuPDF library not available")
        except Exception as e:
            logger.error(f"PyMuPDF filling failed: {e}")
            raise

    def _format_field_value(self, field_key: str, value: Any) -> str:
        """Format field value based on field type."""
        if value is None:
            return ""
        
        # Currency/numeric fields
        currency_fields = [
            'f1_11', 'f1_12', 'f1_13', 'f1_14', 'f1_15', 'f1_16', 'f1_17', 
            'f1_25', 'f1_26', 'f1_28', 'f1_29', 'f1_34', 'f1_35', 'f1_41', 
            'f1_43', 'f1_44', 'f1_49', 'f1_50', 'f1_51', 'total_income', 
            'standard_deduction', 'taxable_income', 'tax_owed', 'federal_withholding', 
            'refund_owed'
        ]
        
        if field_key in currency_fields:
            try:
                num_value = float(str(value).replace(',', ''))
                if num_value == 0:
                    return ""
                elif num_value == int(num_value):
                    return f"{int(num_value):,}"
                else:
                    return f"{num_value:,.2f}"
            except:
                return str(value)
        
        # Regular text fields
        return str(value).upper() if isinstance(value, str) else str(value)

    def _should_check_box(self, field_key: str, value: Any) -> bool:
        """Determine if a checkbox should be checked based on field and value."""
        if value is None:
            return False
        
        # Convert value to boolean-like
        if isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return value != 0
        elif isinstance(value, str):
            return value.lower() in ['true', 'yes', '1', 'on', 'checked']
        
        return bool(value)

    async def _download_pdf_template(self, template_key: str) -> bytes:
        """Download PDF template from S3."""
        try:
            logger.info(f"Downloading template: {template_key}")
            response = self.s3_client.get_object(
                Bucket=self.templates_bucket,
                Key=template_key
            )
            template_data = response['Body'].read()
            logger.info(f"Downloaded template: {len(template_data):,} bytes")
            return template_data
        except Exception as e:
            logger.error(f"Failed to download template {template_key}: {e}")
            raise

    async def _upload_filled_pdf(self, file_content: bytes, form_type: str, 
                                tax_year: int, metadata: Dict[str, str]) -> str:
        """Upload filled PDF to S3 and return presigned URL."""
        try:
            # Generate unique filename
            timestamp = int(time.time())
            taxpayer_name = metadata.get('taxpayer_name', 'TAXPAYER')
            safe_name = ''.join(c for c in taxpayer_name if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')
            
            output_key = f"filled_forms/{form_type.lower()}/{form_type.upper()}_{tax_year}_{safe_name}_{timestamp}.pdf"
            
            logger.info(f"Uploading filled form to: {output_key}")
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.documents_bucket,
                Key=output_key,
                Body=file_content,
                ContentType='application/pdf',
                Metadata=metadata
            )
            
            # Generate presigned URL
            download_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.documents_bucket,
                    'Key': output_key
                },
                ExpiresIn=3600
            )
            
            logger.info(f"Successfully uploaded filled form: {output_key}")
            return download_url
            
        except Exception as e:
            logger.error(f"Failed to upload filled PDF: {e}")
            raise

    def get_available_forms(self) -> List[Dict[str, Any]]:
        """Get list of available tax forms."""
        return [
            {
                'form_type': '1040',
                'description': 'U.S. Individual Income Tax Return',
                'tax_year': 2024,
                'template_key': 'tax_forms/2024/f1040.pdf'
            }
        ]

    def get_form_fields(self, form_type: str) -> Dict[str, Any]:
        """Get metadata about form fields for a specific form type."""
        if form_type.lower() == '1040':
            return {
                'personal_info': [
                    'f1_01',  # First name
                    'f1_02',  # Middle initial
                    'f1_03',  # Last name
                    'f1_04',  # SSN
                    'f1_05',  # Spouse first name
                    'f1_06',  # Spouse middle initial
                    'f1_07',  # Spouse last name
                    'f1_08',  # Spouse SSN
                    'f1_09',  # Address
                    'f1_10',  # City
                    'f1_11',  # State
                    'f1_12',  # ZIP
                ],
                'income': [
                    'f1_13',  # Wages
                    'f1_14',  # Tax-exempt interest
                    'f1_15',  # Taxable interest
                    'f1_16',  # Qualified dividends
                    'f1_17',  # Ordinary dividends
                    'f1_25',  # Other income
                    'f1_26',  # Total income
                ],
                'deductions': [
                    'f1_28',  # Adjusted gross income
                    'f1_29',  # Standard deduction
                    'f1_34',  # Taxable income
                ],
                'tax': [
                    'f1_35',  # Tax
                    'f1_41',  # Total tax after credits
                    'f1_43',  # Total tax
                ],
                'payments': [
                    'f1_44',  # Federal withholding
                    'f1_49',  # Total payments
                ],
                'refund': [
                    'f1_50',  # Overpayment
                    'f1_51',  # Refund amount
                ],
                'checkboxes': [
                    'c1_1',   # Single
                    'c1_2',   # Married filing separately
                    'c1_3',   # Married filing jointly
                    'c1_4',   # Presidential campaign fund
                ]
            }
        
        return {}


# Tool function for agent integration
async def fill_tax_form(form_type: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fill a tax form with provided data.
    
    Args:
        form_type: Type of form to fill (e.g., '1040')
        form_data: Dictionary containing form field data
        
    Returns:
        Dictionary with filled form URL and metadata
    """
    filler = TaxFormFiller()
    
    if form_type.lower() == '1040':
        return await filler.fill_1040_form(form_data)
    else:
        return {
            'success': False,
            'error': f'Unsupported form type: {form_type}',
            'message': 'Only 1040 forms are currently supported'
        }


# Tool function for getting available forms
def get_available_tax_forms() -> List[Dict[str, Any]]:
    """Get list of available tax forms."""
    filler = TaxFormFiller()
    return filler.get_available_forms()


# Tool function for getting form field metadata
def get_tax_form_fields(form_type: str) -> Dict[str, Any]:
    """Get metadata about form fields for a specific form type."""
    filler = TaxFormFiller()
    return filler.get_form_fields(form_type)
