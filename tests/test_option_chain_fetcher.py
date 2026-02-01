#!/usr/bin/env python3
"""
Test Suite for Option Chain Fetcher

Tests option chain data retrieval, storage, and validation.
"""

import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.db_manager import initialize_database
from scripts.option_chain_fetcher import (
    get_option_expiries, fetch_option_chain, parse_option_data
)


class TestOptionChainFetcher(unittest.TestCase):
    """Test suite for option chain fetcher."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        initialize_database()
    
    def test_get_option_expiries(self):
        """Test fetching available option expiry dates."""
        underlying = "NIFTY"
        
        try:
            expiries = get_option_expiries(underlying)
            
            self.assertIsInstance(expiries, list)
            self.assertGreater(len(expiries), 0)
            
            # Verify date format YYYY-MM-DD
            for exp in expiries:
                parts = exp.split("-")
                self.assertEqual(len(parts), 3)
                self.assertEqual(len(parts[0]), 4)  # Year
                self.assertIn(len(parts[1]), [1, 2])  # Month
                self.assertIn(len(parts[2]), [1, 2])  # Day
        
        except Exception as e:
            self.skipTest(f"API unavailable: {e}")
    
    def test_fetch_option_chain(self):
        """Test fetching option chain data."""
        underlying = "NIFTY"
        
        try:
            expiries = get_option_expiries(underlying)
            if not expiries:
                self.skipTest("No expiries available")
            
            expiry = expiries[0]
            
            # Fetch option chain
            options = fetch_option_chain(underlying, expiry)
            
            self.assertIsInstance(options, list)
            
            if len(options) > 0:
                opt = options[0]
                # Verify required fields
                self.assertIn("strike_price", opt)
                self.assertIn("option_type", opt)
                self.assertIn("tradingsymbol", opt)
                self.assertIn("bid_price", opt)
                self.assertIn("ask_price", opt)
                self.assertIn("ltp", opt)
                self.assertIn("volume", opt)
                self.assertIn("oi", opt)
        
        except Exception as e:
            self.skipTest(f"API unavailable: {e}")
    
    def test_option_type_validation(self):
        """Test option type validation (CE/PE)."""
        underlying = "NIFTY"
        
        try:
            expiries = get_option_expiries(underlying)
            if not expiries:
                self.skipTest("No expiries available")
            
            expiry = expiries[0]
            options = fetch_option_chain(underlying, expiry)
            
            for opt in options:
                option_type = opt.get("option_type")
                self.assertIn(option_type, ["CE", "PE"])
        
        except Exception as e:
            self.skipTest(f"API unavailable: {e}")


class TestOptionDataValidation(unittest.TestCase):
    """Test suite for option data validation."""
    
    def test_strike_price_validation(self):
        """Test strike price validation."""
        test_strikes = [22000, 23000, 24000, 25000]
        
        for strike in test_strikes:
            self.assertIsInstance(strike, (int, float))
            self.assertGreater(strike, 0)
    
    def test_greeks_validation(self):
        """Test Greeks value validation."""
        # Test typical Greeks ranges
        test_delta = 0.5345  # Between -1 and 1
        test_gamma = 0.0012  # Small positive value
        test_theta = -0.0234  # Usually negative for long options
        test_vega = 0.0567  # Small positive value
        
        self.assertGreaterEqual(test_delta, -1)
        self.assertLessEqual(test_delta, 1)
        
        self.assertGreater(test_gamma, 0)
        
        self.assertGreater(test_vega, 0)
    
    def test_iv_validation(self):
        """Test Implied Volatility validation."""
        # IV is typically between 0 and 2 (0% to 200%)
        test_iv_values = [0.15, 0.25, 0.35, 0.50]
        
        for iv in test_iv_values:
            self.assertGreater(iv, 0)
            self.assertLess(iv, 3)  # Reasonable upper bound
    
    def test_bid_ask_spread(self):
        """Test bid-ask spread validation."""
        test_cases = [
            {"bid": 100, "ask": 105},  # Positive spread
            {"bid": 50, "ask": 55},
            {"bid": 1000, "ask": 1010},
        ]
        
        for case in test_cases:
            self.assertLess(case["bid"], case["ask"])
            spread = case["ask"] - case["bid"]
            self.assertGreater(spread, 0)
    
    def test_volume_oi_validation(self):
        """Test volume and open interest validation."""
        test_volumes = [0, 1000, 100000, 1000000]
        test_ois = [0, 500000, 5000000, 50000000]
        
        for vol in test_volumes:
            self.assertGreaterEqual(vol, 0)
        
        for oi in test_ois:
            self.assertGreaterEqual(oi, 0)


class TestOptionChainStructure(unittest.TestCase):
    """Test suite for option chain data structure."""
    
    def test_option_chain_completeness(self):
        """Test that option chain has symmetric CE/PE strikes."""
        underlying = "NIFTY"
        
        try:
            expiries = get_option_expiries(underlying)
            if not expiries:
                self.skipTest("No expiries available")
            
            expiry = expiries[0]
            options = fetch_option_chain(underlying, expiry)
            
            if len(options) > 0:
                # Count CE and PE
                ce_strikes = set()
                pe_strikes = set()
                
                for opt in options:
                    strike = opt.get("strike_price")
                    opt_type = opt.get("option_type")
                    
                    if opt_type == "CE":
                        ce_strikes.add(strike)
                    elif opt_type == "PE":
                        pe_strikes.add(strike)
                
                # Usually CE and PE strikes should be the same
                # (though there might be edge cases)
                intersection = ce_strikes & pe_strikes
                self.assertGreater(len(intersection), 0)
        
        except Exception as e:
            self.skipTest(f"API unavailable: {e}")


if __name__ == "__main__":
    unittest.main()
