"""Integration tests for template API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from province.main import create_app


class TestTemplateAPI:
    """Test template API endpoints."""
    
    @pytest.fixture
    def client(self, monkeypatch):
        """Create test client."""
        # Set required environment variables for testing
        monkeypatch.setenv("DOCUMENTS_BUCKET_NAME", "test-bucket")
        monkeypatch.setenv("TEMPLATES_TABLE_NAME", "test-templates-table")
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def mock_template_service(self):
        """Mock template service."""
        return AsyncMock()
    
    def test_list_templates(self, client):
        """Test listing templates endpoint."""
        with patch('province.api.v1.templates.get_template_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.list_templates.return_value = {
                "templates": [],
                "total": 0
            }
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/v1/templates/")
            
            assert response.status_code == 200
            data = response.json()
            assert "templates" in data
            assert "total" in data
    
    def test_create_template(self, client):
        """Test creating template endpoint."""
        with patch('boto3.resource'), \
             patch('province.api.v1.templates.get_template_service') as mock_get_service:
            
            mock_service = AsyncMock()
            mock_template = {
                "template_id": "test_id",
                "name": "Test Template",
                "description": "A test template",
                "version": "1.0.0",
                "applies_to": {},
                "folders": [],
                "starter_docs": [],
                "deadlines": [],
                "agents": [],
                "guardrails": {
                    "required_citations": False,
                    "pii_scan_before_share": True,
                    "privilege_review_required": False,
                    "auto_redaction": False
                },
                "created_by": "test_user",
                "is_active": True,
                "usage_count": 0,
                "created_at": "2025-01-02T10:00:00Z",
                "updated_at": "2025-01-02T10:00:00Z"
            }
            mock_service.create_template.return_value = mock_template
            mock_get_service.return_value = mock_service
            
            template_data = {
                "name": "Test Template",
                "description": "A test template"
            }
            
            response = client.post("/api/v1/templates/", json=template_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Test Template"
    
    def test_validate_template_yaml(self, client):
        """Test validating template YAML endpoint."""
        with patch('province.api.v1.templates.get_template_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.validate_template_yaml.return_value = []
            mock_get_service.return_value = mock_service
            
            yaml_data = {
                "yaml_content": """
name: "Valid Template"
description: "A valid template"
"""
            }
            
            response = client.post("/api/v1/templates/validate-yaml", json=yaml_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["errors"] == []
    
    def test_create_template_from_yaml(self, client):
        """Test creating template from YAML endpoint."""
        with patch('boto3.resource'), \
             patch('province.api.v1.templates.get_template_service') as mock_get_service:
            
            mock_service = AsyncMock()
            mock_template = {
                "template_id": "yaml_test_id",
                "name": "YAML Template",
                "description": "Created from YAML",
                "version": "1.0.0",
                "applies_to": {},
                "folders": [],
                "starter_docs": [],
                "deadlines": [],
                "agents": [],
                "guardrails": {
                    "required_citations": False,
                    "pii_scan_before_share": True,
                    "privilege_review_required": False,
                    "auto_redaction": False
                },
                "created_by": "test_user",
                "is_active": True,
                "usage_count": 0,
                "created_at": "2025-01-02T10:00:00Z",
                "updated_at": "2025-01-02T10:00:00Z"
            }
            mock_service.create_template_from_yaml.return_value = mock_template
            mock_get_service.return_value = mock_service
            
            yaml_data = {
                "yaml_content": """
name: "YAML Template"
description: "Created from YAML"
folders:
  - "Pleadings"
"""
            }
            
            response = client.post("/api/v1/templates/from-yaml", json=yaml_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "YAML Template"
    
    def test_get_template_recommendations(self, client):
        """Test getting template recommendations endpoint."""
        with patch('province.api.v1.templates.get_template_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_recommended_templates.return_value = []
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/v1/templates/recommendations?matter_type=civil&jurisdiction=US-CA")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    
    def test_get_template_by_id(self, client):
        """Test getting template by ID endpoint."""
        with patch('boto3.resource'), \
             patch('province.api.v1.templates.get_template_service') as mock_get_service:
            
            mock_service = AsyncMock()
            mock_template = {
                "template_id": "test_id",
                "name": "Test Template",
                "description": "A test template",
                "version": "1.0.0",
                "applies_to": {},
                "folders": [],
                "starter_docs": [],
                "deadlines": [],
                "agents": [],
                "guardrails": {
                    "required_citations": False,
                    "pii_scan_before_share": True,
                    "privilege_review_required": False,
                    "auto_redaction": False
                },
                "created_by": "test_user",
                "is_active": True,
                "usage_count": 0,
                "created_at": "2025-01-02T10:00:00Z",
                "updated_at": "2025-01-02T10:00:00Z"
            }
            mock_service.get_template.return_value = mock_template
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/v1/templates/test_id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["template_id"] == "test_id"
    
    def test_export_template_to_yaml(self, client):
        """Test exporting template to YAML endpoint."""
        with patch('boto3.resource'), \
             patch('province.api.v1.templates.get_template_service') as mock_get_service:
            
            mock_service = AsyncMock()
            mock_service.export_template_to_yaml.return_value = """
name: Test Template
description: A test template
"""
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/v1/templates/test_id/yaml")
            
            assert response.status_code == 200
            data = response.json()
            assert "yaml_content" in data
            assert "Test Template" in data["yaml_content"]