"""AI-powered template generation service using Claude on Bedrock."""

import json
import logging
import os
from typing import Dict, List, Optional, Any
import boto3
from botocore.exceptions import ClientError

from ai_legal_os.core.exceptions import ValidationError
from ai_legal_os.models.template import Template, FolderStructure, StarterDocument, DeadlineRule, AgentConfig, GuardrailConfig
from ai_legal_os.services.template_parser import TemplateParser
from ai_legal_os.models.base import generate_id

logger = logging.getLogger(__name__)


class AITemplateGenerator:
    """Service for generating legal matter templates using AI."""
    
    def __init__(self, model_id: str = None, region: str = None):
        # Get configuration from environment or use defaults
        self.model_id = model_id or os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
        self.region = region or os.environ.get("BEDROCK_REGION", "us-east-1")
        
        # Check for Bedrock-specific credentials
        bedrock_access_key = os.environ.get("BEDROCK_AWS_ACCESS_KEY_ID")
        bedrock_secret_key = os.environ.get("BEDROCK_AWS_SECRET_ACCESS_KEY")
        
        try:
            if bedrock_access_key and bedrock_secret_key:
                # Use Bedrock-specific credentials
                logger.info("Using Bedrock-specific AWS credentials")
                self.bedrock_client = boto3.client(
                    "bedrock-runtime",
                    region_name=self.region,
                    aws_access_key_id=bedrock_access_key,
                    aws_secret_access_key=bedrock_secret_key
                )
            else:
                # Use standard AWS credentials from environment or default profile
                logger.info("Using standard AWS credentials")
                self.bedrock_client = boto3.client("bedrock-runtime", region_name=self.region)
                
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise ValidationError(f"Cannot initialize Bedrock client: {e}")
        
        logger.info(f"Initialized AI Template Generator with model {self.model_id} in region {self.region}")
        
        # Skip validation for now - will be enabled once credentials are working
        # self._validate_model_access()
    
    async def generate_template_from_description(
        self, 
        description: str, 
        practice_area: str,
        matter_type: str,
        jurisdiction: str,
        user_id: str,
        additional_context: Optional[str] = None
    ) -> Template:
        """Generate a complete legal matter template from natural language description."""
        
        logger.info(f"Generating template for {practice_area} - {matter_type} in {jurisdiction}")
        
        # Create the prompt for Claude
        prompt = self._create_template_generation_prompt(
            description, practice_area, matter_type, jurisdiction, additional_context
        )
        
        try:
            # Call Claude on Bedrock
            response = await self._call_claude(prompt)
            
            # Parse the response to extract YAML
            yaml_content = self._extract_yaml_from_response(response)
            
            # Parse YAML into Template object
            template = TemplateParser.parse_yaml_template(yaml_content, user_id)
            
            # Enhance template with AI-generated metadata
            template.description = f"AI-generated template for {practice_area} matters in {jurisdiction}"
            template.applies_to = {
                "practice_areas": [practice_area.lower()],
                "matter_types": [matter_type.lower()],
                "jurisdictions": [jurisdiction.upper()]
            }
            
            logger.info(f"Successfully generated template: {template.name}")
            return template
            
        except Exception as e:
            logger.error(f"Error generating template: {e}")
            raise ValidationError(f"Failed to generate template: {e}")
    
    async def enhance_existing_template(
        self, 
        template: Template, 
        enhancement_request: str,
        user_id: str
    ) -> Template:
        """Enhance an existing template based on user feedback."""
        
        logger.info(f"Enhancing template {template.name}")
        
        # Convert template to YAML for context
        current_yaml = TemplateParser.template_to_yaml(template)
        
        # Create enhancement prompt
        prompt = self._create_enhancement_prompt(current_yaml, enhancement_request)
        
        try:
            # Call Claude for enhancement
            response = await self._call_claude(prompt)
            
            # Parse enhanced YAML
            enhanced_yaml = self._extract_yaml_from_response(response)
            enhanced_template = TemplateParser.parse_yaml_template(enhanced_yaml, user_id)
            
            # Preserve original metadata
            enhanced_template.template_id = template.template_id
            enhanced_template.created_by = template.created_by
            enhanced_template.created_at = template.created_at
            enhanced_template.usage_count = template.usage_count
            
            logger.info(f"Successfully enhanced template: {enhanced_template.name}")
            return enhanced_template
            
        except Exception as e:
            logger.error(f"Error enhancing template: {e}")
            raise ValidationError(f"Failed to enhance template: {e}")
    
    async def suggest_template_improvements(
        self, 
        template: Template,
        usage_analytics: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Suggest improvements for an existing template based on usage patterns."""
        
        logger.info(f"Analyzing template {template.name} for improvements")
        
        # Convert template to YAML for analysis
        current_yaml = TemplateParser.template_to_yaml(template)
        
        # Create analysis prompt
        prompt = self._create_analysis_prompt(current_yaml, usage_analytics)
        
        try:
            # Call Claude for analysis
            response = await self._call_claude(prompt)
            
            # Parse suggestions from response
            suggestions = self._extract_suggestions_from_response(response)
            
            logger.info(f"Generated {len(suggestions)} improvement suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error analyzing template: {e}")
            return []
    
    def _create_template_generation_prompt(
        self, 
        description: str, 
        practice_area: str, 
        matter_type: str, 
        jurisdiction: str,
        additional_context: Optional[str] = None
    ) -> str:
        """Create a comprehensive prompt for template generation."""
        
        context_section = f"\nAdditional Context: {additional_context}" if additional_context else ""
        
        return f"""You are an expert legal technology consultant specializing in legal matter management systems. Your task is to generate a comprehensive matter template for a legal practice management system.

## Context
The AI Legal OS treats legal matters as structured "codebases" with versioned documents, evidence, and automated processes. Templates define the initial structure, documents, deadlines, and workflows for different types of legal matters.

## Request Details
- **Practice Area**: {practice_area}
- **Matter Type**: {matter_type}  
- **Jurisdiction**: {jurisdiction}
- **Description**: {description}{context_section}

## Template Requirements
Generate a YAML template that includes:

1. **Folder Structure**: Logical organization of documents and evidence
2. **Starter Documents**: Initial documents that should be created for every matter
3. **Deadline Rules**: Key deadlines and statute of limitations calculations
4. **Agent Configurations**: AI agents that should be available for this matter type
5. **Guardrails**: Compliance and security settings appropriate for this practice area

## Legal Best Practices to Consider
- Follow standard legal document organization patterns
- Include appropriate compliance and ethical safeguards
- Consider jurisdiction-specific requirements and deadlines
- Ensure proper document version control and audit trails
- Include templates for common motions, pleadings, and correspondence
- Plan for evidence management and discovery processes

## YAML Template Format
```yaml
name: "Template Name"
description: "Detailed description of when to use this template"
version: "1.0.0"
applies_to:
  practice_areas:
    - "{practice_area.lower()}"
  matter_types:
    - "{matter_type.lower()}"
  jurisdictions:
    - "{jurisdiction.upper()}"

folders:
  - name: "Folder Name"
    subfolders:
      - "Subfolder 1"
      - "Subfolder 2"

starter_docs:
  - path: "folder/document.md"
    auto_generate: true
    template_content: |
      # Document Title
      
      Document content template here...

deadlines:
  - name: "Deadline Name"
    compute:
      from_field: "field_name"
      relativedelta: "days=30"
    reminders:
      - "-7d"
      - "-3d"
      - "-1d"
    required: true

agents:
  - name: "AgentName"
    skills:
      - "skill1"
      - "skill2"
    enabled: true

guardrails:
  required_citations: false
  pii_scan_before_share: true
  privilege_review_required: true
  auto_redaction: false
```

## Instructions
1. Research the specific requirements for {practice_area} matters in {jurisdiction}
2. Create a comprehensive folder structure that follows legal industry standards
3. Include all necessary starter documents with appropriate templates
4. Calculate relevant deadlines and statute of limitations
5. Configure appropriate AI agents for this matter type
6. Set guardrails that ensure compliance and ethical practice

Generate a complete, production-ready YAML template that a law firm could immediately use to manage {matter_type} matters. Be specific and detailed in your recommendations.

**Important**: Return ONLY the YAML template, no additional explanation or markdown formatting."""
    
    def _create_enhancement_prompt(self, current_yaml: str, enhancement_request: str) -> str:
        """Create a prompt for enhancing an existing template."""
        
        return f"""You are an expert legal technology consultant. You need to enhance an existing legal matter template based on user feedback.

## Current Template
```yaml
{current_yaml}
```

## Enhancement Request
{enhancement_request}

## Instructions
1. Analyze the current template structure and content
2. Understand the specific enhancement request
3. Modify the template to address the request while maintaining legal best practices
4. Ensure all changes are appropriate for the practice area and jurisdiction
5. Preserve existing functionality unless explicitly requested to change

## Requirements
- Maintain the same YAML structure and format
- Keep all existing folders, documents, and deadlines unless modification is requested
- Add new elements as needed to fulfill the enhancement request
- Ensure legal compliance and best practices are maintained
- Update version number if significant changes are made

**Important**: Return ONLY the enhanced YAML template, no additional explanation or markdown formatting."""
    
    def _create_analysis_prompt(self, current_yaml: str, usage_analytics: Optional[Dict[str, Any]]) -> str:
        """Create a prompt for analyzing template improvements."""
        
        analytics_section = ""
        if usage_analytics:
            analytics_section = f"""
## Usage Analytics
{json.dumps(usage_analytics, indent=2)}
"""
        
        return f"""You are an expert legal technology consultant analyzing a legal matter template for potential improvements.

## Current Template
```yaml
{current_yaml}
```
{analytics_section}

## Analysis Request
Analyze this template and suggest specific improvements based on:
1. Legal industry best practices
2. Common workflow patterns in this practice area
3. Potential compliance or security enhancements
4. Document organization optimization
5. Deadline management improvements
6. Agent configuration enhancements

## Instructions
Provide 3-7 specific, actionable improvement suggestions. Each suggestion should:
- Be concrete and implementable
- Explain the benefit or problem it solves
- Be appropriate for the practice area and jurisdiction
- Consider modern legal technology trends

Format your response as a JSON array of suggestion strings:
```json
[
  "Suggestion 1: Specific improvement with clear benefit",
  "Suggestion 2: Another concrete recommendation",
  "..."
]
```

**Important**: Return ONLY the JSON array of suggestions, no additional explanation or markdown formatting."""
    
    async def _call_claude(self, prompt: str) -> str:
        """Call Claude on Bedrock with the given prompt."""
        
        try:
            # Prepare the request body for Claude
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "temperature": 0.1,  # Low temperature for consistent, factual output
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Call Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )
            
            # Parse response
            response_body = json.loads(response["body"].read())
            
            if "content" in response_body and len(response_body["content"]) > 0:
                return response_body["content"][0]["text"]
            else:
                raise ValueError("No content in Claude response")
                
        except ClientError as e:
            logger.error(f"Bedrock API error: {e}")
            raise ValidationError(f"AI service error: {e}")
        except Exception as e:
            logger.error(f"Error calling Claude: {e}")
            raise ValidationError(f"Failed to generate AI response: {e}")
    
    def _extract_yaml_from_response(self, response: str) -> str:
        """Extract YAML content from Claude's response."""
        
        # Remove any markdown formatting
        response = response.strip()
        
        # If response is wrapped in code blocks, extract the content
        if response.startswith("```yaml"):
            lines = response.split("\n")
            yaml_lines = []
            in_yaml = False
            
            for line in lines:
                if line.strip() == "```yaml":
                    in_yaml = True
                    continue
                elif line.strip() == "```" and in_yaml:
                    break
                elif in_yaml:
                    yaml_lines.append(line)
            
            return "\n".join(yaml_lines)
        
        elif response.startswith("```"):
            # Generic code block
            lines = response.split("\n")
            yaml_lines = []
            in_code = False
            
            for line in lines:
                if line.strip().startswith("```") and not in_code:
                    in_code = True
                    continue
                elif line.strip() == "```" and in_code:
                    break
                elif in_code:
                    yaml_lines.append(line)
            
            return "\n".join(yaml_lines)
        
        # If no code blocks, return as-is
        return response
    
    def _extract_suggestions_from_response(self, response: str) -> List[str]:
        """Extract suggestions list from Claude's response."""
        
        try:
            # Remove any markdown formatting
            response = response.strip()
            
            # If response is wrapped in code blocks, extract the content
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_content = response[start:end].strip()
            elif response.startswith("[") and response.endswith("]"):
                json_content = response
            else:
                # Try to find JSON array in the response
                start = response.find("[")
                end = response.rfind("]") + 1
                if start >= 0 and end > start:
                    json_content = response[start:end]
                else:
                    # Fallback: split by lines and clean up
                    lines = [line.strip() for line in response.split("\n") if line.strip()]
                    return [line.lstrip("- ").lstrip("* ") for line in lines if line]
            
            # Parse JSON
            suggestions = json.loads(json_content)
            
            if isinstance(suggestions, list):
                return [str(s) for s in suggestions]
            else:
                return [str(suggestions)]
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Could not parse suggestions as JSON: {e}")
            # Fallback: treat as plain text list
            lines = [line.strip() for line in response.split("\n") if line.strip()]
            return [line.lstrip("- ").lstrip("* ") for line in lines if line]
    
    def _validate_model_access(self):
        """Validate that the model is accessible."""
        try:
            # Create a separate bedrock client for listing models
            bedrock_client = boto3.client("bedrock", region_name=self.region)
            bedrock_client.list_foundation_models()
            logger.info(f"Bedrock access validated for region {self.region}")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDeniedException':
                raise ValidationError(
                    f"Access denied to Bedrock in region {self.region}. "
                    "Please check your IAM permissions for bedrock:InvokeModel and bedrock:ListFoundationModels"
                )
            elif error_code == 'UnrecognizedClientException':
                raise ValidationError(
                    f"Invalid AWS credentials or Bedrock not available in region {self.region}"
                )
            else:
                raise ValidationError(f"Bedrock validation failed: {e}")
        except Exception as e:
            raise ValidationError(f"Cannot access Bedrock service: {e}")