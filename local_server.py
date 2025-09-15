#!/usr/bin/env python3
"""
Local development server for the transport routing API.
Handles environments where certain modules may not be available.

PURPOSE: Runs the FastAPI application locally for development and testing

KEY COMPONENTS:
- Uvicorn server configuration for local development
- Import error handling for missing dependencies
- Development-friendly server settings
- Clear user instructions and error messages

CODE STRUCTURE:
1. Server configuration with uvicorn
2. Import error handling for graceful degradation
3. User-friendly console output
4. Keyboard interrupt handling

WHY USED:
- Local development without AWS deployment
- Fast iteration and debugging capabilities
- Environment compatibility handling
- Easy testing of API endpoints locally
- Development workflow optimization
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_server():
    """Run the local development server."""
    try:
        import uvicorn
        from lambda_function import app
        
        print("Starting local development server...")
        print("API will be available at: http://localhost:8000")
        print("API documentation at: http://localhost:8000/docs")
        print("Press Ctrl+C to stop the server")
        
        # Run the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,  # Disable reload to avoid file watching issues
            log_level="info"
        )
        
    except ImportError as e:
        print(f"Error importing required modules: {e}")
        print("Please install required dependencies:")
        print("pip install uvicorn fastapi")
        return 1
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        return 0
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_server())