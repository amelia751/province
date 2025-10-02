"""Core infrastructure stack for AI Legal OS."""

from typing import Dict, Any

import aws_cdk as cdk
from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_kms as kms,
    aws_opensearchserverless as opensearch,
    aws_iam as iam,
)
from constructs import Construct


class CoreResources:
    """Container for core infrastructure resources."""
    
    def __init__(self) -> None:
        self.kms_key: kms.Key
        self.matters_table: dynamodb.Table
        self.documents_table: dynamodb.Table
        self.permissions_table: dynamodb.Table
        self.deadlines_table: dynamodb.Table
        self.templates_table: dynamodb.Table
        self.documents_bucket: s3.Bucket
        self.templates_bucket: s3.Bucket
        self.opensearch_collection: opensearch.CfnCollection


class CoreStack(cdk.Stack):
    """Core infrastructure stack."""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.core_resources = CoreResources()
        
        # Create KMS key for encryption
        self._create_kms_key()
        
        # Create DynamoDB tables
        self._create_dynamodb_tables()
        
        # Create S3 buckets
        self._create_s3_buckets()
        
        # Create OpenSearch Serverless collection
        self._create_opensearch_collection()
        
        # Output important resource ARNs
        self._create_outputs()
    
    def _create_kms_key(self) -> None:
        """Create KMS key for tenant-scoped encryption."""
        self.core_resources.kms_key = kms.Key(
            self, "AILegalOSKey",
            description="AI Legal OS encryption key",
            enable_key_rotation=True,
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )
        
        # Create alias for the key
        kms.Alias(
            self, "AILegalOSKeyAlias",
            alias_name="alias/ai-legal-os",
            target_key=self.core_resources.kms_key,
        )
    
    def _create_dynamodb_tables(self) -> None:
        """Create DynamoDB tables for core data."""
        
        # Matters table
        self.core_resources.matters_table = dynamodb.Table(
            self, "MattersTable",
            table_name="ai-legal-os-matters",
            partition_key=dynamodb.Attribute(
                name="tenant_id_matter_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.core_resources.kms_key,
            point_in_time_recovery=True,
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )
        
        # Add GSI for user queries
        self.core_resources.matters_table.add_global_secondary_index(
            index_name="UserIndex",
            partition_key=dynamodb.Attribute(
                name="created_by",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            ),
        )
        
        # Documents table
        self.core_resources.documents_table = dynamodb.Table(
            self, "DocumentsTable",
            table_name="ai-legal-os-documents",
            partition_key=dynamodb.Attribute(
                name="matter_id_path",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.core_resources.kms_key,
            point_in_time_recovery=True,
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )
        
        # Add GSI for document ID queries
        self.core_resources.documents_table.add_global_secondary_index(
            index_name="DocumentIdIndex",
            partition_key=dynamodb.Attribute(
                name="document_id",
                type=dynamodb.AttributeType.STRING
            ),
        )
        
        # Add GSI for matter queries
        self.core_resources.documents_table.add_global_secondary_index(
            index_name="MatterIndex",
            partition_key=dynamodb.Attribute(
                name="matter_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            ),
        )
        
        # Permissions table
        self.core_resources.permissions_table = dynamodb.Table(
            self, "PermissionsTable",
            table_name="ai-legal-os-permissions",
            partition_key=dynamodb.Attribute(
                name="subject_id_matter_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.core_resources.kms_key,
            point_in_time_recovery=True,
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )
        
        # Deadlines table
        self.core_resources.deadlines_table = dynamodb.Table(
            self, "DeadlinesTable",
            table_name="ai-legal-os-deadlines",
            partition_key=dynamodb.Attribute(
                name="matter_id_deadline_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.core_resources.kms_key,
            point_in_time_recovery=True,
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )
        
        # Add GSI for due date queries
        self.core_resources.deadlines_table.add_global_secondary_index(
            index_name="DueDateIndex",
            partition_key=dynamodb.Attribute(
                name="owner_user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="due_date",
                type=dynamodb.AttributeType.STRING
            ),
        )
        
        # Templates table
        self.core_resources.templates_table = dynamodb.Table(
            self, "TemplatesTable",
            table_name="ai-legal-os-templates",
            partition_key=dynamodb.Attribute(
                name="template_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.core_resources.kms_key,
            point_in_time_recovery=True,
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )
        
        # Add GSI for name queries
        self.core_resources.templates_table.add_global_secondary_index(
            index_name="NameIndex",
            partition_key=dynamodb.Attribute(
                name="name",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="version",
                type=dynamodb.AttributeType.STRING
            ),
        )
        
        # Add GSI for active templates
        self.core_resources.templates_table.add_global_secondary_index(
            index_name="ActiveIndex",
            partition_key=dynamodb.Attribute(
                name="is_active",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="usage_count",
                type=dynamodb.AttributeType.NUMBER
            ),
        )
    
    def _create_s3_buckets(self) -> None:
        """Create S3 buckets for document storage."""
        
        # Documents bucket
        self.core_resources.documents_bucket = s3.Bucket(
            self, "DocumentsBucket",
            bucket_name=f"ai-legal-os-documents-{self.account}-{self.region}",
            versioned=True,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.core_resources.kms_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=cdk.RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="ArchiveOldVersions",
                    enabled=True,
                    noncurrent_version_transitions=[
                        s3.NoncurrentVersionTransition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=cdk.Duration.days(30)
                        ),
                        s3.NoncurrentVersionTransition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=cdk.Duration.days(90)
                        ),
                    ],
                )
            ],
        )
        
        # Templates bucket
        self.core_resources.templates_bucket = s3.Bucket(
            self, "TemplatesBucket",
            bucket_name=f"ai-legal-os-templates-{self.account}-{self.region}",
            versioned=True,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.core_resources.kms_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )
    
    def _create_opensearch_collection(self) -> None:
        """Create OpenSearch Serverless collection."""
        
        # Create security policy for encryption
        encryption_policy = opensearch.CfnSecurityPolicy(
            self, "OpenSearchEncryptionPolicy",
            name="ai-legal-os-encryption-policy",
            type="encryption",
            policy=f"""{{
                "Rules": [
                    {{
                        "ResourceType": "collection",
                        "Resource": ["collection/ai-legal-os-*"]
                    }}
                ],
                "AWSOwnedKey": false,
                "KmsARN": "{self.core_resources.kms_key.key_arn}"
            }}"""
        )
        
        # Create network policy
        network_policy = opensearch.CfnSecurityPolicy(
            self, "OpenSearchNetworkPolicy",
            name="ai-legal-os-network-policy",
            type="network",
            policy="""[
                {
                    "Rules": [
                        {
                            "ResourceType": "collection",
                            "Resource": ["collection/ai-legal-os-*"]
                        },
                        {
                            "ResourceType": "dashboard",
                            "Resource": ["collection/ai-legal-os-*"]
                        }
                    ],
                    "AllowFromPublic": false
                }
            ]"""
        )
        
        # Create the collection
        self.core_resources.opensearch_collection = opensearch.CfnCollection(
            self, "OpenSearchCollection",
            name="ai-legal-os-documents",
            description="Document search collection for AI Legal OS",
            type="SEARCH",
        )
        
        # Add dependencies
        self.core_resources.opensearch_collection.add_dependency(encryption_policy)
        self.core_resources.opensearch_collection.add_dependency(network_policy)
    
    def _create_outputs(self) -> None:
        """Create CloudFormation outputs."""
        
        cdk.CfnOutput(
            self, "KMSKeyId",
            value=self.core_resources.kms_key.key_id,
            description="KMS Key ID for encryption"
        )
        
        cdk.CfnOutput(
            self, "MattersTableName",
            value=self.core_resources.matters_table.table_name,
            description="Matters DynamoDB table name"
        )
        
        cdk.CfnOutput(
            self, "TemplatesTableName",
            value=self.core_resources.templates_table.table_name,
            description="Templates DynamoDB table name"
        )
        
        cdk.CfnOutput(
            self, "DocumentsBucketName",
            value=self.core_resources.documents_bucket.bucket_name,
            description="Documents S3 bucket name"
        )
        
        cdk.CfnOutput(
            self, "OpenSearchCollectionEndpoint",
            value=self.core_resources.opensearch_collection.attr_collection_endpoint,
            description="OpenSearch collection endpoint"
        )