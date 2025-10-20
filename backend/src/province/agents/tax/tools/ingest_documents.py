"""Multi-document ingestion tool using AWS Bedrock Data Automation (supports PDF and JPEG).
Handles W-2, 1099-INT, 1099-MISC, and other tax documents."""

import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, Any, List
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

from province.core.config import get_settings
from ..models import W2Form, W2Extract

logger = logging.getLogger(__name__)


async def ingest_documents(s3_key: str, taxpayer_name: str, tax_year: int, document_type: str = None) -> Dict[str, Any]:
    """
    Extract tax document data using AWS Bedrock Data Automation (supports PDF and JPEG).
    Supports W-2, 1099-INT, 1099-MISC, and other tax documents.
    
    Args:
        s3_key: S3 key of the tax document (PDF or JPEG)
        taxpayer_name: Name of the taxpayer for validation
        tax_year: Tax year for the document
        document_type: Type of document ('W-2', '1099-INT', '1099-MISC', or None for auto-detection)
    
    Returns:
        Dict with extracted tax document data and validation results
    """
    
    settings = get_settings()
    
    try:
        # Load environment variables from .env.local if not already loaded
        from dotenv import load_dotenv
        load_dotenv('.env.local')
        
        # Initialize AWS clients using Data Automation credentials
        data_automation_access_key = os.getenv('DATA_AUTOMATION_AWS_ACCESS_KEY_ID')
        data_automation_secret_key = os.getenv('DATA_AUTOMATION_AWS_SECRET_ACCESS_KEY')
        
        # Fall back to general AWS credentials if Data Automation specific ones aren't available
        if not data_automation_access_key:
            data_automation_access_key = os.getenv('AWS_ACCESS_KEY_ID')
            data_automation_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        runtime_client = boto3.client(
            'bedrock-data-automation-runtime', 
            region_name=settings.aws_region,
            aws_access_key_id=data_automation_access_key,
            aws_secret_access_key=data_automation_secret_key
        )
        s3_client = boto3.client(
            's3', 
            region_name=settings.aws_region,
            aws_access_key_id=data_automation_access_key,
            aws_secret_access_key=data_automation_secret_key
        )
        
        # Use Bedrock Data Automation configuration from environment
        project_arn = os.getenv('BEDROCK_DATA_AUTOMATION_PROJECT_ARN')
        profile_arn = os.getenv('BEDROCK_DATA_AUTOMATION_PROFILE_ARN')
        input_bucket = settings.documents_bucket_name or os.getenv('DOCUMENTS_BUCKET_NAME', "province-documents-[REDACTED-ACCOUNT-ID]-us-east-1")
        output_bucket = os.getenv('BEDROCK_OUTPUT_BUCKET_NAME')
        aws_account_id = os.getenv('AWS_ACCOUNT_ID', '[REDACTED-ACCOUNT-ID]')
        
        logger.info(f"Bedrock config check - Project ARN: {'***' + project_arn[-10:] if project_arn else 'NOT_FOUND'}")
        logger.info(f"Bedrock config check - Profile ARN: {'***' + profile_arn[-10:] if profile_arn else 'NOT_FOUND'}")
        logger.info(f"Bedrock config check - Output Bucket: {output_bucket or 'NOT_FOUND'}")
        
        if not project_arn or not profile_arn or not output_bucket:
            logger.error(f"Missing Bedrock Data Automation configuration:")
            logger.error(f"  Project ARN: {project_arn or 'MISSING'}")
            logger.error(f"  Profile ARN: {profile_arn or 'MISSING'}")
            logger.error(f"  Output Bucket: {output_bucket or 'MISSING'}")
            
            return {
                'success': False,
                'error': 'Bedrock Data Automation configuration is incomplete. Cannot process document without proper configuration.'
            }
        
        # Detect file type from extension
        file_extension = s3_key.lower().split('.')[-1]
        supported_formats = ['pdf', 'jpg', 'jpeg', 'png']
        
        if file_extension not in supported_formats:
            return {
                'success': False,
                'error': f"Unsupported file format: {file_extension}. Supported formats: {', '.join(supported_formats)}"
            }
        
        # Auto-detect document type if not provided
        if not document_type:
            document_type = _detect_document_type(s3_key)
        
        logger.info(f"Processing {document_type} document with Bedrock Data Automation: {s3_key} (format: {file_extension})")
        
        # Get appropriate blueprint/profile for document type
        blueprint_profile = _get_blueprint_profile(document_type, profile_arn)
        
        # Bedrock Data Automation will create its own UUID-based output structure
        # We don't need to specify a custom output key - it uses inference_results/{uuid}/
        
        # First, check if we already have results for this file in the output bucket
        existing_result = _check_existing_bedrock_results(s3_client, output_bucket, s3_key)
        if existing_result:
            logger.info(f"Found existing Bedrock results for {s3_key}")
            tax_data = _extract_tax_data_from_bedrock(existing_result, s3_key, document_type)
        else:
            logger.info(f"No existing results found, attempting to process {s3_key} with Bedrock Data Automation")
            
            # Try to process with real Bedrock Data Automation
            try:
                bedrock_response = None
                try:
                    logger.info(f"🚀 Starting Bedrock Data Automation processing...")
                    logger.info(f"   Input: s3://{input_bucket}/{s3_key}")
                    logger.info(f"   Profile: {blueprint_profile}")
                    
                    response = runtime_client.invoke_data_automation_async(
                        inputConfiguration={
                            's3Uri': f"s3://{input_bucket}/{s3_key}"
                        },
                        outputConfiguration={
                            's3Uri': f"s3://{output_bucket}/inference_results"
                        },
                        dataAutomationConfiguration={
                            'dataAutomationProjectArn': project_arn,
                            'stage': 'LIVE'
                        },
                        dataAutomationProfileArn=blueprint_profile
                    )
                    
                    invocation_arn = response['invocationArn']
                    job_uuid = invocation_arn.split('/')[-1]
                    logger.info(f"✅ Bedrock job started: {invocation_arn}")
                    logger.info(f"   Job UUID: {job_uuid}")
                    
                    # Wait for completion with extended timeout and better feedback
                    max_wait_time = 180  # 3 minutes (increased from 2)
                    start_time = time.time()
                    check_count = 0
                    
                    logger.info(f"⏳ Waiting for Bedrock processing (max {max_wait_time}s)...")
                    
                    while time.time() - start_time < max_wait_time:
                        check_count += 1
                        elapsed = int(time.time() - start_time)
                        
                        try:
                            status_response = runtime_client.get_data_automation_status(invocationArn=invocation_arn)
                            status = status_response.get('status')
                            
                            logger.info(f"   [{elapsed}s] Check #{check_count}: Status = {status}")
                            
                            if status in ['COMPLETED', 'Success']:
                                logger.info(f"✅ Bedrock processing completed in {elapsed}s")
                                
                                # Try multiple result paths
                                possible_keys = [
                                    f"inference_results/{job_uuid}/0/standard_output/0/result.json",
                                    f"inference_results//{job_uuid}/0/standard_output/0/result.json",
                                    f"inference_results/{job_uuid}/0/custom_output/0/result.json"
                                ]
                                
                                bedrock_response = None
                                for result_key in possible_keys:
                                    try:
                                        logger.info(f"   Trying to load: {result_key}")
                                        result_response = s3_client.get_object(
                                            Bucket=output_bucket,
                                            Key=result_key
                                        )
                                        bedrock_response = json.loads(result_response['Body'].read().decode('utf-8'))
                                        logger.info(f"✅ Successfully loaded results from: {result_key}")
                                        break
                                    except Exception as e:
                                        logger.debug(f"   Not found at {result_key}: {e}")
                                        continue
                                
                                if bedrock_response:
                                    break
                                else:
                                    logger.error(f"❌ Results not found in any expected location for job {job_uuid}")
                                    logger.error(f"   Tried: {possible_keys}")
                                    break
                                    
                            elif status in ['FAILED', 'CANCELLED', 'Failed', 'Canceled']:
                                logger.error(f"❌ Bedrock processing failed with status: {status}")
                                error_details = status_response.get('errorMessage', 'No error details provided')
                                logger.error(f"   Error: {error_details}")
                                break
                            elif status in ['IN_PROGRESS', 'InProgress', 'RUNNING', 'Running']:
                                # Still processing, continue waiting
                                pass
                            else:
                                logger.warning(f"⚠️  Unknown status: {status}")
                            
                        except Exception as status_error:
                            logger.warning(f"Error checking status: {status_error}")
                        
                        time.sleep(5)  # Wait 5 seconds before checking again
                    
                    # Check if we timed out
                    if not bedrock_response:
                        elapsed = int(time.time() - start_time)
                        if elapsed >= max_wait_time:
                            logger.error(f"⏱️  Timeout: Bedrock processing took longer than {max_wait_time}s")
                        
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                    error_message = e.response.get('Error', {}).get('Message', str(e))
                    logger.error(f"❌ Bedrock invocation failed:")
                    logger.error(f"   Error Code: {error_code}")
                    logger.error(f"   Message: {error_message}")
                    bedrock_response = None
                
                if bedrock_response:
                    # Extract tax document data from Bedrock response
                    tax_data = _extract_tax_data_from_bedrock(bedrock_response, s3_key, document_type)
                    logger.info(f"Successfully processed {document_type} with Bedrock Data Automation")
                else:
                    # If Bedrock processing failed, return error
                    logger.error("Bedrock Data Automation processing failed - no results obtained")
                    return {
                        'success': False,
                        'error': 'Bedrock Data Automation processing failed. Please try again or contact support.'
                    }
                    
            except Exception as bedrock_error:
                logger.error(f"Bedrock Data Automation failed: {bedrock_error}")
                return {
                    'success': False,
                    'error': f'Bedrock Data Automation error: {str(bedrock_error)}'
                }
        
        # Validate extracted data
        validation_results = _validate_tax_data(tax_data, taxpayer_name, tax_year, document_type)
        
        # Create appropriate extract object based on document type
        if document_type == 'W-2':
            # Create W-2 extract object
            w2_forms = []
            for form_data in tax_data:
                w2_form = W2Form(
                    employer=form_data.get('employer', {}),
                    employee=form_data.get('employee', {}),
                    boxes=form_data.get('boxes', {}),
                    pin_cites=form_data.get('pin_cites', {})
                )
                w2_forms.append(w2_form)
            
            # Calculate totals for W-2
            total_wages = sum(Decimal(str(form.boxes.get('1', 0))) for form in w2_forms)
            total_withholding = sum(Decimal(str(form.boxes.get('2', 0))) for form in w2_forms)
            
            extract_object = W2Extract(
                year=tax_year,
                forms=w2_forms,
                total_wages=total_wages,
                total_withholding=total_withholding
            )
        else:
            # For 1099 forms and others, create a generic extract object
            extract_object = {
                'document_type': document_type,
                'year': tax_year,
                'forms': tax_data,
                'validation_results': validation_results,
                'total_income': sum(Decimal(str(form.get('boxes', {}).get('1', 0))) for form in tax_data),
                'total_withholding': sum(Decimal(str(form.get('boxes', {}).get('4', 0))) for form in tax_data)
            }
        
        logger.info(f"Successfully extracted {document_type} data from {s3_key} ({file_extension} format) using Bedrock Data Automation")
        
        # Prepare return data based on document type
        if document_type == 'W-2':
            result = {
                'success': True,
                'document_type': document_type,
                'w2_extract': extract_object.dict(),
                'validation_results': validation_results,
                'forms_count': len(w2_forms),
                'total_wages': float(total_wages),
                'total_withholding': float(total_withholding),
                'processing_method': 'bedrock_data_automation'
            }
            
            # Save W-2 extract data for calc_1040 to use
            await _save_w2_extract_for_calc(s3_key, result, taxpayer_name)
            
            return result
        else:
            return {
                'success': True,
                'document_type': document_type,
                'extract_object': extract_object,
                'validation_results': validation_results,
                'forms_count': len(tax_data),
                'total_income': float(extract_object['total_income']),
                'total_withholding': float(extract_object['total_withholding']),
                'processing_method': 'bedrock_data_automation'
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



def _extract_w2_from_standard_output(bedrock_response: Dict[str, Any], s3_key: str) -> List[Dict[str, Any]]:
    """Extract W-2 data from Bedrock Data Automation standard output format (pages with markdown)."""
    
    logger.info(f"Extracting W-2 data from Bedrock Data Automation standard output")
    
    w2_data = []
    
    # Extract markdown content from the first page
    page = bedrock_response['pages'][0]
    if 'representation' not in page or 'markdown' not in page['representation']:
        logger.warning("No markdown representation found in standard output")
        return []
    
    markdown_content = page['representation']['markdown']
    logger.info(f"Processing markdown content: {len(markdown_content)} characters")
    
    # Initialize data structures
    employer_info = {}
    employee_info = {}
    boxes = {}
    pin_cites = {}
    
    # Extract employer information using patterns based on actual markdown structure
    # EIN pattern - looking for "b Employer identification number" followed by the number
    ein_match = re.search(r'\*\*b\*\*\s+Employer\s+identification\s+number.*?\n\s*\*\*([0-9]{2}-[0-9]{7})\*\*', markdown_content, re.IGNORECASE | re.DOTALL)
    if ein_match:
        employer_info['EIN'] = ein_match.group(1)
        pin_cites['EIN'] = {'file': s3_key.split('/')[-1], 'page': 1, 'bbox': [0, 0, 0, 0], 'confidence': 0.9, 'source': 'bedrock_standard_output'}
    
    # Employer name pattern - looking for "C Employer's name, address, and ZIP code" followed by the name
    employer_name_match = re.search(r'\*\*C\*\*\s+Employer\'s\s+name,\s+address,\s+and\s+ZIP\s+code.*?\n\s*\*\*([^*\n]+)\*\*', markdown_content, re.IGNORECASE | re.DOTALL)
    if employer_name_match:
        employer_info['name'] = employer_name_match.group(1).strip()
        pin_cites['employer_name'] = {'file': s3_key.split('/')[-1], 'page': 1, 'bbox': [0, 0, 0, 0], 'confidence': 0.9, 'source': 'bedrock_standard_output'}
    
    # Extract employee information
    # SSN pattern - looking for "a Employee's social security number" followed by the number
    ssn_match = re.search(r'\*\*a\s+Employee\'s\s+social\s+security\s+number\*\*.*?\n.*?\*\*([0-9]{3}-[0-9]{2}-[0-9]{4})\*\*', markdown_content, re.IGNORECASE | re.DOTALL)
    if ssn_match:
        employee_info['SSN'] = ssn_match.group(1)
        pin_cites['SSN'] = {'file': s3_key.split('/')[-1], 'page': 1, 'bbox': [0, 0, 0, 0], 'confidence': 0.9, 'source': 'bedrock_standard_output'}
    
    # Employee name pattern - looking for "e Employee's first name and initial" followed by names
    employee_name_match = re.search(r'\*\*e\*\*\s+Employee\'s\s+first\s+name\s+and\s+initial.*?\n.*?\*\*([A-Za-z]+)\*\*.*?\n\*\*([A-Za-z]+)\*\*', markdown_content, re.IGNORECASE | re.DOTALL)
    if employee_name_match:
        first_name = employee_name_match.group(1).strip()
        last_name = employee_name_match.group(2).strip()
        employee_info['name'] = f"{first_name} {last_name}"
        pin_cites['employee_name'] = {'file': s3_key.split('/')[-1], 'page': 1, 'bbox': [0, 0, 0, 0], 'confidence': 0.9, 'source': 'bedrock_standard_output'}
    
    # Employee address pattern - looking for address after employee name
    # Format varies: **First Last**\n... or **First**\n**Last**\n...
    # Flexible pattern to handle both cases
    # Example 1: **Taylor Cox**\n613 Roger Crest Apt. 802\nLeeton IA\n**26442-8249**
    # Example 2: **April**\n**Hensley**\n\n**31403 David Circles**\n\nWest Erinfort WY\n**45881-3334**
    address_match = re.search(
        r'\*\*[A-Za-z]+\*\*(?:\s*\n\s*\*\*[A-Za-z]+\*\*)?\s*\n+\s*\*\*([^\*\n]+)\*\*\s*\n+\s*([A-Za-z\s]+\s+[A-Z]{2})\s*\n\s*\*\*([0-9]{5}(?:-[0-9]{4})?)\*\*',
        markdown_content,
        re.MULTILINE
    )
    if address_match:
        street = address_match.group(1).strip()
        city_state = address_match.group(2).strip()
        zip_code = address_match.group(3).strip()
        
        # Parse city and state
        city_state_parts = city_state.rsplit(' ', 1)  # Split from right to get last 2-letter state
        if len(city_state_parts) == 2:
            city = city_state_parts[0].strip()
            state = city_state_parts[1].strip()
            employee_info['address'] = f"{street}, {city}, {state} {zip_code}"
            employee_info['street'] = street
            employee_info['city'] = city
            employee_info['state'] = state
            employee_info['zip'] = zip_code
            pin_cites['employee_address'] = {'file': s3_key.split('/')[-1], 'page': 1, 'bbox': [0, 0, 0, 0], 'confidence': 0.85, 'source': 'bedrock_standard_output'}
            logger.info(f"Extracted employee address: {employee_info['address']}")
    
    # Extract W-2 box values using patterns based on the actual markdown structure
    # Looking at the sample, the format is like: "1 Wages, tips, other compensation\t\t\t2 Federal income tax withheld\t\n55151.93\t\t\t16606.17\t"
    
    # Box 1: Wages, tips, other compensation
    box1_match = re.search(r'1\s+Wages,\s+tips,\s+other\s+compensation.*?\n([0-9,]+\.?[0-9]*)', markdown_content, re.IGNORECASE | re.DOTALL)
    if box1_match and box1_match.group(1).strip():
        try:
            boxes['1'] = float(box1_match.group(1).replace(',', ''))
            pin_cites['1'] = {'file': s3_key.split('/')[-1], 'page': 1, 'bbox': [0, 0, 0, 0], 'confidence': 0.9, 'source': 'bedrock_standard_output'}
        except ValueError:
            logger.warning(f"Could not parse Box 1 value: {box1_match.group(1)}")
    
    # Box 2: Federal income tax withheld
    box2_match = re.search(r'2\s+Federal\s+income\s+tax\s+withheld.*?\n[0-9,]+\.?[0-9]*\t+([0-9,]+\.?[0-9]*)', markdown_content, re.IGNORECASE | re.DOTALL)
    if box2_match and box2_match.group(1).strip():
        try:
            boxes['2'] = float(box2_match.group(1).replace(',', ''))
            pin_cites['2'] = {'file': s3_key.split('/')[-1], 'page': 1, 'bbox': [0, 0, 0, 0], 'confidence': 0.9, 'source': 'bedrock_standard_output'}
        except ValueError:
            logger.warning(f"Could not parse Box 2 value: {box2_match.group(1)}")
    
    # Box 3: Social security wages
    box3_match = re.search(r'3\s+Social\s+security\s+wages.*?\n([0-9,]+\.?[0-9]*)', markdown_content, re.IGNORECASE | re.DOTALL)
    if box3_match and box3_match.group(1).strip():
        try:
            boxes['3'] = float(box3_match.group(1).replace(',', ''))
            pin_cites['3'] = {'file': s3_key.split('/')[-1], 'page': 1, 'bbox': [0, 0, 0, 0], 'confidence': 0.9, 'source': 'bedrock_standard_output'}
        except ValueError:
            logger.warning(f"Could not parse Box 3 value: {box3_match.group(1)}")
    
    # Box 4: Social security tax withheld
    box4_match = re.search(r'4\s+Social\s+security\s+tax\s+withheld.*?\n[0-9,]+\.?[0-9]*\t+([0-9,]+\.?[0-9]*)', markdown_content, re.IGNORECASE | re.DOTALL)
    if box4_match and box4_match.group(1).strip():
        try:
            boxes['4'] = float(box4_match.group(1).replace(',', ''))
            pin_cites['4'] = {'file': s3_key.split('/')[-1], 'page': 1, 'bbox': [0, 0, 0, 0], 'confidence': 0.9, 'source': 'bedrock_standard_output'}
        except ValueError:
            logger.warning(f"Could not parse Box 4 value: {box4_match.group(1)}")
    
    # Box 5: Medicare wages and tips
    box5_match = re.search(r'5\s+Medicare\s+wages\s+and\s+tips.*?\n([0-9,]+\.?[0-9]*)', markdown_content, re.IGNORECASE | re.DOTALL)
    if box5_match and box5_match.group(1).strip():
        try:
            boxes['5'] = float(box5_match.group(1).replace(',', ''))
            pin_cites['5'] = {'file': s3_key.split('/')[-1], 'page': 1, 'bbox': [0, 0, 0, 0], 'confidence': 0.9, 'source': 'bedrock_standard_output'}
        except ValueError:
            logger.warning(f"Could not parse Box 5 value: {box5_match.group(1)}")
    
    # Box 6: Medicare tax withheld
    box6_match = re.search(r'6\s+Medicare\s+tax\s+withheld.*?\n[0-9,]+\.?[0-9]*\t+([0-9,]+\.?[0-9]*)', markdown_content, re.IGNORECASE | re.DOTALL)
    if box6_match and box6_match.group(1).strip():
        try:
            boxes['6'] = float(box6_match.group(1).replace(',', ''))
            pin_cites['6'] = {'file': s3_key.split('/')[-1], 'page': 1, 'bbox': [0, 0, 0, 0], 'confidence': 0.9, 'source': 'bedrock_standard_output'}
        except ValueError:
            logger.warning(f"Could not parse Box 6 value: {box6_match.group(1)}")
    
    # For state information, look in the table format
    # State information is in a table format: | DC | 786-41-049 | 28287.2 | 1608.75 | 44590.6 | 6842.08 | Rocha Wells |
    state_table_match = re.search(r'\|\s*([A-Z]{2})\s*\|\s*[0-9-]+\s*\|\s*([0-9,]+\.?[0-9]*)\s*\|\s*([0-9,]+\.?[0-9]*)\s*\|\s*([0-9,]+\.?[0-9]*)\s*\|\s*([0-9,]+\.?[0-9]*)\s*\|\s*([^|]+)\s*\|', markdown_content)
    if state_table_match:
        try:
            # Box 15: State
            boxes['15'] = state_table_match.group(1).strip()
            pin_cites['15'] = {'file': s3_key.split('/')[-1], 'page': 1, 'bbox': [0, 0, 0, 0], 'confidence': 0.9, 'source': 'bedrock_standard_output'}
            
            # Box 16: State wages
            if state_table_match.group(2).strip():
                boxes['16'] = float(state_table_match.group(2).replace(',', ''))
                pin_cites['16'] = {'file': s3_key.split('/')[-1], 'page': 1, 'bbox': [0, 0, 0, 0], 'confidence': 0.9, 'source': 'bedrock_standard_output'}
            
            # Box 17: State income tax
            if state_table_match.group(3).strip():
                boxes['17'] = float(state_table_match.group(3).replace(',', ''))
                pin_cites['17'] = {'file': s3_key.split('/')[-1], 'page': 1, 'bbox': [0, 0, 0, 0], 'confidence': 0.9, 'source': 'bedrock_standard_output'}
                
            # Box 20: Locality name
            if state_table_match.group(6).strip():
                boxes['20'] = state_table_match.group(6).strip()
                pin_cites['20'] = {'file': s3_key.split('/')[-1], 'page': 1, 'bbox': [0, 0, 0, 0], 'confidence': 0.9, 'source': 'bedrock_standard_output'}
        except ValueError as e:
            logger.warning(f"Could not parse state table values: {e}")
    
    # Create the W-2 form data
    w2_data.append({
        'employer': employer_info,
        'employee': employee_info,
        'boxes': boxes,
        'pin_cites': pin_cites
    })
    
    logger.info(f"Extracted W-2 data from standard output: {len(boxes)} boxes found")
    return w2_data


def _extract_w2_from_bedrock(bedrock_response: Dict[str, Any], s3_key: str) -> List[Dict[str, Any]]:
    """Extract W-2 data from Bedrock Data Automation standard output response."""
    
    # Check if this is standard output format (pages with markdown)
    if 'pages' in bedrock_response and len(bedrock_response['pages']) > 0:
        return _extract_w2_from_standard_output(bedrock_response, s3_key)
    
    # Fallback: Extract data from custom output format (legacy)
    inference_result = bedrock_response.get('inference_result', {})
    
    if not inference_result:
        logger.warning("No inference_result or pages found in Bedrock response")
        return []
    
    logger.info(f"Extracting W-2 data from Bedrock Data Automation custom output (legacy)")
    
    # Extract structured data from Bedrock inference result
    w2_data = []
    
    # Extract employer information from structured result
    employer_info = {}
    employer_data = inference_result.get('employer_info', {})
    
    if 'ein' in employer_data:
        employer_info['EIN'] = employer_data['ein']
    if 'employer_name' in employer_data:
        employer_info['name'] = employer_data['employer_name']
    if 'employer_address' in employer_data:
        employer_info['address'] = employer_data['employer_address']
    
    # Extract employee information from structured result (correct field names)
    employee_info = {}
    employee_data = inference_result.get('employee_general_info', {})
    
    if 'ssn' in employee_data:
        employee_info['SSN'] = employee_data['ssn']
    # Combine first name and last name
    first_name = employee_data.get('first_name', '')
    last_name = employee_data.get('employee_last_name', '')
    if first_name or last_name:
        employee_info['name'] = f"{first_name} {last_name}".strip()
    if 'employee_address' in employee_data:
        employee_info['address'] = employee_data['employee_address']
    
    # Extract W-2 boxes from structured result
    boxes = {}
    pin_cites = {}
    
    # Map Bedrock fields to W-2 box numbers
    federal_wage_info = inference_result.get('federal_wage_info', {})
    federal_tax_info = inference_result.get('federal_tax_info', {})
    
    # Box 1: Wages, tips, other compensation
    if 'wages_tips_other_compensation' in federal_wage_info:
        boxes['1'] = float(federal_wage_info['wages_tips_other_compensation'])
    
    # Box 2: Federal income tax withheld
    if 'federal_income_tax' in federal_tax_info:
        boxes['2'] = float(federal_tax_info['federal_income_tax'])
    
    # Box 3: Social security wages
    if 'social_security_wages' in federal_wage_info:
        boxes['3'] = float(federal_wage_info['social_security_wages'])
    
    # Box 4: Social security tax withheld
    if 'social_security_tax' in federal_tax_info:
        boxes['4'] = float(federal_tax_info['social_security_tax'])
    
    # Box 5: Medicare wages and tips
    if 'medicare_wages_tips' in federal_wage_info:
        boxes['5'] = float(federal_wage_info['medicare_wages_tips'])
    
    # Box 6: Medicare tax withheld
    if 'medicare_tax' in federal_tax_info:
        boxes['6'] = float(federal_tax_info['medicare_tax'])
    
    # Box 7: Social security tips
    if 'social_security_tips' in federal_wage_info:
        boxes['7'] = float(federal_wage_info['social_security_tips'])
    
    # Box 8: Allocated tips
    if 'allocated_tips' in federal_tax_info:
        boxes['8'] = float(federal_tax_info['allocated_tips'])
    
    # Box 11: Nonqualified plans
    if 'nonqualified_plans_incom' in inference_result:
        boxes['11'] = float(inference_result['nonqualified_plans_incom'])
    
    # Box 12: Codes (12a, 12b, 12c, 12d)
    codes = inference_result.get('codes', [])
    for i, code_item in enumerate(codes[:4]):  # Up to 4 codes (a, b, c, d)
        suffix = chr(ord('a') + i)  # 'a', 'b', 'c', 'd'
        if 'amount' in code_item:
            boxes[f'12{suffix}'] = float(code_item['amount'])
    
    # State and local taxes (Box 15-20)
    state_taxes = inference_result.get('state_taxes_table', [])
    for i, state_tax in enumerate(state_taxes[:4]):  # Up to 4 state entries
        suffix = '' if i == 0 else f'_{chr(ord("a") + i - 1)}'  # '', '_a', '_b', '_c'
        
        if 'state_name' in state_tax:
            boxes[f'15{suffix}'] = state_tax['state_name']
        if 'state_wages_and_tips' in state_tax:
            boxes[f'16{suffix}'] = float(state_tax['state_wages_and_tips'])
        if 'state_income_tax' in state_tax:
            boxes[f'17{suffix}'] = float(state_tax['state_income_tax'])
        if 'local_wages_tips' in state_tax:
            boxes[f'18{suffix}'] = float(state_tax['local_wages_tips'])
        # Note: Box 19 (local tax) and Box 20 (locality name) might be in different fields
    
    # Create pin-cites for all extracted boxes
    for box_key in boxes.keys():
        pin_cites[str(box_key)] = {
            'file': s3_key.split('/')[-1],
            'page': 1,
            'bbox': [0, 0, 0, 0],  # Bedrock provides actual bounding boxes
            'confidence': 0.95,
            'source': 'bedrock_data_automation'
        }
    
    # Create the W-2 form data
    w2_data.append({
        'employer': employer_info,
        'employee': employee_info,
        'boxes': boxes,
        'pin_cites': pin_cites
    })
    
    logger.info(f"Extracted W-2 data: {len(boxes)} boxes found")
    return w2_data


def _check_existing_bedrock_results(s3_client, bucket_name: str, s3_key: str) -> Dict[str, Any]:
    """Check if Bedrock results already exist for this file."""
    try:
        # Look for existing results in the inference_results folder
        # Bedrock creates results with UUIDs in inference_results/{uuid}/0/standard_output/0/result.json
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix="inference_results/"
        )
        
        if 'Contents' not in response:
            return None
            
        # Look for results that match our input file by checking job metadata
        input_filename = s3_key.split('/')[-1]
        logger.info(f"Looking for existing results for file: {input_filename}")
        
        # First, find job metadata files
        metadata_files = [obj for obj in response['Contents'] if obj['Key'].endswith('job_metadata.json')]
        
        for metadata_obj in metadata_files:
            try:
                # Read the job metadata to check if it matches our file
                metadata_response = s3_client.get_object(
                    Bucket=bucket_name,
                    Key=metadata_obj['Key']
                )
                metadata = json.loads(metadata_response['Body'].read().decode('utf-8'))
                
                # Check if this job processed our file
                if 'output_metadata' in metadata and len(metadata['output_metadata']) > 0:
                    asset_input_path = metadata['output_metadata'][0].get('asset_input_path', {})
                    processed_s3_key = asset_input_path.get('s3_key', '')
                    
                    if s3_key in processed_s3_key or input_filename in processed_s3_key:
                        logger.info(f"Found matching job metadata: {metadata_obj['Key']}")
                        
                        # Get the job ID from the metadata file path
                        job_id = metadata_obj['Key'].split('/')[1]
                        
                        # Try to get the standard output result (proper Bedrock structure)
                        # Try both path formats (with and without double slash)
                        possible_keys = [
                            f"inference_results/{job_id}/0/standard_output/0/result.json",
                            f"inference_results//{job_id}/0/standard_output/0/result.json"
                        ]
                        
                        for result_key in possible_keys:
                            try:
                                result_response = s3_client.get_object(
                                    Bucket=bucket_name,
                                    Key=result_key
                                )
                                result_data = json.loads(result_response['Body'].read().decode('utf-8'))
                                logger.info(f"Successfully loaded existing Bedrock results from {result_key}")
                                return result_data
                            except Exception as e:
                                logger.debug(f"Could not read result file {result_key}: {e}")
                                continue
                            
            except Exception as e:
                logger.warning(f"Could not read metadata file {metadata_obj['Key']}: {e}")
                continue
        
        logger.info(f"No existing results found for {s3_key}")
        return None
        
    except Exception as e:
        logger.error(f"Error checking existing Bedrock results: {e}")
        return None


def _get_bedrock_results_from_s3(s3_client, bucket_name: str, output_key: str) -> Dict[str, Any]:
    """Retrieve Bedrock Data Automation results from S3."""
    
    try:
        # List files in the output directory
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=output_key
        )
        
        # Look for the standardOutput.json file
        for obj in response.get('Contents', []):
            key = obj['Key']
            if key.endswith('standardOutput.json'):
                # Download and parse the result
                obj_response = s3_client.get_object(Bucket=bucket_name, Key=key)
                content = obj_response['Body'].read().decode('utf-8')
                return json.loads(content)
        
        logger.warning(f"No standardOutput.json found in {output_key}")
        return None
        
    except Exception as e:
        logger.error(f"Failed to retrieve Bedrock results from S3: {e}")
        return None


# Fallback function removed - if W2 processing fails, it should fail properly




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


def _detect_document_type(s3_key: str) -> str:
    """Detect document type from S3 key or filename."""
    
    key_lower = s3_key.lower()
    
    if 'w2' in key_lower or 'w-2' in key_lower:
        return 'W-2'
    elif '1099-int' in key_lower or '1099int' in key_lower:
        return '1099-INT'
    elif '1099-misc' in key_lower or '1099misc' in key_lower:
        return '1099-MISC'
    elif '1099' in key_lower:
        return '1099-MISC'  # Default 1099 type
    else:
        return 'W-2'  # Default fallback


def _get_blueprint_profile(document_type: str, default_profile_arn: str) -> str:
    """Get the appropriate blueprint profile ARN for the document type."""
    
    # Check for custom blueprints first, then fall back to standard
    # Since we're using the standard US Data Automation profile (us.data-automation-v1),
    # it can handle W-2, 1099, and other tax documents generically
    
    profile_mapping = {
        'W-2': default_profile_arn,        # Standard profile handles W-2
        '1099-INT': default_profile_arn,   # Standard profile handles 1099-INT  
        '1099-MISC': default_profile_arn,  # Standard profile handles 1099-MISC
    }
    
    selected_profile = profile_mapping.get(document_type, default_profile_arn)
    logger.info(f"Using profile for {document_type}: {selected_profile}")
    
    return selected_profile


def _extract_tax_data_from_bedrock(bedrock_response: Dict[str, Any], s3_key: str, document_type: str) -> List[Dict[str, Any]]:
    """Extract tax document data from Bedrock response based on document type."""
    
    if document_type == 'W-2':
        # Use existing W-2 extraction logic
        return _extract_w2_from_bedrock(bedrock_response, s3_key)
    elif document_type in ['1099-INT', '1099-MISC']:
        # Extract 1099 data
        return _extract_1099_from_bedrock(bedrock_response, s3_key, document_type)
    else:
        # Fallback to W-2 extraction for unknown types
        logger.warning(f"Unknown document type {document_type}, using W-2 extraction as fallback")
        return _extract_w2_from_bedrock(bedrock_response, s3_key)


def _extract_1099_from_bedrock(bedrock_response: Dict[str, Any], s3_key: str, document_type: str) -> List[Dict[str, Any]]:
    """Extract 1099 form data from Bedrock response."""
    
    try:
        # This is a simplified implementation - adjust based on actual Bedrock response structure
        extracted_data = []
        
        # Look for standard output structure
        if 'standardOutput' in bedrock_response:
            standard_output = bedrock_response['standardOutput']
            
            # Extract payer information
            payer_info = {
                'name': standard_output.get('payer_name', ''),
                'TIN': standard_output.get('payer_tin', ''),
                'address': standard_output.get('payer_address', '')
            }
            
            # Extract recipient information
            recipient_info = {
                'name': standard_output.get('recipient_name', ''),
                'TIN': standard_output.get('recipient_tin', ''),
                'address': standard_output.get('recipient_address', '')
            }
            
            # Extract box values based on document type
            boxes = {}
            if document_type == '1099-INT':
                boxes = {
                    '1': standard_output.get('interest_income', 0),
                    '2': standard_output.get('early_withdrawal_penalty', 0),
                    '3': standard_output.get('savings_bond_interest', 0),
                    '4': standard_output.get('federal_tax_withheld', 0),
                    '5': standard_output.get('investment_expenses', 0),
                    '6': standard_output.get('foreign_tax_paid', 0),
                    '8': standard_output.get('tax_exempt_interest', 0),
                    '9': standard_output.get('private_activity_bond_interest', 0),
                    '11': standard_output.get('state_tax_withheld', 0),
                    '12': standard_output.get('state', ''),
                    '13': standard_output.get('state_id', '')
                }
            elif document_type == '1099-MISC':
                boxes = {
                    '1': standard_output.get('rents', 0),
                    '2': standard_output.get('royalties', 0),
                    '3': standard_output.get('other_income', 0),
                    '4': standard_output.get('federal_tax_withheld', 0),
                    '5': standard_output.get('fishing_boat_proceeds', 0),
                    '6': standard_output.get('medical_payments', 0),
                    '7': standard_output.get('nonemployee_compensation', 0),
                    '8': standard_output.get('substitute_payments', 0),
                    '9': standard_output.get('direct_sales', 0),
                    '10': standard_output.get('crop_insurance', 0),
                    '11': standard_output.get('state_tax_withheld', 0),
                    '12': standard_output.get('state', ''),
                    '13': standard_output.get('state_id', '')
                }
            
            # Create pin cites (simplified)
            pin_cites = {
                '1': {'file': s3_key.split('/')[-1], 'page': 1, 'bbox': [0, 0, 0, 0], 'confidence': 0.8, 'source': 'bedrock'},
                '4': {'file': s3_key.split('/')[-1], 'page': 1, 'bbox': [0, 0, 0, 0], 'confidence': 0.8, 'source': 'bedrock'}
            }
            
            extracted_data.append({
                'payer': payer_info,
                'recipient': recipient_info,
                'boxes': boxes,
                'pin_cites': pin_cites
            })
        
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error extracting {document_type} data from Bedrock response: {e}")
        return []


def _validate_tax_data(tax_data: List[Dict[str, Any]], taxpayer_name: str, tax_year: int, document_type: str) -> Dict[str, Any]:
    """Validate extracted tax document data based on document type."""
    
    if document_type == 'W-2':
        # Use existing W-2 validation
        return _validate_w2_data(tax_data, taxpayer_name, tax_year)
    elif document_type in ['1099-INT', '1099-MISC']:
        # Validate 1099 data
        return _validate_1099_data(tax_data, taxpayer_name, tax_year, document_type)
    else:
        # Fallback validation
        return {
            'is_valid': True,
            'warnings': [f'Using basic validation for document type: {document_type}'],
            'errors': []
        }


def _validate_1099_data(tax_data: List[Dict[str, Any]], taxpayer_name: str, tax_year: int, document_type: str) -> Dict[str, Any]:
    """Validate 1099 form data."""
    
    validation_results = {
        'is_valid': True,
        'warnings': [],
        'errors': []
    }
    
    if not tax_data:
        validation_results['errors'].append('No 1099 data found')
        validation_results['is_valid'] = False
        return validation_results
    
    for i, form in enumerate(tax_data):
        form_prefix = f"Form {i+1}: " if len(tax_data) > 1 else ""
        
        # Check required fields
        if not form.get('payer', {}).get('name'):
            validation_results['errors'].append(f"{form_prefix}Payer name is missing")
            validation_results['is_valid'] = False
        
        if not form.get('recipient', {}).get('name'):
            validation_results['errors'].append(f"{form_prefix}Recipient name is missing")
            validation_results['is_valid'] = False
        
        # Validate recipient name matches taxpayer
        recipient_name = form.get('recipient', {}).get('name', '').lower()
        if taxpayer_name.lower() not in recipient_name and recipient_name not in taxpayer_name.lower():
            validation_results['warnings'].append(
                f"{form_prefix}Recipient name '{recipient_name}' may not match taxpayer '{taxpayer_name}'"
            )
        
        # Check for reasonable income amounts
        try:
            boxes = form.get('boxes', {})
            primary_income = float(boxes.get('1', 0))  # Box 1 is primary income for most 1099s
            
            if primary_income < 0:
                validation_results['errors'].append(f"{form_prefix}Negative income amount: ${primary_income}")
                validation_results['is_valid'] = False
            elif primary_income > 1000000:
                validation_results['warnings'].append(f"{form_prefix}Very high income amount: ${primary_income}")
            
        except (ValueError, TypeError):
            validation_results['warnings'].append(f"{form_prefix}Could not validate income amounts")
    
    return validation_results


async def _save_w2_extract_for_calc(s3_key: str, w2_result: Dict[str, Any], taxpayer_name: str) -> None:
    """
    Save W-2 extract data in the format that calc_1040 expects.
    This bridges the gap between ingest_documents and calc_1040.
    """
    try:
        # Extract engagement_id from s3_key if it follows the pattern
        # tax-engagements/{engagement_id}/...
        parts = s3_key.split('/')
        if len(parts) >= 2 and parts[0] == 'tax-engagements':
            engagement_id = parts[1]
        else:
            logger.warning(f"Could not extract engagement_id from s3_key: {s3_key}")
            return
        
        # Get user_id from engagement
        settings = get_settings()
        dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        engagements_table = dynamodb.Table(settings.tax_engagements_table_name)
        
        # Find the engagement to get user_id
        response = engagements_table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('engagement_id').eq(engagement_id)
        )
        
        items = response.get('Items', [])
        if not items:
            logger.warning(f"Could not find engagement {engagement_id}")
            return
        
        user_id = items[0]['user_id']
        
        # Save W-2 extract data to S3 in JSON format
        s3_client = boto3.client('s3', region_name=settings.aws_region)
        extract_s3_key = f"tax-engagements/{engagement_id}/Workpapers/W2_Extracts.json"
        
        # Prepare the data in the format calc_1040 expects
        w2_extract_data = {
            "taxpayer_name": taxpayer_name,
            "tax_year": 2024,  # Could be extracted from the result
            "w2_forms": w2_result.get('w2_extract', {}).get('forms', []),
            "total_wages": w2_result.get('total_wages', 0),
            "total_withholding": w2_result.get('total_withholding', 0),
            "forms_count": w2_result.get('forms_count', 0),
            "validation_results": w2_result.get('validation_results', {}),
            "processing_method": w2_result.get('processing_method', 'bedrock_data_automation'),
            "created_at": datetime.now().isoformat()
        }
        
        # Upload to S3
        s3_client.put_object(
            Bucket=settings.documents_bucket_name,
            Key=extract_s3_key,
            Body=json.dumps(w2_extract_data, indent=2, default=str),
            ContentType='application/json'
        )
        
        # Save metadata to DynamoDB in the format calc_1040 expects
        documents_table = dynamodb.Table(settings.tax_documents_table_name)
        
        document_item = {
            'tenant_id#engagement_id': f"{user_id}#{engagement_id}",
            'doc#path': 'doc#/Workpapers/W2_Extracts.json',
            'engagement_id': engagement_id,
            'document_type': 'W-2_EXTRACT',
            'mime_type': 'application/json',
            'created_at': datetime.now().isoformat(),
            's3_key': extract_s3_key,
            'size_bytes': len(json.dumps(w2_extract_data, default=str)),
            'hash': 'w2-extract-hash',
            'total_wages': Decimal(str(w2_result.get('total_wages', 0))),
            'total_withholding': Decimal(str(w2_result.get('total_withholding', 0))),
            'forms_count': w2_result.get('forms_count', 0)
        }
        
        documents_table.put_item(Item=document_item)
        
        logger.info(f"Saved W-2 extract data for calc_1040: {extract_s3_key}")
        
    except Exception as e:
        logger.error(f"Failed to save W-2 extract for calc_1040: {e}")
        # Don't raise the exception - this is a supplementary operation


