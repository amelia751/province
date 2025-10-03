"""
WebSocket Service for Real-time Collaboration

Handles WebSocket connections, message routing, and real-time document
synchronization for collaborative editing features.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

import boto3
from botocore.exceptions import ClientError

from ..core.config import get_settings
from ..core.exceptions import ValidationError, PermissionError

logger = logging.getLogger(__name__)
settings = get_settings()


class MessageType(Enum):
    """WebSocket message types"""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    JOIN_DOCUMENT = "join_document"
    LEAVE_DOCUMENT = "leave_document"
    DOCUMENT_EDIT = "document_edit"
    CURSOR_POSITION = "cursor_position"
    USER_PRESENCE = "user_presence"
    DOCUMENT_LOCK = "document_lock"
    DOCUMENT_UNLOCK = "document_unlock"
    SYNC_REQUEST = "sync_request"
    SYNC_RESPONSE = "sync_response"
    ERROR = "error"


@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    type: MessageType
    payload: Dict[str, Any]
    user_id: str
    connection_id: str
    timestamp: datetime
    message_id: str = None
    
    def __post_init__(self):
        if not self.message_id:
            self.message_id = str(uuid.uuid4())


@dataclass
class DocumentEdit:
    """Document edit operation"""
    operation: str  # "insert", "delete", "replace"
    position: int
    content: str
    length: int = 0
    user_id: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class UserPresence:
    """User presence information"""
    user_id: str
    connection_id: str
    document_id: str
    cursor_position: int
    selection_start: int
    selection_end: int
    last_seen: datetime
    user_name: str = ""
    user_color: str = ""


@dataclass
class DocumentSession:
    """Active document editing session"""
    document_id: str
    matter_id: str
    active_users: Dict[str, UserPresence]
    document_version: str
    last_sync: datetime
    lock_holder: Optional[str] = None
    lock_expires: Optional[datetime] = None


class WebSocketService:
    """Service for managing WebSocket connections and real-time collaboration"""
    
    def __init__(self):
        self.apigateway = boto3.client('apigatewaymanagementapi', region_name=settings.aws_region)
        self.dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        
        # Connection tracking
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.document_sessions: Dict[str, DocumentSession] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        
        # Tables
        self.connections_table = self.dynamodb.Table('websocket_connections')
        self.document_sessions_table = self.dynamodb.Table('document_sessions')
    
    async def handle_connection(self, connection_id: str, user_id: str, matter_id: str = None) -> bool:
        """Handle new WebSocket connection"""
        try:
            logger.info(f"New WebSocket connection: {connection_id} for user {user_id}")
            
            # Store connection info
            connection_info = {
                'connection_id': connection_id,
                'user_id': user_id,
                'matter_id': matter_id,
                'connected_at': datetime.now(timezone.utc).isoformat(),
                'last_ping': datetime.now(timezone.utc).isoformat()
            }
            
            # Store in DynamoDB
            self.connections_table.put_item(Item=connection_info)
            
            # Track in memory
            self.connections[connection_id] = connection_info
            
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            # Send welcome message
            await self.send_to_connection(connection_id, {
                'type': MessageType.CONNECT.value,
                'payload': {
                    'status': 'connected',
                    'connection_id': connection_id,
                    'server_time': datetime.now(timezone.utc).isoformat()
                }
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling connection {connection_id}: {e}")
            return False
    
    async def handle_disconnection(self, connection_id: str) -> bool:
        """Handle WebSocket disconnection"""
        try:
            logger.info(f"WebSocket disconnection: {connection_id}")
            
            # Get connection info
            connection_info = self.connections.get(connection_id)
            if not connection_info:
                return True  # Already cleaned up
            
            user_id = connection_info['user_id']
            
            # Remove from all document sessions
            for document_id, session in list(self.document_sessions.items()):
                if user_id in session.active_users:
                    await self.leave_document(connection_id, document_id)
            
            # Clean up connection tracking
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            del self.connections[connection_id]
            
            # Remove from DynamoDB
            self.connections_table.delete_item(Key={'connection_id': connection_id})
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling disconnection {connection_id}: {e}")
            return False
    
    async def join_document(self, connection_id: str, document_id: str, matter_id: str) -> bool:
        """Join a document editing session"""
        try:
            connection_info = self.connections.get(connection_id)
            if not connection_info:
                raise ValidationError("Invalid connection")
            
            user_id = connection_info['user_id']
            
            # Verify user has access to the document
            # TODO: Add proper permission checking
            
            # Get or create document session
            if document_id not in self.document_sessions:
                self.document_sessions[document_id] = DocumentSession(
                    document_id=document_id,
                    matter_id=matter_id,
                    active_users={},
                    document_version="1.0",
                    last_sync=datetime.now(timezone.utc)
                )
            
            session = self.document_sessions[document_id]
            
            # Add user to session
            user_presence = UserPresence(
                user_id=user_id,
                connection_id=connection_id,
                document_id=document_id,
                cursor_position=0,
                selection_start=0,
                selection_end=0,
                last_seen=datetime.now(timezone.utc),
                user_name=f"User {user_id[-4:]}",  # TODO: Get real user name
                user_color=self._generate_user_color(user_id)
            )
            
            session.active_users[user_id] = user_presence
            
            # Notify user they joined
            await self.send_to_connection(connection_id, {
                'type': MessageType.JOIN_DOCUMENT.value,
                'payload': {
                    'document_id': document_id,
                    'document_version': session.document_version,
                    'active_users': [asdict(user) for user in session.active_users.values()],
                    'lock_holder': session.lock_holder
                }
            })
            
            # Notify other users
            await self.broadcast_to_document(document_id, {
                'type': MessageType.USER_PRESENCE.value,
                'payload': {
                    'user_joined': asdict(user_presence),
                    'active_users_count': len(session.active_users)
                }
            }, exclude_connection=connection_id)
            
            logger.info(f"User {user_id} joined document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error joining document {document_id}: {e}")
            await self.send_error(connection_id, f"Failed to join document: {str(e)}")
            return False
    
    async def leave_document(self, connection_id: str, document_id: str) -> bool:
        """Leave a document editing session"""
        try:
            connection_info = self.connections.get(connection_id)
            if not connection_info:
                return True  # Already disconnected
            
            user_id = connection_info['user_id']
            
            if document_id not in self.document_sessions:
                return True  # Session doesn't exist
            
            session = self.document_sessions[document_id]
            
            # Remove user from session
            if user_id in session.active_users:
                user_presence = session.active_users[user_id]
                del session.active_users[user_id]
                
                # Release document lock if held by this user
                if session.lock_holder == user_id:
                    session.lock_holder = None
                    session.lock_expires = None
                    
                    await self.broadcast_to_document(document_id, {
                        'type': MessageType.DOCUMENT_UNLOCK.value,
                        'payload': {
                            'document_id': document_id,
                            'unlocked_by': user_id
                        }
                    })
                
                # Notify other users
                await self.broadcast_to_document(document_id, {
                    'type': MessageType.USER_PRESENCE.value,
                    'payload': {
                        'user_left': asdict(user_presence),
                        'active_users_count': len(session.active_users)
                    }
                })
                
                # Clean up empty sessions
                if not session.active_users:
                    del self.document_sessions[document_id]
                
                logger.info(f"User {user_id} left document {document_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error leaving document {document_id}: {e}")
            return False
    
    async def handle_document_edit(self, connection_id: str, edit_data: Dict[str, Any]) -> bool:
        """Handle document edit operation"""
        try:
            connection_info = self.connections.get(connection_id)
            if not connection_info:
                raise ValidationError("Invalid connection")
            
            user_id = connection_info['user_id']
            document_id = edit_data.get('document_id')
            
            if not document_id or document_id not in self.document_sessions:
                raise ValidationError("Invalid document session")
            
            session = self.document_sessions[document_id]
            
            # Check if document is locked by another user
            if session.lock_holder and session.lock_holder != user_id:
                if session.lock_expires and datetime.now(timezone.utc) < session.lock_expires:
                    await self.send_error(connection_id, "Document is locked by another user")
                    return False
                else:
                    # Lock expired, clear it
                    session.lock_holder = None
                    session.lock_expires = None
            
            # Create edit operation
            edit = DocumentEdit(
                operation=edit_data.get('operation', 'insert'),
                position=edit_data.get('position', 0),
                content=edit_data.get('content', ''),
                length=edit_data.get('length', 0),
                user_id=user_id
            )
            
            # Broadcast edit to all other users in the document
            await self.broadcast_to_document(document_id, {
                'type': MessageType.DOCUMENT_EDIT.value,
                'payload': {
                    'document_id': document_id,
                    'edit': asdict(edit),
                    'document_version': session.document_version
                }
            }, exclude_connection=connection_id)
            
            # Update session timestamp
            session.last_sync = datetime.now(timezone.utc)
            
            logger.debug(f"Document edit by {user_id} in {document_id}: {edit.operation}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling document edit: {e}")
            await self.send_error(connection_id, f"Edit failed: {str(e)}")
            return False
    
    async def handle_cursor_position(self, connection_id: str, cursor_data: Dict[str, Any]) -> bool:
        """Handle cursor position update"""
        try:
            connection_info = self.connections.get(connection_id)
            if not connection_info:
                return False
            
            user_id = connection_info['user_id']
            document_id = cursor_data.get('document_id')
            
            if not document_id or document_id not in self.document_sessions:
                return False
            
            session = self.document_sessions[document_id]
            
            if user_id in session.active_users:
                user_presence = session.active_users[user_id]
                user_presence.cursor_position = cursor_data.get('position', 0)
                user_presence.selection_start = cursor_data.get('selection_start', 0)
                user_presence.selection_end = cursor_data.get('selection_end', 0)
                user_presence.last_seen = datetime.now(timezone.utc)
                
                # Broadcast cursor position to other users
                await self.broadcast_to_document(document_id, {
                    'type': MessageType.CURSOR_POSITION.value,
                    'payload': {
                        'user_id': user_id,
                        'cursor_position': user_presence.cursor_position,
                        'selection_start': user_presence.selection_start,
                        'selection_end': user_presence.selection_end
                    }
                }, exclude_connection=connection_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling cursor position: {e}")
            return False
    
    async def lock_document(self, connection_id: str, document_id: str, lock_duration: int = 300) -> bool:
        """Lock document for exclusive editing"""
        try:
            connection_info = self.connections.get(connection_id)
            if not connection_info:
                raise ValidationError("Invalid connection")
            
            user_id = connection_info['user_id']
            
            if document_id not in self.document_sessions:
                raise ValidationError("Document session not found")
            
            session = self.document_sessions[document_id]
            
            # Check if already locked
            if session.lock_holder and session.lock_holder != user_id:
                if session.lock_expires and datetime.now(timezone.utc) < session.lock_expires:
                    await self.send_error(connection_id, "Document is already locked")
                    return False
            
            # Set lock
            from datetime import timedelta
            session.lock_holder = user_id
            session.lock_expires = datetime.now(timezone.utc) + timedelta(seconds=lock_duration)
            
            # Notify all users
            await self.broadcast_to_document(document_id, {
                'type': MessageType.DOCUMENT_LOCK.value,
                'payload': {
                    'document_id': document_id,
                    'locked_by': user_id,
                    'lock_expires': session.lock_expires.isoformat()
                }
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error locking document {document_id}: {e}")
            await self.send_error(connection_id, f"Lock failed: {str(e)}")
            return False
    
    async def unlock_document(self, connection_id: str, document_id: str) -> bool:
        """Unlock document"""
        try:
            connection_info = self.connections.get(connection_id)
            if not connection_info:
                return False
            
            user_id = connection_info['user_id']
            
            if document_id not in self.document_sessions:
                return False
            
            session = self.document_sessions[document_id]
            
            # Only lock holder can unlock
            if session.lock_holder != user_id:
                await self.send_error(connection_id, "You don't hold the lock")
                return False
            
            # Clear lock
            session.lock_holder = None
            session.lock_expires = None
            
            # Notify all users
            await self.broadcast_to_document(document_id, {
                'type': MessageType.DOCUMENT_UNLOCK.value,
                'payload': {
                    'document_id': document_id,
                    'unlocked_by': user_id
                }
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error unlocking document {document_id}: {e}")
            return False
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """Send message to specific WebSocket connection"""
        try:
            # Add timestamp and message ID
            message['timestamp'] = datetime.now(timezone.utc).isoformat()
            message['message_id'] = str(uuid.uuid4())
            
            # Send via API Gateway Management API
            response = self.apigateway.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(message, default=str)  # Handle datetime serialization
            )
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'GoneException':
                # Connection is stale, clean it up
                await self.handle_disconnection(connection_id)
            else:
                logger.error(f"Error sending to connection {connection_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending to connection {connection_id}: {e}")
            return False
    
    async def broadcast_to_document(self, document_id: str, message: Dict[str, Any], exclude_connection: str = None) -> int:
        """Broadcast message to all users in a document session"""
        if document_id not in self.document_sessions:
            return 0
        
        session = self.document_sessions[document_id]
        sent_count = 0
        
        for user_id, user_presence in session.active_users.items():
            if exclude_connection and user_presence.connection_id == exclude_connection:
                continue
            
            success = await self.send_to_connection(user_presence.connection_id, message)
            if success:
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]) -> int:
        """Broadcast message to all connections of a user"""
        if user_id not in self.user_connections:
            return 0
        
        sent_count = 0
        for connection_id in self.user_connections[user_id]:
            success = await self.send_to_connection(connection_id, message)
            if success:
                sent_count += 1
        
        return sent_count
    
    async def send_error(self, connection_id: str, error_message: str) -> bool:
        """Send error message to connection"""
        return await self.send_to_connection(connection_id, {
            'type': MessageType.ERROR.value,
            'payload': {
                'error': error_message,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        })
    
    def _generate_user_color(self, user_id: str) -> str:
        """Generate consistent color for user"""
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
        ]
        
        # Use hash of user_id to get consistent color
        hash_value = hash(user_id) % len(colors)
        return colors[hash_value]
    
    async def get_document_session_info(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a document session"""
        if document_id not in self.document_sessions:
            return None
        
        session = self.document_sessions[document_id]
        
        return {
            'document_id': document_id,
            'matter_id': session.matter_id,
            'active_users': [asdict(user) for user in session.active_users.values()],
            'document_version': session.document_version,
            'last_sync': session.last_sync.isoformat(),
            'lock_holder': session.lock_holder,
            'lock_expires': session.lock_expires.isoformat() if session.lock_expires else None
        }
    
    async def cleanup_expired_locks(self) -> int:
        """Clean up expired document locks"""
        cleaned_count = 0
        current_time = datetime.now(timezone.utc)
        
        for document_id, session in self.document_sessions.items():
            if (session.lock_holder and 
                session.lock_expires and 
                current_time > session.lock_expires):
                
                # Clear expired lock
                old_holder = session.lock_holder
                session.lock_holder = None
                session.lock_expires = None
                
                # Notify users
                await self.broadcast_to_document(document_id, {
                    'type': MessageType.DOCUMENT_UNLOCK.value,
                    'payload': {
                        'document_id': document_id,
                        'unlocked_by': 'system',
                        'reason': 'lock_expired',
                        'previous_holder': old_holder
                    }
                })
                
                cleaned_count += 1
                logger.info(f"Cleaned expired lock on document {document_id}")
        
        return cleaned_count


# Global WebSocket service instance
websocket_service = WebSocketService()