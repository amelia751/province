"""
AWS Lambda function to automatically process uploaded tax documents.

This function is triggered by S3 events when new documents are uploaded
to the tax-engagements/ prefix. It processes the documents using Bedrock
Data Automation and updates the chat with processing status.

Event Flow:
1. User uploads document → S3
2. S3 → EventBridge → Lambda (this function)
3. Lambda → Bedrock Data Automation
4. Lambda → WebSocket/Chat notification
"""

import json
import logging
import asyncio
import boto3
from typing import Dict, Any
import os
import sys

# Add the src directory to Python path for imports
sys.path.append('/opt/python/lib/python3.11/site-packages')
sys.path.append('/var/task/src')

from province.agents.tax.tools.ingest_documents import ingest_documents

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda handler for processing uploaded tax documents.
    
    Args:
        event: S3 event notification from EventBridge
        context: Lambda context
    
    Returns:
        Dict with processing results
    """
    logger.info(f"Received event: {json.dumps(event, indent=2)}")
    
    try:
        # Parse S3 event
        records = event.get('Records', [])
        if not records:
            logger.warning("No records found in event")
            return {'statusCode': 200, 'body': 'No records to process'}
        
        results = []
        
        for record in records:
            try:
                # Extract S3 information
                s3_info = record.get('s3', {})
                bucket_name = s3_info.get('bucket', {}).get('name')
                object_key = s3_info.get('object', {}).get('key')
                
                if not bucket_name or not object_key:
                    logger.warning(f"Missing S3 info in record: {record}")
                    continue
                
                logger.info(f"Processing document: s3://{bucket_name}/{object_key}")
                
                # Only process documents in tax-engagements/ prefix
                if not object_key.startswith('tax-engagements/'):
                    logger.info(f"Skipping non-tax document: {object_key}")
                    continue
                
                # Extract engagement_id from path: tax-engagements/{engagement_id}/...
                path_parts = object_key.split('/')
                if len(path_parts) < 3:
                    logger.warning(f"Invalid path structure: {object_key}")
                    continue
                
                engagement_id = path_parts[1]
                file_name = path_parts[-1]
                
                # Determine document type from file name
                document_type = detect_document_type(file_name)
                
                if not document_type:
                    logger.info(f"Unsupported document type: {file_name}")
                    continue
                
                # Process the document asynchronously
                result = asyncio.run(process_document(
                    s3_key=object_key,
                    engagement_id=engagement_id,
                    document_type=document_type,
                    file_name=file_name
                ))
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing record {record}: {e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'record': record
                })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Processed {len(results)} documents',
                'results': results
            })
        }
        
    except Exception as e:
        logger.error(f"Lambda handler error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

def detect_document_type(file_name: str) -> str:
    """
    Detect document type from file name.
    
    Args:
        file_name: Name of the uploaded file
    
    Returns:
        Document type string or None if unsupported
    """
    file_name_lower = file_name.lower()
    
    if 'w2' in file_name_lower or 'w-2' in file_name_lower:
        return 'W-2'
    elif '1099' in file_name_lower:
        if 'int' in file_name_lower:
            return '1099-INT'
        elif 'misc' in file_name_lower:
            return '1099-MISC'
        else:
            return '1099'
    elif 'tax' in file_name_lower:
        return 'tax-document'
    
    # Check file extension for PDFs and images
    if file_name_lower.endswith(('.pdf', '.png', '.jpg', '.jpeg')):
        return 'tax-document'  # Generic tax document for auto-detection
    
    return None

async def process_document(s3_key: str, engagement_id: str, document_type: str, file_name: str) -> Dict[str, Any]:
    """
    Process a tax document using Bedrock Data Automation.
    
    Args:
        s3_key: S3 key of the document
        engagement_id: Tax engagement ID
        document_type: Type of document (W-2, 1099, etc.)
        file_name: Original file name
    
    Returns:
        Processing result dictionary
    """
    logger.info(f"Processing {document_type} document: {s3_key}")
    
    try:
        # Send initial processing notification
        await send_chat_notification(
            engagement_id=engagement_id,
            message=f"📄 Processing {file_name}...",
            status="processing"
        )
        
        # Process document with Bedrock Data Automation
        result = await ingest_documents(
            s3_key=s3_key,
            taxpayer_name="User",  # Will be updated with actual user info
            tax_year=2024,
            document_type=document_type
        )
        
        if result.get('success'):
            # Send success notification with extracted data
            await send_chat_notification(
                engagement_id=engagement_id,
                message=f"✅ {file_name} processed successfully! Found {result.get('document_type')} with wages: ${result.get('total_wages', 0):,.2f}",
                status="completed",
                data=result
            )
            
            logger.info(f"Successfully processed {s3_key}")
            return {
                'success': True,
                'engagement_id': engagement_id,
                'document_type': result.get('document_type'),
                'total_wages': result.get('total_wages'),
                'total_withholding': result.get('total_withholding'),
                's3_key': s3_key
            }
        else:
            # Send error notification
            await send_chat_notification(
                engagement_id=engagement_id,
                message=f"❌ Failed to process {file_name}: {result.get('error')}",
                status="error"
            )
            
            return {
                'success': False,
                'error': result.get('error'),
                'engagement_id': engagement_id,
                's3_key': s3_key
            }
            
    except Exception as e:
        logger.error(f"Error processing document {s3_key}: {e}")
        
        # Send error notification
        await send_chat_notification(
            engagement_id=engagement_id,
            message=f"❌ Error processing {file_name}: {str(e)}",
            status="error"
        )
        
        return {
            'success': False,
            'error': str(e),
            'engagement_id': engagement_id,
            's3_key': s3_key
        }

async def send_chat_notification(engagement_id: str, message: str, status: str, data: Dict = None):
    """
    Send real-time notification to the chat interface.
    
    This could be implemented using:
    - WebSocket API Gateway
    - AWS AppSync
    - Server-Sent Events
    - Polling endpoint
    
    For now, we'll store the notification in DynamoDB for the frontend to poll.
    """
    try:
        dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        table = dynamodb.Table('province-chat-notifications')
        
        notification = {
            'engagement_id': engagement_id,
            'timestamp': int(asyncio.get_event_loop().time() * 1000),
            'message': message,
            'status': status,
            'type': 'document_processing'
        }
        
        if data:
            notification['data'] = data
        
        table.put_item(Item=notification)
        logger.info(f"Sent notification for engagement {engagement_id}: {message}")
        
    except Exception as e:
        logger.error(f"Failed to send chat notification: {e}")
        # Don't fail the whole process if notification fails
