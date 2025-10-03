"""
AWS Bedrock Models Integration

This module handles integration with Bedrock foundation models
(Nova, Claude, etc.) through the managed Bedrock Agents service.
"""

import boto3
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Supported model providers in Bedrock"""
    AMAZON_NOVA = "amazon.nova"
    ANTHROPIC_CLAUDE = "anthropic.claude"
    AI21_JURASSIC = "ai21.j2"
    COHERE_COMMAND = "cohere.command"


@dataclass
class ModelConfig:
    """Configuration for a Bedrock model"""
    model_id: str
    model_arn: str
    provider: ModelProvider
    name: str
    description: str
    max_tokens: int
    supports_streaming: bool
    supports_tool_use: bool


@dataclass
class ModelInvocationConfig:
    """Configuration for model invocation"""
    temperature: float = 0.1
    top_p: float = 0.9
    max_tokens: int = 4096
    stop_sequences: Optional[List[str]] = None


class BedrockModelClient:
    """
    Client for Bedrock foundation models.
    
    Note: When used with Bedrock Agents, the agent handles model invocation.
    This client is for direct model access when needed.
    """
    
    def __init__(self, region_name: str = "us-east-1"):
        self.region_name = region_name
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=region_name
        )
        self.bedrock = boto3.client(
            'bedrock',
            region_name=region_name
        )
        
    def invoke_model(
        self,
        model_id: str,
        prompt: str,
        config: ModelInvocationConfig = None
    ) -> Dict[str, Any]:
        """
        Invoke a Bedrock model directly.
        
        Note: This is for direct model access. Bedrock Agents handle
        model invocation automatically through AgentCore.
        """
        if config is None:
            config = ModelInvocationConfig()
            
        try:
            # Format request based on model provider
            if model_id.startswith("amazon.nova"):
                body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "temperature": config.temperature,
                        "topP": config.top_p,
                        "maxTokenCount": config.max_tokens
                    }
                }
            elif model_id.startswith("anthropic.claude"):
                body = {
                    "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                    "temperature": config.temperature,
                    "top_p": config.top_p,
                    "max_tokens_to_sample": config.max_tokens
                }
            else:
                raise ValueError(f"Unsupported model: {model_id}")
                
            if config.stop_sequences:
                body["stop_sequences"] = config.stop_sequences
                
            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extract text based on model provider
            if model_id.startswith("amazon.nova"):
                return {
                    "text": response_body["results"][0]["outputText"],
                    "usage": response_body.get("inputTextTokenCount", 0) + response_body.get("results", [{}])[0].get("tokenCount", 0)
                }
            elif model_id.startswith("anthropic.claude"):
                return {
                    "text": response_body["completion"],
                    "usage": response_body.get("usage", {})
                }
                
        except Exception as e:
            logger.error(f"Error invoking model {model_id}: {str(e)}")
            raise
            
    def list_foundation_models(self) -> List[Dict[str, Any]]:
        """List available foundation models"""
        try:
            response = self.bedrock.list_foundation_models()
            return response['modelSummaries']
        except Exception as e:
            logger.error(f"Error listing foundation models: {str(e)}")
            raise


class ModelRegistry:
    """Registry of available Bedrock models for the legal OS"""
    
    def __init__(self):
        self.models: Dict[str, ModelConfig] = {}
        self.client = BedrockModelClient()
        
    def register_model(self, config: ModelConfig):
        """Register a model configuration"""
        self.models[config.name] = config
        logger.info(f"Registered model: {config.name}")
        
    def get_model(self, name: str) -> ModelConfig:
        """Get a model configuration by name"""
        if name not in self.models:
            raise ValueError(f"Model {name} not found in registry")
        return self.models[name]
        
    def get_default_drafting_model(self) -> ModelConfig:
        """Get the default model for legal document drafting"""
        return self.get_model("claude_sonnet")
        
    def get_default_analysis_model(self) -> ModelConfig:
        """Get the default model for legal analysis"""
        return self.get_model("nova_pro")
        
    def list_models(self) -> List[ModelConfig]:
        """List all registered models"""
        return list(self.models.values())


# Global model registry
model_registry = ModelRegistry()


def register_legal_models():
    """Register the models used by the legal OS"""
    
    # Amazon Nova Pro - for complex legal analysis
    nova_pro_config = ModelConfig(
        model_id="amazon.nova-pro-v1:0",
        model_arn="arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-pro-v1:0",
        provider=ModelProvider.AMAZON_NOVA,
        name="nova_pro",
        description="Amazon Nova Pro for complex legal analysis and reasoning",
        max_tokens=200000,
        supports_streaming=True,
        supports_tool_use=True
    )
    model_registry.register_model(nova_pro_config)
    
    # Amazon Nova Lite - for quick tasks
    nova_lite_config = ModelConfig(
        model_id="amazon.nova-lite-v1:0",
        model_arn="arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-lite-v1:0",
        provider=ModelProvider.AMAZON_NOVA,
        name="nova_lite",
        description="Amazon Nova Lite for quick legal tasks and summaries",
        max_tokens=100000,
        supports_streaming=True,
        supports_tool_use=True
    )
    model_registry.register_model(nova_lite_config)
    
    # Claude 3.5 Sonnet - for legal document drafting
    claude_sonnet_config = ModelConfig(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        model_arn="arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
        provider=ModelProvider.ANTHROPIC_CLAUDE,
        name="claude_sonnet",
        description="Claude 3.5 Sonnet for precise legal document drafting",
        max_tokens=200000,
        supports_streaming=True,
        supports_tool_use=True
    )
    model_registry.register_model(claude_sonnet_config)
    
    # Claude 3 Haiku - for quick responses
    claude_haiku_config = ModelConfig(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        model_arn="arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
        provider=ModelProvider.ANTHROPIC_CLAUDE,
        name="claude_haiku",
        description="Claude 3 Haiku for fast legal queries and citations",
        max_tokens=100000,
        supports_streaming=True,
        supports_tool_use=True
    )
    model_registry.register_model(claude_haiku_config)


# Initialize models
register_legal_models()