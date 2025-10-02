"""Template management API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from pydantic import BaseModel, Field

from ai_legal_os.core.exceptions import NotFoundError, ValidationError
from ai_legal_os.models.template import Template, TemplateCreate, TemplateListResponse
from ai_legal_os.services.template import TemplateService
from ai_legal_os.services.ai_template_generator import AITemplateGenerator


class TemplateYAMLRequest(BaseModel):
    """Request model for YAML template creation."""
    yaml_content: str


class TemplateValidationResponse(BaseModel):
    """Response model for template validation."""
    valid: bool
    errors: List[str]


class TemplateYAMLResponse(BaseModel):
    """Response model for YAML export."""
    yaml_content: str


class AITemplateGenerationRequest(BaseModel):
    """Request model for AI template generation."""
    description: str = Field(..., min_length=10, max_length=2000, description="Description of the legal matter type")
    practice_area: str = Field(..., min_length=2, max_length=100, description="Practice area (e.g., litigation, corporate, family)")
    matter_type: str = Field(..., min_length=2, max_length=100, description="Specific matter type (e.g., personal injury, contract dispute)")
    jurisdiction: str = Field(..., min_length=2, max_length=50, description="Jurisdiction (e.g., US-CA, US-NY, UK)")
    additional_context: Optional[str] = Field(None, max_length=1000, description="Additional context or requirements")


class TemplateEnhancementRequest(BaseModel):
    """Request model for template enhancement."""
    enhancement_request: str = Field(..., min_length=10, max_length=1000, description="Specific enhancement or modification request")


class TemplateAnalysisResponse(BaseModel):
    """Response model for template analysis."""
    suggestions: List[str] = Field(..., description="List of improvement suggestions")

router = APIRouter()

# Dependency to get current user (mock for now)
async def get_current_user() -> dict:
    """Get current user from authentication context."""
    # TODO: Implement actual authentication
    return {
        "user_id": "user_123",
        "tenant_id": "tenant_456",
        "email": "user@example.com"
    }

# Global service instance for testing
_template_service = None
_template_repo = None

# Global service instances for testing
_ai_generator = None

# Dependency to get template service
def get_template_service() -> TemplateService:
    """Get template service instance."""
    global _template_service, _template_repo
    if _template_service is None:
        if _template_repo is None:
            from ai_legal_os.repositories.template import TemplateRepository
            _template_repo = TemplateRepository()
        _template_service = TemplateService(_template_repo)
    return _template_service


# Dependency to get AI template generator
def get_ai_template_generator() -> AITemplateGenerator:
    """Get AI template generator instance."""
    global _ai_generator
    if _ai_generator is None:
        _ai_generator = AITemplateGenerator()
    return _ai_generator


@router.post("/", response_model=Template, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    current_user: dict = Depends(get_current_user),
    template_service: TemplateService = Depends(get_template_service)
):
    """Create a new template."""
    try:
        template = await template_service.create_template(
            template_data,
            current_user["user_id"]
        )
        return template
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )


@router.get("/", response_model=TemplateListResponse)
async def list_templates(
    template_service: TemplateService = Depends(get_template_service)
):
    """List all active templates."""
    try:
        templates = await template_service.list_templates()
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}"
        )


@router.get("/recommendations", response_model=List[Template])
async def get_recommended_templates(
    matter_type: str = Query(..., description="Matter type"),
    jurisdiction: str = Query(..., description="Jurisdiction"),
    template_service: TemplateService = Depends(get_template_service)
):
    """Get recommended templates for a matter type and jurisdiction."""
    try:
        templates = await template_service.get_recommended_templates(
            matter_type,
            jurisdiction
        )
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommended templates: {str(e)}"
        )


@router.post("/from-yaml", response_model=Template, status_code=status.HTTP_201_CREATED)
async def create_template_from_yaml(
    request: TemplateYAMLRequest,
    current_user: dict = Depends(get_current_user),
    template_service: TemplateService = Depends(get_template_service)
):
    """Create a template from YAML definition."""
    try:
        template = await template_service.create_template_from_yaml(
            request.yaml_content,
            current_user["user_id"]
        )
        return template
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template from YAML: {str(e)}"
        )


@router.post("/validate-yaml", response_model=TemplateValidationResponse)
async def validate_template_yaml(
    request: TemplateYAMLRequest,
    template_service: TemplateService = Depends(get_template_service)
):
    """Validate YAML template definition."""
    try:
        errors = await template_service.validate_template_yaml(request.yaml_content)
        return TemplateValidationResponse(
            valid=len(errors) == 0,
            errors=errors
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate template YAML: {str(e)}"
        )


@router.get("/{template_id}", response_model=Template)
async def get_template(
    template_id: str,
    template_service: TemplateService = Depends(get_template_service)
):
    """Get a template by ID."""
    try:
        template = await template_service.get_template(template_id)
        return template
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template: {str(e)}"
        )


@router.get("/{template_id}/yaml", response_model=TemplateYAMLResponse)
async def export_template_to_yaml(
    template_id: str,
    template_service: TemplateService = Depends(get_template_service)
):
    """Export template to YAML format."""
    try:
        yaml_content = await template_service.export_template_to_yaml(template_id)
        return TemplateYAMLResponse(yaml_content=yaml_content)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export template to YAML: {str(e)}"
        )


@router.post("/generate-ai", response_model=Template, status_code=status.HTTP_201_CREATED)
async def generate_template_with_ai(
    request: AITemplateGenerationRequest,
    current_user: dict = Depends(get_current_user),
    ai_generator: AITemplateGenerator = Depends(get_ai_template_generator),
    template_service: TemplateService = Depends(get_template_service)
):
    """Generate a new template using AI based on natural language description."""
    try:
        # Generate template using AI
        template = await ai_generator.generate_template_from_description(
            description=request.description,
            practice_area=request.practice_area,
            matter_type=request.matter_type,
            jurisdiction=request.jurisdiction,
            user_id=current_user["user_id"],
            additional_context=request.additional_context
        )
        
        # Save the generated template
        saved_template = await template_service.create_template(
            TemplateCreate(
                name=template.name,
                description=template.description,
                applies_to=template.applies_to,
                folders=template.folders,
                starter_docs=template.starter_docs,
                deadlines=template.deadlines,
                agents=template.agents,
                guardrails=template.guardrails
            ),
            current_user["user_id"]
        )
        
        return saved_template
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate template with AI: {str(e)}"
        )


@router.post("/{template_id}/enhance-ai", response_model=Template)
async def enhance_template_with_ai(
    template_id: str,
    request: TemplateEnhancementRequest,
    current_user: dict = Depends(get_current_user),
    ai_generator: AITemplateGenerator = Depends(get_ai_template_generator),
    template_service: TemplateService = Depends(get_template_service)
):
    """Enhance an existing template using AI based on user feedback."""
    try:
        # Get the existing template
        existing_template = await template_service.get_template(template_id)
        
        # Enhance using AI
        enhanced_template = await ai_generator.enhance_existing_template(
            template=existing_template,
            enhancement_request=request.enhancement_request,
            user_id=current_user["user_id"]
        )
        
        # Update the template
        updated_template = await template_service.update_template(
            template_id=template_id,
            template_data=TemplateCreate(
                name=enhanced_template.name,
                description=enhanced_template.description,
                applies_to=enhanced_template.applies_to,
                folders=enhanced_template.folders,
                starter_docs=enhanced_template.starter_docs,
                deadlines=enhanced_template.deadlines,
                agents=enhanced_template.agents,
                guardrails=enhanced_template.guardrails
            ),
            user_id=current_user["user_id"]
        )
        
        return updated_template
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enhance template with AI: {str(e)}"
        )


@router.get("/{template_id}/analyze-ai", response_model=TemplateAnalysisResponse)
async def analyze_template_with_ai(
    template_id: str,
    current_user: dict = Depends(get_current_user),
    ai_generator: AITemplateGenerator = Depends(get_ai_template_generator),
    template_service: TemplateService = Depends(get_template_service)
):
    """Analyze a template and get AI-powered improvement suggestions."""
    try:
        # Get the template
        template = await template_service.get_template(template_id)
        
        # Analyze using AI
        suggestions = await ai_generator.suggest_template_improvements(
            template=template,
            usage_analytics={"usage_count": template.usage_count}
        )
        
        return TemplateAnalysisResponse(suggestions=suggestions)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze template with AI: {str(e)}"
        )