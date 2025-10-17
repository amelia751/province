"""Tax engagement management API endpoints."""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError

from province.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tax-engagements", tags=["tax-engagements"])


class CreateTaxEngagementRequest(BaseModel):
    """Request model for creating tax engagements."""
    user_id: str
    filing_year: int
    status: str = "draft"


class TaxEngagementResponse(BaseModel):
    """Response model for tax engagements."""
    engagement_id: str
    user_id: str
    filing_year: int
    status: str
    created_at: str
    updated_at: str


def get_current_tax_year() -> int:
    """Determine the current tax year."""
    from datetime import datetime
    now = datetime.now()
    current_year = now.year
    
    # For 2025, we're working on 2025 taxes
    if current_year == 2025:
        return 2025
    
    # After April 15th, we're working on next year's taxes
    tax_deadline = datetime(current_year, 4, 15)
    return current_year + 1 if now > tax_deadline else current_year


@router.post("", response_model=Dict[str, Any])
async def create_tax_engagement(request: CreateTaxEngagementRequest) -> Dict[str, Any]:
    """
    Create a new tax engagement.
    
    Args:
        request: Tax engagement creation request
    
    Returns:
        Dict with engagement details
    """
    settings = get_settings()
    
    try:
        # First check if an engagement already exists for this user/year
        dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        table = dynamodb.Table(settings.tax_engagements_table_name)
        
        # Query existing engagements
        existing_response = table.scan(
            FilterExpression='begins_with(#pk, :user_prefix) AND filing_year = :filing_year',
            ExpressionAttributeNames={
                '#pk': 'tenant_id#engagement_id'
            },
            ExpressionAttributeValues={
                ':user_prefix': f"{request.user_id}#",
                ':filing_year': request.filing_year
            }
        )
        
        # If engagement already exists, return it instead of creating a new one
        if existing_response.get('Items'):
            existing_item = existing_response['Items'][0]  # Get the first one
            logger.info(f"Found existing tax engagement {existing_item['engagement_id']} for user {request.user_id}")
            
            return {
                'success': True,
                'engagement_id': existing_item['engagement_id'],
                'filing_year': existing_item['filing_year'],
                'status': existing_item['status'],
                'created_at': existing_item['created_at']
            }
        
        # Generate engagement ID (UUID)
        engagement_id = str(uuid.uuid4())
        
        # Create engagement record
        now = datetime.now().isoformat()
        engagement_data = {
            'tenant_id#engagement_id': f"{request.user_id}#{engagement_id}",  # Composite key for DynamoDB
            'engagement_id': engagement_id,    # Store UUID separately for easy access
            'user_id': request.user_id,        # Store user ID separately for lookup
            'filing_year': request.filing_year,
            'status': request.status,
            'created_at': now,
            'updated_at': now,
            'folder_structure': {
                'uploads': [],
                'workpapers': [],
                'drafts': [],
                'final': []
            }
        }
        
        table.put_item(Item=engagement_data)
        
        logger.info(f"Created tax engagement {engagement_id} for user {request.user_id}")
        
        return {
            'success': True,
            'engagement_id': engagement_id,  # Return only the UUID
            'filing_year': request.filing_year,
            'status': request.status,
            'created_at': now
        }
        
    except ClientError as e:
        logger.error(f"DynamoDB error creating engagement: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating tax engagement: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("", response_model=Dict[str, Any])
async def get_tax_engagements(
    user_id: str,
    filing_year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get tax engagements for a user.
    
    Args:
        user_id: User ID to fetch engagements for
        filing_year: Optional filing year filter
    
    Returns:
        Dict with list of engagements
    """
    settings = get_settings()
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        table = dynamodb.Table(settings.tax_engagements_table_name)
        
        # Query by user_id using composite key prefix
        response = table.scan(
            FilterExpression='begins_with(#pk, :user_prefix)',
            ExpressionAttributeNames={
                '#pk': 'tenant_id#engagement_id'
            },
            ExpressionAttributeValues={
                ':user_prefix': f"{user_id}#"
            }
        )
        
        engagements = []
        for item in response.get('Items', []):
            engagement = {
                'engagement_id': item.get('engagement_id'),
                'user_id': item.get('user_id'),
                'filing_year': item.get('filing_year'),
                'status': item.get('status'),
                'created_at': item.get('created_at'),
                'updated_at': item.get('updated_at')
            }
            
            # Filter by filing year if provided
            if filing_year is None or engagement['filing_year'] == filing_year:
                engagements.append(engagement)
        
        return {
            'success': True,
            'engagements': engagements
        }
        
    except ClientError as e:
        logger.error(f"DynamoDB error fetching engagements: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching tax engagements: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{engagement_id}", response_model=Dict[str, Any])
async def get_tax_engagement(engagement_id: str) -> Dict[str, Any]:
    """
    Get a specific tax engagement by ID.
    
    Args:
        engagement_id: The engagement ID to fetch
    
    Returns:
        Dict with engagement details
    """
    settings = get_settings()
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        table = dynamodb.Table(settings.tax_engagements_table_name)
        
        # Get engagement by UUID (scan for engagement_id field)
        response = table.scan(
            FilterExpression='engagement_id = :engagement_id',
            ExpressionAttributeValues={
                ':engagement_id': engagement_id
            }
        )
        
        if not response.get('Items'):
            raise HTTPException(
                status_code=404,
                detail="Tax engagement not found"
            )
        
        item = response['Items'][0]  # Get first (and should be only) item
        engagement = {
            'engagement_id': item.get('engagement_id'),
            'user_id': item.get('user_id'),
            'filing_year': item.get('filing_year'),
            'status': item.get('status'),
            'created_at': item.get('created_at'),
            'updated_at': item.get('updated_at'),
            'folder_structure': item.get('folder_structure', {})
        }
        
        return {
            'success': True,
            'engagement': engagement
        }
        
    except ClientError as e:
        logger.error(f"DynamoDB error fetching engagement: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error fetching tax engagement: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
