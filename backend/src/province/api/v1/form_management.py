"""
Form Management API - Delete filled forms
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import logging
import boto3
import os

from ...core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/forms", tags=["form-management"])


class DeleteFormsRequest(BaseModel):
    """Request to delete filled forms"""
    user_id: str
    form_type: Optional[str] = "1040"
    tax_year: Optional[int] = 2024


class DeleteFormsResponse(BaseModel):
    """Response for delete forms"""
    success: bool
    message: str
    deleted_count: int


@router.delete("/delete-filled", response_model=DeleteFormsResponse)
async def delete_filled_forms(
    user_id: str = Query(..., description="User ID (Clerk ID)"),
    form_type: str = Query("1040", description="Form type to delete"),
    tax_year: int = Query(2024, description="Tax year")
):
    """
    Delete all filled forms for a specific user, form type, and tax year.
    
    This is useful for testing - clears all versions of filled forms.
    
    Args:
        user_id: Clerk user ID
        form_type: Type of form (default: "1040")
        tax_year: Tax year (default: 2024)
        
    Returns:
        Success status and count of deleted forms
    """
    try:
        settings = get_settings()
        
        s3_client = boto3.client(
            's3',
            region_name=settings.aws_region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        bucket = settings.documents_bucket_name
        
        # Path: filled_forms/{user_id}/{form_type}/{tax_year}/
        prefix = f"filled_forms/{user_id}/{form_type.lower()}/{tax_year}/"
        
        logger.info(f"Deleting filled forms with prefix: {prefix}")
        
        # List all objects with this prefix
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix
        )
        
        deleted_count = 0
        
        if response.get('Contents'):
            # Delete each object
            for obj in response['Contents']:
                s3_client.delete_object(
                    Bucket=bucket,
                    Key=obj['Key']
                )
                deleted_count += 1
                logger.info(f"Deleted: {obj['Key']}")
        
        message = f"Deleted {deleted_count} filled form(s) for user {user_id}"
        logger.info(f"✅ {message}")
        
        return DeleteFormsResponse(
            success=True,
            message=message,
            deleted_count=deleted_count
        )
        
    except Exception as e:
        logger.error(f"Error deleting filled forms: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete filled forms: {str(e)}"
        )


@router.delete("/delete-all-filled", response_model=DeleteFormsResponse)
async def delete_all_filled_forms(
    user_id: str = Query(..., description="User ID (Clerk ID)")
):
    """
    Delete ALL filled forms for a specific user (all form types and years).
    
    WARNING: This deletes everything in filled_forms/{user_id}/
    
    Args:
        user_id: Clerk user ID
        
    Returns:
        Success status and count of deleted forms
    """
    try:
        settings = get_settings()
        
        s3_client = boto3.client(
            's3',
            region_name=settings.aws_region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        bucket = settings.documents_bucket_name
        
        # Path: filled_forms/{user_id}/
        prefix = f"filled_forms/{user_id}/"
        
        logger.info(f"⚠️  Deleting ALL filled forms for user with prefix: {prefix}")
        
        # List all objects with this prefix
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix
        )
        
        deleted_count = 0
        
        if response.get('Contents'):
            # Delete each object
            for obj in response['Contents']:
                s3_client.delete_object(
                    Bucket=bucket,
                    Key=obj['Key']
                )
                deleted_count += 1
                logger.info(f"Deleted: {obj['Key']}")
        
        message = f"Deleted ALL {deleted_count} filled form(s) for user {user_id}"
        logger.info(f"✅ {message}")
        
        return DeleteFormsResponse(
            success=True,
            message=message,
            deleted_count=deleted_count
        )
        
    except Exception as e:
        logger.error(f"Error deleting all filled forms: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete all filled forms: {str(e)}"
        )

