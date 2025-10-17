"""Main API router configuration."""

from fastapi import APIRouter

from province.api.v1 import health, agents, websocket, livekit, agent_invoke, tax, form_filler, tax_service, documents, tax_engagements

api_router = APIRouter()

# Include route modules
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(agents.router, tags=["agents"])
api_router.include_router(websocket.router, tags=["websocket"])
api_router.include_router(livekit.router, tags=["livekit"])
api_router.include_router(agent_invoke.router, tags=["agent-invoke"])
api_router.include_router(tax.router, tags=["tax"])
api_router.include_router(form_filler.router, tags=["form-filler"])
api_router.include_router(tax_service.router, tags=["tax-service"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(tax_engagements.router, tags=["tax-engagements"])