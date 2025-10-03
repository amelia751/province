"""Template service implementation."""

import logging
from typing import List, Optional

from province.core.exceptions import NotFoundError, ValidationError
from province.models.matter import Matter
from province.models.template import Template, TemplateCreate, TemplateListResponse
from province.repositories.template import TemplateRepository
from province.services.template_parser import TemplateParser, TemplateParseError
from province.services.folder_generator import FolderGenerator, FolderGenerationError

logger = logging.getLogger(__name__)


class TemplateService:
    """Service for managing matter templates."""
    
    def __init__(
        self, 
        template_repo: Optional[TemplateRepository] = None,
        folder_generator: Optional[FolderGenerator] = None
    ):
        self.template_repo = template_repo or TemplateRepository()
        self.folder_generator = folder_generator or FolderGenerator()
    
    async def create_template(
        self, 
        template_data: TemplateCreate, 
        user_id: str
    ) -> Template:
        """Create a new template."""
        logger.info(f"Creating template '{template_data.name}' by user {user_id}")
        
        from province.models.base import generate_id
        
        template = Template(
            template_id=generate_id(),
            name=template_data.name,
            description=template_data.description,
            applies_to=template_data.applies_to,
            folders=template_data.folders,
            starter_docs=template_data.starter_docs,
            deadlines=template_data.deadlines,
            agents=template_data.agents,
            guardrails=template_data.guardrails,
            created_by=user_id
        )
        
        created_template = await self.template_repo.create(template)
        logger.info(f"Created template {created_template.template_id}")
        return created_template
    
    async def get_template(self, template_id: str) -> Template:
        """Get a template by ID."""
        template = await self.template_repo.get_by_id(template_id, "system")
        if not template:
            raise NotFoundError(f"Template {template_id} not found")
        return template
    
    async def get_template_by_name(self, name: str) -> Template:
        """Get a template by name."""
        template = await self.template_repo.get_by_name(name)
        if not template:
            raise NotFoundError(f"Template '{name}' not found")
        return template
    
    async def update_template(
        self, 
        template_id: str, 
        template_data: TemplateCreate, 
        user_id: str
    ) -> Template:
        """Update an existing template."""
        logger.info(f"Updating template {template_id} by user {user_id}")
        
        # Get existing template
        existing_template = await self.get_template(template_id)
        
        # Update fields
        existing_template.name = template_data.name
        existing_template.description = template_data.description
        existing_template.applies_to = template_data.applies_to
        existing_template.folders = template_data.folders
        existing_template.starter_docs = template_data.starter_docs
        existing_template.deadlines = template_data.deadlines
        existing_template.agents = template_data.agents
        existing_template.guardrails = template_data.guardrails
        
        # Update metadata
        from datetime import datetime
        existing_template.updated_at = datetime.utcnow()
        
        # Save updated template
        updated_template = await self.template_repo.update(existing_template)
        logger.info(f"Updated template {template_id}")
        return updated_template
    
    async def list_templates(self) -> TemplateListResponse:
        """List all active templates."""
        templates = await self.template_repo.list_active()
        return TemplateListResponse(
            templates=templates,
            total=len(templates)
        )
    
    async def create_template_from_yaml(
        self, 
        yaml_content: str, 
        user_id: str
    ) -> Template:
        """Create a template from YAML definition."""
        try:
            template = TemplateParser.parse_yaml_template(yaml_content, user_id)
            created_template = await self.template_repo.create(template)
            logger.info(f"Created template from YAML: {created_template.template_id}")
            return created_template
        except TemplateParseError as e:
            raise ValidationError(f"Invalid template YAML: {e}")
    
    async def validate_template_yaml(self, yaml_content: str) -> List[str]:
        """Validate YAML template and return list of errors."""
        return TemplateParser.validate_template_yaml(yaml_content)
    
    async def export_template_to_yaml(self, template_id: str) -> str:
        """Export template to YAML format."""
        template = await self.get_template(template_id)
        return TemplateParser.template_to_yaml(template)
    
    async def apply_template_to_matter(
        self, 
        template: Template, 
        matter: Matter, 
        user_id: str
    ) -> None:
        """Apply a template to a matter."""
        logger.info(f"Applying template {template.template_id} to matter {matter.matter_id}")
        
        try:
            # Generate folder structure and starter documents
            await self.folder_generator.generate_matter_structure(template, matter, user_id)
            
            # Increment template usage count
            await self.template_repo.increment_usage(template.template_id)
            
            # TODO: Create deadlines (will be implemented in deadline management task)
            # TODO: Configure agents (will be implemented in agent runtime task)
            
            logger.info(f"Successfully applied template {template.template_id} to matter {matter.matter_id}")
            
        except FolderGenerationError as e:
            logger.error(f"Error applying template: {e}")
            raise ValidationError(f"Failed to apply template: {e}")
    
    async def get_recommended_templates(
        self, 
        matter_type: str, 
        jurisdiction: str
    ) -> List[Template]:
        """Get recommended templates for a matter type and jurisdiction."""
        templates = await self.template_repo.list_active()
        
        recommended = []
        for template in templates:
            applies_to = template.applies_to
            
            # Check if template applies to the matter type
            practice_areas = applies_to.get("practice_areas", [])
            jurisdictions = applies_to.get("jurisdictions", [])
            
            if (not practice_areas or matter_type in practice_areas) and \
               (not jurisdictions or jurisdiction in jurisdictions):
                recommended.append(template)
        
        # Sort by usage count (most used first)
        recommended.sort(key=lambda t: t.usage_count, reverse=True)
        
        return recommended