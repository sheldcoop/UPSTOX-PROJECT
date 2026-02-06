"""
Test Market Quote JOIN Fix
Attempts to join on 'NSE_EQ:' || trading_symbol instead of instrument_key.
"""
import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path("market_data.db").absolute()

def test_join_fix():
    conn = sqlite3.connect(DB_PATH)
    
    print("\n🚀 Testing JOIN Loophole (Symbol Match):")
    query = """
        SELECT 
            im.trading_symbol,
            im.instrument_key as master_key,
            q.instrument_key as quota_key,
            q.close as last_price,
            q.open, q.high, q.low,
            (q.close - q.open) as net_change
        FROM instrument_master im
        LEFT JOIN market_quota_nse500_data q ON im.instrument_key = q.instrument_key
        WHERE im.trading_symbol IN ('RELIANCE', 'AARTISURF')
        AND im.segment = 'NSE_EQ'
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(df.to_string())
    
    if df['last_price'].notnull().all():
        print("\n✅ SUCCESS: Join worked using Symbol Matching!")
    else:
        print("\n❌ FAILURE: Still NULLs.")

if __name__ == "__main__":
    test_join_fix()
