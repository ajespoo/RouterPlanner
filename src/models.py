"""
Data models for the Transport Routing API

Data Models and Validation

PURPOSE: Pydantic models for request/response validation and serialization

KEY COMPONENTS:
- RouteQuery: Validates incoming API request parameters
- RouteLeg: Individual journey segment (bus, train, walk, etc.)
- Route: Complete journey with multiple legs
- RouteResponse: API response wrapper with routes and query info
- Stop: Transport stop information
- ErrorResponse: Standardized error message format

CODE STRUCTURE:
1. Pydantic BaseModel classes with field validation
2. Custom validators for time format validation
3. Field aliases for JSON serialization compatibility
4. Type hints for IDE support and runtime validation

WHY USED:
- Automatic request validation with detailed error messages
- Type safety throughout the application
- Automatic OpenAPI schema generation
- JSON serialization with field aliases
- Runtime data validation prevents invalid data processing

**Key Components**:

class RouteQuery(BaseModel):
    arrival_time: str = Field(..., description="yyyyMMddHHmmss format")
    @validator('arrival_time')
    def validate_arrival_time(cls, v):
        # Custom validation for time format

class RouteLeg(BaseModel):
    mode: str  # Transport mode (BUS, TRAIN, etc.)
    from_stop: str = Field(..., alias="from")  # Field aliases for JSON
    
class RouteResponse(BaseModel):
    routes: List[Route]
    query: dict

"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class RouteQuery(BaseModel):
    """Query parameters for route search"""
    arrival_time: str = Field(..., description="Arrival time in yyyyMMddHHmmss format")
    start_stop: str = Field(..., description="Name of the departure stop")
    end_stop: str = Field(..., description="Name of the destination stop")

    @validator('arrival_time')
    def validate_arrival_time(cls, v):
        """Validate arrival time format"""
        try:
            datetime.strptime(v, '%Y%m%d%H%M%S')
        except ValueError:
            raise ValueError('arrival_time must be in yyyyMMddHHmmss format')
        return v


class RouteLeg(BaseModel):
    """Individual leg of a journey"""
    mode: str = Field(..., description="Transport mode (BUS, TRAIN, WALK, etc.)")
    route: Optional[str] = Field(None, description="Route number/name")
    from_stop: str = Field(..., alias="from", description="Departure stop name")
    to_stop: str = Field(..., alias="to", description="Arrival stop name")
    departure: str = Field(..., description="Departure time")
    arrival: str = Field(..., description="Arrival time")
    duration: int = Field(..., description="Duration in seconds")

    class Config:
        allow_population_by_field_name = True


class Route(BaseModel):
    """Complete route information"""
    departure_time: str = Field(..., description="Overall departure time")
    arrival_time: str = Field(..., description="Overall arrival time")
    duration: int = Field(..., description="Total duration in seconds")
    legs: List[RouteLeg] = Field(..., description="Journey legs")


class RouteResponse(BaseModel):
    """API response for route queries"""
    routes: List[Route] = Field(..., description="Available routes")
    query: dict = Field(..., description="Original query parameters")


class Stop(BaseModel):
    """Transport stop information"""
    gtfs_id: str = Field(..., description="GTFS stop ID")
    name: str = Field(..., description="Stop name")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")