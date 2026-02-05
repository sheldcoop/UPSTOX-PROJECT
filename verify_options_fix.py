import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.market_data.options_chain import OptionsChainService

async def verify_dynamic_resolution():
    service = OptionsChainService()
    
    symbols_to_test = ["NIFTY", "FINNIFTY", "RELIANCE", "BANKNIFTY", "TCS", "SENSEX"]
    
    print("\n--- Testing Instrument Key Resolution ---")
    for symbol in symbols_to_test:
        key = service._get_instrument_key(symbol)
        print(f"Symbol: {symbol:<12} -> Key: {key}")
        
    print("\n--- Testing Option Chain Fetching (Initial Logic) ---")
    # Test for RELIANCE (previously failing/hardcoded incorrectly)
    print("Fetching chain for RELIANCE...")
    chain = service.get_option_chain("RELIANCE")
    if chain and "strikes" in chain:
        print(f"✅ RELIANCE: Successfully fetched {len(chain['strikes'])} strikes")
        print(f"   Expiry picked: {chain['expiry_date']}")
    else:
        print(f"❌ RELIANCE: Failed to fetch chain")

    # Test for FINNIFTY
    print("\nFetching chain for FINNIFTY...")
    chain = service.get_option_chain("FINNIFTY")
    if chain and "strikes" in chain:
        print(f"✅ FINNIFTY: Successfully fetched {len(chain['strikes'])} strikes")
        print(f"   Expiry picked: {chain['expiry_date']}")
    else:
        print(f"❌ FINNIFTY: Failed to fetch chain")

if __name__ == "__main__":
    asyncio.run(verify_dynamic_resolution())
