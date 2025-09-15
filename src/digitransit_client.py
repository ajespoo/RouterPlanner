"""
Client for interacting with Helsinki Digitransit API

PURPOSE: Handles communication with Helsinki's Digitransit GraphQL API

KEY COMPONENTS:
- Async HTTP client using httpx for non-blocking requests
- GraphQL query construction and execution
- Data parsing from GraphQL responses to Pydantic models
- Error handling for external API failures
- Context manager for proper resource cleanup

CODE STRUCTURE:
1. DigitransitClient class with async context manager
2. find_stops() - GraphQL query to search stops by name
3. plan_route() - Complex route planning with arrival time constraints
4. _parse_itinerary() - Converts GraphQL response to Route models
5. _execute_query() - Generic GraphQL query executor

WHY USED:
- Abstracts complex GraphQL queries into simple Python methods
- Handles timestamp conversions and data transformations
- Provides async context manager for connection management
- Separates external API logic from business logic
- Enables easy testing with mock responses
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
import httpx
from .models import Stop, Route, RouteLeg

logger = logging.getLogger(__name__)


class DigitransitClient:
    """Client for Helsinki Digitransit GraphQL API"""

    def __init__(self, base_url: str = "https://api.digitransit.fi/routing/v1/routers/hsl/index/graphql"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def find_stops(self, query: str, limit: int = 10) -> List[Stop]:
        """Find stops by name"""
        graphql_query = """
        query FindStops($name: String!) {
          stops(name: $name) {
            gtfsId
            name
            lat
            lon
          }
        }
        """

        try:
            response = await self._execute_query(
                graphql_query,
                variables={"name": query}
            )
            
            stops_data = response.get("data", {}).get("stops", [])
            return [
                Stop(
                    gtfs_id=stop["gtfsId"],
                    name=stop["name"],
                    lat=stop["lat"],
                    lon=stop["lon"]
                )
                for stop in stops_data[:limit]
            ]
        except Exception as e:
            logger.error(f"Error finding stops for query '{query}': {e}")
            return []

    async def plan_route(
        self,
        from_stop: str,
        to_stop: str,
        arrival_time: datetime,
        max_routes: int = 5
    ) -> List[Route]:
        """Plan routes between two stops arriving by a specific time"""
        
        # Find stops
        from_stops = await self.find_stops(from_stop)
        to_stops = await self.find_stops(to_stop)

        if not from_stops:
            logger.warning(f"No stops found for: {from_stop}")
            return []

        if not to_stops:
            logger.warning(f"No stops found for: {to_stop}")
            return []

        # Use the first matching stop for each
        from_stop_id = from_stops[0].gtfs_id
        to_stop_id = to_stops[0].gtfs_id

        logger.info(f"Planning route from {from_stops[0].name} ({from_stop_id}) to {to_stops[0].name} ({to_stop_id})")

        # Format time for GraphQL (ISO format)
        time_str = arrival_time.strftime("%Y-%m-%dT%H:%M:%S")

        graphql_query = """
        query PlanRoute($from: String!, $to: String!, $time: String!, $arriveBy: Boolean!) {
          plan(
            from: {stop: $from}
            to: {stop: $to}
            date: $time
            time: $time
            arriveBy: $arriveBy
            numItineraries: 5
            transportModes: [
              {mode: BUS}
              {mode: TRAIN}
              {mode: TRAM}
              {mode: SUBWAY}
              {mode: FERRY}
            ]
          ) {
            itineraries {
              startTime
              endTime
              duration
              legs {
                mode
                startTime
                endTime
                duration
                from {
                  stop {
                    gtfsId
                    name
                  }
                }
                to {
                  stop {
                    gtfsId
                    name
                  }
                }
                route {
                  shortName
                  longName
                }
                trip {
                  route {
                    shortName
                  }
                }
              }
            }
          }
        }
        """

        try:
            response = await self._execute_query(
                graphql_query,
                variables={
                    "from": from_stop_id,
                    "to": to_stop_id,
                    "time": time_str,
                    "arriveBy": True
                }
            )

            plan_data = response.get("data", {}).get("plan", {})
            itineraries = plan_data.get("itineraries", [])

            routes = []
            for itinerary in itineraries[:max_routes]:
                route = self._parse_itinerary(itinerary)
                if route:
                    routes.append(route)

            return routes

        except Exception as e:
            logger.error(f"Error planning route: {e}")
            return []

    def _parse_itinerary(self, itinerary: Dict[str, Any]) -> Optional[Route]:
        """Parse GraphQL itinerary response into Route model"""
        try:
            start_time = datetime.fromtimestamp(itinerary["startTime"] / 1000)
            end_time = datetime.fromtimestamp(itinerary["endTime"] / 1000)
            
            legs = []
            for leg_data in itinerary["legs"]:
                leg_start = datetime.fromtimestamp(leg_data["startTime"] / 1000)
                leg_end = datetime.fromtimestamp(leg_data["endTime"] / 1000)
                
                # Get route information
                route_name = None
                if leg_data.get("route"):
                    route_name = leg_data["route"].get("shortName")
                elif leg_data.get("trip", {}).get("route"):
                    route_name = leg_data["trip"]["route"].get("shortName")

                # Get stop names
                from_name = "Unknown"
                to_name = "Unknown"
                
                if leg_data.get("from", {}).get("stop"):
                    from_name = leg_data["from"]["stop"]["name"]
                
                if leg_data.get("to", {}).get("stop"):
                    to_name = leg_data["to"]["stop"]["name"]

                leg = RouteLeg(
                    mode=leg_data["mode"],
                    route=route_name,
                    from_stop=from_name,
                    to_stop=to_name,
                    departure=leg_start.strftime("%H:%M:%S"),
                    arrival=leg_end.strftime("%H:%M:%S"),
                    duration=leg_data["duration"]
                )
                legs.append(leg)

            return Route(
                departure_time=start_time.strftime("%H:%M:%S"),
                arrival_time=end_time.strftime("%H:%M:%S"),
                duration=itinerary["duration"],
                legs=legs
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing itinerary: {e}")
            return None

    async def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query"""
        payload = {
            "query": query,
            "variables": variables or {}
        }

        try:
            response = await self.client.post(
                self.base_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "TransportRoutingAPI/1.0"
                }
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "errors" in result:
                logger.error(f"GraphQL errors: {result['errors']}")
                raise Exception(f"GraphQL query failed: {result['errors']}")
            
            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"API request failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise