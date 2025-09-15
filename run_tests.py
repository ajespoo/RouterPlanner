#!/usr/bin/env python3
"""
Test runner for the transport routing API.
Handles environments where subprocess/signal modules may not be available.

PURPOSE: Provides robust test execution across different environments

KEY COMPONENTS:
- run_tests_direct(): Direct pytest execution for WebContainer environments
- run_tests_subprocess(): Standard subprocess execution for full environments
- Fallback mechanism for environment compatibility
- Coverage reporting with HTML output

CODE STRUCTURE:
1. Environment detection and fallback logic
2. Direct pytest module execution
3. Subprocess-based test execution
4. Error handling for missing modules
5. Coverage reporting configuration

WHY USED:
- Handles WebContainer environment limitations
- Provides fallback mechanisms for different Python environments
- Consistent test execution across platforms
- Comprehensive coverage reporting
- User-friendly error messages and guidance
"""

import sys
import os

def run_tests_direct():
    """Run tests directly using pytest module execution."""
    try:
        import pytest
        
        # Add current directory to Python path
        sys.path.insert(0, os.getcwd())
        
        # Run pytest with coverage
        exit_code = pytest.main([
            '--cov=src',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',
            '--verbose',
            'tests/'
        ])
        
        return exit_code
        
    except ImportError as e:
        print(f"Error importing pytest: {e}")
        print("Please install pytest: pip install pytest pytest-cov")
        return 1

def run_tests_subprocess():
    """Run tests using subprocess (fallback method)."""
    try:
        import subprocess
        
        # Run pytest with coverage
        result = subprocess.run([
            sys.executable, '-m', 'pytest',
            '--cov=src',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',
            '--verbose',
            'tests/'
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
            
        return result.returncode
        
    except ImportError as e:
        print(f"Subprocess not available: {e}")
        return None

def main():
    """Main test runner function."""
    print("Running transport routing API tests...")
    
    # Try subprocess method first (more robust)
    exit_code = run_tests_subprocess()
    
    # If subprocess fails, try direct pytest execution
    if exit_code is None:
        print("Falling back to direct pytest execution...")
        exit_code = run_tests_direct()
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())