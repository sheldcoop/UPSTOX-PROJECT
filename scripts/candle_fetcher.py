#!/usr/bin/env python3
"""
Parameterized Candle Fetcher for Upstox API
Fetches historical OHLCV data for custom symbols, dates, and timeframes.
Stores in SQLite candles table.
"""
import sqlite3
import requests
import json
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import time
import logging

# Add scripts dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auth_manager import AuthManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
DB_PATH = "market_data.db"
API_BASE = "https://api.upstox.com/v2"
TIMEFRAME_MAP = {
    "1m": "1minute",
    "5m": "5minute",
    "15m": "15minute",
    "1h": "30minute",
    "1d": "day",
}


def get_access_token() -> str:
    """Retrieve valid OAuth token using AuthManager with auto-refresh."""
    try:
        auth = AuthManager()
        token = auth.get_valid_token()

        if not token:
            raise Exception("❌ No valid token found. Run ./authenticate.sh first.")

        logger.info(f"✅ Retrieved token (auto-refreshed if needed)")
        return token
    except Exception as e:
        logger.error(f"❌ Failed to get token: {e}")
        raise


def init_db():
    """Create candles table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check if new candles table exists, if not create it
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS candles_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            instrument_key TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER NOT NULL,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(instrument_key, timeframe, timestamp)
        )
    """
    )
    # Create index for fast lookups
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_symbol_timeframe_timestamp 
        ON candles_new(symbol, timeframe, timestamp)
    """
    )
    conn.commit()
    conn.close()
    logger.info("✅ Candles table initialized")


def fetch_candles(
    symbol: str, timeframe: str, start_date: str, end_date: str, access_token: str
) -> List[Dict]:
    """
    Fetch candles from Upstox API.

    Args:
        symbol: Instrument key (e.g., 'NSE_EQ|INE002A01018' for INFY)
        timeframe: '1m', '5m', '15m', '1h', '1d'
        start_date: 'YYYY-MM-DD'
        end_date: 'YYYY-MM-DD'
        access_token: OAuth token

    Returns:
        List of candle dicts with OHLCV data
    """
    if timeframe not in TIMEFRAME_MAP:
        raise ValueError(
            f"Invalid timeframe: {timeframe}. Use: {list(TIMEFRAME_MAP.keys())}"
        )

    api_timeframe = TIMEFRAME_MAP[timeframe]
    # URL format: /historical-candle/:instrument_key/:interval/:to_date/:from_date
    url = (
        f"{API_BASE}/historical-candle/{symbol}/{api_timeframe}/{end_date}/{start_date}"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    logger.info(f"📊 Fetching {symbol} {timeframe} from {start_date} to {end_date}...")

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        data = response.json()

        if data.get("status") != "success":
            logger.error(f"❌ API error: {data.get('errors', data)}")
            return []

        candles = data.get("data", {}).get("candles", [])
        logger.info(f"✅ Fetched {len(candles)} candles for {symbol}")

        return candles

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed for {symbol}: {e}")
        return []


def parse_candle(
    candle: List, symbol: str, instrument_key: str, timeframe: str
) -> Optional[Dict]:
    """
    Parse Upstox candle format.
    Upstox returns: [timestamp, open, high, low, close, volume, oi]

    Returns:
        Dict with parsed OHLCV data
    """
    try:
        timestamp_str, open_p, high, low, close, volume, oi = candle
        # Convert timestamp string to Unix timestamp
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        timestamp = int(dt.timestamp())

        return {
            "symbol": symbol,
            "instrument_key": instrument_key,
            "timeframe": timeframe,
            "timestamp": timestamp,
            "open": float(open_p),
            "high": float(high),
            "low": float(low),
            "close": float(close),
            "volume": int(volume),
        }
    except Exception as e:
        logger.error(f"❌ Error parsing candle {candle}: {e}")
        return None


def store_candles(candles: List[Dict]) -> int:
    """Store candles in DB. Returns count of inserted/updated rows."""
    if not candles:
        return 0

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    inserted = 0
    for candle in candles:
        if not candle:
            continue

        try:
            cur.execute(
                """
                INSERT OR REPLACE INTO candles_new 
                (symbol, instrument_key, timeframe, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    candle["symbol"],
                    candle["instrument_key"],
                    candle["timeframe"],
                    candle["timestamp"],
                    candle["open"],
                    candle["high"],
                    candle["low"],
                    candle["close"],
                    candle["volume"],
                ),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            pass  # Duplicate, skip
        except Exception as e:
            logger.error(f"❌ Error storing candle: {e}")

    conn.commit()
    conn.close()

    logger.info(f"✅ Stored {inserted} candles")
    return inserted


def resolve_symbols(symbols: List[str]) -> List[Tuple]:
    """
    Resolve symbol names to instrument keys via database lookup.

    Args:
        symbols: List of symbol names (e.g., ['INFY', 'TCS'])

    Returns:
        List of (symbol, instrument_key) tuples
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    results = []
    for sym in symbols:
        # Search for symbol in exchange_listings
        cur.execute(
            """
            SELECT symbol, instrument_key FROM exchange_listings 
            WHERE symbol = ? LIMIT 1
        """,
            (sym,),
        )
        row = cur.fetchone()
        if row:
            results.append(row)
            logger.info(f"✅ Resolved {sym} → {row[1]}")
        else:
            logger.warning(f"⚠️  Symbol {sym} not found in database")

    conn.close()
    return results


def fetch_and_store(
    symbols: List[str] = None,
    timeframe: str = "1d",
    start_date: str = None,
    end_date: str = None,
    db_query: str = None,
    rate_limit_delay: float = 0.5,
):
    """
    Main function: Fetch candles and store in DB.

    Args:
        symbols: List of symbols to fetch (e.g., ['INFY', 'TCS'])
                 OR leave as None and use db_query
        timeframe: '1m', '5m', '15m', '1h', '1d'
        start_date: 'YYYY-MM-DD' (default: 1 year ago)
        end_date: 'YYYY-MM-DD' (default: today)
        db_query: SQL WHERE clause for querying from master_stocks
                  (e.g., "segment='NSE_EQ' AND has_fno=1")
        rate_limit_delay: Seconds between API calls
    """
    init_db()

    # Set default dates
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    logger.info(f"📅 Date range: {start_date} to {end_date}")
    logger.info(f"⏱️  Timeframe: {timeframe}")

    # Get access token
    try:
        access_token = get_access_token()
    except Exception as e:
        logger.error(str(e))
        return

    # Get symbol list
    if db_query:
        logger.info(f"🔍 Querying DB: {db_query}")
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        query = "SELECT symbol, instrument_key FROM exchange_listings"
        if db_query:
            query += f" WHERE {db_query}"
        cur.execute(query)
        symbol_list = cur.fetchall()
        conn.close()
    elif symbols:
        logger.info(f"🔍 Resolving {len(symbols)} symbols...")
        symbol_list = resolve_symbols(symbols)
    else:
        logger.error("❌ Provide either symbols list or db_query")
        return

    # Fetch candles for each symbol
    total_candles = 0
    for display_name, instrument_key in symbol_list:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {display_name} ({instrument_key})")
        logger.info(f"{'='*60}")

        try:
            # Fetch from API
            raw_candles = fetch_candles(
                instrument_key, timeframe, start_date, end_date, access_token
            )

            # Parse candles
            parsed = [
                parse_candle(c, display_name, instrument_key, timeframe)
                for c in raw_candles
            ]
            parsed = [c for c in parsed if c]  # Remove None values

            # Store in DB
            stored = store_candles(parsed)
            total_candles += stored

            # Rate limit
            time.sleep(rate_limit_delay)

        except Exception as e:
            logger.error(f"❌ Failed for {display_name}: {e}")
            continue

    logger.info(f"\n{'='*60}")
    logger.info(f"✅ COMPLETE: Stored {total_candles} total candles")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch historical candles from Upstox API"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        help='Comma-separated symbols (e.g., "INFY,TCS,RELIANCE")',
    )
    parser.add_argument(
        "--timeframe", type=str, default="1d", help="1m, 5m, 15m, 1h, 1d (default: 1d)"
    )
    parser.add_argument(
        "--start", type=str, help="Start date YYYY-MM-DD (default: 1 year ago)"
    )
    parser.add_argument("--end", type=str, help="End date YYYY-MM-DD (default: today)")
    parser.add_argument(
        "--db-query",
        type=str,
        help="SQL WHERE clause (e.g., \"segment='NSE_EQ' AND has_fno=1\")",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Rate limit delay between API calls (default: 0.5s)",
    )

    args = parser.parse_args()

    symbols = args.symbols.split(",") if args.symbols else None

    fetch_and_store(
        symbols=symbols,
        timeframe=args.timeframe,
        start_date=args.start,
        end_date=args.end,
        db_query=args.db_query,
        rate_limit_delay=args.delay,
    )
