#!/usr/bin/env python3
"""
CDK App entry point for Transport Routing API

PURPOSE: Main CDK application that defines the deployment configuration

KEY COMPONENTS:
- CDK App instantiation
- Stack creation with environment configuration
- CloudFormation template synthesis

CODE STRUCTURE:
1. Import CDK core and stack modules
2. Create CDK App instance
3. Instantiate TransportRoutingStack with environment config
4. Synthesize CloudFormation templates

WHY USED:
- Single entry point for CDK deployment
- Environment configuration management (account, region)
- Enables infrastructure as code deployment
- Integrates with CDK CLI commands (cdk deploy, cdk synth)
"""
import aws_cdk as cdk
from transport_routing.transport_routing_stack import TransportRoutingStack

app = cdk.App()

TransportRoutingStack(
    app,
    "TransportRoutingStack",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "eu-west-1",
    ),
    description="REST API for Helsinki transport route planning"
)

app.synth()