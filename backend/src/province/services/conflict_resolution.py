"""
Conflict Resolution Service for Collaborative Editing

Implements Conflict-free Replicated Data Type (CRDT) algorithms
and operational transformation for resolving concurrent document edits.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of document operations"""
    INSERT = "insert"
    DELETE = "delete"
    RETAIN = "retain"


@dataclass
class Operation:
    """Document operation for operational transformation"""
    type: OperationType
    position: int
    content: str = ""
    length: int = 0
    user_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    operation_id: str = ""
    
    def __post_init__(self):
        if not self.operation_id:
            import uuid
            self.operation_id = str(uuid.uuid4())
        
        if self.type == OperationType.DELETE and not self.length:
            self.length = len(self.content) if self.content else 1
        elif self.type == OperationType.INSERT and not self.length:
            self.length = len(self.content)


@dataclass
class DocumentState:
    """Document state with operation history"""
    document_id: str
    content: str
    version: int
    operations: List[Operation] = field(default_factory=list)
    last_modified: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def apply_operation(self, operation: Operation) -> bool:
        """Apply an operation to the document"""
        try:
            if operation.type == OperationType.INSERT:
                self.content = (
                    self.content[:operation.position] + 
                    operation.content + 
                    self.content[operation.position:]
                )
            elif operation.type == OperationType.DELETE:
                end_pos = operation.position + operation.length
                self.content = (
                    self.content[:operation.position] + 
                    self.content[end_pos:]
                )
            
            self.operations.append(operation)
            self.version += 1
            self.last_modified = datetime.now(timezone.utc)
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying operation: {e}")
            return False


class ConflictResolver:
    """Service for resolving document editing conflicts"""
    
    def __init__(self):
        self.document_states: Dict[str, DocumentState] = {}
    
    def get_document_state(self, document_id: str, initial_content: str = "") -> DocumentState:
        """Get or create document state"""
        if document_id not in self.document_states:
            self.document_states[document_id] = DocumentState(
                document_id=document_id,
                content=initial_content,
                version=0
            )
        
        return self.document_states[document_id]
    
    def transform_operation(self, op1: Operation, op2: Operation) -> Tuple[Operation, Operation]:
        """
        Transform two concurrent operations using Operational Transformation
        
        Returns transformed versions of both operations that can be applied
        in any order while maintaining consistency.
        """
        # Create copies to avoid modifying originals
        transformed_op1 = Operation(
            type=op1.type,
            position=op1.position,
            content=op1.content,
            length=op1.length,
            user_id=op1.user_id,
            timestamp=op1.timestamp,
            operation_id=op1.operation_id
        )
        
        transformed_op2 = Operation(
            type=op2.type,
            position=op2.position,
            content=op2.content,
            length=op2.length,
            user_id=op2.user_id,
            timestamp=op2.timestamp,
            operation_id=op2.operation_id
        )
        
        # Transform based on operation types
        if op1.type == OperationType.INSERT and op2.type == OperationType.INSERT:
            transformed_op1, transformed_op2 = self._transform_insert_insert(transformed_op1, transformed_op2)
        
        elif op1.type == OperationType.INSERT and op2.type == OperationType.DELETE:
            transformed_op1, transformed_op2 = self._transform_insert_delete(transformed_op1, transformed_op2)
        
        elif op1.type == OperationType.DELETE and op2.type == OperationType.INSERT:
            transformed_op2, transformed_op1 = self._transform_insert_delete(transformed_op2, transformed_op1)
        
        elif op1.type == OperationType.DELETE and op2.type == OperationType.DELETE:
            transformed_op1, transformed_op2 = self._transform_delete_delete(transformed_op1, transformed_op2)
        
        return transformed_op1, transformed_op2
    
    def _transform_insert_insert(self, op1: Operation, op2: Operation) -> Tuple[Operation, Operation]:
        """Transform two concurrent insert operations"""
        if op1.position <= op2.position:
            # op1 comes before op2, adjust op2's position
            op2.position += op1.length
        else:
            # op2 comes before op1, adjust op1's position
            op1.position += op2.length
        
        return op1, op2
    
    def _transform_insert_delete(self, insert_op: Operation, delete_op: Operation) -> Tuple[Operation, Operation]:
        """Transform insert and delete operations"""
        if insert_op.position <= delete_op.position:
            # Insert comes before delete, adjust delete position
            delete_op.position += insert_op.length
        else:
            # Delete comes before insert
            delete_end = delete_op.position + delete_op.length
            if insert_op.position >= delete_end:
                # Insert is after the deleted range
                insert_op.position -= delete_op.length
            else:
                # Insert is within the deleted range, move to delete position
                insert_op.position = delete_op.position
        
        return insert_op, delete_op
    
    def _transform_delete_delete(self, op1: Operation, op2: Operation) -> Tuple[Operation, Operation]:
        """Transform two concurrent delete operations"""
        op1_end = op1.position + op1.length
        op2_end = op2.position + op2.length
        
        # Check for overlap
        if op1.position >= op2_end:
            # op1 is completely after op2
            op1.position -= op2.length
        elif op2.position >= op1_end:
            # op2 is completely after op1
            op2.position -= op1.length
        else:
            # Operations overlap, need to handle carefully
            overlap_start = max(op1.position, op2.position)
            overlap_end = min(op1_end, op2_end)
            overlap_length = overlap_end - overlap_start
            
            if overlap_length > 0:
                # Reduce the length of both operations by the overlap
                if op1.position <= op2.position:
                    # op1 starts first
                    op1.length -= overlap_length
                    op2.position = op1.position + op1.length
                    op2.length -= overlap_length
                else:
                    # op2 starts first
                    op2.length -= overlap_length
                    op1.position = op2.position + op2.length
                    op1.length -= overlap_length
        
        return op1, op2
    
    def resolve_concurrent_operations(self, document_id: str, operations: List[Operation]) -> List[Operation]:
        """
        Resolve a list of concurrent operations using operational transformation
        
        Returns a list of transformed operations that can be applied sequentially
        to achieve a consistent document state.
        """
        if len(operations) <= 1:
            return operations
        
        # Sort operations by timestamp for deterministic ordering
        sorted_ops = sorted(operations, key=lambda op: (op.timestamp, op.operation_id))
        
        # Apply operational transformation pairwise
        resolved_ops = [sorted_ops[0]]
        
        for i in range(1, len(sorted_ops)):
            current_op = sorted_ops[i]
            
            # Transform current operation against all previous operations
            for j in range(len(resolved_ops)):
                _, current_op = self.transform_operation(resolved_ops[j], current_op)
            
            resolved_ops.append(current_op)
        
        return resolved_ops
    
    def apply_operations_with_conflict_resolution(
        self, 
        document_id: str, 
        operations: List[Operation],
        initial_content: str = ""
    ) -> DocumentState:
        """
        Apply operations to document with automatic conflict resolution
        
        Uses operational transformation to resolve conflicts and maintain
        document consistency across concurrent edits.
        """
        document_state = self.get_document_state(document_id, initial_content)
        
        # Resolve conflicts between operations
        resolved_operations = self.resolve_concurrent_operations(document_id, operations)
        
        # Apply resolved operations sequentially
        for operation in resolved_operations:
            success = document_state.apply_operation(operation)
            if not success:
                logger.error(f"Failed to apply operation {operation.operation_id}")
        
        return document_state
    
    def create_operation_from_edit(
        self, 
        edit_data: Dict[str, Any], 
        user_id: str
    ) -> Operation:
        """Create an Operation from edit data"""
        operation_type = OperationType(edit_data.get('operation', 'insert'))
        
        return Operation(
            type=operation_type,
            position=edit_data.get('position', 0),
            content=edit_data.get('content', ''),
            length=edit_data.get('length', 0),
            user_id=user_id
        )
    
    def generate_diff(self, old_content: str, new_content: str) -> List[Operation]:
        """
        Generate a list of operations that transform old_content to new_content
        
        Uses a simple diff algorithm to identify insertions and deletions.
        """
        operations = []
        
        # Simple character-by-character diff
        # In production, you'd want a more sophisticated diff algorithm
        i = j = 0
        position = 0
        
        while i < len(old_content) or j < len(new_content):
            if i >= len(old_content):
                # Remaining characters are insertions
                operations.append(Operation(
                    type=OperationType.INSERT,
                    position=position,
                    content=new_content[j:],
                    user_id="system"
                ))
                break
            elif j >= len(new_content):
                # Remaining characters are deletions
                operations.append(Operation(
                    type=OperationType.DELETE,
                    position=position,
                    content=old_content[i:],
                    length=len(old_content[i:]),
                    user_id="system"
                ))
                break
            elif old_content[i] == new_content[j]:
                # Characters match, continue
                i += 1
                j += 1
                position += 1
            else:
                # Characters differ, determine if it's insert, delete, or replace
                # For simplicity, treat as delete + insert
                operations.append(Operation(
                    type=OperationType.DELETE,
                    position=position,
                    content=old_content[i],
                    length=1,
                    user_id="system"
                ))
                operations.append(Operation(
                    type=OperationType.INSERT,
                    position=position,
                    content=new_content[j],
                    user_id="system"
                ))
                i += 1
                j += 1
                position += 1
        
        return operations
    
    def get_document_history(self, document_id: str) -> List[Dict[str, Any]]:
        """Get the operation history for a document"""
        if document_id not in self.document_states:
            return []
        
        document_state = self.document_states[document_id]
        
        return [
            {
                'operation_id': op.operation_id,
                'type': op.type.value,
                'position': op.position,
                'content': op.content,
                'length': op.length,
                'user_id': op.user_id,
                'timestamp': op.timestamp.isoformat()
            }
            for op in document_state.operations
        ]
    
    def create_checkpoint(self, document_id: str) -> Dict[str, Any]:
        """Create a checkpoint of the current document state"""
        if document_id not in self.document_states:
            return {}
        
        document_state = self.document_states[document_id]
        
        return {
            'document_id': document_id,
            'content': document_state.content,
            'version': document_state.version,
            'last_modified': document_state.last_modified.isoformat(),
            'operation_count': len(document_state.operations)
        }
    
    def restore_from_checkpoint(self, checkpoint: Dict[str, Any]) -> bool:
        """Restore document state from a checkpoint"""
        try:
            document_id = checkpoint['document_id']
            
            self.document_states[document_id] = DocumentState(
                document_id=document_id,
                content=checkpoint['content'],
                version=checkpoint['version'],
                last_modified=datetime.fromisoformat(checkpoint['last_modified'])
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error restoring from checkpoint: {e}")
            return False


# Global conflict resolver instance
conflict_resolver = ConflictResolver()