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
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.db_manager import initialize_database, get_oauth_token
from scripts.oauth_server import ensure_token_valid


# Constants
API_BASE_URL = "https://api.upstox.com/v2"
DB_PATH = "market_data.db"


def ensure_expired_options_table() -> None:
    """Create expired_options table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
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
    """)
    
    # Create index for common queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_expired_opt_underlying_expiry 
        ON expired_options(underlying_symbol, expiry_date)
    """)
    
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
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    params = {
        "underlying_symbol": underlying_symbol
    }
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/option/expiry",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                expiries = data.get("data", [])
                print(f"✓ Found {len(expiries)} expiry dates for {underlying_symbol}")
                for exp in expiries[:5]:
                    print(f"  - {exp}")
                if len(expiries) > 5:
                    print(f"  ... and {len(expiries) - 5} more")
                return expiries
        else:
            print(f"✗ Failed to fetch expiries: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return []
    
    except requests.RequestException as e:
        print(f"✗ Request error: {e}")
        return []


def fetch_expired_option_contracts(
    underlying_symbol: str,
    expiry_date: str,
    option_type: Optional[str] = None,
    strike_price: Optional[float] = None
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
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    params = {
        "underlying_symbol": underlying_symbol,
        "expiry_date": expiry_date
    }
    
    if option_type:
        params["option_type"] = option_type
    if strike_price:
        params["strike_price"] = strike_price
    
    try:
        print(f"\n📡 Fetching expired options for {underlying_symbol} expiry {expiry_date}")
        if option_type:
            print(f"   Filter: {option_type}")
        if strike_price:
            print(f"   Strike: {strike_price}")
        
        response = requests.get(
            f"{API_BASE_URL}/option/contract",
            headers=headers,
            params=params,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                contracts = data.get("data", [])
                print(f"✓ Fetched {len(contracts)} contract(s)")
                return contracts
            else:
                print(f"✗ API returned error: {data.get('message')}")
                return []
        else:
            print(f"✗ HTTP {response.status_code}: {response.text[:200]}")
            return []
    
    except requests.RequestException as e:
        print(f"✗ Request error: {e}")
        return []


def parse_option_data(contract: Dict[str, Any], underlying_symbol: str, expiry_date: str) -> Dict[str, Any]:
    """
    Parse option contract data from API response.
    
    Args:
        contract: Contract data from API
        underlying_symbol: Underlying symbol
        expiry_date: Expiry date
        
    Returns:
        Parsed option data dictionary
    """
    tradingsymbol = contract.get("tradingsymbol", "")
    
    # Extract option type and strike from tradingsymbol
    # Example: NIFTY22JAN23000CE -> extract CE and 23000
    option_type = "CE" if "CE" in tradingsymbol else "PE"
    
    # Try to extract strike price from contract or tradingsymbol
    strike_price = contract.get("strike_price")
    if not strike_price and tradingsymbol:
        # Parse from tradingsymbol like NIFTY22JAN23000CE
        try:
            strike_str = tradingsymbol.replace("NIFTY", "").replace("BANKNIFTY", "")
            strike_str = strike_str.replace("JAN", "").replace("FEB", "").replace("MAR", "")
            strike_str = strike_str.replace("APR", "").replace("MAY", "").replace("JUN", "")
            strike_str = strike_str.replace("JUL", "").replace("AUG", "").replace("SEP", "")
            strike_str = strike_str.replace("OCT", "").replace("NOV", "").replace("DEC", "")
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
        "last_trading_price": None,  # Not provided by this endpoint
        "settlement_price": None,    # Not provided by this endpoint
        "open_interest": None,        # Not provided by this endpoint
        "last_volume": None,          # Not provided by this endpoint
        "fetch_timestamp": int(datetime.now().timestamp())
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
            cursor.execute("""
                INSERT OR REPLACE INTO expired_options (
                    underlying_symbol, option_type, strike_price, expiry_date,
                    tradingsymbol, exchange_token, exchange,
                    last_trading_price, settlement_price, open_interest, last_volume,
                    fetch_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
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
                opt["fetch_timestamp"]
            ))
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1
    
    conn.commit()
    conn.close()
    
    print(f"✓ Stored {inserted} option records (skipped {skipped} duplicates)")
    return inserted


def get_stored_expired_options(
    underlying_symbol: str,
    expiry_date: Optional[str] = None
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
        cursor.execute("""
            SELECT * FROM expired_options 
            WHERE underlying_symbol = ? AND expiry_date = ?
            ORDER BY strike_price, option_type
        """, (underlying_symbol, expiry_date))
    else:
        cursor.execute("""
            SELECT * FROM expired_options 
            WHERE underlying_symbol = ?
            ORDER BY expiry_date DESC, strike_price, option_type
        """, (underlying_symbol,))
    
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
        help="Underlying symbol (NIFTY, BANKNIFTY, INFY, etc.). Use comma-separated for multiple (NIFTY,BANKNIFTY,INFY)"
    )
    parser.add_argument(
        "--expiry",
        help="Expiry date (YYYY-MM-DD). Use comma-separated for multiple (2025-01-22,2025-02-19). If not provided, fetches all available expiries"
    )
    parser.add_argument(
        "--option-type",
        choices=["CE", "PE"],
        help="Filter by option type (CE or PE)"
    )
    parser.add_argument(
        "--strike",
        type=float,
        help="Filter by strike price"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Fetch all available expiries for given underlyings"
    )
    parser.add_argument(
        "--list-expiries",
        action="store_true",
        help="List all available expiry dates"
    )
    parser.add_argument(
        "--query",
        help="Query stored expired options (example: NIFTY@2025-01-22)"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.underlying and not args.query and not args.list_expiries:
        print("✗ Error: --underlying is required (unless using --query or --list-expiries)")
        print("   Example: --underlying NIFTY,BANKNIFTY,INFY")
        return
    
    # Initialize database
    initialize_database()
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
            print(f"\n✓ Found {len(stored)} stored expired options for {symbol}")
            print_options_summary(stored)
        else:
            print(f"✗ No stored options found for {symbol}")
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
                print(f"\n📡 Fetching {underlying} @ {expiry}...")
                
                # Fetch contracts
                contracts = fetch_expired_option_contracts(
                    underlying,
                    expiry,
                    args.option_type,
                    args.strike
                )
                
                if not contracts:
                    print(f"   ⚠ No contracts found for {underlying} @ {expiry}")
                    continue
                
                # Parse and store
                parsed_options = [
                    parse_option_data(contract, underlying, expiry)
                    for contract in contracts
                ]
                
                stored_count = store_expired_options(parsed_options)
                total_count += stored_count
                
                # Print summary
                stored_options = get_stored_expired_options(underlying, expiry)
                ce_count = sum(1 for o in stored_options if o["option_type"] == "CE")
                pe_count = sum(1 for o in stored_options if o["option_type"] == "PE")
                
                print(f"   ✓ Stored {stored_count} options ({ce_count} CE, {pe_count} PE)")
            
            except Exception as e:
                print(f"   ✗ Error: {e}")
                continue
    
    # Final summary
    print(f"\n" + "="*70)
    print(f"📊 BATCH FETCH COMPLETE")
    print(f"="*70)
    print(f"Total Options Stored: {total_count}")
    print(f"Underlyings Processed: {len(underlyings)}")
    print(f"Expiries Processed: {len(expiries_list)}")
    print(f"Total Combinations: {len(underlyings) * len(expiries_list)}")


if __name__ == "__main__":
    main()
