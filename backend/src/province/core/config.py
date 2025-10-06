"""Application configuration management."""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=[".env.local", ".env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from .env.local
    )
    
    # Environment
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    
    # API Configuration
    api_title: str = Field(default="Province Legal OS Backend", description="API title")
    api_version: str = Field(default="0.1.0", description="API version")
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )
    
    # AWS Configuration
    aws_region: str = Field(default="us-east-1", description="AWS region")
    aws_profile: str = Field(default="", description="AWS profile name")
    
    # DynamoDB Tables
    matters_table_name: str = Field(default="matters", description="Matters table name")
    documents_table_name: str = Field(default="documents", description="Documents table name")
    permissions_table_name: str = Field(default="permissions", description="Permissions table name")
    deadlines_table_name: str = Field(default="deadlines", description="Deadlines table name")
    
    # Tax-specific DynamoDB Tables
    tax_engagements_table_name: str = Field(default="tax-engagements", description="Tax engagements table name")
    tax_documents_table_name: str = Field(default="tax-documents", description="Tax documents table name")
    tax_permissions_table_name: str = Field(default="tax-permissions", description="Tax permissions table name")
    tax_deadlines_table_name: str = Field(default="tax-deadlines", description="Tax deadlines table name")
    tax_connections_table_name: str = Field(default="tax-connections", description="Tax connections table name")
    
    # S3 Configuration
    documents_bucket_name: str = Field(default="documents", description="Documents S3 bucket")
    templates_bucket_name: str = Field(default="templates", description="Templates S3 bucket")
    
    # OpenSearch Configuration
    opensearch_endpoint: str = Field(default="", description="OpenSearch Serverless endpoint")
    opensearch_index_name: str = Field(default="legal-documents", description="OpenSearch index name")
    
    # Cognito Configuration
    cognito_user_pool_id: str = Field(default="", description="Cognito User Pool ID")
    cognito_client_id: str = Field(default="", description="Cognito Client ID")
    cognito_region: str = Field(default="us-east-1", description="Cognito region")
    
    # Bedrock Configuration
    bedrock_region: str = Field(default="us-east-1", description="Bedrock region")
    bedrock_model_id: str = Field(default="anthropic.claude-3-sonnet-20240229-v1:0", description="Default Bedrock model")
    
    # KMS Configuration
    kms_key_alias: str = Field(default="alias/province", description="KMS key alias")
    
    # EventBridge Configuration
    eventbridge_bus_name: str = Field(default="province-events", description="EventBridge bus name")
    
    # SNS Configuration
    sns_topic_arn: str = Field(default="", description="SNS topic ARN for notifications")
    
    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(default="json", description="Log format (json or console)")


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()