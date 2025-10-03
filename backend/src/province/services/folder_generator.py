"""Folder structure generation service."""

import logging
import os
from typing import List, Optional

import boto3
from botocore.exceptions import ClientError

from province.models.template import Template, FolderStructure, StarterDocument
from province.models.matter import Matter

logger = logging.getLogger(__name__)


class FolderGenerationError(Exception):
    """Folder generation error."""
    pass


class FolderGenerator:
    """Service for generating folder structures in S3."""
    
    def __init__(self, bucket_name: Optional[str] = None):
        self.bucket_name = bucket_name or os.environ.get("DOCUMENTS_BUCKET_NAME")
        if not self.bucket_name:
            raise ValueError("Documents bucket name not configured")
        
        self.s3_client = boto3.client("s3")
    
    async def generate_matter_structure(
        self, 
        template: Template, 
        matter: Matter, 
        user_id: str
    ) -> None:
        """Generate complete folder structure for a matter from template."""
        logger.info(f"Generating folder structure for matter {matter.matter_id} using template {template.template_id}")
        
        try:
            # Create base matter folder
            matter_prefix = f"matters/{matter.matter_id}/"
            
            # Create folder structure
            await self._create_folder_structure(matter_prefix, template.folders)
            
            # Generate starter documents
            await self._generate_starter_documents(
                matter_prefix, 
                template.starter_docs, 
                matter, 
                user_id
            )
            
            logger.info(f"Successfully generated folder structure for matter {matter.matter_id}")
            
        except Exception as e:
            logger.error(f"Error generating folder structure: {e}")
            raise FolderGenerationError(f"Failed to generate folder structure: {e}")
    
    async def _create_folder_structure(
        self, 
        base_prefix: str, 
        folders: List[FolderStructure]
    ) -> None:
        """Create folder structure in S3."""
        for folder in folders:
            # Create main folder
            folder_key = f"{base_prefix}{folder.name}/"
            await self._create_s3_folder(folder_key)
            
            # Create subfolders
            for subfolder in folder.subfolders:
                subfolder_key = f"{folder_key}{subfolder}/"
                await self._create_s3_folder(subfolder_key)
    
    async def _create_s3_folder(self, folder_key: str) -> None:
        """Create a folder in S3 by putting an empty object."""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=folder_key,
                Body=b"",
                Metadata={
                    "folder": "true",
                    "created_by": "system"
                }
            )
            logger.debug(f"Created S3 folder: {folder_key}")
        except ClientError as e:
            logger.error(f"Error creating S3 folder {folder_key}: {e}")
            raise
    
    async def _generate_starter_documents(
        self,
        base_prefix: str,
        starter_docs: List[StarterDocument],
        matter: Matter,
        user_id: str
    ) -> None:
        """Generate starter documents from template."""
        for doc in starter_docs:
            if doc.auto_generate or doc.template_content:
                await self._create_starter_document(base_prefix, doc, matter, user_id)
    
    async def _create_starter_document(
        self,
        base_prefix: str,
        doc: StarterDocument,
        matter: Matter,
        user_id: str
    ) -> None:
        """Create a single starter document."""
        try:
            # Remove leading slash from path if present
            doc_path = doc.path.lstrip("/")
            full_key = f"{base_prefix}{doc_path}"
            
            # Generate document content
            content = await self._generate_document_content(doc, matter)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=full_key,
                Body=content.encode("utf-8"),
                ContentType="text/plain",
                Metadata={
                    "matter_id": matter.matter_id,
                    "created_by": user_id,
                    "generated_from_template": doc.generator or "static",
                    "document_type": "starter_document"
                }
            )
            
            logger.info(f"Created starter document: {full_key}")
            
        except Exception as e:
            logger.error(f"Error creating starter document {doc.path}: {e}")
            raise
    
    async def _generate_document_content(
        self, 
        doc: StarterDocument, 
        matter: Matter
    ) -> str:
        """Generate content for a starter document."""
        if doc.template_content:
            # Use static template content with basic substitution
            content = doc.template_content
            
            # Simple template variable substitution
            substitutions = {
                "{{matter_title}}": matter.title,
                "{{matter_id}}": matter.matter_id,
                "{{matter_type}}": matter.matter_type,
                "{{jurisdiction}}": matter.jurisdiction or "Unknown",
                "{{created_date}}": matter.created_at.strftime("%Y-%m-%d") if matter.created_at else "Unknown"
            }
            
            for placeholder, value in substitutions.items():
                content = content.replace(placeholder, value)
            
            return content
        
        elif doc.generator:
            # Use generator function (placeholder for now)
            return await self._call_document_generator(doc.generator, matter)
        
        else:
            # Default empty document
            return f"# {doc.path}\n\nDocument created from template.\n"
    
    async def _call_document_generator(self, generator: str, matter: Matter) -> str:
        """Call a document generator function."""
        # This is a placeholder for actual generator functions
        # In a real implementation, this would call specific generators
        # based on the generator name
        
        generators = {
            "research_template": self._generate_research_template,
            "medical_summary_template": self._generate_medical_summary_template,
            "complaint_template": self._generate_complaint_template,
        }
        
        generator_func = generators.get(generator)
        if generator_func:
            return await generator_func(matter)
        else:
            logger.warning(f"Unknown generator: {generator}")
            return f"# Generated Document\n\nGenerated using {generator} for matter {matter.title}\n"
    
    async def _generate_research_template(self, matter: Matter) -> str:
        """Generate research template content."""
        return f"""# Case Law Research - {matter.title}

## Matter Information
- **Matter ID**: {matter.matter_id}
- **Matter Type**: {matter.matter_type}
- **Jurisdiction**: {matter.jurisdiction or 'Unknown'}

## Key Legal Issues
- [ ] Issue 1
- [ ] Issue 2
- [ ] Issue 3

## Relevant Statutes
- [ ] Statute 1
- [ ] Statute 2

## Case Law Research
### Favorable Cases
- [ ] Case 1: [Citation] - [Brief description]
- [ ] Case 2: [Citation] - [Brief description]

### Adverse Cases
- [ ] Case 1: [Citation] - [Brief description]
- [ ] Case 2: [Citation] - [Brief description]

## Research Notes
[Add research notes here]

## Next Steps
- [ ] Research task 1
- [ ] Research task 2
"""
    
    async def _generate_medical_summary_template(self, matter: Matter) -> str:
        """Generate medical summary template content."""
        return f"""# Medical Summary - {matter.title}

## Patient Information
- **Name**: [Patient Name]
- **DOB**: [Date of Birth]
- **Date of Incident**: [Incident Date]

## Injuries Sustained
### Primary Injuries
- [ ] Injury 1: [Description]
- [ ] Injury 2: [Description]

### Secondary Injuries
- [ ] Injury 1: [Description]
- [ ] Injury 2: [Description]

## Treatment Timeline
### Initial Treatment
- **Date**: [Date]
- **Provider**: [Provider Name]
- **Treatment**: [Description]

### Ongoing Treatment
- **Date**: [Date]
- **Provider**: [Provider Name]
- **Treatment**: [Description]

## Current Status
- **Current Symptoms**: [Description]
- **Functional Limitations**: [Description]
- **Prognosis**: [Description]

## Medical Expenses
- **Emergency Room**: $[Amount]
- **Hospital Stay**: $[Amount]
- **Physician Visits**: $[Amount]
- **Physical Therapy**: $[Amount]
- **Total**: $[Total Amount]

## Future Medical Needs
- [ ] Future treatment 1
- [ ] Future treatment 2
"""
    
    async def _generate_complaint_template(self, matter: Matter) -> str:
        """Generate complaint template content."""
        return f"""# Complaint Template - {matter.title}

## Case Caption
[PLAINTIFF NAME]
v.
[DEFENDANT NAME]

Case No: [TO BE ASSIGNED]

## Parties
### Plaintiff
- **Name**: [Plaintiff Name]
- **Address**: [Address]

### Defendant
- **Name**: [Defendant Name]
- **Address**: [Address]

## Jurisdiction and Venue
This Court has jurisdiction over this matter because [jurisdiction basis].
Venue is proper in this Court because [venue basis].

## Facts
### Background
[Factual background]

### The Incident
[Description of the incident giving rise to the claim]

## Causes of Action
### Count I: [Cause of Action]
[Elements and allegations]

### Count II: [Cause of Action]
[Elements and allegations]

## Prayer for Relief
WHEREFORE, Plaintiff respectfully requests that this Court:
1. [Relief requested]
2. [Relief requested]
3. Award costs and attorney's fees
4. Grant such other relief as the Court deems just and proper

Respectfully submitted,

[Attorney Name]
[Bar Number]
[Firm Name]
[Address]
[Phone]
[Email]
"""
    
    async def list_matter_folders(self, matter_id: str) -> List[str]:
        """List all folders in a matter."""
        try:
            prefix = f"matters/{matter_id}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                Delimiter="/"
            )
            
            folders = []
            for prefix_info in response.get("CommonPrefixes", []):
                folder_path = prefix_info["Prefix"]
                # Remove the matter prefix and trailing slash
                folder_name = folder_path[len(prefix):].rstrip("/")
                if folder_name:
                    folders.append(folder_name)
            
            return sorted(folders)
            
        except ClientError as e:
            logger.error(f"Error listing matter folders: {e}")
            return []
    
    async def delete_matter_structure(self, matter_id: str) -> None:
        """Delete entire folder structure for a matter."""
        try:
            prefix = f"matters/{matter_id}/"
            
            # List all objects with the matter prefix
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
            
            objects_to_delete = []
            for page in pages:
                for obj in page.get("Contents", []):
                    objects_to_delete.append({"Key": obj["Key"]})
            
            # Delete objects in batches
            if objects_to_delete:
                for i in range(0, len(objects_to_delete), 1000):  # S3 delete limit
                    batch = objects_to_delete[i:i+1000]
                    self.s3_client.delete_objects(
                        Bucket=self.bucket_name,
                        Delete={"Objects": batch}
                    )
                
                logger.info(f"Deleted {len(objects_to_delete)} objects for matter {matter_id}")
            
        except ClientError as e:
            logger.error(f"Error deleting matter structure: {e}")
            raise FolderGenerationError(f"Failed to delete matter structure: {e}")