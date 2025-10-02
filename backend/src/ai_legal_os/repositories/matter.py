"""Matter repository implementation."""

from typing import Dict, List, Optional

from ai_legal_os.models.matter import Matter, MatterFilters, MatterStats
from ai_legal_os.models.base import MatterStatus

from .base import InMemoryRepository


class MatterRepository(InMemoryRepository):
    """Matter repository."""
    
    def __init__(self):
        super().__init__(Matter)
    
    async def get_by_matter_number(self, matter_number: str, tenant_id: str) -> Optional[Matter]:
        """Get matter by matter number."""
        for matter in self._data.values():
            if (matter.tenant_id == tenant_id and 
                matter.matter_number == matter_number):
                return matter
        return None
    
    async def list_by_user(
        self, 
        user_id: str, 
        tenant_id: str,
        filters: Optional[MatterFilters] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[Matter]:
        """List matters for a specific user."""
        # For now, return all matters for the tenant
        # In a real implementation, this would check user permissions
        filter_dict = {}
        if filters:
            filter_dict = filters.model_dump(exclude_none=True)
        
        return await self.list(tenant_id, filter_dict, page, page_size)
    
    async def get_stats(self, tenant_id: str, user_id: str) -> MatterStats:
        """Get matter statistics for a user."""
        matters = await self.list(tenant_id)
        
        total_matters = len(matters)
        active_matters = len([m for m in matters if m.status == MatterStatus.ACTIVE])
        closed_matters = len([m for m in matters if m.status == MatterStatus.CLOSED])
        
        # Count by type
        matters_by_type: Dict[str, int] = {}
        for matter in matters:
            matters_by_type[matter.matter_type] = matters_by_type.get(matter.matter_type, 0) + 1
        
        # Count by status
        matters_by_status: Dict[str, int] = {}
        for matter in matters:
            status_str = matter.status.value
            matters_by_status[status_str] = matters_by_status.get(status_str, 0) + 1
        
        # Recent activity (last 5 matters)
        recent_matters = sorted(matters, key=lambda m: m.updated_at, reverse=True)[:5]
        recent_activity = [
            {
                "matter_id": matter.matter_id,
                "title": matter.title,
                "action": "updated",
                "timestamp": matter.updated_at.isoformat()
            }
            for matter in recent_matters
        ]
        
        return MatterStats(
            total_matters=total_matters,
            active_matters=active_matters,
            closed_matters=closed_matters,
            matters_by_type=matters_by_type,
            matters_by_status=matters_by_status,
            recent_activity=recent_activity
        )