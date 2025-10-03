"""Template-related data models."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .base import BaseEntity


class FolderStructure(BaseModel):
    """Folder structure definition."""
    
    name: str = Field(..., description="Folder name")
    subfolders: List[str] = Field(default_factory=list, description="Subfolder names")


class StarterDocument(BaseModel):
    """Starter document definition."""
    
    path: str = Field(..., description="Document path within matter")
    generator: Optional[str] = Field(None, description="Generator function name")
    auto_generate: bool = Field(default=False, description="Auto-generate on matter creation")
    template_content: Optional[str] = Field(None, description="Static template content")


class DeadlineRule(BaseModel):
    """Deadline computation rule."""
    
    name: str = Field(..., description="Deadline name")
    compute: Dict[str, Any] = Field(..., description="Computation rules")
    reminders: List[str] = Field(default_factory=list, description="Reminder schedule")
    required: bool = Field(default=True, description="Whether deadline is required")


class AgentConfig(BaseModel):
    """Agent configuration for template."""
    
    name: str = Field(..., description="Agent name")
    skills: List[str] = Field(default_factory=list, description="Agent skills")
    enabled: bool = Field(default=True, description="Whether agent is enabled")


class GuardrailConfig(BaseModel):
    """Guardrail configuration."""
    
    required_citations: bool = Field(default=False)
    pii_scan_before_share: bool = Field(default=True)
    privilege_review_required: bool = Field(default=False)
    auto_redaction: bool = Field(default=False)


class Template(BaseEntity):
    """Matter template."""
    
    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    version: str = Field(default="1.0.0", description="Template version")
    applies_to: Dict[str, List[str]] = Field(default_factory=dict, description="Applicability rules")
    
    # Structure definition
    folders: List[FolderStructure] = Field(default_factory=list, description="Folder structure")
    starter_docs: List[StarterDocument] = Field(default_factory=list, description="Starter documents")
    deadlines: List[DeadlineRule] = Field(default_factory=list, description="Deadline rules")
    
    # Agent configuration
    agents: List[AgentConfig] = Field(default_factory=list, description="Agent configurations")
    guardrails: GuardrailConfig = Field(default_factory=GuardrailConfig, description="Guardrail settings")
    
    # Metadata
    created_by: str = Field(..., description="Template creator")
    is_active: bool = Field(default=True, description="Whether template is active")
    usage_count: int = Field(default=0, description="Number of times used")


class TemplateCreate(BaseModel):
    """Template creation request."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    applies_to: Dict[str, List[str]] = Field(default_factory=dict)
    folders: List[FolderStructure] = Field(default_factory=list)
    starter_docs: List[StarterDocument] = Field(default_factory=list)
    deadlines: List[DeadlineRule] = Field(default_factory=list)
    agents: List[AgentConfig] = Field(default_factory=list)
    guardrails: GuardrailConfig = Field(default_factory=GuardrailConfig)


class TemplateListResponse(BaseModel):
    """Response for template list queries."""
    
    templates: List[Template]
    total: int