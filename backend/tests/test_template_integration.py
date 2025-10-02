"""Integration tests for template system using real AWS mocks."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from ai_legal_os.models.template import TemplateCreate, Template
from ai_legal_os.services.template import TemplateService
from ai_legal_os.repositories.template import TemplateRepository


class TestTemplateIntegration:
    """Integration tests for template system."""
    
    @pytest.mark.asyncio
    async def test_template_service_create_and_get(self, mock_aws_services):
        """Test creating and retrieving a template."""
        # Create service with mocked AWS
        template_repo = TemplateRepository(table_name="ai-legal-os-templates")
        from ai_legal_os.services.folder_generator import FolderGenerator
        folder_generator = FolderGenerator(bucket_name="test-documents-bucket")
        template_service = TemplateService(template_repo=template_repo, folder_generator=folder_generator)
        
        # Create template
        from ai_legal_os.models.template import FolderStructure, StarterDocument
        template_create = TemplateCreate(
            name="Test Template",
            description="A test template for integration testing",
            applies_to={
                "practice_areas": ["litigation"],
                "matter_types": ["civil"]
            },
            folders=[
                FolderStructure(name="Pleadings"),
                FolderStructure(name="Discovery"),
                FolderStructure(name="Motions")
            ],
            starter_docs=[
                StarterDocument(
                    path="Pleadings/complaint_template.docx",
                    auto_generate=True
                )
            ]
        )
        
        # Create template
        created_template = await template_service.create_template(template_create, "test_user")
        
        assert created_template is not None
        assert created_template.name == "Test Template"
        assert created_template.description == "A test template for integration testing"
        assert created_template.created_by == "test_user"
        assert len(created_template.folders) == 3
        assert created_template.folders[0].name == "Pleadings"
        
        # Get template by ID
        retrieved_template = await template_service.get_template(created_template.template_id)
        
        assert retrieved_template is not None
        assert retrieved_template.template_id == created_template.template_id
        assert retrieved_template.name == created_template.name
        
    @pytest.mark.asyncio
    async def test_template_service_list_templates(self, mock_aws_services):
        """Test listing templates."""
        # Create service with mocked AWS
        template_repo = TemplateRepository(table_name="ai-legal-os-templates")
        from ai_legal_os.services.folder_generator import FolderGenerator
        folder_generator = FolderGenerator(bucket_name="test-documents-bucket")
        template_service = TemplateService(template_repo=template_repo, folder_generator=folder_generator)
        
        # Create multiple templates
        from ai_legal_os.models.template import FolderStructure
        for i in range(3):
            template_create = TemplateCreate(
                name=f"Test Template {i+1}",
                description=f"Test template number {i+1}",
                folders=[
                    FolderStructure(name="Folder1"),
                    FolderStructure(name="Folder2")
                ]
            )
            await template_service.create_template(template_create, "test_user")
        
        # List templates
        templates_response = await template_service.list_templates()
        
        assert templates_response is not None
        assert hasattr(templates_response, 'templates')
        assert len(templates_response.templates) == 3
        assert templates_response.total == 3
        
    @pytest.mark.asyncio
    async def test_template_yaml_operations(self, mock_aws_services):
        """Test YAML import/export operations."""
        # Create service with mocked AWS
        template_repo = TemplateRepository(table_name="ai-legal-os-templates")
        from ai_legal_os.services.folder_generator import FolderGenerator
        folder_generator = FolderGenerator(bucket_name="test-documents-bucket")
        template_service = TemplateService(template_repo=template_repo, folder_generator=folder_generator)
        
        # Test YAML content
        yaml_content = """
name: "YAML Test Template"
description: "Created from YAML"
version: "1.0.0"
applies_to:
  practice_areas:
    - "litigation"
  matter_types:
    - "civil"
folders:
  - "Pleadings"
  - "Discovery"
starter_docs:
  - path: "Pleadings/complaint.docx"
    auto_generate: true
"""
        
        # Create template from YAML
        created_template = await template_service.create_template_from_yaml(yaml_content, "test_user")
        
        assert created_template is not None
        assert created_template.name == "YAML Test Template"
        assert created_template.description == "Created from YAML"
        assert len(created_template.folders) == 2
        assert created_template.folders[0].name == "Pleadings"
        assert created_template.folders[1].name == "Discovery"
        
        # Export template to YAML
        exported_yaml = await template_service.export_template_to_yaml(created_template.template_id)
        
        assert exported_yaml is not None
        assert "YAML Test Template" in exported_yaml
        assert "Created from YAML" in exported_yaml
        assert "Pleadings" in exported_yaml
        
    @pytest.mark.asyncio
    async def test_template_validation(self, mock_aws_services):
        """Test template YAML validation."""
        # Create service with mocked AWS
        template_repo = TemplateRepository(table_name="ai-legal-os-templates")
        from ai_legal_os.services.folder_generator import FolderGenerator
        folder_generator = FolderGenerator(bucket_name="test-documents-bucket")
        template_service = TemplateService(template_repo=template_repo, folder_generator=folder_generator)
        
        # Valid YAML
        valid_yaml = """
name: "Valid Template"
description: "A valid template"
version: "1.0.0"
folders:
  - "Documents"
"""
        
        validation_errors = await template_service.validate_template_yaml(valid_yaml)
        assert len(validation_errors) == 0  # No errors means valid
        
        # Invalid YAML (missing required fields)
        invalid_yaml = """
description: "Missing name field"
folders:
  - "Documents"
"""
        
        validation_errors = await template_service.validate_template_yaml(invalid_yaml)
        assert len(validation_errors) > 0  # Has errors means invalid
        
    @pytest.mark.asyncio
    async def test_template_recommendations(self, mock_aws_services):
        """Test template recommendations."""
        # Create service with mocked AWS
        template_repo = TemplateRepository(table_name="ai-legal-os-templates")
        from ai_legal_os.services.folder_generator import FolderGenerator
        folder_generator = FolderGenerator(bucket_name="test-documents-bucket")
        template_service = TemplateService(template_repo=template_repo, folder_generator=folder_generator)
        
        # Create templates with different applies_to criteria
        from ai_legal_os.models.template import FolderStructure
        litigation_template = TemplateCreate(
            name="Litigation Template",
            description="For litigation matters",
            applies_to={
                "practice_areas": ["litigation"],
                "matter_types": ["civil"]
            },
            folders=[FolderStructure(name="Pleadings")]
        )
        
        contract_template = TemplateCreate(
            name="Contract Template", 
            description="For contract matters",
            applies_to={
                "practice_areas": ["corporate"],
                "matter_types": ["contract"]
            },
            folders=[FolderStructure(name="Contracts")]
        )
        
        await template_service.create_template(litigation_template, "test_user")
        await template_service.create_template(contract_template, "test_user")
        
        # Get recommendations for litigation matter
        recommendations = await template_service.get_recommended_templates(
            matter_type="litigation",
            jurisdiction="us"
        )
        
        assert len(recommendations) >= 1
        assert any(t.name == "Litigation Template" for t in recommendations)
        
        # Get recommendations for contract matter
        recommendations = await template_service.get_recommended_templates(
            matter_type="corporate",
            jurisdiction="us"
        )
        
        assert len(recommendations) >= 1
        assert any(t.name == "Contract Template" for t in recommendations)