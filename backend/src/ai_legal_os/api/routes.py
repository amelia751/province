"""Main API router configuration."""

from fastapi import APIRouter

from ai_legal_os.api.v1 import health, matters, templates, documents

api_router = APIRouter()

# Include route modules
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(matters.router, prefix="/matters", tags=["matters"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

# Placeholder for future route modules
# api_router.include_router(agents.router, prefix="/agents", tags=["agents"])