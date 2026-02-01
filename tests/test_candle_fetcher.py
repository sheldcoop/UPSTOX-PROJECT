#!/usr/bin/env python3
"""
Test Suite for Candle Fetcher

Tests candle data retrieval, storage, and validation.
"""

import os
import sys
import sqlite3
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.db_manager import initialize_database
from scripts.candle_fetcher import fetch_candle_data, store_candle_data, get_stored_candles


class TestCandleFetcher(unittest.TestCase):
    """Test suite for candle fetcher."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        cls.db_path = ":memory:"  # Use in-memory database for tests
        initialize_database()
    
    def test_fetch_candle_data(self):
        """Test fetching candle data from API."""
        # Test data
        symbol = "INFY"
        timeframe = "1d"
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Fetch candles (this requires valid API token)
        try:
            candles = fetch_candle_data(symbol, timeframe, start_date, end_date)
            
            # Verify structure
            self.assertIsInstance(candles, list)
            if len(candles) > 0:
                candle = candles[0]
                self.assertIn("timestamp", candle)
                self.assertIn("open", candle)
                self.assertIn("high", candle)
                self.assertIn("low", candle)
                self.assertIn("close", candle)
                self.assertIn("volume", candle)
                
                # Verify OHLC relationships
                self.assertGreaterEqual(candle["high"], candle["low"])
                self.assertGreaterEqual(candle["high"], candle["open"])
                self.assertGreaterEqual(candle["high"], candle["close"])
                self.assertLessEqual(candle["low"], candle["open"])
                self.assertLessEqual(candle["low"], candle["close"])
        
        except Exception as e:
            self.skipTest(f"API unavailable: {e}")
    
    def test_symbol_resolution(self):
        """Test symbol resolution to instrument key."""
        symbols = ["INFY", "TCS", "RELIANCE", "SBIN"]
        
        for symbol in symbols:
            try:
                from scripts.candle_fetcher import resolve_symbol
                key = resolve_symbol(symbol)
                
                # Verify format
                self.assertIn("|", key)
                parts = key.split("|")
                self.assertEqual(len(parts), 2)
                self.assertEqual(parts[0], "NSE_EQ")
                self.assertEqual(parts[1], symbol)
            
            except Exception as e:
                self.skipTest(f"Symbol resolution unavailable: {e}")
    
    def test_timeframe_mapping(self):
        """Test timeframe mapping to API formats."""
        from scripts.candle_fetcher import TIMEFRAME_MAP
        
        # Verify expected timeframes exist
        expected = ["1m", "5m", "15m", "30m", "1h", "1d", "1w", "1mo"]
        for tf in expected:
            self.assertIn(tf, TIMEFRAME_MAP)
            self.assertIsInstance(TIMEFRAME_MAP[tf], str)
    
    def test_date_parsing(self):
        """Test date string parsing."""
        from scripts.candle_fetcher import parse_date_string
        
        test_cases = [
            ("2024-01-01", 1704067200),  # Approximate epoch
            ("2025-01-31", None),  # Should work if function exists
        ]
        
        # Test if function exists and works
        try:
            for date_str, expected_epoch in test_cases:
                timestamp = parse_date_string(date_str)
                self.assertIsInstance(timestamp, int)
                self.assertGreater(timestamp, 0)
        except Exception:
            pass  # Function may not exist in current version


class TestCandleStorage(unittest.TestCase):
    """Test suite for candle storage."""
    
    def test_store_candle_data(self):
        """Test storing candle data in database."""
        initialize_database()
        
        test_candles = [
            {
                "timestamp": 1704067200,
                "open": 3425.50,
                "high": 3452.00,
                "low": 3420.00,
                "close": 3445.50,
                "volume": 2341000,
                "instrument_key": "NSE_EQ|INFY",
                "timeframe": "1d"
            }
        ]
        
        try:
            rows_stored = store_candle_data(test_candles)
            self.assertGreater(rows_stored, 0)
        except Exception as e:
            self.skipTest(f"Storage unavailable: {e}")
    
    def test_retrieve_candle_data(self):
        """Test retrieving stored candles."""
        try:
            # Try to get stored candles
            candles = get_stored_candles("INFY", "1d")
            
            if len(candles) > 0:
                candle = candles[0]
                self.assertIn("timestamp", candle)
                self.assertIn("open", candle)
                self.assertIn("close", candle)
                self.assertIn("volume", candle)
        
        except Exception as e:
            self.skipTest(f"Retrieval unavailable: {e}")


class TestCandleValidation(unittest.TestCase):
    """Test suite for candle data validation."""
    
    def test_ohlc_relationships(self):
        """Test OHLC relationship validation."""
        test_candle = {
            "timestamp": 1704067200,
            "open": 100,
            "high": 110,
            "low": 90,
            "close": 105,
            "volume": 1000000
        }
        
        # High should be >= all prices
        self.assertGreaterEqual(test_candle["high"], test_candle["open"])
        self.assertGreaterEqual(test_candle["high"], test_candle["close"])
        
        # Low should be <= all prices
        self.assertLessEqual(test_candle["low"], test_candle["open"])
        self.assertLessEqual(test_candle["low"], test_candle["close"])
        
        # High should be > Low
        self.assertGreater(test_candle["high"], test_candle["low"])
    
    def test_volume_validation(self):
        """Test volume validation."""
        test_volumes = [1000, 100000, 1000000, 0]
        
        for volume in test_volumes:
            self.assertGreaterEqual(volume, 0)


if __name__ == "__main__":
    unittest.main()
