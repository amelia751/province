"""
WebSocket API endpoints for real-time collaboration

Handles WebSocket connection lifecycle and message routing for
collaborative document editing features.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ...core.config import get_settings
from ...core.exceptions import ValidationError, PermissionError
from ...services.websocket_service import websocket_service, MessageType

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/ws", tags=["websocket"])


class WebSocketConnectionInfo(BaseModel):
    """WebSocket connection information"""
    connection_id: str
    user_id: str
    matter_id: Optional[str] = None
    connected_at: datetime
    status: str


class DocumentSessionInfo(BaseModel):
    """Document session information"""
    document_id: str
    matter_id: str
    active_users_count: int
    active_users: list
    document_version: str
    last_sync: datetime
    lock_holder: Optional[str] = None
    lock_expires: Optional[datetime] = None


class WebSocketMessage(BaseModel):
    """WebSocket message structure"""
    type: str
    payload: Dict[str, Any]
    user_id: Optional[str] = None
    timestamp: Optional[datetime] = None


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(..., description="User ID"),
    matter_id: str = Query(None, description="Matter ID (optional)")
):
    """
    WebSocket endpoint for real-time collaboration
    
    Handles the WebSocket connection lifecycle and message routing
    for collaborative document editing.
    """
    connection_id = None
    
    try:
        # Accept WebSocket connection
        await websocket.accept()
        
        # Generate connection ID (in real implementation, this would come from API Gateway)
        import uuid
        connection_id = str(uuid.uuid4())
        
        logger.info(f"WebSocket connection accepted: {connection_id} for user {user_id}")
        
        # Register connection with WebSocket service
        success = await websocket_service.handle_connection(connection_id, user_id, matter_id)
        
        if not success:
            await websocket.close(code=1011, reason="Failed to register connection")
            return
        
        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Route message based on type
                await handle_websocket_message(connection_id, message_data, websocket)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {connection_id}")
                break
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received from {connection_id}: {e}")
                await send_error_to_websocket(websocket, "Invalid JSON format")
            except Exception as e:
                logger.error(f"Error handling WebSocket message from {connection_id}: {e}")
                await send_error_to_websocket(websocket, f"Message handling error: {str(e)}")
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        # Clean up connection
        if connection_id:
            await websocket_service.handle_disconnection(connection_id)


async def handle_websocket_message(connection_id: str, message_data: Dict[str, Any], websocket: WebSocket):
    """Handle incoming WebSocket message"""
    try:
        message_type = message_data.get('type')
        payload = message_data.get('payload', {})
        
        logger.debug(f"Handling WebSocket message: {message_type} from {connection_id}")
        
        if message_type == MessageType.JOIN_DOCUMENT.value:
            document_id = payload.get('document_id')
            matter_id = payload.get('matter_id')
            
            if not document_id or not matter_id:
                await send_error_to_websocket(websocket, "Missing document_id or matter_id")
                return
            
            await websocket_service.join_document(connection_id, document_id, matter_id)
        
        elif message_type == MessageType.LEAVE_DOCUMENT.value:
            document_id = payload.get('document_id')
            
            if not document_id:
                await send_error_to_websocket(websocket, "Missing document_id")
                return
            
            await websocket_service.leave_document(connection_id, document_id)
        
        elif message_type == MessageType.DOCUMENT_EDIT.value:
            await websocket_service.handle_document_edit(connection_id, payload)
        
        elif message_type == MessageType.CURSOR_POSITION.value:
            await websocket_service.handle_cursor_position(connection_id, payload)
        
        elif message_type == MessageType.DOCUMENT_LOCK.value:
            document_id = payload.get('document_id')
            lock_duration = payload.get('lock_duration', 300)  # 5 minutes default
            
            if not document_id:
                await send_error_to_websocket(websocket, "Missing document_id")
                return
            
            await websocket_service.lock_document(connection_id, document_id, lock_duration)
        
        elif message_type == MessageType.DOCUMENT_UNLOCK.value:
            document_id = payload.get('document_id')
            
            if not document_id:
                await send_error_to_websocket(websocket, "Missing document_id")
                return
            
            await websocket_service.unlock_document(connection_id, document_id)
        
        elif message_type == MessageType.SYNC_REQUEST.value:
            # Handle document synchronization request
            document_id = payload.get('document_id')
            
            if not document_id:
                await send_error_to_websocket(websocket, "Missing document_id")
                return
            
            # Get current document session info
            session_info = await websocket_service.get_document_session_info(document_id)
            
            if session_info:
                await websocket.send_text(json.dumps({
                    'type': MessageType.SYNC_RESPONSE.value,
                    'payload': session_info
                }))
            else:
                await send_error_to_websocket(websocket, "Document session not found")
        
        else:
            await send_error_to_websocket(websocket, f"Unknown message type: {message_type}")
    
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        await send_error_to_websocket(websocket, f"Message handling failed: {str(e)}")


async def send_error_to_websocket(websocket: WebSocket, error_message: str):
    """Send error message via WebSocket"""
    try:
        await websocket.send_text(json.dumps({
            'type': MessageType.ERROR.value,
            'payload': {
                'error': error_message,
                'timestamp': datetime.now().isoformat()
            }
        }))
    except Exception as e:
        logger.error(f"Failed to send error via WebSocket: {e}")


# REST API endpoints for WebSocket management

@router.get("/connections", response_model=list)
async def list_active_connections():
    """
    List all active WebSocket connections
    
    Returns information about currently active WebSocket connections
    for monitoring and debugging purposes.
    """
    try:
        connections = []
        
        for connection_id, info in websocket_service.connections.items():
            connections.append(WebSocketConnectionInfo(
                connection_id=connection_id,
                user_id=info['user_id'],
                matter_id=info.get('matter_id'),
                connected_at=datetime.fromisoformat(info['connected_at']),
                status='active'
            ))
        
        return connections
        
    except Exception as e:
        logger.error(f"Error listing connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{document_id}", response_model=DocumentSessionInfo)
async def get_document_session(document_id: str):
    """
    Get information about a document editing session
    
    Returns details about active users, document version, and lock status
    for a specific document.
    """
    try:
        session_info = await websocket_service.get_document_session_info(document_id)
        
        if not session_info:
            raise HTTPException(status_code=404, detail="Document session not found")
        
        return DocumentSessionInfo(
            document_id=session_info['document_id'],
            matter_id=session_info['matter_id'],
            active_users_count=len(session_info['active_users']),
            active_users=session_info['active_users'],
            document_version=session_info['document_version'],
            last_sync=datetime.fromisoformat(session_info['last_sync']),
            lock_holder=session_info.get('lock_holder'),
            lock_expires=datetime.fromisoformat(session_info['lock_expires']) if session_info.get('lock_expires') else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document session {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_document_sessions():
    """
    List all active document editing sessions
    
    Returns summary information about all currently active
    collaborative editing sessions.
    """
    try:
        sessions = []
        
        for document_id, session in websocket_service.document_sessions.items():
            sessions.append({
                'document_id': document_id,
                'matter_id': session.matter_id,
                'active_users_count': len(session.active_users),
                'document_version': session.document_version,
                'last_sync': session.last_sync.isoformat(),
                'lock_holder': session.lock_holder,
                'lock_expires': session.lock_expires.isoformat() if session.lock_expires else None
            })
        
        return {'sessions': sessions, 'total_count': len(sessions)}
        
    except Exception as e:
        logger.error(f"Error listing document sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/broadcast/{document_id}")
async def broadcast_to_document(
    document_id: str,
    message: WebSocketMessage
):
    """
    Broadcast a message to all users in a document session
    
    Useful for sending system notifications or updates to all
    users currently editing a specific document.
    """
    try:
        message_dict = {
            'type': message.type,
            'payload': message.payload
        }
        
        sent_count = await websocket_service.broadcast_to_document(document_id, message_dict)
        
        return {
            'message': f'Broadcast sent to {sent_count} users',
            'document_id': document_id,
            'recipients': sent_count
        }
        
    except Exception as e:
        logger.error(f"Error broadcasting to document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/locks")
async def cleanup_expired_locks():
    """
    Clean up expired document locks
    
    Removes locks that have exceeded their expiration time
    and notifies affected users.
    """
    try:
        cleaned_count = await websocket_service.cleanup_expired_locks()
        
        return {
            'message': f'Cleaned up {cleaned_count} expired locks',
            'cleaned_locks': cleaned_count
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up locks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/connections/{connection_id}")
async def force_disconnect(connection_id: str):
    """
    Force disconnect a WebSocket connection
    
    Administratively disconnect a specific WebSocket connection
    and clean up associated resources.
    """
    try:
        success = await websocket_service.handle_disconnection(connection_id)
        
        if success:
            return {'message': f'Connection {connection_id} disconnected'}
        else:
            raise HTTPException(status_code=404, detail="Connection not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error force disconnecting {connection_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def websocket_health_check():
    """
    WebSocket service health check
    
    Returns status information about the WebSocket service
    including connection counts and active sessions.
    """
    try:
        health_info = {
            'status': 'healthy',
            'service': 'WebSocket Collaboration Service',
            'active_connections': len(websocket_service.connections),
            'active_sessions': len(websocket_service.document_sessions),
            'total_users': len(websocket_service.user_connections),
            'timestamp': datetime.now().isoformat()
        }
        
        return health_info
        
    except Exception as e:
        logger.error(f"WebSocket health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }