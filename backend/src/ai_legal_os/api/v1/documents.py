"""Document management API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Form, File, UploadFile
from pydantic import BaseModel

from ai_legal_os.core.exceptions import NotFoundError, ValidationError, ConflictError
from ai_legal_os.models.document import (
    Document, DocumentCreate, DocumentUpdate, DocumentUpload, 
    DocumentDownload, DocumentListResponse, DocumentVersion
)
from ai_legal_os.services.document import DocumentService


class DocumentFinalizeRequest(BaseModel):
    """Request model for finalizing document upload."""
    file_size: int
    content_hash: Optional[str] = None


class DocumentLockResponse(BaseModel):
    """Response model for document lock operations."""
    success: bool
    message: str


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
_document_service = None
_document_repo = None

# Dependency to get document service
def get_document_service() -> DocumentService:
    """Get document service instance."""
    global _document_service, _document_repo
    if _document_service is None:
        if _document_repo is None:
            from ai_legal_os.repositories.document import DocumentRepository
            _document_repo = DocumentRepository()
        _document_service = DocumentService(_document_repo)
    return _document_service


@router.post("/", response_model=DocumentUpload, status_code=status.HTTP_201_CREATED)
async def create_document(
    matter_id: str = Query(..., description="Matter ID"),
    document_data: DocumentCreate = ...,
    current_user: dict = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    """Create a new document and get upload URL."""
    try:
        upload_info = await document_service.create_document(
            matter_id,
            document_data,
            current_user["user_id"]
        )
        return upload_info
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
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
            detail=f"Failed to create document: {str(e)}"
        )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    matter_id: str = Query(..., description="Matter ID"),
    folder: Optional[str] = Query(None, description="Folder path to filter by"),
    current_user: dict = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    """List documents in a matter."""
    try:
        documents = await document_service.list_documents(
            matter_id,
            folder,
            current_user["user_id"]
        )
        return documents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/search", response_model=List[Document])
async def search_documents(
    matter_id: str = Query(..., description="Matter ID"),
    query: str = Query(..., description="Search query"),
    limit: int = Query(50, description="Maximum number of results"),
    current_user: dict = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    """Search documents by content."""
    try:
        documents = await document_service.search_documents(
            matter_id,
            query,
            current_user["user_id"],
            limit
        )
        return documents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    """Get a document by ID."""
    try:
        document = await document_service.get_document(document_id, current_user["user_id"])
        return document
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )


@router.put("/{document_id}", response_model=Document)
async def update_document(
    document_id: str,
    update_data: DocumentUpdate,
    current_user: dict = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    """Update document metadata."""
    try:
        document = await document_service.update_document(
            document_id,
            update_data,
            current_user["user_id"]
        )
        return document
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
            detail=f"Failed to update document: {str(e)}"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    """Delete a document."""
    try:
        success = await document_service.delete_document(document_id, current_user["user_id"])
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document"
            )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/{document_id}/download", response_model=DocumentDownload)
async def get_download_url(
    document_id: str,
    version: Optional[str] = Query(None, description="Specific version to download"),
    current_user: dict = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    """Get download URL for a document."""
    try:
        download_info = await document_service.get_download_url(
            document_id,
            current_user["user_id"],
            version
        )
        return download_info
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
            detail=f"Failed to get download URL: {str(e)}"
        )


@router.post("/{document_id}/versions", response_model=DocumentUpload)
async def create_new_version(
    document_id: str,
    mime_type: Optional[str] = Query(None, description="MIME type for new version"),
    current_user: dict = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    """Create a new version of an existing document."""
    try:
        upload_info = await document_service.upload_new_version(
            document_id,
            current_user["user_id"],
            mime_type
        )
        return upload_info
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
            detail=f"Failed to create new version: {str(e)}"
        )


@router.get("/{document_id}/versions", response_model=List[DocumentVersion])
async def get_document_versions(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    """Get all versions of a document."""
    try:
        versions = await document_service.get_document_versions(
            document_id,
            current_user["user_id"]
        )
        return versions
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document versions: {str(e)}"
        )


@router.post("/{document_id}/finalize", response_model=Document)
async def finalize_upload(
    document_id: str,
    finalize_data: DocumentFinalizeRequest,
    current_user: dict = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    """Finalize document upload by updating size and metadata."""
    try:
        document = await document_service.finalize_upload(
            document_id,
            current_user["user_id"],
            finalize_data.file_size,
            finalize_data.content_hash
        )
        return document
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
            detail=f"Failed to finalize upload: {str(e)}"
        )


@router.post("/{document_id}/lock", response_model=DocumentLockResponse)
async def lock_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    """Lock a document for editing."""
    try:
        success = await document_service.lock_document(document_id, current_user["user_id"])
        return DocumentLockResponse(
            success=success,
            message="Document locked successfully" if success else "Document is already locked"
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to lock document: {str(e)}"
        )


@router.delete("/{document_id}/lock", response_model=DocumentLockResponse)
async def unlock_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    """Unlock a document."""
    try:
        success = await document_service.unlock_document(document_id, current_user["user_id"])
        return DocumentLockResponse(
            success=success,
            message="Document unlocked successfully" if success else "Document was not locked by you"
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unlock document: {str(e)}"
        )