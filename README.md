# Transport Routing REST API

<!--
PURPOSE: Main project documentation and quick start guide

KEY COMPONENTS:
- Project overview and feature highlights
- Quick start instructions for local development
- API usage examples with cURL commands
- Architecture overview and technology stack
- Links to detailed documentation

STRUCTURE:
1. Project description and problem statement
2. Feature overview with emojis for visual appeal
3. API endpoint documentation with examples
4. Local development setup instructions
5. Deployment process overview
6. Architecture and technology details

WHY USED:
- First point of contact for developers and stakeholders
- Quick start information for immediate productivity
- GitHub repository documentation standard
- Marketing material for the technical solution
- Central hub linking to detailed documentation
-->

A REST API service for querying public transport routes in Helsinki, specifically designed to help Andrea plan her commute from Aalto Yliopisto to Keilaniemi KONE Building.

## Overview

This service provides a REST API wrapper around Helsinki's Digitransit GraphQL API, allowing users to query transport routes by specifying arrival time, start stop, and destination stop.

## Features

- 🚌 Route planning with arrival time constraints
- 🔍 Stop name to stop ID resolution
- ⏰ Support for weekday scheduling
- 📊 Comprehensive observability and logging
- 🧪 Full test coverage
- 🚀 AWS deployment ready

## API Endpoints

### GET /routes

Query transport routes between two stops.

**Parameters:**
- `arrival_time` (required): Target arrival time in `yyyyMMddHHmmss` format
- `start_stop` (required): Name of the departure stop
- `end_stop` (required): Name of the destination stop

**Example Request:**
```
GET /routes?arrival_time=20241201084500&start_stop=Aalto Yliopisto&end_stop=Keilaniemi
```

**Example Response:**
```json
{
  "routes": [
    {
      "departure_time": "08:20:00",
      "arrival_time": "08:42:00",
      "duration": 1320,
      "legs": [
        {
          "mode": "BUS",
          "route": "550",
          "from": "Aalto Yliopisto",
          "to": "Keilaniemi",
          "departure": "08:20:00",
          "arrival": "08:42:00"
        }
      ]
    }
  ],
  "query": {
    "from": "Aalto Yliopisto",
    "to": "Keilaniemi",
    "arrival_time": "20241201084500"
  }
}
```

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
python -m pytest tests/ -v --cov=src
```

3. Run locally:
```bash
python -m uvicorn src.lambda_function:app --reload --port 8000
```

4. Test the API:
```bash
curl "http://localhost:8000/routes?arrival_time=20241201084500&start_stop=Aalto Yliopisto&end_stop=Keilaniemi"
```

## Deployment

1. Install AWS CDK:
```bash
npm install -g aws-cdk
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Bootstrap CDK (first time only):
```bash
cdk bootstrap
```

4. Deploy:
```bash
cdk deploy
```

## Architecture

- **AWS Lambda**: Hosts the REST API logic
- **API Gateway**: Provides REST endpoint with proper CORS
- **CloudWatch**: Logging and monitoring
- **CDK**: Infrastructure as Code

## Code Quality

- **Linting**: flake8, black
- **Testing**: pytest with coverage
- **Type hints**: Full type annotation support
- **Error handling**: Comprehensive error handling and validation