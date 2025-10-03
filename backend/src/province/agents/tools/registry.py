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
                "title": "Province Legal OS Lambda Tools",
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
    
    # Search Matter Corpus Tool
    search_tool = LambdaTool(
        name="search_matter_corpus",
        description="Search through legal documents and case law using OpenSearch",
        lambda_function_name="province-search-matter-corpus",
        handler="lambda_function.lambda_handler",
        runtime="python3.9",
        timeout=30,
        memory_size=512,
        environment_variables={
            "OPENSEARCH_ENDPOINT": "search-legal-corpus-xyz.us-east-1.es.amazonaws.com",
            "INDEX_NAME": "legal-documents"
        },
        parameters={
            "query": {
                "type": "string",
                "description": "Search query for finding relevant documents"
            },
            "matter_id": {
                "type": "string", 
                "description": "Optional matter ID to scope search to specific matter"
            },
            "document_types": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional filter by document types"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 10
            }
        },
        required_permissions=[
            "es:ESHttpGet",
            "es:ESHttpPost",
            "aoss:APIAccessAll"
        ]
    )
    tool_registry.register_tool(search_tool)
    
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
            "S3_BUCKET": "province-legal-documents",
            "OPENSEARCH_ENDPOINT": "search-legal-corpus-xyz.us-east-1.es.amazonaws.com"
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
                "description": "Type of document (brief, motion, contract, etc.)"
            },
            "metadata": {
                "type": "object",
                "description": "Additional metadata for the document"
            }
        },
        required_permissions=[
            "s3:PutObject",
            "s3:PutObjectAcl",
            "es:ESHttpPost",
            "aoss:APIAccessAll"
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
            "DYNAMODB_TABLE": "province-deadlines",
            "SNS_TOPIC_ARN": "arn:aws:sns:us-east-1:ACCOUNT:deadline-notifications"
        },
        parameters={
            "matter_id": {
                "type": "string",
                "description": "Matter ID to associate deadline with"
            },
            "title": {
                "type": "string",
                "description": "Deadline title"
            },
            "due_date": {
                "type": "string",
                "format": "date-time",
                "description": "Due date in ISO format"
            },
            "description": {
                "type": "string",
                "description": "Optional deadline description"
            },
            "reminder_days": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Days before due date to send reminders"
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
    
    # Validate Citations Tool
    citations_tool = LambdaTool(
        name="validate_citations",
        description="Validate legal citations using external legal databases",
        lambda_function_name="province-validate-citations",
        handler="lambda_function.lambda_handler",
        runtime="python3.9",
        timeout=45,
        memory_size=512,
        environment_variables={
            "LEGAL_API_ENDPOINT": "https://api.courtlistener.com/api/rest/v3/",
            "WESTLAW_API_KEY": "placeholder"
        },
        parameters={
            "citations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of legal citations to validate"
            },
            "document_context": {
                "type": "string",
                "description": "Context where citations are used"
            },
            "jurisdiction": {
                "type": "string",
                "description": "Legal jurisdiction for citation validation"
            }
        },
        required_permissions=[
            "secretsmanager:GetSecretValue"
        ]
    )
    tool_registry.register_tool(citations_tool)
    
    # Generate Contract Tool
    contract_tool = LambdaTool(
        name="generate_contract",
        description="Generate legal contract using Bedrock models and templates",
        lambda_function_name="province-generate-contract",
        handler="lambda_function.lambda_handler",
        runtime="python3.9",
        timeout=120,
        memory_size=1024,
        environment_variables={
            "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "TEMPLATE_BUCKET": "province-legal-templates"
        },
        parameters={
            "contract_type": {
                "type": "string",
                "description": "Type of contract to generate (NDA, employment, etc.)"
            },
            "parties": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Contract parties information"
            },
            "terms": {
                "type": "object",
                "description": "Contract terms and conditions"
            },
            "jurisdiction": {
                "type": "string",
                "description": "Legal jurisdiction for the contract"
            }
        },
        required_permissions=[
            "bedrock:InvokeModel",
            "s3:GetObject"
        ]
    )
    tool_registry.register_tool(contract_tool)


# Initialize all tools
register_all_tools()