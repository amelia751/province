"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
import boto3

from province.main import create_app


@pytest.fixture
def mock_aws_credentials(monkeypatch):
    """Mock AWS credentials for testing."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def mock_aws_services(mock_aws_credentials):
    """Mock AWS services for testing."""
    with mock_aws():
        # Create DynamoDB tables
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        
        # Create templates table
        templates_table = dynamodb.create_table(
            TableName="province-templates",
            KeySchema=[
                {"AttributeName": "template_id", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "template_id", "AttributeType": "S"},
                {"AttributeName": "name", "AttributeType": "S"},
                {"AttributeName": "is_active", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "NameIndex",
                    "KeySchema": [
                        {"AttributeName": "name", "KeyType": "HASH"}
                    ],
                    "Projection": {"ProjectionType": "ALL"}
                },
                {
                    "IndexName": "ActiveIndex",
                    "KeySchema": [
                        {"AttributeName": "is_active", "KeyType": "HASH"}
                    ],
                    "Projection": {"ProjectionType": "ALL"}
                }
            ]
        )
        
        # Create matters table
        matters_table = dynamodb.create_table(
            TableName="province-matters",
            KeySchema=[
                {"AttributeName": "matter_id", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "matter_id", "AttributeType": "S"},
                {"AttributeName": "tenant_id", "AttributeType": "S"},
                {"AttributeName": "created_at", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "TenantIndex",
                    "KeySchema": [
                        {"AttributeName": "tenant_id", "KeyType": "HASH"},
                        {"AttributeName": "created_at", "KeyType": "RANGE"}
                    ],
                    "Projection": {"ProjectionType": "ALL"}
                }
            ]
        )
        
        # Create documents table
        documents_table = dynamodb.create_table(
            TableName="province-documents",
            KeySchema=[
                {"AttributeName": "document_id", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "document_id", "AttributeType": "S"},
                {"AttributeName": "matter_id", "AttributeType": "S"},
                {"AttributeName": "created_at", "AttributeType": "S"},
                {"AttributeName": "folder_path", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "MatterIndex",
                    "KeySchema": [
                        {"AttributeName": "matter_id", "KeyType": "HASH"},
                        {"AttributeName": "created_at", "KeyType": "RANGE"}
                    ],
                    "Projection": {"ProjectionType": "ALL"}
                },
                {
                    "IndexName": "FolderIndex",
                    "KeySchema": [
                        {"AttributeName": "matter_id", "KeyType": "HASH"},
                        {"AttributeName": "folder_path", "KeyType": "RANGE"}
                    ],
                    "Projection": {"ProjectionType": "ALL"}
                }
            ]
        )
        
        # Create S3 buckets
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-documents-bucket")
        s3.create_bucket(Bucket="test-templates-bucket")
        
        yield {
            "dynamodb": dynamodb,
            "s3": s3,
            "templates_table": templates_table,
            "matters_table": matters_table,
            "documents_table": documents_table
        }


@pytest.fixture
def app(mock_aws_services, monkeypatch):
    """Create FastAPI application for testing."""
    # Set environment variables for testing
    monkeypatch.setenv("TEMPLATES_TABLE_NAME", "province-templates")
    monkeypatch.setenv("MATTERS_TABLE_NAME", "province-matters")
    monkeypatch.setenv("DOCUMENTS_TABLE_NAME", "province-documents")
    monkeypatch.setenv("DOCUMENTS_BUCKET_NAME", "test-documents-bucket")
    monkeypatch.setenv("TEMPLATES_BUCKET_NAME", "test-templates-bucket")
    
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)