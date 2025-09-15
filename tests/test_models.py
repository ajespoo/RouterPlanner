"""
Tests for data models
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models import RouteQuery, RouteLeg, Route, RouteResponse, Stop, ErrorResponse


def test_route_query_valid():
    """Test valid route query creation"""
    query = RouteQuery(
        arrival_time="20241201084500",
        start_stop="Aalto Yliopisto",
        end_stop="Keilaniemi"
    )
    
    assert query.arrival_time == "20241201084500"
    assert query.start_stop == "Aalto Yliopisto"
    assert query.end_stop == "Keilaniemi"


def test_route_query_invalid_time():
    """Test route query with invalid time format"""
    with pytest.raises(ValidationError):
        RouteQuery(
            arrival_time="invalid-time",
            start_stop="Aalto Yliopisto",
            end_stop="Keilaniemi"
        )


def test_route_leg_creation():
    """Test route leg model creation"""
    leg = RouteLeg(
        mode="BUS",
        route="550",
        from_stop="Aalto Yliopisto",
        to_stop="Keilaniemi",
        departure="08:20:00",
        arrival="08:42:00",
        duration=1320
    )
    
    assert leg.mode == "BUS"
    assert leg.route == "550"
    assert leg.from_stop == "Aalto Yliopisto"
    assert leg.to_stop == "Keilaniemi"
    assert leg.duration == 1320


def test_route_leg_with_alias():
    """Test route leg creation using field aliases"""
    leg_data = {
        "mode": "BUS",
        "route": "550",
        "from": "Aalto Yliopisto",  # Using alias
        "to": "Keilaniemi",        # Using alias
        "departure": "08:20:00",
        "arrival": "08:42:00",
        "duration": 1320
    }
    
    leg = RouteLeg(**leg_data)
    assert leg.from_stop == "Aalto Yliopisto"
    assert leg.to_stop == "Keilaniemi"


def test_route_creation():
    """Test complete route creation"""
    legs = [
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
    
    route = Route(
        departure_time="08:20:00",
        arrival_time="08:42:00",
        duration=1320,
        legs=legs
    )
    
    assert route.departure_time == "08:20:00"
    assert route.arrival_time == "08:42:00"
    assert route.duration == 1320
    assert len(route.legs) == 1


def test_route_response():
    """Test route response model"""
    legs = [
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
    
    routes = [
        Route(
            departure_time="08:20:00",
            arrival_time="08:42:00",
            duration=1320,
            legs=legs
        )
    ]
    
    response = RouteResponse(
        routes=routes,
        query={
            "from": "Aalto Yliopisto",
            "to": "Keilaniemi",
            "arrival_time": "20241201084500"
        }
    )
    
    assert len(response.routes) == 1
    assert response.query["from"] == "Aalto Yliopisto"


def test_stop_model():
    """Test stop model creation"""
    stop = Stop(
        gtfs_id="HSL:1010101",
        name="Aalto Yliopisto",
        lat=60.18456,
        lon=24.82928
    )
    
    assert stop.gtfs_id == "HSL:1010101"
    assert stop.name == "Aalto Yliopisto"
    assert stop.lat == 60.18456
    assert stop.lon == 24.82928


def test_error_response():
    """Test error response model"""
    error = ErrorResponse(
        error="Not found",
        details="The requested resource was not found"
    )
    
    assert error.error == "Not found"
    assert error.details == "The requested resource was not found"


def test_error_response_without_details():
    """Test error response without details"""
    error = ErrorResponse(error="Bad request")
    
    assert error.error == "Bad request"
    assert error.details is None


def test_route_query_time_validation():
    """Test various time format validations"""
    # Valid formats
    valid_times = [
        "20241201084500",
        "19990101000000",
        "20251231235959"
    ]
    
    for time_str in valid_times:
        query = RouteQuery(
            arrival_time=time_str,
            start_stop="A",
            end_stop="B"
        )
        assert query.arrival_time == time_str
    
    # Invalid formats
    invalid_times = [
        "2024-12-01 08:45:00",  # Wrong format
        "20241301084500",       # Invalid month
        "20241232084500",       # Invalid day
        "20241201254500",       # Invalid hour
        "20241201086000",       # Invalid minute
        "20241201084560",       # Invalid second
        "short",                # Too short
        "toolong123456789",     # Too long
    ]
    
    for time_str in invalid_times:
        with pytest.raises(ValidationError):
            RouteQuery(
                arrival_time=time_str,
                start_stop="A",
                end_stop="B"
            )