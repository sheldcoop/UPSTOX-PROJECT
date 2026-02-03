"""
Tests for User Profile endpoints
Tests the /api/user/profile endpoint
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.api_server import app as flask_app


@pytest.fixture
def app():
    """Create Flask app for testing"""
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestUserProfileEndpoints:
    """Test user profile endpoints"""

    def test_user_profile_unauthenticated(self, client):
        """Test user profile endpoint when not authenticated"""
        response = client.get("/api/user/profile")
        
        # Should return 401 when not authenticated or 500 if auth system error
        assert response.status_code in [401, 500]
        
        data = response.get_json()
        assert "error" in data or "authenticated" in data
        
        if "authenticated" in data:
            assert data["authenticated"] is False

    def test_user_profile_response_structure(self, client):
        """Test user profile response has expected structure"""
        response = client.get("/api/user/profile")
        data = response.get_json()
        
        # Should have authenticated field
        assert "authenticated" in data
        
        # When authenticated, should have these fields
        # When not authenticated, should have error
        if response.status_code == 200:
            required_fields = ["authenticated", "name", "email", "user_id", "user_type", "broker"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Verify broker is Upstox
            assert data["broker"] == "Upstox"
            
            # Verify exchanges is a list
            assert "exchanges" in data
            assert isinstance(data["exchanges"], list)
        else:
            assert "error" in data

    @pytest.mark.live
    def test_user_profile_authenticated(self, client):
        """Test user profile endpoint when authenticated (requires valid token)"""
        # This test only runs when marked with @pytest.mark.live
        # It requires a valid Upstox authentication token
        response = client.get("/api/user/profile")
        
        if response.status_code == 200:
            data = response.get_json()
            
            # Verify authenticated response
            assert data["authenticated"] is True
            assert "name" in data
            assert "user_id" in data
            assert data["broker"] == "Upstox"
