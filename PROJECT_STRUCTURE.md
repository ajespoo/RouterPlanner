# Transport Routing API - Complete File Structure Explanation

## 📁 Project Overview
This document explains every file in the Transport Routing API project, detailing the code structure, purpose, and integration points.

---

## 🏗️ **Core Application Files**

### `src/lambda_function.py` - Main API Handler
**Purpose**: FastAPI application that serves as the AWS Lambda entry point
**Key Components**:
```python
# FastAPI app with CORS middleware
app = FastAPI(title="Transport Routing API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Main route endpoint with validation
@app.get("/routes", response_model=RouteResponse)
async def get_routes(arrival_time: str, start_stop: str, end_stop: str):
    # Validates input using Pydantic models
    # Calls Digitransit API through client
    # Returns structured route data
```
**Why Used**: 
- FastAPI provides automatic OpenAPI documentation
- Mangum adapter enables Lambda deployment
- AWS PowerTools integration for observability
- Async support for external API calls

### `src/digitransit_client.py` - External API Integration
**Purpose**: Handles communication with Helsinki's Digitransit GraphQL API
**Key Components**:
```python
class DigitransitClient:
    async def find_stops(self, query: str) -> List[Stop]:
        # GraphQL query to find stops by name
        
    async def plan_route(self, from_stop: str, to_stop: str, arrival_time: datetime) -> List[Route]:
        # Complex GraphQL query for route planning
        # Handles arrival time constraints
        
    def _parse_itinerary(self, itinerary: Dict) -> Optional[Route]:
        # Converts GraphQL response to Pydantic models
```
**Why Used**:
- Abstracts complex GraphQL queries into simple Python methods
- Handles timestamp conversions and data parsing
- Provides async context manager for connection management
- Error handling for external API failures

### `src/models.py` - Data Models and Validation
**Purpose**: Pydantic models for request/response validation and serialization
**Key Components**:
```python
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
```
**Why Used**:
- Automatic request validation with detailed error messages
- Type safety throughout the application
- Automatic OpenAPI schema generation
- JSON serialization with field aliases

---

## 🏗️ **Infrastructure as Code**

### `app.py` - CDK Application Entry Point
**Purpose**: Main CDK application that defines the deployment
**Key Components**:
```python
app = cdk.App()
TransportRoutingStack(app, "TransportRoutingStack", 
    env=cdk.Environment(region="eu-west-1"))
app.synth()
```
**Why Used**:
- Single entry point for CDK deployment
- Environment configuration management
- Stack instantiation and synthesis

### `transport_routing/transport_routing_stack.py` - AWS Infrastructure
**Purpose**: Defines all AWS resources using CDK constructs
**Key Components**:
```python
# Lambda function with proper configuration
lambda_function = _lambda.Function(
    runtime=_lambda.Runtime.PYTHON_3_11,
    timeout=Duration.seconds(30),
    environment={"DIGITRANSIT_API_URL": "...", "SECRETS_ARN": "..."}
)

# API Gateway with CORS
api = apigateway.RestApi(
    default_cors_preflight_options=apigateway.CorsOptions(
        allow_origins=apigateway.Cors.ALL_ORIGINS
    )
)

# CloudWatch Dashboard
dashboard = cloudwatch.Dashboard(
    widgets=[GraphWidget(title="API Requests", left=[route_requests_metric])]
)

# ElastiCache Redis Cluster
redis_cluster = elasticache.CfnCacheCluster(
    cache_node_type="cache.t3.micro",
    engine="redis"
)
```
**Why Used**:
- Infrastructure as Code for reproducible deployments
- Integrated monitoring and logging setup
- Security best practices with VPC and security groups
- Scalable architecture with caching and CDN

### `cdk.json` - CDK Configuration
**Purpose**: CDK project configuration and feature flags
**Key Components**:
```json
{
  "app": "python app.py",
  "context": {
    "@aws-cdk/aws-lambda:recognizeLayerVersion": true,
    "@aws-cdk/core:checkSecretUsage": true
  }
}
```
**Why Used**:
- Enables CDK feature flags for latest capabilities
- Defines the application entry point
- Watch configuration for development

---

## 🧪 **Testing Infrastructure**

### `tests/test_unit.py` - Comprehensive Unit Tests
**Purpose**: Tests individual components in isolation
**Key Components**:
```python
class TestModelsUnit:
    def test_route_query_validation_errors(self):
        # Tests Pydantic model validation
        
class TestDigitransitClientUnit:
    @pytest.mark.asyncio
    async def test_execute_query_success(self, client):
        # Tests GraphQL query execution with mocks
        
class TestLambdaFunctionUnit:
    def test_lambda_handler_with_mock_event(self):
        # Tests Lambda handler with API Gateway events
```
**Why Used**:
- Ensures individual components work correctly
- Fast execution with mocked dependencies
- High code coverage for reliability
- Catches regressions during development

### `tests/test_integration.py` - End-to-End Testing
**Purpose**: Tests complete workflows and system integration
**Key Components**:
```python
class TestDigitransitIntegration:
    @pytest.mark.asyncio
    async def test_mock_digitransit_workflow(self):
        # Tests complete API workflow with mocked responses
        
class TestAPIIntegration:
    def test_full_api_workflow(self):
        # End-to-end API testing with TestClient
        
class TestPerformance:
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        # Performance testing with concurrent requests
```
**Why Used**:
- Validates system behavior under realistic conditions
- Tests API contracts and data flow
- Performance benchmarking capabilities
- Integration with external services

### `tests/test_models.py` - Data Model Testing
**Purpose**: Focused testing of Pydantic models and validation
**Key Components**:
```python
def test_route_query_valid():
    # Tests valid model creation
    
def test_route_query_invalid_time():
    # Tests validation error handling
    
def test_route_leg_with_alias():
    # Tests field aliases and JSON serialization
```
**Why Used**:
- Ensures data validation works correctly
- Tests edge cases and error conditions
- Validates JSON serialization/deserialization

### `run_tests.py` - Test Runner
**Purpose**: Handles test execution in various environments
**Key Components**:
```python
def run_tests_direct():
    # Direct pytest execution for WebContainer environments
    
def run_tests_subprocess():
    # Subprocess execution for full environments
    
def main():
    # Fallback mechanism for different environments
```
**Why Used**:
- Handles environment limitations (WebContainer)
- Provides fallback mechanisms
- Consistent test execution across platforms

---

## 🚀 **Development and Deployment**

### `local_server.py` - Development Server
**Purpose**: Runs the API locally for development and testing
**Key Components**:
```python
def run_server():
    try:
        import uvicorn
        from lambda_function import app
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
    except ImportError:
        # Handle missing dependencies gracefully
```
**Why Used**:
- Local development without AWS deployment
- Fast iteration and debugging
- Environment compatibility handling

### `deploy.sh` - Automated Deployment Script
**Purpose**: Automates the complete deployment process
**Key Components**:
```bash
# Prerequisites checking
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed"
fi

# CDK bootstrap check
if ! aws cloudformation describe-stacks --stack-name CDKToolkit; then
    cdk bootstrap
fi

# Deployment with error handling
if cdk deploy --require-approval never; then
    print_success "Deployment completed successfully!"
fi
```
**Why Used**:
- Reduces deployment complexity
- Handles prerequisites automatically
- Provides clear feedback and error handling
- Extracts and displays API URL

### `DEPLOYMENT.md` - Deployment Documentation
**Purpose**: Comprehensive deployment guide with troubleshooting
**Key Sections**:
- Prerequisites and setup instructions
- Step-by-step deployment process
- Troubleshooting common issues
- Cost optimization and security considerations
**Why Used**:
- Reduces deployment friction
- Provides troubleshooting guidance
- Documents best practices

---

## 📊 **Documentation and Presentation**

### `docs/index.html` - API Documentation Website
**Purpose**: Professional HTML documentation for the API
**Key Components**:
```html
<div class="endpoint">
    <h3><span class="method">GET</span> /routes</h3>
    <div class="parameter">
        <strong>arrival_time</strong> (required) - yyyyMMddHHmmss format
    </div>
</div>
```
**Why Used**:
- Professional documentation presentation
- Interactive examples and code snippets
- Hosted on CloudFront for fast access
- Comprehensive API reference

### `presentation/Transport_Routing_API.pptx` - Project Presentation
**Purpose**: PowerPoint presentation for stakeholders
**Key Slides**:
- Problem statement and solution overview
- Architecture diagrams and technology stack
- Demo and implementation details
**Why Used**:
- Stakeholder communication
- Technical overview for non-developers
- Project demonstration material

### `README.md` - Project Overview
**Purpose**: Main project documentation and quick start guide
**Key Sections**:
- Feature overview and API examples
- Local development instructions
- Architecture description
**Why Used**:
- First point of contact for developers
- Quick start and overview information
- GitHub repository documentation

---

## 🎨 **Frontend Application**

### `src/App.tsx` - React Frontend
**Purpose**: Interactive web interface for the Transport Routing API
**Key Components**:
```tsx
const [routes, setRoutes] = useState<Route[]>([]);
const [loading, setLoading] = useState(false);

const searchRoutes = async () => {
    // API call with error handling
    const mockResponse: RouteResponse = { /* demo data */ };
    setRoutes(mockResponse.routes);
};

return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        {/* Search form and results display */}
    </div>
);
```
**Why Used**:
- User-friendly interface for API testing
- Demonstrates API capabilities visually
- Professional design with Tailwind CSS
- Mock data for development/demo purposes

### `src/main.tsx` - React Application Entry Point
**Purpose**: Bootstraps the React application
**Key Components**:
```tsx
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```
**Why Used**:
- Standard React 18 application setup
- Strict mode for development warnings
- Root element mounting

### Frontend Configuration Files
- **`package.json`**: Dependencies and scripts for React app
- **`vite.config.ts`**: Vite bundler configuration
- **`tailwind.config.js`**: Tailwind CSS styling configuration
- **`tsconfig.json`**: TypeScript configuration
- **`eslint.config.js`**: Code linting rules

**Why Used**: Standard modern React development stack with TypeScript, Vite, and Tailwind CSS for fast development and professional styling.

---

## 📦 **Configuration and Dependencies**

### `requirements.txt` - Python Dependencies
**Purpose**: Production dependencies for the Lambda function
**Key Dependencies**:
```
aws-cdk-lib==2.115.0  # CDK constructs
fastapi==0.104.1      # Web framework
httpx==0.25.2         # Async HTTP client
pydantic==2.5.0       # Data validation
aws-lambda-powertools==2.29.0  # Observability
```
**Why Used**:
- Pinned versions for reproducible builds
- Production-ready packages only
- AWS-optimized dependencies

### `requirements-dev.txt` - Development Dependencies
**Purpose**: Testing and development tools
**Key Dependencies**:
```
pytest==7.4.3         # Testing framework
pytest-cov==4.1.0     # Coverage reporting
pytest-asyncio==0.21.1 # Async test support
black==23.11.0         # Code formatting
mypy==1.7.1           # Type checking
```
**Why Used**:
- Comprehensive testing capabilities
- Code quality tools
- Development workflow support

---

## 🔧 **Supporting Files**

### `src/__init__.py` & `tests/__init__.py`
**Purpose**: Python package markers
**Why Used**: Makes directories importable as Python packages

### `.gitignore`
**Purpose**: Excludes files from version control
**Key Exclusions**:
```
__pycache__/
*.pyc
.env
cdk.out/
node_modules/
```
**Why Used**: Keeps repository clean and secure

---

## 🏗️ **Architecture Summary**

The project follows a **microservices architecture** with clear separation of concerns:

1. **API Layer**: FastAPI with Pydantic validation
2. **Business Logic**: Digitransit client with async operations
3. **Infrastructure**: CDK with AWS best practices
4. **Testing**: Comprehensive unit and integration tests
5. **Documentation**: Multiple formats for different audiences
6. **Frontend**: React interface for demonstration

Each file serves a specific purpose in creating a **production-ready, scalable, and maintainable** transport routing API that meets Andrea's requirements for her daily commute planning system.