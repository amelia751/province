"""Tests for folder generator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from botocore.exceptions import ClientError

from ai_legal_os.services.folder_generator import FolderGenerator, FolderGenerationError
from ai_legal_os.models.template import Template, FolderStructure, StarterDocument
from ai_legal_os.models.matter import Matter


class TestFolderGenerator:
    """Test folder generator functionality."""
    
    @pytest.fixture
    def mock_s3_client(self):
        """Mock S3 client."""
        return MagicMock()
    
    @pytest.fixture
    def folder_generator(self, mock_s3_client):
        """Folder generator with mocked S3 client."""
        with patch('boto3.client', return_value=mock_s3_client):
            generator = FolderGenerator("test-bucket")
            generator.s3_client = mock_s3_client
            return generator
    
    @pytest.fixture
    def sample_template(self):
        """Sample template for testing."""
        return Template(
            template_id="test_template_id",
            name="Test Template",
            description="A test template",
            folders=[
                FolderStructure(name="Pleadings", subfolders=["Complaints", "Answers"]),
                FolderStructure(name="Discovery"),
                FolderStructure(name="Evidence", subfolders=["Documents", "Photos"])
            ],
            starter_docs=[
                StarterDocument(
                    path="/Research/Notes.md",
                    auto_generate=True,
                    template_content="# Research Notes\n\nMatter: {{matter_title}}"
                ),
                StarterDocument(
                    path="/Pleadings/Complaint_Template.docx",
                    generator="complaint_template",
                    auto_generate=False
                )
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
    async def test_generate_matter_structure(
        self, 
        folder_generator, 
        mock_s3_client, 
        sample_template, 
        sample_matter
    ):
        """Test generating complete matter structure."""
        await folder_generator.generate_matter_structure(
            sample_template, 
            sample_matter, 
            "test_user"
        )
        
        # Verify S3 put_object calls for folders
        expected_folder_calls = [
            "matters/test_matter_id/Pleadings/",
            "matters/test_matter_id/Pleadings/Complaints/",
            "matters/test_matter_id/Pleadings/Answers/",
            "matters/test_matter_id/Discovery/",
            "matters/test_matter_id/Evidence/",
            "matters/test_matter_id/Evidence/Documents/",
            "matters/test_matter_id/Evidence/Photos/"
        ]
        
        # Check that folders were created
        folder_calls = [
            call for call in mock_s3_client.put_object.call_args_list
            if call[1]['Body'] == b""  # Empty body indicates folder
        ]
        
        assert len(folder_calls) == len(expected_folder_calls)
        
        # Check that starter documents were created
        doc_calls = [
            call for call in mock_s3_client.put_object.call_args_list
            if call[1]['Body'] != b""  # Non-empty body indicates document
        ]
        
        assert len(doc_calls) == 1  # Only auto_generate=True document should be created
    
    @pytest.mark.asyncio
    async def test_create_folder_structure(
        self, 
        folder_generator, 
        mock_s3_client, 
        sample_template
    ):
        """Test creating folder structure."""
        await folder_generator._create_folder_structure(
            "matters/test_matter_id/", 
            sample_template.folders
        )
        
        # Verify correct number of put_object calls
        assert mock_s3_client.put_object.call_count == 7  # 3 main + 4 subfolders
        
        # Verify specific folder creation
        calls = mock_s3_client.put_object.call_args_list
        folder_keys = [call[1]['Key'] for call in calls]
        
        assert "matters/test_matter_id/Pleadings/" in folder_keys
        assert "matters/test_matter_id/Pleadings/Complaints/" in folder_keys
        assert "matters/test_matter_id/Discovery/" in folder_keys
    
    @pytest.mark.asyncio
    async def test_generate_starter_documents(
        self, 
        folder_generator, 
        mock_s3_client, 
        sample_template, 
        sample_matter
    ):
        """Test generating starter documents."""
        await folder_generator._generate_starter_documents(
            "matters/test_matter_id/",
            sample_template.starter_docs,
            sample_matter,
            "test_user"
        )
        
        # Only one document should be created (auto_generate=True)
        assert mock_s3_client.put_object.call_count == 1
        
        call = mock_s3_client.put_object.call_args_list[0]
        assert call[1]['Key'] == "matters/test_matter_id/Research/Notes.md"
        assert "Test Matter" in call[1]['Body'].decode('utf-8')  # Template substitution
    
    @pytest.mark.asyncio
    async def test_generate_document_content_with_template(
        self, 
        folder_generator, 
        sample_matter
    ):
        """Test generating document content with template substitution."""
        doc = StarterDocument(
            path="/Research/Notes.md",
            template_content="# Research for {{matter_title}}\n\nMatter ID: {{matter_id}}"
        )
        
        content = await folder_generator._generate_document_content(doc, sample_matter)
        
        assert "# Research for Test Matter" in content
        assert "Matter ID: test_matter_id" in content
    
    @pytest.mark.asyncio
    async def test_generate_document_content_with_generator(
        self, 
        folder_generator, 
        sample_matter
    ):
        """Test generating document content with generator function."""
        doc = StarterDocument(
            path="/Research/Notes.md",
            generator="research_template"
        )
        
        content = await folder_generator._generate_document_content(doc, sample_matter)
        
        assert "Case Law Research" in content
        assert "Test Matter" in content
    
    @pytest.mark.asyncio
    async def test_generate_document_content_unknown_generator(
        self, 
        folder_generator, 
        sample_matter
    ):
        """Test generating document content with unknown generator."""
        doc = StarterDocument(
            path="/Research/Notes.md",
            generator="unknown_generator"
        )
        
        content = await folder_generator._generate_document_content(doc, sample_matter)
        
        assert "Generated using unknown_generator" in content
    
    @pytest.mark.asyncio
    async def test_list_matter_folders(self, folder_generator, mock_s3_client):
        """Test listing matter folders."""
        mock_s3_client.list_objects_v2.return_value = {
            "CommonPrefixes": [
                {"Prefix": "matters/test_matter_id/Pleadings/"},
                {"Prefix": "matters/test_matter_id/Discovery/"},
                {"Prefix": "matters/test_matter_id/Evidence/"}
            ]
        }
        
        folders = await folder_generator.list_matter_folders("test_matter_id")
        
        assert folders == ["Discovery", "Evidence", "Pleadings"]  # Sorted
        mock_s3_client.list_objects_v2.assert_called_once_with(
            Bucket="test-bucket",
            Prefix="matters/test_matter_id/",
            Delimiter="/"
        )
    
    @pytest.mark.asyncio
    async def test_delete_matter_structure(self, folder_generator, mock_s3_client):
        """Test deleting matter structure."""
        # Mock paginator
        mock_paginator = MagicMock()
        mock_s3_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "Contents": [
                    {"Key": "matters/test_matter_id/file1.txt"},
                    {"Key": "matters/test_matter_id/file2.txt"}
                ]
            }
        ]
        
        await folder_generator.delete_matter_structure("test_matter_id")
        
        mock_s3_client.delete_objects.assert_called_once()
        delete_call = mock_s3_client.delete_objects.call_args_list[0]
        objects_to_delete = delete_call[1]['Delete']['Objects']
        
        assert len(objects_to_delete) == 2
        assert {"Key": "matters/test_matter_id/file1.txt"} in objects_to_delete
        assert {"Key": "matters/test_matter_id/file2.txt"} in objects_to_delete
    
    @pytest.mark.asyncio
    async def test_s3_error_handling(self, folder_generator, mock_s3_client, sample_template, sample_matter):
        """Test S3 error handling."""
        mock_s3_client.put_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "PutObject"
        )
        
        with pytest.raises(FolderGenerationError, match="Failed to generate folder structure"):
            await folder_generator.generate_matter_structure(
                sample_template, 
                sample_matter, 
                "test_user"
            )
    
    def test_invalid_bucket_configuration(self):
        """Test initialization with invalid bucket configuration."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="Documents bucket name not configured"):
                FolderGenerator()