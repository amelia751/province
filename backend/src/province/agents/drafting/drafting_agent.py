"""
Legal Drafting Agent

Main drafting agent that orchestrates Bedrock integration, prompt templates,
and citation workflows for comprehensive legal document generation.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from .bedrock_client import DraftingBedrockClient, DraftingRequest, DraftingResponse, ModelType
from .prompt_templates import PromptTemplateManager, DocumentType
from .citation_workflow import CitationWorkflow, CitationValidationResult

logger = logging.getLogger(__name__)


@dataclass
class DraftingAgentRequest:
    """Request for the legal drafting agent"""
    document_type: str
    context: Dict[str, Any]
    matter_id: Optional[str] = None
    jurisdiction: str = "federal"
    model_preference: Optional[str] = None
    include_citations: bool = True
    validate_citations: bool = True
    temperature: float = 0.1
    max_tokens: int = 4000


@dataclass
class DraftingAgentResponse:
    """Response from the legal drafting agent"""
    document_content: str
    document_type: str
    model_used: str
    generation_metadata: Dict[str, Any]
    citation_analysis: Optional[CitationValidationResult] = None
    confidence_score: float = 0.0
    processing_time: float = 0.0
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


class LegalDraftingAgent:
    """
    Main legal drafting agent that combines Bedrock models, prompt templates,
    and citation workflows for comprehensive legal document generation.
    """
    
    def __init__(self, region_name: str = "us-east-1"):
        self.bedrock_client = DraftingBedrockClient(region_name)
        self.template_manager = PromptTemplateManager()
        self.citation_workflow = CitationWorkflow()
        
        # Document type mapping
        self.document_type_mapping = {
            'nda': DocumentType.NDA,
            'non_disclosure_agreement': DocumentType.NDA,
            'employment_agreement': DocumentType.EMPLOYMENT_AGREEMENT,
            'employment_contract': DocumentType.EMPLOYMENT_AGREEMENT,
            'service_agreement': DocumentType.SERVICE_AGREEMENT,
            'consulting_agreement': DocumentType.SERVICE_AGREEMENT,
            'legal_memo': DocumentType.LEGAL_MEMO,
            'memorandum': DocumentType.LEGAL_MEMO,
            'contract': DocumentType.CONTRACT,
            'agreement': DocumentType.CONTRACT
        }
    
    def draft_document(self, request: DraftingAgentRequest) -> DraftingAgentResponse:
        """
        Main method to draft a legal document
        
        Args:
            request: DraftingAgentRequest with document specifications
            
        Returns:
            DraftingAgentResponse with generated document and analysis
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting document drafting: {request.document_type}")
            
            # Step 1: Validate and prepare request
            validated_request = self._validate_request(request)
            
            # Step 2: Generate document using Bedrock
            bedrock_response = self._generate_document(validated_request)
            
            # Step 3: Process citations if requested
            citation_analysis = None
            if request.validate_citations or request.include_citations:
                citation_analysis = self._process_citations(
                    bedrock_response.document_content,
                    request.validate_citations
                )
            
            # Step 4: Generate recommendations
            recommendations = self._generate_recommendations(
                bedrock_response, 
                citation_analysis,
                validated_request
            )
            
            # Step 5: Calculate overall confidence
            confidence_score = self._calculate_overall_confidence(
                bedrock_response,
                citation_analysis
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return DraftingAgentResponse(
                document_content=bedrock_response.document_content,
                document_type=request.document_type,
                model_used=bedrock_response.model_used,
                generation_metadata=bedrock_response.metadata,
                citation_analysis=citation_analysis,
                confidence_score=confidence_score,
                processing_time=processing_time,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error in document drafting: {str(e)}")
            raise
    
    def _validate_request(self, request: DraftingAgentRequest) -> DraftingAgentRequest:
        """Validate and enhance the drafting request"""
        
        # Normalize document type
        doc_type_key = request.document_type.lower().replace(' ', '_')
        if doc_type_key not in self.document_type_mapping:
            logger.warning(f"Unknown document type: {request.document_type}, using generic contract")
            doc_type_key = 'contract'
        
        # Validate context for template
        document_type_enum = self.document_type_mapping[doc_type_key]
        validation_result = self.template_manager.validate_context(document_type_enum, request.context)
        
        if not validation_result['valid']:
            missing_fields = validation_result['missing_required']
            raise ValueError(f"Missing required fields for {request.document_type}: {missing_fields}")
        
        # Set model preference if not specified
        if not request.model_preference:
            # Use document type to select optimal model
            if doc_type_key in ['legal_memo', 'memorandum']:
                request.model_preference = ModelType.NOVA_PRO.value
            elif doc_type_key in ['nda', 'employment_agreement', 'service_agreement']:
                request.model_preference = ModelType.CLAUDE_SONNET.value
            else:
                request.model_preference = ModelType.CLAUDE_SONNET.value
        
        return request
    
    def _generate_document(self, request: DraftingAgentRequest) -> DraftingResponse:
        """Generate document using Bedrock client"""
        
        # Get document type enum
        doc_type_key = request.document_type.lower().replace(' ', '_')
        document_type_enum = self.document_type_mapping[doc_type_key]
        
        # Check if we have a template for this document type
        if document_type_enum in self.template_manager.list_available_templates():
            # Use template-based generation
            return self._generate_with_template(request, document_type_enum)
        else:
            # Use generic generation
            return self._generate_generic(request)
    
    def _generate_with_template(self, request: DraftingAgentRequest, document_type: DocumentType) -> DraftingResponse:
        """Generate document using prompt template"""
        
        # Generate prompts from template
        prompts = self.template_manager.generate_prompt(document_type, request.context)
        
        # Create Bedrock request
        bedrock_request = DraftingRequest(
            document_type=request.document_type,
            content_requirements=prompts['user_prompt'],
            context=request.context,
            model_preference=ModelType(request.model_preference),
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            include_citations=request.include_citations,
            jurisdiction=request.jurisdiction,
            matter_id=request.matter_id
        )
        
        # Override system prompt if template provides one
        # Note: This would require modifying the Bedrock client to accept system prompts
        
        return self.bedrock_client.draft_document(bedrock_request)
    
    def _generate_generic(self, request: DraftingAgentRequest) -> DraftingResponse:
        """Generate document using generic approach"""
        
        # Build generic content requirements
        content_requirements = f"""
        Please draft a {request.document_type} with the following specifications:
        
        Context: {request.context}
        Jurisdiction: {request.jurisdiction}
        
        Ensure the document is:
        - Legally sound and enforceable
        - Properly formatted with appropriate sections
        - Compliant with {request.jurisdiction} law
        - Professional and comprehensive
        """
        
        # Create Bedrock request
        bedrock_request = DraftingRequest(
            document_type=request.document_type,
            content_requirements=content_requirements,
            context=request.context,
            model_preference=ModelType(request.model_preference),
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            include_citations=request.include_citations,
            jurisdiction=request.jurisdiction,
            matter_id=request.matter_id
        )
        
        return self.bedrock_client.draft_document(bedrock_request)
    
    def _process_citations(self, document_content: str, validate: bool = True) -> CitationValidationResult:
        """Process citations in the generated document"""
        
        return self.citation_workflow.process_document(
            text=document_content,
            validate_existing=validate
        )
    
    def _generate_recommendations(self, 
                                bedrock_response: DraftingResponse,
                                citation_analysis: Optional[CitationValidationResult],
                                request: DraftingAgentRequest) -> List[str]:
        """Generate recommendations for the drafted document"""
        
        recommendations = []
        
        # Model-specific recommendations
        if bedrock_response.confidence_score < 0.7:
            recommendations.append("Consider reviewing the generated content for completeness and accuracy")
        
        if bedrock_response.model_used.startswith("amazon.nova-lite"):
            recommendations.append("Consider using Claude Sonnet for more complex legal documents")
        
        # Citation recommendations
        if citation_analysis:
            invalid_citations = citation_analysis.validation_summary.get('invalid_citations', 0)
            if invalid_citations > 0:
                recommendations.append(f"Review and correct {invalid_citations} invalid citations")
            
            if citation_analysis.validation_summary.get('total_citations', 0) == 0:
                if request.document_type.lower() in ['legal_memo', 'memorandum', 'brief']:
                    recommendations.append("Consider adding legal citations to support arguments")
        
        # Document-specific recommendations
        doc_length = len(bedrock_response.document_content.split())
        if doc_length < 200:
            recommendations.append("Document may be too brief - consider adding more detail")
        elif doc_length > 5000:
            recommendations.append("Document is quite lengthy - consider breaking into sections")
        
        # Jurisdiction-specific recommendations
        if request.jurisdiction.lower() != 'federal':
            recommendations.append(f"Ensure compliance with {request.jurisdiction} state-specific requirements")
        
        return recommendations
    
    def _calculate_overall_confidence(self, 
                                    bedrock_response: DraftingResponse,
                                    citation_analysis: Optional[CitationValidationResult]) -> float:
        """Calculate overall confidence score for the drafted document"""
        
        # Start with Bedrock confidence
        confidence = bedrock_response.confidence_score
        
        # Adjust based on citation analysis
        if citation_analysis:
            citation_confidence = citation_analysis.confidence_score
            # Weight: 70% Bedrock, 30% citations
            confidence = (confidence * 0.7) + (citation_confidence * 0.3)
        
        return min(max(confidence, 0.0), 1.0)
    
    def get_available_document_types(self) -> List[Dict[str, Any]]:
        """Get list of available document types with their information"""
        
        document_types = []
        
        # Template-based document types
        for doc_type in self.template_manager.list_available_templates():
            template_info = self.template_manager.get_template_info(doc_type)
            document_types.append({
                'name': doc_type.value,
                'display_name': doc_type.value.replace('_', ' ').title(),
                'has_template': True,
                'required_fields': template_info.get('required_fields', []),
                'optional_fields': template_info.get('optional_fields', [])
            })
        
        # Add generic document types
        generic_types = [
            'contract', 'agreement', 'letter', 'notice', 'policy', 'procedure'
        ]
        
        for doc_type in generic_types:
            if doc_type not in [dt['name'] for dt in document_types]:
                document_types.append({
                    'name': doc_type,
                    'display_name': doc_type.title(),
                    'has_template': False,
                    'required_fields': ['parties', 'jurisdiction'],
                    'optional_fields': ['terms', 'conditions', 'additional_requirements']
                })
        
        return document_types
    
    def get_model_recommendations(self, document_type: str) -> List[Dict[str, Any]]:
        """Get model recommendations for a document type"""
        
        recommendations = self.bedrock_client.get_model_recommendations(document_type)
        
        return [
            {
                'model_type': model.name,
                'model_id': model.value,
                'recommended_for': document_type,
                'reasoning': self._get_model_reasoning(model, document_type)
            }
            for model in recommendations
        ]
    
    def _get_model_reasoning(self, model: ModelType, document_type: str) -> str:
        """Get reasoning for model recommendation"""
        
        reasoning_map = {
            ModelType.CLAUDE_SONNET: "Best for complex legal documents requiring detailed analysis and precise language",
            ModelType.CLAUDE_HAIKU: "Optimal for simple documents and quick drafts",
            ModelType.NOVA_PRO: "Excellent for research-heavy documents and legal analysis",
            ModelType.NOVA_LITE: "Good for routine documents and form-based content"
        }
        
        return reasoning_map.get(model, "General purpose legal document generation")
    
    def preview_template(self, document_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Preview how a template would be filled with given context"""
        
        doc_type_key = document_type.lower().replace(' ', '_')
        if doc_type_key not in self.document_type_mapping:
            return {'error': f'No template available for {document_type}'}
        
        document_type_enum = self.document_type_mapping[doc_type_key]
        
        try:
            validation_result = self.template_manager.validate_context(document_type_enum, context)
            
            if validation_result['valid']:
                prompts = self.template_manager.generate_prompt(document_type_enum, context)
                return {
                    'valid': True,
                    'system_prompt': prompts['system_prompt'][:500] + "...",
                    'user_prompt_preview': prompts['user_prompt'][:1000] + "...",
                    'full_prompts': prompts
                }
            else:
                return {
                    'valid': False,
                    'validation_result': validation_result
                }
                
        except Exception as e:
            return {'error': str(e)}