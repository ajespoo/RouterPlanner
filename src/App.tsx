import React, { useState } from 'react';
import { MapPin, Clock, Route, Search, AlertCircle, CheckCircle } from 'lucide-react';

/*
PURPOSE: React frontend interface for the Transport Routing API

KEY COMPONENTS:
- Interactive search form with validation
- Route results display with transport mode visualization
- Professional design with Tailwind CSS styling
- Mock data for development/demo purposes
- Responsive design for all screen sizes

CODE STRUCTURE:
1. TypeScript interfaces for type safety
2. React hooks for state management
3. Form handling with validation
4. Results display with transport mode icons
5. Utility functions for data formatting

WHY USED:
- User-friendly interface for API testing
- Demonstrates API capabilities visually
- Professional design showcases the solution
- Mock data enables development without backend
- Responsive design works on all devices
*/

interface RouteLeg {
  mode: string;
  route?: string;
  from: string;
  to: string;
  departure: string;
  arrival: string;
  duration: number;
}

interface Route {
  departure_time: string;
  arrival_time: string;
  duration: number;
  legs: RouteLeg[];
}

interface RouteResponse {
  routes: Route[];
  query: {
    from: string;
    to: string;
    arrival_time: string;
  };
}

function App() {
  const [arrivalTime, setArrivalTime] = useState('20241201084500');
  const [startStop, setStartStop] = useState('Aalto Yliopisto');
  const [endStop, setEndStop] = useState('Keilaniemi');
  const [routes, setRoutes] = useState<Route[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastQuery, setLastQuery] = useState<any>(null);

  const formatTime = (timeStr: string) => {
    if (timeStr.length === 14) {
      // yyyyMMddHHmmss format
      const year = timeStr.substring(0, 4);
      const month = timeStr.substring(4, 6);
      const day = timeStr.substring(6, 8);
      const hour = timeStr.substring(8, 10);
      const minute = timeStr.substring(10, 12);
      return `${day}/${month}/${year} ${hour}:${minute}`;
    }
    return timeStr;
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    
    if (hours > 0) {
      return `${hours}h ${remainingMinutes}m`;
    }
    return `${minutes}m`;
  };

  const getModeIcon = (mode: string) => {
    switch (mode.toLowerCase()) {
      case 'bus':
        return '🚌';
      case 'train':
        return '🚆';
      case 'tram':
        return '🚋';
      case 'subway':
        return '🚇';
      case 'walk':
        return '🚶';
      case 'ferry':
        return '⛴️';
      default:
        return '🚌';
    }
  };

  const getModeColor = (mode: string) => {
    switch (mode.toLowerCase()) {
      case 'bus':
        return 'bg-blue-100 text-blue-800';
      case 'train':
        return 'bg-green-100 text-green-800';
      case 'tram':
        return 'bg-purple-100 text-purple-800';
      case 'subway':
        return 'bg-orange-100 text-orange-800';
      case 'walk':
        return 'bg-gray-100 text-gray-800';
      case 'ferry':
        return 'bg-cyan-100 text-cyan-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  const searchRoutes = async () => {
    if (!arrivalTime || !startStop || !endStop) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // For demo purposes, we'll simulate the API call
      // In production, this would call your actual API endpoint
      const mockResponse: RouteResponse = {
        routes: [
          {
            departure_time: "08:20:00",
            arrival_time: "08:42:00",
            duration: 1320,
            legs: [
              {
                mode: "BUS",
                route: "550",
                from: startStop,
                to: endStop,
                departure: "08:20:00",
                arrival: "08:42:00",
                duration: 1320
              }
            ]
          },
          {
            departure_time: "08:15:00",
            arrival_time: "08:45:00",
            duration: 1800,
            legs: [
              {
                mode: "WALK",
                from: startStop,
                to: "Aalto-yliopiston metroasema",
                departure: "08:15:00",
                arrival: "08:18:00",
                duration: 180
              },
              {
                mode: "SUBWAY",
                route: "M1",
                from: "Aalto-yliopiston metroasema",
                to: "Keilaniemi",
                departure: "08:20:00",
                arrival: "08:42:00",
                duration: 1320
              },
              {
                mode: "WALK",
                from: "Keilaniemi",
                to: endStop,
                departure: "08:42:00",
                arrival: "08:45:00",
                duration: 180
              }
            ]
          }
        ],
        query: {
          from: startStop,
          to: endStop,
          arrival_time: arrivalTime
        }
      };

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setRoutes(mockResponse.routes);
      setLastQuery(mockResponse.query);
    } catch (err) {
      setError('Failed to fetch routes. Please try again.');
      console.error('Route search error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Route className="w-12 h-12 text-indigo-600 mr-3" />
            <h1 className="text-4xl font-bold text-gray-900">
              Helsinki Transport Router
            </h1>
          </div>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Plan your journey through Helsinki's public transport network. 
            Find the best routes to arrive on time for your daily meetings.
          </p>
        </div>

        {/* Search Form */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8 max-w-4xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Clock className="w-4 h-4 inline mr-1" />
                Arrival Time
              </label>
              <input
                type="text"
                value={arrivalTime}
                onChange={(e) => setArrivalTime(e.target.value)}
                placeholder="yyyyMMddHHmmss"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Format: {formatTime(arrivalTime)}
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <MapPin className="w-4 h-4 inline mr-1" />
                From Stop
              </label>
              <input
                type="text"
                value={startStop}
                onChange={(e) => setStartStop(e.target.value)}
                placeholder="e.g., Aalto Yliopisto"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <MapPin className="w-4 h-4 inline mr-1" />
                To Stop
              </label>
              <input
                type="text"
                value={endStop}
                onChange={(e) => setEndStop(e.target.value)}
                placeholder="e.g., Keilaniemi"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>
          
          <button
            onClick={searchRoutes}
            disabled={loading}
            className="w-full bg-indigo-600 text-white py-3 px-6 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 flex items-center justify-center"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Searching Routes...
              </>
            ) : (
              <>
                <Search className="w-5 h-5 mr-2" />
                Find Routes
              </>
            )}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 max-w-4xl mx-auto">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
              <p className="text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Results */}
        {routes.length > 0 && (
          <div className="max-w-4xl mx-auto">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <div className="flex items-center">
                <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                <p className="text-green-700">
                  Found {routes.length} route{routes.length !== 1 ? 's' : ''} from{' '}
                  <strong>{lastQuery?.from}</strong> to <strong>{lastQuery?.to}</strong>
                </p>
              </div>
            </div>

            <div className="space-y-4">
              {routes.map((route, routeIndex) => (
                <div key={routeIndex} className="bg-white rounded-xl shadow-lg overflow-hidden">
                  <div className="bg-indigo-50 px-6 py-4 border-b">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="text-center">
                          <p className="text-sm text-gray-600">Departure</p>
                          <p className="text-lg font-semibold text-indigo-600">
                            {route.departure_time}
                          </p>
                        </div>
                        <div className="text-center">
                          <p className="text-sm text-gray-600">Arrival</p>
                          <p className="text-lg font-semibold text-indigo-600">
                            {route.arrival_time}
                          </p>
                        </div>
                        <div className="text-center">
                          <p className="text-sm text-gray-600">Duration</p>
                          <p className="text-lg font-semibold text-gray-900">
                            {formatDuration(route.duration)}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-600">
                          {route.legs.length} leg{route.legs.length !== 1 ? 's' : ''}
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="p-6">
                    <div className="space-y-4">
                      {route.legs.map((leg, legIndex) => (
                        <div key={legIndex} className="flex items-center space-x-4">
                          <div className="flex-shrink-0">
                            <div className={`px-3 py-1 rounded-full text-sm font-medium ${getModeColor(leg.mode)}`}>
                              {getModeIcon(leg.mode)} {leg.mode}
                              {leg.route && ` ${leg.route}`}
                            </div>
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-2">
                                <span className="text-sm font-medium text-gray-900">
                                  {leg.from}
                                </span>
                                <span className="text-gray-400">→</span>
                                <span className="text-sm font-medium text-gray-900">
                                  {leg.to}
                                </span>
                              </div>
                              <div className="flex items-center space-x-4 text-sm text-gray-600">
                                <span>{leg.departure} - {leg.arrival}</span>
                                <span>({formatDuration(leg.duration)})</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* API Information */}
        <div className="mt-12 max-w-4xl mx-auto">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              API Information
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Endpoint</h3>
                <code className="block bg-gray-100 p-2 rounded text-sm">
                  GET /routes
                </code>
              </div>
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Parameters</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li><code>arrival_time</code>: yyyyMMddHHmmss format</li>
                  <li><code>start_stop</code>: Departure stop name</li>
                  <li><code>end_stop</code>: Destination stop name</li>
                </ul>
              </div>
            </div>
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> This demo shows mock data. In production, 
                the API integrates with Helsinki's Digitransit service for real-time 
                public transport information.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;