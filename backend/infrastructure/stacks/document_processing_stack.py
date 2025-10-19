"""
CDK Stack for automated document processing pipeline.

This stack creates:
1. Lambda function for document processing
2. S3 event notifications → EventBridge → Lambda
3. DynamoDB table for chat notifications
4. IAM roles and permissions
"""

from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_events as events,
    aws_events_targets as targets,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    RemovalPolicy
)
from constructs import Construct

class DocumentProcessingStack(Stack):
    """Stack for automated document processing pipeline."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get existing S3 bucket
        documents_bucket = s3.Bucket.from_bucket_name(
            self, "DocumentsBucket",
            bucket_name="province-documents-[REDACTED-ACCOUNT-ID]-us-east-1"
        )

        # Create DynamoDB table for chat notifications
        notifications_table = dynamodb.Table(
            self, "ChatNotificationsTable",
            table_name="province-chat-notifications",
            partition_key=dynamodb.Attribute(
                name="engagement_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            time_to_live_attribute="ttl"  # Auto-cleanup old notifications
        )

        # Create Lambda execution role
        lambda_role = iam.Role(
            self, "DocumentProcessorRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        # Add permissions for S3, DynamoDB, and Bedrock
        lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "s3:GetObject",
                "s3:GetObjectVersion"
            ],
            resources=[f"{documents_bucket.bucket_arn}/*"]
        ))

        lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            resources=[
                notifications_table.table_arn,
                "arn:aws:dynamodb:us-east-1:*:table/province-tax-documents",
                "arn:aws:dynamodb:us-east-1:*:table/province-tax-engagements"
            ]
        ))

        lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock:InvokeModel",
                "bedrock:InvokeDataAutomationAsync",
                "bedrock:GetDataAutomationStatus",
                "bedrock:ListDataAutomationJobs"
            ],
            resources=["*"]
        ))

        # Create Lambda function
        document_processor = _lambda.Function(
            self, "DocumentProcessor",
            function_name="province-document-processor",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="province.lambda.document_processor.lambda_handler",
            code=_lambda.Code.from_asset("src"),
            timeout=Duration.minutes(5),
            memory_size=512,
            role=lambda_role,
            environment={
                "NOTIFICATIONS_TABLE": notifications_table.table_name,
                "AWS_REGION": self.region
            }
        )

        # Create EventBridge rule for S3 events
        s3_event_rule = events.Rule(
            self, "S3DocumentUploadRule",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created"],
                detail={
                    "bucket": {
                        "name": [documents_bucket.bucket_name]
                    },
                    "object": {
                        "key": [{"prefix": "tax-engagements/"}]
                    }
                }
            )
        )

        # Add Lambda as target for the EventBridge rule
        s3_event_rule.add_target(targets.LambdaFunction(document_processor))

        # Enable S3 event notifications to EventBridge
        # Note: This needs to be done manually or via AWS CLI as CDK doesn't support it directly
        # aws s3api put-bucket-notification-configuration --bucket province-documents-[REDACTED-ACCOUNT-ID]-us-east-1 --notification-configuration file://s3-notification-config.json

        # Create API endpoint for polling notifications
        notifications_api = _lambda.Function(
            self, "NotificationsAPI",
            function_name="province-notifications-api",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="province.lambda.notifications_api.lambda_handler",
            code=_lambda.Code.from_asset("src"),
            timeout=Duration.seconds(30),
            memory_size=256,
            role=lambda_role,
            environment={
                "NOTIFICATIONS_TABLE": notifications_table.table_name
            }
        )

        # Output important values
        self.notifications_table_name = notifications_table.table_name
        self.document_processor_arn = document_processor.function_arn
        self.notifications_api_arn = notifications_api.function_arn
