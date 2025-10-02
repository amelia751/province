#!/usr/bin/env python3
"""AWS CDK application entry point."""

import aws_cdk as cdk
from constructs import Construct

from infrastructure.stacks.core_stack import CoreStack
from infrastructure.stacks.api_stack import ApiStack
from infrastructure.stacks.agent_stack import AgentStack


class AILegalOSApp(Construct):
    """Main CDK application for AI Legal OS."""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Environment configuration
        env = cdk.Environment(
            account=kwargs.get("account"),
            region=kwargs.get("region", "us-east-1")
        )
        
        # Core infrastructure stack (DynamoDB, S3, KMS, etc.)
        core_stack = CoreStack(
            self, "AILegalOSCore",
            env=env,
            description="Core infrastructure for AI Legal OS"
        )
        
        # API stack (API Gateway, Lambda, Cognito)
        api_stack = ApiStack(
            self, "AILegalOSApi",
            core_resources=core_stack.core_resources,
            env=env,
            description="API infrastructure for AI Legal OS"
        )
        
        # Agent runtime stack (Bedrock, EventBridge, SNS)
        agent_stack = AgentStack(
            self, "AILegalOSAgents",
            core_resources=core_stack.core_resources,
            api_resources=api_stack.api_resources,
            env=env,
            description="Agent runtime infrastructure for AI Legal OS"
        )
        
        # Add dependencies
        api_stack.add_dependency(core_stack)
        agent_stack.add_dependency(core_stack)
        agent_stack.add_dependency(api_stack)


def main() -> None:
    """Main CDK application."""
    app = cdk.App()
    
    # Get environment from context or use defaults
    account = app.node.try_get_context("account")
    region = app.node.try_get_context("region") or "us-east-1"
    environment = app.node.try_get_context("environment") or "dev"
    
    AILegalOSApp(
        app, f"AILegalOS-{environment}",
        account=account,
        region=region,
        environment=environment
    )
    
    app.synth()


if __name__ == "__main__":
    main()