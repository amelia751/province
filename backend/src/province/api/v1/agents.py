"""
Unified Agent API endpoints for the AI Legal OS

This module provides REST API endpoints for interacting with AWS Bedrock Agents.
Uses AWS managed AgentCore with support for matter context, session management,
and comprehensive agent operations.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging

from ...agents.agent_service import legal_agent_service
from ...agents.bedrock_agent_client import AgentSession, AgentResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    agent_name: str = "legal_drafting"
    matter_id: Optional[str] = None
    enable_trace: bool = False


class ChatResponse(BaseModel):
    response: str
    session_id: str
    agent_name: str
    matter_id: Optional[str] = None
    citations: List[Dict[str, Any]] = []
    trace: Optional[Dict[str, Any]] = None


class SessionRequest(BaseModel):
    agent_name: str = "legal_drafting"
    matter_id: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Send a message to a Bedrock Agent and get a response.
    
    This uses AWS's managed AgentCore orchestrator with support for matter context.
    """
    try:
        # Create session if not provided
        if not request.session_id:
            session = legal_agent_service.create_session(
                agent_name=request.agent_name,
                matter_id=request.matter_id
            )
            session_id = session.session_id
        else:
            session_id = request.session_id
        
        # Chat with agent using AWS managed service
        response = legal_agent_service.chat_with_agent(
            session_id=session_id,
            message=request.message,
            matter_id=request.matter_id,
            enable_trace=request.enable_trace
        )
        
        return ChatResponse(
            response=response.response_text,
            session_id=response.session_id,
            agent_name=request.agent_name,
            matter_id=request.matter_id,
            citations=response.citations,
            trace=response.trace
        )
        
    except Exception as e:
        logger.error(f"Error in agent chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions", response_model=Dict[str, str])
async def create_session(request: SessionRequest):
    """
    Create a new Bedrock Agent session with optional matter context.
    """
    try:
        session = legal_agent_service.create_session(
            agent_name=request.agent_name,
            matter_id=request.matter_id
        )
        
        return {
            "session_id": session.session_id,
            "agent_name": request.agent_name,
            "agent_id": session.agent_id,
            "matter_id": request.matter_id,
            "status": "created"
        }
        
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Get information about a Bedrock Agent session.
    """
    try:
        sessions = legal_agent_service.list_active_sessions()
        session = next((s for s in sessions if s.session_id == session_id), None)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
            
        return {
            "session_id": session.session_id,
            "agent_id": session.agent_id,
            "agent_alias_id": session.agent_alias_id,
            "created_at": session.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Close a Bedrock Agent session.
    """
    try:
        legal_agent_service.close_session(session_id)
        return {"status": "closed"}
        
    except Exception as e:
        logger.error(f"Error closing session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def list_agents():
    """
    List all available Bedrock Agents.
    """
    try:
        agents = []
        for agent_name, config in legal_agent_service.agents.items():
            agents.append({
                "name": agent_name,
                "agent_id": config.agent_id,
                "description": config.description,
                "foundation_model": config.foundation_model,
                "knowledge_bases": config.knowledge_bases,
                "action_groups": config.action_groups
            })
            
        return {"agents": agents}
        
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_name}")
async def get_agent_info(agent_name: str):
    """
    Get detailed information about a specific Bedrock Agent.
    """
    try:
        agent_info = legal_agent_service.get_agent_info(agent_name)
        return agent_info
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting agent info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/cleanup")
async def cleanup_expired_sessions(max_idle_minutes: int = 30):
    """
    Clean up expired agent sessions.
    """
    try:
        cleaned_count = legal_agent_service.cleanup_expired_sessions(max_idle_minutes)
        
        return {
            "message": f"Cleaned up {cleaned_count} expired sessions",
            "cleaned_sessions": cleaned_count
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_agent_stats():
    """
    Get agent system statistics.
    """
    try:
        active_sessions = legal_agent_service.list_active_sessions()
        
        stats = {
            "active_sessions": len(active_sessions),
            "registered_agents": len(legal_agent_service.agents),
            "agent_names": list(legal_agent_service.agents.keys())
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting agent stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def agent_health_check():
    """
    Check the health of the Bedrock Agent system.
    """
    try:
        active_sessions = legal_agent_service.list_active_sessions()
        
        health_status = {
            "status": "healthy",
            "service": "AWS Bedrock Agents (Managed)",
            "orchestrator": "AWS AgentCore",
            "active_sessions": len(active_sessions),
            "registered_agents": len(legal_agent_service.agents),
            "bedrock_connection": "ok"
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Agent health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }