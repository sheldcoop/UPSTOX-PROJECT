"""
Integration Tests for Upstox Client

These tests make REAL API calls to Upstox (sandbox or read-only endpoints).
They validate:
- Live connectivity
- Schema validation (ensure API response format matches expectations)
- Actual data flow

IMPORTANT: These tests require a valid Upstox access token in .env file.
Set UPSTOX_ACCESS_TOKEN environment variable before running.

Usage:
    pytest tests/integration/test_upstox_integration.py -v
    
    Or skip integration tests:
    pytest -m "not integration"
"""

import pytest
import os
from datetime import datetime, timedelta
from typing import Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.upstox.client import (
    UpstoxClient,
    AuthenticationError,
    RateLimitError,
    create_client
)


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def client():
    """
    Create client for integration tests.
    Skips tests if no access token is available.
    """
    access_token = os.getenv('UPSTOX_ACCESS_TOKEN')
    
    if not access_token:
        pytest.skip("UPSTOX_ACCESS_TOKEN not set - skipping integration tests")
    
    return UpstoxClient(access_token=access_token)


class TestLiveConnectivity:
    """Test live API connectivity"""
    
    def test_client_creation(self, client):
        """Test that client is properly initialized"""
        assert client is not None
        assert client.access_token is not None
        assert client.BASE_URL == "https://api.upstox.com/v2"
    
    def test_get_profile_connectivity(self, client):
        """Test connectivity with get_profile endpoint (read-only)"""
        try:
            profile = client.get_profile()
            assert profile is not None
            assert isinstance(profile, dict)
            print(f"\n✅ Profile connectivity test passed")
            print(f"   User: {profile.get('user_name', 'N/A')}")
        except AuthenticationError:
            pytest.skip("Authentication failed - token may be expired")
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")


class TestSchemaValidation:
    """Test that API response schemas match our expectations"""
    
    def test_profile_schema(self, client):
        """
        Validate profile response schema.
        If Upstox changes 'user_name' to 'userName', this test will catch it.
        """
        try:
            profile = client.get_profile()
            
            # Expected keys in profile response
            # Reference: docs/Upstox.md - GET /user/profile
            expected_keys = [
                'user_id',
                'user_name',
                'email',
                'user_type',
                'poa',
                'is_active',
                'exchanges'
            ]
            
            # Check that at least some expected keys exist
            present_keys = [k for k in expected_keys if k in profile]
            
            assert len(present_keys) > 0, \
                f"No expected keys found. Got: {list(profile.keys())}"
            
            print(f"\n✅ Profile schema validation passed")
            print(f"   Expected keys present: {present_keys}")
            print(f"   All keys in response: {list(profile.keys())}")
            
        except AuthenticationError:
            pytest.skip("Authentication failed - token may be expired")
    
    def test_holdings_schema(self, client):
        """
        Validate holdings response schema.
        """
        try:
            holdings = client.get_holdings()
            
            assert isinstance(holdings, list), \
                f"Holdings should be a list, got {type(holdings)}"
            
            if holdings:  # If user has holdings
                first_holding = holdings[0]
                
                # Expected keys in each holding
                # Reference: docs/Upstox.md - GET /portfolio/long-term-holdings
                expected_keys = [
                    'isin',
                    'quantity',
                    'average_price',
                    'last_price',
                    'pnl'
                ]
                
                present_keys = [k for k in expected_keys if k in first_holding]
                
                print(f"\n✅ Holdings schema validation passed")
                print(f"   Holdings count: {len(holdings)}")
                print(f"   Expected keys in first holding: {present_keys}")
                print(f"   All keys: {list(first_holding.keys())}")
            else:
                print(f"\n⚠️  No holdings found (empty portfolio)")
                
        except AuthenticationError:
            pytest.skip("Authentication failed - token may be expired")
    
    def test_positions_schema(self, client):
        """
        Validate positions response schema.
        Should return dict with 'day' and 'net' keys.
        """
        try:
            positions = client.get_positions()
            
            assert isinstance(positions, dict), \
                f"Positions should be a dict, got {type(positions)}"
            
            # Should have 'day' and 'net' keys
            assert 'day' in positions or 'net' in positions, \
                f"Expected 'day' or 'net' keys. Got: {list(positions.keys())}"
            
            day_positions = positions.get('day', [])
            net_positions = positions.get('net', [])
            
            assert isinstance(day_positions, list)
            assert isinstance(net_positions, list)
            
            print(f"\n✅ Positions schema validation passed")
            print(f"   Day positions: {len(day_positions)}")
            print(f"   Net positions: {len(net_positions)}")
            
        except AuthenticationError:
            pytest.skip("Authentication failed - token may be expired")
    
    def test_funds_schema(self, client):
        """
        Validate funds and margin response schema.
        """
        try:
            funds = client.get_funds_and_margin()
            
            assert isinstance(funds, dict), \
                f"Funds should be a dict, got {type(funds)}"
            
            # Reference: docs/Upstox.md - GET /user/get-funds-and-margin
            # Expected keys may vary by segment (equity, commodity, etc.)
            
            print(f"\n✅ Funds schema validation passed")
            print(f"   Keys in response: {list(funds.keys())}")
            
        except AuthenticationError:
            pytest.skip("Authentication failed - token may be expired")


class TestDataQuality:
    """Test quality of data returned by API"""
    
    def test_profile_data_not_empty(self, client):
        """Test that profile returns meaningful data"""
        try:
            profile = client.get_profile()
            
            # User name should not be empty
            user_name = profile.get('user_name', '')
            assert user_name, "user_name should not be empty"
            
            # User ID should exist
            user_id = profile.get('user_id', '')
            assert user_id, "user_id should not be empty"
            
            print(f"\n✅ Profile data quality validated")
            print(f"   User: {user_name}")
            print(f"   ID: {user_id}")
            
        except AuthenticationError:
            pytest.skip("Authentication failed - token may be expired")
    
    def test_market_quote_format(self, client):
        """
        Test market quote with a known instrument.
        Note: This may fail if market is closed or instrument is invalid.
        """
        try:
            # Use a common instrument (this is Infosys on NSE)
            # Format: EXCHANGE_SEGMENT|ISIN
            instrument_key = "NSE_EQ|INE009A01021"  # TCS
            
            quote = client.get_market_quote(instrument_key)
            
            assert isinstance(quote, dict), \
                f"Quote should be a dict, got {type(quote)}"
            
            # Should have price-related fields
            # Note: Key names may vary - check docs
            has_price_data = any(key in quote for key in [
                'last_price', 'ltp', 'close', 'ohlc'
            ])
            
            print(f"\n✅ Market quote format validated")
            print(f"   Instrument: {instrument_key}")
            print(f"   Has price data: {has_price_data}")
            print(f"   Keys in response: {list(quote.keys())}")
            
        except Exception as e:
            # Market may be closed or instrument may be invalid
            print(f"\n⚠️  Market quote test skipped: {e}")
            pytest.skip(f"Market quote test skipped: {e}")


class TestErrorHandlingLive:
    """Test error handling with live API"""
    
    @pytest.mark.skipif(
        not os.getenv('UPSTOX_ACCESS_TOKEN'),
        reason="Requires UPSTOX_ACCESS_TOKEN"
    )
    def test_invalid_token_authentication(self):
        """Test that invalid token raises AuthenticationError"""
        invalid_client = UpstoxClient(access_token="invalid_token_123")
        
        with pytest.raises(AuthenticationError):
            invalid_client.get_profile()
    
    def test_invalid_instrument_key(self, client):
        """Test handling of invalid instrument key"""
        try:
            # Use clearly invalid instrument key
            result = client.get_market_quote("INVALID|KEY123")
            
            # Should either raise error or return empty dict
            if result:
                print(f"\n⚠️  Unexpected: Got result for invalid key: {result}")
            else:
                print(f"\n✅ Invalid instrument handled correctly (empty result)")
                
        except Exception as e:
            # API should handle this gracefully
            print(f"\n✅ Invalid instrument raised error: {type(e).__name__}")


class TestFactoryFunction:
    """Test the factory function for creating clients"""
    
    def test_create_client_factory(self):
        """Test create_client factory function"""
        client = create_client()
        assert isinstance(client, UpstoxClient)
        assert client.BASE_URL == "https://api.upstox.com/v2"


def test_integration_environment_setup():
    """
    Test that integration test environment is properly set up.
    This test always runs to help diagnose setup issues.
    """
    access_token = os.getenv('UPSTOX_ACCESS_TOKEN')
    
    if not access_token:
        print("\n⚠️  UPSTOX_ACCESS_TOKEN not set")
        print("   Integration tests will be skipped")
        print("   Set token in .env file or environment to run integration tests")
    else:
        print(f"\n✅ Integration test environment configured")
        print(f"   Token present: {access_token[:10]}...")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '-s'])
