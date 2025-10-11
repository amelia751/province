"""
Tool Registry for AWS Lambda Tools

Manages the registry of available tools and their AWS Lambda configurations.
"""

import json
import logging
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LambdaTool:
    """Represents an AWS Lambda tool for Bedrock Agents"""
    name: str
    description: str
    lambda_function_name: str
    handler: str
    runtime: str
    timeout: int
    memory_size: int
    environment_variables: Dict[str, str]
    parameters: Dict[str, Any]
    required_permissions: List[str]


class ToolRegistry:
    """Registry for AWS Lambda tools"""
    
    def __init__(self):
        self.tools: Dict[str, LambdaTool] = {}
        
    def register_tool(self, tool: LambdaTool):
        """Register a Lambda tool"""
        self.tools[tool.name] = tool
        logger.info(f"Registered Lambda tool: {tool.name}")
        
    def get_tool(self, name: str) -> LambdaTool:
        """Get a tool by name"""
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found in registry")
        return self.tools[name]
        
    def list_tools(self) -> List[LambdaTool]:
        """List all registered tools"""
        return list(self.tools.values())
        
    def get_openapi_schema(self) -> Dict[str, Any]:
        """Generate OpenAPI schema for all tools"""
        schema = {
            "openapi": "3.0.0",
            "info": {
                "title": "Province Tax System Lambda Tools",
                "version": "1.0.0",
                "description": "AWS Lambda tools for Bedrock Agents"
            },
            "paths": {}
        }
        
        for tool in self.tools.values():
            path = f"/{tool.name}"
            schema["paths"][path] = {
                "post": {
                    "summary": tool.description,
                    "operationId": tool.name,
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": tool.parameters,
                                    "required": list(tool.parameters.keys())
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "result": {"type": "string"},
                                            "success": {"type": "boolean"},
                                            "data": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
        return schema


# Global registry instance
tool_registry = ToolRegistry()


def register_all_tools():
    """Register all available Lambda tools"""
    
    # Save Document Tool
    save_doc_tool = LambdaTool(
        name="save_document",
        description="Save a document to S3 storage with proper indexing",
        lambda_function_name="province-save-document",
        handler="lambda_function.lambda_handler",
        runtime="python3.9",
        timeout=60,
        memory_size=256,
        environment_variables={
            "S3_BUCKET": "province-documents-[REDACTED-ACCOUNT-ID]-us-east-2",
            "OPENSEARCH_ENDPOINT": ""
        },
        parameters={
            "matter_id": {
                "type": "string",
                "description": "Matter ID to associate document with"
            },
            "document_name": {
                "type": "string",
                "description": "Name of the document"
            },
            "content": {
                "type": "string",
                "description": "Document content"
            },
            "document_type": {
                "type": "string",
                "description": "Type of document"
            },
            "metadata": {
                "type": "object",
                "description": "Additional metadata for the document"
            }
        },
        required_permissions=[
            "s3:PutObject",
            "s3:PutObjectAcl"
        ]
    )
    tool_registry.register_tool(save_doc_tool)
    
    # Create Deadline Tool
    deadline_tool = LambdaTool(
        name="create_deadline",
        description="Create a deadline with EventBridge scheduling and notifications",
        lambda_function_name="province-create-deadline",
        handler="lambda_function.lambda_handler",
        runtime="python3.9",
        timeout=30,
        memory_size=256,
        environment_variables={
            "DEADLINES_TABLE": "province-deadlines",
            "SNS_TOPIC_ARN": "arn:aws:sns:us-east-1:123456789012:deadline-notifications"
        },
        parameters={
            "title": {
                "type": "string",
                "description": "Title of the deadline"
            },
            "description": {
                "type": "string",
                "description": "Description of the deadline"
            },
            "due_date": {
                "type": "string",
                "format": "date-time",
                "description": "Due date in ISO format"
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high", "critical"],
                "description": "Priority level"
            },
            "reminder_settings": {
                "type": "object",
                "description": "Reminder configuration"
            }
        },
        required_permissions=[
            "dynamodb:PutItem",
            "events:PutRule",
            "events:PutTargets",
            "sns:Publish"
        ]
    )
    tool_registry.register_tool(deadline_tool)


# Initialize all tools
register_all_tools()
