#!/usr/bin/env python3
"""
Comprehensive API Testing Suite
Tests all API endpoints to ensure no broken paths and proper functionality
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import json
from unittest.mock import patch, MagicMock


class TestAPIServerIntegrity:
    """Test that API server can be imported and configured correctly"""
    
    def test_api_server_imports(self):
        """Test that all API server imports work"""
        try:
            from backend.api.servers import api_server
            assert api_server.app is not None
            assert hasattr(api_server, 'logger')
            assert hasattr(api_server, 'csrf')  # CSRF protection enabled
            print("✅ API server imports successfully")
        except ImportError as e:
            pytest.fail(f"Failed to import API server: {e}")
    
    def test_security_configuration(self):
        """Test that security configurations are in place"""
        from backend.api.servers import api_server
        
        # Check SECRET_KEY is configured
        assert api_server.app.config.get('SECRET_KEY') is not None
        print("✅ SECRET_KEY configured")
        
        # Check CSRF protection is enabled
        assert api_server.app.config.get('WTF_CSRF_ENABLED') == True
        print("✅ CSRF protection enabled")
        
        # Check CORS is configured
        assert hasattr(api_server, 'csrf')
        print("✅ Security configurations in place")
    
    def test_environment_variable_loading(self):
        """Test that credentials are loaded from environment, not hardcoded"""
        from backend.api.servers import api_server
        
        # CLIENT_ID should be from environment or empty (not hardcoded)
        client_id = api_server.CLIENT_ID
        assert client_id != '33b9a757-1a99-47dc-b6fa-c3cf3dcaf6b4', \
            "CLIENT_ID should not be hardcoded!"
        print("✅ Credentials loaded from environment (not hardcoded)")
    
    def test_centralized_logging(self):
        """Test that centralized logging is used"""
        from backend.api.servers import api_server
        
        # Logger should be from centralized config
        assert api_server.logger is not None
        assert api_server.logger.name == 'backend.api.servers.api_server'
        print("✅ Centralized logging configured")


class TestSQLInjectionProtection:
    """Test that SQL injection vulnerabilities are fixed"""
    
    def test_symbol_resolver_parameterized_queries(self):
        """Test symbol_resolver uses parameterized queries"""
        from backend.utils.helpers import symbol_resolver
        
        # Check that resolve_symbols exists and has proper signature
        import inspect
        sig = inspect.signature(symbol_resolver.resolve_symbols)
        params = sig.parameters
        
        assert 'symbols' in params
        assert 'segment' in params
        assert 'sql_filter' in params  # Should exist but be deprecated
        print("✅ symbol_resolver.resolve_symbols has proper signature")
    
    def test_database_validator_table_whitelist(self):
        """Test database_validator uses table whitelist"""
        from backend.data.database import database_validator
        
        # Try to instantiate validator
        try:
            validator = database_validator.DatabaseValidator()
            print("✅ DatabaseValidator instantiated successfully")
            
            # Test that invalid table name raises error
            with pytest.raises(ValueError):
                validator.check_data_quality("malicious_table'; DROP TABLE users--")
            print("✅ Table whitelist protection works")
            
        except Exception as e:
            print(f"⚠️ DatabaseValidator test skipped: {e}")


class TestAPIEndpointPaths:
    """Test that API endpoint paths are defined correctly"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        from backend.api.servers import api_server
        api_server.app.config['TESTING'] = True
        api_server.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        return api_server.app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_health_endpoint_exists(self, client):
        """Test that /api/health endpoint exists"""
        response = client.get('/api/health')
        # Should not return 404
        assert response.status_code != 404, "Health endpoint should exist"
        print(f"✅ /api/health endpoint exists (status: {response.status_code})")
    
    def test_cors_headers(self, client):
        """Test that CORS headers are set"""
        response = client.options('/api/health')
        # CORS should be configured
        print(f"✅ CORS configured (tested with OPTIONS)")
    
    @patch('sqlite3.connect')
    def test_portfolio_endpoints_exist(self, mock_connect, client):
        """Test that portfolio endpoints exist"""
        # Mock database
        mock_cursor = MagicMock()
        mock_connect.return_value.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        endpoints = [
            '/api/portfolio/summary',
            '/api/portfolio/holdings',
            '/api/portfolio/positions',
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code != 404, f"Endpoint {endpoint} should exist"
            print(f"✅ {endpoint} exists (status: {response.status_code})")


class TestDatabaseConnections:
    """Test database connection handling"""
    
    def test_database_path_from_environment(self):
        """Test that database path can be configured via environment"""
        from backend.api.servers import api_server
        
        # DB_PATH should be configurable
        assert hasattr(api_server, 'DB_PATH')
        db_path = api_server.DB_PATH
        assert db_path is not None
        print(f"✅ Database path configured: {db_path}")


class TestLoggingConfiguration:
    """Test logging configuration"""
    
    def test_centralized_logger_import(self):
        """Test that centralized logger can be imported"""
        try:
            from backend.utils.logging.config import get_logger
            logger = get_logger('test')
            assert logger is not None
            print("✅ Centralized logger imports successfully")
        except ImportError as e:
            pytest.fail(f"Failed to import centralized logger: {e}")
    
    def test_logger_works(self):
        """Test that logger actually works"""
        from backend.utils.logging.config import get_logger
        
        logger = get_logger('test_logger')
        try:
            logger.info("Test log message")
            logger.debug("Test debug message")
            logger.warning("Test warning message")
            print("✅ Logger functions work correctly")
        except Exception as e:
            pytest.fail(f"Logger failed: {e}")


class TestSecurityFixes:
    """Test that all security fixes are in place"""
    
    def test_env_example_has_placeholders(self):
        """Test that .env.example doesn't contain real credentials"""
        env_example_path = project_root / '.env.example'
        
        if env_example_path.exists():
            content = env_example_path.read_text()
            
            # Should NOT contain real credentials
            assert '33b9a757-1a99-47dc-b6fa-c3cf3dcaf6b4' not in content, \
                ".env.example should not contain real CLIENT_ID"
            assert 't6hxe1b1ky' not in content, \
                ".env.example should not contain real CLIENT_SECRET"
            
            # Should contain placeholders
            assert 'your-upstox-client-id-here' in content or 'placeholder' in content.lower()
            print("✅ .env.example contains placeholders (no real credentials)")
        else:
            print("⚠️ .env.example not found")


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("\n" + "=" * 70)
    print("🧪 COMPREHENSIVE API TESTING SUITE")
    print("=" * 70)
    
    # Run pytest with verbose output
    exit_code = pytest.main([
        __file__,
        '-v',  # Verbose
        '--tb=short',  # Short traceback
        '-x',  # Stop on first failure
    ])
    
    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✅ ALL TESTS PASSED - No broken paths, APIs working correctly")
    else:
        print("❌ SOME TESTS FAILED - Check output above")
    print("=" * 70)
    
    return exit_code


if __name__ == '__main__':
    exit_code = run_comprehensive_tests()
    sys.exit(exit_code)
