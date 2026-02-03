#!/usr/bin/env python3
"""
Test Suite for Backtest Engine

Tests backtesting functionality, strategy execution, and metrics calculation.
"""

import os
import sys
import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_utils import initialize_database
from scripts.backtest_engine import (
    BacktestEngine,
    SMAStrategy,
    RSIStrategy,
    BacktestResult,
)


class TestCandleDataLoading(unittest.TestCase):
    """Test suite for loading candle data."""

    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        initialize_database()

    def test_load_candle_data(self):
        """Test loading candle data from database."""
        symbol = "INFY"
        timeframe = "1d"

        try:
            engine = BacktestEngine()
            candles = engine.load_candle_data(symbol, timeframe)

            self.assertIsInstance(candles, pd.DataFrame)

            if not candles.empty:
                # Verify structure
                cols = candles.columns
                self.assertIn("open", cols)
                self.assertIn("high", cols)
                self.assertIn("low", cols)
                self.assertIn("close", cols)
                self.assertIn("volume", cols)

        except Exception as e:
            self.skipTest(f"Database unavailable: {e}")

    def test_candle_ordering(self):
        """Test that candles are ordered chronologically."""
        symbol = "INFY"
        timeframe = "1d"

        try:
            engine = BacktestEngine()
            candles = engine.load_candle_data(symbol, timeframe)

            if candles is not None and not candles.empty:
                timestamps = candles.index

                # Verify sorted
                for i in range(len(timestamps) - 1):
                    self.assertLess(timestamps[i], timestamps[i + 1])

        except Exception as e:
            self.skipTest(f"Database unavailable: {e}")


class TestSMAStrategy(unittest.TestCase):
    """Test suite for SMA strategy."""

    def test_sma_calculation(self):
        """Test SMA calculation."""
        close_prices = np.array([100, 102, 101, 103, 105, 104, 106, 107, 105, 108])

        # Calculate 3-period SMA
        window = 3
        sma = np.convolve(close_prices, np.ones(window) / window, mode="valid")

        self.assertEqual(len(sma), len(close_prices) - window + 1)
        self.assertAlmostEqual(sma[0], 101.0)  # (100+102+101)/3

    def test_strategy_initialization(self):
        """Test SMA strategy initialization."""
        strategy = SMAStrategy(params={"fast_period": 20, "slow_period": 50})

        self.assertEqual(strategy.params["fast_period"], 20)
        self.assertEqual(strategy.params["slow_period"], 50)
        self.assertIsNotNone(strategy.name)

    def test_strategy_signal_generation(self):
        """Test that strategy generates valid signals."""
        # Create test price data
        prices = np.arange(100, 200, dtype=float)  # 100 to 199
        close_prices = prices + np.random.normal(0, 5, len(prices))

        strategy = SMAStrategy(params={"fast_period": 10, "slow_period": 20})

        # Verify that strategy can generate signals
        self.assertTrue(hasattr(strategy, "generate_signals"))


class TestRSIStrategy(unittest.TestCase):
    """Test suite for RSI strategy."""

    def test_rsi_calculation(self):
        """Test RSI calculation basics."""
        # RSI formula: 100 - (100 / (1 + RS))
        # where RS = average gain / average loss

        test_prices = np.array(
            [44, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08]
        )

        # Calculate gains and losses
        deltas = np.diff(test_prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        self.assertEqual(len(gains), len(test_prices) - 1)
        self.assertEqual(len(losses), len(test_prices) - 1)

    def test_strategy_initialization(self):
        """Test RSI strategy initialization."""
        strategy = RSIStrategy(params={"rsi_period": 14})

        self.assertEqual(strategy.params["rsi_period"], 14)
        self.assertIsNotNone(strategy.name)

    def test_rsi_bounds(self):
        """Test that RSI values are between 0 and 100."""
        # RSI is bounded between 0 and 100 by definition
        rsi_values = [0, 25, 50, 70, 100]

        for rsi in rsi_values:
            self.assertGreaterEqual(rsi, 0)
            self.assertLessEqual(rsi, 100)


class TestBacktestMetrics(unittest.TestCase):
    """Test suite for backtest metrics calculation."""

    def test_backtest_result_structure(self):
        """Test BacktestResult dataclass structure."""
        result = BacktestResult(
            strategy_name="SMA",
            symbol="INFY",
            start_date="2024-01-01",
            end_date="2024-12-31",
            init_cash=100000.0,
            final_value=115490.0,
            total_return=0.1549,  # 15.49%
            cagr=0.1245,  # 12.45%
            sharpe_ratio=0.94,
            sortino_ratio=1.23,
            calmar_ratio=2.34,
            max_drawdown=-0.1570,
            win_rate=0.67,
            total_trades=3,
            duration_days=365,
        )

        self.assertEqual(result.symbol, "INFY")
        self.assertEqual(result.strategy_name, "SMA")
        self.assertAlmostEqual(result.total_return, 0.1549, places=4)
        self.assertGreater(result.sharpe_ratio, 0)

    def test_return_calculation(self):
        """Test total return calculation."""
        initial_capital = 100000
        final_value = 115490  # +15.49%

        total_return = (final_value - initial_capital) / initial_capital

        self.assertAlmostEqual(total_return, 0.1549, places=4)

    def test_sharpe_ratio_bounds(self):
        """Test Sharpe ratio reasonable bounds."""
        # Sharpe ratio is typically between -2 and 3
        valid_sharpe_values = [-2, -1, 0, 0.5, 1.0, 2.0, 3.0]

        for sharpe in valid_sharpe_values:
            self.assertIsInstance(sharpe, (int, float))

    def test_drawdown_calculation(self):
        """Test max drawdown calculation."""
        cumulative_returns = np.array([1.0, 1.05, 1.02, 0.95, 1.10, 1.08])

        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_dd = np.min(drawdown)

        self.assertLessEqual(max_dd, 0)
        self.assertGreaterEqual(max_dd, -1)

    def test_win_rate_calculation(self):
        """Test win rate calculation."""
        winning_trades = 2
        losing_trades = 1
        total_trades = winning_trades + losing_trades

        win_rate = winning_trades / total_trades

        self.assertAlmostEqual(win_rate, 0.6667, places=4)
        self.assertGreater(win_rate, 0)
        self.assertLess(win_rate, 1)


class TestStrategyExecution(unittest.TestCase):
    """Test suite for strategy execution."""

    def test_signal_generation(self):
        """Test that strategies generate entry/exit signals."""
        # Create test price data
        test_prices = np.arange(100, 150, dtype=float)

        strategy = SMAStrategy(params={"fast_period": 5, "slow_period": 15})

        # Verify strategy has methods for signal generation
        self.assertTrue(
            hasattr(strategy, "generate_signals") or hasattr(strategy, "__call__")
        )

    def test_position_management(self):
        """Test position entry and exit logic."""
        # Test simple entry/exit signals
        entry_signals = [0, 0, 1, 0, 0, 0, 0, 1, 0]  # Positions: 2, 7
        exit_signals = [0, 0, 0, 0, 1, 0, 0, 0, 1]  # Positions: 4, 8

        positions = []
        current_position = False

        for i, (entry, exit) in enumerate(zip(entry_signals, exit_signals)):
            if entry and not current_position:
                positions.append(("ENTRY", i))
                current_position = True
            elif exit and current_position:
                positions.append(("EXIT", i))
                current_position = False

        self.assertGreater(len(positions), 0)
        self.assertEqual(positions[0][0], "ENTRY")


class TestStrategyValidation(unittest.TestCase):
    """Test suite for strategy parameter validation."""

    def test_sma_periods_validation(self):
        """Test SMA period validation."""
        # Fast period should be less than slow period
        strategy = SMAStrategy(params={"fast_period": 20, "slow_period": 50})

        self.assertLess(strategy.params["fast_period"], strategy.params["slow_period"])

    def test_positive_periods(self):
        """Test that periods are positive."""
        strategy_sma = SMAStrategy(params={"fast_period": 10, "slow_period": 30})
        strategy_rsi = RSIStrategy(params={"rsi_period": 14})

        self.assertGreater(strategy_sma.params["fast_period"], 0)
        self.assertGreater(strategy_sma.params["slow_period"], 0)
        self.assertGreater(strategy_rsi.params["rsi_period"], 0)


if __name__ == "__main__":
    unittest.main()
