"""Document-related data models."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .base import BaseEntity


class DocumentVersion(BaseModel):
    """Document version information."""
    
    version: str = Field(..., description="Version identifier")
    s3_key: str = Field(..., description="S3 key for this version")
    size: int = Field(..., description="File size in bytes")
    created_by: str = Field(..., description="User who created this version")
    created_at: datetime = Field(..., description="Version creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Version-specific metadata")


class Document(BaseEntity):
    """Document model."""
    
    document_id: str = Field(..., description="Unique document identifier")
    matter_id: str = Field(..., description="Associated matter ID")
    path: str = Field(..., description="Document path within matter")
    filename: str = Field(..., description="Original filename")
    mime_type: str = Field(..., description="MIME type of the document")
    size: int = Field(..., description="Current file size in bytes")
    version: str = Field(..., description="Current version identifier")
    created_by: str = Field(..., description="User who created the document")
    s3_key: str = Field(..., description="Current S3 key")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    
    # Versioning
    versions: List[DocumentVersion] = Field(default_factory=list, description="Document version history")
    
    # Search and indexing
    indexed: bool = Field(default=False, description="Whether document is indexed for search")
    content_hash: Optional[str] = Field(None, description="Content hash for deduplication")
    
    # Collaboration
    locked_by: Optional[str] = Field(None, description="User ID if document is locked for editing")
    locked_at: Optional[datetime] = Field(None, description="When document was locked")


class DocumentCreate(BaseModel):
    """Document creation request."""
    
    path: str = Field(..., min_length=1, description="Document path within matter")
    filename: str = Field(..., min_length=1, description="Original filename")
    mime_type: str = Field(..., description="MIME type of the document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")


class DocumentUpdate(BaseModel):
    """Document update request."""
    
    filename: Optional[str] = Field(None, description="Updated filename")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")


class DocumentUpload(BaseModel):
    """Document upload response."""
    
    document_id: str = Field(..., description="Document ID")
    upload_url: str = Field(..., description="Pre-signed S3 upload URL")
    fields: Dict[str, str] = Field(..., description="Required form fields for upload")


class DocumentDownload(BaseModel):
    """Document download response."""
    
    document_id: str = Field(..., description="Document ID")
    download_url: str = Field(..., description="Pre-signed S3 download URL")
    filename: str = Field(..., description="Original filename")
    mime_type: str = Field(..., description="MIME type")
    size: int = Field(..., description="File size in bytes")


class DocumentListResponse(BaseModel):
    """Response for document list queries."""
    
    documents: List[Document]
    total: int
    folder: Optional[str] = None


class DocumentSearchResult(BaseModel):
    """Document search result."""
    
    document: Document
    score: float = Field(..., description="Search relevance score")
    highlights: List[str] = Field(default_factory=list, description="Text highlights")
    page_matches: List[int] = Field(default_factory=list, description="Matching page numbers")


class DocumentSearchResponse(BaseModel):
    """Document search response."""
    
    results: List[DocumentSearchResult]
    total: int
    query: str
    took_ms: int = Field(..., description="Search time in milliseconds")