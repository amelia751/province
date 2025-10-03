"""Health check endpoints."""

from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel

from province.core.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str
    timestamp: datetime
    version: str
    environment: str


class DetailedHealthResponse(BaseModel):
    """Detailed health check response model."""
    
    status: str
    timestamp: datetime
    version: str
    environment: str
    services: Dict[str, Any]


@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    settings = get_settings()
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version="0.1.0",
        environment=settings.environment,
    )


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check() -> DetailedHealthResponse:
    """Detailed health check with service status."""
    settings = get_settings()
    
    # TODO: Add actual service health checks in future tasks
    services = {
        "database": {"status": "not_configured", "message": "DynamoDB not yet configured"},
        "storage": {"status": "not_configured", "message": "S3 not yet configured"},
        "search": {"status": "not_configured", "message": "OpenSearch not yet configured"},
        "auth": {"status": "not_configured", "message": "Cognito not yet configured"},
        "ai": {"status": "not_configured", "message": "Bedrock not yet configured"},
    }
    
    return DetailedHealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version="0.1.0",
        environment=settings.environment,
        services=services,
    )