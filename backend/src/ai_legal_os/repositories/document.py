"""Document repository implementation."""

import json
import logging
import os
from datetime import datetime
from typing import List, Optional

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from ai_legal_os.models.document import Document, DocumentVersion
from ai_legal_os.models.base import generate_id

logger = logging.getLogger(__name__)


class DocumentRepository:
    """Document repository using DynamoDB."""
    
    def __init__(self, table_name: Optional[str] = None):
        self.table_name = table_name or os.environ.get("DOCUMENTS_TABLE_NAME", "ai-legal-os-documents")
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(self.table_name)
    
    async def create(self, document: Document) -> Document:
        """Create a new document."""
        if not document.document_id:
            document.document_id = generate_id()
        
        try:
            item = self._document_to_item(document)
            self.table.put_item(Item=item)
            logger.info(f"Created document {document.document_id}")
            return document
        except ClientError as e:
            logger.error(f"Error creating document: {e}")
            raise
    
    async def get_by_id(self, document_id: str, user_id: str) -> Optional[Document]:
        """Get document by ID."""
        try:
            # Use GSI to query by document_id
            response = self.table.query(
                IndexName="DocumentIdIndex",
                KeyConditionExpression=Key("document_id").eq(document_id),
                Limit=1
            )
            items = response.get("Items", [])
            if items:
                return self._item_to_document(items[0])
            return None
        except ClientError as e:
            logger.error(f"Error getting document {document_id}: {e}")
            return None
    
    async def get_by_matter_and_path(self, matter_id: str, path: str) -> Optional[Document]:
        """Get document by matter ID and path."""
        try:
            # Use composite key for efficient lookup
            matter_path_key = f"{matter_id}#{path}"
            response = self.table.get_item(Key={"matter_id_path": matter_path_key})
            item = response.get("Item")
            if item:
                return self._item_to_document(item)
            return None
        except ClientError as e:
            logger.error(f"Error getting document by matter {matter_id} and path {path}: {e}")
            return None
    
    async def list_by_matter(self, matter_id: str, folder: Optional[str] = None) -> List[Document]:
        """List documents in a matter, optionally filtered by folder."""
        try:
            # Query by matter_id using GSI
            response = self.table.query(
                IndexName="MatterIndex",
                KeyConditionExpression=Key("matter_id").eq(matter_id)
            )
            
            documents = [self._item_to_document(item) for item in response.get("Items", [])]
            
            # Filter by folder if specified
            if folder:
                folder_prefix = folder.rstrip("/") + "/"
                documents = [doc for doc in documents if doc.path.startswith(folder_prefix)]
            
            # Sort by path for consistent ordering
            documents.sort(key=lambda d: d.path)
            
            return documents
            
        except ClientError as e:
            logger.error(f"Error listing documents for matter {matter_id}: {e}")
            return []
    
    async def update(self, document: Document) -> Document:
        """Update an existing document."""
        try:
            item = self._document_to_item(document)
            self.table.put_item(Item=item)
            logger.info(f"Updated document {document.document_id}")
            return document
        except ClientError as e:
            logger.error(f"Error updating document: {e}")
            raise
    
    async def delete(self, document_id: str) -> bool:
        """Delete a document."""
        try:
            # First get the document to find its matter_id_path key
            document = await self.get_by_id(document_id, "system")
            if not document:
                logger.warning(f"Document {document_id} not found for deletion")
                return False
            
            # Delete using the primary key
            matter_path_key = f"{document.matter_id}#{document.path}"
            self.table.delete_item(Key={"matter_id_path": matter_path_key})
            logger.info(f"Deleted document {document_id}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    async def add_version(self, document_id: str, version: DocumentVersion) -> bool:
        """Add a new version to a document."""
        try:
            # Get current document
            document = await self.get_by_id(document_id, "system")
            if not document:
                logger.error(f"Document {document_id} not found for version update")
                return False
            
            # Add new version
            document.versions.append(version)
            
            # Update current version info
            document.version = version.version
            document.s3_key = version.s3_key
            document.size = version.size
            document.updated_at = version.created_at
            
            # Save updated document
            await self.update(document)
            return True
            
        except ClientError as e:
            logger.error(f"Error adding version to document {document_id}: {e}")
            return False
    
    async def get_versions(self, document_id: str) -> List[DocumentVersion]:
        """Get all versions of a document."""
        try:
            document = await self.get_by_id(document_id, "system")
            if document:
                return document.versions
            return []
        except ClientError as e:
            logger.error(f"Error getting versions for document {document_id}: {e}")
            return []
    
    async def search_by_content(self, matter_id: str, query: str, limit: int = 50) -> List[Document]:
        """Search documents by content (placeholder for full-text search)."""
        # This is a simple implementation - in production, this would use OpenSearch
        try:
            documents = await self.list_by_matter(matter_id)
            
            # Simple text matching in filename and metadata
            query_lower = query.lower()
            matching_docs = []
            
            for doc in documents:
                if (query_lower in doc.filename.lower() or 
                    any(query_lower in str(v).lower() for v in doc.metadata.values())):
                    matching_docs.append(doc)
                
                if len(matching_docs) >= limit:
                    break
            
            return matching_docs
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    async def lock_document(self, document_id: str, user_id: str) -> bool:
        """Lock a document for editing."""
        try:
            # First get the document to find its primary key
            document = await self.get_by_id(document_id, user_id)
            if not document:
                logger.error(f"Document {document_id} not found for locking")
                return False
            
            matter_path_key = f"{document.matter_id}#{document.path}"
            self.table.update_item(
                Key={"matter_id_path": matter_path_key},
                UpdateExpression="SET locked_by = :user_id, locked_at = :timestamp",
                ConditionExpression="attribute_not_exists(locked_by) OR locked_by = :user_id",
                ExpressionAttributeValues={
                    ":user_id": user_id,
                    ":timestamp": datetime.utcnow().isoformat()
                }
            )
            logger.info(f"Locked document {document_id} for user {user_id}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.warning(f"Document {document_id} is already locked by another user")
                return False
            logger.error(f"Error locking document {document_id}: {e}")
            return False
    
    async def unlock_document(self, document_id: str, user_id: str) -> bool:
        """Unlock a document."""
        try:
            # First get the document to find its primary key
            document = await self.get_by_id(document_id, user_id)
            if not document:
                logger.error(f"Document {document_id} not found for unlocking")
                return False
            
            matter_path_key = f"{document.matter_id}#{document.path}"
            self.table.update_item(
                Key={"matter_id_path": matter_path_key},
                UpdateExpression="REMOVE locked_by, locked_at",
                ConditionExpression="locked_by = :user_id",
                ExpressionAttributeValues={":user_id": user_id}
            )
            logger.info(f"Unlocked document {document_id} for user {user_id}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.warning(f"Document {document_id} is not locked by user {user_id}")
                return False
            logger.error(f"Error unlocking document {document_id}: {e}")
            return False
    
    def _document_to_item(self, document: Document) -> dict:
        """Convert Document model to DynamoDB item."""
        item = document.model_dump()
        
        # Add composite key for efficient matter+path lookups
        item["matter_id_path"] = f"{document.matter_id}#{document.path}"
        
        # Convert datetime objects to ISO strings
        if document.created_at:
            item["created_at"] = document.created_at.isoformat()
        if document.updated_at:
            item["updated_at"] = document.updated_at.isoformat()
        if document.locked_at:
            item["locked_at"] = document.locked_at.isoformat()
        
        # Convert versions to dict format
        if document.versions:
            item["versions"] = [
                {
                    **version.model_dump(),
                    "created_at": version.created_at.isoformat()
                }
                for version in document.versions
            ]
        
        return item
    
    def _item_to_document(self, item: dict) -> Document:
        """Convert DynamoDB item to Document model."""
        # Convert ISO strings back to datetime objects
        if "created_at" in item and isinstance(item["created_at"], str):
            item["created_at"] = datetime.fromisoformat(item["created_at"])
        if "updated_at" in item and isinstance(item["updated_at"], str):
            item["updated_at"] = datetime.fromisoformat(item["updated_at"])
        if "locked_at" in item and isinstance(item["locked_at"], str):
            item["locked_at"] = datetime.fromisoformat(item["locked_at"])
        
        # Convert versions back to DocumentVersion objects
        if "versions" in item and item["versions"]:
            versions = []
            for version_data in item["versions"]:
                if "created_at" in version_data and isinstance(version_data["created_at"], str):
                    version_data["created_at"] = datetime.fromisoformat(version_data["created_at"])
                versions.append(DocumentVersion(**version_data))
            item["versions"] = versions
        
        # Remove composite key before creating model
        item.pop("matter_id_path", None)
        
        return Document(**item)