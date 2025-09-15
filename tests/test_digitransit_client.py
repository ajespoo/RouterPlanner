"""
Tests for Digitransit client
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
import httpx

from src.digitransit_client import DigitransitClient
from src.models import Stop, Route


@pytest.fixture
def client():
    """Test client fixture"""
    return DigitransitClient()


@pytest.fixture
def mock_stops_response():
    """Mock GraphQL response for stops query"""
    return {
        "data": {
            "stops": [
                {
                    "gtfsId": "HSL:1010101",
                    "name": "Aalto Yliopisto",
                    "lat": 60.18456,
                    "lon": 24.82928
                },
                {
                    "gtfsId": "HSL:1010102",
                    "name": "Aalto-yliopiston metroasema",
                    "lat": 60.18445,
                    "lon": 24.82632
                }
            ]
        }
    }


@pytest.fixture
def mock_plan_response():
    """Mock GraphQL response for route planning"""
    return {
        "data": {
            "plan": {
                "itineraries": [
                    {
                        "startTime": 1701410400000,  # 2023-12-01 08:20:00 UTC
                        "endTime": 1701411720000,    # 2023-12-01 08:42:00 UTC
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
                                    "shortName": "550",
                                    "longName": "Bus 550"
                                },
                                "trip": {
                                    "route": {
                                        "shortName": "550"
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
    }


@pytest.mark.asyncio
async def test_find_stops_success(client, mock_stops_response):
    """Test successful stop search"""
    with patch.object(client, '_execute_query', return_value=mock_stops_response):
        stops = await client.find_stops("Aalto")
        
        assert len(stops) == 2
        assert isinstance(stops[0], Stop)
        assert stops[0].name == "Aalto Yliopisto"
        assert stops[0].gtfs_id == "HSL:1010101"
        assert stops[1].name == "Aalto-yliopiston metroasema"


@pytest.mark.asyncio
async def test_find_stops_with_limit(client, mock_stops_response):
    """Test stop search with limit"""
    with patch.object(client, '_execute_query', return_value=mock_stops_response):
        stops = await client.find_stops("Aalto", limit=1)
        
        assert len(stops) == 1
        assert stops[0].name == "Aalto Yliopisto"


@pytest.mark.asyncio
async def test_find_stops_no_results(client):
    """Test stop search with no results"""
    empty_response = {"data": {"stops": []}}
    
    with patch.object(client, '_execute_query', return_value=empty_response):
        stops = await client.find_stops("Nonexistent")
        
        assert len(stops) == 0


@pytest.mark.asyncio
async def test_find_stops_api_error(client):
    """Test stop search when API fails"""
    with patch.object(client, '_execute_query', side_effect=Exception("API Error")):
        stops = await client.find_stops("Aalto")
        
        assert len(stops) == 0


@pytest.mark.asyncio
async def test_plan_route_success(client, mock_stops_response, mock_plan_response):
    """Test successful route planning"""
    with patch.object(client, '_execute_query') as mock_query:
        mock_query.side_effect = [mock_stops_response, mock_stops_response, mock_plan_response]
        
        arrival_time = datetime(2023, 12, 1, 8, 45, 0)
        routes = await client.plan_route("Aalto Yliopisto", "Keilaniemi", arrival_time)
        
        assert len(routes) == 1
        assert isinstance(routes[0], Route)
        assert routes[0].departure_time == "08:20:00"
        assert routes[0].arrival_time == "08:42:00"
        assert routes[0].duration == 1320
        assert len(routes[0].legs) == 1
        assert routes[0].legs[0].mode == "BUS"
        assert routes[0].legs[0].route == "550"


@pytest.mark.asyncio
async def test_plan_route_no_from_stops(client):
    """Test route planning when from stop is not found"""
    empty_response = {"data": {"stops": []}}
    
    with patch.object(client, '_execute_query', return_value=empty_response):
        arrival_time = datetime(2023, 12, 1, 8, 45, 0)
        routes = await client.plan_route("Nonexistent", "Keilaniemi", arrival_time)
        
        assert len(routes) == 0


@pytest.mark.asyncio
async def test_plan_route_no_to_stops(client, mock_stops_response):
    """Test route planning when to stop is not found"""
    empty_response = {"data": {"stops": []}}
    
    with patch.object(client, '_execute_query') as mock_query:
        mock_query.side_effect = [mock_stops_response, empty_response]
        
        arrival_time = datetime(2023, 12, 1, 8, 45, 0)
        routes = await client.plan_route("Aalto Yliopisto", "Nonexistent", arrival_time)
        
        assert len(routes) == 0


@pytest.mark.asyncio
async def test_plan_route_no_itineraries(client, mock_stops_response):
    """Test route planning when no itineraries found"""
    empty_plan_response = {"data": {"plan": {"itineraries": []}}}
    
    with patch.object(client, '_execute_query') as mock_query:
        mock_query.side_effect = [mock_stops_response, mock_stops_response, empty_plan_response]
        
        arrival_time = datetime(2023, 12, 1, 8, 45, 0)
        routes = await client.plan_route("Aalto Yliopisto", "Keilaniemi", arrival_time)
        
        assert len(routes) == 0


@pytest.mark.asyncio
async def test_plan_route_api_error(client, mock_stops_response):
    """Test route planning when API fails"""
    with patch.object(client, '_execute_query') as mock_query:
        mock_query.side_effect = [mock_stops_response, mock_stops_response, Exception("API Error")]
        
        arrival_time = datetime(2023, 12, 1, 8, 45, 0)
        routes = await client.plan_route("Aalto Yliopisto", "Keilaniemi", arrival_time)
        
        assert len(routes) == 0


@pytest.mark.asyncio
async def test_execute_query_success(client):
    """Test successful GraphQL query execution"""
    mock_response = AsyncMock()
    mock_response.json.return_value = {"data": {"test": "success"}}
    mock_response.raise_for_status.return_value = None
    
    with patch.object(client.client, 'post', return_value=mock_response):
        result = await client._execute_query("query { test }")
        
        assert result == {"data": {"test": "success"}}


@pytest.mark.asyncio
async def test_execute_query_graphql_error(client):
    """Test GraphQL query with errors"""
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "errors": [{"message": "GraphQL error"}]
    }
    mock_response.raise_for_status.return_value = None
    
    with patch.object(client.client, 'post', return_value=mock_response):
        with pytest.raises(Exception, match="GraphQL query failed"):
            await client._execute_query("query { test }")


@pytest.mark.asyncio
async def test_execute_query_http_error(client):
    """Test GraphQL query with HTTP error"""
    with patch.object(client.client, 'post', side_effect=httpx.HTTPStatusError(
        "Not Found", request=AsyncMock(), response=AsyncMock(status_code=404, text="Not Found")
    )):
        with pytest.raises(Exception, match="API request failed"):
            await client._execute_query("query { test }")


@pytest.mark.asyncio
async def test_client_context_manager():
    """Test client as async context manager"""
    async with DigitransitClient() as client:
        assert isinstance(client, DigitransitClient)
        assert client.client is not None


@pytest.mark.asyncio
async def test_client_close():
    """Test explicit client close"""
    client = DigitransitClient()
    await client.close()
    # Client should be closed gracefully without errors


def test_parse_itinerary_success(client):
    """Test parsing valid itinerary data"""
    itinerary_data = {
        "startTime": 1701410400000,  # 2023-12-01 08:20:00 UTC
        "endTime": 1701411720000,    # 2023-12-01 08:42:00 UTC
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
    
    route = client._parse_itinerary(itinerary_data)
    
    assert route is not None
    assert route.departure_time == "08:20:00"
    assert route.arrival_time == "08:42:00"
    assert route.duration == 1320
    assert len(route.legs) == 1
    assert route.legs[0].mode == "BUS"
    assert route.legs[0].route == "550"


def test_parse_itinerary_missing_data(client):
    """Test parsing itinerary with missing data"""
    invalid_data = {"invalid": "data"}
    
    route = client._parse_itinerary(invalid_data)
    
    assert route is None


def test_parse_itinerary_without_route_info(client):
    """Test parsing itinerary without route information"""
    itinerary_data = {
        "startTime": 1701410400000,
        "endTime": 1701411720000,
        "duration": 1320,
        "legs": [
            {
                "mode": "WALK",
                "startTime": 1701410400000,
                "endTime": 1701411720000,
                "duration": 1320,
                "from": {"stop": {"name": "Start"}},
                "to": {"stop": {"name": "End"}}
            }
        ]
    }
    
    route = client._parse_itinerary(itinerary_data)
    
    assert route is not None
    assert route.legs[0].mode == "WALK"
    assert route.legs[0].route is None