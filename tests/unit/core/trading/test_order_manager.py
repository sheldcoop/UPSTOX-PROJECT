"""
Unit tests for Order Management System
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Fix import path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.core.trading.order_manager import OrderManagerV3

@pytest.fixture
def test_db():
    db_file = "test_orders.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    yield db_file
    if os.path.exists(db_file):
        os.remove(db_file)

@pytest.fixture
def mock_session():
    with patch('requests.Session') as mock:
        yield mock.return_value

@pytest.fixture
def order_manager(test_db, mock_session):
    # Mock AuthManager to prevent env var checks or network calls during init
    with patch('backend.core.trading.order_manager.AuthManager'):
        om = OrderManagerV3(db_path=test_db)
        om.session = mock_session # Inject mock session
        return om

class TestOrderManagerV3:
    """Test OrderManagerV3 functionality"""

    def test_place_order_validation(self, order_manager):
        """Test input validation for place_order"""
        
        # Invalid Side
        with pytest.raises(ValueError, match="Side must be BUY or SELL"):
            order_manager.place_order("INFY", "HOLD", 1)

        # Invalid Method
        with pytest.raises(ValueError, match="Invalid order type"):
            order_manager.place_order("INFY", "BUY", 1, order_type="INVALID")
            
        # Limit without Price
        with pytest.raises(ValueError, match="Price required"):
            order_manager.place_order("INFY", "BUY", 1, order_type="LIMIT")

    def test_place_order_v3_success(self, order_manager, mock_session):
        """Test successful V3 order placement"""
        
        # Mock API Response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": {"order_id": "ORD_V3_123"}
        }
        mock_session.post.return_value = mock_response
        
        order_id = order_manager.place_order(
            symbol="TCS",
            side="BUY",
            quantity=10,
            order_type="MARKET",
            product_type="I"
        )
        
        assert order_id == "ORD_V3_123"
        
        # Verify V3 endpoint called
        args, _ = mock_session.post.call_args
        assert "/orders/v3/regular/create" in args[0]
        
        # Verify DB persistence
        with order_manager.db_pool.get_connection() as conn:
            cursor = conn.execute("SELECT order_id, api_version FROM orders_v3 WHERE order_id=?", (order_id,))
            row = cursor.fetchone()
            assert row[0] == "ORD_V3_123"
            assert row[1] == "v3"

    def test_place_order_v2_fallback(self, order_manager, mock_session):
        """Test fallback to V2 when V3 fails"""
        
        # Mock V3 Failure (e.g., 500 error) then V2 Success
        v3_fail = Mock()
        v3_fail.status_code = 500
        v3_fail.raise_for_status.side_effect = Exception("V3 Down")
        
        v2_success = Mock()
        v2_success.status_code = 200
        v2_success.json.return_value = {
            "status": "success", 
            "data": {"order_id": "ORD_V2_456"}
        }
        
        # Side effect: First call V3 (fail), Second call V2 (success)
        mock_session.post.side_effect = [v3_fail, v2_success]
        
        order_id = order_manager.place_order(
            symbol="RELIANCE",
            side="SELL",
            quantity=5
        )
        
        assert order_id == "ORD_V2_456"
        
        # Verify DB persistence says v2
        with order_manager.db_pool.get_connection() as conn:
            row = conn.execute("SELECT api_version FROM orders_v3 WHERE order_id=?", (order_id,)).fetchone()
            assert row[0] == "v2"

    def test_modify_order(self, order_manager, mock_session):
        """Test modify order logic"""
        mock_session.put.return_value.status_code = 200
        
        # Pre-seed DB
        with order_manager.db_pool.get_connection() as conn:
            conn.execute(
                "INSERT INTO orders_v3 (order_id, symbol, side, quantity, order_type) VALUES (?, ?, ?, ?, ?)",
                ("ORD_MOD", "ITC", "BUY", 100, "LIMIT")
            )
            
        success = order_manager.modify_order(
            order_id="ORD_MOD",
            quantity=50,
            price=250.0
        )
        
        assert success is True
        
        # Verify API called with modifications
        args, kwargs = mock_session.put.call_args
        payload = kwargs['json']
        assert payload['quantity'] == 50
        assert payload['price'] == 250.0
        assert payload['order_id'] == "ORD_MOD"

    def test_cancel_order(self, order_manager, mock_session):
        """Test cancel order logic"""
        mock_session.delete.return_value.status_code = 200
        
        # Pre-seed DB
        with order_manager.db_pool.get_connection() as conn:
            conn.execute(
                "INSERT INTO orders_v3 (order_id, symbol, side, quantity, order_type) VALUES (?, ?, ?, ?, ?)",
                ("ORD_CNCL", "SBIN", "BUY", 1000, "MARKET")
            )
            
        success = order_manager.cancel_order("ORD_CNCL")
        assert success is True
        
        # Verify API call
        args, _ = mock_session.delete.call_args
        assert "ORD_CNCL" in args[0]
        
        # Check DB status update
        with order_manager.db_pool.get_connection() as conn:
            row = conn.execute("SELECT order_status FROM orders_v3 WHERE order_id=?", ("ORD_CNCL",)).fetchone()
            assert row[0] == "CANCELLED"
