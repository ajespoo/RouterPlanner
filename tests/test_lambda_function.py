"""
Tests for the Lambda function handler
"""
import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient
from src.lambda_function import app, lambda_handler
from src.models import Route, RouteLeg


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def sample_route():
    """Sample route data for testing"""
    return Route(
        departure_time="08:20:00",
        arrival_time="08:42:00",
        duration=1320,
        legs=[
            RouteLeg(
                mode="BUS",
                route="550",
                from_stop="Aalto Yliopisto",
                to_stop="Keilaniemi",
                departure="08:20:00",
                arrival="08:42:00",
                duration=1320
            )
        ]
    )


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Transport Routing API"
    assert data["status"] == "healthy"


def test_health_endpoint_success(client):
    """Test health endpoint with successful API connection"""
    with patch("src.lambda_function.DigitransitClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.find_stops.return_value = [MagicMock()]
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Transport Routing API"
        assert data["status"] == "healthy"
        assert data["components"]["digitransit_api"] == "healthy"


def test_health_endpoint_api_failure(client):
    """Test health endpoint when API is down"""
    with patch("src.lambda_function.DigitransitClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.find_stops.side_effect = Exception("API Error")
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["components"]["digitransit_api"] == "unhealthy"


def test_routes_endpoint_success(client, sample_route):
    """Test successful route query"""
    with patch("src.lambda_function.DigitransitClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.plan_route.return_value = [sample_route]
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        response = client.get("/routes", params={
            "arrival_time": "20241201084500",
            "start_stop": "Aalto Yliopisto",
            "end_stop": "Keilaniemi"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["routes"]) == 1
        assert data["routes"][0]["departure_time"] == "08:20:00"
        assert data["query"]["from"] == "Aalto Yliopisto"
        assert data["query"]["to"] == "Keilaniemi"


def test_routes_endpoint_no_routes(client):
    """Test route query with no results"""
    with patch("src.lambda_function.DigitransitClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.plan_route.return_value = []
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        response = client.get("/routes", params={
            "arrival_time": "20241201084500",
            "start_stop": "Nonexistent Stop",
            "end_stop": "Another Nonexistent Stop"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["routes"]) == 0
        assert data["query"]["from"] == "Nonexistent Stop"


def test_routes_endpoint_missing_parameters(client):
    """Test route query with missing required parameters"""
    response = client.get("/routes")
    assert response.status_code == 422  # Validation error


def test_routes_endpoint_invalid_time_format(client):
    """Test route query with invalid time format"""
    response = client.get("/routes", params={
        "arrival_time": "invalid-time",
        "start_stop": "Aalto Yliopisto",
        "end_stop": "Keilaniemi"
    })
    
    assert response.status_code == 400
    data = response.json()
    assert "Invalid input" in data["error"]


def test_routes_endpoint_api_error(client):
    """Test route query when API fails"""
    with patch("src.lambda_function.DigitransitClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.plan_route.side_effect = Exception("API Error")
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        response = client.get("/routes", params={
            "arrival_time": "20241201084500",
            "start_stop": "Aalto Yliopisto",
            "end_stop": "Keilaniemi"
        })
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to plan route" in data["error"]


def test_lambda_handler_success():
    """Test Lambda handler with successful API Gateway event"""
    event = {
        "httpMethod": "GET",
        "path": "/",
        "headers": {},
        "queryStringParameters": None,
        "body": None,
        "isBase64Encoded": False
    }
    context = MagicMock()
    
    response = lambda_handler(event, context)
    
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["service"] == "Transport Routing API"


def test_lambda_handler_routes_success(sample_route):
    """Test Lambda handler with routes endpoint"""
    event = {
        "httpMethod": "GET",
        "path": "/routes",
        "headers": {},
        "queryStringParameters": {
            "arrival_time": "20241201084500",
            "start_stop": "Aalto Yliopisto",
            "end_stop": "Keilaniemi"
        },
        "body": None,
        "isBase64Encoded": False
    }
    context = MagicMock()
    
    with patch("src.lambda_function.DigitransitClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.plan_route.return_value = [sample_route]
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body["routes"]) == 1


@pytest.mark.asyncio
async def test_digitransit_client_integration():
    """Integration test with real Digitransit API (optional, for development)"""
    pytest.skip("Skip integration test - enable for development testing")
    
    from src.digitransit_client import DigitransitClient
    
    async with DigitransitClient() as client:
        # Test stop search
        stops = await client.find_stops("Aalto Yliopisto", limit=1)
        assert len(stops) > 0
        assert "Aalto" in stops[0].name
        
        # Test route planning
        arrival_time = datetime(2024, 12, 1, 8, 45, 0)
        routes = await client.plan_route(
            "Aalto Yliopisto",
            "Keilaniemi",
            arrival_time,
            max_routes=3
        )
        assert isinstance(routes, list)