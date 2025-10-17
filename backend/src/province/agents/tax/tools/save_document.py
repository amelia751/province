"""Save document tool for tax engagements."""

import json
import logging
import base64
from typing import Dict, Any
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from province.core.config import get_settings

logger = logging.getLogger(__name__)


async def save_document(engagement_id: str, path: str, content_b64: str, mime_type: str) -> Dict[str, Any]:
    """
    Save a document to S3 and update the tax documents table.
    
    Args:
        engagement_id: The tax engagement ID
        path: Document path within the engagement folder structure
        content_b64: Base64 encoded document content
        mime_type: MIME type of the document
    
    Returns:
        Dict with success status and document metadata
    """
    
    settings = get_settings()
    
    try:
        # Decode base64 content
        content = base64.b64decode(content_b64)
        
        # Generate S3 key
        s3_key = f"tax-engagements/{engagement_id}/{path}"
        
        # Upload to S3
        s3_client = boto3.client('s3', region_name=settings.aws_region)
        
        bucket_name = settings.documents_bucket_name
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=content,
            ContentType=mime_type,
            Metadata={
                'engagement_id': engagement_id,
                'document_path': path,
                'upload_timestamp': datetime.now().isoformat()
            }
        )
        
        # Calculate content hash
        import hashlib
        content_hash = hashlib.sha256(content).hexdigest()
        
        # Update DynamoDB documents table
        dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        table = dynamodb.Table(settings.tax_documents_table_name)
        
        # Get engagement details to find the user_id
        engagements_table = dynamodb.Table(settings.tax_engagements_table_name)
        engagement_response = engagements_table.scan(
            FilterExpression='engagement_id = :engagement_id',
            ExpressionAttributeValues={
                ':engagement_id': engagement_id
            }
        )
        
        if not engagement_response.get('Items'):
            raise Exception(f"Engagement {engagement_id} not found")
        
        user_id = engagement_response['Items'][0]['user_id']
        
        table.put_item(
            Item={
                'tenant_id#engagement_id': f"{user_id}#{engagement_id}",
                'doc#path': f"doc#{path}",
                'document_type': _determine_document_type(path),
                's3_key': s3_key,
                'mime_type': mime_type,
                'version': 1,
                'hash': content_hash,
                'size_bytes': len(content),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'engagement_id': engagement_id  # Store engagement_id for easy lookup
            }
        )
        
        logger.info(f"Saved document {path} for engagement {engagement_id}")
        
        return {
            'success': True,
            'document_id': f"{engagement_id}#{path}",
            's3_key': s3_key,
            'hash': content_hash,
            'size_bytes': len(content)
        }
        
    except ClientError as e:
        logger.error(f"AWS error saving document: {e}")
        return {
            'success': False,
            'error': f"AWS error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error saving document: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def _determine_document_type(path: str) -> str:
    """Determine document type from path."""
    
    path_lower = path.lower()
    
    if 'w2' in path_lower and path_lower.endswith('.pdf'):
        return 'w2'
    elif 'prior_year' in path_lower and '1040' in path_lower:
        return 'prior_year_1040'
    elif 'organizer.md' in path_lower:
        return 'organizer'
    elif 'w2_extracts.json' in path_lower:
        return 'w2_extracts'
    elif 'calc_1040_simple.json' in path_lower:
        return 'calc_1040_simple'
    elif '1040_draft.pdf' in path_lower:
        return 'draft_1040'
    elif 'federal.ics' in path_lower:
        return 'federal_ics'
    else:
        return 'other'
