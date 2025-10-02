"""Template repository implementation."""

import json
import logging
import os
from typing import List, Optional

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from ai_legal_os.models.template import Template
from ai_legal_os.models.base import generate_id

logger = logging.getLogger(__name__)


class TemplateRepository:
    """Template repository using DynamoDB."""
    
    def __init__(self, table_name: Optional[str] = None):
        self.table_name = table_name or os.environ.get("TEMPLATES_TABLE_NAME", "ai-legal-os-templates")
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(self.table_name)
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure default templates are initialized."""
        if self._initialized:
            return
            
        try:
            # Check if any templates exist
            response = self.table.scan(Limit=1)
            if not response.get("Items"):
                logger.info("Initializing default templates")
                await self._create_default_templates()
            self._initialized = True
        except ClientError as e:
            logger.error(f"Error checking for existing templates: {e}")
            # Don't fail initialization, just log the error
            self._initialized = True
    
    async def _create_default_templates(self):
        """Create default templates."""
        from ai_legal_os.models.template import (
            FolderStructure, StarterDocument, DeadlineRule, 
            AgentConfig, GuardrailConfig
        )
        
        # General Civil Litigation Template
        civil_template = Template(
            template_id=generate_id(),
            name="General Civil Litigation",
            description="Standard template for civil litigation matters",
            version="1.0.0",
            applies_to={
                "practice_areas": ["civil", "commercial", "employment"],
                "jurisdictions": ["US-CA", "US-NY", "US-TX"]
            },
            folders=[
                FolderStructure(name="Pleadings", subfolders=["Complaints", "Answers", "Motions"]),
                FolderStructure(name="Discovery", subfolders=["Requests", "Responses", "Depositions"]),
                FolderStructure(name="Evidence", subfolders=["Documents", "Photos", "Expert_Reports"]),
                FolderStructure(name="Correspondence"),
                FolderStructure(name="Research"),
                FolderStructure(name="Deadlines"),
                FolderStructure(name="Settlement")
            ],
            starter_docs=[
                StarterDocument(
                    path="/Research/Case_Law_Research.md",
                    generator="research_template",
                    auto_generate=True,
                    template_content="# Case Law Research\n\n## Key Cases\n\n## Statutes\n\n## Notes\n"
                )
            ],
            deadlines=[
                DeadlineRule(
                    name="Answer Deadline",
                    compute={"from_field": "service_date", "relativedelta": "days=30"},
                    reminders=["-7d", "-3d", "-1d"]
                )
            ],
            agents=[
                AgentConfig(name="DraftingAgent", skills=["draft_complaint", "draft_motion"]),
                AgentConfig(name="ResearchAgent", skills=["case_law_search", "statute_research"])
            ],
            guardrails=GuardrailConfig(
                required_citations=True,
                pii_scan_before_share=True,
                privilege_review_required=True
            ),
            created_by="system"
        )
        
        # Personal Injury Template
        pi_template = Template(
            template_id=generate_id(),
            name="Personal Injury",
            description="Template for personal injury cases",
            version="1.0.0",
            applies_to={
                "practice_areas": ["personal_injury", "tort"],
                "jurisdictions": ["US-CA", "US-NY", "US-TX", "US-FL"]
            },
            folders=[
                FolderStructure(name="Pleadings", subfolders=["Complaint", "Answer"]),
                FolderStructure(name="Medical_Records", subfolders=["Hospital", "Doctor", "Therapy"]),
                FolderStructure(name="Discovery", subfolders=["Interrogatories", "Depositions"]),
                FolderStructure(name="Evidence", subfolders=["Photos", "Witness_Statements", "Expert_Reports"]),
                FolderStructure(name="Insurance", subfolders=["Correspondence", "Policies"]),
                FolderStructure(name="Settlement"),
                FolderStructure(name="Trial_Prep")
            ],
            starter_docs=[
                StarterDocument(
                    path="/Medical_Records/Medical_Summary.md",
                    generator="medical_summary_template",
                    auto_generate=True,
                    template_content="# Medical Summary\n\n## Injuries\n\n## Treatment\n\n## Prognosis\n"
                )
            ],
            deadlines=[
                DeadlineRule(
                    name="Statute of Limitations",
                    compute={"from_field": "incident_date", "relativedelta": "years=2"},
                    reminders=["-365d", "-180d", "-90d", "-30d"]
                )
            ],
            agents=[
                AgentConfig(name="MedicalAgent", skills=["medical_record_analysis", "injury_assessment"]),
                AgentConfig(name="SettlementAgent", skills=["damage_calculation", "settlement_negotiation"])
            ],
            guardrails=GuardrailConfig(
                required_citations=False,
                pii_scan_before_share=True,
                privilege_review_required=False
            ),
            created_by="system"
        )
        
        # Store templates in DynamoDB
        await self.create(civil_template)
        await self.create(pi_template)
    
    async def create(self, template: Template) -> Template:
        """Create a new template."""
        if not template.template_id:
            template.template_id = generate_id()
        
        try:
            item = self._template_to_item(template)
            self.table.put_item(Item=item)
            logger.info(f"Created template {template.template_id}")
            return template
        except ClientError as e:
            logger.error(f"Error creating template: {e}")
            raise
    
    async def get_by_id(self, template_id: str, user_id: str) -> Optional[Template]:
        """Get template by ID."""
        try:
            response = self.table.get_item(Key={"template_id": template_id})
            item = response.get("Item")
            if item:
                return self._item_to_template(item)
            return None
        except ClientError as e:
            logger.error(f"Error getting template {template_id}: {e}")
            return None
    
    async def get_by_name(self, name: str) -> Optional[Template]:
        """Get template by name."""
        try:
            response = self.table.query(
                IndexName="NameIndex",
                KeyConditionExpression=Key("name").eq(name),
                FilterExpression="is_active = :active",
                ExpressionAttributeValues={":active": "true"},
                ScanIndexForward=False,  # Get latest version first
                Limit=1
            )
            items = response.get("Items", [])
            if items:
                return self._item_to_template(items[0])
            return None
        except ClientError as e:
            logger.error(f"Error getting template by name {name}: {e}")
            return None
    
    async def list_active(self) -> List[Template]:
        """List all active templates."""
        await self._ensure_initialized()
        try:
            response = self.table.query(
                IndexName="ActiveIndex",
                KeyConditionExpression=Key("is_active").eq("true"),
                ScanIndexForward=False  # Sort by usage_count descending
            )
            items = response.get("Items", [])
            return [self._item_to_template(item) for item in items]
        except ClientError as e:
            logger.error(f"Error listing active templates: {e}")
            return []
    
    async def update(self, template: Template) -> Template:
        """Update an existing template."""
        try:
            item = self._template_to_item(template)
            self.table.put_item(Item=item)
            logger.info(f"Updated template {template.template_id}")
            return template
        except ClientError as e:
            logger.error(f"Error updating template: {e}")
            raise
    
    async def increment_usage(self, template_id: str) -> None:
        """Increment template usage count."""
        try:
            self.table.update_item(
                Key={"template_id": template_id},
                UpdateExpression="ADD usage_count :inc",
                ExpressionAttributeValues={":inc": 1}
            )
            logger.info(f"Incremented usage count for template {template_id}")
        except ClientError as e:
            logger.error(f"Error incrementing usage count: {e}")
    
    def _template_to_item(self, template: Template) -> dict:
        """Convert Template model to DynamoDB item."""
        item = template.model_dump()
        # Convert boolean to string for GSI
        item["is_active"] = "true" if template.is_active else "false"
        
        # Convert datetime objects to ISO strings
        if template.created_at:
            item["created_at"] = template.created_at.isoformat()
        if template.updated_at:
            item["updated_at"] = template.updated_at.isoformat()
        
        return item
    
    def _item_to_template(self, item: dict) -> Template:
        """Convert DynamoDB item to Template model."""
        # Convert string back to boolean
        if "is_active" in item:
            item["is_active"] = item["is_active"] == "true"
        
        # Convert ISO strings back to datetime objects
        if "created_at" in item and isinstance(item["created_at"], str):
            from datetime import datetime
            item["created_at"] = datetime.fromisoformat(item["created_at"])
        if "updated_at" in item and isinstance(item["updated_at"], str):
            from datetime import datetime
            item["updated_at"] = datetime.fromisoformat(item["updated_at"])
        
        return Template(**item)