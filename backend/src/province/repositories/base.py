"""Base repository with common functionality."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar

from province.core.exceptions import NotFoundError

T = TypeVar('T')


class BaseRepository(ABC):
    """Base repository interface."""
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: str, tenant_id: str) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def update(self, entity_id: str, tenant_id: str, updates: Dict[str, Any]) -> T:
        """Update entity."""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str, tenant_id: str) -> bool:
        """Delete entity."""
        pass
    
    @abstractmethod
    async def list(
        self, 
        tenant_id: str, 
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[T]:
        """List entities with optional filters."""
        pass


class InMemoryRepository(BaseRepository):
    """In-memory repository implementation for development."""
    
    def __init__(self, entity_class: Type[T]):
        self.entity_class = entity_class
        self._data: Dict[str, T] = {}
    
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        entity_id = getattr(entity, f"{self.entity_class.__name__.lower()}_id")
        self._data[entity_id] = entity
        return entity
    
    async def get_by_id(self, entity_id: str, tenant_id: str) -> Optional[T]:
        """Get entity by ID."""
        entity = self._data.get(entity_id)
        if entity:
            # For system entities (like templates), allow any tenant
            if tenant_id == "system" or getattr(entity, 'tenant_id', None) == tenant_id:
                return entity
        return None
    
    async def update(self, entity_id: str, tenant_id: str, updates: Dict[str, Any]) -> T:
        """Update entity."""
        entity = await self.get_by_id(entity_id, tenant_id)
        if not entity:
            raise NotFoundError(f"{self.entity_class.__name__} not found")
        
        # Update fields
        for key, value in updates.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        
        # Update timestamp - always ensure it's newer than the original
        if hasattr(entity, 'updated_at'):
            from province.models.base import utc_now
            from datetime import timedelta
            # Always increment timestamp to ensure it's different
            original_time = entity.updated_at
            new_time = utc_now()
            # Ensure new time is always greater than original
            if new_time <= original_time:
                new_time = original_time + timedelta(microseconds=1)
            entity.updated_at = new_time
        
        self._data[entity_id] = entity
        return entity
    
    async def delete(self, entity_id: str, tenant_id: str) -> bool:
        """Delete entity."""
        entity = await self.get_by_id(entity_id, tenant_id)
        if entity:
            del self._data[entity_id]
            return True
        return False
    
    async def list(
        self, 
        tenant_id: str, 
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[T]:
        """List entities with optional filters."""
        entities = [
            entity for entity in self._data.values()
            if getattr(entity, 'tenant_id', None) == tenant_id
        ]
        
        # Apply filters
        if filters:
            entities = self._apply_filters(entities, filters)
        
        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        return entities[start:end]
    
    def _apply_filters(self, entities: List[T], filters: Dict[str, Any]) -> List[T]:
        """Apply filters to entity list."""
        filtered = entities
        
        for key, value in filters.items():
            if value is None:
                continue
                
            if key == 'search':
                # Simple text search in title and description
                filtered = [
                    entity for entity in filtered
                    if (hasattr(entity, 'title') and value.lower() in entity.title.lower()) or
                       (hasattr(entity, 'description') and entity.description and value.lower() in entity.description.lower())
                ]
            else:
                # Exact match filter
                filtered = [
                    entity for entity in filtered
                    if hasattr(entity, key) and getattr(entity, key) == value
                ]
        
        return filtered
    
    async def count(self, tenant_id: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching filters."""
        entities = await self.list(tenant_id, filters, page=1, page_size=1000000)
        return len(entities)