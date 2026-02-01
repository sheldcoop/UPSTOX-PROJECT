import sqlite3
from scripts.upstox_live_api import get_upstox_api
import json

# 1. Get Instrument Key from DB
db_path = "market_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT instrument_key, symbol, trading_symbol, segment_id, type_code FROM instruments WHERE symbol='UFBL' OR trading_symbol='UFBL'")
rows = cursor.fetchall()
conn.close()

if not rows:
    print("UFBL not found in database.")
    exit()

print(f"Found instruments: {rows}")
keys = [r[0] for r in rows]

# 2. Fetch Live Quote
api = get_upstox_api()
print(f"Fetching quotes for keys: {keys}")
quotes = api.get_batch_market_quotes(keys)
print(f"Raw Quotes: {quotes}")

for key in keys:
    if quotes and key in quotes:
        q = quotes[key]
        print(f"\n--- Quote Data ({key}) ---")
        print(json.dumps(q, indent=2))
        
        ohlc = q.get('ohlc', {})
        close_price = ohlc.get('close', 0)
        last_price = q.get('last_price', 0)
        
        print(f"\nPrevious Close: {close_price}")
        print(f"Last Price: {last_price}")
        
        if close_price > 0:
            pct_change = ((last_price - close_price) / close_price) * 100
            print(f"Calculated % Change: {pct_change:.2f}%")
        else:
            print("Previous Close is 0 or missing.")

