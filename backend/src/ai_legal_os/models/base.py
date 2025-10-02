"""Base models and common types."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid4())


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class BaseEntity(BaseModel):
    """Base entity with common fields."""
    
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


class MatterStatus(str, Enum):
    """Matter status enumeration."""
    
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"
    ON_HOLD = "on_hold"


class DocumentType(str, Enum):
    """Document type enumeration."""
    
    PLEADING = "pleading"
    DISCOVERY = "discovery"
    EVIDENCE = "evidence"
    CORRESPONDENCE = "correspondence"
    RESEARCH = "research"
    DEADLINE = "deadline"
    SETTLEMENT = "settlement"
    OTHER = "other"


class DeadlineStatus(str, Enum):
    """Deadline status enumeration."""
    
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    COMPLETED = "completed"
    OVERDUE = "overdue"