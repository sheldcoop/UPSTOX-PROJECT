import sys
import os
import asyncio
from datetime import datetime, timedelta

# Ensure project root is in path
sys.path.append(os.getcwd())

from scripts.expired_options_fetcher import (
    fetch_expired_option_contracts,
    fetch_expired_historical_candles,
    ensure_token_valid,
)


async def verify_candles():
    symbol = "NIFTY"
    expiry = "2026-01-27"

    print(f"--- CANDLE VERIFICATION TEST for {symbol} {expiry} ---")

    # 1. Fetch Chain
    print("Fetching option chain...")
    contracts = fetch_expired_option_contracts(symbol, expiry)

    if not contracts:
        print("Failed to fetch contracts.")
        return

    # 2. Pick specific contracts to test (based on user's CSV)
    # NIFTY 23300 CE (Missing in CSV) vs NIFTY 23750 CE (Present in CSV)

    target_strikes = [23300.0, 23750.0]

    for strike in target_strikes:
        print(f"\nAnalyzing Strike {strike}...")

        # Find CE and PE
        ce_contract = next(
            (
                c
                for c in contracts
                if c["strike_price"] == strike and c["instrument_type"] == "CE"
            ),
            None,
        )
        pe_contract = next(
            (
                c
                for c in contracts
                if c["strike_price"] == strike and c["instrument_type"] == "PE"
            ),
            None,
        )

        for contract in [ce_contract, pe_contract]:
            if not contract:
                continue

            name = contract["trading_symbol"]
            inst_key = contract["instrument_key"]
            print(f" Checking: {name} ({inst_key})")

            # Fetch Candles (Day interval, recent history)
            candles = fetch_expired_historical_candles(
                inst_key,
                "day",
                expiry,  # from_date (Upstox backward logic check?)
                expiry,  # to_date
            )

            # Note: In previous edits we noticed Upstox params are weird: {instrument_key}/{interval}/{to_date}/{from_date}
            # fetch_expired_historical_candles(key, interval, from_date, to_date)
            # function definition in script: def fetch_expired_historical_candles(instrument_key, interval, from_date, to_date)
            # inside script: url = .../{to_date}/{from_date}

            print(f"  -> Candle Count: {len(candles)}")
            if candles:
                print(f"  -> First Candle: {candles[0]}")
            else:
                print("  -> No candles returned.")


if __name__ == "__main__":
    # The script uses sync requests inside, so we don't strictly need asyncio loop unless reusing async wrappers
    # But for compatibility with existing patterns
    try:
        asyncio.run(verify_candles())
    except Exception as e:
        print(f"Test Error: {e}")
