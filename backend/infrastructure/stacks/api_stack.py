"""API infrastructure stack for AI Legal OS."""

from typing import Dict, Any

import aws_cdk as cdk
from aws_cdk import (
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_cognito as cognito,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct

from infrastructure.stacks.core_stack import CoreResources


class ApiResources:
    """Container for API infrastructure resources."""
    
    def __init__(self) -> None:
        self.user_pool: cognito.UserPool
        self.user_pool_client: cognito.UserPoolClient
        self.api_gateway: apigateway.RestApi
        self.lambda_function: lambda_.Function
        self.websocket_api: apigateway.WebSocketApi


class ApiStack(cdk.Stack):
    """API infrastructure stack."""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        core_resources: CoreResources,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.core_resources = core_resources
        self.api_resources = ApiResources()
        
        # Create Cognito User Pool
        self._create_cognito_user_pool()
        
        # Create Lambda function
        self._create_lambda_function()
        
        # Create API Gateway
        self._create_api_gateway()
        
        # Create WebSocket API
        self._create_websocket_api()
        
        # Create outputs
        self._create_outputs()
    
    def _create_cognito_user_pool(self) -> None:
        """Create Cognito User Pool for authentication."""
        
        self.api_resources.user_pool = cognito.UserPool(
            self, "AILegalOSUserPool",
            user_pool_name="ai-legal-os-users",
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=12,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )
        
        # Add custom attributes for tenant isolation
        self.api_resources.user_pool.add_custom_attributes(
            tenant_id=cognito.StringAttribute(min_len=1, max_len=256, mutable=False),
            roles=cognito.StringAttribute(min_len=1, max_len=1024, mutable=True),
        )
        
        # Create user pool client
        self.api_resources.user_pool_client = cognito.UserPoolClient(
            self, "AILegalOSUserPoolClient",
            user_pool=self.api_resources.user_pool,
            user_pool_client_name="ai-legal-os-client",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
            ),
            generate_secret=False,  # For frontend applications
            token_validity=cognito.TokenValidity(
                access_token=cdk.Duration.hours(1),
                id_token=cdk.Duration.hours(1),
                refresh_token=cdk.Duration.days(30),
            ),
        )
    
    def _create_lambda_function(self) -> None:
        """Create Lambda function for API backend."""
        
        # Create execution role
        lambda_role = iam.Role(
            self, "AILegalOSLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )
        
        # Grant permissions to access core resources
        self.core_resources.matters_table.grant_read_write_data(lambda_role)
        self.core_resources.documents_table.grant_read_write_data(lambda_role)
        self.core_resources.permissions_table.grant_read_write_data(lambda_role)
        self.core_resources.deadlines_table.grant_read_write_data(lambda_role)
        self.core_resources.templates_table.grant_read_write_data(lambda_role)
        self.core_resources.documents_bucket.grant_read_write(lambda_role)
        self.core_resources.templates_bucket.grant_read(lambda_role)
        self.core_resources.kms_key.grant_encrypt_decrypt(lambda_role)
        
        # Grant Bedrock permissions
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=["*"],  # Bedrock models don't have specific ARNs
            )
        )
        
        # Grant OpenSearch permissions
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "aoss:APIAccessAll",
                ],
                resources=[self.core_resources.opensearch_collection.attr_arn],
            )
        )
        
        # Create Lambda function
        self.api_resources.lambda_function = lambda_.Function(
            self, "AILegalOSLambda",
            function_name="ai-legal-os-backend",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="ai_legal_os.lambda_handler.handler",
            code=lambda_.Code.from_asset("src"),
            role=lambda_role,
            timeout=cdk.Duration.seconds(30),
            memory_size=1024,
            environment={
                "ENVIRONMENT": "production",
                "AWS_REGION": self.region,
                "MATTERS_TABLE_NAME": self.core_resources.matters_table.table_name,
                "DOCUMENTS_TABLE_NAME": self.core_resources.documents_table.table_name,
                "PERMISSIONS_TABLE_NAME": self.core_resources.permissions_table.table_name,
                "DEADLINES_TABLE_NAME": self.core_resources.deadlines_table.table_name,
                "TEMPLATES_TABLE_NAME": self.core_resources.templates_table.table_name,
                "DOCUMENTS_BUCKET_NAME": self.core_resources.documents_bucket.bucket_name,
                "TEMPLATES_BUCKET_NAME": self.core_resources.templates_bucket.bucket_name,
                "OPENSEARCH_ENDPOINT": self.core_resources.opensearch_collection.attr_collection_endpoint,
                "COGNITO_USER_POOL_ID": self.api_resources.user_pool.user_pool_id,
                "COGNITO_CLIENT_ID": self.api_resources.user_pool_client.user_pool_client_id,
                "KMS_KEY_ALIAS": "alias/ai-legal-os",
            },
            log_retention=logs.RetentionDays.ONE_MONTH,
        )
    
    def _create_api_gateway(self) -> None:
        """Create API Gateway REST API."""
        
        # Create Cognito authorizer
        cognito_authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self, "AILegalOSAuthorizer",
            cognito_user_pools=[self.api_resources.user_pool],
            authorizer_name="ai-legal-os-authorizer",
        )
        
        # Create API Gateway
        self.api_resources.api_gateway = apigateway.RestApi(
            self, "AILegalOSApi",
            rest_api_name="ai-legal-os-api",
            description="AI Legal OS REST API",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["*"],
            ),
            deploy_options=apigateway.StageOptions(
                stage_name="v1",
                throttling_rate_limit=1000,
                throttling_burst_limit=2000,
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
            ),
        )
        
        # Create Lambda integration
        lambda_integration = apigateway.LambdaIntegration(
            self.api_resources.lambda_function,
            proxy=True,
        )
        
        # Add proxy resource to handle all paths
        proxy_resource = self.api_resources.api_gateway.root.add_proxy(
            default_integration=lambda_integration,
            default_method_options=apigateway.MethodOptions(
                authorizer=cognito_authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
            ),
        )
        
        # Add health check endpoint without authorization
        health_resource = self.api_resources.api_gateway.root.add_resource("health")
        health_resource.add_method(
            "GET",
            lambda_integration,
            authorization_type=apigateway.AuthorizationType.NONE,
        )
    
    def _create_websocket_api(self) -> None:
        """Create WebSocket API for real-time features."""
        
        # Create WebSocket Lambda integration
        websocket_integration = apigateway.LambdaWebSocketIntegration(
            "WebSocketIntegration",
            self.api_resources.lambda_function,
        )
        
        # Create WebSocket API
        self.api_resources.websocket_api = apigateway.WebSocketApi(
            self, "AILegalOSWebSocketApi",
            api_name="ai-legal-os-websocket",
            description="AI Legal OS WebSocket API for real-time collaboration",
            connect_route_options=apigateway.WebSocketRouteOptions(
                integration=websocket_integration,
            ),
            disconnect_route_options=apigateway.WebSocketRouteOptions(
                integration=websocket_integration,
            ),
            default_route_options=apigateway.WebSocketRouteOptions(
                integration=websocket_integration,
            ),
        )
        
        # Create WebSocket stage
        websocket_stage = apigateway.WebSocketStage(
            self, "AILegalOSWebSocketStage",
            web_socket_api=self.api_resources.websocket_api,
            stage_name="v1",
            auto_deploy=True,
        )
        
        # Grant Lambda permission to manage WebSocket connections
        self.api_resources.lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "execute-api:ManageConnections",
                ],
                resources=[
                    f"arn:aws:execute-api:{self.region}:{self.account}:"
                    f"{self.api_resources.websocket_api.api_id}/*"
                ],
            )
        )
    
    def _create_outputs(self) -> None:
        """Create CloudFormation outputs."""
        
        cdk.CfnOutput(
            self, "UserPoolId",
            value=self.api_resources.user_pool.user_pool_id,
            description="Cognito User Pool ID"
        )
        
        cdk.CfnOutput(
            self, "UserPoolClientId",
            value=self.api_resources.user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID"
        )
        
        cdk.CfnOutput(
            self, "ApiGatewayUrl",
            value=self.api_resources.api_gateway.url,
            description="API Gateway URL"
        )
        
        cdk.CfnOutput(
            self, "WebSocketApiUrl",
            value=self.api_resources.websocket_api.api_endpoint,
            description="WebSocket API URL"
        )