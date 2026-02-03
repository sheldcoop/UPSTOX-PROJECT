#!/usr/bin/env python3
"""
Expired Options Fetcher - Retrieve historical/expired option contract data

Fetches option chain data for expired option contracts from Upstox API.
Useful for backtesting and historical analysis of expired derivatives.

Supports:
  • Single underlying, single expiry
  • Single underlying, multiple expiries
  • Multiple underlyings, single expiry
  • Multiple underlyings, multiple expiries (batch mode)
  • Filtering by option type (CE/PE) and strike price
  • Querying stored options from database

Usage:
    # Single underlying, single expiry
    python expired_options_fetcher.py --underlying NIFTY --expiry 2025-01-22

    # Multiple expiries for one underlying
    python expired_options_fetcher.py --underlying NIFTY --expiry 2025-01-22,2025-02-19,2025-03-26

    # Multiple underlyings, single expiry
    python expired_options_fetcher.py --underlying NIFTY,BANKNIFTY,INFY --expiry 2025-01-22

    # Multiple underlyings, all available expiries (batch)
    python expired_options_fetcher.py --underlying NIFTY,BANKNIFTY --batch

    # Filter by option type
    python expired_options_fetcher.py --underlying NIFTY --batch --option-type CE

    # List available expiries
    python expired_options_fetcher.py --underlying NIFTY,BANKNIFTY --list-expiries

    # Query stored options
    python expired_options_fetcher.py --query NIFTY@2025-01-22
"""

import os
import sys
import sqlite3
import argparse
import requests
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.auth_manager import AuthManager


def ensure_token_valid():
    """Get a valid access token using AuthManager."""
    try:
        auth = AuthManager()
        # Use simple get_valid_token logic (assuming single user setup)
        # AuthManager.get_valid_token requires user_id usually, but defaults to 'default'
        token = auth.get_valid_token()
        if not token:
            raise Exception("No valid token returned from AuthManager")
        return token
    except Exception as e:
        print(f"Auth Error: {e}")
        raise


# Constants
API_BASE_URL = "https://api.upstox.com/v2"
DB_PATH = "market_data.db"

# Mapping for common symbols to Instrument Keys (required for Expired API)
INSTRUMENT_KEYS = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "FINNIFTY": "NSE_INDEX|Nifty Fin Service",
    "INDIA VIX": "NSE_INDEX|India VIX",
}


def get_instrument_key(symbol: str) -> str:
    """Resolve symbol to instrument key using hardcoded map or DB lookup."""
    upper_sym = symbol.upper().strip()

    # 1. Check Hardcoded Map
    if upper_sym in INSTRUMENT_KEYS:
        return INSTRUMENT_KEYS[upper_sym]

    # 2. Check if it looks like a key already (contains |)
    if "|" in upper_sym:
        return upper_sym

    # 3. Try DB Lookup (Equity/Index)
    try:
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            # Try exact match on symbol first (e.g. RELIANCE)
            # Prioritize NSE_EQ over others
            c.execute(
                """
                SELECT instrument_key FROM instruments 
                WHERE symbol = ? AND segment_id IN ('NSE_EQ', 'BSE_EQ') 
                ORDER BY CASE WHEN segment_id = 'NSE_EQ' THEN 1 ELSE 2 END 
                LIMIT 1
            """,
                (upper_sym,),
            )
            row = c.fetchone()
            if row:
                conn.close()
                return row[0]

            # Try trading symbol match
            c.execute(
                "SELECT instrument_key FROM instruments WHERE trading_symbol = ? LIMIT 1",
                (upper_sym,),
            )
            row = c.fetchone()
            if row:
                conn.close()
                return row[0]

            conn.close()
    except Exception as e:
        print(f"DB Lookup failed for {symbol}: {e}")

    # Default: Return as is (might fail if API needs key)
    return symbol


def ensure_expired_options_table() -> None:
    """Create expired_options table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS expired_options (
            id INTEGER PRIMARY KEY,
            underlying_symbol TEXT NOT NULL,
            option_type TEXT NOT NULL,
            strike_price REAL NOT NULL,
            expiry_date TEXT NOT NULL,
            tradingsymbol TEXT NOT NULL,
            exchange_token TEXT NOT NULL,
            exchange TEXT DEFAULT 'NFO',
            last_trading_price REAL,
            settlement_price REAL,
            open_interest INTEGER,
            last_volume INTEGER,
            fetch_timestamp INTEGER NOT NULL,
            UNIQUE(underlying_symbol, strike_price, option_type, expiry_date)
        )
    """
    )

    # Create index for common queries
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_expired_opt_underlying_expiry 
        ON expired_options(underlying_symbol, expiry_date)
    """
    )

    # Create table for expired candles (OHLC)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS expired_candles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instrument_key TEXT NOT NULL,
            interval TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            oi INTEGER,
            UNIQUE(instrument_key, interval, timestamp)
        )
    """
    )

    conn.commit()
    conn.close()


def get_available_expiries(underlying_symbol: str) -> List[str]:
    """
    Get all available expiry dates for an underlying.

    Args:
        underlying_symbol: Symbol like NIFTY, BANKNIFTY, INFY

    Returns:
        List of expiry dates in YYYY-MM-DD format
    """
    token = ensure_token_valid()

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    # Use Expired Instruments API
    # Endpoint: /v2/expired-instruments/expiries

    inst_key = get_instrument_key(underlying_symbol)

    params = {"instrument_key": inst_key}

    try:
        print(f"I: Fetching expired expiries for {inst_key}...")
        response = requests.get(
            f"{API_BASE_URL}/expired-instruments/expiries",
            headers=headers,
            params=params,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                expiries = data.get("data", [])
                print(f"✓ Found {len(expiries)} expiry dates for {underlying_symbol}")
                return expiries
        else:
            print(f"✗ Failed to fetch expiries: {response.status_code}")
            try:
                print(f"  Response: {response.json()}")
            except:
                print(f"   Response: {response.text[:200]}")
            return []

    except requests.RequestException as e:
        print(f"✗ Request error: {e}")
        return []


def fetch_expired_future_contracts(
    underlying_symbol: str, expiry_date: str
) -> List[Dict[str, Any]]:
    """
    Fetch expired future contracts from Upstox API.

    Args:
        underlying_symbol: Symbol like NIFTY, BANKNIFTY, INFY
        expiry_date: Expiry date in YYYY-MM-DD format

    Returns:
        List of future contract dictionaries
    """
    token = ensure_token_valid()

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    # Use Expired Instruments API
    # Endpoint: /v2/expired-instruments/future/contract

    inst_key = get_instrument_key(underlying_symbol)

    params = {"instrument_key": inst_key, "expiry_date": expiry_date}

    try:
        print(f"\n📡 Fetching expired futures for {inst_key} expiry {expiry_date}")

        response = requests.get(
            f"{API_BASE_URL}/expired-instruments/future/contract",
            headers=headers,
            params=params,
            timeout=15,
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                contracts = data.get("data", [])
                print(f"✓ Fetched {len(contracts)} future contract(s)")
                return contracts
            else:
                print(f"✗ API returned error: {data.get('message')}")
                return []
        else:
            print(f"✗ Failed: {response.status_code} - {response.text[:200]}")
            return []

    except Exception as e:
        print(f"Error fetching future contracts: {e}")
        return []


def fetch_expired_option_contracts(
    underlying_symbol: str,
    expiry_date: str,
    option_type: Optional[str] = None,
    strike_price: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch expired option contracts from Upstox API.

    Args:
        underlying_symbol: Symbol like NIFTY, BANKNIFTY, INFY
        expiry_date: Expiry date in YYYY-MM-DD format
        option_type: Optional filter (CE or PE)
        strike_price: Optional filter for specific strike

    Returns:
        List of option contract dictionaries
    """
    token = ensure_token_valid()

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    # Use Expired Instruments API
    # Endpoint: /v2/expired-instruments/option/contract

    inst_key = get_instrument_key(underlying_symbol)

    params = {"instrument_key": inst_key, "expiry_date": expiry_date}

    # Note: The expired API might not support filtering by option_type/strike directly in params
    # We might need to filter client-side if the API ignores these.
    # But let's try passing them just in case, or filter after fetching.

    try:
        print(f"\n📡 Fetching expired options for {inst_key} expiry {expiry_date}")

        response = requests.get(
            f"{API_BASE_URL}/expired-instruments/option/contract",
            headers=headers,
            params=params,
            timeout=15,
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                contracts = data.get("data", [])
                if contracts:
                    ce_c = sum(1 for c in contracts if c.get("instrument_type") == "CE")
                    pe_c = sum(1 for c in contracts if c.get("instrument_type") == "PE")
                    print(
                        f"DEBUG RAW API: CE={ce_c}, PE={pe_c} (Total {len(contracts)})"
                    )
                    print(f"DEBUG SAMPLE CONTRACT: {contracts[0]}")

                # Manual filtering if needed
                if option_type:
                    contracts = [
                        c for c in contracts if c.get("option_type") == option_type
                    ]
                if strike_price:
                    contracts = [
                        c for c in contracts if c.get("strike_price") == strike_price
                    ]

                print(f"✓ Fetched {len(contracts)} contract(s)")
                return contracts
            else:
                print(f"✗ API returned error: {data.get('message')}")
                return []
        else:
            print(f"✗ Failed: {response.status_code} - {response.text[:200]}")
            return []

    except Exception as e:
        print(f"Error fetching contracts: {e}")
        return []


def parse_option_data(
    contract: Dict[str, Any], underlying_symbol: str, expiry_date: str
) -> Dict[str, Any]:
    """
    Parse option contract data from API response.

    Args:
        contract: Contract data from API
        underlying_symbol: Underlying symbol
        expiry_date: Expiry date

    Returns:
        Parsed option data dictionary
    """
    # API uses 'trading_symbol' but we check both just in case
    tradingsymbol = contract.get("trading_symbol") or contract.get("tradingsymbol", "")

    # Extract option type: Prefer explicit field, else parse
    option_type = contract.get("instrument_type")
    if not option_type:
        # Fallback parsing
        option_type = "CE" if "CE" in tradingsymbol else "PE"

    # Try to extract strike price from contract or tradingsymbol
    strike_price = contract.get("strike_price")
    if not strike_price and tradingsymbol:
        # Parse from tradingsymbol like NIFTY22JAN23000CE
        try:
            strike_str = tradingsymbol.replace("NIFTY", "").replace("BANKNIFTY", "")
            strike_str = (
                strike_str.replace("JAN", "").replace("FEB", "").replace("MAR", "")
            )
            strike_str = (
                strike_str.replace("APR", "").replace("MAY", "").replace("JUN", "")
            )
            strike_str = (
                strike_str.replace("JUL", "").replace("AUG", "").replace("SEP", "")
            )
            strike_str = (
                strike_str.replace("OCT", "").replace("NOV", "").replace("DEC", "")
            )
            strike_str = strike_str.replace("CE", "").replace("PE", "").strip()

            if strike_str and strike_str.isdigit():
                strike_price = float(strike_str)
        except (ValueError, IndexError):
            strike_price = None

    return {
        "underlying_symbol": underlying_symbol,
        "option_type": option_type,
        "strike_price": strike_price,
        "expiry_date": expiry_date,
        "tradingsymbol": tradingsymbol,
        "exchange_token": contract.get("exchange_token", ""),
        "exchange": contract.get("exchange", "NFO"),
        "last_trading_price": None,
        "settlement_price": None,
        "open_interest": None,
        "last_volume": None,
        "fetch_timestamp": int(datetime.now().timestamp()),
    }


def parse_future_data(
    contract: Dict[str, Any], underlying_symbol: str, expiry_date: str
) -> Dict[str, Any]:
    """
    Parse future contract data from API response.

    Args:
        contract: Future Contract data from API
        underlying_symbol: Underlying symbol
        expiry_date: Expiry date

    Returns:
        Parsed dictionary compatible with store_expired_options
    """
    tradingsymbol = contract.get("tradingsymbol", "")

    # Futures don't have strike or option type (CE/PE) in the same way
    # We will map them to:
    # option_type = "FUT"
    # strike_price = 0.0

    return {
        "underlying_symbol": underlying_symbol,
        "option_type": "FUT",
        "strike_price": 0.0,
        "expiry_date": expiry_date,
        "tradingsymbol": tradingsymbol,
        "exchange_token": contract.get("exchange_token", ""),
        "exchange": contract.get("exchange", "NFO"),
        "last_trading_price": None,
        "settlement_price": None,
        "open_interest": None,
        "last_volume": None,
        "fetch_timestamp": int(datetime.now().timestamp()),
    }


def store_expired_options(options: List[Dict[str, Any]]) -> int:
    """
    Store expired option contracts in database.

    Args:
        options: List of parsed option dictionaries

    Returns:
        Number of records inserted/updated
    """
    if not options:
        print("⚠ No options to store")
        return 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    inserted = 0
    skipped = 0

    for opt in options:
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO expired_options (
                    underlying_symbol, option_type, strike_price, expiry_date,
                    tradingsymbol, exchange_token, exchange,
                    last_trading_price, settlement_price, open_interest, last_volume,
                    fetch_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    opt["underlying_symbol"],
                    opt["option_type"],
                    opt["strike_price"],
                    opt["expiry_date"],
                    opt["tradingsymbol"],
                    opt["exchange_token"],
                    opt["exchange"],
                    opt["last_trading_price"],
                    opt["settlement_price"],
                    opt["open_interest"],
                    opt["last_volume"],
                    opt["fetch_timestamp"],
                ),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1

    conn.commit()
    conn.close()

    print(f"✓ Stored {inserted} option records (skipped {skipped} duplicates)")
    return inserted


def get_stored_expired_options(
    underlying_symbol: str, expiry_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve stored expired options from database.

    Args:
        underlying_symbol: Symbol to filter by
        expiry_date: Optional expiry date filter

    Returns:
        List of stored option records
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if expiry_date:
        cursor.execute(
            """
            SELECT * FROM expired_options 
            WHERE underlying_symbol = ? AND expiry_date = ?
            ORDER BY strike_price, option_type
        """,
            (underlying_symbol, expiry_date),
        )
    else:
        cursor.execute(
            """
            SELECT * FROM expired_options 
            WHERE underlying_symbol = ?
            ORDER BY expiry_date DESC, strike_price, option_type
        """,
            (underlying_symbol,),
        )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def print_options_summary(options: List[Dict[str, Any]]) -> None:
    """Print summary of stored options."""
    if not options:
        print("No options found")
        return

    # Group by strike and type
    by_strike = {}
    for opt in options:
        strike = opt["strike_price"]
        if strike not in by_strike:
            by_strike[strike] = {"CE": None, "PE": None}
        by_strike[strike][opt["option_type"]] = opt

    print("\n📊 Expired Options Summary:")
    print(f"{'Strike':<10} {'Call (CE)':<30} {'Put (PE)':<30}")
    print("-" * 70)

    for strike in sorted(by_strike.keys()):
        ce = by_strike[strike].get("CE")
        pe = by_strike[strike].get("PE")

        ce_symbol = ce["tradingsymbol"] if ce else "-"
        pe_symbol = pe["tradingsymbol"] if pe else "-"

        print(f"{strike:<10} {ce_symbol:<30} {pe_symbol:<30}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Fetch and store expired option contracts"
    )
    parser.add_argument(
        "--underlying",
        help="Underlying symbol (NIFTY, BANKNIFTY, INFY, etc.). Use comma-separated for multiple (NIFTY,BANKNIFTY,INFY)",
    )
    parser.add_argument(
        "--expiry",
        help="Expiry date (YYYY-MM-DD). Use comma-separated for multiple (2025-01-22,2025-02-19). If not provided, fetches all available expiries",
    )
    parser.add_argument(
        "--option-type", choices=["CE", "PE"], help="Filter by option type (CE or PE)"
    )
    parser.add_argument("--strike", type=float, help="Filter by strike price")
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Fetch all available expiries for given underlyings",
    )
    parser.add_argument(
        "--list-expiries", action="store_true", help="List all available expiry dates"
    )
    parser.add_argument(
        "--query", help="Query stored expired options (example: NIFTY@2025-01-22)"
    )
    parser.add_argument(
        "--fetch-futures",
        action="store_true",
        help="Also fetch expired future contracts",
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.underlying and not args.query and not args.list_expiries:
        print(
            "✗ Error: --underlying is required (unless using --query or --list-expiries)"
        )
        print("   Example: --underlying NIFTY,BANKNIFTY,INFY")
        return

    # Initialize database
    ensure_expired_options_table()

    # List expiries for single underlying
    if args.list_expiries:
        if not args.underlying:
            print("✗ Error: --underlying required with --list-expiries")
            return
        underlyings = args.underlying.split(",")
        for underlying in underlyings:
            underlying = underlying.strip()
            expiries = get_available_expiries(underlying)
            print(f"\n📅 Available Expiry Dates for {underlying}:")
            for exp in expiries:
                print(f"   {exp}")
        return

    # Query stored options
    if args.query:
        parts = args.query.split("@")
        symbol = parts[0]
        exp_date = parts[1] if len(parts) > 1 else None

        stored = get_stored_expired_options(symbol, exp_date)
        if stored:
            # Separate Futures and Options for display
            futures = [o for o in stored if o["option_type"] == "FUT"]
            options = [o for o in stored if o["option_type"] != "FUT"]

            print(f"\n✓ Found {len(stored)} stored expired instruments for {symbol}")
            if futures:
                print(f"  - {len(futures)} Future Contracts")
            if options:
                print_options_summary(options)
        else:
            print(f"✗ No stored instruments found for {symbol}")
        return

    # Parse underlyings (comma-separated)
    underlyings = [u.strip() for u in args.underlying.split(",")]

    # Parse expiries (comma-separated) or fetch all
    if args.expiry:
        expiries_list = [e.strip() for e in args.expiry.split(",")]
    elif args.batch:
        # Fetch all available expiries for each underlying
        expiries_list = []
        for underlying in underlyings:
            avail_expiries = get_available_expiries(underlying)
            expiries_list.extend(avail_expiries)
        expiries_list = list(set(expiries_list))  # Remove duplicates
        print(f"📅 Found {len(expiries_list)} unique expiry dates across underlyings")
    else:
        # Default: get first available expiry for first underlying
        expiries_list = get_available_expiries(underlyings[0])
        if not expiries_list:
            print(f"✗ No expiry dates available for {underlyings[0]}")
            return
        expiries_list = [expiries_list[0]]
        print(f"Using expiry: {expiries_list[0]}")

    # Batch fetch all combinations
    print(f"\n🔄 Starting batch fetch...")
    print(f"   Underlyings: {len(underlyings)}")
    print(f"   Expiries: {len(expiries_list)}")
    total_count = 0

    for underlying in underlyings:
        for expiry in expiries_list:
            try:
                print(f"\n======== {underlying} @ {expiry} ========")

                # 1. Fetch Options
                print(f"--- Options ---")
                contracts = fetch_expired_option_contracts(
                    underlying, expiry, args.option_type, args.strike
                )

                # Parse and store options
                if contracts:
                    parsed_options = [
                        parse_option_data(contract, underlying, expiry)
                        for contract in contracts
                    ]
                    stored_count = store_expired_options(parsed_options)
                    total_count += stored_count

                    stored_db = get_stored_expired_options(underlying, expiry)
                    ce_count = sum(1 for o in stored_db if o["option_type"] == "CE")
                    pe_count = sum(1 for o in stored_db if o["option_type"] == "PE")
                    print(
                        f"   ✓ Stored {stored_count} options ({ce_count} CE, {pe_count} PE)"
                    )
                else:
                    print(f"   ⚠ No option contracts found")

                # 2. Fetch Futures (if requested)
                if args.fetch_futures:
                    print(f"--- Futures ---")
                    fut_contracts = fetch_expired_future_contracts(underlying, expiry)

                    if fut_contracts:
                        parsed_futures = [
                            parse_future_data(contract, underlying, expiry)
                            for contract in fut_contracts
                        ]
                        stored_fut = store_expired_options(parsed_futures)
                        total_count += stored_fut
                        print(f"   ✓ Stored {stored_fut} future contracts")
                    else:
                        print(
                            f"   ⚠ No future contracts found (Futures generally expire monthly)"
                        )

            except Exception as e:
                print(f"   ✗ Error: {e}")
                continue

    # Final summary
    print(f"\n" + "=" * 70)
    print(f"📊 BATCH FETCH COMPLETE")
    print(f"=" * 70)
    print(f"Total Options Stored: {total_count}")
    print(f"Underlyings Processed: {len(underlyings)}")
    print(f"Expiries Processed: {len(expiries_list)}")
    print(f"Total Combinations: {len(underlyings) * len(expiries_list)}")


if __name__ == "__main__":
    main()

# ============================================================================
# NEW: Historical Candle Support (Applied via User Request)
# ============================================================================


def fetch_expired_historical_candles(
    instrument_key: str, interval: str, from_date: str, to_date: str
) -> List[Any]:
    """
    Fetch historical candles for an expired instrument.
    Endpoint: /expired-instruments/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}
    """
    try:
        token = ensure_token_valid()
    except Exception as e:
        print(f"Token Error: {e}")
        return []

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    # API Format: /expired-instruments/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}
    # Important: Upstox 'to_date' comes BEFORE 'from_date' in path for historical V2
    url = f"{API_BASE_URL}/expired-instruments/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"

    try:
        response = requests.get(url, headers=headers, timeout=12)

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                candles = data.get("data", {}).get("candles", [])
                if not candles and isinstance(data.get("data"), list):
                    candles = data.get("data")
                return candles
            else:
                return []
        else:
            print(f"Candle fetch failed for {instrument_key}: {response.status_code}")
            return []

    except Exception as e:
        print(f"Error fetching candles: {e}")
        return []


def store_expired_candles(
    instrument_key: str, interval: str, candles: List[List[Any]]
) -> int:
    """
    Store fetched candles into sqlite.
    Candle format: [timestamp, open, high, low, close, volume, oi]
    """
    if not candles:
        return 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    count = 0
    try:
        data_to_insert = []
        for c in candles:
            # Format: [timestamp_str, open, high, low, close, volume, oi]
            if len(c) < 7:
                continue

            ts = c[0]
            op = float(c[1])
            hi = float(c[2])
            lo = float(c[3])
            cl = float(c[4])
            vol = int(c[5])
            oi = int(c[6])

            data_to_insert.append(
                (instrument_key, interval, ts, op, hi, lo, cl, vol, oi)
            )

        cursor.executemany(
            """
            INSERT OR IGNORE INTO expired_candles 
            (instrument_key, interval, timestamp, open, high, low, close, volume, oi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            data_to_insert,
        )

        count = cursor.rowcount
        conn.commit()
    except Exception as e:
        print(f"Error storing candles: {e}")
    finally:
        conn.close()

    return count
