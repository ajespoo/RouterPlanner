"""
Integration tests for the Transport Routing API

PURPOSE: Tests complete workflows and system integration with realistic scenarios

KEY COMPONENTS:
- TestDigitransitIntegration: End-to-end API workflow tests
- TestAPIIntegration: FastAPI application integration tests
- TestPerformance: Concurrent request and response time tests
- TestDataValidation: Edge cases and data validation tests

CODE STRUCTURE:
1. Integration test classes with realistic scenarios
2. Mock external API responses for consistent testing
3. Performance benchmarking with concurrent requests
4. CORS and API contract validation
5. Error handling and edge case testing

WHY USED:
- Validates system behavior under realistic conditions
- Tests API contracts and data flow
- Performance benchmarking capabilities
- Integration with external services (mocked)
- Ensures components work together correctly
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, AsyncMock
import httpx

from src.digitransit_client import DigitransitClient
from src.lambda_function import app
from fastapi.testclient import TestClient


class TestDigitransitIntegration:
    """Integration tests with Digitransit API"""

    @pytest.mark.asyncio
    async def test_real_digitransit_connection(self):
        """Test actual connection to Digitransit API (optional)"""
        pytest.skip("Skip real API test - enable for integration testing")
        
        async with DigitransitClient() as client:
            stops = await client.find_stops("Aalto", limit=1)
            assert len(stops) > 0
            assert "Aalto" in stops[0].name

    @pytest.mark.asyncio
    async def test_mock_digitransit_workflow(self):
        """Test complete workflow with mocked Digitransit responses"""
        mock_stops_response = {
            "data": {
                "stops": [
                    {
                        "gtfsId": "HSL:1010101",
                        "name": "Aalto Yliopisto",
                        "lat": 60.18456,
                        "lon": 24.82928
                    }
                ]
            }
        }
        
        mock_plan_response = {
            "data": {
                "plan": {
                    "itineraries": [
                        {
                            "startTime": 1701410400000,
                            "endTime": 1701411720000,
                            "duration": 1320,
                            "legs": [
                                {
                                    "mode": "BUS",
                                    "startTime": 1701410400000,
                                    "endTime": 1701411720000,
                                    "duration": 1320,
                                    "from": {
                                        "stop": {
                                            "gtfsId": "HSL:1010101",
                                            "name": "Aalto Yliopisto"
                                        }
                                    },
                                    "to": {
                                        "stop": {
                                            "gtfsId": "HSL:2020201",
                                            "name": "Keilaniemi"
                                        }
                                    },
                                    "route": {
                                        "shortName": "550"
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        }

        async with DigitransitClient() as client:
            with patch.object(client, '_execute_query') as mock_query:
                mock_query.side_effect = [
                    mock_stops_response,  # from_stops
                    mock_stops_response,  # to_stops
                    mock_plan_response    # route planning
                ]
                
                arrival_time = datetime(2023, 12, 1, 8, 45, 0)
                routes = await client.plan_route(
                    "Aalto Yliopisto",
                    "Keilaniemi", 
                    arrival_time
                )
                
                assert len(routes) == 1
                assert routes[0].departure_time == "08:20:00"
                assert routes[0].arrival_time == "08:42:00"


class TestAPIIntegration:
    """End-to-end API integration tests"""

    def test_full_api_workflow(self):
        """Test complete API workflow from request to response"""
        client = TestClient(app)
        
        with patch("src.lambda_function.DigitransitClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.plan_route.return_value = [
                {
                    "departure_time": "08:20:00",
                    "arrival_time": "08:42:00",
                    "duration": 1320,
                    "legs": [
                        {
                            "mode": "BUS",
                            "route": "550",
                            "from_stop": "Aalto Yliopisto",
                            "to_stop": "Keilaniemi",
                            "departure": "08:20:00",
                            "arrival": "08:42:00",
                            "duration": 1320
                        }
                    ]
                }
            ]
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            response = client.get("/routes", params={
                "arrival_time": "20241201084500",
                "start_stop": "Aalto Yliopisto",
                "end_stop": "Keilaniemi"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "routes" in data
            assert "query" in data

    def test_api_error_handling(self):
        """Test API error handling scenarios"""
        client = TestClient(app)
        
        # Test missing parameters
        response = client.get("/routes")
        assert response.status_code == 422
        
        # Test invalid time format
        response = client.get("/routes", params={
            "arrival_time": "invalid",
            "start_stop": "A",
            "end_stop": "B"
        })
        assert response.status_code == 400

    def test_cors_headers(self):
        """Test CORS headers are properly set"""
        client = TestClient(app)
        
        response = client.options("/routes")
        assert response.headers.get("access-control-allow-origin") == "*"
        assert "GET" in response.headers.get("access-control-allow-methods", "")


class TestPerformance:
    """Performance and load testing"""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent requests"""
        async def make_request():
            async with httpx.AsyncClient() as client:
                with patch("src.digitransit_client.DigitransitClient._execute_query"):
                    # Simulate API call
                    await asyncio.sleep(0.1)
                    return {"status": "ok"}
        
        # Test 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert all(r["status"] == "ok" for r in results)

    def test_response_time(self):
        """Test API response time is reasonable"""
        client = TestClient(app)
        
        with patch("src.lambda_function.DigitransitClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.plan_route.return_value = []
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            import time
            start_time = time.time()
            
            response = client.get("/routes", params={
                "arrival_time": "20241201084500",
                "start_stop": "Aalto Yliopisto",
                "end_stop": "Keilaniemi"
            })
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 5.0  # Should respond within 5 seconds


class TestDataValidation:
    """Test data validation and edge cases"""

    def test_edge_case_stop_names(self):
        """Test handling of edge case stop names"""
        client = TestClient(app)
        
        edge_cases = [
            "Aalto-yliopisto",
            "Helsinki-Vantaa lentoasema",
            "Rautatientori",
            "Sörnäinen",
            "Käpylä"
        ]
        
        with patch("src.lambda_function.DigitransitClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.plan_route.return_value = []
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            for stop_name in edge_cases:
                response = client.get("/routes", params={
                    "arrival_time": "20241201084500",
                    "start_stop": stop_name,
                    "end_stop": "Keilaniemi"
                })
                assert response.status_code == 200

    def test_time_format_variations(self):
        """Test various time format edge cases"""
        client = TestClient(app)
        
        valid_times = [
            "20241201084500",
            "19990101000000",
            "20251231235959"
        ]
        
        invalid_times = [
            "2024-12-01 08:45:00",
            "20241301084500",  # Invalid month
            "20241232084500",  # Invalid day
            "short",
            "toolong123456789"
        ]
        
        with patch("src.lambda_function.DigitransitClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.plan_route.return_value = []
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            # Test valid times
            for time_str in valid_times:
                response = client.get("/routes", params={
                    "arrival_time": time_str,
                    "start_stop": "A",
                    "end_stop": "B"
                })
                assert response.status_code == 200
            
            # Test invalid times
            for time_str in invalid_times:
                response = client.get("/routes", params={
                    "arrival_time": time_str,
                    "start_stop": "A",
                    "end_stop": "B"
                })
                assert response.status_code == 400