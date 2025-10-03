"""Document service implementation."""

import hashlib
import logging
import mimetypes
import os
from datetime import datetime, timedelta
from typing import BinaryIO, Dict, List, Optional, Tuple
from urllib.parse import quote

import boto3
from botocore.exceptions import ClientError

from province.core.exceptions import NotFoundError, ValidationError, ConflictError
from province.models.document import (
    Document, DocumentCreate, DocumentUpdate, DocumentUpload, 
    DocumentDownload, DocumentListResponse, DocumentVersion
)
from province.models.base import generate_id
from province.repositories.document import DocumentRepository
from province.services.document_indexer import DocumentIndexer

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for managing documents with S3 storage and versioning."""
    
    def __init__(
        self, 
        document_repo: Optional[DocumentRepository] = None,
        bucket_name: Optional[str] = None,
        indexer: Optional[DocumentIndexer] = None
    ):
        self.document_repo = document_repo or DocumentRepository()
        self.bucket_name = bucket_name or os.environ.get("DOCUMENTS_BUCKET_NAME")
        if not self.bucket_name:
            raise ValueError("Documents bucket name not configured")
        
        self.s3_client = boto3.client("s3")
        self.indexer = indexer or DocumentIndexer()
    
    async def create_document(
        self, 
        matter_id: str, 
        document_data: DocumentCreate, 
        user_id: str
    ) -> DocumentUpload:
        """Create a new document and return upload URL."""
        logger.info(f"Creating document '{document_data.filename}' in matter {matter_id}")
        
        # Validate path
        if not document_data.path.startswith("/"):
            document_data.path = "/" + document_data.path
        
        # Check if document already exists at this path
        existing = await self.document_repo.get_by_matter_and_path(matter_id, document_data.path)
        if existing:
            raise ConflictError(f"Document already exists at path {document_data.path}")
        
        # Generate document ID and S3 key
        document_id = generate_id()
        version = "v1"
        s3_key = self._generate_s3_key(matter_id, document_data.path, version)
        
        # Create document record
        document = Document(
            document_id=document_id,
            matter_id=matter_id,
            path=document_data.path,
            filename=document_data.filename,
            mime_type=document_data.mime_type,
            size=0,  # Will be updated after upload
            version=version,
            created_by=user_id,
            s3_key=s3_key,
            metadata=document_data.metadata
        )
        
        # Save to database
        await self.document_repo.create(document)
        
        # Generate pre-signed upload URL
        upload_url, fields = self._generate_upload_url(s3_key, document_data.mime_type)
        
        return DocumentUpload(
            document_id=document_id,
            upload_url=upload_url,
            fields=fields
        )
    
    async def get_document(self, document_id: str, user_id: str) -> Document:
        """Get a document by ID."""
        document = await self.document_repo.get_by_id(document_id, user_id)
        if not document:
            raise NotFoundError(f"Document {document_id} not found")
        return document
    
    async def get_document_by_path(self, matter_id: str, path: str, user_id: str) -> Document:
        """Get a document by matter ID and path."""
        if not path.startswith("/"):
            path = "/" + path
        
        document = await self.document_repo.get_by_matter_and_path(matter_id, path)
        if not document:
            raise NotFoundError(f"Document not found at path {path}")
        return document
    
    async def list_documents(
        self, 
        matter_id: str, 
        folder: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> DocumentListResponse:
        """List documents in a matter."""
        documents = await self.document_repo.list_by_matter(matter_id, folder)
        return DocumentListResponse(
            documents=documents,
            total=len(documents),
            folder=folder
        )
    
    async def update_document(
        self, 
        document_id: str, 
        update_data: DocumentUpdate, 
        user_id: str
    ) -> Document:
        """Update document metadata."""
        document = await self.get_document(document_id, user_id)
        
        if update_data.filename:
            document.filename = update_data.filename
        
        if update_data.metadata:
            document.metadata.update(update_data.metadata)
        
        document.updated_at = datetime.utcnow()
        
        return await self.document_repo.update(document)
    
    async def upload_new_version(
        self, 
        document_id: str, 
        user_id: str,
        mime_type: Optional[str] = None
    ) -> DocumentUpload:
        """Create a new version of an existing document."""
        document = await self.get_document(document_id, user_id)
        
        # Generate new version
        current_version_num = int(document.version[1:]) if document.version.startswith("v") else 1
        new_version = f"v{current_version_num + 1}"
        
        # Generate new S3 key
        s3_key = self._generate_s3_key(document.matter_id, document.path, new_version)
        
        # Use existing mime type if not provided
        if not mime_type:
            mime_type = document.mime_type
        
        # Generate pre-signed upload URL
        upload_url, fields = self._generate_upload_url(s3_key, mime_type)
        
        return DocumentUpload(
            document_id=document_id,
            upload_url=upload_url,
            fields=fields
        )
    
    async def finalize_upload(
        self, 
        document_id: str, 
        user_id: str,
        file_size: int,
        content_hash: Optional[str] = None
    ) -> Document:
        """Finalize document upload by updating size and creating version record."""
        document = await self.get_document(document_id, user_id)
        
        # Create version record
        version = DocumentVersion(
            version=document.version,
            s3_key=document.s3_key,
            size=file_size,
            created_by=user_id,
            created_at=datetime.utcnow(),
            metadata={"content_hash": content_hash} if content_hash else {}
        )
        
        # Update document
        document.size = file_size
        document.content_hash = content_hash
        document.updated_at = datetime.utcnow()
        
        # Add version to history if this is not the first version
        if document.versions or document.version != "v1":
            await self.document_repo.add_version(document_id, version)
        else:
            document.versions = [version]
            await self.document_repo.update(document)
        
        # Index document for search
        try:
            await self.indexer.index_document(document, self.bucket_name)
            document.indexed = True
            await self.document_repo.update(document)
            logger.info(f"Document {document_id} indexed for search")
        except Exception as e:
            logger.error(f"Failed to index document {document_id}: {e}")
            # Don't fail the upload if indexing fails
        
        return document
    
    async def get_download_url(self, document_id: str, user_id: str, version: Optional[str] = None) -> DocumentDownload:
        """Get a pre-signed download URL for a document."""
        document = await self.get_document(document_id, user_id)
        
        # Determine S3 key based on version
        if version:
            # Find specific version
            target_version = None
            for v in document.versions:
                if v.version == version:
                    target_version = v
                    break
            
            if not target_version:
                raise NotFoundError(f"Version {version} not found for document {document_id}")
            
            s3_key = target_version.s3_key
            size = target_version.size
        else:
            # Use current version
            s3_key = document.s3_key
            size = document.size
        
        # Generate pre-signed download URL
        try:
            download_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=3600  # 1 hour
            )
            
            return DocumentDownload(
                document_id=document_id,
                download_url=download_url,
                filename=document.filename,
                mime_type=document.mime_type,
                size=size
            )
            
        except ClientError as e:
            logger.error(f"Error generating download URL: {e}")
            raise ValidationError("Failed to generate download URL")
    
    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete a document and all its versions."""
        document = await self.get_document(document_id, user_id)
        
        # Delete all versions from S3
        s3_keys_to_delete = [document.s3_key]
        for version in document.versions:
            if version.s3_key != document.s3_key:
                s3_keys_to_delete.append(version.s3_key)
        
        # Delete from S3
        for s3_key in s3_keys_to_delete:
            try:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
                logger.info(f"Deleted S3 object: {s3_key}")
            except ClientError as e:
                logger.error(f"Error deleting S3 object {s3_key}: {e}")
        
        # Remove from search index
        try:
            await self.indexer.remove_from_index(document_id)
            logger.info(f"Document {document_id} removed from search index")
        except Exception as e:
            logger.error(f"Failed to remove document {document_id} from search index: {e}")
        
        # Delete from database
        return await self.document_repo.delete(document_id)
    
    async def get_document_versions(self, document_id: str, user_id: str) -> List[DocumentVersion]:
        """Get all versions of a document."""
        document = await self.get_document(document_id, user_id)
        return document.versions
    
    async def lock_document(self, document_id: str, user_id: str) -> bool:
        """Lock a document for editing."""
        return await self.document_repo.lock_document(document_id, user_id)
    
    async def unlock_document(self, document_id: str, user_id: str) -> bool:
        """Unlock a document."""
        return await self.document_repo.unlock_document(document_id, user_id)
    
    async def search_documents(
        self, 
        matter_id: str, 
        query: str, 
        user_id: str,
        limit: int = 50
    ) -> List[Document]:
        """Search documents by content."""
        return await self.document_repo.search_by_content(matter_id, query, limit)
    
    def _generate_s3_key(self, matter_id: str, path: str, version: str) -> str:
        """Generate S3 key for a document."""
        # Remove leading slash from path
        clean_path = path.lstrip("/")
        return f"matters/{matter_id}/{clean_path}#{version}"
    
    def _generate_upload_url(self, s3_key: str, mime_type: str) -> Tuple[str, Dict[str, str]]:
        """Generate pre-signed upload URL."""
        try:
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fields={'Content-Type': mime_type},
                Conditions=[
                    {'Content-Type': mime_type},
                    ['content-length-range', 1, 100 * 1024 * 1024]  # 1 byte to 100MB
                ],
                ExpiresIn=3600  # 1 hour
            )
            
            return response['url'], response['fields']
            
        except ClientError as e:
            logger.error(f"Error generating upload URL: {e}")
            raise ValidationError("Failed to generate upload URL")
    
    def _calculate_content_hash(self, content: BinaryIO) -> str:
        """Calculate SHA-256 hash of content."""
        hasher = hashlib.sha256()
        for chunk in iter(lambda: content.read(4096), b""):
            hasher.update(chunk)
        content.seek(0)  # Reset file pointer
        return hasher.hexdigest()
    
    def _guess_mime_type(self, filename: str) -> str:
        """Guess MIME type from filename."""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"