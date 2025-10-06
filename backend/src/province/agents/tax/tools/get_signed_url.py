"""Get signed URL tool for tax document access."""

import json
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError

from province.core.config import get_settings

logger = logging.getLogger(__name__)


async def get_signed_url(engagement_id: str, path: str, mode: str, mime_type: str = None) -> Dict[str, Any]:
    """
    Generate a pre-signed S3 URL for document upload or download.
    
    Args:
        engagement_id: The tax engagement ID
        path: Document path within the engagement folder structure
        mode: "put" for upload, "get" for download
        mime_type: MIME type (required for put operations)
    
    Returns:
        Dict with signed URL and metadata
    """
    
    settings = get_settings()
    
    try:
        # Generate S3 key
        s3_key = f"tax-engagements/{engagement_id}/{path}"
        
        s3_client = boto3.client('s3', region_name=settings.aws_region)
        bucket_name = "province-documents-storage"
        
        if mode == "put":
            # Generate upload URL
            if not mime_type:
                return {
                    'success': False,
                    'error': 'MIME type is required for upload URLs'
                }
            
            # Set expiration time (15 minutes for uploads)
            expiration = 900  # 15 minutes
            
            url = s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': s3_key,
                    'ContentType': mime_type,
                    'Metadata': {
                        'engagement_id': engagement_id,
                        'document_path': path,
                        'upload_timestamp': datetime.now().isoformat()
                    }
                },
                ExpiresIn=expiration
            )
            
        elif mode == "get":
            # Generate download URL
            
            # Set expiration time (1 hour for downloads)
            expiration = 3600  # 1 hour
            
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            
        else:
            return {
                'success': False,
                'error': f'Invalid mode: {mode}. Must be "put" or "get"'
            }
        
        logger.info(f"Generated {mode} URL for {path} in engagement {engagement_id}")
        
        return {
            'success': True,
            'url': url,
            's3_key': s3_key,
            'mode': mode,
            'expires_in_seconds': expiration,
            'expires_at': (datetime.now() + timedelta(seconds=expiration)).isoformat()
        }
        
    except ClientError as e:
        logger.error(f"AWS error generating signed URL: {e}")
        return {
            'success': False,
            'error': f"AWS error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error generating signed URL: {e}")
        return {
            'success': False,
            'error': str(e)
        }
