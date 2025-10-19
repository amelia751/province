"""
Form Template Processor Lambda

Automatically processes tax form templates uploaded to S3, extracts fields,
uses AI to generate semantic mappings, and caches them in DynamoDB.

Triggered by: S3 EventBridge notification on object created
"""

import json
import logging
import os
import re
import sys
import tempfile
from typing import Dict, List, Any
from datetime import datetime

import boto3
import fitz  # PyMuPDF

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Add src to path for agent import
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_src = os.path.abspath(os.path.join(current_dir, '../../'))  # Points to backend/src
if backend_src not in sys.path:
    sys.path.insert(0, backend_src)

try:
    from province.agents.form_mapping_agent import FormMappingAgent
    USE_AGENT = True
    logger.info("✅ FormMappingAgent loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️  FormMappingAgent not available ({e}), using single-shot AI")
    USE_AGENT = False


class FormTemplateProcessor:
    """Processes tax form templates and generates AI-powered semantic mappings."""
    
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name='us-east-1')
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.mappings_table = self.dynamodb.Table('province-form-mappings')
        
        # Initialize FormMappingAgent if available
        if USE_AGENT:
            self.mapping_agent = FormMappingAgent(aws_region='us-east-1')
            logger.info("🤖 FormMappingAgent initialized")
    
    def extract_fields_from_pdf(self, pdf_bytes: bytes) -> List[Dict[str, Any]]:
        """Extract all form fields from PDF using PyMuPDF."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(pdf_bytes)
            temp_path = temp_file.name
        
        try:
            doc = fitz.open(temp_path)
            fields = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Get text blocks for label matching
                text_blocks = page.get_text("dict")['blocks']
                text_labels = []
                for block in text_blocks:
                    if block['type'] == 0:  # Text block
                        for line in block.get('lines', []):
                            text = ''.join([span['text'] for span in line.get('spans', [])])
                            if text.strip():
                                text_labels.append({
                                    'text': text.strip(),
                                    'bbox': line['bbox']
                                })
                
                # Extract form fields
                for widget in page.widgets():
                    field_name = widget.field_name
                    if not field_name:
                        continue
                    
                    field_type = "text"
                    if widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                        field_type = "checkbox"
                    elif widget.field_type == fitz.PDF_WIDGET_TYPE_RADIOBUTTON:
                        field_type = "radio"
                    
                    # Find nearby label
                    rect = widget.rect
                    nearby_label = self._find_nearby_label(rect, text_labels)
                    
                    fields.append({
                        'field_name': field_name,
                        'field_type': field_type,
                        'page': page_num + 1,
                        'position': {
                            'x': round(rect.x0, 1),
                            'y': round(rect.y0, 1),
                            'width': round(rect.width, 1),
                            'height': round(rect.height, 1)
                        },
                        'nearby_label': nearby_label[:200] if nearby_label else None
                    })
            
            doc.close()
            os.unlink(temp_path)
            
            logger.info(f"Extracted {len(fields)} fields from PDF")
            return fields
            
        except Exception as e:
            logger.error(f"Error extracting fields: {e}")
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise
    
    def _find_nearby_label(self, field_rect, text_labels) -> str:
        """Find text label near a form field."""
        field_x = field_rect.x0
        field_y = field_rect.y0
        
        candidates = []
        for label in text_labels:
            label_x = label['bbox'][0]
            label_y = label['bbox'][1]
            
            # Label should be above or to the left of field
            if (label_y < field_y and field_y - label_y < 50) or \
               (label_x < field_x and field_x - label_x < 100):
                
                distance = ((label_x - field_x)**2 + (label_y - field_y)**2)**0.5
                candidates.append((distance, label['text']))
        
        if candidates:
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]
        return None
    
    def generate_mapping_with_ai(self, form_type: str, tax_year: str, fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use FormMappingAgent (agentic reasoning) or fallback to single-shot AI."""
        
        if USE_AGENT:
            logger.info("🤖 Using FormMappingAgent (agentic reasoning)...")
            # Convert fields to format expected by agent
            agent_fields = []
            for f in fields:
                agent_fields.append({
                    'field_name': f['field_name'],
                    'field_type': 'Text' if f['field_type'] == 'text' else 'CheckBox',
                    'field_value': None,
                    'page_number': f['page'],
                    'rect': {
                        'x0': f['position']['x'],
                        'y0': f['position']['y'],
                        'x1': f['position']['x'] + f['position']['width'],
                        'y1': f['position']['y'] + f['position']['height']
                    },
                    'nearby_label': f.get('nearby_label', '')
                })
            
            mapping = self.mapping_agent.map_form_fields(
                form_type=form_type,
                tax_year=tax_year,
                fields=agent_fields
            )
            
            return mapping
        
        # Fallback to single-shot AI
        logger.warning("⚠️  Using fallback single-shot AI (may not achieve 90%+ coverage)")
        
        # Prepare condensed field info for AI
        field_summary = []
        for f in fields:
            field_summary.append({
                'name': f['field_name'],
                'type': f['field_type'],
                'page': f['page'],
                'y_pos': f['position']['y'],
                'label': f['nearby_label'][:80] if f['nearby_label'] else None
            })
        
        prompt = f"""You are a PDF form analysis expert creating a COMPLETE field mapping.

FORM: {form_type} (2024)
FIELDS TO MAP: {len(fields)} fields (YOU MUST MAP ALL OF THEM)

FIELDS LIST:
{json.dumps(field_summary, indent=2)}

**YOUR MISSION**: Create a JSON mapping for EVERY SINGLE field above. Not most. Not the important ones. EVERY. SINGLE. ONE.

PROCESS:
1. Go through the field list sequentially
2. For EACH field, create a semantic name and add it to the appropriate section
3. If you see similar fields (like dependent rows 1-4), map ALL of them individually
4. Don't skip fields because they seem redundant - map them anyway
5. Count as you go - you should end up with {len(fields)} mappings

MANDATORY:
- If there are 4 dependent rows with 5 fields each = map all 20 fields
- If there are 10 similar text fields for different lines = map all 10
- If there are multiple checkboxes with same base name = map each one with unique semantic name
- You MUST have close to {len(fields)} total field mappings in your output

FIELD NAMING CONVENTIONS:
- Text fields: Use snake_case describing content (e.g., "taxpayer_first_name", "wages_line_1a")
- Checkboxes: Include checkbox purpose (e.g., "filing_status_single", "presidential_election_you")
- Keep original FULL field names as values (e.g., "topmostSubform[0].Page1[0].f1_04[0]")
- **CRITICAL**: Some fields have same base name but different array indices (e.g., c1_3[0], c1_3[1], c1_3[2])
  Each of these is a SEPARATE field that needs its own semantic name!

DISCOVER SECTIONS DYNAMICALLY:
Look at the nearby_label and y_pos to understand what each field is for. Common sections might include:
- Header/metadata (tax year, form info)
- Personal identification (names, SSNs)
- Address information
- Electoral/campaign checkboxes
- Filing status
- Standard deduction options
- Age/blindness indicators
- Dependent information
- Income lines (wages, interest, dividends, etc.)
- Adjustments and deductions
- Tax calculations
- Credits
- Payments and withholding
- Refund or amount owed
- Bank account info
- Third party designee
- Signature fields
- Paid preparer information

OUTPUT FORMAT:
{{
  "form_metadata": {{
    "form_type": "{form_type}",
    "tax_year": "2024",
    "total_fields": {len(fields)},
    "field_types": {{
      "text": <count>,
      "checkbox": <count>
    }}
  }},
  "<section_name>": {{
    "<semantic_field_name>": "<actual_field_name>",
    ...
  }},
  ...
}}

SPECIFIC CHECKLIST - Verify you included:
✓ All {len([f for f in fields if f['field_type'] == 'text'])} text fields
✓ All {len([f for f in fields if f['field_type'] == 'checkbox'])} checkbox fields
✓ Presidential Election (2 checkboxes - you and spouse)
✓ Filing status (5+ checkboxes for single, married joint/separate, HOH, QSS)
✓ Digital assets (2 checkboxes - yes and no)
✓ Standard deduction options (multiple checkboxes)
✓ Age/Blindness (4 checkboxes - you born before, you blind, spouse born before, spouse blind)
✓ Dependent-related checkboxes (child tax credit, other credit for each dependent row)
✓ Third party designee (text fields + checkbox)
✓ Signature fields (taxpayer, spouse, preparer)
✓ All paid preparer fields (name, PTIN, firm info, etc.)
✓ Direct deposit (routing, account, account type checkboxes)

VALIDATION: Count your output - you should have close to {len(fields)} mappings!

IMPORTANT:
- Create as many sections as needed to organize ALL {len(fields)} fields
- Don't follow a predefined structure - discover it from the form
- Map EVERY SINGLE FIELD, even if it seems minor
- Use nearby_label to understand each field's purpose
- If unsure about a field, include it anyway with a descriptive guess
- Field names should be usable in code (snake_case)
- **Your output will be validated - if coverage < 90%, you failed the task**

Output ONLY valid JSON. No explanations, no markdown, just pure JSON."""

        try:
            # Use cross-region inference profile for Claude 3.5 Sonnet
            response = self.bedrock.invoke_model(
                modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 8000,  # Increased for comprehensive mapping
                    'temperature': 0.0,
                    'messages': [{
                        'role': 'user',
                        'content': prompt
                    }]
                })
            )
            
            response_body = json.loads(response['body'].read())
            mapping_text = response_body['content'][0]['text']
            
            # Extract JSON from response (in case it's wrapped in markdown)
            if '```json' in mapping_text:
                mapping_text = mapping_text.split('```json')[1].split('```')[0].strip()
            elif '```' in mapping_text:
                mapping_text = mapping_text.split('```')[1].split('```')[0].strip()
            
            mapping = json.loads(mapping_text)
            logger.info(f"Generated AI mapping with {len(mapping)} sections")
            return mapping
            
        except Exception as e:
            logger.error(f"Error generating AI mapping: {e}")
            raise
    
    def validate_mapping(self, mapping: Dict[str, Any], fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that the AI-generated mapping is correct."""
        field_names = set(f['field_name'] for f in fields)
        # Also create a set of simplified field names (extract f1_XX, f2_XX, c1_X from full paths)
        simplified_names = set()
        import re
        for full_name in field_names:
            # Extract simplified name like "f1_04" from "topmostSubform[0].Page1[0].f1_04[0]"
            match = re.search(r'([fc][12]_\d+)', full_name)
            if match:
                simplified_names.add(match.group(1))
        
        errors = []
        warnings = []
        
        # Extract all field references from mapping
        def extract_field_refs(obj, path=""):
            refs = []
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and (value.startswith('f1_') or value.startswith('f2_') or value.startswith('c1_')):
                        refs.append((f"{path}.{key}", value))
                    elif isinstance(value, (dict, list)):
                        refs.extend(extract_field_refs(value, f"{path}.{key}"))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    refs.extend(extract_field_refs(item, f"{path}[{i}]"))
            return refs
        
        field_refs = extract_field_refs(mapping)
        
        # Check if all referenced fields exist (using simplified names)
        for path, field_name in field_refs:
            # Strip array notation if AI added it (e.g., c1_3[1] -> c1_3)
            clean_field_name = re.sub(r'\[\d+\]$', '', field_name)
            
            # Check both full name and simplified name
            if field_name not in field_names and clean_field_name not in simplified_names:
                errors.append(f"Field {field_name} referenced at {path} does not exist in PDF")
        
        # Check coverage
        mapped_fields = set(ref[1] for ref in field_refs)
        unmapped_fields = field_names - mapped_fields
        
        coverage_pct = (len(mapped_fields) / len(field_names)) * 100 if field_names else 0
        
        if coverage_pct < 80:  # Expect at least 80% coverage
            warnings.append(f"Only {coverage_pct:.1f}% field coverage ({len(mapped_fields)}/{len(field_names)} fields). Aim for 90%+")
        elif coverage_pct < 90:
            warnings.append(f"Good coverage: {coverage_pct:.1f}% ({len(mapped_fields)}/{len(field_names)} fields). Can improve to 90%+")
        else:
            # This is good!
            pass
        
        is_valid = len(errors) == 0
        
        return {
            'valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'coverage': f"{len(mapped_fields)}/{len(field_names)} fields mapped"
        }
    
    def save_mapping(self, form_type: str, tax_year: str, mapping: Dict[str, Any], 
                    validation_result: Dict[str, Any], fields_count: int):
        """Save mapping to DynamoDB."""
        try:
            self.mappings_table.put_item(
                Item={
                    'form_type': form_type,
                    'tax_year': tax_year,
                    'mapping': mapping,
                    'metadata': {
                        'generated_at': datetime.utcnow().isoformat(),
                        'model': 'claude-3.5-sonnet',
                        'fields_count': fields_count,
                        'validation': validation_result,
                        'version': '1.0'
                    }
                }
            )
            logger.info(f"Saved mapping for {form_type}-{tax_year} to DynamoDB")
        except Exception as e:
            logger.error(f"Error saving mapping: {e}")
            raise
    
    def process_form_template(self, bucket: str, key: str) -> Dict[str, Any]:
        """Main processing function."""
        logger.info(f"Processing form template: s3://{bucket}/{key}")
        
        # Extract form type and year from S3 key
        # Expected format: tax_forms/2024/f1040.pdf
        match = re.search(r'(\d{4})/([a-z0-9_-]+)\.pdf$', key, re.IGNORECASE)
        if not match:
            raise ValueError(f"Invalid S3 key format: {key}. Expected: year/form_name.pdf")
        
        tax_year = match.group(1)
        form_name = match.group(2)
        form_type = form_name.upper()
        
        # Download PDF
        response = self.s3_client.get_object(Bucket=bucket, Key=key)
        pdf_bytes = response['Body'].read()
        logger.info(f"Downloaded {len(pdf_bytes):,} bytes")
        
        # Extract fields
        fields = self.extract_fields_from_pdf(pdf_bytes)
        
        # Generate AI mapping
        mapping = self.generate_mapping_with_ai(form_type, tax_year, fields)
        
        # Validate mapping
        validation_result = self.validate_mapping(mapping, fields)
        
        if not validation_result['valid']:
            logger.error(f"Mapping validation failed: {validation_result['errors']}")
            raise ValueError(f"Invalid mapping: {validation_result['errors']}")
        
        if validation_result['warnings']:
            logger.warning(f"Mapping warnings: {validation_result['warnings']}")
        
        # Save to DynamoDB
        self.save_mapping(form_type, tax_year, mapping, validation_result, len(fields))
        
        return {
            'form_type': form_type,
            'tax_year': tax_year,
            'fields_count': len(fields),
            'validation': validation_result
        }


def lambda_handler(event, context):
    """Lambda handler for EventBridge S3 notifications."""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        processor = FormTemplateProcessor()
        
        # Handle EventBridge S3 event
        if 'detail' in event:
            bucket = event['detail']['bucket']['name']
            key = event['detail']['object']['key']
        # Handle direct S3 event
        elif 'Records' in event:
            bucket = event['Records'][0]['s3']['bucket']['name']
            key = event['Records'][0]['s3']['object']['key']
        else:
            raise ValueError("Unknown event format")
        
        # Only process PDF files in tax_forms directory
        if not key.endswith('.pdf') or not key.startswith('tax_forms/'):
            logger.info(f"Skipping non-tax-form file: {key}")
            return {'statusCode': 200, 'body': 'Skipped'}
        
        result = processor.process_form_template(bucket, key)
        
        logger.info(f"Successfully processed {result['form_type']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Error processing form template: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


# For local testing
if __name__ == "__main__":
    # Load environment for local testing
    from dotenv import load_dotenv
    load_dotenv('.env.local')
    
    # Test locally
    bucket_name = os.getenv('TEMPLATES_BUCKET_NAME')
    if not bucket_name:
        raise ValueError("TEMPLATES_BUCKET_NAME not set in .env.local")
    
    test_event = {
        'detail': {
            'bucket': {'name': bucket_name},
            'object': {'key': 'tax_forms/2024/f1040.pdf'}
        }
    }
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))

