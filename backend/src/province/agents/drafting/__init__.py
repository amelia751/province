"""
Legal Drafting Agent with Bedrock Integration

This module provides specialized legal document drafting capabilities
using AWS Bedrock models with context-aware generation and citation validation.
"""

from .bedrock_client import DraftingBedrockClient
from .drafting_agent import LegalDraftingAgent
from .prompt_templates import PromptTemplateManager
from .citation_workflow import CitationWorkflow

__all__ = [
    'DraftingBedrockClient',
    'LegalDraftingAgent', 
    'PromptTemplateManager',
    'CitationWorkflow'
]