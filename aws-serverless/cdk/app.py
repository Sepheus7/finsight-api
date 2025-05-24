#!/usr/bin/env python3
"""
AWS CDK Stack for Financial AI Quality Enhancement API
Alternative to SAM template for those who prefer CDK
"""

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_logs as logs,
    aws_iam as iam,
)
from constructs import Construct
import os

class FinancialAIQualityApiStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Parameters
        stage = self.node.try_get_context("stage") or "dev"

        # DynamoDB Tables
        enhancement_history_table = dynamodb.Table(
            self, "EnhancementHistoryTable",
            table_name=f"{construct_id}-enhancement-history",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", 
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.DESTROY  # Use RETAIN for production
        )

        compliance_rules_table = dynamodb.Table(
            self, "ComplianceRulesTable",
            table_name=f"{construct_id}-compliance-rules",
            partition_key=dynamodb.Attribute(
                name="rule_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY  # Use RETAIN for production
        )

        # S3 Bucket for data caching
        data_cache_bucket = s3.Bucket(
            self, "DataCacheBucket",
            bucket_name=f"{construct_id}-data-cache-{self.account}",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldCacheData",
                    enabled=True,
                    expiration=Duration.days(7)
                )
            ],
            removal_policy=RemovalPolicy.DESTROY  # Use RETAIN for production
        )

        # Lambda Layer for shared dependencies
        lambda_layer = _lambda.LayerVersion(
            self, "FinAILayer",
            code=_lambda.Code.from_asset("lambda-layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
            description="Shared dependencies for Financial AI Quality API"
        )

        # Common Lambda function configuration
        lambda_environment = {
            "DYNAMODB_TABLE": enhancement_history_table.table_name,
            "COMPLIANCE_RULES_TABLE": compliance_rules_table.table_name,
            "S3_BUCKET": data_cache_bucket.bucket_name,
        }

        lambda_common_props = {
            "runtime": _lambda.Runtime.PYTHON_3_11,
            "timeout": Duration.seconds(30),
            "memory_size": 512,
            "environment": lambda_environment,
            "layers": [lambda_layer],
            "tracing": _lambda.Tracing.ACTIVE,
        }

        # Lambda Functions
        
        # Main Enhancement Function
        enhance_function = _lambda.Function(
            self, "EnhanceResponseFunction",
            code=_lambda.Code.from_asset("src"),
            handler="enhance_handler.lambda_handler",
            description="Main endpoint to enhance AI responses",
            **lambda_common_props
        )

        # Fact Check Function
        fact_check_function = _lambda.Function(
            self, "FactCheckFunction", 
            code=_lambda.Code.from_asset("src"),
            handler="fact_check_handler.lambda_handler",
            description="Verify financial claims and statements",
            timeout=Duration.seconds(60),
            **{k: v for k, v in lambda_common_props.items() if k != 'timeout'}
        )

        # Context Enrichment Function
        context_enrichment_function = _lambda.Function(
            self, "ContextEnrichmentFunction",
            code=_lambda.Code.from_asset("src"),
            handler="context_enrichment_handler.lambda_handler", 
            description="Add relevant financial context to responses",
            **lambda_common_props
        )

        # Compliance Check Function
        compliance_check_function = _lambda.Function(
            self, "ComplianceCheckFunction",
            code=_lambda.Code.from_asset("src"),
            handler="compliance_handler.lambda_handler",
            description="Check for regulatory compliance issues",
            **lambda_common_props
        )

        # Health Check Function
        health_check_function = _lambda.Function(
            self, "HealthCheckFunction",
            code=_lambda.Code.from_asset("src"),
            handler="health_handler.lambda_handler",
            description="API health check endpoint",
            **lambda_common_props
        )

        # Root Function
        root_function = _lambda.Function(
            self, "RootFunction",
            code=_lambda.Code.from_asset("src"),
            handler="root_handler.lambda_handler",
            description="API information endpoint",
            **lambda_common_props
        )

        # Add environment variables for function references
        enhance_function.add_environment("FACT_CHECK_FUNCTION", fact_check_function.function_name)
        enhance_function.add_environment("CONTEXT_ENRICHMENT_FUNCTION", context_enrichment_function.function_name)
        enhance_function.add_environment("COMPLIANCE_CHECK_FUNCTION", compliance_check_function.function_name)

        # IAM Permissions
        
        # DynamoDB permissions
        enhancement_history_table.grant_read_write_data(enhance_function)
        compliance_rules_table.grant_read_data(compliance_check_function)

        # S3 permissions
        data_cache_bucket.grant_read_write(fact_check_function)
        data_cache_bucket.grant_read(context_enrichment_function)

        # Lambda invoke permissions
        fact_check_function.grant_invoke(enhance_function)
        context_enrichment_function.grant_invoke(enhance_function)
        compliance_check_function.grant_invoke(enhance_function)

        # CloudWatch Logs
        for func in [enhance_function, fact_check_function, context_enrichment_function, 
                    compliance_check_function, health_check_function, root_function]:
            logs.LogGroup(
                self, f"{func.function_name}LogGroup",
                log_group_name=f"/aws/lambda/{func.function_name}",
                retention=logs.RetentionDays.ONE_MONTH,
                removal_policy=RemovalPolicy.DESTROY
            )

        # API Gateway
        api = apigateway.RestApi(
            self, "FinancialAIApi",
            rest_api_name="Financial AI Quality Enhancement API",
            description="Serverless API for enhancing AI-generated financial content",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Amz-Security-Token"]
            ),
            deploy_options=apigateway.StageOptions(
                stage_name=stage,
                tracing_enabled=True,
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True
            )
        )

        # API Gateway Integrations
        enhance_integration = apigateway.LambdaIntegration(enhance_function)
        health_integration = apigateway.LambdaIntegration(health_check_function)
        root_integration = apigateway.LambdaIntegration(root_function)

        # API Routes
        api.root.add_method("GET", root_integration)
        
        enhance_resource = api.root.add_resource("enhance")
        enhance_resource.add_method("POST", enhance_integration)
        
        health_resource = api.root.add_resource("health")
        health_resource.add_method("GET", health_integration)

        # API Gateway CloudWatch Role
        api_gateway_role = iam.Role(
            self, "ApiGatewayCloudWatchRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonAPIGatewayPushToCloudWatchLogs")
            ]
        )

        # Outputs
        cdk.CfnOutput(
            self, "ApiUrl",
            value=api.url,
            description="API Gateway endpoint URL",
            export_name=f"{construct_id}-ApiUrl"
        )

        cdk.CfnOutput(
            self, "EnhancementHistoryTableName",
            value=enhancement_history_table.table_name,
            description="DynamoDB table name for enhancement history",
            export_name=f"{construct_id}-HistoryTable"
        )

        cdk.CfnOutput(
            self, "DataCacheBucketName", 
            value=data_cache_bucket.bucket_name,
            description="S3 bucket name for data caching",
            export_name=f"{construct_id}-CacheBucket"
        )

        cdk.CfnOutput(
            self, "ComplianceRulesTableName",
            value=compliance_rules_table.table_name,
            description="DynamoDB table name for compliance rules",
            export_name=f"{construct_id}-ComplianceRulesTable"
        )


app = cdk.App()
FinancialAIQualityApiStack(
    app, 
    "FinancialAIQualityApiStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION', 'us-east-1')
    )
)

app.synth()
