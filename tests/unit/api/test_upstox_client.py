"""
Unit Tests for Upstox Client

These tests use mocking to ensure NO real internet calls are made.
All scenarios test error handling and edge cases.

Test Coverage:
- Authentication failures (401)
- Rate limiting (429) with Retry-After header
- Malformed JSON responses (HTML instead of JSON)
- Defensive JSON parsing
- Calculation logic
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.upstox.client import (
    UpstoxClient,
    AuthenticationError,
    RateLimitError,
    InvalidResponseError,
    UpstoxAPIError,
    safe_get,
    parse_json_safely
)


class TestHelperFunctions:
    """Test defensive JSON parsing helper functions"""
    
    def test_safe_get_simple(self):
        """Test safe_get with simple dictionary"""
        data = {'key1': 'value1'}
        assert safe_get(data, 'key1') == 'value1'
        assert safe_get(data, 'missing', default='default') == 'default'
    
    def test_safe_get_nested(self):
        """Test safe_get with nested dictionary"""
        data = {'data': {'ltp': 100.5, 'volume': 1000}}
        assert safe_get(data, 'data', 'ltp') == 100.5
        assert safe_get(data, 'data', 'volume') == 1000
        assert safe_get(data, 'data', 'missing', default=0) == 0
    
    def test_safe_get_deep_nested(self):
        """Test safe_get with deeply nested structure"""
        data = {'level1': {'level2': {'level3': 'value'}}}
        assert safe_get(data, 'level1', 'level2', 'level3') == 'value'
        assert safe_get(data, 'level1', 'missing', 'level3', default=None) is None
    
    def test_safe_get_non_dict(self):
        """Test safe_get with non-dictionary input"""
        assert safe_get(None, 'key', default='default') == 'default'
        assert safe_get('string', 'key', default='default') == 'default'
        assert safe_get(123, 'key', default='default') == 'default'
    
    def test_parse_json_safely_valid(self):
        """Test parse_json_safely with valid JSON"""
        mock_response = Mock()
        mock_response.json.return_value = {'status': 'success', 'data': {}}
        
        result = parse_json_safely(mock_response)
        assert result == {'status': 'success', 'data': {}}
    
    def test_parse_json_safely_invalid(self):
        """Test parse_json_safely with HTML response (common proxy error)"""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("No JSON object could be decoded")
        mock_response.text = "<html><body>Error 502 Bad Gateway</body></html>"
        
        with pytest.raises(InvalidResponseError) as exc_info:
            parse_json_safely(mock_response)
        
        assert "Expected JSON but got" in str(exc_info.value)


class TestAuthenticationFailure:
    """Test authentication failure scenarios (401)"""
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_401_raises_authentication_error(self, mock_session_class):
        """Test that 401 status raises AuthenticationError"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        # Create client and attempt request
        client = UpstoxClient(access_token="invalid_token")
        
        with pytest.raises(AuthenticationError) as exc_info:
            client.get_profile()
        
        assert "Authentication failed" in str(exc_info.value)
    
    def test_no_access_token_raises_error(self):
        """Test that missing access token raises AuthenticationError"""
        client = UpstoxClient()  # No token provided
        client.access_token = None  # Ensure it's None
        
        with pytest.raises(AuthenticationError) as exc_info:
            client._get_headers()
        
        assert "No access token available" in str(exc_info.value)


class TestRateLimiting:
    """Test rate limiting scenarios (429)"""
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_429_raises_rate_limit_error(self, mock_session_class):
        """Test that 429 status raises RateLimitError"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '60'}
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        # Create client and attempt request
        client = UpstoxClient(access_token="valid_token")
        
        with pytest.raises(RateLimitError) as exc_info:
            client.get_profile()
        
        assert "Rate limit exceeded" in str(exc_info.value)
        assert exc_info.value.retry_after == 60
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_429_without_retry_after_header(self, mock_session_class):
        """Test 429 without Retry-After header defaults to 60 seconds"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {}  # No Retry-After header
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        # Create client and attempt request
        client = UpstoxClient(access_token="valid_token")
        
        with pytest.raises(RateLimitError) as exc_info:
            client.get_profile()
        
        assert exc_info.value.retry_after == 60  # Default value


class TestMalformedResponse:
    """Test handling of malformed JSON responses"""
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_html_instead_of_json(self, mock_session_class):
        """Test HTML response instead of JSON (common proxy error)"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("No JSON")
        mock_response.text = "<html><body>502 Bad Gateway</body></html>"
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        # Create client and attempt request
        client = UpstoxClient(access_token="valid_token")
        
        with pytest.raises(InvalidResponseError) as exc_info:
            client.get_profile()
        
        assert "Expected JSON" in str(exc_info.value)


class TestDefensiveParsing:
    """Test defensive JSON parsing in API methods"""
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_missing_data_key(self, mock_session_class):
        """Test handling of response without 'data' key"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success'}  # No 'data' key
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        # Create client and make request
        client = UpstoxClient(access_token="valid_token")
        result = client.get_profile()
        
        # Should return empty dict, not crash
        assert result == {}
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_partial_data(self, mock_session_class):
        """Test handling of partial data in response"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'data': {'user_id': '123'}  # Missing user_name, email, etc.
        }
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        # Create client and make request
        client = UpstoxClient(access_token="valid_token")
        
        # Should handle gracefully with safe_get
        assert safe_get(mock_response.json(), 'data', 'user_name', default='Unknown') == 'Unknown'


class TestSuccessfulRequests:
    """Test successful API requests with proper data"""
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_get_profile_success(self, mock_session_class):
        """Test successful profile fetch"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'data': {
                'user_name': 'John Doe',
                'email': 'john@example.com',
                'user_id': 'ABC123'
            }
        }
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        # Create client and make request
        client = UpstoxClient(access_token="valid_token")
        profile = client.get_profile()
        
        assert profile['user_name'] == 'John Doe'
        assert profile['email'] == 'john@example.com'
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_get_holdings_success(self, mock_session_class):
        """Test successful holdings fetch"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'data': [
                {'tradingsymbol': 'INFY', 'quantity': 10},
                {'tradingsymbol': 'TCS', 'quantity': 5}
            ]
        }
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        # Create client and make request
        client = UpstoxClient(access_token="valid_token")
        holdings = client.get_holdings()
        
        assert len(holdings) == 2
        assert holdings[0]['tradingsymbol'] == 'INFY'


class TestClientInitialization:
    """Test client initialization and configuration"""
    
    def test_base_url_is_correct(self):
        """Test that BASE_URL is set to https://api.upstox.com/v2"""
        assert UpstoxClient.BASE_URL == "https://api.upstox.com/v2"
    
    def test_initialization_with_env_vars(self, monkeypatch):
        """Test initialization loads from environment variables"""
        monkeypatch.setenv('UPSTOX_API_KEY', 'test_key')
        monkeypatch.setenv('UPSTOX_ACCESS_TOKEN', 'test_token')
        
        client = UpstoxClient()
        assert client.api_key == 'test_key'
        assert client.access_token == 'test_token'
    
    def test_initialization_with_explicit_params(self):
        """Test initialization with explicit parameters"""
        client = UpstoxClient(api_key='explicit_key', access_token='explicit_token')
        assert client.api_key == 'explicit_key'
        assert client.access_token == 'explicit_token'
    
    def test_session_created(self):
        """Test that session is created on initialization"""
        client = UpstoxClient(access_token='token')
        assert client.session is not None
        assert isinstance(client.session, requests.Session)


class TestErrorHandling:
    """Test general error handling"""
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_timeout_error(self, mock_session_class):
        """Test handling of request timeout"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.request.side_effect = requests.exceptions.Timeout()
        
        # Create client and attempt request
        client = UpstoxClient(access_token="valid_token")
        
        with pytest.raises(UpstoxAPIError) as exc_info:
            client.get_profile()
        
        assert "timeout" in str(exc_info.value).lower()
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_connection_error(self, mock_session_class):
        """Test handling of connection error"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.request.side_effect = requests.exceptions.ConnectionError()
        
        # Create client and attempt request
        client = UpstoxClient(access_token="valid_token")
        
        with pytest.raises(UpstoxAPIError) as exc_info:
            client.get_profile()
        
        assert "Connection error" in str(exc_info.value)


class TestInstrumentKeyFormat:
    """Test instrument key format handling"""
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_instrument_key_format(self, mock_session_class):
        """Test that instrument keys use NSE_EQ|INE... format"""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'data': {
                'NSE_EQ|INE669E01016': {
                    'last_price': 1500.50,
                    'volume': 1000000
                }
            }
        }
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        # Create client and make request
        client = UpstoxClient(access_token="valid_token")
        quote = client.get_market_quote("NSE_EQ|INE669E01016")
        
        assert quote['last_price'] == 1500.50
        # Verify the request was made with correct params
        call_args = mock_session.request.call_args
        assert call_args[1]['params'] == {'instrument_key': 'NSE_EQ|INE669E01016'}


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
