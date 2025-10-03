"""Document indexing service for search preparation."""

import hashlib
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

import boto3
from botocore.exceptions import ClientError

from province.models.document import Document

logger = logging.getLogger(__name__)


class DocumentIndexer:
    """Service for indexing documents for search."""
    
    def __init__(self, opensearch_endpoint: Optional[str] = None):
        self.opensearch_endpoint = opensearch_endpoint or os.environ.get("OPENSEARCH_ENDPOINT")
        self.textract_client = boto3.client("textract")
        self.s3_client = boto3.client("s3")
        
        # For now, we'll prepare the indexing structure without OpenSearch
        # This will be ready when OpenSearch Serverless is set up
        self.index_name = "province-documents"
    
    async def index_document(self, document: Document, bucket_name: str) -> bool:
        """Index a document for search."""
        try:
            logger.info(f"Indexing document {document.document_id}: {document.filename}")
            
            # Extract text content from document
            text_content = await self._extract_text_content(document, bucket_name)
            
            # Create search document
            search_doc = self._create_search_document(document, text_content)
            
            # For now, log the search document structure
            # In production, this would be sent to OpenSearch
            logger.info(f"Prepared search document for {document.document_id}")
            logger.debug(f"Search document structure: {json.dumps(search_doc, indent=2, default=str)}")
            
            # Mark document as indexed
            return True
            
        except Exception as e:
            logger.error(f"Error indexing document {document.document_id}: {e}")
            return False
    
    async def remove_from_index(self, document_id: str) -> bool:
        """Remove a document from the search index."""
        try:
            logger.info(f"Removing document {document_id} from search index")
            
            # In production, this would delete from OpenSearch
            # For now, just log the operation
            logger.info(f"Document {document_id} removed from index")
            return True
            
        except Exception as e:
            logger.error(f"Error removing document {document_id} from index: {e}")
            return False
    
    async def update_document_index(self, document: Document, bucket_name: str) -> bool:
        """Update an existing document in the search index."""
        try:
            # Remove old version and add new one
            await self.remove_from_index(document.document_id)
            return await self.index_document(document, bucket_name)
            
        except Exception as e:
            logger.error(f"Error updating document index for {document.document_id}: {e}")
            return False
    
    async def _extract_text_content(self, document: Document, bucket_name: str) -> str:
        """Extract text content from document using AWS Textract."""
        try:
            # Check if document is text-based or needs OCR
            if self._is_text_document(document.mime_type):
                return await self._extract_text_directly(document, bucket_name)
            elif self._is_image_or_pdf(document.mime_type):
                return await self._extract_text_with_textract(document, bucket_name)
            else:
                logger.warning(f"Unsupported document type for text extraction: {document.mime_type}")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting text from document {document.document_id}: {e}")
            return ""
    
    async def _extract_text_directly(self, document: Document, bucket_name: str) -> str:
        """Extract text directly from text-based documents."""
        try:
            # Download document content from S3
            response = self.s3_client.get_object(Bucket=bucket_name, Key=document.s3_key)
            content = response['Body'].read()
            
            # Decode based on mime type
            if document.mime_type.startswith('text/'):
                return content.decode('utf-8', errors='ignore')
            else:
                # For other text formats, try UTF-8 decoding
                return content.decode('utf-8', errors='ignore')
                
        except Exception as e:
            logger.error(f"Error reading text document {document.document_id}: {e}")
            return ""
    
    async def _extract_text_with_textract(self, document: Document, bucket_name: str) -> str:
        """Extract text from images and PDFs using AWS Textract."""
        try:
            # Use Textract to extract text
            response = self.textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': bucket_name,
                        'Name': document.s3_key
                    }
                }
            )
            
            # Extract text from Textract response
            text_lines = []
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    text_lines.append(block['Text'])
            
            return '\n'.join(text_lines)
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UnsupportedDocumentException':
                logger.warning(f"Document {document.document_id} format not supported by Textract")
            else:
                logger.error(f"Textract error for document {document.document_id}: {e}")
            return ""
        except Exception as e:
            logger.error(f"Error using Textract for document {document.document_id}: {e}")
            return ""
    
    def _create_search_document(self, document: Document, text_content: str) -> Dict[str, Any]:
        """Create a search document for indexing."""
        # Extract metadata for search
        search_doc = {
            "document_id": document.document_id,
            "matter_id": document.matter_id,
            "path": document.path,
            "filename": document.filename,
            "mime_type": document.mime_type,
            "size": document.size,
            "version": document.version,
            "created_by": document.created_by,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
            "content": text_content,
            "content_length": len(text_content),
            "content_hash": hashlib.sha256(text_content.encode()).hexdigest(),
            "metadata": document.metadata,
            "indexed_at": datetime.utcnow()
        }
        
        # Add searchable fields
        search_doc["searchable_text"] = f"{document.filename} {text_content}"
        search_doc["folder"] = self._extract_folder_from_path(document.path)
        search_doc["file_extension"] = self._extract_file_extension(document.filename)
        
        # Add document type classification
        search_doc["document_type"] = self._classify_document_type(document.filename, document.mime_type)
        
        return search_doc
    
    def _is_text_document(self, mime_type: str) -> bool:
        """Check if document is text-based."""
        text_types = [
            'text/plain',
            'text/markdown',
            'text/html',
            'application/json',
            'application/xml',
            'text/xml'
        ]
        return mime_type in text_types
    
    def _is_image_or_pdf(self, mime_type: str) -> bool:
        """Check if document is an image or PDF that can be processed by Textract."""
        supported_types = [
            'application/pdf',
            'image/jpeg',
            'image/jpg',
            'image/png',
            'image/tiff',
            'image/tif'
        ]
        return mime_type in supported_types
    
    def _extract_folder_from_path(self, path: str) -> str:
        """Extract folder name from document path."""
        path_parts = path.strip('/').split('/')
        if len(path_parts) > 1:
            return path_parts[0]
        return "root"
    
    def _extract_file_extension(self, filename: str) -> str:
        """Extract file extension from filename."""
        if '.' in filename:
            return filename.split('.')[-1].lower()
        return ""
    
    def _classify_document_type(self, filename: str, mime_type: str) -> str:
        """Classify document type based on filename and mime type."""
        filename_lower = filename.lower()
        
        # Legal document types
        if any(term in filename_lower for term in ['complaint', 'petition', 'pleading']):
            return "pleading"
        elif any(term in filename_lower for term in ['motion', 'brief']):
            return "motion"
        elif any(term in filename_lower for term in ['contract', 'agreement']):
            return "contract"
        elif any(term in filename_lower for term in ['deposition', 'transcript']):
            return "transcript"
        elif any(term in filename_lower for term in ['evidence', 'exhibit']):
            return "evidence"
        elif any(term in filename_lower for term in ['correspondence', 'letter', 'email']):
            return "correspondence"
        elif any(term in filename_lower for term in ['research', 'memo']):
            return "research"
        
        # File type based classification
        elif mime_type.startswith('image/'):
            return "image"
        elif mime_type == 'application/pdf':
            return "pdf"
        elif mime_type.startswith('text/'):
            return "text"
        else:
            return "document"
    
    def get_index_mapping(self) -> Dict[str, Any]:
        """Get the OpenSearch index mapping for documents."""
        return {
            "mappings": {
                "properties": {
                    "document_id": {"type": "keyword"},
                    "matter_id": {"type": "keyword"},
                    "path": {"type": "keyword"},
                    "filename": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "mime_type": {"type": "keyword"},
                    "size": {"type": "long"},
                    "version": {"type": "keyword"},
                    "created_by": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "indexed_at": {"type": "date"},
                    "content": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "content_length": {"type": "long"},
                    "content_hash": {"type": "keyword"},
                    "searchable_text": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "folder": {"type": "keyword"},
                    "file_extension": {"type": "keyword"},
                    "document_type": {"type": "keyword"},
                    "metadata": {
                        "type": "object",
                        "dynamic": True
                    }
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "legal_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                                "stop",
                                "stemmer"
                            ]
                        }
                    }
                }
            }
        }