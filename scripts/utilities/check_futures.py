import sqlite3
import pandas as pd
from datetime import datetime

db_path = "market_data.db"
conn = sqlite3.connect(db_path)

# query futures
query = """
    SELECT el.symbol, d.expiry_date as expiry, el.instrument_key 
    FROM exchange_listings el
    LEFT JOIN derivatives d ON el.instrument_key = d.instrument_key
    WHERE el.segment='NSE_FO' AND el.instrument_type='FUT'
"""
df = pd.read_sql(query, conn)
conn.close()

print(f"Total Futures: {len(df)}")
print(df.head())

# unique symbols
print(f"Unique Symbols: {df['symbol'].nunique()}")
print(df["symbol"].unique()[:10])

# Check expirations
print("\nExpirations sample:")
print(df["expiry"].dropna().sort_values().unique()[:5])
