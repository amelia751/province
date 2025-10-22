#!/usr/bin/env python3
"""
Setup AWS Bedrock Data Automation for W2 processing.

This script creates a Bedrock Data Automation project and blueprint
specifically designed for W2 tax form processing.
"""

import os
import json
import boto3
import logging
from typing import Dict, Any
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BedrockDataAutomationSetup:
    """Setup AWS Bedrock Data Automation for W2 processing."""
    
    def __init__(self):
        """Initialize the setup with AWS credentials from environment."""
        # Use general AWS credentials for Bedrock Data Automation
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.aws_account_id = os.getenv('AWS_ACCOUNT_ID')
        
        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.aws_account_id]):
            raise ValueError("Missing required AWS credentials in environment variables")
        
        # Initialize Bedrock Data Automation client
        self.client = boto3.client(
            'bedrock-data-automation',
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )
        
        # S3 bucket for documents
        self.documents_bucket = os.getenv('DOCUMENTS_BUCKET_NAME', 'province-documents-<account-id>-<region>')
        
        logger.info(f"Initialized Bedrock Data Automation setup for region: {self.aws_region}")
        logger.info(f"Using documents bucket: {self.documents_bucket}")
    
    def create_w2_blueprint(self) -> Dict[str, Any]:
        """Create a blueprint specifically for W2 form processing."""
        
        blueprint_name = "w2-tax-form-processor"
        
        # Define the blueprint schema for W2 processing based on AWS documentation
        blueprint_schema = {
            "class": "W2Form",
            "description": "Blueprint for processing W-2 tax forms",
            "properties": {
                "employee_name": {
                    "type": "string",
                    "inferenceType": "explicit",
                    "instruction": "The full name of the employee as shown on the W-2 form"
                },
                "employee_ssn": {
                    "type": "string",
                    "inferenceType": "explicit",
                    "instruction": "The employee's Social Security Number in format XXX-XX-XXXX"
                },
                "employee_address": {
                    "type": "string",
                    "inferenceType": "explicit",
                    "instruction": "The employee's address including street, city, state, and ZIP code"
                },
                "employer_name": {
                    "type": "string",
                    "inferenceType": "explicit",
                    "instruction": "The name of the employer company"
                },
                "employer_ein": {
                    "type": "string",
                    "inferenceType": "explicit",
                    "instruction": "The Employer Identification Number (EIN) in format XX-XXXXXXX"
                },
                "employer_address": {
                    "type": "string",
                    "inferenceType": "explicit",
                    "instruction": "The employer's address including street, city, state, and ZIP code"
                },
                "box_1_wages": {
                    "type": "number",
                    "inferenceType": "explicit",
                    "instruction": "Box 1: Wages, tips, other compensation - the total taxable wages"
                },
                "box_2_federal_tax_withheld": {
                    "type": "number",
                    "inferenceType": "explicit",
                    "instruction": "Box 2: Federal income tax withheld from employee's pay"
                },
                "box_3_social_security_wages": {
                    "type": "number",
                    "inferenceType": "explicit",
                    "instruction": "Box 3: Social security wages subject to Social Security tax"
                },
                "box_4_social_security_tax_withheld": {
                    "type": "number",
                    "inferenceType": "explicit",
                    "instruction": "Box 4: Social security tax withheld from employee's pay"
                },
                "box_5_medicare_wages": {
                    "type": "number",
                    "inferenceType": "explicit",
                    "instruction": "Box 5: Medicare wages and tips subject to Medicare tax"
                },
                "box_6_medicare_tax_withheld": {
                    "type": "number",
                    "inferenceType": "explicit",
                    "instruction": "Box 6: Medicare tax withheld from employee's pay"
                },
                "box_7_social_security_tips": {
                    "type": "number",
                    "inferenceType": "explicit",
                    "instruction": "Box 7: Social security tips reported by employee"
                },
                "box_8_allocated_tips": {
                    "type": "number",
                    "inferenceType": "explicit",
                    "instruction": "Box 8: Allocated tips (if applicable)"
                },
                "box_10_dependent_care_benefits": {
                    "type": "number",
                    "inferenceType": "explicit",
                    "instruction": "Box 10: Dependent care benefits provided by employer"
                },
                "box_11_nonqualified_plans": {
                    "type": "number",
                    "inferenceType": "explicit",
                    "instruction": "Box 11: Nonqualified plans distributions"
                },
                "box_12_codes": {
                    "type": "string",
                    "inferenceType": "explicit",
                    "instruction": "Box 12: Various codes and amounts (401k contributions, health insurance, etc.) - extract all codes and amounts"
                },
                "box_13_checkboxes": {
                    "type": "string",
                    "inferenceType": "explicit",
                    "instruction": "Box 13: Checkboxes for statutory employee, retirement plan, third-party sick pay"
                },
                "box_14_other": {
                    "type": "string",
                    "inferenceType": "explicit",
                    "instruction": "Box 14: Other information such as state disability insurance"
                }
            }
        }
        
        try:
            logger.info(f"Creating W2 blueprint: {blueprint_name}")
            
            response = self.client.create_blueprint(
                blueprintName=blueprint_name,
                type="DOCUMENT",
                blueprintStage="DEVELOPMENT",
                schema=json.dumps(blueprint_schema)
            )
            
            logger.info(f"Blueprint creation response: {response}")
            # Add blueprintArn if not present in response
            if 'blueprintArn' not in response:
                response['blueprintArn'] = f"arn:aws:bedrock:{self.aws_region}:{self.aws_account_id}:blueprint/{blueprint_name}"
            
            logger.info(f"Successfully created blueprint: {response['blueprintArn']}")
            return response
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                logger.info(f"Blueprint {blueprint_name} already exists, retrieving existing blueprint")
                return self.get_blueprint(blueprint_name)
            else:
                logger.error(f"Failed to create blueprint: {e}")
                raise
    
    def get_blueprint(self, blueprint_name: str) -> Dict[str, Any]:
        """Get an existing blueprint."""
        try:
            response = self.client.get_blueprint(blueprintArn=f"arn:aws:bedrock:{self.aws_region}:{self.aws_account_id}:blueprint/{blueprint_name}")
            return response
        except ClientError as e:
            logger.error(f"Failed to get blueprint: {e}")
            raise
    
    def create_w2_project(self, blueprint_arn: str) -> Dict[str, Any]:
        """Create a data automation project for W2 processing."""
        
        project_name = "w2-tax-processing-project"
        
        try:
            logger.info(f"Creating W2 data automation project: {project_name}")
            
            response = self.client.create_data_automation_project(
                projectName=project_name,
                standardOutputConfiguration={
                    "document": {
                        "extraction": {
                            "category": {
                                "state": "ENABLED",
                                "types": ["TEXT_DETECTION"]
                            },
                            "boundingBox": {
                                "state": "ENABLED"
                            }
                        },
                        "generativeField": {
                            "state": "ENABLED"
                        }
                    },
                    "image": {
                        "extraction": {
                            "category": {
                                "state": "ENABLED",
                                "types": ["TEXT_DETECTION"]
                            },
                            "boundingBox": {
                                "state": "ENABLED"
                            }
                        },
                        "generativeField": {
                            "state": "ENABLED"
                        }
                    }
                }
            )
            
            logger.info(f"Project creation response: {response}")
            # Add projectArn if not present in response
            if 'projectArn' not in response:
                response['projectArn'] = f"arn:aws:bedrock:{self.aws_region}:{self.aws_account_id}:data-automation-project/{project_name}"
            
            logger.info(f"Successfully created project: {response['projectArn']}")
            return response
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException':
                logger.info(f"Project {project_name} already exists, retrieving existing project")
                return self.get_project(project_name)
            else:
                logger.error(f"Failed to create project: {e}")
                raise
    
    def get_project(self, project_name: str) -> Dict[str, Any]:
        """Get an existing project."""
        try:
            response = self.client.get_data_automation_project(
                projectArn=f"arn:aws:bedrock:{self.aws_region}:{self.aws_account_id}:data-automation-project/{project_name}"
            )
            return response
        except ClientError as e:
            logger.error(f"Failed to get project: {e}")
            raise
    
    def list_blueprints(self) -> Dict[str, Any]:
        """List all available blueprints."""
        try:
            response = self.client.list_blueprints()
            return response
        except ClientError as e:
            logger.error(f"Failed to list blueprints: {e}")
            raise
    
    def list_projects(self) -> Dict[str, Any]:
        """List all data automation projects."""
        try:
            response = self.client.list_data_automation_projects()
            return response
        except ClientError as e:
            logger.error(f"Failed to list projects: {e}")
            raise
    
    def update_project_with_blueprint(self, project_arn: str, blueprint_arn: str) -> Dict[str, Any]:
        """Update the project to include the blueprint for custom extraction."""
        
        try:
            logger.info(f"Updating project with blueprint: {blueprint_arn}")
            
            response = self.client.update_data_automation_project(
                projectArn=project_arn,
                customOutputConfiguration={
                    "blueprints": [
                        {
                            "blueprintArn": blueprint_arn,
                            "blueprintVersion": "1",
                            "blueprintStage": "DEVELOPMENT"
                        }
                    ]
                }
            )
            
            logger.info("Successfully updated project with blueprint")
            return response
            
        except ClientError as e:
            logger.error(f"Failed to update project with blueprint: {e}")
            raise

    def setup_complete_w2_automation(self) -> Dict[str, Any]:
        """Set up complete W2 automation including blueprint and project."""
        
        logger.info("Starting complete W2 Bedrock Data Automation setup...")
        
        # Step 1: Create W2 blueprint
        blueprint_response = self.create_w2_blueprint()
        blueprint_arn = blueprint_response['blueprintArn']
        
        # Step 2: Create W2 project
        project_response = self.create_w2_project(blueprint_arn)
        project_arn = project_response['projectArn']
        
        # Step 3: Update project with blueprint
        self.update_project_with_blueprint(project_arn, blueprint_arn)
        
        # Step 4: Return setup summary
        setup_summary = {
            "setup_status": "completed",
            "blueprint": {
                "name": "w2-tax-form-processor",
                "arn": blueprint_arn,
                "status": blueprint_response.get('blueprintStage', 'DEVELOPMENT')
            },
            "project": {
                "name": "w2-tax-processing-project", 
                "arn": project_arn,
                "status": project_response.get('projectStage', 'DEVELOPMENT')
            },
            "region": self.aws_region,
            "documents_bucket": self.documents_bucket
        }
        
        logger.info("W2 Bedrock Data Automation setup completed successfully!")
        logger.info(f"Blueprint ARN: {blueprint_arn}")
        logger.info(f"Project ARN: {project_arn}")
        
        return setup_summary


def main():
    """Main function to set up Bedrock Data Automation for W2 processing."""
    
    try:
        # Initialize setup
        setup = BedrockDataAutomationSetup()
        
        # Run complete setup
        result = setup.setup_complete_w2_automation()
        
        # Save setup results
        output_file = "bedrock_data_automation_setup.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print("\n" + "="*60)
        print("AWS BEDROCK DATA AUTOMATION SETUP COMPLETED")
        print("="*60)
        print(f"✅ Blueprint: {result['blueprint']['name']}")
        print(f"✅ Project: {result['project']['name']}")
        print(f"✅ Region: {result['region']}")
        print(f"✅ Setup details saved to: {output_file}")
        print("\nNext steps:")
        print("1. Test with sample W2 documents")
        print("2. Integrate with existing ingest_w2 tool")
        print("3. Update frontend to use new processing method")
        
        return result
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        print(f"\n❌ Setup failed: {e}")
        return None


if __name__ == "__main__":
    main()
