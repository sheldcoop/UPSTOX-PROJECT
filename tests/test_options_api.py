#!/usr/bin/env python3
"""
Test script for Options Chain API
Run this separately while servers are running
"""

import requests
import json


def test_options_api():
    """Test the options chain API endpoint"""
    try:
        print("🔍 Testing Options Chain API...")
        print("=" * 60)

        # Test API endpoint
        url = "http://localhost:5001/api/options/chain"
        params = {"symbol": "NIFTY"}

        print(f"\n📡 Request: GET {url}")
        print(f"   Params: {params}")

        response = requests.get(url, params=params, timeout=10)

        print(f"\n✅ Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            print(f"\n📊 Options Chain Data:")
            print(f"   Symbol: {data.get('symbol')}")
            print(f"   Underlying Price: ₹{data.get('underlying_price'):,.2f}")
            print(f"   Expiry Date: {data.get('expiry_date')}")
            print(f"   Market Open: {data.get('market_open')}")
            print(f"   Data Source: {data.get('data_source', 'live')}")
            print(f"   Number of Strikes: {len(data.get('strikes', []))}")

            # Show a few strikes
            strikes = data.get("strikes", [])
            if strikes:
                print(f"\n📈 Sample Strikes (showing 5 ATM strikes):")
                mid_idx = len(strikes) // 2
                sample_strikes = strikes[mid_idx - 2 : mid_idx + 3]

                print(
                    f"\n{'Strike':<10} {'Call LTP':<12} {'Put LTP':<12} {'Call OI':<12} {'Put OI':<12}"
                )
                print("-" * 60)
                for strike_data in sample_strikes:
                    strike = strike_data["strike"]
                    call = strike_data["call"]
                    put = strike_data["put"]
                    print(
                        f"{strike:<10.0f} ₹{call['ltp']:<11.2f} ₹{put['ltp']:<11.2f} {call['oi']:<12,d} {put['oi']:<12,d}"
                    )

            print("\n✅ Options Chain API is working!")
            return True

        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"   {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: API server is not running!")
        print("   Please start the servers with: ./start.sh")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    test_options_api()
