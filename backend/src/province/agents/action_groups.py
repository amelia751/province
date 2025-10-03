"""
AWS Bedrock Agent Action Groups

Action Groups are AWS managed tool execution environments.
This module integrates with the Lambda tools registry.
"""

import logging
from typing import Dict, Any, List
from .tools.registry import tool_registry

logger = logging.getLogger(__name__)


class ActionGroupManager:
    """Manager for Bedrock Agent Action Groups"""
    
    def __init__(self):
        self.tool_registry = tool_registry
        
    def get_openapi_schema(self) -> Dict[str, Any]:
        """
        Generate OpenAPI schema for all Lambda tools.
        This is used by AWS Bedrock Agents to understand available tools.
        """
        return self.tool_registry.get_openapi_schema()
        
    def list_tools(self):
        """List all available Lambda tools"""
        return self.tool_registry.list_tools()
        
    def get_tool(self, name: str):
        """Get a specific Lambda tool"""
        return self.tool_registry.get_tool(name)
        
    def create_action_group_config(self, action_group_name: str = "LegalTools") -> Dict[str, Any]:
        """
        Create Action Group configuration for Bedrock Agent deployment
        """
        return {
            'name': action_group_name,
            'description': 'AWS Lambda tools for legal document operations',
            'lambda_arn': 'arn:aws:lambda:us-east-1:ACCOUNT:function:legal-tools-dispatcher',
            'api_schema': self.get_openapi_schema()
        }


# Global action group manager
action_group_manager = ActionGroupManager()

# For backward compatibility
action_group_registry = action_group_manager