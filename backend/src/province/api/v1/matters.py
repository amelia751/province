"""Matter management API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from province.core.exceptions import NotFoundError, ValidationError
from province.models.matter import (
    Matter, MatterCreate, MatterUpdate, MatterFilters, 
    MatterListResponse, MatterStats, MatterStatus
)
from province.services.matter import MatterService

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

# Global service instances for testing
_matter_service = None

# Dependency to get matter service
def get_matter_service() -> MatterService:
    """Get matter service instance."""
    global _matter_service
    if _matter_service is None:
        from province.api.v1.templates import get_template_service
        template_service = get_template_service()
        _matter_service = MatterService(template_service=template_service)
    return _matter_service


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: str


@router.post("/", response_model=Matter, status_code=status.HTTP_201_CREATED)
async def create_matter(
    matter_data: MatterCreate,
    current_user: dict = Depends(get_current_user),
    matter_service: MatterService = Depends(get_matter_service)
):
    """Create a new matter."""
    try:
        matter = await matter_service.create_matter(
            matter_data, 
            current_user["user_id"], 
            current_user["tenant_id"]
        )
        return matter
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create matter: {str(e)}"
        )


@router.get("/", response_model=MatterListResponse)
async def list_matters(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    status: Optional[MatterStatus] = Query(None, description="Filter by status"),
    matter_type: Optional[str] = Query(None, description="Filter by matter type"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    current_user: dict = Depends(get_current_user),
    matter_service: MatterService = Depends(get_matter_service)
):
    """List matters for the current user."""
    try:
        filters = MatterFilters(
            status=status,
            matter_type=matter_type,
            jurisdiction=jurisdiction,
            search=search
        )
        
        matters = await matter_service.list_matters(
            current_user["user_id"],
            current_user["tenant_id"],
            filters,
            page,
            page_size
        )
        return matters
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list matters: {str(e)}"
        )


@router.get("/stats", response_model=MatterStats)
async def get_matter_stats(
    current_user: dict = Depends(get_current_user),
    matter_service: MatterService = Depends(get_matter_service)
):
    """Get matter statistics for the current user."""
    try:
        stats = await matter_service.get_matter_stats(
            current_user["user_id"],
            current_user["tenant_id"]
        )
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get matter stats: {str(e)}"
        )


@router.get("/search", response_model=MatterListResponse)
async def search_matters(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: dict = Depends(get_current_user),
    matter_service: MatterService = Depends(get_matter_service)
):
    """Search matters by query."""
    try:
        matters = await matter_service.search_matters(
            q,
            current_user["user_id"],
            current_user["tenant_id"],
            page,
            page_size
        )
        return matters
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search matters: {str(e)}"
        )


@router.get("/{matter_id}", response_model=Matter)
async def get_matter(
    matter_id: str,
    current_user: dict = Depends(get_current_user),
    matter_service: MatterService = Depends(get_matter_service)
):
    """Get a matter by ID."""
    try:
        matter = await matter_service.get_matter(
            matter_id,
            current_user["user_id"],
            current_user["tenant_id"]
        )
        return matter
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get matter: {str(e)}"
        )


@router.put("/{matter_id}", response_model=Matter)
async def update_matter(
    matter_id: str,
    updates: MatterUpdate,
    current_user: dict = Depends(get_current_user),
    matter_service: MatterService = Depends(get_matter_service)
):
    """Update a matter."""
    try:
        matter = await matter_service.update_matter(
            matter_id,
            updates,
            current_user["user_id"],
            current_user["tenant_id"]
        )
        return matter
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
            detail=f"Failed to update matter: {str(e)}"
        )


@router.delete("/{matter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_matter(
    matter_id: str,
    current_user: dict = Depends(get_current_user),
    matter_service: MatterService = Depends(get_matter_service)
):
    """Delete a matter."""
    try:
        deleted = await matter_service.delete_matter(
            matter_id,
            current_user["user_id"],
            current_user["tenant_id"]
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Matter not found"
            )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete matter: {str(e)}"
        )