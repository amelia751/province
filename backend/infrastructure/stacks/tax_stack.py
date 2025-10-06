"""Tax infrastructure stack for Province Tax Filing System."""

from typing import Dict, Any

import aws_cdk as cdk
from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_kms as kms,
)
from constructs import Construct


class TaxResources:
    """Container for tax infrastructure resources."""
    
    def __init__(self) -> None:
        self.tax_engagements_table: dynamodb.Table
        self.tax_documents_table: dynamodb.Table
        self.tax_permissions_table: dynamodb.Table
        self.tax_deadlines_table: dynamodb.Table
        self.tax_connections_table: dynamodb.Table


class TaxStack(cdk.Stack):
    """Tax infrastructure stack."""
    
    def __init__(self, scope: Construct, construct_id: str, kms_key: kms.Key, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.tax_resources = TaxResources()
        self.kms_key = kms_key
        
        # Create DynamoDB tables for tax system
        self._create_tax_dynamodb_tables()
        
        # Output important resource ARNs
        self._create_outputs()
    
    def _create_tax_dynamodb_tables(self) -> None:
        """Create DynamoDB tables for tax data."""
        
        # Tax Engagements table
        self.tax_resources.tax_engagements_table = dynamodb.Table(
            self, "TaxEngagementsTable",
            table_name="province-tax-engagements",
            partition_key=dynamodb.Attribute(
                name="tenant_id#engagement_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )
        
        # Add GSI for user queries
        self.tax_resources.tax_engagements_table.add_global_secondary_index(
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
        
        # Add GSI for status queries
        self.tax_resources.tax_engagements_table.add_global_secondary_index(
            index_name="StatusIndex",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="updated_at",
                type=dynamodb.AttributeType.STRING
            ),
        )
        
        # Tax Documents table
        self.tax_resources.tax_documents_table = dynamodb.Table(
            self, "TaxDocumentsTable",
            table_name="province-tax-documents",
            partition_key=dynamodb.Attribute(
                name="tenant_id#engagement_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="doc#path",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )
        
        # Add GSI for document type queries
        self.tax_resources.tax_documents_table.add_global_secondary_index(
            index_name="DocumentTypeIndex",
            partition_key=dynamodb.Attribute(
                name="document_type",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            ),
        )
        
        # Tax Permissions table
        self.tax_resources.tax_permissions_table = dynamodb.Table(
            self, "TaxPermissionsTable",
            table_name="province-tax-permissions",
            partition_key=dynamodb.Attribute(
                name="tenant_id#engagement_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="perm#user#user_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )
        
        # Tax Deadlines table
        self.tax_resources.tax_deadlines_table = dynamodb.Table(
            self, "TaxDeadlinesTable",
            table_name="province-tax-deadlines",
            partition_key=dynamodb.Attribute(
                name="tenant_id#engagement_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="deadline#deadline_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )
        
        # Add GSI for due date queries
        self.tax_resources.tax_deadlines_table.add_global_secondary_index(
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
        
        # Tax Connections table (for agent session management)
        self.tax_resources.tax_connections_table = dynamodb.Table(
            self, "TaxConnectionsTable",
            table_name="province-tax-connections",
            partition_key=dynamodb.Attribute(
                name="connection_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=cdk.RemovalPolicy.RETAIN,
            # TTL for automatic cleanup of old connections
            time_to_live_attribute="ttl",
        )
        
        # Add GSI for engagement queries
        self.tax_resources.tax_connections_table.add_global_secondary_index(
            index_name="EngagementIndex",
            partition_key=dynamodb.Attribute(
                name="engagement_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            ),
        )
    
    def _create_outputs(self) -> None:
        """Create CloudFormation outputs."""
        
        cdk.CfnOutput(
            self, "TaxEngagementsTableName",
            value=self.tax_resources.tax_engagements_table.table_name,
            description="Tax Engagements DynamoDB table name"
        )
        
        cdk.CfnOutput(
            self, "TaxDocumentsTableName",
            value=self.tax_resources.tax_documents_table.table_name,
            description="Tax Documents DynamoDB table name"
        )
        
        cdk.CfnOutput(
            self, "TaxPermissionsTableName",
            value=self.tax_resources.tax_permissions_table.table_name,
            description="Tax Permissions DynamoDB table name"
        )
        
        cdk.CfnOutput(
            self, "TaxDeadlinesTableName",
            value=self.tax_resources.tax_deadlines_table.table_name,
            description="Tax Deadlines DynamoDB table name"
        )
        
        cdk.CfnOutput(
            self, "TaxConnectionsTableName",
            value=self.tax_resources.tax_connections_table.table_name,
            description="Tax Connections DynamoDB table name"
        )
