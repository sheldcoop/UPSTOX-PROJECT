"""
Test Market Quote Equity Join
Checks if instrument_master can join with market_quota_nse500_data.
Target: RELIANCE (Liquid) and AARTISURF (User Example)
"""
import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path("market_data.db").absolute()

def test_equity_join():
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    
    # 1. Check Instrument Master Key
    print("\n🔍 Instrument Master Keys:")
    cursor = conn.cursor()
    cursor.execute("SELECT trading_symbol, instrument_key FROM instrument_master WHERE trading_symbol IN ('RELIANCE', 'AARTISURF') AND segment='NSE_EQ'")
    master_keys = cursor.fetchall()
    for symbol, key in master_keys:
        print(f"   {symbol:12} -> {key}")
        
    # 2. Check Market Quota Key (Raw Table Scan)
    print("\n🔍 Market Quota Keys (Raw Table Scan):")
    # We use LIKE because we suspect the key format is different
    cursor.execute("SELECT instrument_key, close FROM market_quota_nse500_data WHERE instrument_key LIKE '%RELIANCE%' OR instrument_key LIKE '%AARTISURF%' LIMIT 5")
    quota_rows = cursor.fetchall()
    for key, price in quota_rows:
        print(f"   {key:25} -> Price: {price}")
        
    # 3. Attempt Join (The Real Test)
    print("\n🚀 Testing JOIN (App Logic):")
    query = """
        SELECT 
            im.trading_symbol,
            im.instrument_key as master_key,
            q.instrument_key as quota_key,
            q.close as last_price
        FROM instrument_master im
        LEFT JOIN market_quota_nse500_data q ON im.instrument_key = q.instrument_key
        WHERE im.trading_symbol IN ('RELIANCE', 'AARTISURF')
        AND im.segment = 'NSE_EQ'
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(df.to_string())
    
    if df['last_price'].isnull().any():
        print("\n❌ FAILURE: Join failed (Price is NULL). Keys do not match.")
    else:
        print("\n✅ SUCCESS: Join worked!")

if __name__ == "__main__":
    test_equity_join()
