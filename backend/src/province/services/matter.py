"""Matter service implementation."""

import logging
from typing import List, Optional

from province.core.exceptions import NotFoundError, ValidationError
from province.models.matter import (
    Matter, MatterCreate, MatterUpdate, MatterFilters, 
    MatterListResponse, MatterStats
)
from province.repositories.matter import MatterRepository
from province.repositories.template import TemplateRepository
from province.services.template import TemplateService

logger = logging.getLogger(__name__)


class MatterService:
    """Service for managing legal matters."""
    
    def __init__(
        self,
        matter_repo: Optional[MatterRepository] = None,
        template_repo: Optional[TemplateRepository] = None,
        template_service: Optional[TemplateService] = None
    ):
        self.matter_repo = matter_repo or MatterRepository()
        if template_service:
            self.template_service = template_service
            self.template_repo = template_service.template_repo
        else:
            self.template_repo = template_repo or TemplateRepository()
            self.template_service = TemplateService(self.template_repo)
    
    async def create_matter(
        self, 
        matter_data: MatterCreate, 
        user_id: str, 
        tenant_id: str
    ) -> Matter:
        """Create a new matter."""
        logger.info(f"Creating matter for user {user_id}, tenant {tenant_id}")
        
        # Validate template if provided
        template = None
        if matter_data.template_id:
            template = await self.template_repo.get_by_id(matter_data.template_id, "system")
            if not template:
                raise ValidationError(f"Template {matter_data.template_id} not found")
        
        # Create matter entity
        matter = Matter(
            tenant_id=tenant_id,
            title=matter_data.title,
            matter_type=matter_data.matter_type,
            jurisdiction=matter_data.jurisdiction,
            description=matter_data.description,
            client_name=matter_data.client_name,
            opposing_party=matter_data.opposing_party,
            created_by=user_id,
            template_id=matter_data.template_id,
            custom_fields=matter_data.custom_fields
        )
        
        # Save matter
        created_matter = await self.matter_repo.create(matter)
        
        # Apply template if provided
        if template:
            await self.template_service.apply_template_to_matter(
                template, created_matter, user_id
            )
            # Increment template usage
            await self.template_repo.increment_usage(template.template_id)
        
        logger.info(f"Created matter {created_matter.matter_id} ({created_matter.matter_number})")
        return created_matter
    
    async def get_matter(self, matter_id: str, user_id: str, tenant_id: str) -> Matter:
        """Get a matter by ID."""
        matter = await self.matter_repo.get_by_id(matter_id, tenant_id)
        if not matter:
            raise NotFoundError(f"Matter {matter_id} not found")
        
        # TODO: Check user permissions
        return matter
    
    async def get_matter_by_number(
        self, 
        matter_number: str, 
        user_id: str, 
        tenant_id: str
    ) -> Matter:
        """Get a matter by matter number."""
        matter = await self.matter_repo.get_by_matter_number(matter_number, tenant_id)
        if not matter:
            raise NotFoundError(f"Matter {matter_number} not found")
        
        # TODO: Check user permissions
        return matter
    
    async def update_matter(
        self, 
        matter_id: str, 
        updates: MatterUpdate, 
        user_id: str, 
        tenant_id: str
    ) -> Matter:
        """Update a matter."""
        # Check if matter exists and user has permission
        await self.get_matter(matter_id, user_id, tenant_id)
        
        # Prepare update data
        update_data = updates.model_dump(exclude_none=True)
        
        # Update matter
        updated_matter = await self.matter_repo.update(matter_id, tenant_id, update_data)
        
        logger.info(f"Updated matter {matter_id} by user {user_id}")
        return updated_matter
    
    async def delete_matter(self, matter_id: str, user_id: str, tenant_id: str) -> bool:
        """Delete a matter."""
        # Check if matter exists and user has permission
        await self.get_matter(matter_id, user_id, tenant_id)
        
        # Delete matter
        deleted = await self.matter_repo.delete(matter_id, tenant_id)
        
        if deleted:
            logger.info(f"Deleted matter {matter_id} by user {user_id}")
        
        return deleted
    
    async def list_matters(
        self,
        user_id: str,
        tenant_id: str,
        filters: Optional[MatterFilters] = None,
        page: int = 1,
        page_size: int = 20
    ) -> MatterListResponse:
        """List matters for a user."""
        matters = await self.matter_repo.list_by_user(
            user_id, tenant_id, filters, page, page_size
        )
        
        # Get total count
        filter_dict = filters.model_dump(exclude_none=True) if filters else {}
        total = await self.matter_repo.count(tenant_id, filter_dict)
        
        has_next = (page * page_size) < total
        
        return MatterListResponse(
            matters=matters,
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next
        )
    
    async def get_matter_stats(self, user_id: str, tenant_id: str) -> MatterStats:
        """Get matter statistics for a user."""
        return await self.matter_repo.get_stats(tenant_id, user_id)
    
    async def get_matter_stats(self, user_id: str, tenant_id: str) -> MatterStats:
        """Get matter statistics for a user."""
        return await self.matter_repo.get_stats(tenant_id, user_id)
    
    async def search_matters(
        self,
        query: str,
        user_id: str,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> MatterListResponse:
        """Search matters by query."""
        filters = MatterFilters(search=query)
        return await self.list_matters(user_id, tenant_id, filters, page, page_size)