"""Document management API endpoints."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from province.agents.tax.tools.save_document import save_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


class SaveDocumentRequest(BaseModel):
    """Request model for saving documents."""
    engagement_id: str
    path: str
    content_b64: str
    mime_type: str


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
