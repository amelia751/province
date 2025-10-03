"""
AWS Lambda Tools for Bedrock Agents

Each tool is implemented as a separate AWS Lambda function.
This module provides the registry and deployment utilities.
"""

from .registry import tool_registry
from .deploy import deploy_all_tools

__all__ = ['tool_registry', 'deploy_all_tools']