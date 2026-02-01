#!/usr/bin/env python3
"""Populate has_fno column based on NSE_FO underlying_symbol."""
import sqlite3

DB = 'market_data.db'
conn = sqlite3.connect(DB)
cur = conn.cursor()

print("🔄 Populating has_fno column...")

# Get all F&O underlying symbols
fno_symbols = cur.execute(
    "SELECT DISTINCT underlying_symbol FROM exchange_listings WHERE segment='NSE_FO' AND underlying_type='EQUITY'"
).fetchall()

fno_symbols = [s[0] for s in fno_symbols]
print(f"   Found {len(fno_symbols)} F&O stocks")

# Update exchange_listings
cur.execute('BEGIN')
for symbol in fno_symbols:
    cur.execute(
        "UPDATE exchange_listings SET has_fno=1 WHERE trading_symbol=?",
        (symbol,)
    )

conn.commit()
print(f"✅ Updated {len(fno_symbols)} rows with has_fno=1")

# Verify
result = cur.execute("SELECT COUNT(*) FROM exchange_listings WHERE has_fno=1").fetchone()[0]
print(f"✅ Total stocks with F&O: {result}")

conn.close()
