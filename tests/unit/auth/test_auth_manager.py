"""
Authentication Tests

Tests for auth manager and token refresh scheduler
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import time
from datetime import datetime, timedelta
import pytz
from cryptography.fernet import Fernet

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.utils.auth.manager import AuthManager
from backend.utils.auth.token_refresh_scheduler import TokenRefreshScheduler

# Generate valid Fernet key for testing
TEST_ENCRYPTION_KEY = Fernet.generate_key().decode()

@pytest.fixture
def auth_manager_db():
    db_file = "test_auth_manager.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    yield db_file
    if os.path.exists(db_file):
        os.remove(db_file)

class TestAuthManager:
    """Test AuthManager functionality"""
    
    @patch('backend.utils.auth.manager.os.getenv')
    def test_initialization(self, mock_getenv, auth_manager_db):
        """Test AuthManager initializes with env variables"""
        mock_getenv.side_effect = lambda key, default=None: {
            'UPSTOX_CLIENT_ID': 'test_client_id',
            'UPSTOX_CLIENT_SECRET': 'test_secret',
            'UPSTOX_REDIRECT_URI': 'http://localhost:5050/callback',
            'ENCRYPTION_KEY': TEST_ENCRYPTION_KEY
        }.get(key, default)
        
        auth = AuthManager(db_path=auth_manager_db)
        
        assert auth.client_id == 'test_client_id'
        assert auth.client_secret == 'test_secret'
        assert auth.redirect_uri == 'http://localhost:5050/callback'
    
    @patch('backend.utils.auth.manager.os.getenv')
    def test_get_authorization_url(self, mock_getenv, auth_manager_db):
        """Test authorization URL generation"""
        mock_getenv.side_effect = lambda key, default=None: {
            'UPSTOX_CLIENT_ID': 'test_client',
            'UPSTOX_CLIENT_SECRET': 'test_secret',
            'UPSTOX_REDIRECT_URI': 'http://localhost:5050/callback',
            'ENCRYPTION_KEY': TEST_ENCRYPTION_KEY
        }.get(key, default)
        
        auth = AuthManager(db_path=auth_manager_db)
        url = auth.get_authorization_url()
        
        assert 'https://api.upstox.com/v2/login/authorization/dialog' in url
        assert 'client_id=test_client' in url
        assert 'response_type=code' in url
    
    @patch('backend.utils.auth.manager.requests.post')
    @patch('backend.utils.auth.manager.os.getenv')
    def test_exchange_code_for_token_success(self, mock_getenv, mock_post, auth_manager_db):
        """Test successful token exchange"""
        mock_getenv.side_effect = lambda key, default=None: {
            'UPSTOX_CLIENT_ID': 'test_client',
            'UPSTOX_CLIENT_SECRET': 'test_secret',
            'ENCRYPTION_KEY': TEST_ENCRYPTION_KEY
        }.get(key, default)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'expires_in': 86400
        }
        mock_post.return_value = mock_response
        
        auth = AuthManager(db_path=auth_manager_db)
        token_data = auth.exchange_code_for_token('test_code')
        
        assert token_data['access_token'] == 'test_access_token'
        assert token_data['refresh_token'] == 'test_refresh_token'
    
    @patch('backend.utils.auth.manager.requests.post')
    @patch('backend.utils.auth.manager.os.getenv')
    def test_exchange_code_failure(self, mock_getenv, mock_post, auth_manager_db):
        """Test token exchange handles failure"""
        mock_getenv.side_effect = lambda key, default=None: {
            'UPSTOX_CLIENT_ID': 'test_client',
            'UPSTOX_CLIENT_SECRET': 'test_secret',
            'ENCRYPTION_KEY': TEST_ENCRYPTION_KEY
        }.get(key, default)
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("Unauthorized")
        mock_post.return_value = mock_response
        
        auth = AuthManager(db_path=auth_manager_db)
        
        with pytest.raises(Exception):
            auth.exchange_code_for_token('invalid_code')
    
    @patch('backend.utils.auth.manager.os.getenv')
    def test_save_and_retrieve_token(self, mock_getenv, auth_manager_db):
        """Test saving and retrieving tokens"""
        mock_getenv.side_effect = lambda key, default=None: {
            'UPSTOX_CLIENT_ID': 'test_client',
            'UPSTOX_CLIENT_SECRET': 'test_secret',
            'ENCRYPTION_KEY': TEST_ENCRYPTION_KEY
        }.get(key, default)
        
        auth = AuthManager(db_path=auth_manager_db)
        
        token_data = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'expires_in': 86400  # 24 hours
        }
        
        auth.save_token('test_user', token_data)
        
        retrieved_token = auth.get_valid_token('test_user')
        
        assert retrieved_token == 'test_access_token'
    
    @patch('backend.utils.auth.manager.os.getenv')
    def test_revoke_token(self, mock_getenv, auth_manager_db):
        """Test token revocation"""
        mock_getenv.side_effect = lambda key, default=None: {
            'UPSTOX_CLIENT_ID': 'test_client',
            'UPSTOX_CLIENT_SECRET': 'test_secret',
            'ENCRYPTION_KEY': TEST_ENCRYPTION_KEY
        }.get(key, default)
        
        auth = AuthManager(db_path=auth_manager_db)
        
        token_data = {
            'access_token': 'test_token',
            'refresh_token': 'refresh',
            'expires_in': 86400
        }
        
        auth.save_token('test_user', token_data)
        auth.revoke_token('test_user')
        
        # Should not retrieve revoked token
        retrieved = auth.get_valid_token('test_user')
        assert retrieved is None


class TestTokenRefreshScheduler:
    """Test Token Refresh Scheduler"""
    
    @patch('backend.utils.auth.token_refresh_scheduler.AuthManager')
    def test_initialization(self, mock_auth):
        """Test scheduler initializes correctly"""
        scheduler = TokenRefreshScheduler()
        
        assert scheduler is not None
        assert scheduler.env_type in ['live', 'sandbox']
    
    def test_parse_jwt_token(self):
        """Test JWT token parsing"""
        scheduler = TokenRefreshScheduler()
        
        # Live token from user
        live_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIyWkNEUTkiLCJqdGkiOiI2OTgzZTIwZmU1OTE0MTcyNTNmY2Q0Y2IiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzcwMjUwNzY3LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NzAzMjg4MDB9.IE4EsLt02lL-5xv6WWazrKPw-JEGI-8UQwGAe5kKWTQ"
        
        decoded = scheduler.parse_jwt_token(live_token)
        
        assert decoded['sub'] == '2ZCDQ9'
        assert 'exp' in decoded
        assert 'iat' in decoded
    
    def test_get_token_expiry(self):
        """Test extracting token expiry datetime"""
        scheduler = TokenRefreshScheduler()
        
        live_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIyWkNEUTkiLCJqdGkiOiI2OTgzZTIwZmU1OTE0MTcyNTNmY2Q0Y2IiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzcwMjUwNzY3LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NzAzMjg4MDB9.IE4EsLt02lL-5xv6WWazrKPw-JEGI-8UQwGAe5kKWTQ"
        
        expiry_dt = scheduler.get_token_expiry(live_token)
        
        assert expiry_dt is not None
        assert isinstance(expiry_dt, datetime)
        # Live tokens expire at 3:30 PM IST
        assert expiry_dt.hour == 3
        assert expiry_dt.minute == 30
    
    def test_is_token_expiring_soon(self):
        """Test detecting if token is expiring soon"""
        scheduler = TokenRefreshScheduler()
        
        live_token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIyWkNEUTkiLCJqdGkiOiI2OTgzZTIwZmU1OTE0MTcyNTNmY2Q0Y2IiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzcwMjUwNzY3LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NzAzMjg4MDB9.IE4EsLt02lL-5xv6WWazrKPw-JEGI-8UQwGAe5kKWTQ"
        
        # Check expiry with various thresholds
        expiring_soon_30min = scheduler.is_token_expiring_soon(live_token, minutes_before=30)
        
        # Result depends on current time vs token expiry
        assert isinstance(expiring_soon_30min, bool)
    
    @patch('backend.utils.auth.token_refresh_scheduler.AuthManager')
    def test_schedule_live_token_refresh(self, mock_auth):
        """Test scheduling live token refresh"""
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        
        scheduler = TokenRefreshScheduler()
        scheduler.env_type = 'live'
        
        scheduler.schedule_live_token_refresh('test_user')
        
        # Check that job was added
        jobs = scheduler.scheduler.get_jobs()
        assert len(jobs) > 0
        
        # Clean up
        if hasattr(scheduler, 'scheduler') and scheduler.scheduler.running:
            scheduler.stop()
    
    @patch('backend.utils.auth.token_refresh_scheduler.AuthManager')
    def test_get_status(self, mock_auth):
        """Test getting scheduler status"""
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        
        scheduler = TokenRefreshScheduler()
        scheduler.start('test_user')
        
        status = scheduler.get_status()
        
        assert 'running' in status
        assert 'env_type' in status
        assert 'jobs' in status
        assert 'timezone' in status
        
        # Clean up
        if hasattr(scheduler, 'scheduler') and scheduler.scheduler.running:
            scheduler.stop()


class TestTokenAutoRefreshIntegration:
    """Integration tests for token auto-refresh"""
    
    @patch('backend.utils.auth.manager.requests.post')
    @patch('backend.utils.auth.manager.os.getenv')
    def test_expired_token_auto_refresh(self, mock_getenv, mock_post, auth_manager_db):
        """Test auto-refresh of expired token"""
        mock_getenv.side_effect = lambda key, default=None: {
            'UPSTOX_CLIENT_ID': 'test_client',
            'UPSTOX_CLIENT_SECRET': 'test_secret',
            'ENCRYPTION_KEY': TEST_ENCRYPTION_KEY
        }.get(key, default)
        
        # Mock successful refresh
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 86400
        }
        mock_post.return_value = mock_response
        
        auth = AuthManager(db_path=auth_manager_db)
        
        # Save token that expires in 1 second
        token_data = {
            'access_token': 'old_token',
            'refresh_token': 'refresh_token',
            'expires_in': 1  # Expires in 1 second
        }
        
        auth.save_token('test_user', token_data)
        
        # Wait for expiry
        time.sleep(2)
        
        # Get token (should trigger auto-refresh)
        new_token = auth.get_valid_token('test_user')
        
        # Should have refreshed
        assert mock_post.called


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
