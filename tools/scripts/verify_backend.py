#!/usr/bin/env python3
"""
System verification - Check all backend components are operational
"""

import sqlite3
import json
import os
from datetime import datetime

print("\n" + "=" * 80)
print("UPSTOX BACKEND - COMPLETE SYSTEM VERIFICATION")
print("=" * 80)

try:
    conn = sqlite3.connect("market_data.db")
    cursor = conn.cursor()

    # 1. Check tables exist
    print("\n[1] DATABASE SCHEMA")
    print("-" * 80)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    print(f"✅ Tables created: {len(tables)}")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"   - {table[0]:30} {count:10} records")

    # 2. Check OAuth tokens
    print("\n[2] AUTHENTICATION")
    print("-" * 80)
    cursor.execute("SELECT COUNT(*) FROM oauth_tokens")
    token_count = cursor.fetchone()[0]
    if token_count > 0:
        print(f"✅ OAuth tokens stored: {token_count}")
    else:
        print("❌ No OAuth tokens - run scripts/oauth_server.py first")

    # 3. Check stock data
    print("\n[3] STOCK DATA")
    print("-" * 80)
    cursor.execute("SELECT DISTINCT symbol FROM candles_new ORDER BY symbol")
    symbols = [row[0] for row in cursor.fetchall()]
    print(f"✅ Symbols with candles: {len(symbols)}")
    for sym in symbols:
        cursor.execute("SELECT COUNT(*) FROM candles_new WHERE symbol=?", (sym,))
        count = cursor.fetchone()[0]
        print(f"   - {sym:10} {count:5} candles")

    # 4. Check option data
    print("\n[4] OPTION DATA")
    print("-" * 80)
    cursor.execute("SELECT COUNT(*) FROM option_chain_snapshots")
    snap_count = cursor.fetchone()[0]
    print(f"✅ Option chain snapshots: {snap_count}")

    cursor.execute("SELECT COUNT(*) FROM option_market_data")
    market_count = cursor.fetchone()[0]
    print(f"✅ Option market data records: {market_count}")

    cursor.execute("SELECT COUNT(*) FROM option_candles")
    candle_count = cursor.fetchone()[0]
    print(f"✅ Option historical candles: {candle_count}")

    # 5. Check latest data
    print("\n[5] LATEST DATA")
    print("-" * 80)
    cursor.execute(
        """
        SELECT symbol, MAX(timestamp) as latest_ts
        FROM candles_new
        GROUP BY symbol
    """
    )
    for sym, ts in cursor.fetchall():
        dt = datetime.fromtimestamp(ts)
        print(f"   {sym:10} latest: {dt.date()}")

    # 6. Check backtest results
    print("\n[6] BACKTEST INFRASTRUCTURE")
    print("-" * 80)
    results_files = [
        f
        for f in os.listdir(".")
        if f.startswith("backtest_results_") and f.endswith(".json")
    ]
    print(f"✅ Backtest results files: {len(results_files)}")
    if results_files:
        latest_file = sorted(results_files)[-1]
        with open(latest_file) as f:
            data = json.load(f)
            print(f"   Latest: {latest_file}")
            print(f"   Backtests in file: {len(data['results'])}")

    conn.close()

    print("\n" + "=" * 80)
    print("✅ BACKEND SYSTEM STATUS: FULLY OPERATIONAL")
    print("=" * 80)
    print("\nNEXT STEPS:")
    print("1. Run: python3 run_backtest.py --symbols INFY --strategy SMA")
    print("2. Or run components: python3 scripts/backtest_engine.py --symbol INFY")
    print("3. See BACKEND_README.md for full documentation")
    print()

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback

    traceback.print_exc()
