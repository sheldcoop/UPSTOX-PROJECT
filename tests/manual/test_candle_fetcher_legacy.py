#!/usr/bin/env python3
"""
Quick test for candle fetcher - validates setup
"""
import sqlite3
import sys
import os
from datetime import datetime, timedelta

# Add scripts dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auth_manager import AuthManager

DB_PATH = "market_data.db"

print("=" * 60)
print("CANDLE FETCHER TEST")
print("=" * 60)

# 1. Check authentication
print("\n1️⃣  Checking authentication...")
try:
    auth = AuthManager()
    token = auth.get_valid_token()

    if token:
        print(f"   ✅ Valid token found (auto-refreshed if needed)")
    else:
        print(f"   ⚠️  No token found - run ./authenticate.sh")
except Exception as e:
    print(f"   ❌ Auth error: {e}")

# 2. Check DB
print("\n2️⃣  Checking database...")
try:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check auth_tokens
    cur.execute("SELECT COUNT(*) FROM auth_tokens WHERE is_active = 1")
    token_count = cur.fetchone()[0]
    print(f"   ✅ Active auth tokens: {token_count}")

    # Check master_stocks
    cur.execute("SELECT COUNT(*) FROM master_stocks")
    stock_count = cur.fetchone()[0]
    print(f"   ✅ Master stocks: {stock_count}")

    # Check candles (might not exist yet)
    try:
        cur.execute("SELECT COUNT(*) FROM candles_new")
        candle_count = cur.fetchone()[0]
        print(f"   ✅ Existing candles: {candle_count}")
    except:
        print(f"   ℹ️  Candles table doesn't exist yet (will be created on first fetch)")

    conn.close()
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# 2. Check a sample symbol exists
print("\n2️⃣  Checking sample symbols...")
try:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT symbol, instrument_key FROM exchange_listings 
        WHERE segment='NSE_EQ' LIMIT 5
    """
    )
    symbols = cur.fetchall()
    conn.close()

    if symbols:
        print(f"   ✅ Found {len(symbols)} sample symbols:")
        for sym, key in symbols:
            print(f"      - {sym}: {key}")
    else:
        print("   ❌ No symbols found!")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# 3. Test fetch with INFY
print("\n3️⃣  Testing fetch with INFY...")
import sys

sys.path.insert(0, "/Users/prince/Desktop/UPSTOX-project/scripts")

try:
    from candle_fetcher import (
        get_access_token,
        fetch_candles,
        parse_candle,
        store_candles,
    )

    # Get token
    print("   Getting access token...")
    token = get_access_token()
    print(f"   ✅ Token ready")

    # Fetch 5 days of data for INFY
    end_date = "2025-01-31"
    start_date = "2025-01-26"

    print(f"   Fetching INFY {start_date} to {end_date}...")
    raw_candles = fetch_candles(
        "NSE_EQ|INE002A01018", "1d", start_date, end_date, token  # INFY
    )

    if raw_candles:
        print(f"   ✅ Fetched {len(raw_candles)} candles")

        # Parse and store
        parsed = [
            parse_candle(c, "INFY", "NSE_EQ|INE002A01018", "1d") for c in raw_candles
        ]
        parsed = [c for c in parsed if c]
        stored = store_candles(parsed)
        print(f"   ✅ Stored {stored} candles")
    else:
        print("   ❌ No candles fetched")

except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ TEST COMPLETE")
print("=" * 60)
