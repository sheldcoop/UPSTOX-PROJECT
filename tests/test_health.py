"""
Tests for Health Blueprint endpoints
Tests the health check API endpoint
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


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check(self, client):
        """Test health check endpoint returns proper status"""
        response = client.get("/api/health")
        assert response.status_code == 200

        data = response.get_json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert data["version"] == "1.0.0"

    def test_health_check_response_format(self, client):
        """Test health check response has correct format"""
        response = client.get("/api/health")
        data = response.get_json()

        # Verify required fields are present
        required_fields = ["status", "timestamp", "version"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_health_check_timestamp_format(self, client):
        """Test health check timestamp is in ISO format"""
        response = client.get("/api/health")
        data = response.get_json()

        # Verify timestamp is a valid ISO format string
        timestamp = data["timestamp"]
        assert isinstance(timestamp, str)
        # Should be able to parse as ISO format
        from datetime import datetime
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            pytest.fail(f"Timestamp {timestamp} is not valid ISO format")
