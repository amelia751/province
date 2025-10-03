"""
AWS Bedrock Knowledge Bases Integration

Knowledge Bases provide AWS managed RAG (Retrieval Augmented Generation).
This module handles integration with Bedrock Knowledge Bases.
"""

import boto3
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeBaseConfig:
    """Configuration for a Bedrock Knowledge Base"""
    knowledge_base_id: str
    name: str
    description: str
    data_source_s3_bucket: str
    opensearch_collection_arn: str
    embedding_model_arn: str


@dataclass
class RetrievalResult:
    """Result from Knowledge Base retrieval"""
    content: str
    score: float
    source_uri: str
    metadata: Dict[str, Any]


class BedrockKnowledgeBaseClient:
    """
    Client for AWS Bedrock Knowledge Bases managed service.
    
    This uses AWS's native RAG implementation, not custom retrieval logic.
    """
    
    def __init__(self, region_name: str = "us-east-1"):
        self.region_name = region_name
        self.bedrock_agent_runtime = boto3.client(
            'bedrock-agent-runtime',
            region_name=region_name
        )
        self.bedrock_agent = boto3.client(
            'bedrock-agent',
            region_name=region_name
        )
        
    def retrieve(
        self,
        knowledge_base_id: str,
        retrieval_query: str,
        number_of_results: int = 10,
        retrieval_configuration: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant documents from Knowledge Base using AWS managed RAG.
        """
        try:
            params = {
                'knowledgeBaseId': knowledge_base_id,
                'retrievalQuery': {
                    'text': retrieval_query
                },
                'retrievalConfiguration': retrieval_configuration or {
                    'vectorSearchConfiguration': {
                        'numberOfResults': number_of_results
                    }
                }
            }
            
            response = self.bedrock_agent_runtime.retrieve(**params)
            
            results = []
            for item in response['retrievalResults']:
                result = RetrievalResult(
                    content=item['content']['text'],
                    score=item['score'],
                    source_uri=item['location']['s3Location']['uri'],
                    metadata=item.get('metadata', {})
                )
                results.append(result)
                
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving from Knowledge Base: {str(e)}")
            raise
            
    def retrieve_and_generate(
        self,
        knowledge_base_id: str,
        input_text: str,
        model_arn: str,
        number_of_results: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve and generate response using AWS managed RAG + generation.
        """
        try:
            response = self.bedrock_agent_runtime.retrieve_and_generate(
                input={
                    'text': input_text
                },
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': knowledge_base_id,
                        'modelArn': model_arn,
                        'retrievalConfiguration': {
                            'vectorSearchConfiguration': {
                                'numberOfResults': number_of_results
                            }
                        }
                    }
                }
            )
            
            return {
                'output': response['output']['text'],
                'citations': response.get('citations', []),
                'session_id': response.get('sessionId')
            }
            
        except Exception as e:
            logger.error(f"Error in retrieve and generate: {str(e)}")
            raise
            
    def get_knowledge_base_info(self, knowledge_base_id: str) -> Dict[str, Any]:
        """Get information about a Knowledge Base"""
        try:
            response = self.bedrock_agent.get_knowledge_base(
                knowledgeBaseId=knowledge_base_id
            )
            return response['knowledgeBase']
        except Exception as e:
            logger.error(f"Error getting knowledge base info: {str(e)}")
            raise
            
    def list_data_sources(self, knowledge_base_id: str) -> List[Dict[str, Any]]:
        """List data sources for a Knowledge Base"""
        try:
            response = self.bedrock_agent.list_data_sources(
                knowledgeBaseId=knowledge_base_id
            )
            return response['dataSourceSummaries']
        except Exception as e:
            logger.error(f"Error listing data sources: {str(e)}")
            raise
            
    def start_ingestion_job(
        self,
        knowledge_base_id: str,
        data_source_id: str,
        description: Optional[str] = None
    ) -> str:
        """Start an ingestion job for a data source"""
        try:
            params = {
                'knowledgeBaseId': knowledge_base_id,
                'dataSourceId': data_source_id
            }
            if description:
                params['description'] = description
                
            response = self.bedrock_agent.start_ingestion_job(**params)
            return response['ingestionJob']['ingestionJobId']
            
        except Exception as e:
            logger.error(f"Error starting ingestion job: {str(e)}")
            raise


class KnowledgeBaseManager:
    """Manager for multiple Knowledge Bases in the legal OS"""
    
    def __init__(self):
        self.client = BedrockKnowledgeBaseClient()
        self.knowledge_bases: Dict[str, KnowledgeBaseConfig] = {}
        
    def register_knowledge_base(self, config: KnowledgeBaseConfig):
        """Register a Knowledge Base configuration"""
        self.knowledge_bases[config.name] = config
        logger.info(f"Registered Knowledge Base: {config.name}")
        
    def search_legal_corpus(
        self,
        query: str,
        matter_id: Optional[str] = None,
        max_results: int = 10
    ) -> List[RetrievalResult]:
        """
        Search the legal document corpus using Knowledge Base.
        """
        # Use the main legal corpus knowledge base
        kb_config = self.knowledge_bases.get('legal_corpus')
        if not kb_config:
            raise ValueError("Legal corpus Knowledge Base not configured")
            
        # Add matter context to query if provided
        enhanced_query = query
        if matter_id:
            enhanced_query = f"Matter {matter_id}: {query}"
            
        return self.client.retrieve(
            knowledge_base_id=kb_config.knowledge_base_id,
            retrieval_query=enhanced_query,
            number_of_results=max_results
        )
        
    def generate_with_context(
        self,
        query: str,
        model_arn: str,
        knowledge_base_name: str = 'legal_corpus'
    ) -> Dict[str, Any]:
        """
        Generate response with Knowledge Base context.
        """
        kb_config = self.knowledge_bases.get(knowledge_base_name)
        if not kb_config:
            raise ValueError(f"Knowledge Base {knowledge_base_name} not configured")
            
        return self.client.retrieve_and_generate(
            knowledge_base_id=kb_config.knowledge_base_id,
            input_text=query,
            model_arn=model_arn
        )


# Global knowledge base manager
knowledge_base_manager = KnowledgeBaseManager()


def register_legal_knowledge_bases():
    """Register the legal OS Knowledge Bases"""
    
    # Main legal corpus Knowledge Base
    legal_corpus_config = KnowledgeBaseConfig(
        knowledge_base_id="KB_LEGAL_CORPUS_ID",  # Will be set during deployment
        name="legal_corpus",
        description="Main legal document corpus with case law, statutes, and precedents",
        data_source_s3_bucket="province-legal-documents",
        opensearch_collection_arn="arn:aws:aoss:us-east-1:ACCOUNT:collection/legal-corpus",
        embedding_model_arn="arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1"
    )
    knowledge_base_manager.register_knowledge_base(legal_corpus_config)
    
    # Matter-specific Knowledge Base (for large matters)
    matter_specific_config = KnowledgeBaseConfig(
        knowledge_base_id="KB_MATTER_SPECIFIC_ID",  # Will be set during deployment
        name="matter_specific",
        description="Matter-specific documents and evidence",
        data_source_s3_bucket="province-matter-documents",
        opensearch_collection_arn="arn:aws:aoss:us-east-1:ACCOUNT:collection/matter-docs",
        embedding_model_arn="arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1"
    )
    knowledge_base_manager.register_knowledge_base(matter_specific_config)


# Initialize knowledge bases
register_legal_knowledge_bases()