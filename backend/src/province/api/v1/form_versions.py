"""
Form Versions API

Endpoints for fetching filled form versions from S3 with metadata.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import logging
import boto3
from datetime import datetime
import os

from ...core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/forms", tags=["form-versions"])


class FormVersion(BaseModel):
    """Form version metadata"""
    version: str
    version_number: int
    s3_key: str
    size: int
    timestamp: str
    last_modified: str
    download_url: str


class FormVersionsResponse(BaseModel):
    """Response for form versions list"""
    engagement_id: str
    form_type: str
    tax_year: int
    total_versions: int
    versions: List[FormVersion]
    latest_version: str


@router.get("/{form_type}/{engagement_id}/versions", response_model=FormVersionsResponse)
async def get_form_versions(
    form_type: str,
    engagement_id: str,
    tax_year: int = Query(2024, description="Tax year"),
    limit: int = Query(50, description="Maximum versions to return")
):
    """
    Get all versions of a filled form for an engagement.
    
    Args:
        form_type: Type of form (e.g., "1040")
        engagement_id: Tax engagement ID
        tax_year: Tax year (default: 2024)
        limit: Maximum number of versions to return
        
    Returns:
        List of form versions with metadata and signed URLs
    """
    try:
        settings = get_settings()
        
        # First, get the user_id from the engagement
        dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        engagements_table = dynamodb.Table(settings.tax_engagements_table_name)
        
        # Query for the engagement to get user_id
        engagement_response = engagements_table.scan(
            FilterExpression='engagement_id = :engagement_id',
            ExpressionAttributeValues={
                ':engagement_id': engagement_id
            },
            Limit=1
        )
        
        if not engagement_response.get('Items'):
            raise HTTPException(
                status_code=404,
                detail=f"Engagement {engagement_id} not found"
            )
        
        user_id = engagement_response['Items'][0].get('user_id')
        if not user_id:
            raise HTTPException(
                status_code=500,
                detail=f"Engagement {engagement_id} has no associated user_id"
            )
        
        logger.info(f"Found user_id={user_id} for engagement={engagement_id}")
        
        s3_client = boto3.client(
            's3',
            region_name=settings.aws_region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        bucket = settings.documents_bucket_name
        
        # Forms are now stored as: filled_forms/{user_id}/{form_type}/{tax_year}/vXXX_*.pdf
        prefix = f"filled_forms/{user_id}/{form_type.lower()}/{tax_year}/"
        
        logger.info(f"Searching for forms with prefix: {prefix}")
        
        # List all form versions for this user
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix,
            MaxKeys=limit
        )
        
        versions = []
        
        if response.get('Contents'):
            for obj in response['Contents']:
                key = obj['Key']
                
                # Skip if not a PDF
                if not key.endswith('.pdf'):
                    continue
                
                # Extract version from filename (e.g., v031_1040_1760887161.pdf)
                filename = key.split('/')[-1]
                if filename.startswith('v'):
                    version_str = filename.split('_')[0]  # e.g., "v031"
                    version_num = int(version_str[1:])  # Extract number
                    
                    # Generate signed URL (valid for 1 hour)
                    signed_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': bucket, 'Key': key},
                        ExpiresIn=3600
                    )
                    
                    versions.append(FormVersion(
                        version=version_str,
                        version_number=version_num,
                        s3_key=key,
                        size=obj['Size'],
                        timestamp=obj['LastModified'].isoformat(),
                        last_modified=obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S'),
                        download_url=signed_url
                    ))
        
        logger.info(f"Found {len(versions)} versions for user_id={user_id}, form={form_type}, year={tax_year}")
        
        if not versions:
            raise HTTPException(
                status_code=404,
                detail=f"No versions found for {form_type} form"
            )
        
        # Sort by timestamp (most recent first), not version number
        # Version numbers only make sense within a single taxpayer folder
        versions.sort(key=lambda x: x.timestamp, reverse=True)
        
        return FormVersionsResponse(
            engagement_id=engagement_id,
            form_type=form_type,
            tax_year=tax_year,
            total_versions=len(versions),
            versions=versions,
            latest_version=versions[0].version if versions else "v001"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching form versions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch form versions: {str(e)}"
        )


@router.get("/{form_type}/{engagement_id}/pdf")
async def get_form_pdf(
    form_type: str,
    engagement_id: str,
    version: Optional[str] = Query("latest", description="Version to fetch (e.g., 'v031' or 'latest')"),
    taxpayer: Optional[str] = Query(None, description="Taxpayer name (alternative to engagement_id)"),
    tax_year: int = Query(2024, description="Tax year")
):
    """
    Get a specific version of a filled form PDF.
    
    Args:
        form_type: Type of form (e.g., "1040")
        engagement_id: Tax engagement ID (or "sample" for sample forms)
        version: Version to fetch (default: "latest")
        taxpayer: Taxpayer name for direct lookup (e.g., "John_A._Smith")
        tax_year: Tax year (default: 2024)
        
    Returns:
        Redirect to signed S3 URL for the PDF
    """
    try:
        settings = get_settings()
        
        # Handle direct taxpayer lookup (for sample forms)
        if engagement_id == "sample" and taxpayer:
            s3_client = boto3.client(
                's3',
                region_name=settings.aws_region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            
            bucket = settings.documents_bucket_name
            prefix = f"filled_forms/{taxpayer}/{form_type}/{tax_year}/"
            
            # List objects
            response = s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix,
                MaxKeys=100
            )
            
            if not response.get('Contents'):
                raise HTTPException(
                    status_code=404,
                    detail=f"No forms found for taxpayer {taxpayer}"
                )
            
            # Sort by last modified (latest first)
            objects = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)
            
            # Find the requested version
            if version == "latest":
                target_obj = objects[0]
            else:
                target_obj = next(
                    (obj for obj in objects if version in obj['Key']),
                    None
                )
            
            if not target_obj:
                raise HTTPException(
                    status_code=404,
                    detail=f"Version {version} not found"
                )
            
            # Generate signed URL
            download_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': target_obj['Key']},
                ExpiresIn=3600
            )
            
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=download_url)
        
        # Normal engagement ID lookup
        versions_response = await get_form_versions(
            form_type=form_type,
            engagement_id=engagement_id,
            tax_year=tax_year
        )
        
        # Find the requested version
        if version == "latest":
            target_version = versions_response.versions[0]
        else:
            target_version = next(
                (v for v in versions_response.versions if v.version == version),
                None
            )
        
        if not target_version:
            raise HTTPException(
                status_code=404,
                detail=f"Version {version} not found"
            )
        
        # Return redirect to signed URL
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=target_version.download_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching form PDF: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch form PDF: {str(e)}"
        )

