"""
API endpoints for Legal Drafting Agent

This module provides REST API endpoints for legal document drafting
using the Bedrock-powered drafting agent.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from ...agents.drafting.drafting_agent import (
    LegalDraftingAgent, DraftingAgentRequest, DraftingAgentResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drafting", tags=["drafting"])

# Global drafting agent instance
drafting_agent = LegalDraftingAgent()


class DraftDocumentRequest(BaseModel):
    """Request model for document drafting"""
    document_type: str = Field(..., description="Type of document to draft (e.g., 'nda', 'employment_agreement')")
    context: Dict[str, Any] = Field(..., description="Context information for document generation")
    matter_id: Optional[str] = Field(None, description="Associated matter ID")
    jurisdiction: str = Field("federal", description="Legal jurisdiction")
    model_preference: Optional[str] = Field(None, description="Preferred Bedrock model")
    include_citations: bool = Field(True, description="Whether to include legal citations")
    validate_citations: bool = Field(True, description="Whether to validate citations")
    temperature: float = Field(0.1, ge=0.0, le=1.0, description="Model temperature for generation")
    max_tokens: int = Field(4000, ge=100, le=8000, description="Maximum tokens to generate")


class DraftDocumentResponse(BaseModel):
    """Response model for document drafting"""
    document_content: str
    document_type: str
    model_used: str
    confidence_score: float
    processing_time: float
    recommendations: List[str]
    generation_metadata: Dict[str, Any]
    citation_analysis: Optional[Dict[str, Any]] = None


class TemplatePreviewRequest(BaseModel):
    """Request model for template preview"""
    document_type: str
    context: Dict[str, Any]


class TemplatePreviewResponse(BaseModel):
    """Response model for template preview"""
    valid: bool
    system_prompt: Optional[str] = None
    user_prompt_preview: Optional[str] = None
    validation_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/draft", response_model=DraftDocumentResponse)
async def draft_document(request: DraftDocumentRequest):
    """
    Draft a legal document using the Bedrock-powered drafting agent
    
    This endpoint generates legal documents using AWS Bedrock models with
    specialized prompt templates and citation validation.
    """
    try:
        # Create drafting agent request
        agent_request = DraftingAgentRequest(
            document_type=request.document_type,
            context=request.context,
            matter_id=request.matter_id,
            jurisdiction=request.jurisdiction,
            model_preference=request.model_preference,
            include_citations=request.include_citations,
            validate_citations=request.validate_citations,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Draft the document
        response = drafting_agent.draft_document(agent_request)
        
        # Convert citation analysis to dict if present
        citation_analysis_dict = None
        if response.citation_analysis:
            citation_analysis_dict = {
                'total_citations': response.citation_analysis.validation_summary.get('total_citations', 0),
                'valid_citations': response.citation_analysis.validation_summary.get('valid_citations', 0),
                'invalid_citations': response.citation_analysis.validation_summary.get('invalid_citations', 0),
                'confidence_score': response.citation_analysis.confidence_score,
                'validation_notes': response.citation_analysis.validation_summary.get('validation_notes', [])
            }
        
        return DraftDocumentResponse(
            document_content=response.document_content,
            document_type=response.document_type,
            model_used=response.model_used,
            confidence_score=response.confidence_score,
            processing_time=response.processing_time,
            recommendations=response.recommendations,
            generation_metadata=response.generation_metadata,
            citation_analysis=citation_analysis_dict
        )
        
    except ValueError as e:
        logger.error(f"Validation error in document drafting: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in document drafting: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document drafting failed: {str(e)}")


@router.get("/document-types")
async def get_document_types():
    """
    Get list of available document types with their requirements
    
    Returns information about supported document types, including
    required and optional fields for each type.
    """
    try:
        document_types = drafting_agent.get_available_document_types()
        
        return {
            "document_types": document_types,
            "total_types": len(document_types)
        }
        
    except Exception as e:
        logger.error(f"Error getting document types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document-types/{document_type}")
async def get_document_type_info(document_type: str):
    """
    Get detailed information about a specific document type
    
    Returns template information, required fields, and example context
    for the specified document type.
    """
    try:
        # Get all document types and find the requested one
        document_types = drafting_agent.get_available_document_types()
        doc_info = next((dt for dt in document_types if dt['name'] == document_type), None)
        
        if not doc_info:
            raise HTTPException(status_code=404, detail=f"Document type '{document_type}' not found")
        
        # Get model recommendations
        model_recommendations = drafting_agent.get_model_recommendations(document_type)
        
        return {
            "document_type": doc_info,
            "model_recommendations": model_recommendations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document type info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview-template", response_model=TemplatePreviewResponse)
async def preview_template(request: TemplatePreviewRequest):
    """
    Preview how a template would be filled with given context
    
    This endpoint allows users to see how their context will be used
    to generate prompts before actually drafting a document.
    """
    try:
        preview_result = drafting_agent.preview_template(
            request.document_type, 
            request.context
        )
        
        if 'error' in preview_result:
            return TemplatePreviewResponse(
                valid=False,
                error=preview_result['error']
            )
        elif preview_result.get('valid', False):
            return TemplatePreviewResponse(
                valid=True,
                system_prompt=preview_result.get('system_prompt'),
                user_prompt_preview=preview_result.get('user_prompt_preview')
            )
        else:
            return TemplatePreviewResponse(
                valid=False,
                validation_result=preview_result.get('validation_result')
            )
        
    except Exception as e:
        logger.error(f"Error previewing template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_available_models():
    """
    Get list of available Bedrock models for document drafting
    
    Returns information about supported models and their capabilities.
    """
    try:
        from ...agents.drafting.bedrock_client import DraftingBedrockClient
        
        client = DraftingBedrockClient()
        models = client.list_available_models()
        
        return {
            "models": models,
            "total_models": len(models)
        }
        
    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{document_type}/recommendations")
async def get_model_recommendations(document_type: str):
    """
    Get model recommendations for a specific document type
    
    Returns recommended models with reasoning for the given document type.
    """
    try:
        recommendations = drafting_agent.get_model_recommendations(document_type)
        
        return {
            "document_type": document_type,
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"Error getting model recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-context")
async def validate_context(document_type: str, context: Dict[str, Any]):
    """
    Validate context for a document type without generating the document
    
    This endpoint checks if the provided context has all required fields
    for the specified document type.
    """
    try:
        from ...agents.drafting.prompt_templates import PromptTemplateManager, DocumentType
        
        template_manager = PromptTemplateManager()
        
        # Map document type string to enum
        doc_type_mapping = {
            'nda': DocumentType.NDA,
            'employment_agreement': DocumentType.EMPLOYMENT_AGREEMENT,
            'service_agreement': DocumentType.SERVICE_AGREEMENT,
            'legal_memo': DocumentType.LEGAL_MEMO
        }
        
        doc_type_key = document_type.lower().replace(' ', '_')
        if doc_type_key not in doc_type_mapping:
            raise HTTPException(status_code=400, detail=f"Unsupported document type: {document_type}")
        
        document_type_enum = doc_type_mapping[doc_type_key]
        validation_result = template_manager.validate_context(document_type_enum, context)
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def drafting_health_check():
    """
    Check the health of the drafting agent system
    
    Returns status information about the drafting agent and its dependencies.
    """
    try:
        # Test basic functionality
        document_types = drafting_agent.get_available_document_types()
        
        health_status = {
            "status": "healthy",
            "service": "Legal Drafting Agent",
            "bedrock_integration": "configured",
            "available_document_types": len(document_types),
            "template_manager": "operational",
            "citation_workflow": "operational"
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Drafting health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }