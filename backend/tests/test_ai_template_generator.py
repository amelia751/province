"""Tests for AI template generator service."""

import pytest
from unittest.mock import AsyncMock, patch
from province.services.ai_template_generator import AITemplateGenerator
from province.models.template import Template


class TestAITemplateGenerator:
    """Test AI template generator functionality."""
    
    @pytest.fixture
    def mock_bedrock_response(self):
        """Mock Bedrock response with sample YAML."""
        return {
            "content": [
                {
                    "text": '''
name: "Test Legal Template"
description: "AI-generated test template"
version: "1.0.0"
applies_to:
  practice_areas:
    - "litigation"
  matter_types:
    - "civil"
  jurisdictions:
    - "US-CA"

folders:
  - name: "Pleadings"
    subfolders:
      - "Motions"
      - "Briefs"
  - name: "Discovery"

starter_docs:
  - path: "Pleadings/complaint.md"
    auto_generate: true
    template_content: |
      # Complaint Template
      
      ## Case Information
      - Case Number: [CASE_NUMBER]
      - Plaintiff: [PLAINTIFF_NAME]
      - Defendant: [DEFENDANT_NAME]

deadlines:
  - name: "Response Deadline"
    compute:
      from_field: "service_date"
      relativedelta: "days=30"
    reminders:
      - "-7d"
      - "-3d"
    required: true

agents:
  - name: "LitigationAgent"
    skills:
      - "pleading_drafting"
      - "motion_preparation"
    enabled: true

guardrails:
  required_citations: true
  pii_scan_before_share: true
  privilege_review_required: true
  auto_redaction: false
'''
                }
            ]
        }
    
    @pytest.fixture
    def ai_generator(self):
        """Create AI generator with mocked Bedrock client."""
        generator = AITemplateGenerator()
        # Mock the Bedrock client to avoid actual API calls
        generator.bedrock_client = AsyncMock()
        return generator
    
    @pytest.mark.asyncio
    async def test_generate_template_from_description(self, ai_generator, mock_bedrock_response):
        """Test generating template from description."""
        
        # Mock the Bedrock response
        mock_response = AsyncMock()
        mock_response.read.return_value = b'{"content": [{"text": "name: \\"Test Template\\"\ndescription: \\"Test\\"\nversion: \\"1.0.0\\"\nfolders:\n  - name: \\"Documents\\""}]}'
        ai_generator.bedrock_client.invoke_model.return_value = {"body": mock_response}
        
        # Mock the _call_claude method directly
        ai_generator._call_claude = AsyncMock(return_value=mock_bedrock_response["content"][0]["text"])
        
        # Test template generation
        template = await ai_generator.generate_template_from_description(
            description="A template for civil litigation cases",
            practice_area="Litigation",
            matter_type="Civil Dispute",
            jurisdiction="US-CA",
            user_id="test_user"
        )
        
        # Verify template properties
        assert isinstance(template, Template)
        assert template.name == "Test Legal Template"
        assert "AI-generated template for Litigation matters in US-CA" in template.description
        assert len(template.folders) == 2
        assert template.folders[0].name == "Pleadings"
        assert len(template.folders[0].subfolders) == 2
        assert len(template.starter_docs) == 1
        assert len(template.deadlines) == 1
        assert len(template.agents) == 1
        
        # Verify applies_to configuration
        assert "litigation" in template.applies_to["practice_areas"]
        assert "civil dispute" in template.applies_to["matter_types"]
        assert "US-CA" in template.applies_to["jurisdictions"]
    
    @pytest.mark.asyncio
    async def test_enhance_existing_template(self, ai_generator, mock_bedrock_response):
        """Test enhancing an existing template."""
        
        # Create a base template
        from province.models.template import FolderStructure, GuardrailConfig
        base_template = Template(
            template_id="test_id",
            name="Base Template",
            description="Base template for testing",
            version="1.0.0",
            applies_to={"practice_areas": ["litigation"]},
            folders=[FolderStructure(name="Documents")],
            starter_docs=[],
            deadlines=[],
            agents=[],
            guardrails=GuardrailConfig(),
            created_by="test_user"
        )
        
        # Mock the enhancement response
        enhanced_yaml = mock_bedrock_response["content"][0]["text"]
        ai_generator._call_claude = AsyncMock(return_value=enhanced_yaml)
        
        # Test enhancement
        enhanced_template = await ai_generator.enhance_existing_template(
            template=base_template,
            enhancement_request="Add discovery folder and litigation agent",
            user_id="test_user"
        )
        
        # Verify enhancement
        assert isinstance(enhanced_template, Template)
        assert enhanced_template.name == "Test Legal Template"
        assert len(enhanced_template.folders) == 2
        assert any(folder.name == "Discovery" for folder in enhanced_template.folders)
        assert len(enhanced_template.agents) == 1
        assert enhanced_template.agents[0].name == "LitigationAgent"
    
    @pytest.mark.asyncio
    async def test_suggest_template_improvements(self, ai_generator):
        """Test template improvement suggestions."""
        
        # Create a template for analysis
        from province.models.template import FolderStructure, GuardrailConfig
        template = Template(
            template_id="test_id",
            name="Test Template",
            description="Template for testing",
            version="1.0.0",
            applies_to={"practice_areas": ["litigation"]},
            folders=[FolderStructure(name="Documents")],
            starter_docs=[],
            deadlines=[],
            agents=[],
            guardrails=GuardrailConfig(),
            created_by="test_user"
        )
        
        # Mock suggestions response
        suggestions_response = '''[
            "Add automated deadline calculations for statute of limitations",
            "Include document templates for common motions",
            "Configure compliance agents for privilege review",
            "Add integration with calendar systems"
        ]'''
        
        ai_generator._call_claude = AsyncMock(return_value=suggestions_response)
        
        # Test suggestions
        suggestions = await ai_generator.suggest_template_improvements(
            template=template,
            usage_analytics={"usage_count": 10}
        )
        
        # Verify suggestions
        assert isinstance(suggestions, list)
        assert len(suggestions) == 4
        assert "deadline calculations" in suggestions[0]
        assert "document templates" in suggestions[1]
        assert "compliance agents" in suggestions[2]
        assert "calendar systems" in suggestions[3]
    
    def test_extract_yaml_from_response(self, ai_generator):
        """Test YAML extraction from Claude response."""
        
        # Test with code blocks
        response_with_blocks = '''```yaml
name: "Test Template"
description: "Test"
folders:
  - name: "Documents"
```'''
        
        yaml_content = ai_generator._extract_yaml_from_response(response_with_blocks)
        assert 'name: "Test Template"' in yaml_content
        assert "```" not in yaml_content
        
        # Test without code blocks
        response_without_blocks = '''name: "Test Template"
description: "Test"
folders:
  - name: "Documents"'''
        
        yaml_content = ai_generator._extract_yaml_from_response(response_without_blocks)
        assert 'name: "Test Template"' in yaml_content
    
    def test_extract_suggestions_from_response(self, ai_generator):
        """Test suggestions extraction from Claude response."""
        
        # Test with JSON format
        json_response = '''```json
[
  "Suggestion 1: Add more folders",
  "Suggestion 2: Include deadlines",
  "Suggestion 3: Configure agents"
]
```'''
        
        suggestions = ai_generator._extract_suggestions_from_response(json_response)
        assert len(suggestions) == 3
        assert "Add more folders" in suggestions[0]
        assert "Include deadlines" in suggestions[1]
        assert "Configure agents" in suggestions[2]
        
        # Test with plain text format
        text_response = '''- Add more folders for better organization
- Include automated deadline calculations
- Configure AI agents for document review'''
        
        suggestions = ai_generator._extract_suggestions_from_response(text_response)
        assert len(suggestions) == 3
        assert "Add more folders" in suggestions[0]
    
    def test_create_template_generation_prompt(self, ai_generator):
        """Test prompt creation for template generation."""
        
        prompt = ai_generator._create_template_generation_prompt(
            description="Personal injury case management",
            practice_area="Personal Injury",
            matter_type="Motor Vehicle Accident",
            jurisdiction="US-CA",
            additional_context="Focus on medical records"
        )
        
        # Verify prompt contains key elements
        assert "Personal injury case management" in prompt
        assert "Personal Injury" in prompt
        assert "Motor Vehicle Accident" in prompt
        assert "US-CA" in prompt
        assert "medical records" in prompt
        assert "YAML" in prompt
        assert "folders:" in prompt
        assert "starter_docs:" in prompt
        assert "deadlines:" in prompt
    
    def test_create_enhancement_prompt(self, ai_generator):
        """Test prompt creation for template enhancement."""
        
        current_yaml = '''name: "Test Template"
folders:
  - name: "Documents"'''
        
        prompt = ai_generator._create_enhancement_prompt(
            current_yaml=current_yaml,
            enhancement_request="Add discovery folder"
        )
        
        # Verify prompt contains key elements
        assert current_yaml in prompt
        assert "Add discovery folder" in prompt
        assert "enhance" in prompt.lower()
        assert "YAML" in prompt
    
    def test_create_analysis_prompt(self, ai_generator):
        """Test prompt creation for template analysis."""
        
        current_yaml = '''name: "Test Template"
folders:
  - name: "Documents"'''
        
        usage_analytics = {"usage_count": 15, "avg_duration": 180}
        
        prompt = ai_generator._create_analysis_prompt(
            current_yaml=current_yaml,
            usage_analytics=usage_analytics
        )
        
        # Verify prompt contains key elements
        assert current_yaml in prompt
        assert "15" in prompt  # usage_count
        assert "180" in prompt  # avg_duration
        assert "improvement" in prompt.lower()
        assert "suggestions" in prompt.lower()
        assert "JSON" in prompt