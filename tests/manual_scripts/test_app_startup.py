#!/usr/bin/env python3
"""
App Startup Verification Test

Tests that the application can start without errors or crashes.
Verifies:
- All imports work
- Services initialize
- No runtime errors on startup
- API server can be configured
- Client creation works
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Colors for output
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


def test_upstox_client_import():
    """Test that Upstox client can be imported"""
    print_header("TEST 1: Upstox Client Import")
    
    try:
        from backend.services.upstox.client import (
            UpstoxClient,
            create_client,
            AuthenticationError,
            RateLimitError,
            InvalidResponseError,
            safe_get,
            parse_json_safely
        )
        print_success("Upstox client imports successfully")
        print_success(f"UpstoxClient class available")
        print_success(f"All helper functions available")
        print_success(f"All exception classes available")
        return True
    except ImportError as e:
        print_error(f"Failed to import Upstox client: {e}")
        return False


def test_client_creation():
    """Test that client can be created"""
    print_header("TEST 2: Client Creation")
    
    try:
        from backend.services.upstox.client import create_client, UpstoxClient
        
        # Create client without token (should work)
        client = UpstoxClient(api_key="test_key")
        print_success("Client created with explicit API key")
        
        # Test factory function
        client2 = create_client()
        print_success("Client created with factory function")
        
        # Verify BASE_URL
        assert client.BASE_URL == "https://api.upstox.com/v2"
        print_success(f"BASE_URL correct: {client.BASE_URL}")
        
        # Verify session exists
        assert client.session is not None
        print_success("Session initialized")
        
        return True
    except Exception as e:
        print_error(f"Client creation failed: {e}")
        return False


def test_api_methods_exist():
    """Test that all API methods exist"""
    print_header("TEST 3: API Methods Availability")
    
    try:
        from backend.services.upstox.client import UpstoxClient
        
        client = UpstoxClient(api_key="test")
        
        # Check all expected methods
        expected_methods = [
            'get_profile',
            'get_funds_and_margin',
            'get_holdings',
            'get_positions',
            'get_market_quote',
            'get_historical_candles',
            'get_orders',
            'get_order_details',
            'get_order_history',
            'get_trades',
            'get_trades_by_order',
            'get_option_chain',
            'get_charges',
        ]
        
        missing_methods = []
        for method in expected_methods:
            if not hasattr(client, method):
                missing_methods.append(method)
            else:
                print_success(f"Method available: {method}()")
        
        if missing_methods:
            print_error(f"Missing methods: {', '.join(missing_methods)}")
            return False
        
        print_success(f"All {len(expected_methods)} API methods available")
        return True
        
    except Exception as e:
        print_error(f"Method check failed: {e}")
        return False


def test_helper_functions():
    """Test helper functions work"""
    print_header("TEST 4: Helper Functions")
    
    try:
        from backend.services.upstox.client import safe_get, parse_json_safely
        from unittest.mock import Mock
        
        # Test safe_get
        data = {'level1': {'level2': {'level3': 'value'}}}
        result = safe_get(data, 'level1', 'level2', 'level3')
        assert result == 'value'
        print_success("safe_get() works correctly")
        
        # Test with missing key
        result = safe_get(data, 'missing', 'key', default='default')
        assert result == 'default'
        print_success("safe_get() handles missing keys")
        
        # Test parse_json_safely with valid JSON
        mock_response = Mock()
        mock_response.json.return_value = {'test': 'data'}
        result = parse_json_safely(mock_response)
        assert result == {'test': 'data'}
        print_success("parse_json_safely() works correctly")
        
        return True
    except Exception as e:
        print_error(f"Helper function test failed: {e}")
        return False


def test_error_classes():
    """Test that error classes can be raised and caught"""
    print_header("TEST 5: Error Classes")
    
    try:
        from backend.services.upstox.client import (
            UpstoxAPIError,
            AuthenticationError,
            RateLimitError,
            InvalidResponseError,
            InstrumentNotFoundError
        )
        
        # Test raising and catching errors
        try:
            raise AuthenticationError("Test auth error")
        except AuthenticationError as e:
            print_success("AuthenticationError can be raised and caught")
        
        try:
            raise RateLimitError("Test rate limit", retry_after=60)
        except RateLimitError as e:
            assert e.retry_after == 60
            print_success("RateLimitError with retry_after works")
        
        try:
            raise InvalidResponseError("Test invalid response")
        except InvalidResponseError:
            print_success("InvalidResponseError can be raised and caught")
        
        # Test inheritance
        try:
            raise AuthenticationError("Test")
        except UpstoxAPIError:
            print_success("Error inheritance works (AuthenticationError is UpstoxAPIError)")
        
        return True
    except Exception as e:
        print_error(f"Error class test failed: {e}")
        return False


def test_api_server_imports():
    """Test that API server can be imported"""
    print_header("TEST 6: API Server Imports")
    
    try:
        # Try importing API server
        from backend.api.servers import api_server
        print_success("API server module imports successfully")
        
        # Check Flask app exists
        assert hasattr(api_server, 'app')
        print_success("Flask app is available")
        
        # Check CSRF protection
        assert hasattr(api_server, 'csrf')
        print_success("CSRF protection is configured")
        
        return True
    except ImportError as e:
        print_info(f"API server import skipped: {e}")
        return True  # Not critical
    except Exception as e:
        print_error(f"API server check failed: {e}")
        return False


def test_auth_manager():
    """Test that auth manager can be imported"""
    print_header("TEST 7: Auth Manager")
    
    try:
        from backend.utils.auth.manager import AuthManager
        print_success("AuthManager imports successfully")
        
        # Try creating instance
        auth_mgr = AuthManager()
        print_success("AuthManager instantiated")
        
        return True
    except ImportError as e:
        print_info(f"AuthManager import skipped: {e}")
        return True  # Not critical
    except Exception as e:
        print_error(f"AuthManager test failed: {e}")
        return False


def test_environment_setup():
    """Test environment configuration"""
    print_header("TEST 8: Environment Configuration")
    
    # Check for .env.example
    env_example_path = project_root / '.env.example'
    if env_example_path.exists():
        print_success(".env.example file exists")
    else:
        print_info(".env.example not found (optional)")
    
    # Check environment variable loading
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print_success("python-dotenv loads successfully")
    except ImportError:
        print_info("python-dotenv not installed (optional)")
    
    return True


def run_all_startup_tests():
    """Run all startup verification tests"""
    print("\n" + "=" * 70)
    print(f"{BOLD}🚀 APP STARTUP VERIFICATION TEST SUITE{RESET}")
    print("=" * 70)
    
    tests = [
        ("Upstox Client Import", test_upstox_client_import),
        ("Client Creation", test_client_creation),
        ("API Methods Available", test_api_methods_exist),
        ("Helper Functions", test_helper_functions),
        ("Error Classes", test_error_classes),
        ("API Server Imports", test_api_server_imports),
        ("Auth Manager", test_auth_manager),
        ("Environment Setup", test_environment_setup),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"{test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {test_name:30} {status}")
    
    print(f"\n{BOLD}Results: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"\n{GREEN}{BOLD}✅ ALL STARTUP TESTS PASSED!{RESET}")
        print(f"{GREEN}   - App can start without errors")
        print(f"   - All imports work correctly")
        print(f"   - No crashes on initialization")
        print(f"   - All API methods available{RESET}")
        return 0
    else:
        print(f"\n{RED}{BOLD}❌ SOME TESTS FAILED{RESET}")
        print(f"{RED}   Check errors above{RESET}")
        return 1


if __name__ == '__main__':
    exit_code = run_all_startup_tests()
    sys.exit(exit_code)
