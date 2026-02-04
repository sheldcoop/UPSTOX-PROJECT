#!/usr/bin/env python3
"""
Test BSE SME Market Data
Check if Upstox API returns quotes for BSE SME instruments
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.upstox_live_api import get_upstox_api

DB_PATH = Path(__file__).parent.parent / "market_data.db"

def test_bse_sme_quotes():
    """Test if we can get quotes for BSE SME stocks"""
    
    print("=" * 70)
    print("BSE SME MARKET DATA TEST")
    print("=" * 70)
    
    # Get BSE SME instruments from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT instrument_key, symbol, trading_symbol, company_name
        FROM instruments
        WHERE exchange='BSE' AND segment='BSE_EQ'
        AND instrument_type IN ('M', 'MT')
        AND is_active = 1
        LIMIT 20
    """)
    
    instruments = cursor.fetchall()
    conn.close()
    
    print(f"\nFound {len(instruments)} BSE SME instruments in database")
    print("\nSample instruments:")
    for inst in instruments[:5]:
        print(f"  {inst[1]:15} | {inst[2]:20} | {inst[3][:40]}")
    
    # Get instrument keys
    instrument_keys = [inst[0] for inst in instruments]
    
    print(f"\nFetching quotes for {len(instrument_keys)} instruments...")
    print(f"Sample keys: {instrument_keys[:3]}")
    
    # Get API
    api = get_upstox_api()
    
    # Fetch quotes
    try:
        quotes = api.get_batch_market_quotes(instrument_keys)
        
        print(f"\n✅ API Response received")
        print(f"Total quotes returned: {len(quotes) if quotes else 0}")
        
        if quotes:
            # Analyze response
            valid_quotes = 0
            zero_price = 0
            missing_data = 0
            
            print("\nSample Quotes:")
            print("-" * 70)
            
            for i, (key, data) in enumerate(list(quotes.items())[:10]):
                if data:
                    ltp = data.get('last_price', 0)
                    volume = data.get('volume', 0)
                    change = data.get('net_change', 0)
                    
                    if ltp > 0:
                        valid_quotes += 1
                        print(f"{i+1}. {key[:30]:30} | LTP: ₹{ltp:8.2f} | Vol: {volume:10,} | Chg: {change:+7.2f}")
                    else:
                        zero_price += 1
                        print(f"{i+1}. {key[:30]:30} | LTP: ₹0.00 (NO PRICE DATA)")
                else:
                    missing_data += 1
                    print(f"{i+1}. {key[:30]:30} | NULL DATA")
            
            print("\n" + "=" * 70)
            print("SUMMARY")
            print("=" * 70)
            print(f"Total instruments requested: {len(instrument_keys)}")
            print(f"API responses received:      {len(quotes)}")
            print(f"Valid quotes (LTP > 0):      {valid_quotes}")
            print(f"Zero price quotes:           {zero_price}")
            print(f"Missing/null data:           {missing_data}")
            print("=" * 70)
            
            if valid_quotes == 0:
                print("\n❌ ISSUE FOUND: No valid price data for BSE SME stocks!")
                print("Possible reasons:")
                print("  1. BSE SME stocks may not be actively traded today")
                print("  2. Upstox API may not provide real-time data for BSE SME")
                print("  3. Market may be closed")
            elif valid_quotes < len(instrument_keys) * 0.5:
                print(f"\n⚠️  WARNING: Only {valid_quotes}/{len(instrument_keys)} stocks have valid prices")
                print("This explains why BSE SME movers appears empty!")
            else:
                print(f"\n✅ Good coverage: {valid_quotes}/{len(instrument_keys)} stocks have valid prices")
        
        else:
            print("\n❌ API returned empty/null response")
            print("Possible reasons:")
            print("  1. API authentication issue")
            print("  2. Invalid instrument keys")
            print("  3. API rate limit exceeded")
    
    except Exception as e:
        print(f"\n❌ Error fetching quotes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_bse_sme_quotes()
