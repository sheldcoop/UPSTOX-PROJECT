"""
Comprehensive WebSocket Tests

Tests WebSocket V3 functionality:
- Connection establishment
- Data streaming
- Reconnection logic
- Error handling
- Health monitoring
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import json
import time
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.services.streaming.websocket_v3_streamer import WebSocketV3Streamer


class TestWebSocketConnection:
    """Test WebSocket connection establishment"""
    
    @patch('backend.services.streaming.websocket_v3_streamer.requests.Session')
    @patch('backend.services.streaming.websocket_v3_streamer.AuthManager')
    def test_websocket_initialization(self, mock_auth, mock_session):
        """Test WebSocket streamer initializes correctly"""
        ws = WebSocketV3Streamer()
        
        assert ws is not None
        assert ws.connected == False
        assert ws.ws_url is None
        assert ws.subscribed_symbols == []
        assert ws.total_messages_received == 0
    
    @patch('backend.services.streaming.websocket_v3_streamer.requests.Session')
    @patch('backend.services.streaming.websocket_v3_streamer.AuthManager')
    def test_authorize_v3_success(self, mock_auth, mock_session_class):
        """Test v3 authorization succeeds"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'data': {
                'authorized_redirect_uri': 'wss://feed.upstox.com/v3/market-data-feed'
            }
        }
        mock_session.get.return_value = mock_response
        
        # Mock auth manager
        mock_auth_instance = MagicMock()
        mock_auth_instance.get_valid_token.return_value = "test_token"
        mock_auth.return_value = mock_auth_instance
        
        ws = WebSocketV3Streamer()
        auth_data = ws.authorize_v3()
        
        assert 'authorized_redirect_uri' in auth_data
        assert ws.ws_url == 'wss://feed.upstox.com/v3/market-data-feed'
    
    @patch('backend.services.streaming.websocket_v3_streamer.requests.Session')
    @patch('backend.services.streaming.websocket_v3_streamer.AuthManager')
    def test_authorize_v3_failure(self, mock_auth, mock_session_class):
        """Test v3 authorization handles failure"""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("Unauthorized")
        mock_session.get.return_value = mock_response
        
        # Mock auth manager
        mock_auth_instance = MagicMock()
        mock_auth_instance.get_valid_token.return_value = "test_token"
        mock_auth.return_value = mock_auth_instance
        
        ws = WebSocketV3Streamer()
        
        with pytest.raises(Exception):
            ws.authorize_v3()


class TestWebSocketSubscription:
    """Test WebSocket subscription mechanism"""
    
    @patch('backend.services.streaming.websocket_v3_streamer.websocket.WebSocketApp')
    @patch('backend.services.streaming.websocket_v3_streamer.requests.Session')
    @patch('backend.services.streaming.websocket_v3_streamer.AuthManager')
    def test_subscribe_instruments(self, mock_auth, mock_session, mock_ws_app):
        """Test subscribing to instruments"""
        # Mock WebSocket
        mock_ws_instance = MagicMock()
        mock_ws_app.return_value = mock_ws_instance
        
        # Mock auth manager
        mock_auth_instance = MagicMock()
        mock_auth_instance.get_valid_token.return_value = "test_token"
        mock_auth.return_value = mock_auth_instance
        
        ws = WebSocketV3Streamer()
        ws.connected = True
        ws.ws = mock_ws_instance
        
        # Subscribe
        instrument_keys = ['NSE_EQ|INE009A01021', 'NSE_EQ|INE669E01016']
        result = ws.subscribe(instrument_keys)
        
        assert result == True
        assert len(ws.subscribed_symbols) == 2
        
        # Verify send was called
        mock_ws_instance.send.assert_called_once()
        
        # Verify message format
        call_args = mock_ws_instance.send.call_args[0][0]
        message = json.loads(call_args)
        assert message['method'] == 'sub'
        assert message['data']['instrumentKeys'] == instrument_keys
    
    @patch('backend.services.streaming.websocket_v3_streamer.requests.Session')
    @patch('backend.services.streaming.websocket_v3_streamer.AuthManager')
    def test_subscribe_not_connected(self, mock_auth, mock_session):
        """Test subscribe fails when not connected"""
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        
        ws = WebSocketV3Streamer()
        ws.connected = False
        
        result = ws.subscribe(['NSE_EQ|INE009A01021'])
        
        assert result == False
    
    @patch('backend.services.streaming.websocket_v3_streamer.websocket.WebSocketApp')
    @patch('backend.services.streaming.websocket_v3_streamer.requests.Session')
    @patch('backend.services.streaming.websocket_v3_streamer.AuthManager')
    def test_unsubscribe_instruments(self, mock_auth, mock_session, mock_ws_app):
        """Test unsubscribing from instruments"""
        mock_ws_instance = MagicMock()
        mock_ws_app.return_value = mock_ws_instance
        
        mock_auth_instance = MagicMock()
        mock_auth_instance.get_valid_token.return_value = "test_token"
        mock_auth.return_value = mock_auth_instance
        
        ws = WebSocketV3Streamer()
        ws.connected = True
        ws.ws = mock_ws_instance
        ws.subscribed_symbols = ['NSE_EQ|INE009A01021', 'NSE_EQ|INE669E01016']
        
        # Unsubscribe
        result = ws.unsubscribe(['NSE_EQ|INE009A01021'])
        
        assert result == True
        assert len(ws.subscribed_symbols) == 1
        assert 'NSE_EQ|INE669E01016' in ws.subscribed_symbols
        
        # Verify unsub message sent
        call_args = mock_ws_instance.send.call_args[0][0]
        message = json.loads(call_args)
        assert message['method'] == 'unsub'


class TestWebSocketDataProcessing:
    """Test WebSocket data processing"""
    
    @patch('backend.services.streaming.websocket_v3_streamer.requests.Session')
    @patch('backend.services.streaming.websocket_v3_streamer.AuthManager')
    def test_process_tick_data(self, mock_auth, mock_session):
        """Test processing incoming tick data"""
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        
        ws = WebSocketV3Streamer()
        
        # Mock database connection
        ws.db_pool = MagicMock()
        mock_conn = MagicMock()
        ws.db_pool.get_connection.return_value.__enter__.return_value = mock_conn
        
        # Process tick data
        tick_data = {
            'feeds': {
                'NSE_EQ|INE009A01021': {
                    'ltp': 18500.50,
                    'volume': 1000,
                    'oi': 500,
                    'bid_price': 18500.00,
                    'ask_price': 18501.00,
                    'high': 18600.00,
                    'low': 18400.00,
                }
            }
        }
        
        ws._process_tick_data(tick_data)
        
        # Verify database insert was called
        mock_conn.execute.assert_called_once()
    
    @patch('backend.services.streaming.websocket_v3_streamer.requests.Session')
    @patch('backend.services.streaming.websocket_v3_streamer.AuthManager')
    def test_on_message_handler(self, mock_auth, mock_session):
        """Test _on_message handler processes messages correctly"""
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        
        ws = WebSocketV3Streamer()
        ws.db_pool = MagicMock()
        
        # Simulate message
        message_data = {
            'feeds': {
                'NSE_EQ|INE009A01021': {'ltp': 18500.50}
            }
        }
        message_str = json.dumps(message_data)
        
        ws._on_message(None, message_str)
        
        assert ws.total_messages_received == 1
        assert ws.last_message_time is not None


class TestWebSocketReconnection:
    """Test WebSocket reconnection logic"""
    
    @patch('backend.services.streaming.websocket_v3_streamer.requests.Session')
    @patch('backend.services.streaming.websocket_v3_streamer.AuthManager')
    def test_on_open_handler(self, mock_auth, mock_session):
        """Test _on_open sets connection state correctly"""
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        
        ws = WebSocketV3Streamer()
        ws._on_open(None)
        
        assert ws.connected == True
        assert ws.connection_start_time is not None
        assert ws.reconnect_attempts == 0
    
    @patch('backend.services.streaming.websocket_v3_streamer.requests.Session')
    @patch('backend.services.streaming.websocket_v3_streamer.AuthManager')
    def test_on_close_handler(self, mock_auth, mock_session):
        """Test _on_close sets disconnection state"""
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        
        ws = WebSocketV3Streamer()
        ws.connected = True
        ws.connection_start_time = datetime.now()
        ws.db_pool = MagicMock()
        
        ws._on_close(None, 1000, "Normal closure")
        
        assert ws.connected == False
    
    @patch('backend.services.streaming.websocket_v3_streamer.requests.Session')
    @patch('backend.services.streaming.websocket_v3_streamer.AuthManager')
    def test_on_error_handler(self, mock_auth, mock_session):
        """Test _on_error logs errors"""
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        
        ws = WebSocketV3Streamer()
        
        # Should not raise exception
        ws._on_error(None, "Test error")
        
        # Health status should still be accessible
        status = ws.get_health_status()
        assert isinstance(status, dict)


class TestWebSocketHealthMonitoring:
    """Test WebSocket health monitoring"""
    
    @patch('backend.services.streaming.websocket_v3_streamer.requests.Session')
    @patch('backend.services.streaming.websocket_v3_streamer.AuthManager')
    def test_get_health_status(self, mock_auth, mock_session):
        """Test health status returns correct metrics"""
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        
        ws = WebSocketV3Streamer()
        ws.connected = True
        ws.connection_start_time = datetime.now()
        ws.total_messages_received = 100
        ws.last_message_time = datetime.now()
        ws.subscribed_symbols = ['NSE_EQ|INE009A01021']
        
        status = ws.get_health_status()
        
        assert status['connected'] == True
        assert status['messages_received'] == 100
        assert status['subscribed_count'] == 1
        assert 'uptime_seconds' in status
        assert 'last_message_ago_seconds' in status
        assert 'timestamp' in status
    
    @patch('backend.services.streaming.websocket_v3_streamer.requests.Session')
    @patch('backend.services.streaming.websocket_v3_streamer.AuthManager')
    def test_update_health_status(self, mock_auth, mock_session):
        """Test health status updates correctly"""
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        
        ws = WebSocketV3Streamer()
        ws.connected = False
        
        ws._update_health_status()
        
        assert ws.health_status['connected'] == False
        assert ws.health_status['uptime_seconds'] == 0


class TestWebSocketDisconnection:
    """Test WebSocket disconnection"""
    
    @patch('backend.services.streaming.websocket_v3_streamer.requests.Session')
    @patch('backend.services.streaming.websocket_v3_streamer.AuthManager')
    def test_disconnect(self, mock_auth, mock_session):
        """Test disconnect closes WebSocket"""
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        
        ws = WebSocketV3Streamer()
        ws.ws = MagicMock()
        ws.connected = True
        
        ws.disconnect()
        
        ws.ws.close.assert_called_once()
        assert ws.connected == False


class TestWebSocketMetricsPersistence:
    """Test WebSocket metrics persistence"""
    
    @patch('backend.services.streaming.websocket_v3_streamer.requests.Session')
    @patch('backend.services.streaming.websocket_v3_streamer.AuthManager')
    def test_save_connection_metrics(self, mock_auth, mock_session):
        """Test connection metrics are saved to database"""
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        
        ws = WebSocketV3Streamer()
        ws.connection_start_time = datetime.now()
        ws.total_messages_received = 500
        ws.reconnect_attempts = 2
        
        # Mock database
        ws.db_pool = MagicMock()
        mock_conn = MagicMock()
        ws.db_pool.get_connection.return_value.__enter__.return_value = mock_conn
        
        ws._save_connection_metrics("Test disconnect")
        
        # Verify metrics were saved
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        assert 'websocket_metrics' in call_args[0]
    
    @patch('backend.services.streaming.websocket_v3_streamer.requests.Session')
    @patch('backend.services.streaming.websocket_v3_streamer.AuthManager')
    def test_save_tick(self, mock_auth, mock_session):
        """Test tick data is saved to database"""
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        
        ws = WebSocketV3Streamer()
        
        # Mock database
        ws.db_pool = MagicMock()
        mock_conn = MagicMock()
        ws.db_pool.get_connection.return_value.__enter__.return_value = mock_conn
        
        tick_data = {
            'ltp': 18500.50,
            'volume': 1000,
            'bid_price': 18500.00,
            'ask_price': 18501.00,
        }
        
        ws._save_tick('NSE_EQ|INE009A01021', tick_data)
        
        # Verify tick was saved
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        assert 'websocket_ticks_v3' in call_args[0]


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
