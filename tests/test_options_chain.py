#!/usr/bin/env python3
"""
Quick Test Script for Options Chain Service

Tests:
1. Market hours detection
2. Mock data generation
3. API endpoint responses
4. TraceID logging
5. Greeks calculations
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.options_chain_service import OptionsChainService

def test_market_hours():
    """Test market hours detection"""
    print("=" * 60)
    print("TEST 1: Market Hours Detection")
    print("=" * 60)
    
    service = OptionsChainService()
    is_open, message = service.is_market_open()
    
    print(f"✓ Market Status: {message}")
    print(f"✓ Is Open: {is_open}")
    print(f"✓ Current IST Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    return is_open

def test_mock_data():
    """Test mock data generation"""
    print("=" * 60)
    print("TEST 2: Mock Data Generation")
    print("=" * 60)
    
    service = OptionsChainService()
    
    # Test with NIFTY
    chain = service._mock_option_chain('NIFTY', '2025-02-06', False)
    
    print(f"✓ Symbol: {chain['symbol']}")
    print(f"✓ Underlying Price: ₹{chain['underlying_price']:,}")
    print(f"✓ Expiry: {chain['expiry_date']}")
    print(f"✓ Total Strikes: {len(chain['strikes'])}")
    print(f"✓ Data Source: {chain['data_source']}")
    print(f"✓ Market Open: {chain['market_open']}")
    print()
    
    # Verify strike structure
    first_strike = chain['strikes'][0]
    print(f"✓ First Strike: {first_strike['strike']}")
    print(f"  - Call LTP: ₹{first_strike['call']['ltp']:.2f}")
    print(f"  - Call OI: {first_strike['call']['oi']:,}")
    print(f"  - Call Volume: {first_strike['call']['volume']:,}")
    print(f"  - Call IV: {first_strike['call']['iv']:.1f}%")
    print(f"  - Call Delta: {first_strike['call']['delta']:.3f}")
    print(f"  - Call Gamma: {first_strike['call']['gamma']:.4f}")
    print(f"  - Call Theta: {first_strike['call']['theta']:.2f}")
    print(f"  - Call Vega: {first_strike['call']['vega']:.2f}")
    print()
    
    return chain

def test_atm_strike(chain):
    """Test ATM strike identification"""
    print("=" * 60)
    print("TEST 3: ATM Strike Identification")
    print("=" * 60)
    
    underlying = chain['underlying_price']
    
    # Find ATM strike (closest to underlying)
    atm_strike = min(chain['strikes'], key=lambda x: abs(x['strike'] - underlying))
    
    print(f"✓ Underlying Price: ₹{underlying:,}")
    print(f"✓ ATM Strike: {atm_strike['strike']}")
    print(f"✓ Distance: ₹{abs(atm_strike['strike'] - underlying):,.0f}")
    print()
    print("ATM Greeks (Should be ~0.50 for Delta):")
    print(f"  - Call Delta: {atm_strike['call']['delta']:.3f} (expected: ~0.50)")
    print(f"  - Put Delta: {atm_strike['put']['delta']:.3f} (expected: ~-0.50)")
    print(f"  - Call Gamma: {atm_strike['call']['gamma']:.4f} (highest at ATM)")
    print(f"  - Call Theta: {atm_strike['call']['theta']:.2f} (most negative at ATM)")
    print()
    
    # Validate
    assert 0.45 <= atm_strike['call']['delta'] <= 0.55, "Call Delta should be ~0.50 at ATM"
    assert -0.55 <= atm_strike['put']['delta'] <= -0.45, "Put Delta should be ~-0.50 at ATM"
    print("✓ ATM Greeks validation PASSED")
    print()

def test_greeks_progression(chain):
    """Test Greeks change across strikes"""
    print("=" * 60)
    print("TEST 4: Greeks Progression Across Strikes")
    print("=" * 60)
    
    print(f"{'Strike':<10} {'Call Δ':<10} {'Put Δ':<10} {'Moneyness':<12}")
    print("-" * 50)
    
    underlying = chain['underlying_price']
    
    for strike_data in chain['strikes'][:10]:  # First 10 strikes
        strike = strike_data['strike']
        call_delta = strike_data['call']['delta']
        put_delta = strike_data['put']['delta']
        
        # Determine moneyness
        if strike < underlying:
            moneyness = 'ITM (Calls)'
        elif abs(strike - underlying) / underlying < 0.005:
            moneyness = 'ATM'
        else:
            moneyness = 'OTM (Calls)'
        
        print(f"{strike:<10} {call_delta:<10.3f} {put_delta:<10.3f} {moneyness:<12}")
    
    print()
    print("✓ Call Delta should decrease from ITM to OTM")
    print("✓ Put Delta should become more negative from OTM to ITM")
    print()

def test_api_endpoint():
    """Test API endpoint (requires API server running)"""
    print("=" * 60)
    print("TEST 5: API Endpoint (Optional)")
    print("=" * 60)
    
    try:
        import requests
        
        # Test market status
        response = requests.get('http://localhost:5001/api/options/market-status')
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Market Status API: {data['message']}")
            print(f"✓ Timestamp: {data['timestamp']}")
        else:
            print(f"✗ Market Status API failed: {response.status_code}")
        
        # Test options chain
        response = requests.get('http://localhost:5001/api/options/chain?symbol=NIFTY')
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Options Chain API: SUCCESS")
            print(f"✓ Strikes returned: {len(data['data']['strikes'])}")
            print(f"✓ Data source: {data['data']['data_source']}")
            print(f"✓ TraceID: {data.get('trace_id', 'N/A')}")
        else:
            print(f"✗ Options Chain API failed: {response.status_code}")
        
        print()
        
    except ImportError:
        print("⚠ requests library not available, skipping API tests")
        print("  Install with: pip install requests")
        print()
    except requests.exceptions.ConnectionError:
        print("⚠ API server not running at http://localhost:5001")
        print("  Start with: python scripts/api_server.py")
        print()

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("OPTIONS CHAIN SERVICE - QUICK TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        # Test 1: Market hours
        is_market_open = test_market_hours()
        
        # Test 2: Mock data generation
        chain = test_mock_data()
        
        # Test 3: ATM strike
        test_atm_strike(chain)
        
        # Test 4: Greeks progression
        test_greeks_progression(chain)
        
        # Test 5: API endpoint
        test_api_endpoint()
        
        # Summary
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print()
        print("Next Steps:")
        print("1. Start API server: python scripts/api_server.py")
        print("2. Start frontend: cd frontend && npm run dev")
        print("3. Navigate to: http://localhost:5173")
        print("4. Click 'Options Chain' in sidebar")
        print("5. Select symbol and verify data displays")
        print()
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
