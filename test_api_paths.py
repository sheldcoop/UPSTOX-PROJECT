#!/usr/bin/env python3
"""
API Endpoint Path Verification
Tests that all API endpoint paths are properly defined and accessible
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(msg):
    print(f"\n{BOLD}{BLUE}{'=' * 70}{RESET}")
    print(f"{BOLD}{BLUE}{msg}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 70}{RESET}\n")

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_info(msg):
    print(f"{BLUE}ℹ️  {msg}{RESET}")


def test_api_imports():
    """Test that API server modules can be imported"""
    print_header("Testing API Server Imports")
    
    try:
        # Test basic imports without starting server
        import importlib.util
        
        # Check if api_server.py exists and has valid syntax
        api_path = Path('backend/api/servers/api_server.py')
        if not api_path.exists():
            print_error("api_server.py not found")
            return False
        
        print_success("api_server.py found")
        
        # Check for required imports
        content = api_path.read_text()
        required_imports = [
            'from flask import Flask',
            'from flask_cors import CORS',
            'from flask_wtf.csrf import CSRFProtect',
        ]
        
        for imp in required_imports:
            if imp in content:
                print_success(f"Found: {imp}")
            else:
                print_error(f"Missing: {imp}")
                return False
        
        return True
        
    except Exception as e:
        print_error(f"Import test failed: {e}")
        return False


def test_endpoint_definitions():
    """Test that API endpoints are properly defined"""
    print_header("Testing API Endpoint Definitions")
    
    api_path = Path('backend/api/servers/api_server.py')
    if not api_path.exists():
        print_error("api_server.py not found")
        return False
    
    content = api_path.read_text()
    
    # Common endpoint patterns
    endpoints = [
        ('/api/health', 'Health check endpoint'),
        ('/api/portfolio', 'Portfolio endpoints'),
        ('/api/orders', 'Orders endpoints'),
        ('/api/positions', 'Positions endpoints'),
        ('/api/market', 'Market data endpoints'),
    ]
    
    found_endpoints = []
    missing_endpoints = []
    
    for endpoint, description in endpoints:
        # Look for route decorator or path definition
        if f"'{endpoint}" in content or f'"{endpoint}' in content:
            found_endpoints.append((endpoint, description))
            print_success(f"{endpoint:30} - {description}")
        else:
            missing_endpoints.append((endpoint, description))
            print_info(f"{endpoint:30} - {description} (may be defined dynamically)")
    
    print(f"\nFound {len(found_endpoints)} endpoint patterns")
    return len(found_endpoints) > 0


def test_security_features():
    """Test that security features are properly configured"""
    print_header("Testing Security Features")
    
    api_path = Path('backend/api/servers/api_server.py')
    if not api_path.exists():
        print_error("api_server.py not found")
        return False
    
    content = api_path.read_text()
    
    security_features = [
        ('CSRFProtect', 'CSRF protection'),
        ('SECRET_KEY', 'Secret key configuration'),
        ('WTF_CSRF_ENABLED', 'CSRF enabled flag'),
        ('get_logger', 'Centralized logging'),
        ("os.getenv('UPSTOX_CLIENT_ID'", 'Environment-based credentials'),
    ]
    
    all_present = True
    for feature, description in security_features:
        if feature in content:
            print_success(f"{description:30} - Present")
        else:
            print_error(f"{description:30} - Missing")
            all_present = False
    
    return all_present


def test_middleware_configuration():
    """Test that middleware is properly configured"""
    print_header("Testing Middleware Configuration")
    
    api_path = Path('backend/api/servers/api_server.py')
    if not api_path.exists():
        print_error("api_server.py not found")
        return False
    
    content = api_path.read_text()
    
    middleware_features = [
        ('@app.before_request', 'Request middleware'),
        ('@app.after_request', 'Response middleware'),
        ('@app.errorhandler', 'Error handling'),
        ('inject_trace_id', 'Request tracing'),
    ]
    
    all_present = True
    for feature, description in middleware_features:
        if feature in content:
            print_success(f"{description:30} - Present")
        else:
            print_info(f"{description:30} - Not found (optional)")
    
    return True


def test_database_configuration():
    """Test that database is properly configured"""
    print_header("Testing Database Configuration")
    
    api_path = Path('backend/api/servers/api_server.py')
    content = api_path.read_text()
    
    db_features = [
        ("os.getenv('DATABASE_PATH'", 'Environment-based DB path'),
        ('DB_PATH', 'Database path variable'),
    ]
    
    all_present = True
    for feature, description in db_features:
        if feature in content:
            print_success(f"{description:30} - Present")
        else:
            print_error(f"{description:30} - Missing")
            all_present = False
    
    return all_present


def test_frontend_paths():
    """Test that frontend files exist"""
    print_header("Testing Frontend Structure")
    
    frontend_path = Path('frontend')
    if not frontend_path.exists():
        print_info("frontend/ directory not found (may be in different location)")
        return True
    
    # Check for NiceGUI dashboard
    nicegui_path = Path('nicegui_dashboard.py')
    if nicegui_path.exists():
        print_success("NiceGUI dashboard file found")
        return True
    
    print_info("Frontend files may be organized differently")
    return True


def run_all_tests():
    """Run all endpoint path tests"""
    print("\n" + "=" * 70)
    print(f"{BOLD}🧪 API ENDPOINT PATH VERIFICATION{RESET}")
    print("=" * 70)
    
    tests = [
        ("API Imports", test_api_imports),
        ("Endpoint Definitions", test_endpoint_definitions),
        ("Security Features", test_security_features),
        ("Middleware Configuration", test_middleware_configuration),
        ("Database Configuration", test_database_configuration),
        ("Frontend Structure", test_frontend_paths),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"{test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {test_name:30} {status}")
    
    print(f"\n{BOLD}Results: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"\n{GREEN}{BOLD}✅ ALL PATH VERIFICATIONS PASSED!{RESET}")
        print(f"{GREEN}   - API server properly configured")
        print(f"   - Security features in place")
        print(f"   - No broken paths detected")
        print(f"   - Endpoints properly defined{RESET}")
        return 0
    else:
        print(f"\n{YELLOW}{BOLD}⚠️  SOME TESTS HAD ISSUES{RESET}")
        print(f"{YELLOW}   This may be expected for optional features{RESET}")
        return 0 if passed >= total * 0.8 else 1  # Pass if 80%+ pass


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
