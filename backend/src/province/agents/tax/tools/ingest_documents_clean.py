"""Clean document ingestion tool using only AWS Bedrock Data Automation.
Handles W-2, 1099-INT, 1099-MISC, and other tax documents."""

import json
import logging
import os
import re
import time
from typing import Dict, Any, List
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

from province.core.config import get_settings
from ..models import W2Form, W2Extract

logger = logging.getLogger(__name__)


async def ingest_documents(s3_key: str, taxpayer_name: str, tax_year: int, document_type: str = None) -> Dict[str, Any]:
    """
    Extract tax document data using AWS Bedrock Data Automation only.
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
        
        # Use appropriate profile based on document type
        if document_type.upper() == 'W-2':
            profile_to_use = profile_arn
            logger.info(f"Using profile for W-2: {profile_to_use}")
        else:
            # For other document types, use the same profile for now
            profile_to_use = profile_arn
            logger.info(f"Using profile for {document_type}: {profile_to_use}")
        
        # Check for existing results first
        existing_result = await _check_existing_results(s3_client, output_bucket, s3_key)
        if existing_result:
            logger.info(f"Found existing Bedrock results for {s3_key}")
            return existing_result
        
        # Process with Bedrock Data Automation
        return await _process_with_bedrock_data_automation(
            runtime_client, s3_client, project_arn, profile_to_use, 
            input_bucket, output_bucket, s3_key, taxpayer_name, tax_year, document_type
        )
        
    except Exception as e:
        logger.error(f"Error in ingest_documents: {e}")
        return {
            'success': False,
            'error': f"Document processing failed: {str(e)}"
        }


async def _check_existing_results(s3_client, output_bucket: str, s3_key: str) -> Dict[str, Any]:
    """Check if Bedrock Data Automation results already exist for this file."""
    
    try:
        filename = s3_key.split('/')[-1]
        logger.info(f"Looking for existing results for file: {filename}")
        
        # List objects in the output bucket to find matching results
        response = s3_client.list_objects_v2(
            Bucket=output_bucket,
            Prefix='inference_results/'
        )
        
        if 'Contents' not in response:
            return None
        
        # Look for job metadata files that might contain our file
        for obj in response['Contents']:
            if obj['Key'].endswith('job_metadata.json'):
                try:
                    # Download and check the metadata
                    metadata_response = s3_client.get_object(Bucket=output_bucket, Key=obj['Key'])
                    metadata = json.loads(metadata_response['Body'].read())
                    
                    # Check if this job processed our file
                    if 'inputDataConfig' in metadata:
                        input_config = metadata['inputDataConfig']
                        if 'dataSource' in input_config and 's3Location' in input_config['dataSource']:
                            s3_location = input_config['dataSource']['s3Location']
                            if filename in s3_location.get('uri', ''):
                                logger.info(f"Found matching job metadata: {obj['Key']}")
                                
                                # Try to load the results
                                job_id = obj['Key'].split('/')[1]  # Extract job ID from path
                                result_key = f"inference_results/{job_id}/0/standard_output/0/result.json"
                                
                                try:
                                    result_response = s3_client.get_object(Bucket=output_bucket, Key=result_key)
                                    result_data = json.loads(result_response['Body'].read())
                                    logger.info(f"Successfully loaded existing Bedrock results from {result_key}")
                                    
                                    # Process the existing results
                                    return await _process_bedrock_results(result_data, s3_key, "Unknown", 2024, "W-2")
                                    
                                except ClientError as e:
                                    logger.warning(f"Could not load result file {result_key}: {e}")
                                    continue
                                    
                except Exception as e:
                    logger.warning(f"Error checking metadata file {obj['Key']}: {e}")
                    continue
        
        return None
        
    except Exception as e:
        logger.warning(f"Error checking for existing results: {e}")
        return None


async def _process_with_bedrock_data_automation(runtime_client, s3_client, project_arn: str, profile_arn: str, 
                                              input_bucket: str, output_bucket: str, s3_key: str, 
                                              taxpayer_name: str, tax_year: int, document_type: str) -> Dict[str, Any]:
    """Process document using Bedrock Data Automation."""
    
    try:
        # Invoke Bedrock Data Automation
        response = runtime_client.invoke_data_automation_async(
            projectArn=project_arn,
            inputDataConfig={
                'dataSource': {
                    's3Location': {
                        'uri': f's3://{input_bucket}/{s3_key}'
                    }
                }
            },
            outputDataConfig={
                'dataSource': {
                    's3Location': {
                        'uri': f's3://{output_bucket}/inference_results'
                    }
                }
            },
            dataAutomationConfiguration={
                'dataAutomationArn': profile_arn
            }
        )
        
        invocation_arn = response['invocationArn']
        logger.info(f"Started Bedrock Data Automation job: {invocation_arn}")
        
        # Wait for completion with timeout
        max_wait_time = 300  # 5 minutes
        wait_interval = 10   # 10 seconds
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            try:
                status_response = runtime_client.get_data_automation_status(
                    invocationArn=invocation_arn
                )
                
                status = status_response['status']
                logger.info(f"Bedrock job status: {status}")
                
                if status == 'Completed':
                    # Get the results
                    output_location = status_response.get('outputDataConfig', {}).get('dataSource', {}).get('s3Location', {}).get('uri', '')
                    if output_location:
                        # Extract results from S3
                        return await _extract_bedrock_results(s3_client, output_location, s3_key, taxpayer_name, tax_year, document_type)
                    else:
                        return {
                            'success': False,
                            'error': 'Bedrock processing completed but no output location found'
                        }
                        
                elif status in ['Failed', 'Cancelled']:
                    error_msg = status_response.get('failureReason', f'Job {status.lower()}')
                    logger.error(f"Bedrock job {status.lower()}: {error_msg}")
                    return {
                        'success': False,
                        'error': f'Bedrock Data Automation processing {status.lower()}: {error_msg}'
                    }
                
                # Wait before checking again
                time.sleep(wait_interval)
                elapsed_time += wait_interval
                
            except Exception as e:
                logger.error(f"Error checking Bedrock job status: {e}")
                return {
                    'success': False,
                    'error': f'Error monitoring Bedrock job: {str(e)}'
                }
        
        # Timeout
        logger.error(f"Bedrock processing timed out after {max_wait_time} seconds")
        return {
            'success': False,
            'error': f'Bedrock processing timed out after {max_wait_time} seconds'
        }
        
    except Exception as e:
        logger.error(f"Error in Bedrock Data Automation processing: {e}")
        return {
            'success': False,
            'error': f'Bedrock Data Automation processing failed: {str(e)}'
        }


async def _extract_bedrock_results(s3_client, output_location: str, s3_key: str, taxpayer_name: str, tax_year: int, document_type: str) -> Dict[str, Any]:
    """Extract and process results from Bedrock Data Automation output."""
    
    try:
        # Parse S3 location
        if not output_location.startswith('s3://'):
            return {
                'success': False,
                'error': f'Invalid output location format: {output_location}'
            }
        
        # Extract bucket and prefix from S3 URI
        s3_parts = output_location.replace('s3://', '').split('/', 1)
        bucket = s3_parts[0]
        prefix = s3_parts[1] if len(s3_parts) > 1 else ''
        
        # Look for result files
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix
        )
        
        if 'Contents' not in response:
            return {
                'success': False,
                'error': 'No results found in Bedrock output location'
            }
        
        # Find the result.json file
        result_key = None
        for obj in response['Contents']:
            if obj['Key'].endswith('result.json'):
                result_key = obj['Key']
                break
        
        if not result_key:
            return {
                'success': False,
                'error': 'No result.json file found in Bedrock output'
            }
        
        # Download and process the results
        result_response = s3_client.get_object(Bucket=bucket, Key=result_key)
        result_data = json.loads(result_response['Body'].read())
        
        return await _process_bedrock_results(result_data, s3_key, taxpayer_name, tax_year, document_type)
        
    except Exception as e:
        logger.error(f"Error extracting Bedrock results: {e}")
        return {
            'success': False,
            'error': f'Error extracting Bedrock results: {str(e)}'
        }


async def _process_bedrock_results(result_data: Dict[str, Any], s3_key: str, taxpayer_name: str, tax_year: int, document_type: str) -> Dict[str, Any]:
    """Process Bedrock Data Automation results into structured tax data."""
    
    try:
        logger.info("Extracting W-2 data from Bedrock Data Automation standard output")
        
        # Extract standard output content
        standard_output = result_data.get('standard_output', '')
        if not standard_output:
            return {
                'success': False,
                'error': 'No standard output found in Bedrock results'
            }
        
        logger.info(f"Processing markdown content: {len(standard_output)} characters")
        
        # Extract W-2 data from the markdown content
        w2_data = _extract_w2_from_standard_output(standard_output, s3_key)
        
        if not w2_data:
            return {
                'success': False,
                'error': 'Could not extract W-2 data from Bedrock results'
            }
        
        logger.info(f"Extracted W-2 data from standard output: {len(w2_data)} boxes found")
        
        # Create W2Extract object
        w2_forms = []
        total_wages = Decimal('0')
        total_withholding = Decimal('0')
        
        for form_data in w2_data:
            boxes = form_data.get('boxes', {})
            pin_cites = form_data.get('pin_cites', {})
            
            # Convert string values to Decimal for financial calculations
            for box_num, value in boxes.items():
                if isinstance(value, str) and value.replace('.', '').replace(',', '').isdigit():
                    boxes[box_num] = Decimal(value.replace(',', ''))
            
            w2_form = W2Form(
                employer_name=form_data.get('employer_name', ''),
                employer_ein=form_data.get('employer_ein', ''),
                employee_name=taxpayer_name,
                employee_ssn=form_data.get('employee_ssn', ''),
                boxes=boxes,
                pin_cites=pin_cites
            )
            
            w2_forms.append(w2_form)
            
            # Add to totals
            if '1' in boxes:  # Wages
                total_wages += boxes['1']
            if '2' in boxes:  # Federal withholding
                total_withholding += boxes['2']
        
        # Create W2Extract
        w2_extract = W2Extract(
            forms=w2_forms,
            total_wages=total_wages,
            total_withholding=total_withholding
        )
        
        logger.info(f"Successfully extracted W-2 data from {s3_key} using Bedrock Data Automation")
        
        return {
            'success': True,
            'message': f"Successfully processed {document_type} document! Found {len(w2_forms)} form(s) with total wages/income of ${total_wages} and federal withholding of ${total_withholding}.",
            'extracted_data': w2_extract.model_dump(),
            'taxpayer_name': taxpayer_name,
            'tax_year': tax_year,
            'document_type': document_type,
            'total_wages': float(total_wages),
            'total_withholding': float(total_withholding),
            'processing_method': 'bedrock_data_automation'
        }
        
    except Exception as e:
        logger.error(f"Error processing Bedrock results: {e}")
        return {
            'success': False,
            'error': f'Error processing Bedrock results: {str(e)}'
        }


def _detect_document_type(s3_key: str) -> str:
    """Detect document type from S3 key."""
    
    key_lower = s3_key.lower()
    
    if 'w2' in key_lower or 'w-2' in key_lower:
        return 'W-2'
    elif '1099' in key_lower:
        if 'int' in key_lower:
            return '1099-INT'
        elif 'misc' in key_lower:
            return '1099-MISC'
        else:
            return '1099'
    else:
        return 'W-2'  # Default


def _extract_w2_from_standard_output(standard_output: str, s3_key: str) -> List[Dict[str, Any]]:
    """Extract W-2 data from Bedrock Data Automation standard output."""
    
    try:
        w2_forms = []
        
        # Parse the markdown content to extract W-2 information
        lines = standard_output.split('\n')
        current_form = {}
        boxes = {}
        
        for line in lines:
            line = line.strip()
            
            # Look for box patterns (e.g., "Box 1: $55,151.93")
            box_match = re.search(r'Box\s+(\d+[a-z]?):\s*\$?([\d,]+\.?\d*)', line, re.IGNORECASE)
            if box_match:
                box_num = box_match.group(1)
                amount = box_match.group(2).replace(',', '')
                try:
                    boxes[box_num] = float(amount)
                except ValueError:
                    boxes[box_num] = amount
            
            # Look for employer information
            if 'employer' in line.lower() and ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    current_form['employer_name'] = parts[1].strip()
            
            # Look for EIN
            if 'ein' in line.lower() and ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    current_form['employer_ein'] = parts[1].strip()
        
        if boxes:
            # Create pin_cites for the extracted data
            pin_cites = {}
            for box_num in boxes.keys():
                pin_cites[box_num] = {
                    'file': s3_key.split('/')[-1],
                    'page': 1,
                    'confidence': 0.9,
                    'source': 'bedrock_data_automation'
                }
            
            current_form.update({
                'boxes': boxes,
                'pin_cites': pin_cites
            })
            
            w2_forms.append(current_form)
        
        return w2_forms
        
    except Exception as e:
        logger.error(f"Error extracting W-2 from standard output: {e}")
        return []
