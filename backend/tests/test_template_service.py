"""Tests for template service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai_legal_os.services.template import TemplateService
from ai_legal_os.models.template import Template, TemplateCreate, FolderStructure
from ai_legal_os.models.matter import Matter
from ai_legal_os.core.exceptions import NotFoundError, ValidationError


class TestTemplateService:
    """Test template service functionality."""
    
    @pytest.fixture
    def mock_template_repo(self):
        """Mock template repository."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_folder_generator(self):
        """Mock folder generator."""
        return AsyncMock()
    
    @pytest.fixture
    def template_service(self, mock_template_repo, mock_folder_generator):
        """Template service with mocked dependencies."""
        return TemplateService(
            template_repo=mock_template_repo,
            folder_generator=mock_folder_generator
        )
    
    @pytest.fixture
    def sample_template(self):
        """Sample template for testing."""
        return Template(
            template_id="test_template_id",
            name="Test Template",
            description="A test template",
            folders=[
                FolderStructure(name="Pleadings", subfolders=["Complaints"]),
                FolderStructure(name="Discovery")
            ],
            created_by="test_user"
        )
    
    @pytest.fixture
    def sample_matter(self):
        """Sample matter for testing."""
        return Matter(
            matter_id="test_matter_id",
            tenant_id="test_tenant",
            title="Test Matter",
            matter_type="civil",
            jurisdiction="US-CA",
            status="active",
            created_by="test_user"
        )
    
    @pytest.mark.asyncio
    async def test_create_template(self, template_service, mock_template_repo):
        """Test creating a template."""
        template_data = TemplateCreate(
            name="New Template",
            description="A new template"
        )
        
        expected_template = Template(
            template_id="new_template_id",
            name="New Template",
            description="A new template",
            created_by="test_user"
        )
        
        mock_template_repo.create.return_value = expected_template
        
        result = await template_service.create_template(template_data, "test_user")
        
        assert result == expected_template
        mock_template_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_template(self, template_service, mock_template_repo, sample_template):
        """Test getting a template by ID."""
        mock_template_repo.get_by_id.return_value = sample_template
        
        result = await template_service.get_template("test_template_id")
        
        assert result == sample_template
        mock_template_repo.get_by_id.assert_called_once_with("test_template_id", "system")
    
    @pytest.mark.asyncio
    async def test_get_template_not_found(self, template_service, mock_template_repo):
        """Test getting a non-existent template."""
        mock_template_repo.get_by_id.return_value = None
        
        with pytest.raises(NotFoundError, match="Template test_template_id not found"):
            await template_service.get_template("test_template_id")
    
    @pytest.mark.asyncio
    async def test_get_template_by_name(self, template_service, mock_template_repo, sample_template):
        """Test getting a template by name."""
        mock_template_repo.get_by_name.return_value = sample_template
        
        result = await template_service.get_template_by_name("Test Template")
        
        assert result == sample_template
        mock_template_repo.get_by_name.assert_called_once_with("Test Template")
    
    @pytest.mark.asyncio
    async def test_list_templates(self, template_service, mock_template_repo, sample_template):
        """Test listing templates."""
        mock_template_repo.list_active.return_value = [sample_template]
        
        result = await template_service.list_templates()
        
        assert len(result.templates) == 1
        assert result.templates[0] == sample_template
        assert result.total == 1
    
    @pytest.mark.asyncio
    async def test_create_template_from_yaml(self, template_service, mock_template_repo):
        """Test creating template from YAML."""
        yaml_content = """
name: "YAML Template"
description: "Created from YAML"
folders:
  - "Pleadings"
"""
        
        expected_template = Template(
            template_id="yaml_template_id",
            name="YAML Template",
            description="Created from YAML",
            created_by="test_user"
        )
        
        mock_template_repo.create.return_value = expected_template
        
        result = await template_service.create_template_from_yaml(yaml_content, "test_user")
        
        assert result == expected_template
        mock_template_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_template_from_invalid_yaml(self, template_service):
        """Test creating template from invalid YAML."""
        yaml_content = """
invalid: [yaml: syntax
"""
        
        with pytest.raises(ValidationError, match="Invalid template YAML"):
            await template_service.create_template_from_yaml(yaml_content, "test_user")
    
    @pytest.mark.asyncio
    async def test_validate_template_yaml_valid(self, template_service):
        """Test validating valid YAML."""
        yaml_content = """
name: "Valid Template"
description: "A valid template"
"""
        
        errors = await template_service.validate_template_yaml(yaml_content)
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_template_yaml_invalid(self, template_service):
        """Test validating invalid YAML."""
        yaml_content = """
description: "Missing name"
"""
        
        errors = await template_service.validate_template_yaml(yaml_content)
        assert len(errors) > 0
        assert any("name is required" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_export_template_to_yaml(self, template_service, mock_template_repo, sample_template):
        """Test exporting template to YAML."""
        mock_template_repo.get_by_id.return_value = sample_template
        
        result = await template_service.export_template_to_yaml("test_template_id")
        
        assert "name: Test Template" in result
        assert "description: A test template" in result
    
    @pytest.mark.asyncio
    async def test_apply_template_to_matter(
        self, 
        template_service, 
        mock_template_repo, 
        mock_folder_generator,
        sample_template, 
        sample_matter
    ):
        """Test applying template to matter."""
        await template_service.apply_template_to_matter(
            sample_template, 
            sample_matter, 
            "test_user"
        )
        
        mock_folder_generator.generate_matter_structure.assert_called_once_with(
            sample_template, 
            sample_matter, 
            "test_user"
        )
        mock_template_repo.increment_usage.assert_called_once_with("test_template_id")
    
    @pytest.mark.asyncio
    async def test_get_recommended_templates(
        self, 
        template_service, 
        mock_template_repo, 
        sample_template
    ):
        """Test getting recommended templates."""
        # Update sample template to match criteria
        sample_template.applies_to = {
            "practice_areas": ["civil", "commercial"],
            "jurisdictions": ["US-CA", "US-NY"]
        }
        sample_template.usage_count = 5
        
        mock_template_repo.list_active.return_value = [sample_template]
        
        result = await template_service.get_recommended_templates("civil", "US-CA")
        
        assert len(result) == 1
        assert result[0] == sample_template
    
    @pytest.mark.asyncio
    async def test_get_recommended_templates_no_match(
        self, 
        template_service, 
        mock_template_repo, 
        sample_template
    ):
        """Test getting recommended templates with no matches."""
        # Update sample template to not match criteria
        sample_template.applies_to = {
            "practice_areas": ["criminal"],
            "jurisdictions": ["US-TX"]
        }
        
        mock_template_repo.list_active.return_value = [sample_template]
        
        result = await template_service.get_recommended_templates("civil", "US-CA")
        
        assert len(result) == 0