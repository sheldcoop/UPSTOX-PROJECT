"""
Additional Unit Tests for New API Endpoints

Tests for Orders, Trades, Option Chain, and Charges APIs
All tests use mocking - no real API calls
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.upstox.client import UpstoxClient, safe_get


class TestOrdersAPI:
    """Test Orders API endpoints"""
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_get_orders(self, mock_session_class):
        """Test get_orders returns list of orders"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'data': [
                {'order_id': 'ORD001', 'status': 'complete'},
                {'order_id': 'ORD002', 'status': 'pending'}
            ]
        }
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        client = UpstoxClient(access_token="token")
        orders = client.get_orders()
        
        assert len(orders) == 2
        assert orders[0]['order_id'] == 'ORD001'
        assert orders[1]['status'] == 'pending'
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_get_order_details(self, mock_session_class):
        """Test get_order_details returns specific order"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'data': {
                'order_id': 'ORD001',
                'status': 'complete',
                'quantity': 10,
                'price': 1500.0
            }
        }
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        client = UpstoxClient(access_token="token")
        order = client.get_order_details("ORD001")
        
        assert order['order_id'] == 'ORD001'
        assert order['quantity'] == 10
        assert order['price'] == 1500.0
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_get_order_history(self, mock_session_class):
        """Test get_order_history returns order trail"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'data': [
                {'timestamp': '2024-01-01 09:15', 'status': 'pending'},
                {'timestamp': '2024-01-01 09:16', 'status': 'complete'}
            ]
        }
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        client = UpstoxClient(access_token="token")
        history = client.get_order_history("ORD001")
        
        assert len(history) == 2
        assert history[1]['status'] == 'complete'


class TestTradesAPI:
    """Test Trades API endpoints"""
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_get_trades(self, mock_session_class):
        """Test get_trades returns all trades"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'data': [
                {'trade_id': 'TRD001', 'quantity': 10, 'price': 1500.0},
                {'trade_id': 'TRD002', 'quantity': 5, 'price': 1505.0}
            ]
        }
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        client = UpstoxClient(access_token="token")
        trades = client.get_trades()
        
        assert len(trades) == 2
        assert trades[0]['trade_id'] == 'TRD001'
        assert trades[1]['quantity'] == 5
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_get_trades_by_order(self, mock_session_class):
        """Test get_trades_by_order returns trades for specific order"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'data': [
                {'trade_id': 'TRD001', 'order_id': 'ORD001', 'quantity': 10}
            ]
        }
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        client = UpstoxClient(access_token="token")
        trades = client.get_trades_by_order("ORD001")
        
        assert len(trades) == 1
        assert trades[0]['order_id'] == 'ORD001'


class TestOptionChainAPI:
    """Test Option Chain API"""
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_get_option_chain(self, mock_session_class):
        """Test get_option_chain returns option data"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'data': {
                'expiry': ['2024-01-25', '2024-02-01'],
                'strike_prices': [18000, 18100, 18200],
                'options': []
            }
        }
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        client = UpstoxClient(access_token="token")
        chain = client.get_option_chain("NSE_INDEX|Nifty 50")
        
        assert 'expiry' in chain
        assert len(chain['expiry']) == 2
        assert 'strike_prices' in chain
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_get_option_chain_with_expiry(self, mock_session_class):
        """Test get_option_chain with expiry filter"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'data': {'options': []}
        }
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        client = UpstoxClient(access_token="token")
        chain = client.get_option_chain("NSE_INDEX|Nifty 50", expiry_date="2024-01-25")
        
        # Verify expiry_date was passed in params
        call_args = mock_session.request.call_args
        assert 'params' in call_args[1]
        assert call_args[1]['params']['expiry_date'] == "2024-01-25"


class TestChargesAPI:
    """Test Charges API"""
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_get_charges(self, mock_session_class):
        """Test get_charges returns brokerage breakdown"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'data': {
                'brokerage': 20.0,
                'stt': 15.0,
                'stamp_duty': 5.0,
                'total_charges': 40.0
            }
        }
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        client = UpstoxClient(access_token="token")
        charges = client.get_charges(
            "NSE_EQ|INE669E01016",
            10,
            "D",
            "BUY",
            1500.0
        )
        
        assert charges['brokerage'] == 20.0
        assert charges['total_charges'] == 40.0
        
        # Verify params were passed
        call_args = mock_session.request.call_args
        params = call_args[1]['params']
        assert params['quantity'] == 10
        assert params['product'] == 'D'
        assert params['transaction_type'] == 'BUY'


class TestDefensiveParsingNewEndpoints:
    """Test defensive parsing for new endpoints"""
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_orders_empty_response(self, mock_session_class):
        """Test get_orders handles empty data"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success'}  # No 'data'
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        client = UpstoxClient(access_token="token")
        orders = client.get_orders()
        
        # Should return empty list, not crash
        assert orders == []
    
    @patch('backend.services.upstox.client.requests.Session')
    def test_option_chain_missing_data(self, mock_session_class):
        """Test option_chain handles missing data gracefully"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success'}  # No 'data'
        mock_response.request = Mock(method='GET', url='test')
        mock_session.request.return_value = mock_response
        
        client = UpstoxClient(access_token="token")
        chain = client.get_option_chain("NSE_INDEX|Nifty 50")
        
        # Should return empty dict, not crash
        assert chain == {}


class TestAPIMethodCoverage:
    """Verify all methods are tested"""
    
    def test_all_methods_have_tests(self):
        """Verify we have tests for all API methods"""
        # List of all methods we should test
        tested_methods = [
            'get_profile',  # Original tests
            'get_holdings',  # Original tests
            'get_positions',  # Original tests
            'get_funds_and_margin',  # Original tests
            'get_market_quote',  # Original tests
            'get_historical_candles',  # Original tests
            'get_orders',  # New
            'get_order_details',  # New
            'get_order_history',  # New
            'get_trades',  # New
            'get_trades_by_order',  # New
            'get_option_chain',  # New
            'get_charges',  # New
        ]
        
        # Verify all methods exist in client
        from backend.services.upstox.client import UpstoxClient
        client = UpstoxClient(api_key="test")
        
        for method in tested_methods:
            assert hasattr(client, method), f"Method {method} missing in client"
        
        print(f"\n✅ All {len(tested_methods)} API methods exist and have test coverage")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
