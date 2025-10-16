"""
Tax Processing API Endpoints

Provides REST API endpoints for tax-related document processing,
including W2 ingestion using AWS Bedrock Data Automation.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...agents.tax.tools.ingest_documents import ingest_documents

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tax", tags=["tax"])


class IngestW2Request(BaseModel):
    """Request model for W2 ingestion."""
    s3_key: str = Field(..., description="S3 key of the W-2 document (PDF or JPEG)")
    taxpayer_name: str = Field(..., description="Name of the taxpayer for validation")
    tax_year: int = Field(..., description="Tax year for the W-2", ge=2000, le=2030)


class IngestW2Response(BaseModel):
    """Response model for W2 ingestion."""
    success: bool
    w2_extract: Optional[Dict[str, Any]] = Field(None, description="Extracted W2 data")
    validation_results: Optional[Dict[str, Any]] = Field(None, description="Validation results")
    forms_count: Optional[int] = Field(None, description="Number of W2 forms processed")
    total_wages: Optional[float] = Field(None, description="Total wages from all forms")
    total_withholding: Optional[float] = Field(None, description="Total withholding from all forms")
    processing_method: Optional[str] = Field(None, description="Processing method used")
    error: Optional[str] = Field(None, description="Error message if processing failed")


@router.post("/ingest-w2", response_model=IngestW2Response)
async def ingest_w2_endpoint(request: IngestW2Request) -> IngestW2Response:
    """
    Extract W-2 data from document using AWS Bedrock Data Automation.
    
    This endpoint processes W2 documents (PDF or image formats) and extracts
    structured tax data including employer information, employee information,
    and all W2 tax boxes with validation.
    
    Args:
        request: W2 ingestion request with S3 key, taxpayer name, and tax year
        
    Returns:
        Structured W2 data with validation results and processing metadata
    """
    try:
        logger.info(f"Processing W2 ingestion request for {request.s3_key}")
        
        # Call the ingest_documents function with W-2 type
        result = await ingest_documents(
            s3_key=request.s3_key,
            taxpayer_name=request.taxpayer_name,
            tax_year=request.tax_year,
            document_type='W-2'
        )
        
        # Convert the result to the response model
        response = IngestW2Response(
            success=result.get('success', False),
            w2_extract=result.get('w2_extract'),
            validation_results=result.get('validation_results'),
            forms_count=result.get('forms_count'),
            total_wages=result.get('total_wages'),
            total_withholding=result.get('total_withholding'),
            processing_method=result.get('processing_method'),
            error=result.get('error')
        )
        
        if result.get('success'):
            logger.info(f"Successfully processed W2: {request.s3_key} - {result.get('forms_count', 0)} forms")
        else:
            logger.error(f"Failed to process W2: {request.s3_key} - {result.get('error', 'Unknown error')}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in W2 ingestion endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"W2 processing failed: {str(e)}")


@router.get("/health")
async def tax_health_check():
    """Health check endpoint for tax processing services."""
    return {
        "status": "healthy",
        "service": "tax_processing",
        "features": [
            "w2_ingestion",
            "bedrock_data_automation"
        ]
    }
