"""Tests for document repository."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

from province.repositories.document import DocumentRepository
from province.models.document import Document, DocumentVersion


class TestDocumentRepository:
    """Test document repository functionality."""
    
    @pytest.fixture
    def mock_table(self):
        """Mock DynamoDB table."""
        return MagicMock()
    
    @pytest.fixture
    def document_repo(self, mock_table):
        """Document repository with mocked DynamoDB table."""
        with patch('boto3.resource') as mock_resource:
            mock_dynamodb = MagicMock()
            mock_dynamodb.Table.return_value = mock_table
            mock_resource.return_value = mock_dynamodb
            
            repo = DocumentRepository("test-documents-table")
            repo.table = mock_table
            return repo
    
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
            metadata={"category": "pleading"},
            created_at=datetime(2025, 1, 2, 10, 0, 0),
            updated_at=datetime(2025, 1, 2, 10, 0, 0)
        )
    
    @pytest.mark.asyncio
    async def test_create_document(self, document_repo, mock_table, sample_document):
        """Test creating a document."""
        mock_table.put_item.return_value = {}
        
        result = await document_repo.create(sample_document)
        
        assert result == sample_document
        mock_table.put_item.assert_called_once()
        
        # Verify the item structure
        call_args = mock_table.put_item.call_args[1]
        item = call_args['Item']
        assert item['document_id'] == "test_doc_id"
        assert item['matter_id_path'] == "test_matter_id#/Pleadings/complaint.pdf"
        assert item['created_at'] == "2025-01-02T10:00:00"
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, document_repo, mock_table, sample_document):
        """Test getting document by ID."""
        mock_table.query.return_value = {
            'Items': [{
                'document_id': 'test_doc_id',
                'matter_id': 'test_matter_id',
                'path': '/Pleadings/complaint.pdf',
                'filename': 'complaint.pdf',
                'mime_type': 'application/pdf',
                'size': 1024,
                'version': 'v1',
                'created_by': 'test_user',
                's3_key': 'matters/test_matter_id/Pleadings/complaint.pdf#v1',
                'metadata': {'category': 'pleading'},
                'created_at': '2025-01-02T10:00:00',
                'updated_at': '2025-01-02T10:00:00',
                'versions': [],
                'indexed': False
            }]
        }
        
        result = await document_repo.get_by_id("test_doc_id", "test_user")
        
        assert result is not None
        assert result.document_id == "test_doc_id"
        assert result.filename == "complaint.pdf"
        assert isinstance(result.created_at, datetime)
        mock_table.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, document_repo, mock_table):
        """Test getting non-existent document."""
        mock_table.query.return_value = {'Items': []}
        
        result = await document_repo.get_by_id("nonexistent", "test_user")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_matter_and_path(self, document_repo, mock_table):
        """Test getting document by matter and path."""
        mock_table.get_item.return_value = {
            'Item': {
                'document_id': 'test_doc_id',
                'matter_id': 'test_matter_id',
                'path': '/Pleadings/complaint.pdf',
                'filename': 'complaint.pdf',
                'mime_type': 'application/pdf',
                'size': 1024,
                'version': 'v1',
                'created_by': 'test_user',
                's3_key': 'matters/test_matter_id/Pleadings/complaint.pdf#v1',
                'metadata': {},
                'created_at': '2025-01-02T10:00:00',
                'updated_at': '2025-01-02T10:00:00',
                'versions': [],
                'indexed': False
            }
        }
        
        result = await document_repo.get_by_matter_and_path(
            "test_matter_id",
            "/Pleadings/complaint.pdf"
        )
        
        assert result is not None
        assert result.document_id == "test_doc_id"
        mock_table.get_item.assert_called_once_with(
            Key={"matter_id_path": "test_matter_id#/Pleadings/complaint.pdf"}
        )
    
    @pytest.mark.asyncio
    async def test_list_by_matter(self, document_repo, mock_table):
        """Test listing documents by matter."""
        mock_table.query.return_value = {
            'Items': [
                {
                    'document_id': 'doc1',
                    'matter_id': 'test_matter_id',
                    'path': '/Pleadings/complaint.pdf',
                    'filename': 'complaint.pdf',
                    'mime_type': 'application/pdf',
                    'size': 1024,
                    'version': 'v1',
                    'created_by': 'test_user',
                    's3_key': 'key1',
                    'metadata': {},
                    'created_at': '2025-01-02T10:00:00',
                    'updated_at': '2025-01-02T10:00:00',
                    'versions': [],
                    'indexed': False
                },
                {
                    'document_id': 'doc2',
                    'matter_id': 'test_matter_id',
                    'path': '/Discovery/request.pdf',
                    'filename': 'request.pdf',
                    'mime_type': 'application/pdf',
                    'size': 2048,
                    'version': 'v1',
                    'created_by': 'test_user',
                    's3_key': 'key2',
                    'metadata': {},
                    'created_at': '2025-01-02T11:00:00',
                    'updated_at': '2025-01-02T11:00:00',
                    'versions': [],
                    'indexed': False
                }
            ]
        }
        
        result = await document_repo.list_by_matter("test_matter_id")
        
        assert len(result) == 2
        assert result[0].path == "/Discovery/request.pdf"  # Sorted by path
        assert result[1].path == "/Pleadings/complaint.pdf"
        mock_table.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_by_matter_with_folder_filter(self, document_repo, mock_table):
        """Test listing documents filtered by folder."""
        mock_table.query.return_value = {
            'Items': [
                {
                    'document_id': 'doc1',
                    'matter_id': 'test_matter_id',
                    'path': '/Pleadings/complaint.pdf',
                    'filename': 'complaint.pdf',
                    'mime_type': 'application/pdf',
                    'size': 1024,
                    'version': 'v1',
                    'created_by': 'test_user',
                    's3_key': 'key1',
                    'metadata': {},
                    'created_at': '2025-01-02T10:00:00',
                    'updated_at': '2025-01-02T10:00:00',
                    'versions': [],
                    'indexed': False
                },
                {
                    'document_id': 'doc2',
                    'matter_id': 'test_matter_id',
                    'path': '/Discovery/request.pdf',
                    'filename': 'request.pdf',
                    'mime_type': 'application/pdf',
                    'size': 2048,
                    'version': 'v1',
                    'created_by': 'test_user',
                    's3_key': 'key2',
                    'metadata': {},
                    'created_at': '2025-01-02T11:00:00',
                    'updated_at': '2025-01-02T11:00:00',
                    'versions': [],
                    'indexed': False
                }
            ]
        }
        
        result = await document_repo.list_by_matter("test_matter_id", "/Pleadings")
        
        assert len(result) == 1
        assert result[0].path == "/Pleadings/complaint.pdf"
    
    @pytest.mark.asyncio
    async def test_update_document(self, document_repo, mock_table, sample_document):
        """Test updating a document."""
        mock_table.put_item.return_value = {}
        
        result = await document_repo.update(sample_document)
        
        assert result == sample_document
        mock_table.put_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_document(self, document_repo, mock_table):
        """Test deleting a document."""
        mock_table.delete_item.return_value = {}
        
        result = await document_repo.delete("test_doc_id")
        
        assert result is True
        mock_table.delete_item.assert_called_once_with(Key={"document_id": "test_doc_id"})
    
    @pytest.mark.asyncio
    async def test_add_version(self, document_repo, mock_table):
        """Test adding a version to a document."""
        # Mock getting existing document via query
        mock_table.query.return_value = {
            'Items': [{
                'document_id': 'test_doc_id',
                'matter_id': 'test_matter_id',
                'path': '/Pleadings/complaint.pdf',
                'filename': 'complaint.pdf',
                'mime_type': 'application/pdf',
                'size': 1024,
                'version': 'v1',
                'created_by': 'test_user',
                's3_key': 'old_key',
                'metadata': {},
                'created_at': '2025-01-02T10:00:00',
                'updated_at': '2025-01-02T10:00:00',
                'versions': [],
                'indexed': False
            }]
        }
        
        # Mock updating document
        mock_table.put_item.return_value = {}
        
        version = DocumentVersion(
            version="v2",
            s3_key="new_key",
            size=2048,
            created_by="test_user",
            created_at=datetime(2025, 1, 2, 12, 0, 0)
        )
        
        result = await document_repo.add_version("test_doc_id", version)
        
        assert result is True
        mock_table.query.assert_called_once()
        mock_table.put_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lock_document(self, document_repo, mock_table):
        """Test locking a document."""
        mock_table.update_item.return_value = {}
        
        result = await document_repo.lock_document("test_doc_id", "test_user")
        
        assert result is True
        mock_table.update_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lock_document_already_locked(self, document_repo, mock_table):
        """Test locking a document that's already locked."""
        mock_table.update_item.side_effect = ClientError(
            {'Error': {'Code': 'ConditionalCheckFailedException'}},
            'UpdateItem'
        )
        
        result = await document_repo.lock_document("test_doc_id", "test_user")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_unlock_document(self, document_repo, mock_table):
        """Test unlocking a document."""
        mock_table.update_item.return_value = {}
        
        result = await document_repo.unlock_document("test_doc_id", "test_user")
        
        assert result is True
        mock_table.update_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_by_content(self, document_repo, mock_table):
        """Test searching documents by content."""
        mock_table.query.return_value = {
            'Items': [
                {
                    'document_id': 'doc1',
                    'matter_id': 'test_matter_id',
                    'path': '/Pleadings/complaint.pdf',
                    'filename': 'complaint.pdf',
                    'mime_type': 'application/pdf',
                    'size': 1024,
                    'version': 'v1',
                    'created_by': 'test_user',
                    's3_key': 'key1',
                    'metadata': {'description': 'This is a complaint document'},
                    'created_at': '2025-01-02T10:00:00',
                    'updated_at': '2025-01-02T10:00:00',
                    'versions': [],
                    'indexed': False
                }
            ]
        }
        
        result = await document_repo.search_by_content("test_matter_id", "complaint")
        
        assert len(result) == 1
        assert result[0].filename == "complaint.pdf"