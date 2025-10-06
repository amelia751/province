"""Main API router configuration."""

from fastapi import APIRouter

from province.api.v1 import health, matters, templates, documents, agents, drafting, deadlines, evidence, websocket, livekit, agent_invoke

api_router = APIRouter()

# Include route modules
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(matters.router, prefix="/matters", tags=["matters"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

api_router.include_router(agents.router, tags=["agents"])
api_router.include_router(drafting.router, tags=["drafting"])
api_router.include_router(deadlines.router, tags=["deadlines"])
api_router.include_router(evidence.router, tags=["evidence"])
api_router.include_router(websocket.router, tags=["websocket"])
api_router.include_router(livekit.router, tags=["livekit"])
api_router.include_router(agent_invoke.router, tags=["agent-invoke"])