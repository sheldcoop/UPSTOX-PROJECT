"""
Unit tests for Backtest Engine and Strategies
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Fix import path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.core.analytics.backtest_engine import (
    BacktestEngine, 
    SMAStrategy, 
    RSIStrategy,
    BacktestResult
)

@pytest.fixture
def sample_ohlcv():
    """Create sample OHLCV data for testing"""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    df = pd.DataFrame(index=dates)
    
    # Create valid trend for SMA: Up then Down
    # periods 0-50: Price rises (Fast MA > Slow MA)
    # periods 50-100: Price falls (Fast MA < Slow MA)
    prices = np.concatenate([
        np.linspace(100, 200, 50),
        np.linspace(200, 100, 50)
    ])
    
    df['open'] = prices
    df['high'] = prices + 1
    df['low'] = prices - 1
    df['close'] = prices
    df['volume'] = 1000
    return df

class TestStrategies:
    """Test Strategy Signal Generation"""

    def test_sma_strategy_signals(self, sample_ohlcv):
        """Test SMA crossover signals"""
        # Fast=10, Slow=30
        strategy = SMAStrategy(params={"fast_period": 10, "slow_period": 30})
        
        signals = strategy.generate_signals(sample_ohlcv)
        
        assert 'signal' in signals.columns
        assert 'trade_signal' in signals.columns
        
        # Verify columns preserved
        assert 'close' in signals.columns

        # In our synthetic data:
        # First 30 days: undefined (MA needs 30 days)
        # Day 30-50: Fast MA > Slow MA -> Signal 1 (Buy)
        # Day 50+: Fast MA < Slow MA -> Signal -1 (Sell)
        
        # Check a point in the 'uptrend'
        assert signals['signal'].iloc[40] == 1 
        
        # Check a point in the 'downtrend'
        assert signals['signal'].iloc[-10] == -1

    def test_rsi_strategy_signals(self, sample_ohlcv):
        """Test RSI overbought/oversold signals"""
        # Create distinct overbought/oversold conditions
        # RSI calculation is complex, so we just verify structural correctness
        # and basic logic preservation
        strategy = RSIStrategy(params={"rsi_period": 14})
        
        signals = strategy.generate_signals(sample_ohlcv)
        
        assert 'signal' in signals.columns
        assert 'rsi' in signals.columns
        
        # Verify values are within -1, 0, 1
        unique_signals = signals['signal'].unique()
        for s in unique_signals:
            assert s in [-1, 0, 1]

class TestBacktestEngine:
    """Test Backtest Engine Flow (Mocking vectorbt)"""

    @patch('backend.core.analytics.backtest_engine.vbt')
    @patch('backend.core.analytics.backtest_engine.pd.read_sql_query')
    @patch('backend.core.analytics.backtest_engine.sqlite3.connect')
    def test_run_backtest_success(self, mock_conn, mock_read_sql, mock_vbt, sample_ohlcv):
        """Test complete backtest run with mocked data and vectorbt"""
        
        # 1. Mock DB Data Loading
        # read_sql_query returns a DataFrame. 
        # The engine expects the 'timestamp' column to be processed
        db_df = sample_ohlcv.copy()
        db_df['timestamp'] = db_df.index.view(int) // 10**9 # mock unix timestamp column
        db_df = db_df.reset_index(drop=True)
        
        mock_read_sql.return_value = db_df
        
        # 2. Mock vectorbt Portfolio
        mock_pf = MagicMock()
        mock_pf.total_return.return_value = 0.15 # 15%
        mock_pf.sharpe_ratio.return_value = 1.5
        mock_pf.sortino_ratio.return_value = 2.0
        mock_pf.calmar_ratio.return_value = 3.0
        mock_pf.max_drawdown.return_value = -0.10
        mock_pf.final_value.return_value = 115000
        mock_pf.entries.sum.return_value = 5
        mock_pf.exits.sum.return_value = 5
        mock_pf.win_rate = 0.6  # 60% win rate
        
        # Mock class method from_signals
        mock_vbt.Portfolio.from_signals.return_value = mock_pf
        
        # 3. Initialize Engine
        engine = BacktestEngine(params={"init_cash": 100000})
        strategy = SMAStrategy()
        
        # 4. Run Backtest
        result = engine.run_backtest(
            symbol="TEST",
            strategy=strategy,
            start_date="2024-01-01"
        )
        
        # 5. Verify Results
        assert isinstance(result, BacktestResult)
        assert result.symbol == "TEST"
        assert result.total_return == 0.15
        assert result.sharpe_ratio == 1.5
        assert result.total_trades > 0
        
        # Verify DB Loaded
        mock_read_sql.assert_called_once()
        
        # Verify VBT called with signals
        mock_vbt.Portfolio.from_signals.assert_called_once()

    def test_backtest_engine_no_data(self):
        """Test engine handles missing data gracefully"""
        with patch('backend.core.analytics.backtest_engine.pd.read_sql_query', return_value=pd.DataFrame()):
            with patch('backend.core.analytics.backtest_engine.sqlite3.connect'):
                engine = BacktestEngine()
                strategy = SMAStrategy()
                
                result = engine.run_backtest("EMPTY", strategy)
                assert result is None
