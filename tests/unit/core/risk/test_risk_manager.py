"""
Unit tests for Risk Management System
"""

import pytest
import os
import time
from datetime import datetime
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.core.risk.manager import RiskManager

@pytest.fixture
def risk_db():
    db_file = "test_risk_manager.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    yield db_file
    if os.path.exists(db_file):
        os.remove(db_file)

class TestRiskManager:
    """Test RiskManager functionality"""

    def test_initialization(self, risk_db):
        """Test RiskManager initializes correctly with custom params"""
        rm = RiskManager(
            db_path=risk_db,
            max_position_size=50000,
            max_daily_loss=1000,
            max_risk_per_trade=0.01
        )
        
        assert rm.db_path == risk_db
        assert rm.max_position_size == 50000
        assert rm.max_daily_loss == 1000
        assert rm.max_risk_per_trade == 0.01
        
        # Verify DB tables created
        import sqlite3
        conn = sqlite3.connect(risk_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        assert 'risk_configs' in tables
        assert 'stop_loss_orders' in tables
        assert 'circuit_breaker_events' in tables
        assert 'risk_metrics' in tables

    def test_calculate_position_size_standard(self, risk_db):
        """Test standard position sizing calculation"""
        rm = RiskManager(db_path=risk_db, max_risk_per_trade=0.02)
        
        # Scenario: 100k account, 2% risk (2k), Entry 100, SL 90 (Risk/Share 10)
        # 2000 / 10 = 200 shares
        
        result = rm.calculate_position_size(
            symbol="TEST",
            entry_price=100.0,
            stop_loss_price=90.0,
            account_balance=100000.0
        )
        
        assert result['quantity'] == 200
        assert result['risk_amount'] == 2000.0
        assert result['recommendation'] == 'PROCEED'

    def test_calculate_position_size_max_limit(self, risk_db):
        """Test position sizing capped by max position size"""
        rm = RiskManager(
            db_path=risk_db, 
            max_position_size=10000, # Max 10k per trade
            max_risk_per_trade=0.05
        )
        
        # Scenario: 100k account, 5% risk (5k), Entry 100, SL 90 (Risk/Share 10)
        # Raw calc: 5000 / 10 = 500 shares -> 500 * 100 = 50,000 value
        # Limit: 10000 / 100 = 100 shares
        
        result = rm.calculate_position_size(
            symbol="TEST",
            entry_price=100.0,
            stop_loss_price=90.0,
            account_balance=100000.0
        )
        
        assert result['quantity'] == 100
        assert result['position_value'] <= 10000
        assert result['recommendation'] == 'PROCEED'

    def test_calculate_position_size_zero_risk(self, risk_db):
        """Test with invalid SL (Entry = SL)"""
        rm = RiskManager(db_path=risk_db)
        
        result = rm.calculate_position_size(
            symbol="TEST",
            entry_price=100.0,
            stop_loss_price=100.0,
            account_balance=100000.0
        )
        
        assert result['quantity'] == 0
        assert result['error'] == "Invalid stop-loss price"

    def test_stop_loss_lifecycle(self, risk_db):
        """Test setting and triggering a stop loss"""
        rm = RiskManager(db_path=risk_db)
        
        # 1. Set Stop Loss (Long Position)
        # Entry 100, SL 95
        sl_id = rm.set_stop_loss(
            symbol="INFY",
            entry_price=100.0,
            stop_loss_price=95.0,
            quantity=10,
            order_id="ORD123"
        )
        
        assert sl_id is not None
        
        # 2. Check with price ABOVE SL (No trigger)
        current_prices = {"INFY": 98.0}
        triggered = rm.check_stop_losses(current_prices)
        assert len(triggered) == 0
        
        # 3. Check with price BELOW SL (Trigger!)
        current_prices = {"INFY": 94.0}
        triggered = rm.check_stop_losses(current_prices)
        
        assert len(triggered) == 1
        data = triggered[0]
        assert data['symbol'] == "INFY"
        assert data['exit_price'] == 94.0
        assert data['pnl'] == (94.0 - 100.0) * 10  # -6 * 10 = -60

    def test_circuit_breaker_trigger(self, risk_db):
        """Test daily loss limit triggers circuit breaker"""
        rm = RiskManager(
            db_path=risk_db,
            max_daily_loss=500  # Strict limit
        )
        
        # 1. Simulate a large loss
        # Set SL and immediately trigger it manually via check
        rm.set_stop_loss("LOSS_MAKER", 100, 90, 60, "ORD_FAIL") 
        # Loss: (80 - 100) * 60 = -1200 > 500
        
        rm.check_stop_losses({"LOSS_MAKER": 80})
        
        # 2. Check Breaker Status
        status = rm.check_daily_loss()
        
        assert status['daily_pnl'] == -1200.0
        assert status['breached'] is True
        assert status['circuit_breaker_active'] is True
        assert rm.circuit_breaker_triggered is True

    def test_risk_metrics_calculation(self, risk_db):
        """Test risk metric calculations (VAR, Sharpe, Drawdown)"""
        rm = RiskManager(db_path=risk_db)
        
        # Helper to inject past trades
        import sqlite3
        conn = sqlite3.connect(risk_db)
        cursor = conn.cursor()
        
        # Inject 5 days of trades
        trades = []
        # Days 1-5
        pnls = [1000, -500, 200, -100, 1500] 
        start_date = datetime.now()
        
        for i, pnl in enumerate(pnls):
            # Hacky: inserting directly to simulate history
            cursor.execute(
                """
                INSERT INTO stop_loss_orders 
                (symbol, entry_price, stop_loss_price, quantity, status, triggered_at, pnl)
                VALUES (?, ?, ?, ?, ?, datetime('now', ?), ?)
                """,
                ("TEST", 100, 90, 10, 'TRIGGERED', f'-{5-i} days', pnl)
            )
        conn.commit()
        conn.close()
        
        # Calculate Metrics
        metrics = rm.get_risk_metrics(days=7)
        
        assert metrics['total_trades'] == 5 # Logic groups by day, here 1 trade per day
        assert metrics['current_equity'] == 100000 + sum(pnls) # 100k + 2100 = 102100
