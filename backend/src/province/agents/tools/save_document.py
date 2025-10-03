"""
AWS Lambda Function: Save Document

This Lambda function saves documents to S3 and indexes them in OpenSearch.
Deployed as: province-save-document
"""

import json
import boto3
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any
from opensearchpy import OpenSearch, RequestsHttpConnection
from aws_requests_auth.aws_auth import AWSRequestsAuth

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
textract_client = boto3.client('textract')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Save document to S3 and index in OpenSearch
    
    Args:
        event: Lambda event containing document data
        context: Lambda context
        
    Returns:
        Dict containing save results
    """
    try:
        # Parse request body
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
            
        matter_id = body.get('matter_id')
        document_name = body.get('document_name')
        content = body.get('content')
        document_type = body.get('document_type', 'document')
        metadata = body.get('metadata', {})
        
        if not all([matter_id, document_name, content]):
            raise ValueError("Missing required fields: matter_id, document_name, content")
            
        logger.info(f"Saving document: {document_name} for matter: {matter_id}")
        
        # Generate document ID and timestamp
        doc_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        # Prepare S3 key structure
        s3_bucket = os.environ.get('S3_BUCKET')
        if not s3_bucket:
            raise ValueError("S3_BUCKET environment variable not set")
            
        s3_key = f"matters/{matter_id}/documents/{doc_id}/{document_name}"
        
        # Save to S3
        s3_metadata = {
            'matter_id': matter_id,
            'document_type': document_type,
            'created_at': timestamp.isoformat(),
            'document_id': doc_id,
            **{k: str(v) for k, v in metadata.items()}  # Convert all values to strings
        }
        
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=content.encode('utf-8'),
            ContentType='text/plain',
            Metadata=s3_metadata,
            ServerSideEncryption='AES256'
        )
        
        logger.info(f"Document saved to S3: s3://{s3_bucket}/{s3_key}")
        
        # Extract text content for indexing (if it's a file upload)
        indexed_content = content
        
        # If content looks like base64 or binary, try to extract text
        if len(content) > 1000 and not content.strip().startswith('{') and not content.strip().startswith('<'):
            try:
                # Use Textract for text extraction if needed
                # This is a simplified version - in production you'd handle different file types
                pass
            except Exception as e:
                logger.warning(f"Text extraction failed: {str(e)}")
        
        # Index in OpenSearch
        opensearch_endpoint = os.environ.get('OPENSEARCH_ENDPOINT')
        if opensearch_endpoint:
            try:
                region = os.environ.get('AWS_REGION', 'us-east-1')
                service = 'aoss'
                
                credentials = boto3.Session().get_credentials()
                awsauth = AWSRequestsAuth(credentials, region, service)
                
                client = OpenSearch(
                    hosts=[{'host': opensearch_endpoint, 'port': 443}],
                    http_auth=awsauth,
                    use_ssl=True,
                    verify_certs=True,
                    connection_class=RequestsHttpConnection
                )
                
                # Prepare document for indexing
                doc_for_index = {
                    'document_id': doc_id,
                    'title': document_name,
                    'content': indexed_content[:10000],  # Limit content size for indexing
                    'matter_id': matter_id,
                    'document_type': document_type,
                    'created_at': timestamp.isoformat(),
                    'file_path': s3_key,
                    'author': metadata.get('author', 'unknown'),
                    'metadata': metadata,
                    'summary': indexed_content[:500] + "..." if len(indexed_content) > 500 else indexed_content
                }
                
                # Index the document
                index_name = 'legal-documents'
                response = client.index(
                    index=index_name,
                    id=doc_id,
                    body=doc_for_index
                )
                
                logger.info(f"Document indexed in OpenSearch: {response['_id']}")
                
            except Exception as e:
                logger.error(f"OpenSearch indexing failed: {str(e)}")
                # Don't fail the entire operation if indexing fails
        
        # Generate document URL
        document_url = f"s3://{s3_bucket}/{s3_key}"
        
        # Prepare response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'result': f"Document '{document_name}' saved successfully to matter {matter_id}",
                'success': True,
                'data': {
                    'document_id': doc_id,
                    'document_name': document_name,
                    'matter_id': matter_id,
                    'document_type': document_type,
                    's3_location': document_url,
                    's3_key': s3_key,
                    'created_at': timestamp.isoformat(),
                    'metadata': metadata
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Document save error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'result': f"Failed to save document: {str(e)}",
                'success': False,
                'error': str(e)
            })
        }


# For local testing
if __name__ == "__main__":
    test_event = {
        "matter_id": "matter-123",
        "document_name": "test-contract.txt",
        "content": "This is a test contract document with legal content...",
        "document_type": "contract",
        "metadata": {
            "author": "John Doe",
            "department": "Legal"
        }
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))