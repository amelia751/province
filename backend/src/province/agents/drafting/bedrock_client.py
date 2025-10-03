"""
Bedrock Client for Legal Drafting

Enhanced Bedrock client specifically designed for legal document drafting
with Claude/Nova model access and legal-specific optimizations.
"""

import boto3
import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Supported Bedrock models for legal drafting"""
    CLAUDE_SONNET = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    CLAUDE_HAIKU = "anthropic.claude-3-haiku-20240307-v1:0"
    NOVA_PRO = "amazon.nova-pro-v1:0"
    NOVA_LITE = "amazon.nova-lite-v1:0"


@dataclass
class DraftingRequest:
    """Request for legal document drafting"""
    document_type: str
    content_requirements: str
    context: Dict[str, Any]
    model_preference: ModelType = ModelType.CLAUDE_SONNET
    temperature: float = 0.1
    max_tokens: int = 4000
    include_citations: bool = True
    jurisdiction: str = "federal"
    matter_id: Optional[str] = None


@dataclass
class DraftingResponse:
    """Response from legal document drafting"""
    document_content: str
    model_used: str
    token_usage: Dict[str, int]
    citations_found: List[Dict[str, Any]]
    confidence_score: float
    generation_time: float
    metadata: Dict[str, Any]


class DraftingBedrockClient:
    """
    Enhanced Bedrock client for legal document drafting.
    
    Provides specialized methods for legal document generation with
    Claude and Nova models, including citation handling and legal formatting.
    """
    
    def __init__(self, region_name: str = "us-east-1"):
        self.region_name = region_name
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        self.bedrock = boto3.client('bedrock', region_name=region_name)
        
        # Model-specific configurations
        self.model_configs = {
            ModelType.CLAUDE_SONNET: {
                "max_tokens": 200000,
                "supports_system_prompt": True,
                "best_for": ["complex_contracts", "litigation_documents", "detailed_analysis"]
            },
            ModelType.CLAUDE_HAIKU: {
                "max_tokens": 100000,
                "supports_system_prompt": True,
                "best_for": ["simple_letters", "quick_drafts", "summaries"]
            },
            ModelType.NOVA_PRO: {
                "max_tokens": 200000,
                "supports_system_prompt": False,
                "best_for": ["research_memos", "case_analysis", "precedent_review"]
            },
            ModelType.NOVA_LITE: {
                "max_tokens": 100000,
                "supports_system_prompt": False,
                "best_for": ["form_documents", "routine_correspondence", "basic_drafts"]
            }
        }
    
    def draft_document(self, request: DraftingRequest) -> DraftingResponse:
        """
        Draft a legal document using Bedrock models
        
        Args:
            request: DraftingRequest with document requirements
            
        Returns:
            DraftingResponse with generated document and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            # Select optimal model if not specified
            if not request.model_preference:
                request.model_preference = self._select_optimal_model(request.document_type)
            
            # Generate the document
            response = self._invoke_model(request)
            
            # Post-process the response
            processed_content = self._post_process_content(
                response['content'], 
                request.document_type,
                request.jurisdiction
            )
            
            # Extract citations if requested
            citations = []
            if request.include_citations:
                citations = self._extract_citations(processed_content)
            
            # Calculate metrics
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            confidence_score = self._calculate_confidence_score(response, request)
            
            return DraftingResponse(
                document_content=processed_content,
                model_used=request.model_preference.value,
                token_usage=response.get('usage', {}),
                citations_found=citations,
                confidence_score=confidence_score,
                generation_time=generation_time,
                metadata={
                    'document_type': request.document_type,
                    'jurisdiction': request.jurisdiction,
                    'matter_id': request.matter_id,
                    'generation_timestamp': start_time.isoformat(),
                    'model_config': self.model_configs[request.model_preference]
                }
            )
            
        except Exception as e:
            logger.error(f"Error drafting document: {str(e)}")
            raise
    
    def _select_optimal_model(self, document_type: str) -> ModelType:
        """Select the optimal model based on document type"""
        
        # Model selection logic based on document complexity
        complex_documents = [
            'contract', 'merger_agreement', 'litigation_brief', 
            'patent_application', 'securities_filing'
        ]
        
        simple_documents = [
            'letter', 'email', 'memo', 'notice', 'form'
        ]
        
        research_documents = [
            'research_memo', 'case_analysis', 'legal_opinion',
            'precedent_review', 'statute_analysis'
        ]
        
        if document_type.lower() in complex_documents:
            return ModelType.CLAUDE_SONNET
        elif document_type.lower() in research_documents:
            return ModelType.NOVA_PRO
        elif document_type.lower() in simple_documents:
            return ModelType.CLAUDE_HAIKU
        else:
            # Default to Claude Sonnet for unknown document types
            return ModelType.CLAUDE_SONNET
    
    def _invoke_model(self, request: DraftingRequest) -> Dict[str, Any]:
        """Invoke the specified Bedrock model"""
        
        model_id = request.model_preference.value
        
        # Prepare the prompt
        prompt = self._build_prompt(request)
        
        # Model-specific request formatting
        if model_id.startswith("anthropic.claude"):
            return self._invoke_claude(model_id, prompt, request)
        elif model_id.startswith("amazon.nova"):
            return self._invoke_nova(model_id, prompt, request)
        else:
            raise ValueError(f"Unsupported model: {model_id}")
    
    def _invoke_claude(self, model_id: str, prompt: str, request: DraftingRequest) -> Dict[str, Any]:
        """Invoke Claude model"""
        
        # Claude uses messages format
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": min(request.max_tokens, self.model_configs[request.model_preference]["max_tokens"]),
            "temperature": request.temperature,
            "top_p": 0.9,
            "messages": messages
        }
        
        # Add system prompt for legal context
        if self.model_configs[request.model_preference]["supports_system_prompt"]:
            request_body["system"] = self._get_legal_system_prompt(request.document_type, request.jurisdiction)
        
        response = self.bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        
        return {
            'content': response_body['content'][0]['text'],
            'usage': response_body.get('usage', {}),
            'stop_reason': response_body.get('stop_reason')
        }
    
    def _invoke_nova(self, model_id: str, prompt: str, request: DraftingRequest) -> Dict[str, Any]:
        """Invoke Nova model"""
        
        request_body = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": min(request.max_tokens, self.model_configs[request.model_preference]["max_tokens"]),
                "temperature": request.temperature,
                "topP": 0.9
            }
        }
        
        response = self.bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        
        return {
            'content': response_body['results'][0]['outputText'],
            'usage': {
                'input_tokens': response_body.get('inputTextTokenCount', 0),
                'output_tokens': response_body['results'][0].get('tokenCount', 0)
            }
        }
    
    def _build_prompt(self, request: DraftingRequest) -> str:
        """Build the prompt for legal document drafting"""
        
        context_str = ""
        if request.context:
            context_str = f"\nContext Information:\n{json.dumps(request.context, indent=2)}\n"
        
        citations_instruction = ""
        if request.include_citations:
            citations_instruction = """
- Include proper legal citations where appropriate
- Use Bluebook citation format
- Ensure all citations are accurate and verifiable
- Add [CITATION NEEDED] where additional research is required
"""
        
        prompt = f"""You are a legal document drafting assistant specializing in {request.jurisdiction} law. 

Document Type: {request.document_type}
Jurisdiction: {request.jurisdiction}

Requirements:
{request.content_requirements}
{context_str}
Instructions:
- Draft a complete, professional legal document
- Use appropriate legal language and formatting
- Ensure compliance with {request.jurisdiction} legal standards
- Include all necessary clauses and provisions
- Use clear, precise language while maintaining legal accuracy
{citations_instruction}
- Format the document with proper headings and structure
- Include signature blocks and execution requirements where appropriate

Please draft the complete document:"""

        return prompt
    
    def _get_legal_system_prompt(self, document_type: str, jurisdiction: str) -> str:
        """Get system prompt for legal context"""
        
        return f"""You are an expert legal document drafting assistant with extensive knowledge of {jurisdiction} law. 

Your expertise includes:
- Legal document structure and formatting
- Appropriate legal terminology and phrasing
- Compliance requirements for {jurisdiction}
- Standard clauses and provisions for {document_type} documents
- Legal citation formats and requirements
- Contract law, corporate law, litigation procedures, and regulatory compliance

Always:
- Maintain the highest standards of legal accuracy
- Use precise, unambiguous language
- Follow established legal document conventions
- Include appropriate disclaimers and legal protections
- Ensure documents are enforceable and compliant
- Provide comprehensive coverage of relevant legal issues

Never:
- Provide legal advice beyond document drafting
- Make assumptions about facts not provided
- Include provisions that may be unenforceable
- Use ambiguous or unclear language
- Omit essential legal protections"""
    
    def _post_process_content(self, content: str, document_type: str, jurisdiction: str) -> str:
        """Post-process the generated content for legal formatting"""
        
        # Clean up the content
        processed = content.strip()
        
        # Ensure proper document title
        if not processed.upper().startswith(document_type.upper()):
            title = document_type.replace('_', ' ').title()
            processed = f"{title}\n\n{processed}"
        
        # Add jurisdiction notice if not present
        if jurisdiction.lower() not in processed.lower():
            processed += f"\n\nThis document is governed by {jurisdiction} law."
        
        # Add generation timestamp
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        footer = f"\n\n---\nDocument generated by Province Legal OS on {timestamp}\nThis document should be reviewed by qualified legal counsel before execution."
        
        return processed + footer
    
    def _extract_citations(self, content: str) -> List[Dict[str, Any]]:
        """Extract legal citations from the generated content"""
        
        import re
        
        citations = []
        
        # Common citation patterns
        patterns = {
            'case_citation': r'(\d+)\s+([A-Za-z\.]+)\s+(\d+)(?:\s*\(([^)]+)\))?',
            'statute_citation': r'(\d+)\s+U\.?S\.?C\.?\s*§?\s*(\d+)',
            'federal_register': r'(\d+)\s+Fed\.?\s*Reg\.?\s+(\d+)',
            'cfr_citation': r'(\d+)\s+C\.?F\.?R\.?\s*§?\s*(\d+)'
        }
        
        for citation_type, pattern in patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                citations.append({
                    'type': citation_type,
                    'text': match.group(0),
                    'position': match.span(),
                    'components': match.groups()
                })
        
        return citations
    
    def _calculate_confidence_score(self, response: Dict[str, Any], request: DraftingRequest) -> float:
        """Calculate confidence score for the generated document"""
        
        score = 0.8  # Base score
        
        # Adjust based on model used
        if request.model_preference == ModelType.CLAUDE_SONNET:
            score += 0.1  # Higher confidence for complex model
        
        # Adjust based on stop reason (for Claude)
        if response.get('stop_reason') == 'end_turn':
            score += 0.05  # Natural completion
        elif response.get('stop_reason') == 'max_tokens':
            score -= 0.1  # Truncated response
        
        # Adjust based on content length
        content_length = len(response.get('content', ''))
        if content_length > 1000:
            score += 0.05  # Substantial content
        elif content_length < 500:
            score -= 0.05  # Potentially incomplete
        
        return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """List available models with their capabilities"""
        
        models = []
        for model_type, config in self.model_configs.items():
            models.append({
                'model_type': model_type.name,
                'model_id': model_type.value,
                'max_tokens': config['max_tokens'],
                'supports_system_prompt': config['supports_system_prompt'],
                'best_for': config['best_for']
            })
        
        return models
    
    def get_model_recommendations(self, document_type: str) -> List[ModelType]:
        """Get model recommendations for a document type"""
        
        recommendations = []
        
        for model_type, config in self.model_configs.items():
            if document_type.lower() in [doc.lower() for doc in config['best_for']]:
                recommendations.append(model_type)
        
        # If no specific recommendations, provide general ones
        if not recommendations:
            recommendations = [ModelType.CLAUDE_SONNET, ModelType.NOVA_PRO]
        
        return recommendations