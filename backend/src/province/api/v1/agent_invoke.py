"""
Agent Invoke API for LiveKit Edge Agent → AWS System Agent delegation.

This endpoint provides a simple proxy for LiveKit Edge Agents to delegate
reasoning and tool execution to AWS Bedrock AgentCore.
"""

import os
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from province.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/agent", tags=["agent-invoke"])

# Use the global legal agent service instance (agents are already registered)
from province.agents.agent_service import legal_agent_service


class AgentInvokeRequest(BaseModel):
    """Request model for LiveKit Edge Agent → AWS System Agent delegation."""
    tenant_id: Optional[str] = None
    matter_id: Optional[str] = None
    utterance: str
    room_id: Optional[str] = None
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    agent_name: Optional[str] = "legal_drafting"


class AgentInvokeResponse(BaseModel):
    """Response model for AWS System Agent → LiveKit Edge Agent."""
    text: str
    citations: List[Dict[str, Any]] = []
    actions: List[Dict[str, Any]] = []
    trace_id: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/invoke", response_model=AgentInvokeResponse)
async def invoke_agent(request: AgentInvokeRequest) -> AgentInvokeResponse:
    """
    Invoke AWS System Agent for LiveKit Edge Agent delegation.
    
    This endpoint:
    1. Receives utterance from LiveKit Edge Agent
    2. Creates or reuses AWS Bedrock Agent session
    3. Delegates reasoning/tool execution to AWS
    4. Returns normalized response for Edge Agent to speak
    
    Args:
        request: Agent invocation request with utterance and context
        
    Returns:
        Normalized response with text, citations, and actions
    """
    try:
        trace_id = request.trace_id or str(uuid.uuid4())
        
        logger.info(f"Agent invoke request - trace_id: {trace_id}, utterance: {request.utterance[:100]}...")
        
        # Debug: List available agents
        available_agents = list(legal_agent_service.agents.keys())
        logger.info(f"Available agents: {available_agents}")
        
        agent_name = request.agent_name or "legal_drafting"
        logger.info(f"Requested agent: {agent_name}")
        
        # Create or get session for this room/user
        session_key = f"livekit_{request.room_id}_{request.session_id}" if request.room_id and request.session_id else None
        
        # For now, create a new session for each request
        # In production, you'd want to maintain session state per room/user
        session = legal_agent_service.create_session(
            agent_name=agent_name
        )
        
        logger.info(f"Created session {session.session_id} for agent invoke - trace_id: {trace_id}")
        
        # Delegate to AWS System Agent
        agent_response = legal_agent_service.chat_with_agent(
            session_id=session.session_id,
            message=request.utterance,
            enable_trace=True
        )
        
        logger.info(f"Agent response received - trace_id: {trace_id}, response_length: {len(agent_response.response_text)}")
        
        # Convert to normalized format for LiveKit Edge Agent
        response = AgentInvokeResponse(
            text=agent_response.response_text,
            citations=[
                {
                    "path": citation.document_path,
                    "page": citation.page_number,
                    "snippet": citation.text_snippet
                }
                for citation in agent_response.citations
            ] if agent_response.citations else [],
            actions=[],  # Add any file save/action commands here
            trace_id=trace_id,
            session_id=session.session_id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in agent invoke - trace_id: {request.trace_id}, error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Agent invocation failed: {str(e)}"
        )


@router.get("/health")
async def agent_invoke_health():
    """Health check for agent invoke service."""
    return {
        "status": "ok",
        "service": "agent_invoke",
        "aws_configured": bool(os.getenv("AWS_ACCESS_KEY_ID")),
        "bedrock_region": os.getenv("AWS_REGION", "us-east-1")
    }
