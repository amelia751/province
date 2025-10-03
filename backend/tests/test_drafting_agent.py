"""
Unit tests for Legal Drafting Agent

Tests the drafting agent functionality including Bedrock integration,
prompt templates, and citation workflows.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.province.agents.drafting.drafting_agent import (
    LegalDraftingAgent, DraftingAgentRequest, DraftingAgentResponse
)
from src.province.agents.drafting.bedrock_client import (
    DraftingBedrockClient, ModelType, DraftingResponse
)
from src.province.agents.drafting.prompt_templates import (
    PromptTemplateManager, DocumentType
)
from src.province.agents.drafting.citation_workflow import (
    CitationWorkflow, Citation, CitationType, CitationValidationResult
)


class TestDraftingBedrockClient:
    """Test the Bedrock client for legal drafting"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.client = DraftingBedrockClient()
    
    def test_model_selection(self):
        """Test optimal model selection based on document type"""
        
        # Test complex document selection
        model = self.client._select_optimal_model('contract')
        assert model == ModelType.CLAUDE_SONNET
        
        # Test research document selection
        model = self.client._select_optimal_model('research_memo')
        assert model == ModelType.NOVA_PRO
        
        # Test simple document selection
        model = self.client._select_optimal_model('letter')
        assert model == ModelType.CLAUDE_HAIKU
        
        # Test unknown document type (should default to Claude Sonnet)
        model = self.client._select_optimal_model('unknown_type')
        assert model == ModelType.CLAUDE_SONNET
    
    def test_prompt_building(self):
        """Test prompt building for document generation"""
        from src.province.agents.drafting.bedrock_client import DraftingRequest
        
        request = DraftingRequest(
            document_type="NDA",
            content_requirements="Draft a standard NDA",
            context={'parties': ['Company A', 'Company B']},
            jurisdiction="California",
            include_citations=True
        )
        
        prompt = self.client._build_prompt(request)
        
        assert "NDA" in prompt
        assert "California" in prompt
        assert "legal citations" in prompt
        assert "Company A" in prompt
    
    def test_citation_extraction(self):
        """Test citation extraction from generated content"""
        
        content = """
        This case is governed by Smith v. Jones, 123 F.3d 456 (9th Cir. 2020).
        See also 42 U.S.C. § 1983 for statutory authority.
        """
        
        citations = self.client._extract_citations(content)
        
        assert len(citations) >= 2
        assert any('123 F.3d 456' in citation['text'] for citation in citations)
        assert any('42 U.S.C. § 1983' in citation['text'] for citation in citations)
    
    def test_confidence_calculation(self):
        """Test confidence score calculation"""
        
        # Test high confidence response
        response = {
            'content': 'A comprehensive legal document with substantial content...' * 50,
            'stop_reason': 'end_turn'
        }
        
        from src.province.agents.drafting.bedrock_client import DraftingRequest
        request = DraftingRequest(
            document_type="contract",
            content_requirements="test",
            context={},
            model_preference=ModelType.CLAUDE_SONNET
        )
        
        score = self.client._calculate_confidence_score(response, request)
        assert 0.8 <= score <= 1.0
        
        # Test low confidence response (truncated)
        response['stop_reason'] = 'max_tokens'
        response['content'] = 'Short content'
        
        score = self.client._calculate_confidence_score(response, request)
        assert score < 0.8


class TestPromptTemplateManager:
    """Test the prompt template manager"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.manager = PromptTemplateManager()
    
    def test_template_availability(self):
        """Test that templates are available for document types"""
        
        available_types = self.manager.list_available_templates()
        
        assert DocumentType.NDA in available_types
        assert DocumentType.EMPLOYMENT_AGREEMENT in available_types
        assert DocumentType.SERVICE_AGREEMENT in available_types
        assert DocumentType.LEGAL_MEMO in available_types
    
    def test_nda_template_generation(self):
        """Test NDA template prompt generation"""
        
        context = {
            'parties': [
                {'name': 'TechCorp Inc.', 'type': 'company'},
                {'name': 'John Smith', 'type': 'individual'}
            ],
            'agreement_type': 'bilateral',
            'purpose': 'Business partnership evaluation',
            'jurisdiction': 'California'
        }
        
        prompts = self.manager.generate_prompt(DocumentType.NDA, context)
        
        assert 'system_prompt' in prompts
        assert 'user_prompt' in prompts
        assert 'TechCorp Inc.' in prompts['user_prompt']
        assert 'California' in prompts['user_prompt']
        assert 'bilateral' in prompts['user_prompt']
    
    def test_context_validation(self):
        """Test context validation for templates"""
        
        # Valid context
        valid_context = {
            'parties': ['Company A', 'Company B'],
            'agreement_type': 'bilateral',
            'purpose': 'Testing',
            'jurisdiction': 'California'
        }
        
        result = self.manager.validate_context(DocumentType.NDA, valid_context)
        assert result['valid'] is True
        assert len(result['missing_required']) == 0
        
        # Invalid context (missing required fields)
        invalid_context = {
            'parties': ['Company A']
            # Missing other required fields
        }
        
        result = self.manager.validate_context(DocumentType.NDA, invalid_context)
        assert result['valid'] is False
        assert len(result['missing_required']) > 0
    
    def test_example_context(self):
        """Test example context retrieval"""
        
        example = self.manager.get_example_context(DocumentType.NDA)
        
        assert 'parties' in example
        assert 'jurisdiction' in example
        assert isinstance(example['parties'], list)


class TestCitationWorkflow:
    """Test the citation workflow"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.workflow = CitationWorkflow()
    
    def test_citation_extraction(self):
        """Test citation extraction from text"""
        
        text = """
        The landmark case Smith v. Jones, 123 F.3d 456 (9th Cir. 2020) established
        the principle. See also 42 U.S.C. § 1983 and 29 C.F.R. § 1630.2.
        """
        
        citations = self.workflow.extract_citations(text)
        
        assert len(citations) >= 3
        
        # Check case citation
        case_citations = [c for c in citations if c.citation_type == CitationType.CASE_LAW]
        assert len(case_citations) >= 1
        assert '123 F.3d 456' in case_citations[0].text
        
        # Check statute citation
        statute_citations = [c for c in citations if c.citation_type == CitationType.STATUTE]
        assert len(statute_citations) >= 1
        assert '42 U.S.C. § 1983' in statute_citations[0].text
        
        # Check regulation citation
        reg_citations = [c for c in citations if c.citation_type == CitationType.REGULATION]
        assert len(reg_citations) >= 1
        assert '29 C.F.R. § 1630.2' in reg_citations[0].text
    
    def test_citation_validation(self):
        """Test citation validation"""
        
        # Create test citations
        valid_citation = Citation(
            text="123 F.3d 456 (9th Cir. 2020)",
            citation_type=CitationType.CASE_LAW,
            components={'volume': '123', 'reporter': 'F.3d', 'page': '456'},
            position=(0, 25)
        )
        
        invalid_citation = Citation(
            text="Invalid Citation Format",
            citation_type=CitationType.UNKNOWN,
            components={},
            position=(26, 50)
        )
        
        citations = [valid_citation, invalid_citation]
        
        # Mock external validation to avoid API calls
        with patch.object(self.workflow, '_validate_citation_content', return_value=0.8):
            validated = self.workflow.validate_citations(citations)
        
        assert len(validated) == 2
        assert validated[0].validation_score > validated[1].validation_score
    
    def test_citation_insertion(self):
        """Test citation insertion into text"""
        
        text = "This is a legal principle."
        suggestions = [
            {
                'position': 25,  # After "principle"
                'citation': 'See Smith v. Jones, 123 F.3d 456 (9th Cir. 2020).'
            }
        ]
        
        result = self.workflow.insert_citations(text, suggestions)
        
        assert 'Smith v. Jones' in result
        assert len(result) > len(text)
    
    def test_document_processing(self):
        """Test complete document processing workflow"""
        
        text = """
        The court held in Smith v. Jones, 123 F.3d 456 (9th Cir. 2020) that
        the statute 42 U.S.C. § 1983 applies to this situation.
        """
        
        # Mock external validation
        with patch.object(self.workflow, '_validate_citation_content', return_value=0.8):
            result = self.workflow.process_document(text, validate_existing=True)
        
        assert isinstance(result, CitationValidationResult)
        assert result.original_text == text
        assert len(result.citations_found) >= 2
        assert 'total_citations' in result.validation_summary
        assert result.confidence_score > 0


class TestLegalDraftingAgent:
    """Test the main legal drafting agent"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.agent = LegalDraftingAgent()
    
    @patch('src.province.agents.drafting.bedrock_client.boto3.client')
    def test_nda_drafting(self, mock_boto_client):
        """Test NDA document drafting"""
        
        # Mock Bedrock response
        mock_bedrock = Mock()
        mock_boto_client.return_value = mock_bedrock
        
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{'text': 'Generated NDA content...'}],
            'usage': {'input_tokens': 100, 'output_tokens': 500}
        }).encode()
        
        mock_bedrock.invoke_model.return_value = mock_response
        
        # Create drafting request
        request = DraftingAgentRequest(
            document_type="nda",
            context={
                'parties': [
                    {'name': 'TechCorp Inc.', 'type': 'company'},
                    {'name': 'John Smith', 'type': 'individual'}
                ],
                'agreement_type': 'bilateral',
                'purpose': 'Business partnership evaluation',
                'jurisdiction': 'California'
            },
            jurisdiction="California",
            include_citations=False,  # Skip citation validation for this test
            validate_citations=False
        )
        
        # Draft document
        response = self.agent.draft_document(request)
        
        assert isinstance(response, DraftingAgentResponse)
        assert response.document_type == "nda"
        assert "Generated NDA content" in response.document_content
        assert response.confidence_score > 0
        assert len(response.recommendations) >= 0
    
    def test_document_type_mapping(self):
        """Test document type mapping and validation"""
        
        # Test valid document type
        request = DraftingAgentRequest(
            document_type="employment_agreement",
            context={
                'employer_name': 'TechCorp Inc.',
                'employee_name': 'Jane Doe',
                'position_title': 'Software Engineer',
                'employment_type': 'at-will',
                'jurisdiction': 'California'
            }
        )
        
        validated = self.agent._validate_request(request)
        assert validated.document_type == "employment_agreement"
        
        # Test invalid context (missing required fields)
        invalid_request = DraftingAgentRequest(
            document_type="nda",
            context={'parties': ['Company A']}  # Missing other required fields
        )
        
        with pytest.raises(ValueError, match="Missing required fields"):
            self.agent._validate_request(invalid_request)
    
    def test_available_document_types(self):
        """Test getting available document types"""
        
        doc_types = self.agent.get_available_document_types()
        
        assert len(doc_types) > 0
        assert any(dt['name'] == 'nda' for dt in doc_types)
        assert any(dt['has_template'] is True for dt in doc_types)
        
        # Check structure
        for doc_type in doc_types:
            assert 'name' in doc_type
            assert 'display_name' in doc_type
            assert 'has_template' in doc_type
            assert 'required_fields' in doc_type
            assert 'optional_fields' in doc_type
    
    def test_model_recommendations(self):
        """Test model recommendations for document types"""
        
        recommendations = self.agent.get_model_recommendations("contract")
        
        assert len(recommendations) > 0
        assert any(rec['model_type'] == 'CLAUDE_SONNET' for rec in recommendations)
        
        # Check structure
        for rec in recommendations:
            assert 'model_type' in rec
            assert 'model_id' in rec
            assert 'reasoning' in rec
    
    def test_template_preview(self):
        """Test template preview functionality"""
        
        context = {
            'parties': [
                {'name': 'Company A', 'type': 'company'},
                {'name': 'Person B', 'type': 'individual'}
            ],
            'agreement_type': 'bilateral',
            'purpose': 'Testing',
            'jurisdiction': 'California'
        }
        
        preview = self.agent.preview_template("nda", context)
        
        assert preview['valid'] is True
        assert 'system_prompt' in preview
        assert 'user_prompt_preview' in preview
        assert 'Company A' in preview['user_prompt_preview']
    
    def test_confidence_calculation(self):
        """Test overall confidence calculation"""
        
        # Mock Bedrock response
        bedrock_response = DraftingResponse(
            document_content="Test content",
            model_used="claude-3-5-sonnet",
            token_usage={'input_tokens': 100, 'output_tokens': 500},
            citations_found=[],
            confidence_score=0.8,
            generation_time=2.5,
            metadata={}
        )
        
        # Mock citation analysis
        citation_analysis = CitationValidationResult(
            original_text="Test content",
            citations_found=[],
            validation_summary={'total_citations': 0},
            corrected_text="Test content",
            confidence_score=0.9
        )
        
        confidence = self.agent._calculate_overall_confidence(
            bedrock_response, 
            citation_analysis
        )
        
        # Should be weighted average: 0.8 * 0.7 + 0.9 * 0.3 = 0.83
        assert 0.82 <= confidence <= 0.84


if __name__ == "__main__":
    pytest.main([__file__])