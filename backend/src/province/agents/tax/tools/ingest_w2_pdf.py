"""W-2 PDF ingestion tool using AWS Textract."""

import json
import logging
from typing import Dict, Any, List
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

from province.core.config import get_settings
from ..models import W2Form, W2Extract

logger = logging.getLogger(__name__)


async def ingest_w2_pdf(s3_key: str, taxpayer_name: str, tax_year: int) -> Dict[str, Any]:
    """
    Extract W-2 data from PDF using AWS Textract.
    
    Args:
        s3_key: S3 key of the W-2 PDF document
        taxpayer_name: Name of the taxpayer for validation
        tax_year: Tax year for the W-2
    
    Returns:
        Dict with extracted W-2 data and validation results
    """
    
    settings = get_settings()
    
    try:
        # Initialize AWS clients
        textract_client = boto3.client('textract', region_name=settings.aws_region)
        s3_client = boto3.client('s3', region_name=settings.aws_region)
        
        bucket_name = "province-documents-storage"
        
        # Start Textract analysis
        response = textract_client.analyze_document(
            Document={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': s3_key
                }
            },
            FeatureTypes=['FORMS', 'TABLES']
        )
        
        # Extract W-2 data from Textract response
        w2_data = _extract_w2_from_textract(response, s3_key)
        
        # Validate extracted data
        validation_results = _validate_w2_data(w2_data, taxpayer_name, tax_year)
        
        # Create W-2 extract object
        w2_forms = []
        for form_data in w2_data:
            w2_form = W2Form(
                employer=form_data.get('employer', {}),
                employee=form_data.get('employee', {}),
                boxes=form_data.get('boxes', {}),
                pin_cites=form_data.get('pin_cites', {})
            )
            w2_forms.append(w2_form)
        
        # Calculate totals
        total_wages = sum(Decimal(str(form.boxes.get('1', 0))) for form in w2_forms)
        total_withholding = sum(Decimal(str(form.boxes.get('2', 0))) for form in w2_forms)
        
        w2_extract = W2Extract(
            year=tax_year,
            forms=w2_forms,
            total_wages=total_wages,
            total_withholding=total_withholding
        )
        
        logger.info(f"Successfully extracted W-2 data from {s3_key}")
        
        return {
            'success': True,
            'w2_extract': w2_extract.dict(),
            'validation_results': validation_results,
            'forms_count': len(w2_forms),
            'total_wages': float(total_wages),
            'total_withholding': float(total_withholding)
        }
        
    except ClientError as e:
        logger.error(f"AWS error processing W-2: {e}")
        return {
            'success': False,
            'error': f"AWS error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error processing W-2: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def _extract_w2_from_textract(textract_response: Dict[str, Any], s3_key: str) -> List[Dict[str, Any]]:
    """Extract W-2 data from Textract response."""
    
    blocks = textract_response.get('Blocks', [])
    
    # Create mappings for easier access
    key_map = {}
    value_map = {}
    block_map = {}
    
    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        
        if block['BlockType'] == 'KEY_VALUE_SET':
            if 'KEY' in block.get('EntityTypes', []):
                key_map[block_id] = block
            else:
                value_map[block_id] = block
    
    # Extract key-value pairs
    kvs = _get_kv_map(key_map, value_map, block_map)
    
    # Map to W-2 structure
    w2_data = []
    
    # For now, assume single W-2 per document
    # In production, you'd need more sophisticated logic to handle multiple W-2s
    
    employer_info = {
        'name': _find_value(kvs, ['employer name', 'company name', 'employer']),
        'EIN': _find_value(kvs, ['employer identification number', 'ein', 'federal ein']),
        'address': _find_value(kvs, ['employer address', 'company address'])
    }
    
    employee_info = {
        'name': _find_value(kvs, ['employee name', 'employee', 'name']),
        'SSN': _find_value(kvs, ['social security number', 'ssn', 'employee ssn']),
        'address': _find_value(kvs, ['employee address', 'address'])
    }
    
    # Extract W-2 boxes
    boxes = {}
    pin_cites = {}
    
    # Common W-2 box mappings
    box_mappings = {
        '1': ['wages tips other compensation', 'box 1', '1 wages', 'wages'],
        '2': ['federal income tax withheld', 'box 2', '2 federal', 'federal tax'],
        '3': ['social security wages', 'box 3', '3 social security', 'ss wages'],
        '4': ['social security tax withheld', 'box 4', '4 social security tax', 'ss tax'],
        '5': ['medicare wages and tips', 'box 5', '5 medicare', 'medicare wages'],
        '6': ['medicare tax withheld', 'box 6', '6 medicare tax', 'medicare tax'],
        '7': ['social security tips', 'box 7', '7 ss tips'],
        '8': ['allocated tips', 'box 8', '8 allocated tips'],
        '9': ['verification code', 'box 9', '9 verification'],
        '10': ['dependent care benefits', 'box 10', '10 dependent care'],
        '11': ['nonqualified plans', 'box 11', '11 nonqualified'],
        '12': ['box 12', '12 codes', 'codes'],
        '13': ['statutory employee', 'retirement plan', 'third party sick pay'],
        '14': ['other', 'box 14', '14 other'],
        '15': ['state', 'box 15', '15 state'],
        '16': ['state wages', 'box 16', '16 state wages'],
        '17': ['state income tax', 'box 17', '17 state tax'],
        '18': ['local wages', 'box 18', '18 local wages'],
        '19': ['local income tax', 'box 19', '19 local tax'],
        '20': ['locality name', 'box 20', '20 locality']
    }
    
    for box_num, search_terms in box_mappings.items():
        value = _find_value(kvs, search_terms)
        if value:
            # Try to convert to decimal for monetary amounts
            if box_num in ['1', '2', '3', '4', '5', '6', '7', '8', '10', '11', '16', '17', '18', '19']:
                try:
                    # Clean the value (remove $ and commas)
                    clean_value = value.replace('$', '').replace(',', '').strip()
                    boxes[box_num] = float(clean_value)
                except ValueError:
                    boxes[box_num] = value
            else:
                boxes[box_num] = value
            
            # Create pin-cite (simplified - would need actual bounding box from Textract)
            pin_cites[box_num] = {
                'file': s3_key.split('/')[-1],
                'page': 1,
                'bbox': [0, 0, 0, 0],  # Would extract actual coordinates from Textract
                'confidence': 0.9  # Would use actual confidence from Textract
            }
    
    w2_data.append({
        'employer': employer_info,
        'employee': employee_info,
        'boxes': boxes,
        'pin_cites': pin_cites
    })
    
    return w2_data


def _get_kv_map(key_map: Dict, value_map: Dict, block_map: Dict) -> Dict[str, str]:
    """Create key-value mapping from Textract blocks."""
    
    kvs = {}
    
    for block_id, key_block in key_map.items():
        value_block = _find_value_block(key_block, value_map)
        if value_block:
            key = _get_text(key_block, block_map)
            val = _get_text(value_block, block_map)
            kvs[key.lower()] = val
    
    return kvs


def _find_value_block(key_block: Dict, value_map: Dict) -> Dict:
    """Find the value block associated with a key block."""
    
    for relationship in key_block.get('Relationships', []):
        if relationship['Type'] == 'VALUE':
            for value_id in relationship['Ids']:
                if value_id in value_map:
                    return value_map[value_id]
    return None


def _get_text(result: Dict, blocks_map: Dict) -> str:
    """Extract text from a Textract block."""
    
    text = ''
    if 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'WORD':
                        text += word['Text'] + ' '
    return text.strip()


def _find_value(kvs: Dict[str, str], search_terms: List[str]) -> str:
    """Find a value in the key-value pairs using search terms."""
    
    for term in search_terms:
        if term in kvs:
            return kvs[term]
    
    # Try partial matches
    for key, value in kvs.items():
        for term in search_terms:
            if term in key:
                return value
    
    return None


def _validate_w2_data(w2_data: List[Dict[str, Any]], taxpayer_name: str, tax_year: int) -> Dict[str, Any]:
    """Validate extracted W-2 data."""
    
    validation_results = {
        'is_valid': True,
        'warnings': [],
        'errors': []
    }
    
    for i, form in enumerate(w2_data):
        form_prefix = f"Form {i+1}: "
        
        # Check required fields
        if not form.get('employer', {}).get('name'):
            validation_results['errors'].append(f"{form_prefix}Employer name is missing")
            validation_results['is_valid'] = False
        
        if not form.get('employee', {}).get('name'):
            validation_results['errors'].append(f"{form_prefix}Employee name is missing")
            validation_results['is_valid'] = False
        
        # Validate employee name matches taxpayer
        employee_name = form.get('employee', {}).get('name', '').lower()
        if employee_name and taxpayer_name.lower() not in employee_name:
            validation_results['warnings'].append(f"{form_prefix}Employee name may not match taxpayer")
        
        # Validate monetary amounts
        boxes = form.get('boxes', {})
        try:
            box1 = float(boxes.get('1', 0))
            box2 = float(boxes.get('2', 0))
            box3 = float(boxes.get('3', 0))
            
            # Basic validation: Box 1 should generally equal Box 3
            if box1 > 0 and box3 > 0:
                diff_percentage = abs(box1 - box3) / box1 * 100
                if diff_percentage > 20:
                    validation_results['warnings'].append(
                        f"{form_prefix}Significant difference between Box 1 (${box1:,.2f}) and Box 3 (${box3:,.2f})"
                    )
            
            # Check withholding rate
            if box1 > 0 and box2 > 0:
                withholding_rate = (box2 / box1) * 100
                if withholding_rate > 50:
                    validation_results['warnings'].append(
                        f"{form_prefix}High withholding rate: {withholding_rate:.1f}%"
                    )
        
        except (ValueError, TypeError, ZeroDivisionError):
            validation_results['warnings'].append(f"{form_prefix}Could not validate monetary amounts")
    
    return validation_results
