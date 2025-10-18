"""Document management API endpoints."""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import boto3
import os
from province.config import settings

from province.agents.tax.tools.save_document import save_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


class SaveDocumentRequest(BaseModel):
    """Request model for saving documents."""
    engagement_id: str
    path: str
    content_b64: str
    mime_type: str


class DeleteDocumentRequest(BaseModel):
    """Request model for deleting documents."""
    user_id: str
    document_key: str  # S3 key of the document


class ListDocumentsRequest(BaseModel):
    """Request model for listing user documents."""
    user_id: str


@router.post("/save")
async def save_document_endpoint(request: SaveDocumentRequest) -> Dict[str, Any]:
    """
    Save a document to S3 and update the tax documents table.
    
    Args:
        request: Document save request containing engagement_id, path, content_b64, and mime_type
    
    Returns:
        Dict with success status and document metadata
    """
    try:
        result = await save_document(
            engagement_id=request.engagement_id,
            path=request.path,
            content_b64=request.content_b64,
            mime_type=request.mime_type
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Document save failed')
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in save_document_endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/list")
async def list_user_documents(request: ListDocumentsRequest) -> Dict[str, Any]:
    """
    List all documents belonging to a user.
    
    Args:
        request: List request containing user_id
    
    Returns:
        Dict with documents list and metadata
    """
    try:
        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        table = dynamodb.Table('province-tax-documents')
        
        # Scan for documents belonging to this user
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('tenant_id#engagement_id').begins_with(f"{request.user_id}#")
        )
        
        documents = []
        for item in response.get('Items', []):
            documents.append({
                'document_key': item.get('document_key'),
                'document_path': item.get('document_path'),
                'mime_type': item.get('mime_type'),
                'file_size': item.get('file_size'),
                'upload_timestamp': item.get('upload_timestamp'),
                'engagement_id': item.get('engagement_id'),
                'tenant_id_engagement_id': item.get('tenant_id#engagement_id')
            })
        
        return {
            'success': True,
            'documents': documents,
            'count': len(documents)
        }
        
    except Exception as e:
        logger.error(f"Error listing user documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.delete("/delete")
async def delete_document(request: DeleteDocumentRequest) -> Dict[str, Any]:
    """
    Delete a specific document belonging to a user.
    
    Args:
        request: Delete request containing user_id and document_key
    
    Returns:
        Dict with success status
    """
    try:
        # Initialize AWS clients
        s3_client = boto3.client('s3', region_name=settings.aws_region)
        dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        table = dynamodb.Table('province-tax-documents')
        
        # First, verify the document belongs to this user
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('tenant_id#engagement_id').begins_with(f"{request.user_id}#") &
                           boto3.dynamodb.conditions.Attr('document_key').eq(request.document_key)
        )
        
        items = response.get('Items', [])
        if not items:
            raise HTTPException(
                status_code=404,
                detail="Document not found or does not belong to user"
            )
        
        document_item = items[0]
        
        # Delete from S3
        try:
            s3_client.delete_object(
                Bucket='province-documents-[REDACTED-ACCOUNT-ID]-us-east-1',
                Key=request.document_key
            )
            logger.info(f"Deleted document from S3: {request.document_key}")
        except Exception as s3_error:
            logger.warning(f"Failed to delete from S3 (may not exist): {s3_error}")
        
        # Delete from DynamoDB
        table.delete_item(
            Key={
                'tenant_id#engagement_id': document_item['tenant_id#engagement_id'],
                'document_key': request.document_key
            }
        )
        
        logger.info(f"Deleted document from DynamoDB: {request.document_key}")
        
        return {
            'success': True,
            'message': f"Document {request.document_key} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.delete("/delete-all")
async def delete_all_user_documents(request: ListDocumentsRequest) -> Dict[str, Any]:
    """
    Delete all documents belonging to a user.
    
    Args:
        request: Request containing user_id
    
    Returns:
        Dict with success status and count of deleted documents
    """
    try:
        # Initialize AWS clients
        s3_client = boto3.client('s3', region_name=settings.aws_region)
        dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        table = dynamodb.Table('province-tax-documents')
        
        # Get all documents for this user
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('tenant_id#engagement_id').begins_with(f"{request.user_id}#")
        )
        
        items = response.get('Items', [])
        if not items:
            return {
                'success': True,
                'message': "No documents found to delete",
                'deleted_count': 0
            }
        
        deleted_count = 0
        errors = []
        
        for item in items:
            try:
                document_key = item['document_key']
                
                # Delete from S3
                try:
                    s3_client.delete_object(
                        Bucket='province-documents-[REDACTED-ACCOUNT-ID]-us-east-1',
                        Key=document_key
                    )
                except Exception as s3_error:
                    logger.warning(f"Failed to delete from S3: {document_key} - {s3_error}")
                
                # Delete from DynamoDB
                table.delete_item(
                    Key={
                        'tenant_id#engagement_id': item['tenant_id#engagement_id'],
                        'document_key': document_key
                    }
                )
                
                deleted_count += 1
                logger.info(f"Deleted document: {document_key}")
                
            except Exception as e:
                error_msg = f"Failed to delete {item.get('document_key', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return {
            'success': True,
            'message': f"Deleted {deleted_count} documents",
            'deleted_count': deleted_count,
            'errors': errors if errors else None
        }
        
    except Exception as e:
        logger.error(f"Error deleting all user documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete documents: {str(e)}"
        )
