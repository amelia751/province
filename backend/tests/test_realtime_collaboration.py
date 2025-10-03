"""
Integration tests for real-time collaboration features

Tests WebSocket connections, document synchronization, conflict resolution,
and collaborative editing workflows.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from src.province.services.websocket_service import (
    WebSocketService, 
    MessageType, 
    DocumentEdit, 
    UserPresence,
    DocumentSession
)
from src.province.services.conflict_resolution import (
    ConflictResolver,
    Operation,
    OperationType,
    DocumentState
)


@pytest.fixture
def websocket_service():
    """Create WebSocket service instance for testing"""
    service = WebSocketService()
    # Mock AWS clients to avoid real connections
    service.apigateway = Mock()
    service.dynamodb = Mock()
    service.connections_table = Mock()
    service.document_sessions_table = Mock()
    return service


@pytest.fixture
def conflict_resolver():
    """Create conflict resolver instance for testing"""
    return ConflictResolver()


@pytest.fixture
def sample_document_edit():
    """Create sample document edit"""
    return DocumentEdit(
        operation="insert",
        position=10,
        content="Hello World",
        user_id="user_123"
    )


class TestWebSocketService:
    """Test WebSocket service functionality"""
    
    @pytest.mark.asyncio
    async def test_handle_connection(self, websocket_service):
        """Test WebSocket connection handling"""
        connection_id = "conn_123"
        user_id = "user_456"
        matter_id = "matter_789"
        
        # Mock successful connection storage
        websocket_service.connections_table.put_item.return_value = {}
        websocket_service.apigateway.post_to_connection.return_value = {}
        
        result = await websocket_service.handle_connection(connection_id, user_id, matter_id)
        
        assert result == True
        assert connection_id in websocket_service.connections
        assert websocket_service.connections[connection_id]['user_id'] == user_id
        assert user_id in websocket_service.user_connections
        assert connection_id in websocket_service.user_connections[user_id]
    
    @pytest.mark.asyncio
    async def test_handle_disconnection(self, websocket_service):
        """Test WebSocket disconnection handling"""
        connection_id = "conn_123"
        user_id = "user_456"
        
        # Set up initial connection
        websocket_service.connections[connection_id] = {
            'user_id': user_id,
            'matter_id': 'matter_789'
        }
        websocket_service.user_connections[user_id] = {connection_id}
        
        # Mock DynamoDB operations
        websocket_service.connections_table.delete_item.return_value = {}
        
        result = await websocket_service.handle_disconnection(connection_id)
        
        assert result == True
        assert connection_id not in websocket_service.connections
        assert user_id not in websocket_service.user_connections
    
    @pytest.mark.asyncio
    async def test_join_document(self, websocket_service):
        """Test joining a document editing session"""
        connection_id = "conn_123"
        user_id = "user_456"
        document_id = "doc_789"
        matter_id = "matter_101"
        
        # Set up connection
        websocket_service.connections[connection_id] = {
            'user_id': user_id,
            'matter_id': matter_id
        }
        
        # Mock API Gateway response
        websocket_service.apigateway.post_to_connection.return_value = {}
        
        result = await websocket_service.join_document(connection_id, document_id, matter_id)
        
        assert result == True
        assert document_id in websocket_service.document_sessions
        
        session = websocket_service.document_sessions[document_id]
        assert user_id in session.active_users
        assert session.active_users[user_id].connection_id == connection_id
    
    @pytest.mark.asyncio
    async def test_leave_document(self, websocket_service):
        """Test leaving a document editing session"""
        connection_id = "conn_123"
        user_id = "user_456"
        document_id = "doc_789"
        matter_id = "matter_101"
        
        # Set up connection and session
        websocket_service.connections[connection_id] = {
            'user_id': user_id,
            'matter_id': matter_id
        }
        
        session = DocumentSession(
            document_id=document_id,
            matter_id=matter_id,
            active_users={},
            document_version="1.0",
            last_sync=datetime.now(timezone.utc)
        )
        
        session.active_users[user_id] = UserPresence(
            user_id=user_id,
            connection_id=connection_id,
            document_id=document_id,
            cursor_position=0,
            selection_start=0,
            selection_end=0,
            last_seen=datetime.now(timezone.utc)
        )
        
        websocket_service.document_sessions[document_id] = session
        
        result = await websocket_service.leave_document(connection_id, document_id)
        
        assert result == True
        # Session should be cleaned up since no users remain
        assert document_id not in websocket_service.document_sessions
    
    @pytest.mark.asyncio
    async def test_handle_document_edit(self, websocket_service):
        """Test handling document edit operations"""
        connection_id = "conn_123"
        user_id = "user_456"
        document_id = "doc_789"
        matter_id = "matter_101"
        
        # Set up connection and session
        websocket_service.connections[connection_id] = {
            'user_id': user_id,
            'matter_id': matter_id
        }
        
        session = DocumentSession(
            document_id=document_id,
            matter_id=matter_id,
            active_users={user_id: UserPresence(
                user_id=user_id,
                connection_id=connection_id,
                document_id=document_id,
                cursor_position=0,
                selection_start=0,
                selection_end=0,
                last_seen=datetime.now(timezone.utc)
            )},
            document_version="1.0",
            last_sync=datetime.now(timezone.utc)
        )
        
        websocket_service.document_sessions[document_id] = session
        
        # Mock API Gateway response
        websocket_service.apigateway.post_to_connection.return_value = {}
        
        edit_data = {
            'document_id': document_id,
            'operation': 'insert',
            'position': 10,
            'content': 'Hello World'
        }
        
        result = await websocket_service.handle_document_edit(connection_id, edit_data)
        
        assert result == True
        # Verify session was updated
        assert session.last_sync > datetime.now(timezone.utc).replace(second=0)
    
    @pytest.mark.asyncio
    async def test_document_locking(self, websocket_service):
        """Test document locking mechanism"""
        connection_id = "conn_123"
        user_id = "user_456"
        document_id = "doc_789"
        matter_id = "matter_101"
        
        # Set up connection and session
        websocket_service.connections[connection_id] = {
            'user_id': user_id,
            'matter_id': matter_id
        }
        
        session = DocumentSession(
            document_id=document_id,
            matter_id=matter_id,
            active_users={user_id: UserPresence(
                user_id=user_id,
                connection_id=connection_id,
                document_id=document_id,
                cursor_position=0,
                selection_start=0,
                selection_end=0,
                last_seen=datetime.now(timezone.utc)
            )},
            document_version="1.0",
            last_sync=datetime.now(timezone.utc)
        )
        
        websocket_service.document_sessions[document_id] = session
        
        # Mock API Gateway response
        websocket_service.apigateway.post_to_connection.return_value = {}
        
        # Test locking
        result = await websocket_service.lock_document(connection_id, document_id, 300)
        
        assert result == True
        assert session.lock_holder == user_id
        assert session.lock_expires is not None
        
        # Test unlocking
        result = await websocket_service.unlock_document(connection_id, document_id)
        
        assert result == True
        assert session.lock_holder is None
        assert session.lock_expires is None


class TestConflictResolution:
    """Test conflict resolution functionality"""
    
    def test_create_operation(self, conflict_resolver):
        """Test creating operations from edit data"""
        edit_data = {
            'operation': 'insert',
            'position': 5,
            'content': 'Hello',
            'length': 5
        }
        
        operation = conflict_resolver.create_operation_from_edit(edit_data, 'user_123')
        
        assert operation.type == OperationType.INSERT
        assert operation.position == 5
        assert operation.content == 'Hello'
        assert operation.user_id == 'user_123'
    
    def test_transform_insert_insert(self, conflict_resolver):
        """Test transforming two concurrent insert operations"""
        op1 = Operation(
            type=OperationType.INSERT,
            position=5,
            content="Hello",
            user_id="user1"
        )
        
        op2 = Operation(
            type=OperationType.INSERT,
            position=5,
            content="World",
            user_id="user2"
        )
        
        transformed_op1, transformed_op2 = conflict_resolver.transform_operation(op1, op2)
        
        # One operation should have its position adjusted
        assert transformed_op1.position == 5
        assert transformed_op2.position == 10  # Adjusted by length of op1
    
    def test_transform_insert_delete(self, conflict_resolver):
        """Test transforming insert and delete operations"""
        insert_op = Operation(
            type=OperationType.INSERT,
            position=10,
            content="Hello",
            user_id="user1"
        )
        
        delete_op = Operation(
            type=OperationType.DELETE,
            position=5,
            length=3,
            user_id="user2"
        )
        
        transformed_insert, transformed_delete = conflict_resolver.transform_operation(insert_op, delete_op)
        
        # Insert position should be adjusted for the deletion
        assert transformed_insert.position == 7  # 10 - 3 (deleted length)
        assert transformed_delete.position == 5  # Unchanged
    
    def test_resolve_concurrent_operations(self, conflict_resolver):
        """Test resolving multiple concurrent operations"""
        operations = [
            Operation(
                type=OperationType.INSERT,
                position=5,
                content="A",
                user_id="user1",
                timestamp=datetime(2024, 1, 1, 10, 0, 0)
            ),
            Operation(
                type=OperationType.INSERT,
                position=5,
                content="B",
                user_id="user2",
                timestamp=datetime(2024, 1, 1, 10, 0, 1)
            ),
            Operation(
                type=OperationType.DELETE,
                position=3,
                length=2,
                user_id="user3",
                timestamp=datetime(2024, 1, 1, 10, 0, 2)
            )
        ]
        
        resolved_ops = conflict_resolver.resolve_concurrent_operations("doc_123", operations)
        
        assert len(resolved_ops) == 3
        # Operations should be sorted by timestamp
        assert resolved_ops[0].timestamp < resolved_ops[1].timestamp < resolved_ops[2].timestamp
    
    def test_apply_operations_with_conflict_resolution(self, conflict_resolver):
        """Test applying operations with automatic conflict resolution"""
        document_id = "doc_123"
        initial_content = "Hello World"
        
        operations = [
            Operation(
                type=OperationType.INSERT,
                position=5,
                content=" Beautiful",
                user_id="user1"
            ),
            Operation(
                type=OperationType.DELETE,
                position=0,
                length=5,
                user_id="user2"
            )
        ]
        
        document_state = conflict_resolver.apply_operations_with_conflict_resolution(
            document_id, operations, initial_content
        )
        
        assert document_state.document_id == document_id
        assert document_state.version == 2  # Two operations applied
        assert len(document_state.operations) == 2
    
    def test_generate_diff(self, conflict_resolver):
        """Test generating operations from content diff"""
        old_content = "Hello World"
        new_content = "Hello Beautiful World"
        
        operations = conflict_resolver.generate_diff(old_content, new_content)
        
        # Should generate operations to transform old to new
        assert len(operations) > 0
        
        # Apply operations to verify they work
        document_state = DocumentState(
            document_id="test",
            content=old_content,
            version=0
        )
        
        for op in operations:
            document_state.apply_operation(op)
        
        # Result should match new content (approximately, due to simple diff algorithm)
        assert "Beautiful" in document_state.content
    
    def test_document_checkpoint(self, conflict_resolver):
        """Test creating and restoring document checkpoints"""
        document_id = "doc_123"
        initial_content = "Hello World"
        
        # Create document state
        document_state = conflict_resolver.get_document_state(document_id, initial_content)
        
        # Apply some operations
        operation = Operation(
            type=OperationType.INSERT,
            position=5,
            content=" Beautiful",
            user_id="user1"
        )
        document_state.apply_operation(operation)
        
        # Create checkpoint
        checkpoint = conflict_resolver.create_checkpoint(document_id)
        
        assert checkpoint['document_id'] == document_id
        assert checkpoint['version'] == 1
        assert "Beautiful" in checkpoint['content']
        
        # Modify document further
        operation2 = Operation(
            type=OperationType.INSERT,
            position=0,
            content="Hi ",
            user_id="user2"
        )
        document_state.apply_operation(operation2)
        
        assert document_state.version == 2
        
        # Restore from checkpoint
        success = conflict_resolver.restore_from_checkpoint(checkpoint)
        
        assert success == True
        restored_state = conflict_resolver.get_document_state(document_id)
        assert restored_state.version == 1
        assert "Beautiful" in restored_state.content
        assert not restored_state.content.startswith("Hi ")


@pytest.mark.asyncio
async def test_integration_websocket_and_conflict_resolution():
    """Integration test combining WebSocket service and conflict resolution"""
    websocket_service = WebSocketService()
    conflict_resolver = ConflictResolver()
    
    # Mock AWS clients
    websocket_service.apigateway = Mock()
    websocket_service.dynamodb = Mock()
    websocket_service.connections_table = Mock()
    websocket_service.document_sessions_table = Mock()
    
    # Mock successful responses
    websocket_service.connections_table.put_item.return_value = {}
    websocket_service.apigateway.post_to_connection.return_value = {}
    
    # Set up two users
    user1_conn = "conn_1"
    user2_conn = "conn_2"
    user1_id = "user_1"
    user2_id = "user_2"
    document_id = "doc_123"
    matter_id = "matter_456"
    
    # Connect both users
    await websocket_service.handle_connection(user1_conn, user1_id, matter_id)
    await websocket_service.handle_connection(user2_conn, user2_id, matter_id)
    
    # Both users join the same document
    await websocket_service.join_document(user1_conn, document_id, matter_id)
    await websocket_service.join_document(user2_conn, document_id, matter_id)
    
    # Verify session exists
    assert document_id in websocket_service.document_sessions
    session = websocket_service.document_sessions[document_id]
    assert len(session.active_users) == 2
    
    # Simulate concurrent edits
    edit1_data = {
        'document_id': document_id,
        'operation': 'insert',
        'position': 5,
        'content': 'Hello'
    }
    
    edit2_data = {
        'document_id': document_id,
        'operation': 'insert',
        'position': 5,
        'content': 'World'
    }
    
    # Apply edits through WebSocket service
    await websocket_service.handle_document_edit(user1_conn, edit1_data)
    await websocket_service.handle_document_edit(user2_conn, edit2_data)
    
    # Create operations for conflict resolution
    op1 = conflict_resolver.create_operation_from_edit(edit1_data, user1_id)
    op2 = conflict_resolver.create_operation_from_edit(edit2_data, user2_id)
    
    # Resolve conflicts
    resolved_ops = conflict_resolver.resolve_concurrent_operations(document_id, [op1, op2])
    
    # Apply resolved operations
    document_state = conflict_resolver.apply_operations_with_conflict_resolution(
        document_id, resolved_ops, "Initial content"
    )
    
    # Verify final state
    assert document_state.version == 2
    assert "Hello" in document_state.content
    assert "World" in document_state.content
    
    # Clean up
    await websocket_service.leave_document(user1_conn, document_id)
    await websocket_service.leave_document(user2_conn, document_id)
    await websocket_service.handle_disconnection(user1_conn)
    await websocket_service.handle_disconnection(user2_conn)
    
    # Verify cleanup
    assert document_id not in websocket_service.document_sessions
    assert len(websocket_service.connections) == 0