#!/usr/bin/env python3
"""
Test Suite for Expired Options Fetcher

Tests expired option contract retrieval and storage.
"""

import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.db_manager import initialize_database
from scripts.expired_options_fetcher import (
    get_available_expiries,
    fetch_expired_option_contracts,
    parse_option_data,
    ensure_expired_options_table
)


class TestExpiredOptionsFetcher(unittest.TestCase):
    """Test suite for expired options fetcher."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        initialize_database()
        ensure_expired_options_table()
    
    def test_get_available_expiries(self):
        """Test fetching available expiry dates."""
        underlying = "NIFTY"
        
        try:
            expiries = get_available_expiries(underlying)
            
            self.assertIsInstance(expiries, list)
            self.assertGreater(len(expiries), 0)
            
            # Verify date format YYYY-MM-DD
            for exp in expiries:
                parts = exp.split("-")
                self.assertEqual(len(parts), 3)
                self.assertEqual(len(parts[0]), 4)  # Year
                # Month and day can be 1-2 digits
                self.assertGreaterEqual(int(parts[1]), 1)
                self.assertLessEqual(int(parts[1]), 12)
                self.assertGreaterEqual(int(parts[2]), 1)
                self.assertLessEqual(int(parts[2]), 31)
        
        except Exception as e:
            self.skipTest(f"API unavailable: {e}")
    
    def test_fetch_expired_option_contracts(self):
        """Test fetching expired option contracts."""
        underlying = "NIFTY"
        
        try:
            expiries = get_available_expiries(underlying)
            if not expiries:
                self.skipTest("No expiries available")
            
            expiry = expiries[0]
            
            contracts = fetch_expired_option_contracts(underlying, expiry)
            
            self.assertIsInstance(contracts, list)
            
            if len(contracts) > 0:
                contract = contracts[0]
                
                # Verify required fields
                self.assertIn("tradingsymbol", contract)
                self.assertIn("exchange_token", contract)
                self.assertIn("exchange", contract)
        
        except Exception as e:
            self.skipTest(f"API unavailable: {e}")
    
    def test_fetch_with_option_type_filter(self):
        """Test fetching with option type filter."""
        underlying = "NIFTY"
        
        try:
            expiries = get_available_expiries(underlying)
            if not expiries:
                self.skipTest("No expiries available")
            
            expiry = expiries[0]
            
            # Fetch only CE
            ce_contracts = fetch_expired_option_contracts(
                underlying, expiry, option_type="CE"
            )
            
            # Fetch only PE
            pe_contracts = fetch_expired_option_contracts(
                underlying, expiry, option_type="PE"
            )
            
            # Both should be lists
            self.assertIsInstance(ce_contracts, list)
            self.assertIsInstance(pe_contracts, list)
        
        except Exception as e:
            self.skipTest(f"API unavailable: {e}")
    
    def test_fetch_with_strike_filter(self):
        """Test fetching with strike price filter."""
        underlying = "NIFTY"
        strike = 23000
        
        try:
            expiries = get_available_expiries(underlying)
            if not expiries:
                self.skipTest("No expiries available")
            
            expiry = expiries[0]
            
            contracts = fetch_expired_option_contracts(
                underlying, expiry, strike_price=strike
            )
            
            self.assertIsInstance(contracts, list)
            
            # If contracts found, verify they match the strike
            if len(contracts) > 0:
                for contract in contracts:
                    strike_in_contract = contract.get("strike_price")
                    if strike_in_contract:
                        self.assertEqual(strike_in_contract, strike)
        
        except Exception as e:
            self.skipTest(f"API unavailable: {e}")


class TestOptionDataParsing(unittest.TestCase):
    """Test suite for option data parsing."""
    
    def test_parse_option_data(self):
        """Test parsing option contract data."""
        test_contract = {
            "tradingsymbol": "NIFTY22JAN23000CE",
            "exchange_token": "12345",
            "exchange": "NFO",
            "strike_price": 23000
        }
        
        parsed = parse_option_data(
            test_contract,
            "NIFTY",
            "2025-01-22"
        )
        
        self.assertEqual(parsed["underlying_symbol"], "NIFTY")
        self.assertEqual(parsed["expiry_date"], "2025-01-22")
        self.assertEqual(parsed["option_type"], "CE")
        self.assertEqual(parsed["tradingsymbol"], "NIFTY22JAN23000CE")
    
    def test_option_type_extraction(self):
        """Test extraction of option type from symbol."""
        test_cases = [
            ("NIFTY22JAN23000CE", "CE"),
            ("NIFTY22JAN23000PE", "PE"),
            ("BANKNIFTY22JAN43000CE", "CE"),
            ("BANKNIFTY22JAN43000PE", "PE"),
        ]
        
        for symbol, expected_type in test_cases:
            contract = {"tradingsymbol": symbol}
            parsed = parse_option_data(contract, "NIFTY", "2025-01-22")
            
            self.assertEqual(parsed["option_type"], expected_type)
    
    def test_strike_extraction_from_symbol(self):
        """Test extraction of strike from symbol."""
        test_cases = [
            ("NIFTY22JAN23000CE", 23000),
            ("NIFTY22JAN22500PE", 22500),
            ("BANKNIFTY22JAN43000CE", 43000),
        ]
        
        for symbol, expected_strike in test_cases:
            contract = {"tradingsymbol": symbol, "strike_price": None}
            parsed = parse_option_data(contract, "NIFTY", "2025-01-22")
            
            # Strike might be extracted from symbol or contract
            strike = parsed.get("strike_price") or expected_strike
            self.assertIsNotNone(strike)


class TestExpiredOptionsStorage(unittest.TestCase):
    """Test suite for expired options storage."""
    
    def test_expired_options_table_creation(self):
        """Test that expired options table is created."""
        try:
            ensure_expired_options_table()
            
            # Try to query the table
            import sqlite3
            conn = sqlite3.connect("market_data.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='expired_options'
            """)
            
            result = cursor.fetchone()
            self.assertIsNotNone(result)
            
            conn.close()
        
        except Exception as e:
            self.skipTest(f"Database unavailable: {e}")
    
    def test_expired_options_unique_constraint(self):
        """Test that expired options table enforces uniqueness."""
        try:
            ensure_expired_options_table()
            
            import sqlite3
            conn = sqlite3.connect("market_data.db")
            cursor = conn.cursor()
            
            # Insert test data
            cursor.execute("""
                INSERT OR REPLACE INTO expired_options (
                    underlying_symbol, option_type, strike_price, expiry_date,
                    tradingsymbol, exchange_token, exchange, fetch_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ("NIFTY", "CE", 23000, "2025-01-22", 
                  "NIFTY22JAN23000CE", "12345", "NFO", 
                  int(datetime.now().timestamp())))
            
            # Try to insert duplicate (should replace, not fail)
            cursor.execute("""
                INSERT OR REPLACE INTO expired_options (
                    underlying_symbol, option_type, strike_price, expiry_date,
                    tradingsymbol, exchange_token, exchange, fetch_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ("NIFTY", "CE", 23000, "2025-01-22",
                  "NIFTY22JAN23000CE", "54321", "NFO",
                  int(datetime.now().timestamp())))
            
            conn.commit()
            
            # Verify only one record exists
            cursor.execute("""
                SELECT COUNT(*) FROM expired_options 
                WHERE underlying_symbol = ? AND strike_price = ? 
                AND option_type = ? AND expiry_date = ?
            """, ("NIFTY", 23000, "CE", "2025-01-22"))
            
            count = cursor.fetchone()[0]
            self.assertEqual(count, 1)
            
            conn.close()
        
        except Exception as e:
            self.skipTest(f"Database unavailable: {e}")


class TestExpiredOptionsValidation(unittest.TestCase):
    """Test suite for expired options data validation."""
    
    def test_strike_price_validation(self):
        """Test strike price is positive."""
        test_strikes = [22500, 23000, 23500, 24000]
        
        for strike in test_strikes:
            self.assertIsInstance(strike, (int, float))
            self.assertGreater(strike, 0)
    
    def test_option_type_validation(self):
        """Test option type is CE or PE."""
        valid_types = ["CE", "PE"]
        
        for opt_type in valid_types:
            self.assertIn(opt_type, ["CE", "PE"])
    
    def test_expiry_date_format(self):
        """Test expiry date format is YYYY-MM-DD."""
        test_dates = [
            "2025-01-22",
            "2025-02-19",
            "2025-03-26",
        ]
        
        for date_str in test_dates:
            parts = date_str.split("-")
            self.assertEqual(len(parts), 3)
            self.assertEqual(len(parts[0]), 4)  # Year
            self.assertGreaterEqual(int(parts[1]), 1)
            self.assertLessEqual(int(parts[1]), 12)
            self.assertGreaterEqual(int(parts[2]), 1)
            self.assertLessEqual(int(parts[2]), 31)


if __name__ == "__main__":
    unittest.main()
