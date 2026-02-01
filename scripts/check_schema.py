#!/usr/bin/env python3
"""
Check database schema
"""
import sqlite3

DB_PATH = 'market_data.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Get schema for master_stocks
print("master_stocks columns:")
cur.execute("PRAGMA table_info(master_stocks)")
columns = cur.fetchall()
for col in columns:
    print(f"  {col[1]}: {col[2]}")

print("\nexchange_listings columns:")
cur.execute("PRAGMA table_info(exchange_listings)")
columns = cur.fetchall()
for col in columns:
    print(f"  {col[1]}: {col[2]}")

print("\ncandles columns:")
cur.execute("PRAGMA table_info(candles)")
columns = cur.fetchall()
for col in columns:
    print(f"  {col[1]}: {col[2]}")

# Sample data from master_stocks
print("\nSample from master_stocks:")
cur.execute("SELECT * FROM master_stocks LIMIT 1")
row = cur.fetchone()
if row:
    print(row)

# Sample data from exchange_listings
print("\nSample from exchange_listings:")
cur.execute("SELECT * FROM exchange_listings WHERE segment='NSE_EQ' LIMIT 1")
row = cur.fetchone()
if row:
    print(row)

conn.close()
