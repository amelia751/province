"""
Tax Form Filler Tool

AI-powered form filling using hybrid mapping (seed + agent) for precise field matching.
Supports conversational questions for missing critical fields.
"""

import json
import logging
import os
import tempfile
import time
import io
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

from province.core.config import get_settings

logger = logging.getLogger(__name__)

class TaxFormFiller:
    """AI-powered tax form filling with hybrid mapping and conversational questions."""
    
    def __init__(self):
        self.settings = get_settings()
        self.s3_client = boto3.client(
            's3',
            region_name=self.settings.aws_region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.bedrock = boto3.client(
            'bedrock-runtime',
            region_name=self.settings.aws_region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=self.settings.aws_region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.templates_bucket = self.settings.templates_bucket_name
        self.documents_bucket = self.settings.documents_bucket_name
        self.mappings_table = self.dynamodb.Table(os.getenv('FORM_MAPPINGS_TABLE_NAME', 'province-form-mappings'))

    def _get_hybrid_mapping(self, form_type: str, tax_year: str = "2024") -> Optional[Dict[str, Any]]:
        """Load hybrid mapping from DynamoDB."""
        try:
            response = self.mappings_table.get_item(
                Key={'form_type': form_type, 'tax_year': tax_year}
            )
            item = response.get('Item')
            if item:
                def convert_decimal(obj):
                    if isinstance(obj, Decimal):
                        return float(obj)
                    raise TypeError
                return json.loads(json.dumps(item['mapping'], default=convert_decimal))
            return None
        except Exception as e:
            logger.error(f"Error loading hybrid mapping: {e}")
            return None
    
    def _ask_ai_for_questions(self, form_data: Dict[str, Any], form_mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to identify missing critical fields and generate questions."""
        try:
            available_fields = []
            for section, fields in form_mapping.items():
                if isinstance(fields, dict) and section != 'form_metadata':
                    available_fields.extend(list(fields.keys())[:20])
            
            prompt = f"""You are helping fill IRS Form 1040. Review the data and identify MISSING critical fields.

FORM DATA AVAILABLE:
{json.dumps(form_data, indent=2)[:1500]}

FORM FIELDS (examples):
{json.dumps(available_fields[:30], indent=2)}

CRITICAL FIELDS TO CHECK:
- Bank routing/account (if refund > 0)
- Dependent SSN/names (if has dependents)
- Spouse info (if married filing jointly)

TASK: Return JSON with:
1. "needs_input": true/false
2. "questions": list of questions if needs input
3. "ready_to_fill": true/false

OUTPUT:
{{
  "needs_input": true,
  "questions": [
    {{"field": "routing_number_35b", "question": "What's your bank routing number?", "context": "For $X refund"}}
  ],
  "ready_to_fill": false
}}"""

            response = self.bedrock.invoke_model(
                modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 2000,
                    'temperature': 0,
                    'messages': [{'role': 'user', 'content': prompt}]
                })
            )
            
            ai_response = json.loads(response['body'].read())['content'][0]['text']
            json_match = re.search(r'```json\n({.*?})\n```', ai_response, re.DOTALL)
            if json_match:
                ai_response = json_match.group(1)
            
            return json.loads(ai_response)
        except Exception as e:
            logger.error(f"AI question generation error: {e}")
            return {"needs_input": False, "ready_to_fill": True, "questions": []}
    
    async def fill_tax_form(self, form_type: str, form_data: Dict[str, Any], user_responses: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Fill tax form using AI reasoning and hybrid mapping.
        
        Args:
            form_type: Type of form (1040, SCHEDULE_C, etc.)
            form_data: Form data including calculations
            user_responses: Optional responses to questions
            
        Returns:
            Dict with filled form URL, questions, or metadata
        """
        try:
            logger.info(f"🤖 AI-powered filling: {form_type}")
            
            # 1. Load hybrid mapping
            tax_year = form_data.get('tax_year', '2024')
            form_type_upper = form_type.upper()
            mapping_key = 'F1040' if '1040' in form_type_upper else form_type_upper
            
            hybrid_mapping = self._get_hybrid_mapping(mapping_key, tax_year)
            if not hybrid_mapping:
                logger.warning("No hybrid mapping found, falling back to legacy method")
                return await self._legacy_fill(form_type, form_data)
            
            logger.info(f"✅ Loaded hybrid mapping")
            
            # 2. Check if AI needs to ask questions (unless user already responded)
            if not user_responses:
                ai_analysis = self._ask_ai_for_questions(form_data, hybrid_mapping)
                
                if ai_analysis.get('needs_input') and ai_analysis.get('questions'):
                    return {
                        'success': False,
                        'needs_input': True,
                        'message': "I need some additional information:",
                        'questions': ai_analysis['questions']
                    }
            
            # 3. Merge user responses into form_data
            if user_responses:
                form_data = {**form_data, **user_responses}
            
            # 4. Download template
            template_key = self._get_template_path(form_type)
            template_data = await self._download_pdf_template(template_key)
            
            # 5. Fill using hybrid mapping
            filled_pdf_bytes = self._fill_pdf_with_hybrid_mapping(template_data, form_data, hybrid_mapping)
            
            # Upload the filled form with versioning
            upload_result = await self._upload_filled_pdf_with_versioning(
                file_content=filled_pdf_bytes,
                form_type=form_type,
                tax_year=form_data.get('tax_year', 2024),
                metadata={
                    'form_type': form_type,
                    'tax_year': str(form_data.get('tax_year', 2024)),
                    'filled_by': 'tax_form_filler_tool',
                    'filling_method': 'pymupdf_dynamic_mapping',
                    'fields_filled': str(len(form_data)),
                    'taxpayer_name': form_data.get('taxpayer_name', 'Unknown')
                },
                taxpayer_id=form_data.get('taxpayer_name', 'Unknown').replace(' ', '_')
            )
            
            logger.info(f"Successfully filled {form_type} form")
            
            return {
                'success': True,
                'filled_form_url': upload_result['download_url'],
                'form_type': form_type,
                'tax_year': form_data.get('tax_year', 2024),
                'fields_filled': len(form_data),
                'file_size': len(filled_pdf_bytes),
                'message': f'Form {form_type} filled successfully with dynamic mapping',
                'versioning': {
                    'document_id': upload_result['document_id'],
                    'version': upload_result['version'],
                    'is_new_document': upload_result['is_new_document'],
                    'total_versions': upload_result['total_versions'],
                    'previous_versions': upload_result['previous_versions']
                }
            }
            
        except Exception as e:
            logger.error(f"Error filling {form_type} form: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to fill {form_type} form'
            }

    async def fill_1040_form(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fill a 1040 tax form with provided data (legacy method).
        
        Args:
            form_data: Dictionary containing form field data
            
        Returns:
            Dictionary with filled form URL and metadata
        """
        return await self.fill_tax_form('1040', form_data)

    def _get_template_path(self, form_type: str) -> str:
        """
        Get S3 template path for different form types.
        
        Args:
            form_type: Type of form (1040, SCHEDULE_C, STATE_CA, etc.)
            
        Returns:
            S3 key path to the template
        """
        template_paths = {
            '1040': 'tax_forms/2024/f1040.pdf',
            'SCHEDULE_C': 'tax_forms/2024/f1040sc.pdf',
            'SCHEDULE_D': 'tax_forms/2024/f1040sd.pdf',
            'SCHEDULE_E': 'tax_forms/2024/f1040se.pdf',
            'SCHEDULE_A': 'tax_forms/2024/f1040sa.pdf',
            'SCHEDULE_B': 'tax_forms/2024/f1040sb.pdf',
            'STATE_CA': 'tax_forms/2024/ca/ca540.pdf',
            'STATE_NY': 'tax_forms/2024/ny/it201.pdf',
            'STATE_TX': 'tax_forms/2024/tx/no_state_tax.pdf',
            'STATE_FL': 'tax_forms/2024/fl/no_state_tax.pdf',
            'CITY_NYC': 'tax_forms/2024/nyc/nyc_resident.pdf',
            'CITY_SF': 'tax_forms/2024/ca/sf_payroll.pdf',
        }
        
        return template_paths.get(form_type.upper(), 'tax_forms/2024/f1040.pdf')

    def _fill_pdf_with_hybrid_mapping(self, pdf_data: bytes, form_data: Dict[str, Any], hybrid_mapping: Dict[str, Any]) -> bytes:
        """Fill PDF using hybrid mapping (seed + AI agent)."""
        import fitz
        
        logger.info("Filling with hybrid mapping...")
        doc = fitz.open(stream=pdf_data, filetype='pdf')
        
        # Flatten mapping
        flat_mapping = {}
        for section, fields in hybrid_mapping.items():
            if isinstance(fields, dict) and section != 'form_metadata':
                flat_mapping.update(fields)
        
        logger.info(f"Hybrid mapping has {len(flat_mapping)} semantic fields")
        
        filled_text = 0
        filled_checkboxes = 0
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            for widget in page.widgets():
                full_field_name = widget.field_name
                if not full_field_name:
                    continue
                
                # Find semantic name for this PDF field
                semantic_name = None
                for sem, pdf_path in flat_mapping.items():
                    if pdf_path == full_field_name:
                        semantic_name = sem
                        break
                
                if semantic_name and semantic_name in form_data:
                    value = form_data[semantic_name]
                    
                    if widget.field_type == 7:  # Text
                        widget.field_value = str(value)
                        widget.update()
                        filled_text += 1
                    elif widget.field_type == 2:  # Checkbox
                        if value is True or value == "Yes" or value == 1:
                            widget.field_value = "Yes"
                            widget.update()
                            filled_checkboxes += 1
        
        logger.info(f"✅ Filled {filled_text} text, {filled_checkboxes} checkboxes")
        
        # Save to bytes
        output_buffer = io.BytesIO()
        doc.save(output_buffer, deflate=True)
        output_buffer.seek(0)
        pdf_bytes = output_buffer.read()
        doc.close()
        
        return pdf_bytes
    
    async def _legacy_fill(self, form_type: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy fill method (fallback)."""
        template_key = self._get_template_path(form_type)
        template_data = await self._download_pdf_template(template_key)
        filled_pdf_bytes = self._fill_pdf_with_pymupdf_legacy(template_data, form_data)
        
        upload_result = await self._upload_filled_pdf_with_versioning(
            file_content=filled_pdf_bytes,
            form_type=form_type,
            tax_year=form_data.get('tax_year', 2024),
            metadata={'method': 'legacy'},
            taxpayer_id=form_data.get('taxpayer_name', 'Unknown').replace(' ', '_')
        )
        
        return {
            'success': True,
            'filled_form_url': upload_result['download_url'],
            'message': 'Form filled (legacy method)'
        }
    
    def _fill_pdf_with_pymupdf_legacy(self, pdf_data: bytes, form_data: Dict[str, Any]) -> bytes:
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
            
            # Log all field names for debugging
            logger.info("Available text field names:")
            for widget in text_fields[:10]:  # Log first 10 for debugging
                logger.info(f"  - {widget.field_name}")
            
            # Get dynamic field mapping based on form type
            field_mapping = self._get_field_mapping_for_form(form_data)
            
            # Fill text fields using mapping
            for widget in text_fields:
                field_name = widget.field_name
                if field_name:
                    # Try to match using field mapping
                    for data_key, value in form_data.items():
                        mapped_fields = field_mapping.get(data_key, [])
                        
                        # Extract the simple field name from the full path
                        # e.g., "topmostSubform[0].Page1[0].f1_01[0]" -> "f1_01"
                        simple_field_name = field_name.split('.')[-1].split('[')[0] if '.' in field_name else field_name
                        
                        # Check if this widget matches any mapped field
                        if simple_field_name in mapped_fields:
                            try:
                                # Special handling for taxpayer_name - split into parts
                                if data_key == 'taxpayer_name' and isinstance(value, str):
                                    name_parts = value.split()
                                    if simple_field_name == 'f1_01' and len(name_parts) > 0:  # First name
                                        formatted_value = name_parts[0]
                                    elif simple_field_name == 'f1_02' and len(name_parts) > 2:  # Middle initial
                                        formatted_value = name_parts[1][0] if name_parts[1] else ''
                                    elif simple_field_name == 'f1_03' and len(name_parts) > 1:  # Last name
                                        formatted_value = name_parts[-1]
                                    else:
                                        formatted_value = self._format_field_value(data_key, value)
                                else:
                                    # Format the value appropriately
                                    formatted_value = self._format_field_value(data_key, value)
                                
                                widget.field_value = formatted_value
                                widget.update()
                                filled_count += 1
                                logger.info(f"✅ Filled text field {field_name} ({data_key}): {formatted_value}")
                                break
                            except Exception as e:
                                logger.warning(f"Could not fill text field {field_name}: {e}")
                        
                        # Also try direct matching as fallback
                        elif (data_key in field_name or 
                              field_name.endswith(data_key) or
                              field_name.endswith(f"{data_key}[0]")):
                            try:
                                formatted_value = self._format_field_value(data_key, value)
                                widget.field_value = formatted_value
                                widget.update()
                                filled_count += 1
                                logger.info(f"✅ Filled text field {field_name} (direct match): {formatted_value}")
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

    async def _upload_filled_pdf_with_versioning(self, file_content: bytes, form_type: str, 
                                               tax_year: int, metadata: Dict[str, str], 
                                               taxpayer_id: str = None) -> Dict[str, Any]:
        """Upload filled PDF with versioning support."""
        try:
            # Generate taxpayer ID if not provided
            if not taxpayer_id:
                taxpayer_id = metadata.get('taxpayer_name', 'TAXPAYER').replace(' ', '_')
            
            # Create base document ID for versioning
            document_id = f"tax_form_{taxpayer_id}_{form_type}_{tax_year}"
            base_key = f"filled_forms/{taxpayer_id}/{form_type.lower()}/{tax_year}"
            
            # Check for existing versions
            existing_versions = await self._list_existing_versions(base_key)
            version_num = len(existing_versions) + 1
            
            # Create versioned S3 key
            timestamp = int(time.time())
            output_key = f"{base_key}/v{version_num:03d}_{form_type}_{timestamp}.pdf"
            
            logger.info(f"Uploading filled form version {version_num} to: {output_key}")
            
            # Enhanced metadata with versioning info
            enhanced_metadata = {
                **metadata,
                'document_id': document_id,
                'version': f"v{version_num}",
                'taxpayer_id': taxpayer_id,
                'created_at': datetime.now().isoformat(),
                'file_size': str(len(file_content)),
                'content_hash': self._calculate_content_hash(file_content)
            }
            
            # Add previous version reference if exists
            if existing_versions:
                enhanced_metadata['previous_version'] = existing_versions[-1]['version']
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.documents_bucket,
                Key=output_key,
                Body=file_content,
                ContentType='application/pdf',
                Metadata=enhanced_metadata
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
            
            # Store version info in DynamoDB if table exists
            await self._store_version_metadata(document_id, {
                'version': f"v{version_num}",
                's3_key': output_key,
                'size': len(file_content),
                'created_at': datetime.now().isoformat(),
                'metadata': enhanced_metadata,
                'download_url': download_url
            })
            
            logger.info(f"Successfully uploaded filled form version {version_num}: {output_key}")
            
            return {
                'download_url': download_url,
                'document_id': document_id,
                'version': f"v{version_num}",
                's3_key': output_key,
                'is_new_document': version_num == 1,
                'previous_versions': [v['version'] for v in existing_versions],
                'total_versions': version_num
            }
            
        except Exception as e:
            logger.error(f"Failed to upload filled PDF with versioning: {e}")
            raise

    async def _upload_filled_pdf(self, file_content: bytes, form_type: str, 
                                tax_year: int, metadata: Dict[str, str]) -> str:
        """Legacy upload method - now uses versioning internally."""
        try:
            result = await self._upload_filled_pdf_with_versioning(
                file_content, form_type, tax_year, metadata
            )
            return result['download_url']
        except Exception as e:
            logger.error(f"Failed to upload filled PDF: {e}")
            raise

    def get_available_forms(self) -> List[Dict[str, Any]]:
        """Get list of available tax forms."""
        return [
            # Federal Forms
            {
                'form_type': '1040',
                'description': 'U.S. Individual Income Tax Return',
                'category': 'federal',
                'tax_year': 2024,
                'template_key': 'tax_forms/2024/f1040.pdf'
            },
            {
                'form_type': 'SCHEDULE_C',
                'description': 'Profit or Loss From Business (Sole Proprietorship)',
                'category': 'federal_schedule',
                'tax_year': 2024,
                'template_key': 'tax_forms/2024/f1040sc.pdf'
            },
            {
                'form_type': 'SCHEDULE_D',
                'description': 'Capital Gains and Losses',
                'category': 'federal_schedule',
                'tax_year': 2024,
                'template_key': 'tax_forms/2024/f1040sd.pdf'
            },
            {
                'form_type': 'SCHEDULE_E',
                'description': 'Supplemental Income and Loss',
                'category': 'federal_schedule',
                'tax_year': 2024,
                'template_key': 'tax_forms/2024/f1040se.pdf'
            },
            {
                'form_type': 'SCHEDULE_A',
                'description': 'Itemized Deductions',
                'category': 'federal_schedule',
                'tax_year': 2024,
                'template_key': 'tax_forms/2024/f1040sa.pdf'
            },
            
            # State Forms
            {
                'form_type': 'STATE_CA',
                'description': 'California Resident Income Tax Return',
                'category': 'state',
                'state': 'CA',
                'tax_year': 2024,
                'template_key': 'tax_forms/2024/ca/ca540.pdf'
            },
            {
                'form_type': 'STATE_NY',
                'description': 'New York Resident Income Tax Return',
                'category': 'state',
                'state': 'NY',
                'tax_year': 2024,
                'template_key': 'tax_forms/2024/ny/it201.pdf'
            },
            {
                'form_type': 'STATE_TX',
                'description': 'Texas (No State Income Tax)',
                'category': 'state',
                'state': 'TX',
                'tax_year': 2024,
                'template_key': 'tax_forms/2024/tx/no_state_tax.pdf'
            },
            {
                'form_type': 'STATE_FL',
                'description': 'Florida (No State Income Tax)',
                'category': 'state',
                'state': 'FL',
                'tax_year': 2024,
                'template_key': 'tax_forms/2024/fl/no_state_tax.pdf'
            },
            
            # City Forms
            {
                'form_type': 'CITY_NYC',
                'description': 'New York City Resident Income Tax Return',
                'category': 'city',
                'city': 'New York City',
                'state': 'NY',
                'tax_year': 2024,
                'template_key': 'tax_forms/2024/nyc/nyc_resident.pdf'
            },
            {
                'form_type': 'CITY_SF',
                'description': 'San Francisco Payroll Tax',
                'category': 'city',
                'city': 'San Francisco',
                'state': 'CA',
                'tax_year': 2024,
                'template_key': 'tax_forms/2024/ca/sf_payroll.pdf'
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

    def _get_field_mapping_for_form(self, form_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Get dynamic field mapping based on form type and available data.
        
        Args:
            form_data: Form data containing form_type and other fields
            
        Returns:
            Dictionary mapping data keys to form field names
        """
        form_type = form_data.get('form_type', '1040').upper()
        
        # Get base mapping for the form type
        base_mapping = self._get_base_field_mapping(form_type)
        
        # Enhance mapping with intelligent field detection
        enhanced_mapping = self._enhance_mapping_with_field_detection(base_mapping, form_data)
        
        logger.info(f"Using field mapping for {form_type}: {len(enhanced_mapping)} data keys mapped")
        return enhanced_mapping

    def _get_base_field_mapping(self, form_type: str) -> Dict[str, List[str]]:
        """
        Get base field mapping for different form types.
        
        Args:
            form_type: Type of tax form (1040, SCHEDULE_C, STATE_CA, etc.)
            
        Returns:
            Base field mapping dictionary
        """
        mappings = {
            '1040': {
                # Personal Information
                'taxpayer_name': ['f1_01', 'f1_02', 'f1_03'],  # First, Middle, Last
                'ssn': ['f1_04'],
                'spouse_name': ['f1_05', 'f1_06', 'f1_07'],
                'spouse_ssn': ['f1_08'],
                'address': ['f1_09'],
                'city': ['f1_10'],
                'state': ['f1_11'],
                'zip': ['f1_12'],
                
                # Income
                'wages': ['f1_13'],
                'taxable_interest': ['f1_14'],
                'tax_exempt_interest': ['f1_15'],
                'ordinary_dividends': ['f1_16'],
                'qualified_dividends': ['f1_17'],
                'ira_distributions': ['f1_18'],
                'pensions_annuities': ['f1_19'],
                'social_security': ['f1_20'],
                'capital_gains': ['f1_21'],
                'other_income': ['f1_22'],
                'total_income': ['f1_23'],
                
                # Adjustments and Deductions
                'adjusted_gross_income': ['f1_24'],
                'standard_deduction': ['f1_29'],
                'itemized_deductions': ['f1_30'],
                'taxable_income': ['f1_34'],
                
                # Tax and Credits
                'tax_liability': ['f1_35'],
                'child_tax_credit': ['f1_36'],
                'education_credits': ['f1_37'],
                'other_credits': ['f1_38'],
                'total_tax': ['f1_39'],
                
                # Payments
                'federal_withholding': ['f1_44'],
                'estimated_tax_payments': ['f1_45'],
                'earned_income_credit': ['f1_46'],
                'additional_child_tax_credit': ['f1_47'],
                'total_payments': ['f1_48'],
                
                # Refund or Amount Due
                'overpayment': ['f1_50'],
                'refund_or_due': ['f1_50', 'f1_51'],
                'amount_owed': ['f1_52']
            },
            
            'SCHEDULE_C': {
                # Business Information
                'business_name': ['f2_01'],
                'business_code': ['f2_02'],
                'business_address': ['f2_03'],
                'accounting_method': ['f2_04'],
                'ein': ['f2_05'],
                
                # Income
                'gross_receipts': ['f2_10'],
                'returns_allowances': ['f2_11'],
                'other_income': ['f2_12'],
                'total_income': ['f2_13'],
                
                # Expenses
                'advertising': ['f2_20'],
                'car_truck_expenses': ['f2_21'],
                'commissions_fees': ['f2_22'],
                'contract_labor': ['f2_23'],
                'depletion': ['f2_24'],
                'depreciation': ['f2_25'],
                'employee_benefit_programs': ['f2_26'],
                'insurance': ['f2_27'],
                'interest_mortgage': ['f2_28'],
                'interest_other': ['f2_29'],
                'legal_professional': ['f2_30'],
                'office_expense': ['f2_31'],
                'pension_profit_sharing': ['f2_32'],
                'rent_lease_vehicles': ['f2_33'],
                'rent_lease_other': ['f2_34'],
                'repairs_maintenance': ['f2_35'],
                'supplies': ['f2_36'],
                'taxes_licenses': ['f2_37'],
                'travel': ['f2_38'],
                'meals': ['f2_39'],
                'utilities': ['f2_40'],
                'wages': ['f2_41'],
                'other_expenses': ['f2_42'],
                'total_expenses': ['f2_43'],
                
                # Net Profit/Loss
                'net_profit_loss': ['f2_50']
            },
            
            'SCHEDULE_D': {
                # Short-term Capital Gains/Losses
                'st_description_1': ['f3_01'],
                'st_date_acquired_1': ['f3_02'],
                'st_date_sold_1': ['f3_03'],
                'st_proceeds_1': ['f3_04'],
                'st_cost_basis_1': ['f3_05'],
                'st_gain_loss_1': ['f3_06'],
                
                # Long-term Capital Gains/Losses
                'lt_description_1': ['f3_10'],
                'lt_date_acquired_1': ['f3_11'],
                'lt_date_sold_1': ['f3_12'],
                'lt_proceeds_1': ['f3_13'],
                'lt_cost_basis_1': ['f3_14'],
                'lt_gain_loss_1': ['f3_15'],
                
                # Totals
                'total_st_gain_loss': ['f3_20'],
                'total_lt_gain_loss': ['f3_21'],
                'net_capital_gain_loss': ['f3_22']
            },
            
            'STATE_CA': {  # California State Tax
                'ca_taxpayer_name': ['ca_f1_01', 'ca_f1_02', 'ca_f1_03'],
                'ca_ssn': ['ca_f1_04'],
                'ca_spouse_name': ['ca_f1_05', 'ca_f1_06', 'ca_f1_07'],
                'ca_spouse_ssn': ['ca_f1_08'],
                'ca_address': ['ca_f1_09'],
                'ca_city': ['ca_f1_10'],
                'ca_zip': ['ca_f1_11'],
                'ca_wages': ['ca_f1_20'],
                'ca_withholding': ['ca_f1_30'],
                'ca_tax_liability': ['ca_f1_40'],
                'ca_refund_due': ['ca_f1_50']
            },
            
            'STATE_NY': {  # New York State Tax
                'ny_taxpayer_name': ['ny_f1_01', 'ny_f1_02', 'ny_f1_03'],
                'ny_ssn': ['ny_f1_04'],
                'ny_spouse_name': ['ny_f1_05', 'ny_f1_06', 'ny_f1_07'],
                'ny_spouse_ssn': ['ny_f1_08'],
                'ny_address': ['ny_f1_09'],
                'ny_city': ['ny_f1_10'],
                'ny_zip': ['ny_f1_11'],
                'ny_wages': ['ny_f1_20'],
                'ny_withholding': ['ny_f1_30'],
                'ny_tax_liability': ['ny_f1_40'],
                'ny_refund_due': ['ny_f1_50']
            },
            
            'CITY_NYC': {  # NYC City Tax
                'nyc_taxpayer_name': ['nyc_f1_01', 'nyc_f1_02', 'nyc_f1_03'],
                'nyc_ssn': ['nyc_f1_04'],
                'nyc_address': ['nyc_f1_09'],
                'nyc_wages': ['nyc_f1_20'],
                'nyc_withholding': ['nyc_f1_30'],
                'nyc_tax_liability': ['nyc_f1_40'],
                'nyc_refund_due': ['nyc_f1_50']
            }
        }
        
        return mappings.get(form_type, {})

    def _enhance_mapping_with_field_detection(self, base_mapping: Dict[str, List[str]], 
                                            form_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Enhance base mapping with intelligent field detection based on available data.
        
        Args:
            base_mapping: Base field mapping for the form type
            form_data: Available form data
            
        Returns:
            Enhanced field mapping
        """
        enhanced_mapping = base_mapping.copy()
        
        # Add intelligent mappings for common field patterns
        for data_key in form_data.keys():
            if data_key not in enhanced_mapping:
                # Try to find matching fields using common patterns
                potential_fields = self._find_potential_field_matches(data_key)
                if potential_fields:
                    enhanced_mapping[data_key] = potential_fields
                    logger.info(f"Auto-detected field mapping: {data_key} -> {potential_fields}")
        
        return enhanced_mapping

    def _find_potential_field_matches(self, data_key: str) -> List[str]:
        """
        Find potential field matches using common naming patterns.
        
        Args:
            data_key: Data key to find matches for
            
        Returns:
            List of potential field names
        """
        potential_fields = []
        
        # Common field naming patterns
        patterns = {
            'name': ['name', 'nm', 'taxpayer'],
            'address': ['addr', 'address', 'street'],
            'city': ['city', 'cty'],
            'state': ['state', 'st'],
            'zip': ['zip', 'postal', 'zipcode'],
            'ssn': ['ssn', 'social', 'tin'],
            'phone': ['phone', 'tel', 'telephone'],
            'email': ['email', 'mail'],
            'income': ['income', 'wages', 'salary'],
            'tax': ['tax', 'liability'],
            'withholding': ['withhold', 'withheld', 'wh'],
            'refund': ['refund', 'overpayment'],
            'amount_due': ['due', 'owed', 'balance'],
            'date': ['date', 'dt'],
            'amount': ['amount', 'amt']
        }
        
        data_key_lower = data_key.lower()
        
        # Look for pattern matches
        for pattern_key, pattern_values in patterns.items():
            if any(pattern in data_key_lower for pattern in pattern_values):
                # Generate potential field names based on common form field patterns
                potential_fields.extend([
                    f"f1_{pattern_key}",  # Standard pattern
                    f"{pattern_key}",     # Simple pattern
                    f"field_{pattern_key}",  # Field prefix pattern
                    f"txt_{pattern_key}",    # Text field pattern
                ])
        
        return potential_fields[:3]  # Return top 3 matches to avoid too many attempts

    async def _list_existing_versions(self, base_key: str) -> List[Dict[str, Any]]:
        """List existing versions of a document in S3."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.documents_bucket,
                Prefix=base_key
            )
            
            versions = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    if key.endswith('.pdf'):
                        # Extract version from filename
                        filename = key.split('/')[-1]
                        if filename.startswith('v'):
                            version = filename.split('_')[0]  # e.g., 'v001'
                            versions.append({
                                'version': version,
                                's3_key': key,
                                'size': obj['Size'],
                                'last_modified': obj['LastModified'].isoformat()
                            })
            
            # Sort by version number
            versions.sort(key=lambda x: int(x['version'][1:]))
            return versions
            
        except Exception as e:
            logger.warning(f"Could not list existing versions for {base_key}: {e}")
            return []

    def _calculate_content_hash(self, content: bytes) -> str:
        """Calculate SHA256 hash of content."""
        import hashlib
        return hashlib.sha256(content).hexdigest()

    async def _store_version_metadata(self, document_id: str, version_info: Dict[str, Any]):
        """Store version metadata in DynamoDB if available."""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Use the document versions table
            dynamodb = boto3.resource('dynamodb', region_name=self.settings.aws_region)
            
            # Use the document versions table name
            table_name = os.getenv('DOCUMENT_VERSIONS_TABLE_NAME', 'province-document-versions')
            table = dynamodb.Table(table_name)
            
            # Extract form type and taxpayer from document_id
            # Format: tax_form_TaxpayerName_FormType_Year
            parts = document_id.split('_')
            if len(parts) >= 4:
                taxpayer_id = '_'.join(parts[2:-2]) if len(parts) > 4 else parts[2]
                form_type = parts[-2]
                tax_year = parts[-1]
            else:
                taxpayer_id = 'unknown'
                form_type = 'unknown'
                tax_year = '2024'
            
            # Store version metadata with proper structure
            table.put_item(
                Item={
                    'document_id': document_id,
                    'version': version_info['version'],
                    'taxpayer_id': taxpayer_id,
                    'form_type': form_type,
                    'tax_year': tax_year,
                    's3_key': version_info['s3_key'],
                    'size': version_info['size'],
                    'created_at': version_info['created_at'],
                    'content_hash': version_info['metadata'].get('content_hash', ''),
                    'file_size': version_info['metadata'].get('file_size', ''),
                    'filling_method': version_info['metadata'].get('filling_method', ''),
                    'fields_filled': version_info['metadata'].get('fields_filled', ''),
                    'download_url': version_info['download_url'],
                    'metadata': version_info['metadata']
                }
            )
            
            logger.info(f"Stored version metadata for {document_id} {version_info['version']} in {table_name}")
            
        except Exception as e:
            logger.warning(f"Could not store version metadata: {e}")
            # Don't fail the upload if metadata storage fails

    async def get_version_history(self, document_id: str) -> List[Dict[str, Any]]:
        """Get version history for a document."""
        try:
            # Extract base info from document_id
            # Format: tax_form_John_Doe_1040_2024
            parts = document_id.split('_')
            if len(parts) >= 4:
                # Skip 'tax' and 'form' parts
                taxpayer_id = '_'.join(parts[2:-2]) if len(parts) > 4 else parts[2]
                form_type = parts[-2]
                tax_year = parts[-1]
                
                base_key = f"filled_forms/{taxpayer_id}/{form_type.lower()}/{tax_year}/"
                logger.info(f"Looking for versions with base key: {base_key}")
                return await self._list_existing_versions(base_key)
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting version history for {document_id}: {e}")
            return []


# Tool function for agent integration
async def fill_tax_form(form_type: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fill any tax form with provided data using dynamic field mapping.
    
    Args:
        form_type: Type of form to fill (1040, SCHEDULE_C, STATE_CA, etc.)
        form_data: Dictionary containing form field data
        
    Returns:
        Dictionary with filled form URL and metadata
    """
    filler = TaxFormFiller()
    return await filler.fill_tax_form(form_type, form_data)


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
