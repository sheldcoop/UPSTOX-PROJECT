import sys
import os
from pathlib import Path
import logging
import json

# Setup path to project root
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.append(project_root)

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestScript")

def test_option_fetching():
    print("="*60)
    print("🚀 TESTING OPTION CHAIN FETCHING")
    print("="*60)

    try:
        # Import Service
        print("1. Importing OptionsChainService...")
        from backend.services.market_data.options_chain import OptionsChainService
        from backend.utils.auth.manager import AuthManager
        
        # Check Auth first
        print("2. Checking Authentication State...")
        auth = AuthManager()
        token = auth.get_valid_token()
        
        if token:
            print(f"   ✅ Valid Token Found: {token[:20]}...")
        else:
            print("   ❌ NO VALID TOKEN FOUND. Please authenticate first at http://localhost:5050/auth/start")
            return

        # Initialize Service
        print("3. Initializing OptionsChainService...")
        service = OptionsChainService()
        
        # Fetch Data
        symbol = "NIFTY"
        print(f"4. Fetching Option Chain for {symbol}...")
        data = service.get_option_chain(symbol)
        
        if data:
            print("\n✅ DATA FETCHED SUCCESSFULLY!")
            print(f"   Symbol: {data.get('symbol')}")
            print(f"   Expiry: {data.get('expiry')}")
            print(f"   Spot Price: {data.get('underlying_price')}")
            print(f"   Strikes Count: {len(data.get('strikes', []))}")
            
            # Print a few strikes as sample
            print("\n   Sample Data (First 3 Strikes):")
            for strike in data.get('strikes', [])[:3]:
                print(f"   - Strike {strike['strike']}: "
                      f"CE LTW {strike['call'].get('ltp', 'N/A')} | "
                      f"PE LTP {strike['put'].get('ltp', 'N/A')}")
        else:
            print("\n⚠️  FETCH RETURNED NONE")
            print("   Possible causes:")
            print("   - Market closed and no cached data")
            print("   - API request failed (check logs)")
            print("   - Token expired during request")

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_option_fetching()
