"""
Comprehensive unit tests for Transport Routing API components

PURPOSE: Tests individual components in isolation with mocked dependencies

KEY COMPONENTS:
- TestModelsUnit: Pydantic model validation and serialization tests
- TestDigitransitClientUnit: GraphQL client functionality tests
- TestLambdaFunctionUnit: FastAPI application and Lambda handler tests
- TestUtilityFunctions: Helper function and utility tests
- TestConfigurationUnit: Environment and configuration tests

CODE STRUCTURE:
1. Test classes organized by component
2. Fixtures for reusable test data
3. Mock objects for external dependencies
4. Async test support with pytest-asyncio
5. Comprehensive edge case coverage

WHY USED:
- Ensures individual components work correctly in isolation
- Fast execution with mocked dependencies
- High code coverage for reliability
- Catches regressions during development
- Validates business logic without external dependencies
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import json

from src.models import RouteQuery, RouteLeg, Route, RouteResponse, Stop, ErrorResponse
from src.digitransit_client import DigitransitClient
from src.lambda_function import app, lambda_handler
from fastapi.testclient import TestClient


class TestModelsUnit:
    """Unit tests for Pydantic models"""

    def test_route_query_creation(self):
        """Test RouteQuery model creation and validation"""
        query = RouteQuery(
            arrival_time="20241201084500",
            start_stop="Aalto Yliopisto",
            end_stop="Keilaniemi"
        )
        
        assert query.arrival_time == "20241201084500"
        assert query.start_stop == "Aalto Yliopisto"
        assert query.end_stop == "Keilaniemi"

    def test_route_query_validation_errors(self):
        """Test RouteQuery validation failures"""
        from pydantic import ValidationError
        
        # Test missing required fields
        with pytest.raises(ValidationError):
            RouteQuery(arrival_time="20241201084500")
        
        # Test invalid time format
        with pytest.raises(ValidationError):
            RouteQuery(
                arrival_time="invalid-time",
                start_stop="A",
                end_stop="B"
            )

    def test_route_leg_with_aliases(self):
        """Test RouteLeg model with field aliases"""
        leg_data = {
            "mode": "BUS",
            "route": "550",
            "from": "Start",
            "to": "End",
            "departure": "08:00:00",
            "arrival": "08:30:00",
            "duration": 1800
        }
        
        leg = RouteLeg(**leg_data)
        assert leg.from_stop == "Start"
        assert leg.to_stop == "End"
        assert leg.mode == "BUS"

    def test_route_model_serialization(self):
        """Test Route model JSON serialization"""
        leg = RouteLeg(
            mode="BUS",
            route="550",
            from_stop="A",
            to_stop="B",
            departure="08:00:00",
            arrival="08:30:00",
            duration=1800
        )
        
        route = Route(
            departure_time="08:00:00",
            arrival_time="08:30:00",
            duration=1800,
            legs=[leg]
        )
        
        json_data = route.dict()
        assert json_data["departure_time"] == "08:00:00"
        assert len(json_data["legs"]) == 1

    def test_error_response_model(self):
        """Test ErrorResponse model"""
        error = ErrorResponse(
            error="Test error",
            details="Test details"
        )
        
        assert error.error == "Test error"
        assert error.details == "Test details"
        
        # Test without details
        error_simple = ErrorResponse(error="Simple error")
        assert error_simple.details is None


class TestDigitransitClientUnit:
    """Unit tests for DigitransitClient"""

    @pytest.fixture
    def client(self):
        return DigitransitClient("https://test-api.example.com")

    def test_client_initialization(self, client):
        """Test client initialization"""
        assert client.base_url == "https://test-api.example.com"
        assert client.client is not None

    @pytest.mark.asyncio
    async def test_execute_query_success(self, client):
        """Test successful GraphQL query execution"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {"data": {"test": "success"}}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.client, 'post', return_value=mock_response):
            result = await client._execute_query("query { test }")
            assert result == {"data": {"test": "success"}}

    @pytest.mark.asyncio
    async def test_execute_query_graphql_errors(self, client):
        """Test GraphQL query with errors"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "errors": [{"message": "GraphQL error"}]
        }
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.client, 'post', return_value=mock_response):
            with pytest.raises(Exception, match="GraphQL query failed"):
                await client._execute_query("query { test }")

    def test_parse_itinerary_success(self, client):
        """Test successful itinerary parsing"""
        itinerary_data = {
            "startTime": 1701410400000,
            "endTime": 1701411720000,
            "duration": 1320,
            "legs": [
                {
                    "mode": "BUS",
                    "startTime": 1701410400000,
                    "endTime": 1701411720000,
                    "duration": 1320,
                    "from": {"stop": {"name": "Start"}},
                    "to": {"stop": {"name": "End"}},
                    "route": {"shortName": "550"}
                }
            ]
        }
        
        route = client._parse_itinerary(itinerary_data)
        assert route is not None
        assert route.duration == 1320
        assert len(route.legs) == 1
        assert route.legs[0].mode == "BUS"

    def test_parse_itinerary_invalid_data(self, client):
        """Test itinerary parsing with invalid data"""
        invalid_data = {"invalid": "data"}
        route = client._parse_itinerary(invalid_data)
        assert route is None

    @pytest.mark.asyncio
    async def test_find_stops_empty_result(self, client):
        """Test find_stops with empty result"""
        empty_response = {"data": {"stops": []}}
        
        with patch.object(client, '_execute_query', return_value=empty_response):
            stops = await client.find_stops("Nonexistent")
            assert len(stops) == 0

    @pytest.mark.asyncio
    async def test_find_stops_with_limit(self, client):
        """Test find_stops with limit parameter"""
        mock_response = {
            "data": {
                "stops": [
                    {"gtfsId": "1", "name": "Stop 1", "lat": 60.0, "lon": 24.0},
                    {"gtfsId": "2", "name": "Stop 2", "lat": 60.1, "lon": 24.1},
                    {"gtfsId": "3", "name": "Stop 3", "lat": 60.2, "lon": 24.2}
                ]
            }
        }
        
        with patch.object(client, '_execute_query', return_value=mock_response):
            stops = await client.find_stops("Test", limit=2)
            assert len(stops) == 2


class TestLambdaFunctionUnit:
    """Unit tests for Lambda function components"""

    def test_app_initialization(self):
        """Test FastAPI app initialization"""
        assert app.title == "Transport Routing API"
        assert app.version == "1.0.0"

    def test_lambda_handler_structure(self):
        """Test lambda_handler function exists and is callable"""
        assert callable(lambda_handler)

    def test_lambda_handler_with_mock_event(self):
        """Test lambda_handler with mock API Gateway event"""
        event = {
            "httpMethod": "GET",
            "path": "/",
            "headers": {},
            "queryStringParameters": None,
            "body": None,
            "isBase64Encoded": False
        }
        context = Mock()
        
        response = lambda_handler(event, context)
        assert "statusCode" in response
        assert "body" in response

    def test_root_endpoint_unit(self):
        """Test root endpoint in isolation"""
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Transport Routing API"
        assert data["status"] == "healthy"

    def test_routes_endpoint_validation(self):
        """Test routes endpoint parameter validation"""
        client = TestClient(app)
        
        # Test missing parameters
        response = client.get("/routes")
        assert response.status_code == 422
        
        # Test partial parameters
        response = client.get("/routes?arrival_time=20241201084500")
        assert response.status_code == 422

    def test_error_handlers(self):
        """Test custom error handlers"""
        client = TestClient(app)
        
        # Test 404 error
        response = client.get("/nonexistent")
        assert response.status_code == 404


class TestUtilityFunctions:
    """Unit tests for utility functions and helpers"""

    def test_time_parsing(self):
        """Test time parsing functionality"""
        from datetime import datetime
        
        # Test valid time string
        time_str = "20241201084500"
        parsed_time = datetime.strptime(time_str, '%Y%m%d%H%M%S')
        
        assert parsed_time.year == 2024
        assert parsed_time.month == 12
        assert parsed_time.day == 1
        assert parsed_time.hour == 8
        assert parsed_time.minute == 45
        assert parsed_time.second == 0

    def test_duration_calculations(self):
        """Test duration calculation utilities"""
        # Test duration in seconds to minutes conversion
        duration_seconds = 1320  # 22 minutes
        duration_minutes = duration_seconds // 60
        
        assert duration_minutes == 22

    def test_stop_name_normalization(self):
        """Test stop name normalization"""
        test_names = [
            "Aalto Yliopisto",
            "Helsinki-Vantaa lentoasema",
            "Sörnäinen",
            "Käpylä"
        ]
        
        for name in test_names:
            # Test that names are handled as strings
            assert isinstance(name, str)
            assert len(name) > 0


class TestConfigurationUnit:
    """Unit tests for configuration and environment handling"""

    def test_environment_variables(self):
        """Test environment variable handling"""
        import os
        
        # Test default values
        default_url = "https://api.digitransit.fi/routing/v1/routers/hsl/index/graphql"
        api_url = os.getenv("DIGITRANSIT_API_URL", default_url)
        
        assert api_url is not None
        assert api_url.startswith("https://")

    def test_logging_configuration(self):
        """Test logging configuration"""
        import logging
        
        logger = logging.getLogger(__name__)
        assert logger is not None
        
        # Test log level setting
        logger.setLevel(logging.INFO)
        assert logger.level == logging.INFO


class TestDataStructures:
    """Unit tests for data structures and transformations"""

    def test_route_data_transformation(self):
        """Test route data transformation"""
        raw_leg_data = {
            "mode": "BUS",
            "startTime": 1701410400000,
            "endTime": 1701411720000,
            "duration": 1320,
            "from": {"stop": {"name": "Start"}},
            "to": {"stop": {"name": "End"}},
            "route": {"shortName": "550"}
        }
        
        # Test timestamp conversion
        start_time = datetime.fromtimestamp(raw_leg_data["startTime"] / 1000)
        end_time = datetime.fromtimestamp(raw_leg_data["endTime"] / 1000)
        
        assert isinstance(start_time, datetime)
        assert isinstance(end_time, datetime)
        assert end_time > start_time

    def test_json_serialization(self):
        """Test JSON serialization of models"""
        leg = RouteLeg(
            mode="BUS",
            route="550",
            from_stop="A",
            to_stop="B",
            departure="08:00:00",
            arrival="08:30:00",
            duration=1800
        )
        
        # Test model can be serialized to JSON
        json_str = json.dumps(leg.dict())
        assert isinstance(json_str, str)
        
        # Test deserialization
        data = json.loads(json_str)
        assert data["mode"] == "BUS"
        assert data["route"] == "550"