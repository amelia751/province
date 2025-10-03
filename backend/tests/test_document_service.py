"""Tests for document service."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from province.services.document import DocumentService
from province.models.document import Document, DocumentCreate, DocumentUpdate, DocumentVersion
from province.core.exceptions import NotFoundError, ValidationError, ConflictError


class TestDocumentService:
    """Test document service functionality."""
    
    @pytest.fixture
    def mock_document_repo(self):
        """Mock document repository."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_s3_client(self):
        """Mock S3 client."""
        return MagicMock()
    
    @pytest.fixture
    def document_service(self, mock_document_repo, mock_s3_client):
        """Document service with mocked dependencies."""
        with patch('boto3.client', return_value=mock_s3_client):
            service = DocumentService(
                document_repo=mock_document_repo,
                bucket_name="test-bucket"
            )
            service.s3_client = mock_s3_client
            return service
    
    @pytest.fixture
    def sample_document(self):
        """Sample document for testing."""
        return Document(
            document_id="test_doc_id",
            matter_id="test_matter_id",
            path="/Pleadings/complaint.pdf",
            filename="complaint.pdf",
            mime_type="application/pdf",
            size=1024,
            version="v1",
            created_by="test_user",
            s3_key="matters/test_matter_id/Pleadings/complaint.pdf#v1",
            metadata={"category": "pleading"}
        )
    
    @pytest.mark.asyncio
    async def test_create_document(self, document_service, mock_document_repo, mock_s3_client):
        """Test creating a document."""
        document_data = DocumentCreate(
            path="/Pleadings/complaint.pdf",
            filename="complaint.pdf",
            mime_type="application/pdf",
            metadata={"category": "pleading"}
        )
        
        mock_document_repo.get_by_matter_and_path.return_value = None
        mock_document_repo.create.return_value = AsyncMock()
        
        mock_s3_client.generate_presigned_post.return_value = {
            'url': 'https://test-bucket.s3.amazonaws.com/',
            'fields': {'key': 'test-key', 'Content-Type': 'application/pdf'}
        }
        
        result = await document_service.create_document(
            "test_matter_id",
            document_data,
            "test_user"
        )
        
        assert result.document_id is not None
        assert result.upload_url == 'https://test-bucket.s3.amazonaws.com/'
        assert 'key' in result.fields
        mock_document_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_document_conflict(self, document_service, mock_document_repo, sample_document):
        """Test creating a document that already exists."""
        document_data = DocumentCreate(
            path="/Pleadings/complaint.pdf",
            filename="complaint.pdf",
            mime_type="application/pdf"
        )
        
        mock_document_repo.get_by_matter_and_path.return_value = sample_document
        
        with pytest.raises(ConflictError, match="Document already exists"):
            await document_service.create_document(
                "test_matter_id",
                document_data,
                "test_user"
            )
    
    @pytest.mark.asyncio
    async def test_get_document(self, document_service, mock_document_repo, sample_document):
        """Test getting a document by ID."""
        mock_document_repo.get_by_id.return_value = sample_document
        
        result = await document_service.get_document("test_doc_id", "test_user")
        
        assert result == sample_document
        mock_document_repo.get_by_id.assert_called_once_with("test_doc_id", "test_user")
    
    @pytest.mark.asyncio
    async def test_get_document_not_found(self, document_service, mock_document_repo):
        """Test getting a non-existent document."""
        mock_document_repo.get_by_id.return_value = None
        
        with pytest.raises(NotFoundError, match="Document test_doc_id not found"):
            await document_service.get_document("test_doc_id", "test_user")
    
    @pytest.mark.asyncio
    async def test_get_document_by_path(self, document_service, mock_document_repo, sample_document):
        """Test getting a document by path."""
        mock_document_repo.get_by_matter_and_path.return_value = sample_document
        
        result = await document_service.get_document_by_path(
            "test_matter_id",
            "/Pleadings/complaint.pdf",
            "test_user"
        )
        
        assert result == sample_document
        mock_document_repo.get_by_matter_and_path.assert_called_once_with(
            "test_matter_id",
            "/Pleadings/complaint.pdf"
        )
    
    @pytest.mark.asyncio
    async def test_list_documents(self, document_service, mock_document_repo, sample_document):
        """Test listing documents."""
        mock_document_repo.list_by_matter.return_value = [sample_document]
        
        result = await document_service.list_documents("test_matter_id", None, "test_user")
        
        assert len(result.documents) == 1
        assert result.documents[0] == sample_document
        assert result.total == 1
        mock_document_repo.list_by_matter.assert_called_once_with("test_matter_id", None)
    
    @pytest.mark.asyncio
    async def test_update_document(self, document_service, mock_document_repo, sample_document):
        """Test updating document metadata."""
        mock_document_repo.get_by_id.return_value = sample_document
        mock_document_repo.update.return_value = sample_document
        
        update_data = DocumentUpdate(
            filename="updated_complaint.pdf",
            metadata={"status": "reviewed"}
        )
        
        result = await document_service.update_document(
            "test_doc_id",
            update_data,
            "test_user"
        )
        
        assert result.filename == "updated_complaint.pdf"
        assert result.metadata["status"] == "reviewed"
        mock_document_repo.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_new_version(self, document_service, mock_document_repo, mock_s3_client, sample_document):
        """Test uploading a new version of a document."""
        mock_document_repo.get_by_id.return_value = sample_document
        mock_s3_client.generate_presigned_post.return_value = {
            'url': 'https://test-bucket.s3.amazonaws.com/',
            'fields': {'key': 'test-key-v2', 'Content-Type': 'application/pdf'}
        }
        
        result = await document_service.upload_new_version(
            "test_doc_id",
            "test_user",
            "application/pdf"
        )
        
        assert result.document_id == "test_doc_id"
        assert result.upload_url == 'https://test-bucket.s3.amazonaws.com/'
        assert 'key' in result.fields
    
    @pytest.mark.asyncio
    async def test_finalize_upload(self, document_service, mock_document_repo, sample_document):
        """Test finalizing document upload."""
        mock_document_repo.get_by_id.return_value = sample_document
        mock_document_repo.update.return_value = sample_document
        
        result = await document_service.finalize_upload(
            "test_doc_id",
            "test_user",
            2048,
            "abc123hash"
        )
        
        assert result.size == 2048
        assert result.content_hash == "abc123hash"
        # Should be called twice: once for document update, once for indexing status
        assert mock_document_repo.update.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_download_url(self, document_service, mock_document_repo, mock_s3_client, sample_document):
        """Test getting download URL."""
        mock_document_repo.get_by_id.return_value = sample_document
        mock_s3_client.generate_presigned_url.return_value = "https://download-url.com"
        
        result = await document_service.get_download_url("test_doc_id", "test_user")
        
        assert result.document_id == "test_doc_id"
        assert result.download_url == "https://download-url.com"
        assert result.filename == "complaint.pdf"
        assert result.mime_type == "application/pdf"
        assert result.size == 1024
    
    @pytest.mark.asyncio
    async def test_delete_document(self, document_service, mock_document_repo, mock_s3_client, sample_document):
        """Test deleting a document."""
        mock_document_repo.get_by_id.return_value = sample_document
        mock_document_repo.delete.return_value = True
        mock_s3_client.delete_object.return_value = {}
        
        result = await document_service.delete_document("test_doc_id", "test_user")
        
        assert result is True
        mock_s3_client.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key=sample_document.s3_key
        )
        mock_document_repo.delete.assert_called_once_with("test_doc_id")
    
    @pytest.mark.asyncio
    async def test_lock_document(self, document_service, mock_document_repo):
        """Test locking a document."""
        mock_document_repo.lock_document.return_value = True
        
        result = await document_service.lock_document("test_doc_id", "test_user")
        
        assert result is True
        mock_document_repo.lock_document.assert_called_once_with("test_doc_id", "test_user")
    
    @pytest.mark.asyncio
    async def test_unlock_document(self, document_service, mock_document_repo):
        """Test unlocking a document."""
        mock_document_repo.unlock_document.return_value = True
        
        result = await document_service.unlock_document("test_doc_id", "test_user")
        
        assert result is True
        mock_document_repo.unlock_document.assert_called_once_with("test_doc_id", "test_user")
    
    @pytest.mark.asyncio
    async def test_search_documents(self, document_service, mock_document_repo, sample_document):
        """Test searching documents."""
        mock_document_repo.search_by_content.return_value = [sample_document]
        
        result = await document_service.search_documents(
            "test_matter_id",
            "complaint",
            "test_user",
            10
        )
        
        assert len(result) == 1
        assert result[0] == sample_document
        mock_document_repo.search_by_content.assert_called_once_with(
            "test_matter_id",
            "complaint",
            10
        )
    
    def test_generate_s3_key(self, document_service):
        """Test S3 key generation."""
        s3_key = document_service._generate_s3_key(
            "matter123",
            "/Pleadings/complaint.pdf",
            "v1"
        )
        
        assert s3_key == "matters/matter123/Pleadings/complaint.pdf#v1"
    
    def test_generate_upload_url(self, document_service, mock_s3_client):
        """Test upload URL generation."""
        mock_s3_client.generate_presigned_post.return_value = {
            'url': 'https://test-bucket.s3.amazonaws.com/',
            'fields': {'key': 'test-key', 'Content-Type': 'application/pdf'}
        }
        
        url, fields = document_service._generate_upload_url(
            "test-key",
            "application/pdf"
        )
        
        assert url == 'https://test-bucket.s3.amazonaws.com/'
        assert fields['key'] == 'test-key'
        assert fields['Content-Type'] == 'application/pdf'
    
    def test_guess_mime_type(self, document_service):
        """Test MIME type guessing."""
        assert document_service._guess_mime_type("test.pdf") == "application/pdf"
        assert document_service._guess_mime_type("test.docx") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert document_service._guess_mime_type("test.unknown") == "application/octet-stream"