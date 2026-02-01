#!/usr/bin/env python3
"""
Historical Option Data Fetcher - Fetch historical OHLCV data for option contracts
Stores historical candles for specific option strike/expiry combinations
"""

import requests
import sqlite3
import logging
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import time
from dateutil.parser import isoparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = 'market_data.db'
API_BASE_URL = 'https://api.upstox.com/v2'

TIMEFRAME_MAP = {
    '1m': '1minute',
    '5m': '5minute',
    '15m': '15minute',
    '1h': '30minute',  # 30 minute candles in Upstox
    '1d': 'day'
}

# Common option underlyings for Indian market
OPTION_UNDERLYINGS = {
    'NIFTY': 'NSE_INDEX|Nifty 50',
    'BANKNIFTY': 'NSE_INDEX|Nifty Bank',
    'FINNIFTY': 'NSE_INDEX|Nifty Financial Services',
    'MIDCPNIFTY': 'NSE_INDEX|Nifty Midcap 50',
    'SENSEX': 'BSE_INDEX|Sensex',
}


def ensure_option_candles_table():
    """Create option_candles table if it doesn't exist"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create option_candles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS option_candles (
                symbol TEXT NOT NULL,
                instrument_key TEXT NOT NULL,
                option_type TEXT NOT NULL,  -- 'CALL' or 'PUT'
                strike_price REAL NOT NULL,
                expiry_date TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                oi INTEGER,
                created_at INTEGER DEFAULT (strftime('%s','now')),
                UNIQUE(instrument_key, timeframe, timestamp),
                FOREIGN KEY(instrument_key) REFERENCES exchange_listings(instrument_key)
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_option_candles_symbol_expiry_type
            ON option_candles(symbol, expiry_date, option_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_option_candles_instrument_ts
            ON option_candles(instrument_key, timestamp)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("✓ option_candles table ready")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to create option_candles table: {e}")
        return False


def get_access_token() -> Optional[str]:
    """Retrieve valid access token using AuthManager with auto-refresh"""
    try:
        from auth_manager import AuthManager
        auth = AuthManager()
        token = auth.get_valid_token()
        
        if token:
            logger.info("✓ Retrieved valid access token (auto-refreshed if needed)")
            return token
        else:
            logger.error("✗ No valid token found. Run ./authenticate.sh first.")
            return None
    except Exception as e:
        logger.error(f"✗ Failed to get access token: {e}")
        return None


def resolve_option_symbols(
    underlying_key: str,
    strike_prices: List[float],
    expiry_date: str,
    option_types: List[str],
    access_token: str
) -> Dict[str, str]:
    """
    Resolve option symbols to instrument keys
    Returns dict: {f"{strike}_{option_type}": "instrument_key", ...}
    """
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        url = f"{API_BASE_URL}/option/contract"
        params = {
            'instrument_key': underlying_key,
            'expiry_date': expiry_date
        }
        
        logger.info(f"Fetching option contracts for {underlying_key} @ {expiry_date}...")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"✗ Failed to get contracts. Status: {response.status_code}")
            return {}
        
        data = response.json()
        if data.get('status') != 'success':
            logger.error(f"✗ API returned non-success status: {data.get('status')}")
            return {}
        
        contracts = data.get('data', [])
        logger.info(f"✓ Found {len(contracts)} total contracts")
        
        # Build mapping for requested strikes and types
        symbol_map = {}
        for contract in contracts:
            strike = contract.get('strike_price')
            opt_type = contract.get('instrument_type', '').upper()  # CE or PE
            key = contract.get('instrument_key')
            
            if strike in strike_prices and opt_type in option_types:
                map_key = f"{strike}_{opt_type}"
                symbol_map[map_key] = key
        
        logger.info(f"✓ Mapped {len(symbol_map)} requested option contracts")
        return symbol_map
        
    except Exception as e:
        logger.error(f"✗ Failed to resolve option symbols: {e}")
        return {}


def fetch_option_candles(
    instrument_key: str,
    timeframe: str,
    start_date: datetime,
    end_date: datetime,
    access_token: str
) -> Optional[List[List]]:
    """
    Fetch historical OHLCV data for an option contract
    Returns list of candles: [[timestamp, open, high, low, close, volume, oi], ...]
    """
    try:
        if timeframe not in TIMEFRAME_MAP:
            logger.error(f"✗ Invalid timeframe: {timeframe}. Use: {list(TIMEFRAME_MAP.keys())}")
            return None
        
        api_timeframe = TIMEFRAME_MAP[timeframe]
        
        # Upstox API: /historical-candle/:instrument_key/:interval/:to_date/:from_date
        # Note: dates are reversed (to_date first, then from_date)
        to_date_str = end_date.strftime('%Y-%m-%d')
        from_date_str = start_date.strftime('%Y-%m-%d')
        
        url = f"{API_BASE_URL}/historical-candle/{instrument_key}/{api_timeframe}/{to_date_str}/{from_date_str}"
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        logger.info(f"Fetching {instrument_key} {timeframe} from {from_date_str} to {to_date_str}...")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"✗ Failed to fetch candles. Status: {response.status_code}")
            logger.error(f"  URL: {url}")
            return None
        
        data = response.json()
        
        if data.get('status') != 'success':
            logger.error(f"✗ API returned non-success status: {data.get('status')}")
            return None
        
        candles = data.get('data', {}).get('candles', [])
        logger.info(f"✓ Fetched {len(candles)} candles")
        return candles
        
    except Exception as e:
        logger.error(f"✗ Failed to fetch option candles: {e}")
        return None


def parse_option_candle(
    candle: List,
    symbol: str,
    instrument_key: str,
    option_type: str,
    strike_price: float,
    expiry_date: str,
    timeframe: str
) -> Optional[Dict]:
    """
    Parse candle data (7 elements: timestamp, open, high, low, close, volume, oi)
    Timestamp can be ISO8601 string or epoch integer
    Returns candle dict ready for DB insertion
    """
    try:
        if len(candle) < 7:
            logger.warning(f"⚠ Incomplete candle data: {len(candle)} elements")
            return None
        
        timestamp_raw, open_price, high, low, close, volume, oi = candle[:7]
        
        # Convert timestamp to epoch if it's ISO8601 string
        if isinstance(timestamp_raw, str):
            dt = isoparse(timestamp_raw)
            timestamp = int(dt.timestamp())
        else:
            timestamp = int(timestamp_raw)
        
        return {
            'symbol': symbol,
            'instrument_key': instrument_key,
            'option_type': option_type,
            'strike_price': strike_price,
            'expiry_date': expiry_date,
            'timeframe': timeframe,
            'timestamp': timestamp,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': int(volume) if volume else 0,
            'oi': int(oi) if oi else 0,
        }
        
    except Exception as e:
        logger.error(f"✗ Failed to parse candle: {e}")
        return None


def store_option_candles(candles: List[Dict]) -> int:
    """
    Store option candles in option_candles table
    Returns count of rows inserted
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        inserted_count = 0
        
        for candle in candles:
            if not candle:
                continue
            
            cursor.execute("""
                INSERT OR REPLACE INTO option_candles
                (symbol, instrument_key, option_type, strike_price, expiry_date,
                 timeframe, timestamp, open, high, low, close, volume, oi)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                candle['symbol'],
                candle['instrument_key'],
                candle['option_type'],
                candle['strike_price'],
                candle['expiry_date'],
                candle['timeframe'],
                candle['timestamp'],
                candle['open'],
                candle['high'],
                candle['low'],
                candle['close'],
                candle['volume'],
                candle['oi'],
            ))
            
            inserted_count += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"✓ Stored {inserted_count} option candles")
        return inserted_count
        
    except Exception as e:
        logger.error(f"✗ Failed to store candles: {e}")
        return 0


def fetch_and_store_option_candles(
    underlying_name: str,
    strikes: List[float],
    option_types: List[str],
    expiry_date: str,
    timeframe: str = '1d',
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    delay: float = 1.0
) -> int:
    """
    Main function: fetch historical option candles and store in DB
    Returns total count of candles fetched
    """
    # Ensure table exists
    ensure_option_candles_table()
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        return 0
    
    # Resolve underlying
    if underlying_name.upper() in OPTION_UNDERLYINGS:
        underlying_key = OPTION_UNDERLYINGS[underlying_name.upper()]
        logger.info(f"✓ Resolved '{underlying_name}' → {underlying_key}")
    else:
        underlying_key = underlying_name
        logger.warning(f"⚠ Using '{underlying_name}' as-is (not in predefined list)")
    
    # Set date range
    if end_date:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end_dt = datetime.now()
    
    if start_date:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        # Default: last 3 months
        start_dt = end_dt - timedelta(days=90)
    
    logger.info(f"Date range: {start_dt.date()} to {end_dt.date()}")
    
    # Resolve option symbols
    symbol_map = resolve_option_symbols(
        underlying_key, strikes, expiry_date, option_types, access_token
    )
    
    if not symbol_map:
        logger.error("✗ Could not resolve any option symbols")
        return 0
    
    logger.info(f"\nFetching candles for {len(symbol_map)} options:")
    for map_key in sorted(symbol_map.keys()):
        logger.info(f"  - {map_key}")
    
    total_candles = 0
    
    for map_key, instrument_key in sorted(symbol_map.items()):
        strike_str, opt_type = map_key.rsplit('_', 1)
        strike_price = float(strike_str)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Fetching {map_key} ({instrument_key})")
        logger.info(f"{'='*60}")
        
        # Fetch candles
        candles = fetch_option_candles(
            instrument_key, timeframe, start_dt, end_dt, access_token
        )
        
        if not candles:
            logger.warning(f"⚠ No candles for {map_key}")
            time.sleep(delay)
            continue
        
        # Parse candles
        parsed_candles = []
        for candle in candles:
            parsed = parse_option_candle(
                candle,
                underlying_name,
                instrument_key,
                opt_type,
                strike_price,
                expiry_date,
                timeframe
            )
            if parsed:
                parsed_candles.append(parsed)
        
        # Store candles
        count = store_option_candles(parsed_candles)
        total_candles += count
        
        time.sleep(delay)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✓ COMPLETED: Fetched {total_candles} option candles total")
    logger.info(f"{'='*60}")
    
    return total_candles


def main():
    parser = argparse.ArgumentParser(
        description='Fetch historical option candles from Upstox API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch NIFTY 21000 CE/PE for Feb expiry (last 3 months)
  python3 scripts/option_history_fetcher.py \\
    --underlying NIFTY --strikes 21000 --types CALL,PUT \\
    --expiry 2025-02-13
  
  # Fetch multiple strikes (daily candles)
  python3 scripts/option_history_fetcher.py \\
    --underlying NIFTY --strikes 21000,21100,21200 \\
    --types CALL,PUT --expiry 2025-02-13 --timeframe 1d
  
  # Fetch 1-month data for specific date range
  python3 scripts/option_history_fetcher.py \\
    --underlying NIFTY --strikes 21000 --types CALL \\
    --expiry 2025-02-13 --timeframe 1h \\
    --start 2025-01-15 --end 2025-02-13
        """
    )
    
    parser.add_argument(
        '--underlying',
        type=str,
        required=True,
        help='Option underlying symbol (e.g., NIFTY, BANKNIFTY)'
    )
    
    parser.add_argument(
        '--strikes',
        type=str,
        required=True,
        help='Strike prices (comma-separated, e.g., 21000,21100,21200)'
    )
    
    parser.add_argument(
        '--types',
        type=str,
        default='CE,PE',
        help='Option types: CE, PE, or both (default: CE,PE)'
    )
    
    parser.add_argument(
        '--expiry',
        type=str,
        required=True,
        help='Expiry date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--timeframe',
        type=str,
        default='1d',
        choices=['1m', '5m', '15m', '1h', '1d'],
        help='Candle timeframe (default: 1d)'
    )
    
    parser.add_argument(
        '--start',
        type=str,
        default=None,
        help='Start date (YYYY-MM-DD). Default: 90 days ago'
    )
    
    parser.add_argument(
        '--end',
        type=str,
        default=None,
        help='End date (YYYY-MM-DD). Default: today'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay between API calls in seconds (default: 1.0)'
    )
    
    args = parser.parse_args()
    
    strikes = [float(s.strip()) for s in args.strikes.split(',')]
    option_types = [t.strip().upper() for t in args.types.split(',')]
    
    total = fetch_and_store_option_candles(
        args.underlying,
        strikes,
        option_types,
        args.expiry,
        args.timeframe,
        args.start,
        args.end,
        args.delay
    )
    
    return 0 if total > 0 else 1


if __name__ == '__main__':
    exit(main())
