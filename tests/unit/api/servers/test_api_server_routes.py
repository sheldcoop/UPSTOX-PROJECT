"""
Unit tests for API Server Routes
"""

import pytest
import os
import sys
import json
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Fix import path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.api.servers.api_server import app, get_db_connection

@pytest.fixture
def mock_db_path():
    db_file = "test_api_server.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    yield db_file
    if os.path.exists(db_file):
        os.remove(db_file)

@pytest.fixture
def init_db(mock_db_path):
    conn = sqlite3.connect(mock_db_path)
    
    # Create necessary tables
    conn.execute("""
        CREATE TABLE IF NOT EXISTS paper_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT, side TEXT, quantity INTEGER, order_type TEXT, 
            price REAL, status TEXT, created_at DATETIME, executed_at DATETIME
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alert_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT, alert_type TEXT, threshold REAL, priority TEXT,
            is_active INTEGER, created_at DATETIME, triggered_at DATETIME
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS paper_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT, quantity INTEGER, average_price REAL, updated_at DATETIME
        )
    """)
    conn.commit()
    conn.close()
    return mock_db_path

@pytest.fixture
def client(init_db):
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for testing
    
    # Patch the DB_PATH global in the module
    # We also need to patch get_db_connection to use our mock_db_path
    
    def mock_get_db():
        conn = sqlite3.connect(init_db)
        conn.row_factory = sqlite3.Row
        return conn

    with patch('backend.api.servers.api_server.DB_PATH', init_db):
        with patch('backend.api.servers.api_server.get_db_connection', side_effect=mock_get_db):
             with app.test_client() as client:
                yield client

class TestAPIRoutes:
    """Test API Server Endpoints"""

    @patch('backend.utils.auth.manager.AuthManager')
    @patch('backend.api.servers.api_server.requests.get')
    def test_get_portfolio_authenticated(self, mock_get, mock_auth_cls, client):
        """Test portfolio endpoint with valid Upstox token"""
        # Mock Auth
        mock_auth = mock_auth_cls.return_value
        mock_auth.get_valid_token.return_value = "ACCESS_TOKEN"
        
        # Mock Upstox Responses
        mock_profile = Mock()
        mock_profile.status_code = 200
        
        mock_holdings = Mock()
        mock_holdings.status_code = 200
        mock_holdings.json.return_value = {"data": [{"symbol": "INFY"}]}
        
        mock_funds = Mock()
        mock_funds.status_code = 200
        mock_funds.json.return_value = {
            "data": {"equity": {"available_margin": 50000, "used_margin": 10000}}
        }
        
        mock_get.side_effect = [mock_profile, mock_holdings, mock_funds]
        
        response = client.get('/api/portfolio')
        data = response.get_json()
        
        assert response.status_code == 200
        assert data['authenticated'] is True
        assert data['cash_available'] == 50000
        assert data['positions_count'] == 1

    @patch('backend.api.servers.api_server.PaperTradingSystem')
    def test_place_order_validation(self, mock_paper_cls, client):
        """Test order placement validation"""
        # Msg missing 'symbol'
        payload = {
            "side": "BUY",
            "quantity": 10,
            "order_type": "MARKET"
        }
        
        response = client.post('/api/orders', json=payload)
        assert response.status_code == 400
        assert "Missing required field: symbol" in response.get_json()['error']

    @patch('backend.api.servers.api_server.PaperTradingSystem')
    def test_place_order_success(self, mock_paper_cls, client):
        """Test successful order placement via paper trading"""
        mock_paper = mock_paper_cls.return_value
        mock_paper.place_order.return_value = {"id": 123, "status": "PENDING"}
        
        payload = {
            "symbol": "TCS",
            "side": "BUY",
            "quantity": 10,
            "order_type": "MARKET"
        }
        
        response = client.post('/api/orders', json=payload)
        assert response.status_code == 201
        assert response.get_json()['id'] == 123

    def test_alert_crud(self, client):
        """Test Create, Read, Delete Alerts"""
        
        # 1. Create Alert
        payload = {
            "symbol": "RELIANCE",
            "alert_type": "PRICE_ABOVE",
            "threshold": 2500
        }
        resp = client.post('/api/alerts', json=payload)
        assert resp.status_code == 201
        alert_id = resp.get_json()['id']
        
        # 2. Get Alerts
        resp = client.get('/api/alerts')
        alerts = resp.get_json()
        assert len(alerts) == 1
        assert alerts[0]['symbol'] == "RELIANCE"
        
        # 3. Delete Alert
        resp = client.delete(f'/api/alerts/{alert_id}')
        assert resp.status_code == 200
        
        # 4. Verify Deleted
        resp = client.get('/api/alerts')
        assert len(resp.get_json()) == 0

    @patch('backend.api.servers.api_server.PerformanceAnalytics')
    def test_get_performance(self, mock_analytics_cls, client):
        """Test performance endpoint"""
        mock_analytics = mock_analytics_cls.return_value
        mock_analytics.get_comprehensive_report.return_value = {
            'total_trades': 100,
            'win_rate': 60.5
        }
        
        response = client.get('/api/performance')
        data = response.get_json()
        
        assert response.status_code == 200
        assert data['total_trades'] == 100
        assert data['win_rate'] == 60.5
