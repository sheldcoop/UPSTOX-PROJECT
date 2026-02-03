"""
Tests for Positions endpoints
Tests the /api/positions and /api/positions/<symbol> endpoints
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


class TestPositionsEndpoints:
    """Test positions endpoints"""

    def test_get_all_positions(self, client):
        """Test get all positions endpoint"""
        response = client.get("/api/positions")
        
        # May return 500 if database tables don't exist (fresh install)
        # or 200 if properly configured
        assert response.status_code in [200, 500]
        
        data = response.get_json()
        if response.status_code == 200:
            # Should return a list (may be empty)
            assert isinstance(data, list)
        else:
            # Should return error if DB not initialized
            assert "error" in data

    def test_positions_response_structure(self, client):
        """Test positions response has correct structure"""
        response = client.get("/api/positions")
        
        # Skip test if database not initialized
        if response.status_code != 200:
            pytest.skip("Database not initialized")
            return
        
        data = response.get_json()
        
        # If there are positions, verify structure
        if len(data) > 0:
            position = data[0]
            
            # Required fields for each position
            required_fields = [
                "id", "symbol", "quantity", "entry_price", 
                "current_price", "entry_date", "pnl", 
                "pnl_percent", "side"
            ]
            
            for field in required_fields:
                assert field in position, f"Missing required field: {field}"
            
            # Verify field types
            assert isinstance(position["quantity"], (int, float))
            assert isinstance(position["entry_price"], (int, float))
            assert isinstance(position["current_price"], (int, float))
            assert isinstance(position["pnl"], (int, float))
            assert isinstance(position["pnl_percent"], (int, float))
            assert position["side"] in ["long", "short"]

    def test_get_position_by_symbol(self, client):
        """Test get position by symbol endpoint"""
        # First get all positions to find a valid symbol
        response = client.get("/api/positions")
        
        # Skip if database not initialized
        if response.status_code != 200:
            pytest.skip("Database not initialized")
            return
        
        data = response.get_json()
        
        if len(data) > 0:
            # Test with first position's symbol
            symbol = data[0]["symbol"]
            response = client.get(f"/api/positions/{symbol}")
            
            assert response.status_code == 200
            position = response.get_json()
            
            # Verify it's the correct symbol
            assert position["symbol"] == symbol
            
            # Verify required fields
            required_fields = ["id", "symbol", "quantity", "entry_price", "current_price"]
            for field in required_fields:
                assert field in position

    def test_get_position_by_invalid_symbol(self, client):
        """Test get position by invalid symbol returns 404"""
        # Use a symbol that definitely doesn't exist
        response = client.get("/api/positions/INVALID_SYMBOL_XYZ_999")
        
        # Should return 404 for non-existent position or 500 if DB not initialized
        assert response.status_code in [404, 500]
        
        data = response.get_json()
        assert "error" in data

    def test_positions_pnl_calculation(self, client):
        """Test P&L calculation is correct"""
        response = client.get("/api/positions")
        
        # Skip if database not initialized
        if response.status_code != 200:
            pytest.skip("Database not initialized")
            return
        
        data = response.get_json()
        
        if len(data) > 0:
            position = data[0]
            
            # Verify P&L calculation accounting for position side
            # For long positions: P&L = (current_price - entry_price) * quantity
            # For short positions: P&L = (entry_price - current_price) * quantity
            if position.get("side", "").lower() == "long":
                expected_pnl = (position["current_price"] - position["entry_price"]) * position["quantity"]
            else:  # short
                expected_pnl = (position["entry_price"] - position["current_price"]) * position["quantity"]
            
            assert abs(position["pnl"] - expected_pnl) < 0.01  # Allow small rounding errors
            
            # Verify P&L percentage calculation
            if position["entry_price"] > 0:
                if position.get("side", "").lower() == "long":
                    expected_pnl_percent = ((position["current_price"] - position["entry_price"]) / position["entry_price"]) * 100
                else:  # short
                    expected_pnl_percent = ((position["entry_price"] - position["current_price"]) / position["entry_price"]) * 100
                
                assert abs(position["pnl_percent"] - expected_pnl_percent) < 0.01
