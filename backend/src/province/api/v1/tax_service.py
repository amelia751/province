"""
Tax Service API endpoints using Strands SDK

Provides REST API for conversational tax filing flow.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging

from ...services.tax_service import tax_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tax-service", tags=["tax-service"])


class StartConversationRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Optional session ID")


class StartConversationResponse(BaseModel):
    session_id: str
    message: str
    available_w2s: List[str] = Field(default_factory=list)


class ContinueConversationRequest(BaseModel):
    session_id: str
    user_message: str


class ContinueConversationResponse(BaseModel):
    session_id: str
    agent_response: str
    conversation_state: Dict[str, Any] = Field(default_factory=dict)


class ConversationStateResponse(BaseModel):
    session_id: str
    state: Dict[str, Any]


@router.post("/start", response_model=StartConversationResponse)
async def start_tax_conversation(request: StartConversationRequest):
    """
    Start a new tax filing conversation.
    
    Returns initial greeting and available W2 documents.
    """
    try:
        logger.info(f"Starting tax conversation with session_id: {request.session_id}")
        
        # Start conversation
        initial_message = await tax_service.start_conversation(request.session_id)
        
        # Get session ID (generated if not provided)
        from ...services.tax_service import conversation_state
        session_id = conversation_state.get('current_session_id')
        
        # List available W2s for demo
        available_w2s = await tax_service.list_available_w2s()
        
        return StartConversationResponse(
            session_id=session_id,
            message=initial_message,
            available_w2s=available_w2s
        )
        
    except Exception as e:
        logger.error(f"Error starting tax conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {str(e)}")


@router.post("/continue", response_model=ContinueConversationResponse)
async def continue_tax_conversation(request: ContinueConversationRequest):
    """
    Continue an existing tax filing conversation.
    
    Processes user input and returns agent response.
    """
    try:
        logger.info(f"Continuing conversation {request.session_id} with message: {request.user_message[:100]}...")
        
        # Continue conversation
        agent_response = await tax_service.continue_conversation(
            user_message=request.user_message,
            session_id=request.session_id
        )
        
        # Get updated conversation state
        conversation_state = tax_service.get_conversation_state(request.session_id)
        
        return ContinueConversationResponse(
            session_id=request.session_id,
            agent_response=agent_response,
            conversation_state=conversation_state
        )
        
    except Exception as e:
        logger.error(f"Error continuing conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to continue conversation: {str(e)}")


@router.get("/state/{session_id}", response_model=ConversationStateResponse)
async def get_conversation_state(session_id: str):
    """
    Get current conversation state for a session.
    """
    try:
        state = tax_service.get_conversation_state(session_id)
        
        return ConversationStateResponse(
            session_id=session_id,
            state=state
        )
        
    except Exception as e:
        logger.error(f"Error getting conversation state: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation state: {str(e)}")


@router.get("/w2s", response_model=List[str])
async def list_available_w2s():
    """
    List available W2 documents in the system.
    """
    try:
        w2_files = await tax_service.list_available_w2s()
        return w2_files
        
    except Exception as e:
        logger.error(f"Error listing W2s: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list W2s: {str(e)}")


@router.delete("/session/{session_id}")
async def clear_conversation_session(session_id: str):
    """
    Clear conversation session data.
    """
    try:
        if session_id in tax_service.conversation_state:
            del tax_service.conversation_state[session_id]
        
        return {"message": f"Session {session_id} cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")
