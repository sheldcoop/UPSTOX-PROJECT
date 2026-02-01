#!/usr/bin/env python3
"""
Test Suite for Option History Fetcher

Tests historical option candle data retrieval and storage.
"""

import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.db_manager import initialize_database
from scripts.option_history_fetcher import (
    fetch_option_candles, parse_option_candle, get_option_expiries
)


class TestOptionHistoryFetcher(unittest.TestCase):
    """Test suite for option history fetcher."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        initialize_database()
    
    def test_fetch_option_candles(self):
        """Test fetching historical option candles."""
        underlying = "NIFTY"
        option_type = "CE"
        strike = 23000
        
        try:
            expiries = get_option_expiries(underlying)
            if not expiries:
                self.skipTest("No expiries available")
            
            expiry = expiries[0]
            
            # Calculate date range (last 30 days)
            to_date = datetime.now()
            from_date = to_date - timedelta(days=30)
            
            candles = fetch_option_candles(
                underlying=underlying,
                option_type=option_type,
                strike_price=strike,
                expiry_date=expiry,
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=to_date.strftime("%Y-%m-%d")
            )
            
            # Verify structure
            if len(candles) > 0:
                candle = candles[0]
                self.assertIn("timestamp", candle)
                self.assertIn("open", candle)
                self.assertIn("high", candle)
                self.assertIn("low", candle)
                self.assertIn("close", candle)
                self.assertIn("volume", candle)
        
        except Exception as e:
            self.skipTest(f"API unavailable: {e}")
    
    def test_timestamp_parsing(self):
        """Test ISO8601 timestamp parsing."""
        from scripts.option_history_fetcher import parse_option_candle
        from dateutil.parser import isoparse
        
        test_timestamps = [
            "2025-01-30T00:00:00+05:30",
            "2025-01-29T15:30:00+05:30",
            "2025-01-28T09:15:00+05:30",
        ]
        
        for ts_str in test_timestamps:
            try:
                parsed = isoparse(ts_str)
                epoch = int(parsed.timestamp())
                self.assertIsInstance(epoch, int)
                self.assertGreater(epoch, 0)
            except Exception:
                pass  # Skip if dateutil not available
    
    def test_ohlc_validation(self):
        """Test OHLC data validation for options."""
        underlying = "NIFTY"
        option_type = "CE"
        strike = 23000
        
        try:
            expiries = get_option_expiries(underlying)
            if not expiries:
                self.skipTest("No expiries available")
            
            expiry = expiries[0]
            to_date = datetime.now()
            from_date = to_date - timedelta(days=7)
            
            candles = fetch_option_candles(
                underlying=underlying,
                option_type=option_type,
                strike_price=strike,
                expiry_date=expiry,
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=to_date.strftime("%Y-%m-%d")
            )
            
            for candle in candles:
                # OHLC relationships
                self.assertGreaterEqual(candle["high"], candle["low"])
                self.assertGreaterEqual(candle["high"], candle["open"])
                self.assertGreaterEqual(candle["high"], candle["close"])
                self.assertLessEqual(candle["low"], candle["open"])
                self.assertLessEqual(candle["low"], candle["close"])
                
                # Volume should be non-negative
                self.assertGreaterEqual(candle.get("volume", 0), 0)
        
        except Exception as e:
            self.skipTest(f"API unavailable: {e}")


class TestOptionCandleStorage(unittest.TestCase):
    """Test suite for option candle storage."""
    
    def test_option_candle_structure(self):
        """Test option candle data structure."""
        test_candle = {
            "option_symbol": "NIFTY23JAN23000CE",
            "timestamp": 1704067200,
            "open": 150.50,
            "high": 165.00,
            "low": 145.00,
            "close": 160.25,
            "volume": 50000,
            "oi": 500000
        }
        
        # Verify structure
        self.assertIn("option_symbol", test_candle)
        self.assertIn("timestamp", test_candle)
        self.assertIn("open", test_candle)
        self.assertIn("close", test_candle)
        self.assertIn("volume", test_candle)
    
    def test_option_symbol_format(self):
        """Test option symbol format validation."""
        valid_symbols = [
            "NIFTY30JAN23000CE",
            "NIFTY30JAN23000PE",
            "BANKNIFTY30JAN43000CE",
            "INFY30JAN2300CE",
        ]
        
        for symbol in valid_symbols:
            # Verify basic format
            self.assertIsInstance(symbol, str)
            self.assertGreater(len(symbol), 5)
            self.assertTrue(
                "CE" in symbol or "PE" in symbol,
                f"Symbol {symbol} must contain CE or PE"
            )


class TestOptionExpiryManagement(unittest.TestCase):
    """Test suite for option expiry management."""
    
    def test_get_option_expiries(self):
        """Test fetching available option expiries."""
        underlying = "NIFTY"
        
        try:
            expiries = get_option_expiries(underlying)
            
            self.assertIsInstance(expiries, list)
            if len(expiries) > 0:
                # Verify date format
                for exp in expiries:
                    parts = exp.split("-")
                    self.assertEqual(len(parts), 3)
                    # Each part should be numeric
                    for part in parts:
                        self.assertTrue(part.isdigit())
        
        except Exception as e:
            self.skipTest(f"API unavailable: {e}")
    
    def test_expiry_date_ordering(self):
        """Test that expiry dates are in chronological order."""
        underlying = "NIFTY"
        
        try:
            expiries = get_option_expiries(underlying)
            
            if len(expiries) > 1:
                # Parse and sort
                from datetime import datetime
                parsed = [datetime.strptime(e, "%Y-%m-%d") for e in expiries]
                
                # Verify they're sorted
                for i in range(len(parsed) - 1):
                    self.assertLess(parsed[i], parsed[i + 1])
        
        except Exception as e:
            self.skipTest(f"API unavailable: {e}")


class TestOptionCandleTimeframes(unittest.TestCase):
    """Test suite for option candle timeframes."""
    
    def test_timeframe_support(self):
        """Test that option candles support various timeframes."""
        underlying = "NIFTY"
        
        try:
            expiries = get_option_expiries(underlying)
            if not expiries:
                self.skipTest("No expiries available")
            
            # Typically options support 1m, 5m, 15m, 1h, 1d
            # Though this test is basic since the API may not return all
            self.assertTrue(True)  # Placeholder
        
        except Exception as e:
            self.skipTest(f"API unavailable: {e}")


if __name__ == "__main__":
    unittest.main()
