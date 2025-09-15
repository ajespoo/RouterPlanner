"""
AWS Lambda handler for Transport Routing REST API

PURPOSE: Main FastAPI application that serves as the AWS Lambda entry point

#**Key Components**:

# FastAPI app with CORS middleware

#app = FastAPI(title="Transport Routing API", version="1.0.0")
#app.add_middleware(CORSMiddleware, allow_origins=["*"])

KEY COMPONENTS:
- FastAPI app with CORS middleware for cross-origin requests
- AWS PowerTools integration for observability (logging, tracing, metrics)
- Pydantic model validation for request/response data
- Async integration with Digitransit GraphQL API
- Comprehensive error handling with custom exception handlers
- Health check endpoints for monitoring

CODE STRUCTURE:
1. FastAPI app initialization with middleware
2. Environment variable configuration
3. Custom exception handlers for HTTP and general errors
4. Route endpoints (/routes, /health, /metrics)
5. Lambda handler with Mangum adapter

WHY USED:
- FastAPI provides automatic OpenAPI documentation and validation
- Mangum adapter enables seamless Lambda deployment
- AWS PowerTools provides production-ready observability
- Async support handles external API calls efficiently
- CORS middleware enables frontend integration
"""
import json
import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit

from .models import RouteQuery, RouteResponse, ErrorResponse
from .digitransit_client import DigitransitClient

# Initialize AWS PowerTools
logger = Logger()
tracer = Tracer()
metrics = Metrics()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI(
    title="Transport Routing API",
    description="REST API for Helsinki transport route planning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
DIGITRANSIT_API_URL = os.getenv(
    "DIGITRANSIT_API_URL",
    "https://api.digitransit.fi/routing/v1/routers/hsl/index/graphql"
)
SECRETS_ARN = os.getenv("SECRETS_ARN")
REDIS_ENDPOINT = os.getenv("REDIS_ENDPOINT")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
    
    # Add custom metric for HTTP errors
    metrics.add_metric(name="HTTPErrors", unit=MetricUnit.Count, value=1)
    metrics.add_metadata(key="error_code", value=str(exc.status_code))
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            details=f"HTTP {exc.status_code}"
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    # Add custom metric for unhandled exceptions
    metrics.add_metric(name="UnhandledExceptions", unit=MetricUnit.Count, value=1)
    metrics.add_metadata(key="exception_type", value=type(exc).__name__)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            details="An unexpected error occurred"
        ).dict()
    )


@app.get("/", response_model=dict)
@tracer.capture_method
async def root():
    """Health check endpoint"""
    metrics.add_metric(name="HealthChecks", unit=MetricUnit.Count, value=1)
    return {
        "service": "Transport Routing API",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health", response_model=dict)
@tracer.capture_method
async def health_check():
    """Detailed health check"""
    metrics.add_metric(name="DetailedHealthChecks", unit=MetricUnit.Count, value=1)
    
    try:
        async with DigitransitClient(DIGITRANSIT_API_URL) as client:
            # Test API connectivity
            stops = await client.find_stops("Aalto", limit=1)
            api_status = "healthy" if stops else "degraded"
            
        # Test Redis connectivity (placeholder)
        redis_status = "healthy"  # Placeholder - would test actual Redis connection
        
        # Test Secrets Manager access (placeholder)
        secrets_status = "healthy"  # Placeholder - would test actual secrets access
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        api_status = "unhealthy"
        redis_status = "unknown"
        secrets_status = "unknown"

    return {
        "service": "Transport Routing API",
        "status": "healthy",
        "components": {
            "digitransit_api": api_status,
            "redis_cache": redis_status,
            "secrets_manager": secrets_status,
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/routes", response_model=RouteResponse)
@tracer.capture_method
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
async def get_routes(
    arrival_time: str = Query(
        ...,
        description="Target arrival time in yyyyMMddHHmmss format",
        example="20241201084500"
    ),
    start_stop: str = Query(
        ...,
        description="Name of the departure stop",
        example="Aalto Yliopisto"
    ),
    end_stop: str = Query(
        ...,
        description="Name of the destination stop",
        example="Keilaniemi"
    ),
):
    """
    Get transport routes between two stops with arrival time constraint.
    
    This endpoint helps users plan their journey by finding the best routes
    that arrive at the destination by the specified time.
    """
    
    # Add custom metrics
    metrics.add_metric(name="RouteRequests", unit=MetricUnit.Count, value=1)
    metrics.add_metadata(key="start_stop", value=start_stop)
    metrics.add_metadata(key="end_stop", value=end_stop)
    
    # Start timing for performance metrics
    import time
    start_time = time.time()
    
    # Validate input using Pydantic model
    try:
        query = RouteQuery(
            arrival_time=arrival_time,
            start_stop=start_stop,
            end_stop=end_stop
        )
    except Exception as e:
        logger.error(f"Input validation failed: {e}")
        metrics.add_metric(name="ValidationErrors", unit=MetricUnit.Count, value=1)
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")

    logger.info(f"Processing route request from {start_stop} to {end_stop} at {arrival_time}")

    try:
        # Parse arrival time
        target_time = datetime.strptime(arrival_time, '%Y%m%d%H%M%S')
        
        # TODO: Check Redis cache for existing results
        # cache_key = f"route:{start_stop}:{end_stop}:{arrival_time}"
        # cached_result = await get_from_cache(cache_key)
        # if cached_result:
        #     metrics.add_metric(name="CacheHits", unit=MetricUnit.Count, value=1)
        #     return cached_result
        
        # Create Digitransit client and plan route
        async with DigitransitClient(DIGITRANSIT_API_URL) as client:
            routes = await client.plan_route(
                from_stop=start_stop,
                to_stop=end_stop,
                arrival_time=target_time,
                max_routes=5
            )

        if not routes:
            logger.warning(f"No routes found for query: {query.dict()}")
            metrics.add_metric(name="NoRoutesFound", unit=MetricUnit.Count, value=1)
            
            # Still return a valid response with empty routes
            response = RouteResponse(
                routes=[],
                query={
                    "from": start_stop,
                    "to": end_stop,
                    "arrival_time": arrival_time
                }
            )
        else:
            logger.info(f"Found {len(routes)} routes")
            metrics.add_metric(name="SuccessfulRequests", unit=MetricUnit.Count, value=1)
            metrics.add_metric(name="RoutesFound", unit=MetricUnit.Count, value=len(routes))

            response = RouteResponse(
                routes=routes,
                query={
                    "from": start_stop,
                    "to": end_stop,
                    "arrival_time": arrival_time
                }
            )

        # Record response time
        response_time = time.time() - start_time
        metrics.add_metric(name="ResponseTime", unit=MetricUnit.Seconds, value=response_time)
        
        # TODO: Cache the result in Redis
        # await cache_result(cache_key, response, ttl=300)  # 5 minutes TTL

        return response

    except ValueError as e:
        logger.error(f"Date parsing error: {e}")
        metrics.add_metric(name="DateParsingErrors", unit=MetricUnit.Count, value=1)
        raise HTTPException(
            status_code=400,
            detail="Invalid arrival_time format. Use yyyyMMddHHmmss format."
        )
    except Exception as e:
        logger.error(f"Route planning error: {e}", exc_info=True)
        metrics.add_metric(name="PlanningErrors", unit=MetricUnit.Count, value=1)
        raise HTTPException(
            status_code=500,
            detail="Failed to plan route. Please try again later."
        )


@app.get("/metrics", response_model=dict)
@tracer.capture_method
async def get_metrics():
    """Get API metrics and statistics"""
    # This would return cached metrics from CloudWatch or Redis
    # For now, return placeholder data
    return {
        "total_requests": 0,
        "successful_requests": 0,
        "error_rate": 0.0,
        "average_response_time": 0.0,
        "cache_hit_rate": 0.0,
        "timestamp": datetime.utcnow().isoformat()
    }


# Create Lambda handler
handler = Mangum(app, lifespan="off")


def lambda_handler(event, context):
    """AWS Lambda entry point"""
    logger.info("Processing Lambda request", extra={
        "event": json.dumps(event, default=str)
    })
    
    # Add Lambda-specific metrics
    metrics.add_metric(name="LambdaInvocations", unit=MetricUnit.Count, value=1)
    
    try:
        return handler(event, context)
    except Exception as e:
        logger.error(f"Lambda handler error: {e}", exc_info=True)
        metrics.add_metric(name="LambdaErrors", unit=MetricUnit.Count, value=1)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error",
                "details": str(e)
            }),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            }
        }