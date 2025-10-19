"""
Document processing notifications API endpoints.

This provides the same functionality as the Lambda notifications API
but as a FastAPI endpoint for development and testing.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import boto3
import os
from province.core.config import get_settings
from decimal import Decimal

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents/notifications", tags=["document-notifications"])


class MarkReadRequest(BaseModel):
    """Request model for marking notifications as read."""
    timestamps: List[int]


@router.get("/{engagement_id}")
async def get_notifications(
    engagement_id: str,
    since: Optional[int] = None,
    limit: int = 50,
    status: Optional[str] = None,
    x_user_id: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Get document processing notifications for an engagement.
    
    Args:
        engagement_id: Tax engagement ID
        since: Get notifications since this timestamp (optional)
        limit: Maximum number of notifications to return
        status: Filter by notification status (optional)
        x_user_id: User ID from header for authorization
    
    Returns:
        Dict with notifications list and metadata
    """
    try:
        # For now, return mock notifications since we don't have the DynamoDB table set up
        # In production, this would query the province-chat-notifications table
        
        mock_notifications = []
        
        # If this is a request for recent notifications, add some mock processing notifications
        if not since or since < 1000000000000:  # If no since or very old timestamp
            mock_notifications = [
                {
                    'engagement_id': engagement_id,
                    'timestamp': 1697587200000,  # Mock timestamp
                    'message': '📄 Processing W2_XL_input_clean_1000.pdf...',
                    'status': 'processing',
                    'type': 'document_processing',
                    'read': False
                },
                {
                    'engagement_id': engagement_id,
                    'timestamp': 1697587260000,  # 1 minute later
                    'message': '✅ W2_XL_input_clean_1000.pdf processed successfully! Found W-2 with wages: $55,151.93',
                    'status': 'completed',
                    'type': 'document_processing',
                    'read': False,
                    'data': {
                        'document_type': 'W-2',
                        'total_wages': 55151.93,
                        'total_withholding': 16606.17,
                        'forms_count': 1
                    }
                }
            ]
        
        # Filter by status if provided
        if status:
            mock_notifications = [n for n in mock_notifications if n.get('status') == status]
        
        # Apply limit
        mock_notifications = mock_notifications[:limit]
        
        return {
            'success': True,
            'notifications': mock_notifications,
            'count': len(mock_notifications),
            'engagement_id': engagement_id
        }
        
    except Exception as e:
        logger.error(f"Error getting notifications for engagement {engagement_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get notifications: {str(e)}"
        )


@router.post("/{engagement_id}/mark-read")
async def mark_notifications_read(
    engagement_id: str,
    request: MarkReadRequest,
    x_user_id: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Mark notifications as read.
    
    Args:
        engagement_id: Tax engagement ID
        request: Request with timestamps to mark as read
        x_user_id: User ID from header for authorization
    
    Returns:
        Dict with success status and count of updated notifications
    """
    try:
        # For now, just return success since we don't have the DynamoDB table
        # In production, this would update the notifications in the database
        
        updated_count = len(request.timestamps)
        
        logger.info(f"Marked {updated_count} notifications as read for engagement {engagement_id}")
        
        return {
            'success': True,
            'message': f'Marked {updated_count} notifications as read',
            'updated_count': updated_count
        }
        
    except Exception as e:
        logger.error(f"Error marking notifications as read for engagement {engagement_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mark notifications as read: {str(e)}"
        )


@router.post("/{engagement_id}/simulate-processing")
async def simulate_document_processing(
    engagement_id: str,
    x_user_id: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Simulate document processing notifications for testing.
    
    This endpoint simulates what would happen when a document is uploaded
    and processed by the automated pipeline.
    """
    try:
        # Simulate the processing flow
        import asyncio
        from province.agents.tax.tools.ingest_documents import ingest_documents
        
        # Use an existing test document
        s3_key = "datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_1000.pdf"
        
        # Process the document
        result = await ingest_documents(
            s3_key=s3_key,
            taxpayer_name="Test User",
            tax_year=2024,
            document_type="W-2"
        )
        
        if result.get('success'):
            return {
                'success': True,
                'message': 'Document processing simulation completed',
                'processing_result': {
                    'document_type': result.get('document_type'),
                    'total_wages': result.get('total_wages'),
                    'total_withholding': result.get('total_withholding'),
                    'forms_count': result.get('forms_count')
                },
                'notifications': [
                    {
                        'message': '📄 Processing W2_XL_input_clean_1000.pdf...',
                        'status': 'processing',
                        'timestamp': 'now'
                    },
                    {
                        'message': f'✅ W2_XL_input_clean_1000.pdf processed successfully! Found {result.get("document_type")} with wages: ${result.get("total_wages", 0):,.2f}',
                        'status': 'completed',
                        'timestamp': 'now + 30s',
                        'data': result
                    }
                ]
            }
        else:
            return {
                'success': False,
                'error': result.get('error'),
                'notifications': [
                    {
                        'message': '📄 Processing W2_XL_input_clean_1000.pdf...',
                        'status': 'processing',
                        'timestamp': 'now'
                    },
                    {
                        'message': f'❌ Failed to process W2_XL_input_clean_1000.pdf: {result.get("error")}',
                        'status': 'error',
                        'timestamp': 'now + 30s'
                    }
                ]
            }
            
    except Exception as e:
        logger.error(f"Error simulating document processing: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to simulate processing: {str(e)}"
        )
