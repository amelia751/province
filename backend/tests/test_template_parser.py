"""Tests for template parser."""

import pytest
from province.services.template_parser import TemplateParser, TemplateParseError
from province.models.template import Template, FolderStructure, StarterDocument


class TestTemplateParser:
    """Test template parser functionality."""
    
    def test_parse_simple_yaml_template(self):
        """Test parsing a simple YAML template."""
        yaml_content = """
name: "Test Template"
description: "A test template"
version: "1.0.0"
applies_to:
  practice_areas: ["civil", "commercial"]
  jurisdictions: ["US-CA", "US-NY"]

folders:
  - name: "Pleadings"
    subfolders: ["Complaints", "Answers"]
  - "Discovery"
  - "Evidence"

starter_docs:
  - path: "/Research/Notes.md"
    auto_generate: true
    template_content: "# Research Notes\\n\\nMatter: {{matter_title}}"

deadlines:
  - name: "Answer Deadline"
    compute:
      from_field: "service_date"
      relativedelta: "days=30"
    reminders: ["-7d", "-3d", "-1d"]

agents:
  - name: "DraftingAgent"
    skills: ["draft_complaint", "draft_motion"]
    enabled: true

guardrails:
  required_citations: true
  pii_scan_before_share: true
"""
        
        template = TemplateParser.parse_yaml_template(yaml_content, "test_user")
        
        assert template.name == "Test Template"
        assert template.description == "A test template"
        assert template.version == "1.0.0"
        assert template.applies_to["practice_areas"] == ["civil", "commercial"]
        assert template.applies_to["jurisdictions"] == ["US-CA", "US-NY"]
        
        # Check folders
        assert len(template.folders) == 3
        assert template.folders[0].name == "Pleadings"
        assert template.folders[0].subfolders == ["Complaints", "Answers"]
        assert template.folders[1].name == "Discovery"
        assert template.folders[1].subfolders == []
        
        # Check starter docs
        assert len(template.starter_docs) == 1
        assert template.starter_docs[0].path == "/Research/Notes.md"
        assert template.starter_docs[0].auto_generate is True
        
        # Check deadlines
        assert len(template.deadlines) == 1
        assert template.deadlines[0].name == "Answer Deadline"
        
        # Check agents
        assert len(template.agents) == 1
        assert template.agents[0].name == "DraftingAgent"
        assert template.agents[0].skills == ["draft_complaint", "draft_motion"]
        
        # Check guardrails
        assert template.guardrails.required_citations is True
        assert template.guardrails.pii_scan_before_share is True
    
    def test_parse_minimal_yaml_template(self):
        """Test parsing a minimal YAML template."""
        yaml_content = """
name: "Minimal Template"
description: "A minimal template"
"""
        
        template = TemplateParser.parse_yaml_template(yaml_content, "test_user")
        
        assert template.name == "Minimal Template"
        assert template.description == "A minimal template"
        assert template.version == "1.0.0"  # Default version
        assert len(template.folders) == 0
        assert len(template.starter_docs) == 0
        assert len(template.deadlines) == 0
        assert len(template.agents) == 0
    
    def test_parse_invalid_yaml(self):
        """Test parsing invalid YAML."""
        yaml_content = """
name: "Test Template"
description: [invalid: yaml: structure
"""
        
        with pytest.raises(TemplateParseError, match="Invalid YAML"):
            TemplateParser.parse_yaml_template(yaml_content, "test_user")
    
    def test_parse_missing_required_fields(self):
        """Test parsing YAML with missing required fields."""
        yaml_content = """
description: "Missing name"
"""
        
        with pytest.raises(TemplateParseError, match="Template name is required"):
            TemplateParser.parse_yaml_template(yaml_content, "test_user")
    
    def test_template_to_yaml(self):
        """Test converting template to YAML."""
        template = Template(
            template_id="test_id",
            name="Test Template",
            description="A test template",
            version="1.0.0",
            folders=[
                FolderStructure(name="Pleadings", subfolders=["Complaints"]),
                FolderStructure(name="Discovery")
            ],
            starter_docs=[
                StarterDocument(
                    path="/Research/Notes.md",
                    auto_generate=True,
                    template_content="# Notes"
                )
            ],
            created_by="test_user"
        )
        
        yaml_content = TemplateParser.template_to_yaml(template)
        
        assert "name: Test Template" in yaml_content
        assert "description: A test template" in yaml_content
        assert "Pleadings" in yaml_content
        assert "Complaints" in yaml_content
        assert "/Research/Notes.md" in yaml_content
    
    def test_validate_template_yaml_valid(self):
        """Test validating valid YAML template."""
        yaml_content = """
name: "Valid Template"
description: "A valid template"
folders:
  - name: "Pleadings"
    subfolders: ["Complaints"]
starter_docs:
  - path: "/Research/Notes.md"
    auto_generate: true
deadlines:
  - name: "Answer Deadline"
    compute:
      from_field: "service_date"
agents:
  - name: "DraftingAgent"
    skills: ["draft"]
"""
        
        errors = TemplateParser.validate_template_yaml(yaml_content)
        assert len(errors) == 0
    
    def test_validate_template_yaml_invalid(self):
        """Test validating invalid YAML template."""
        yaml_content = """
description: "Missing name"
folders:
  - invalid_folder_structure
starter_docs:
  - invalid_doc_structure
deadlines:
  - invalid_deadline_structure
agents:
  - invalid_agent_structure
"""
        
        errors = TemplateParser.validate_template_yaml(yaml_content)
        assert len(errors) > 0
        assert any("name is required" in error for error in errors)
    
    def test_validate_invalid_yaml_syntax(self):
        """Test validating YAML with syntax errors."""
        yaml_content = """
name: "Test"
invalid: [yaml: syntax
"""
        
        errors = TemplateParser.validate_template_yaml(yaml_content)
        assert len(errors) == 1
        assert "Invalid YAML" in errors[0]