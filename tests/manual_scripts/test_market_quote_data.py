"""
Test Market Quote Data Retrieval
Replicates the SQL logic used in frontend/pages/market_quote.py
"""
import sqlite3
from pathlib import Path
import pandas as pd
import sys

# Assume run from project root
DB_PATH = Path("market_data.db").absolute()

def test_screener_query(limit=5):
    print(f"📂 Connecting to DB: {DB_PATH}")
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        
        # 1. Check Source Tables
        print("\n🔍 Checking Source Tables:")
        c = conn.cursor()
        
        c.execute("SELECT count(*) FROM instrument_master WHERE is_active=1")
        master_count = c.fetchone()[0]
        print(f"   - instrument_master (active): {master_count} rows")
        
        c.execute("SELECT count(*) FROM market_quota_nse500_data")
        quote_count = c.fetchone()
        quote_count = quote_count[0] if quote_count else 0
        print(f"   - market_quota_nse500_data:   {quote_count} rows")

        # 2. Run the actual Join Query
        print("\n🚀 Running JOIN Query (Market Quote Page Logic):")
        query = """
            SELECT 
                im.trading_symbol,
                im.segment,
                im.sector,
                q.close as last_price
            FROM instrument_master im
            LEFT JOIN market_quota_nse500_data q ON im.instrument_key = q.instrument_key
            WHERE im.trading_symbol IN ('RELIANCE', 'TCS', 'SBIN', 'INFY')
            AND im.segment = 'NSE_EQ'
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            print("❌ Query returned NO DATA.")
            print("   Possible Cause: No active NSE_EQ instruments or Join failed.")
        else:
            print(f"✅ Query returned {len(df)} rows:")
            print(df.to_string())
            
            # Check for NULL prices
            null_prices = df[df['last_price'].isna()]
            if not null_prices.empty:
                print(f"\n⚠️ Warning: {len(null_prices)} rows have NULL 'last_price'.")
                print("   This means 'market_quota_nse500_data' is likely empty or matching keys failed.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_screener_query()
