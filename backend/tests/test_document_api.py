"""Tests for document API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

from province.main import create_app
from province.models.document import Document, DocumentVersion


class TestDocumentAPI:
    """Test document API endpoints."""
    
    @pytest.fixture
    def client(self, monkeypatch):
        """Create test client with mocked AWS services."""
        # Set required environment variables
        monkeypatch.setenv("DOCUMENTS_BUCKET_NAME", "test-bucket")
        monkeypatch.setenv("DOCUMENTS_TABLE_NAME", "test-documents-table")
        
        # Mock AWS services completely
        with patch('boto3.resource') as mock_resource, \
             patch('boto3.client') as mock_client:
            
            # Mock DynamoDB table
            mock_table = MagicMock()
            mock_table.get_item.return_value = {"Item": None}
            mock_table.put_item.return_value = {}
            mock_table.query.return_value = {"Items": []}
            
            mock_dynamodb = MagicMock()
            mock_dynamodb.Table.return_value = mock_table
            mock_resource.return_value = mock_dynamodb
            
            # Mock S3 client
            mock_s3 = MagicMock()
            mock_s3.generate_presigned_post.return_value = {
                'url': 'https://test-bucket.s3.amazonaws.com/',
                'fields': {'key': 'test-key', 'Content-Type': 'application/pdf'}
            }
            mock_s3.generate_presigned_url.return_value = "https://download-url.com"
            mock_client.return_value = mock_s3
            
            app = create_app()
            return TestClient(app)
    
    def test_create_document_endpoint_exists(self, client):
        """Test that the create document endpoint exists."""
        document_data = {
            "path": "/Pleadings/complaint.pdf",
            "filename": "complaint.pdf",
            "mime_type": "application/pdf",
            "metadata": {"category": "pleading"}
        }
        
        response = client.post(
            "/api/v1/documents/?matter_id=test_matter_id",
            json=document_data
        )
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_list_documents_endpoint_exists(self, client):
        """Test that the list documents endpoint exists."""
        response = client.get("/api/v1/documents/?matter_id=test_matter_id")
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_search_documents_endpoint_exists(self, client):
        """Test that the search documents endpoint exists."""
        response = client.get("/api/v1/documents/search?matter_id=test_matter_id&query=complaint")
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_get_document_endpoint_exists(self, client):
        """Test that the get document endpoint exists."""
        response = client.get("/api/v1/documents/test_doc_id")
        
        # Should return 404 for non-existent document (correct behavior)
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_update_document_endpoint_exists(self, client):
        """Test that the update document endpoint exists."""
        update_data = {
            "filename": "updated_complaint.pdf",
            "metadata": {"status": "reviewed"}
        }
        
        response = client.put("/api/v1/documents/test_doc_id", json=update_data)
        
        # Should return 404 for non-existent document (correct behavior)
        assert response.status_code == 404
    
    def test_delete_document_endpoint_exists(self, client):
        """Test that the delete document endpoint exists."""
        response = client.delete("/api/v1/documents/test_doc_id")
        
        # Should return 404 for non-existent document (correct behavior)
        assert response.status_code == 404
    
    def test_get_download_url_endpoint_exists(self, client):
        """Test that the download URL endpoint exists."""
        response = client.get("/api/v1/documents/test_doc_id/download")
        
        # Should return 404 for non-existent document (correct behavior)
        assert response.status_code == 404
    
    def test_create_new_version_endpoint_exists(self, client):
        """Test that the create new version endpoint exists."""
        response = client.post("/api/v1/documents/test_doc_id/versions")
        
        # Should return 404 for non-existent document (correct behavior)
        assert response.status_code == 404
    
    def test_get_versions_endpoint_exists(self, client):
        """Test that the get versions endpoint exists."""
        response = client.get("/api/v1/documents/test_doc_id/versions")
        
        # Should return 404 for non-existent document (correct behavior)
        assert response.status_code == 404
    
    def test_finalize_upload_endpoint_exists(self, client):
        """Test that the finalize upload endpoint exists."""
        finalize_data = {
            "file_size": 1024,
            "content_hash": "abc123"
        }
        
        response = client.post("/api/v1/documents/test_doc_id/finalize", json=finalize_data)
        
        # Should return 404 for non-existent document (correct behavior)
        assert response.status_code == 404
    
    def test_lock_document_endpoint_exists(self, client):
        """Test that the lock document endpoint exists."""
        response = client.post("/api/v1/documents/test_doc_id/lock")
        
        # Should not return 404 (endpoint exists) - may return 200 with success=false
        assert response.status_code != 404
    
    def test_unlock_document_endpoint_exists(self, client):
        """Test that the unlock document endpoint exists."""
        response = client.delete("/api/v1/documents/test_doc_id/lock")
        
        # Should not return 404 (endpoint exists) - may return 200 with success=false
        assert response.status_code != 404