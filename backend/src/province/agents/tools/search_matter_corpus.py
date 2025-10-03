"""
AWS Lambda Function: Search Matter Corpus

This Lambda function searches through legal documents using OpenSearch Serverless.
Deployed as: province-search-matter-corpus
"""

import json
import boto3
import logging
import os
from typing import Dict, Any, List
from opensearchpy import OpenSearch, RequestsHttpConnection
from aws_requests_auth.aws_auth import AWSRequestsAuth

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Search legal documents using OpenSearch Serverless
    
    Args:
        event: Lambda event containing search parameters
        context: Lambda context
        
    Returns:
        Dict containing search results
    """
    try:
        # Parse request body
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
            
        query = body.get('query', '')
        matter_id = body.get('matter_id')
        document_types = body.get('document_types', [])
        max_results = body.get('max_results', 10)
        
        logger.info(f"Searching for: {query}, matter_id: {matter_id}")
        
        # Initialize OpenSearch client
        opensearch_endpoint = os.environ.get('OPENSEARCH_ENDPOINT')
        if not opensearch_endpoint:
            raise ValueError("OPENSEARCH_ENDPOINT environment variable not set")
            
        region = os.environ.get('AWS_REGION', 'us-east-1')
        service = 'aoss'  # OpenSearch Serverless
        
        credentials = boto3.Session().get_credentials()
        awsauth = AWSRequestsAuth(credentials, region, service)
        
        client = OpenSearch(
            hosts=[{'host': opensearch_endpoint, 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30
        )
        
        # Build search query
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["content^2", "title^3", "summary", "metadata.tags"],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    ],
                    "filter": []
                }
            },
            "highlight": {
                "fields": {
                    "content": {"fragment_size": 150, "number_of_fragments": 3},
                    "title": {},
                    "summary": {}
                }
            },
            "size": min(max_results, 50),  # Cap at 50 results
            "_source": [
                "title", "content", "matter_id", "document_type", 
                "created_at", "author", "metadata", "file_path"
            ],
            "sort": [
                {"_score": {"order": "desc"}},
                {"created_at": {"order": "desc"}}
            ]
        }
        
        # Add matter filter if specified
        if matter_id:
            search_body["query"]["bool"]["filter"].append({
                "term": {"matter_id": matter_id}
            })
            
        # Add document type filter if specified
        if document_types:
            search_body["query"]["bool"]["filter"].append({
                "terms": {"document_type": document_types}
            })
        
        # Execute search
        index_name = os.environ.get('INDEX_NAME', 'legal-documents')
        response = client.search(
            index=index_name,
            body=search_body
        )
        
        # Format results
        results = []
        for hit in response['hits']['hits']:
            source = hit['_source']
            
            # Get highlighted content if available
            highlighted_content = ""
            if 'highlight' in hit:
                if 'content' in hit['highlight']:
                    highlighted_content = " ... ".join(hit['highlight']['content'])
                elif 'summary' in hit['highlight']:
                    highlighted_content = " ... ".join(hit['highlight']['summary'])
            
            result = {
                "document_id": hit['_id'],
                "title": source.get('title', 'Untitled'),
                "content_preview": highlighted_content or source.get('content', '')[:300] + "...",
                "matter_id": source.get('matter_id', ''),
                "document_type": source.get('document_type', 'unknown'),
                "created_at": source.get('created_at', ''),
                "author": source.get('author', ''),
                "file_path": source.get('file_path', ''),
                "relevance_score": hit['_score'],
                "metadata": source.get('metadata', {})
            }
            results.append(result)
        
        # Prepare response
        total_hits = response['hits']['total']['value']
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'result': f"Found {len(results)} documents matching '{query}' (total: {total_hits})",
                'success': True,
                'data': {
                    'documents': results,
                    'total_hits': total_hits,
                    'query': query,
                    'filters': {
                        'matter_id': matter_id,
                        'document_types': document_types
                    }
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'result': f"Search failed: {str(e)}",
                'success': False,
                'error': str(e)
            })
        }


# For local testing
if __name__ == "__main__":
    test_event = {
        "query": "contract law precedents",
        "matter_id": "matter-123",
        "max_results": 5
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))