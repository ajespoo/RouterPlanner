"""
CDK Stack for Transport Routing API

PURPOSE: Defines all AWS resources using CDK constructs for infrastructure as code

KEY COMPONENTS:
- AWS Lambda function with proper runtime and environment configuration
- API Gateway with CORS support and stage configuration
- CloudWatch dashboard with custom metrics and alarms
- VPC and security groups for secure networking
- ElastiCache Redis cluster for caching (placeholder)
- Secrets Manager for API key management (placeholder)
- S3 + CloudFront for documentation hosting

**Key Components**:

# Lambda function with proper configuration
lambda_function = _lambda.Function(
    runtime=_lambda.Runtime.PYTHON_3_11,
    timeout=Duration.seconds(30),
    environment={"DIGITRANSIT_API_URL": "...", "SECRETS_ARN": "..."}
)

# API Gateway with CORS
api = apigateway.RestApi(
    default_cors_preflight_options=apigateway.CorsOptions(
        allow_origins=apigateway.Cors.ALL_ORIGINS
    )
)

# CloudWatch Dashboard
dashboard = cloudwatch.Dashboard(
    widgets=[GraphWidget(title="API Requests", left=[route_requests_metric])]
)

# ElastiCache Redis Cluster
redis_cluster = elasticache.CfnCacheCluster(
    cache_node_type="cache.t3.micro",
    engine="redis"
)


CODE STRUCTURE:
1. VPC and networking setup
2. ElastiCache Redis cluster configuration
3. Secrets Manager for API keys
4. S3 bucket and CloudFront distribution for docs
5. Lambda function with environment variables
6. API Gateway with proxy integration
7. CloudWatch dashboard and alarms
8. CloudFormation outputs

WHY USED:
- Infrastructure as Code for reproducible deployments
- Integrated monitoring and logging setup
- Security best practices with VPC and security groups
- Scalable architecture with caching and CDN
- Cost-effective serverless architecture
"""
from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_secretsmanager as secretsmanager,
    aws_elasticache as elasticache,
    aws_ec2 as ec2,
    aws_iam as iam,
    RemovalPolicy,
)
from constructs import Construct


class TransportRoutingStack(Stack):
    """CDK Stack for Transport Routing API"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC for ElastiCache (placeholder)
        vpc = ec2.Vpc(
            self,
            "TransportRoutingVPC",
            max_azs=2,
            nat_gateways=1,
            enable_dns_hostnames=True,
            enable_dns_support=True,
        )

        # Security group for ElastiCache
        cache_security_group = ec2.SecurityGroup(
            self,
            "CacheSecurityGroup",
            vpc=vpc,
            description="Security group for ElastiCache cluster",
            allow_all_outbound=False,
        )

        # ElastiCache subnet group
        cache_subnet_group = elasticache.CfnSubnetGroup(
            self,
            "CacheSubnetGroup",
            description="Subnet group for ElastiCache",
            subnet_ids=[subnet.subnet_id for subnet in vpc.private_subnets],
        )

        # ElastiCache Redis cluster (placeholder)
        redis_cluster = elasticache.CfnCacheCluster(
            self,
            "RedisCluster",
            cache_node_type="cache.t3.micro",
            engine="redis",
            num_cache_nodes=1,
            cache_subnet_group_name=cache_subnet_group.ref,
            vpc_security_group_ids=[cache_security_group.security_group_id],
        )

        # Secrets Manager for API keys (placeholder)
        api_secrets = secretsmanager.Secret(
            self,
            "ApiSecrets",
            description="API keys and secrets for Transport Routing API",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"digitransit_api_key": "placeholder"}',
                generate_string_key="api_key",
                exclude_characters='"@/\\'
            ),
        )

        # S3 bucket for documentation
        docs_bucket = s3.Bucket(
            self,
            "DocsBucket",
            bucket_name=f"transport-routing-docs-{self.account}-{self.region}",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # CloudFront Origin Access Identity
        origin_access_identity = cloudfront.OriginAccessIdentity(
            self,
            "DocsOAI",
            comment="OAI for Transport Routing API documentation",
        )

        # Grant CloudFront access to S3 bucket
        docs_bucket.grant_read(origin_access_identity)

        # CloudFront distribution for documentation
        docs_distribution = cloudfront.Distribution(
            self,
            "DocsDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    docs_bucket,
                    origin_access_identity=origin_access_identity,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
            default_root_object="index.html",
            comment="Transport Routing API Documentation",
        )

        # Custom CloudWatch dashboard
        dashboard = cloudwatch.Dashboard(
            self,
            "TransportRoutingDashboard",
            dashboard_name="TransportRoutingAPI",
        )

        # Lambda function
        lambda_function = _lambda.Function(
            self,
            "TransportRoutingFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("src"),
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "DIGITRANSIT_API_URL": "https://api.digitransit.fi/routing/v1/routers/hsl/index/graphql",
                "LOG_LEVEL": "INFO",
                "SECRETS_ARN": api_secrets.secret_arn,
                "REDIS_ENDPOINT": redis_cluster.attr_redis_endpoint_address,
                "REDIS_PORT": redis_cluster.attr_redis_endpoint_port,
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[cache_security_group],
        )

        # Grant Lambda access to Secrets Manager
        api_secrets.grant_read(lambda_function)

        # Custom metrics for Lambda function
        route_requests_metric = cloudwatch.Metric(
            namespace="TransportRouting/API",
            metric_name="RouteRequests",
            statistic="Sum",
        )

        error_rate_metric = cloudwatch.Metric(
            namespace="TransportRouting/API", 
            metric_name="ErrorRate",
            statistic="Average",
        )

        # CloudWatch alarms
        high_error_rate_alarm = cloudwatch.Alarm(
            self,
            "HighErrorRateAlarm",
            metric=error_rate_metric,
            threshold=5,
            evaluation_periods=2,
            alarm_description="High error rate in Transport Routing API",
        )

        # Add widgets to dashboard
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="API Requests",
                left=[route_requests_metric],
                width=12,
                height=6,
            ),
            cloudwatch.GraphWidget(
                title="Error Rate",
                left=[error_rate_metric],
                width=12,
                height=6,
            ),
            cloudwatch.GraphWidget(
                title="Lambda Duration",
                left=[lambda_function.metric_duration()],
                width=12,
                height=6,
            ),
            cloudwatch.GraphWidget(
                title="Lambda Invocations",
                left=[lambda_function.metric_invocations()],
                width=12,
                height=6,
            ),
        )

        # API Gateway
        api = apigateway.RestApi(
            self,
            "TransportRoutingApi",
            rest_api_name="Transport Routing Service",
            description="REST API for Helsinki transport route planning",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"],
            ),
            deploy_options=apigateway.StageOptions(
                stage_name="prod",
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True,
            ),
        )

        # Lambda integration
        lambda_integration = apigateway.LambdaIntegration(
            lambda_function,
            request_templates={"application/json": '{ "statusCode": "200" }'},
        )

        # Add proxy resource to handle all paths and methods
        api.root.add_proxy(
            default_integration=lambda_integration,
            any_method=True,
        )

        # API Gateway custom metrics
        api_requests_metric = api.metric_requests()
        api_latency_metric = api.metric_latency()
        api_errors_metric = api.metric_client_error()

        # Add API Gateway metrics to dashboard
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="API Gateway Requests",
                left=[api_requests_metric],
                width=8,
                height=6,
            ),
            cloudwatch.GraphWidget(
                title="API Gateway Latency",
                left=[api_latency_metric],
                width=8,
                height=6,
            ),
            cloudwatch.GraphWidget(
                title="API Gateway Errors",
                left=[api_errors_metric],
                width=8,
                height=6,
            ),
        )

        # Output the API URL
        self.add_outputs(
            api_url=api.url,
            docs_distribution_url=f"https://{docs_distribution.distribution_domain_name}",
            dashboard_url=f"https://{self.region}.console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name=TransportRoutingAPI",
            secrets_arn=api_secrets.secret_arn,
        )

    def add_outputs(self, **outputs):
        """Add CloudFormation outputs"""
        from aws_cdk import CfnOutput
        
        for key, value in outputs.items():
            CfnOutput(self, key, value=value)