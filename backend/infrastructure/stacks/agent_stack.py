"""Agent runtime infrastructure stack for AI Legal OS."""

from typing import Dict, Any

import aws_cdk as cdk
from aws_cdk import (
    aws_events as events,
    aws_events_targets as events_targets,
    aws_sns as sns,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct

from infrastructure.stacks.core_stack import CoreResources
from infrastructure.stacks.api_stack import ApiResources


class AgentResources:
    """Container for agent infrastructure resources."""
    
    def __init__(self) -> None:
        self.event_bus: events.EventBus
        self.notification_topic: sns.Topic


class AgentStack(cdk.Stack):
    """Agent runtime infrastructure stack."""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        core_resources: CoreResources,
        api_resources: ApiResources,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.core_resources = core_resources
        self.api_resources = api_resources
        self.agent_resources = AgentResources()
        
        # Create SNS topic for notifications
        self._create_notification_topic()
        
        # Create EventBridge custom bus
        self._create_event_bus()
        
        # Configure X-Ray tracing
        self._configure_xray_tracing()
        
        # Agent permissions will be granted in the API stack to avoid cyclic dependencies
        
        # Create outputs
        self._create_outputs()
    
    def _create_event_bus(self) -> None:
        """Create EventBridge custom bus for agent events."""
        
        self.agent_resources.event_bus = events.EventBus(
            self, "AILegalOSEventBus",
            event_bus_name="ai-legal-os-events",
            description="Custom event bus for AI Legal OS agent events",
        )
        
        # Create event rules for deadline management
        deadline_rule = events.Rule(
            self, "DeadlineRule",
            event_bus=self.agent_resources.event_bus,
            rule_name="ai-legal-os-deadline-rule",
            description="Rule for deadline reminder events",
            event_pattern=events.EventPattern(
                source=["ai-legal-os.deadlines"],
                detail_type=["Deadline Reminder"],
            ),
        )
        
        # Add SNS target to deadline rule
        deadline_rule.add_target(
            events_targets.SnsTopic(self.agent_resources.notification_topic)
        )
    
    def _create_notification_topic(self) -> None:
        """Create SNS topic for notifications."""
        
        self.agent_resources.notification_topic = sns.Topic(
            self, "AILegalOSNotificationTopic",
            topic_name="ai-legal-os-notifications",
            display_name="AI Legal OS Notifications",
            master_key=self.core_resources.kms_key,
        )
        
        # Create subscription for email notifications (placeholder)
        # In production, this would be configured with actual email addresses
        # or integrated with SES for transactional emails
    
    def _configure_xray_tracing(self) -> None:
        """Configure X-Ray tracing for observability."""
        
        # Enable X-Ray tracing on the Lambda function
        self.api_resources.lambda_function.add_environment(
            "AWS_XRAY_TRACING_NAME", "ai-legal-os-backend"
        )
        
        # Grant X-Ray permissions to Lambda
        self.api_resources.lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                ],
                resources=["*"],
            )
        )
    
    def _grant_agent_permissions(self) -> None:
        """Grant additional permissions needed for agent operations."""
        
        lambda_role = self.api_resources.lambda_function.role
        
        # EventBridge permissions
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "events:PutEvents",
                ],
                resources=[self.agent_resources.event_bus.event_bus_arn],
            )
        )
        
        # SNS permissions
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "sns:Publish",
                ],
                resources=[self.agent_resources.notification_topic.topic_arn],
            )
        )
        
        # Textract permissions for evidence processing
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "textract:DetectDocumentText",
                    "textract:AnalyzeDocument",
                    "textract:StartDocumentAnalysis",
                    "textract:GetDocumentAnalysis",
                ],
                resources=["*"],
            )
        )
        
        # Transcribe permissions for audio processing
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "transcribe:StartTranscriptionJob",
                    "transcribe:GetTranscriptionJob",
                ],
                resources=["*"],
            )
        )
        
        # Comprehend permissions for entity extraction
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "comprehend:DetectEntities",
                    "comprehend:DetectPiiEntities",
                    "comprehendmedical:DetectEntitiesV2",
                    "comprehendmedical:DetectPHI",
                ],
                resources=["*"],
            )
        )
        
        # Macie permissions for PII detection
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "macie2:CreateClassificationJob",
                    "macie2:GetFindings",
                ],
                resources=["*"],
            )
        )
        
        # CloudWatch Logs permissions for enhanced logging
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:PutMetricFilter",
                ],
                resources=["*"],
            )
        )
    
    def _create_outputs(self) -> None:
        """Create CloudFormation outputs."""
        
        cdk.CfnOutput(
            self, "EventBusName",
            value=self.agent_resources.event_bus.event_bus_name,
            description="EventBridge custom bus name"
        )
        
        cdk.CfnOutput(
            self, "NotificationTopicArn",
            value=self.agent_resources.notification_topic.topic_arn,
            description="SNS notification topic ARN"
        )