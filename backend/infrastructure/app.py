#!/usr/bin/env python3
"""AWS CDK application entry point."""

import aws_cdk as cdk
from constructs import Construct

from infrastructure.stacks.core_stack import CoreStack
from infrastructure.stacks.api_stack import ApiStack
from infrastructure.stacks.agent_stack import AgentStack
from infrastructure.stacks.tax_stack import TaxStack


def main() -> None:
    """Main CDK application."""
    app = cdk.App()
    
    # Get environment from context or use defaults
    account = app.node.try_get_context("account")
    region = app.node.try_get_context("region") or "us-east-2"
    environment = app.node.try_get_context("environment") or "dev"
    
    # Environment configuration
    env = cdk.Environment(
        account=account,
        region=region
    )
    
    # Core infrastructure stack (DynamoDB, S3, KMS, etc.)
    core_stack = CoreStack(
        app, f"AILegalOSCore-{environment}",
        env=env,
        description="Core infrastructure for AI Legal OS"
    )
    
    # API stack (API Gateway, Lambda, Cognito)
    api_stack = ApiStack(
        app, f"AILegalOSApi-{environment}",
        core_resources=core_stack.core_resources,
        env=env,
        description="API infrastructure for AI Legal OS"
    )
    
    # Tax infrastructure stack (Tax-specific DynamoDB tables)
    tax_stack = TaxStack(
        app, f"AILegalOSTax-{environment}",
        kms_key=core_stack.core_resources.kms_key,
        env=env,
        description="Tax infrastructure for AI Legal OS"
    )
    
    # Agent runtime stack (Bedrock, EventBridge, SNS)
    agent_stack = AgentStack(
        app, f"AILegalOSAgents-{environment}",
        core_resources=core_stack.core_resources,
        api_resources=api_stack.api_resources,
        env=env,
        description="Agent runtime infrastructure for AI Legal OS"
    )
    
    # Add dependencies
    api_stack.add_dependency(core_stack)
    tax_stack.add_dependency(core_stack)
    agent_stack.add_dependency(core_stack)
    agent_stack.add_dependency(api_stack)
    
    app.synth()


if __name__ == "__main__":
    main()