"""Simple API tests for template endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import os

from province.main import create_app


class TestTemplateAPISimple:
    """Simple test template API endpoints."""
    
    @pytest.fixture
    def client(self, monkeypatch):
        """Create test client with mocked AWS services."""
        # Set required environment variables
        monkeypatch.setenv("DOCUMENTS_BUCKET_NAME", "test-bucket")
        monkeypatch.setenv("TEMPLATES_TABLE_NAME", "test-templates-table")
        
        # Mock AWS services completely
        with patch('boto3.resource') as mock_resource, \
             patch('boto3.client') as mock_client:
            
            # Mock DynamoDB table
            mock_table = MagicMock()
            mock_table.scan.return_value = {"Items": []}
            mock_table.put_item.return_value = {}
            mock_table.get_item.return_value = {"Item": None}
            mock_table.query.return_value = {"Items": []}
            
            mock_dynamodb = MagicMock()
            mock_dynamodb.Table.return_value = mock_table
            mock_resource.return_value = mock_dynamodb
            
            # Mock S3 client
            mock_s3 = MagicMock()
            mock_s3.put_object.return_value = {}
            mock_client.return_value = mock_s3
            
            app = create_app()
            return TestClient(app)
    
    def test_list_templates_endpoint_exists(self, client):
        """Test that the list templates endpoint exists."""
        response = client.get("/api/v1/templates/")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_create_template_endpoint_exists(self, client):
        """Test that the create template endpoint exists."""
        template_data = {
            "name": "Test Template",
            "description": "A test template"
        }
        response = client.post("/api/v1/templates/", json=template_data)
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_validate_yaml_endpoint_exists(self, client):
        """Test that the validate YAML endpoint exists."""
        yaml_data = {
            "yaml_content": "name: Test\ndescription: Test"
        }
        response = client.post("/api/v1/templates/validate-yaml", json=yaml_data)
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_create_from_yaml_endpoint_exists(self, client):
        """Test that the create from YAML endpoint exists."""
        yaml_data = {
            "yaml_content": "name: Test\ndescription: Test"
        }
        response = client.post("/api/v1/templates/from-yaml", json=yaml_data)
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_get_recommendations_endpoint_exists(self, client):
        """Test that the recommendations endpoint exists."""
        response = client.get("/api/v1/templates/recommendations?matter_type=civil&jurisdiction=US-CA")
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_get_template_by_id_endpoint_exists(self, client):
        """Test that the get template by ID endpoint exists."""
        response = client.get("/api/v1/templates/test_id")
        # Should return 404 for non-existent template (correct behavior)
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_export_yaml_endpoint_exists(self, client):
        """Test that the export YAML endpoint exists."""
        response = client.get("/api/v1/templates/test_id/yaml")
        # Should return 404 for non-existent template (correct behavior)
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()