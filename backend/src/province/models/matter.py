"""Matter-related data models."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field

from .base import BaseEntity, MatterStatus, generate_id


class MatterCreate(BaseModel):
    """Matter creation request."""
    
    title: str = Field(..., min_length=1, max_length=200, description="Matter title")
    matter_type: str = Field(..., description="Type of legal matter")
    jurisdiction: str = Field(..., description="Legal jurisdiction")
    description: Optional[str] = Field(None, max_length=1000, description="Matter description")
    client_name: Optional[str] = Field(None, max_length=100, description="Client name")
    opposing_party: Optional[str] = Field(None, max_length=100, description="Opposing party")
    template_id: Optional[str] = Field(None, description="Template to apply")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom matter fields")


class MatterUpdate(BaseModel):
    """Matter update request."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[MatterStatus] = None
    description: Optional[str] = Field(None, max_length=1000)
    client_name: Optional[str] = Field(None, max_length=100)
    opposing_party: Optional[str] = Field(None, max_length=100)
    custom_fields: Optional[Dict[str, Any]] = None


class Matter(BaseEntity):
    """Matter entity."""
    
    matter_id: str = Field(default_factory=generate_id, description="Unique matter identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    title: str = Field(..., description="Matter title")
    matter_type: str = Field(..., description="Type of legal matter")
    jurisdiction: str = Field(..., description="Legal jurisdiction")
    status: MatterStatus = Field(default=MatterStatus.ACTIVE, description="Matter status")
    description: Optional[str] = Field(None, description="Matter description")
    client_name: Optional[str] = Field(None, description="Client name")
    opposing_party: Optional[str] = Field(None, description="Opposing party")
    created_by: str = Field(..., description="User who created the matter")
    template_id: Optional[str] = Field(None, description="Applied template ID")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom matter fields")
    
    # Computed fields
    document_count: int = Field(default=0, description="Number of documents in matter")
    deadline_count: int = Field(default=0, description="Number of active deadlines")
    
    @computed_field
    @property
    def matter_number(self) -> str:
        """Generate a human-readable matter number."""
        # Format: MTR-YYYY-NNNN (e.g., MTR-2025-0001)
        year = self.created_at.year
        # Use last 8 chars of matter_id for uniqueness
        short_id = self.matter_id.replace("-", "")[-8:].upper()
        return f"MTR-{year}-{short_id[:4]}"


class MatterListResponse(BaseModel):
    """Response for matter list queries."""
    
    matters: List[Matter]
    total: int
    page: int
    page_size: int
    has_next: bool


class MatterFilters(BaseModel):
    """Filters for matter queries."""
    
    status: Optional[MatterStatus] = None
    matter_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    client_name: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    search: Optional[str] = Field(None, description="Search in title and description")


class MatterStats(BaseModel):
    """Matter statistics."""
    
    total_matters: int
    active_matters: int
    closed_matters: int
    matters_by_type: Dict[str, int]
    matters_by_status: Dict[str, int]
    recent_activity: List[Dict[str, Any]]