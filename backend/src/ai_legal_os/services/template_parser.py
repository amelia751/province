"""Template YAML parser and validator."""

import logging
from typing import Dict, Any, List, Optional

import yaml
from pydantic import ValidationError

from ai_legal_os.models.template import (
    Template, FolderStructure, StarterDocument, DeadlineRule,
    AgentConfig, GuardrailConfig
)
from ai_legal_os.models.base import generate_id

logger = logging.getLogger(__name__)


class TemplateParseError(Exception):
    """Template parsing error."""
    pass


class TemplateParser:
    """Parser for YAML template definitions."""
    
    @staticmethod
    def parse_yaml_template(yaml_content: str, created_by: str) -> Template:
        """Parse YAML template definition into Template model."""
        try:
            data = yaml.safe_load(yaml_content)
            return TemplateParser.parse_dict_template(data, created_by)
        except yaml.YAMLError as e:
            raise TemplateParseError(f"Invalid YAML: {e}")
    
    @staticmethod
    def parse_dict_template(data: Dict[str, Any], created_by: str) -> Template:
        """Parse dictionary template definition into Template model."""
        try:
            # Extract basic fields
            name = data.get("name")
            if not name:
                raise TemplateParseError("Template name is required")
            
            description = data.get("description", "")
            version = data.get("version", "1.0.0")
            applies_to = data.get("applies_to", {})
            
            # Parse folder structures
            folders = []
            for folder_data in data.get("folders", []):
                if isinstance(folder_data, str):
                    folders.append(FolderStructure(name=folder_data))
                elif isinstance(folder_data, dict):
                    folders.append(FolderStructure(
                        name=folder_data["name"],
                        subfolders=folder_data.get("subfolders", [])
                    ))
                else:
                    raise TemplateParseError(f"Invalid folder definition: {folder_data}")
            
            # Parse starter documents
            starter_docs = []
            for doc_data in data.get("starter_docs", []):
                starter_docs.append(StarterDocument(
                    path=doc_data["path"],
                    generator=doc_data.get("generator"),
                    auto_generate=doc_data.get("auto_generate", False),
                    template_content=doc_data.get("template_content")
                ))
            
            # Parse deadline rules
            deadlines = []
            for deadline_data in data.get("deadlines", []):
                deadlines.append(DeadlineRule(
                    name=deadline_data["name"],
                    compute=deadline_data["compute"],
                    reminders=deadline_data.get("reminders", []),
                    required=deadline_data.get("required", True)
                ))
            
            # Parse agent configurations
            agents = []
            for agent_data in data.get("agents", []):
                agents.append(AgentConfig(
                    name=agent_data["name"],
                    skills=agent_data.get("skills", []),
                    enabled=agent_data.get("enabled", True)
                ))
            
            # Parse guardrails
            guardrails_data = data.get("guardrails", {})
            guardrails = GuardrailConfig(
                required_citations=guardrails_data.get("required_citations", False),
                pii_scan_before_share=guardrails_data.get("pii_scan_before_share", True),
                privilege_review_required=guardrails_data.get("privilege_review_required", False),
                auto_redaction=guardrails_data.get("auto_redaction", False)
            )
            
            # Create template
            template = Template(
                template_id=generate_id(),
                name=name,
                description=description,
                version=version,
                applies_to=applies_to,
                folders=folders,
                starter_docs=starter_docs,
                deadlines=deadlines,
                agents=agents,
                guardrails=guardrails,
                created_by=created_by
            )
            
            return template
            
        except (KeyError, TypeError, ValidationError) as e:
            raise TemplateParseError(f"Invalid template structure: {e}")
    
    @staticmethod
    def template_to_yaml(template: Template) -> str:
        """Convert Template model to YAML string."""
        data = {
            "name": template.name,
            "description": template.description,
            "version": template.version,
            "applies_to": template.applies_to,
            "folders": [
                {
                    "name": folder.name,
                    "subfolders": folder.subfolders
                } if folder.subfolders else folder.name
                for folder in template.folders
            ],
            "starter_docs": [
                {
                    "path": doc.path,
                    "generator": doc.generator,
                    "auto_generate": doc.auto_generate,
                    "template_content": doc.template_content
                }
                for doc in template.starter_docs
            ],
            "deadlines": [
                {
                    "name": deadline.name,
                    "compute": deadline.compute,
                    "reminders": deadline.reminders,
                    "required": deadline.required
                }
                for deadline in template.deadlines
            ],
            "agents": [
                {
                    "name": agent.name,
                    "skills": agent.skills,
                    "enabled": agent.enabled
                }
                for agent in template.agents
            ],
            "guardrails": {
                "required_citations": template.guardrails.required_citations,
                "pii_scan_before_share": template.guardrails.pii_scan_before_share,
                "privilege_review_required": template.guardrails.privilege_review_required,
                "auto_redaction": template.guardrails.auto_redaction
            }
        }
        
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    
    @staticmethod
    def validate_template_yaml(yaml_content: str) -> List[str]:
        """Validate YAML template and return list of errors."""
        errors = []
        
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            return [f"Invalid YAML: {e}"]
        
        # Check required fields
        if not data.get("name"):
            errors.append("Template name is required")
        
        if not data.get("description"):
            errors.append("Template description is required")
        
        # Validate folder structures
        folders = data.get("folders", [])
        for i, folder in enumerate(folders):
            if isinstance(folder, dict):
                if not folder.get("name"):
                    errors.append(f"Folder {i}: name is required")
                if "subfolders" in folder and not isinstance(folder["subfolders"], list):
                    errors.append(f"Folder {i}: subfolders must be a list")
            elif not isinstance(folder, str):
                errors.append(f"Folder {i}: must be string or object with name")
        
        # Validate starter documents
        starter_docs = data.get("starter_docs", [])
        for i, doc in enumerate(starter_docs):
            if not isinstance(doc, dict):
                errors.append(f"Starter document {i}: must be an object")
                continue
            if not doc.get("path"):
                errors.append(f"Starter document {i}: path is required")
            if "auto_generate" in doc and not isinstance(doc["auto_generate"], bool):
                errors.append(f"Starter document {i}: auto_generate must be boolean")
        
        # Validate deadlines
        deadlines = data.get("deadlines", [])
        for i, deadline in enumerate(deadlines):
            if not isinstance(deadline, dict):
                errors.append(f"Deadline {i}: must be an object")
                continue
            if not deadline.get("name"):
                errors.append(f"Deadline {i}: name is required")
            if not deadline.get("compute"):
                errors.append(f"Deadline {i}: compute rules are required")
            if "reminders" in deadline and not isinstance(deadline["reminders"], list):
                errors.append(f"Deadline {i}: reminders must be a list")
        
        # Validate agents
        agents = data.get("agents", [])
        for i, agent in enumerate(agents):
            if not isinstance(agent, dict):
                errors.append(f"Agent {i}: must be an object")
                continue
            if not agent.get("name"):
                errors.append(f"Agent {i}: name is required")
            if "skills" in agent and not isinstance(agent["skills"], list):
                errors.append(f"Agent {i}: skills must be a list")
        
        return errors