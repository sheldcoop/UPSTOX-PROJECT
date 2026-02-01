#!/usr/bin/env python3
"""
Option Chain Fetcher - Fetch live option chain data from Upstox API
Stores current option chain snapshots and market data (Greeks, bid-ask, IV, etc)
"""

import requests
import sqlite3
import json
import logging
import argparse
import sys
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import time

# Add scripts dir to path for AuthManager import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auth_manager import AuthManager

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
    'INFY': 'NSE_EQ|INE009A01021',
    'TCS': 'NSE_EQ|INE467B01029',
    'RELIANCE': 'NSE_EQ|INE002A01018',
}


def get_access_token() -> Optional[str]:
    """Retrieve valid access token using AuthManager with auto-refresh"""
    try:
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


def get_option_expiries(underlying_key: str, access_token: str) -> List[str]:
    """Fetch available option expiry dates for a given underlying"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        # Get option contracts to find expiries
        url = f"{API_BASE_URL}/option/contract"
        params = {'instrument_key': underlying_key}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"✗ Failed to get expiries. Status: {response.status_code}")
            return []
        
        data = response.json()
        expiries = set()
        
        if data.get('status') == 'success' and data.get('data'):
            for contract in data['data']:
                if 'expiry' in contract:
                    expiries.add(contract['expiry'])
        
        logger.info(f"✓ Found {len(expiries)} expiry dates: {sorted(expiries)}")
        return sorted(list(expiries))
        
    except Exception as e:
        logger.error(f"✗ Failed to get expiries: {e}")
        return []


def fetch_option_chain(
    underlying_key: str,
    expiry_date: str,
    access_token: str
) -> Optional[List[Dict]]:
    """
    Fetch put/call option chain for given underlying and expiry
    Returns list of strike data with call/put Greeks and market data
    """
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        url = f"{API_BASE_URL}/option/chain"
        params = {
            'instrument_key': underlying_key,
            'expiry_date': expiry_date
        }
        
        logger.info(f"Fetching option chain for {underlying_key} @ {expiry_date}...")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"✗ Failed to fetch option chain. Status: {response.status_code}")
            logger.error(f"  Response: {response.text[:200]}")
            return None
        
        data = response.json()
        
        if data.get('status') != 'success':
            logger.error(f"✗ API returned non-success status: {data.get('status')}")
            return None
        
        chain_data = data.get('data', [])
        logger.info(f"✓ Fetched {len(chain_data)} strikes")
        return chain_data
        
    except Exception as e:
        logger.error(f"✗ Failed to fetch option chain: {e}")
        return None


def parse_option_data(
    strike_data: Dict,
    underlying_key: str,
    expiry_date: str,
    snapshot_ts: int
) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Parse call and put option data from strike snapshot
    Returns (call_option_data, put_option_data) tuples with all Greeks, market data
    """
    try:
        strike_price = strike_data.get('strike_price')
        
        call_data = None
        put_data = None
        
        # Parse CALL option
        call_opts = strike_data.get('call_options', {})
        if call_opts.get('instrument_key'):
            call_market = call_opts.get('market_data', {})
            call_greeks = call_opts.get('option_greeks', {})
            
            call_data = {
                'instrument_key': call_opts['instrument_key'],
                'underlying_key': underlying_key,
                'strike_price': strike_price,
                'expiry': expiry_date,
                'option_type': 'CALL',
                'ts': snapshot_ts,
                'ltp': call_market.get('ltp'),
                'close_price': call_market.get('close_price'),
                'bid_price': call_market.get('bid_price'),
                'bid_qty': call_market.get('bid_qty'),
                'ask_price': call_market.get('ask_price'),
                'ask_qty': call_market.get('ask_qty'),
                'volume': call_market.get('volume'),
                'oi': call_market.get('oi'),
                'prev_oi': call_market.get('prev_oi'),
                'delta': call_greeks.get('delta'),
                'gamma': call_greeks.get('gamma'),
                'theta': call_greeks.get('theta'),
                'vega': call_greeks.get('vega'),
                'iv': call_greeks.get('iv'),
                'pop': call_greeks.get('pop'),  # probability of profit
            }
        
        # Parse PUT option
        put_opts = strike_data.get('put_options', {})
        if put_opts.get('instrument_key'):
            put_market = put_opts.get('market_data', {})
            put_greeks = put_opts.get('option_greeks', {})
            
            put_data = {
                'instrument_key': put_opts['instrument_key'],
                'underlying_key': underlying_key,
                'strike_price': strike_price,
                'expiry': expiry_date,
                'option_type': 'PUT',
                'ts': snapshot_ts,
                'ltp': put_market.get('ltp'),
                'close_price': put_market.get('close_price'),
                'bid_price': put_market.get('bid_price'),
                'bid_qty': put_market.get('bid_qty'),
                'ask_price': put_market.get('ask_price'),
                'ask_qty': put_market.get('ask_qty'),
                'volume': put_market.get('volume'),
                'oi': put_market.get('oi'),
                'prev_oi': put_market.get('prev_oi'),
                'delta': put_greeks.get('delta'),
                'gamma': put_greeks.get('gamma'),
                'theta': put_greeks.get('theta'),
                'vega': put_greeks.get('vega'),
                'iv': put_greeks.get('iv'),
                'pop': put_greeks.get('pop'),
            }
        
        return call_data, put_data
        
    except Exception as e:
        logger.error(f"✗ Failed to parse option data: {e}")
        return None, None


def store_option_chain_snapshot(
    underlying_key: str,
    expiry_date: str,
    snapshot_ts: int,
    raw_json: str
) -> bool:
    """Store snapshot of full option chain in option_chain_snapshots table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO option_chain_snapshots
            (underlying_instrument_key, expiry_date, snapshot_ts, raw_json)
            VALUES (?, ?, ?, ?)
        """, (underlying_key, expiry_date, snapshot_ts, raw_json))
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"✗ Failed to store snapshot: {e}")
        return False


def store_option_market_data(options_list: List[Dict]) -> int:
    """
    Store option market data (Greeks, prices, OI) in option_market_data table
    Returns count of rows inserted
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        inserted_count = 0
        
        for opt in options_list:
            if not opt or not opt.get('instrument_key'):
                continue
            
            cursor.execute("""
                INSERT OR REPLACE INTO option_market_data
                (instrument_key, ts, ltp, bid_price, bid_qty, ask_price, ask_qty,
                 oi, iv, delta, gamma, theta, vega, pop)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                opt['instrument_key'],
                opt['ts'],
                opt.get('ltp'),
                opt.get('bid_price'),
                opt.get('bid_qty'),
                opt.get('ask_price'),
                opt.get('ask_qty'),
                opt.get('oi'),
                opt.get('iv'),
                opt.get('delta'),
                opt.get('gamma'),
                opt.get('theta'),
                opt.get('vega'),
                opt.get('pop'),
            ))
            
            inserted_count += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"✓ Stored {inserted_count} option market data records")
        return inserted_count
        
    except Exception as e:
        logger.error(f"✗ Failed to store market data: {e}")
        return 0


def fetch_and_store_option_chain(
    underlying_name: str,
    expiry_date: Optional[str] = None,
    delay: float = 1.0
) -> bool:
    """
    Main function: fetch option chain from API and store in DB
    If expiry_date not specified, fetches for first available expiry
    """
    # Get access token
    access_token = get_access_token()
    if not access_token:
        return False
    
    # Resolve underlying name to key
    if underlying_name.upper() in OPTION_UNDERLYINGS:
        underlying_key = OPTION_UNDERLYINGS[underlying_name.upper()]
        logger.info(f"✓ Resolved '{underlying_name}' → {underlying_key}")
    else:
        underlying_key = underlying_name
        logger.warning(f"⚠ Using '{underlying_name}' as-is (not in predefined list)")
    
    # Get available expiries if not specified
    expiries = get_option_expiries(underlying_key, access_token)
    if not expiries:
        logger.error("✗ Could not get any expiry dates")
        return False
    
    if expiry_date:
        if expiry_date not in expiries:
            logger.error(f"✗ Expiry '{expiry_date}' not available. Available: {expiries}")
            return False
        expiries_to_fetch = [expiry_date]
    else:
        expiries_to_fetch = [expiries[0]]  # Fetch nearest expiry
    
    snapshot_ts = int(time.time())
    total_options = 0
    
    for expiry in expiries_to_fetch:
        logger.info(f"\n{'='*60}")
        logger.info(f"Fetching {underlying_name} @ {expiry}")
        logger.info(f"{'='*60}")
        
        # Fetch option chain
        chain_data = fetch_option_chain(underlying_key, expiry, access_token)
        if not chain_data:
            logger.error(f"✗ Failed to fetch chain for {expiry}")
            continue
        
        # Store raw snapshot
        raw_json = json.dumps(chain_data)
        if store_option_chain_snapshot(underlying_key, expiry, snapshot_ts, raw_json):
            logger.info(f"✓ Stored snapshot ({len(raw_json)} bytes)")
        
        # Parse and store individual option data
        all_options = []
        for strike_data in chain_data:
            call_data, put_data = parse_option_data(
                strike_data, underlying_key, expiry, snapshot_ts
            )
            
            if call_data:
                all_options.append(call_data)
            if put_data:
                all_options.append(put_data)
        
        # Store all option market data
        count = store_option_market_data(all_options)
        total_options += count
        
        time.sleep(delay)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✓ COMPLETED: Stored {total_options} option records total")
    logger.info(f"{'='*60}")
    
    return total_options > 0


def main():
    parser = argparse.ArgumentParser(
        description='Fetch current option chain from Upstox API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch NIFTY chain (nearest expiry)
  python3 scripts/option_chain_fetcher.py --underlying NIFTY
  
  # Fetch specific expiry
  python3 scripts/option_chain_fetcher.py --underlying NIFTY --expiry 2025-02-13
  
  # Fetch multiple underlyings with delay
  python3 scripts/option_chain_fetcher.py --underlying NIFTY,BANKNIFTY --delay 2
        """
    )
    
    parser.add_argument(
        '--underlying',
        type=str,
        default='NIFTY',
        help='Option underlying symbol (e.g., NIFTY, BANKNIFTY, INFY, TCS). Comma-separated for multiple.'
    )
    
    parser.add_argument(
        '--expiry',
        type=str,
        default=None,
        help='Expiry date (YYYY-MM-DD). If not specified, uses nearest available expiry.'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay between API calls in seconds (default: 1.0)'
    )
    
    args = parser.parse_args()
    
    underlyings = [u.strip() for u in args.underlying.split(',')]
    
    success_count = 0
    for underlying in underlyings:
        if fetch_and_store_option_chain(underlying, args.expiry, args.delay):
            success_count += 1
    
    if success_count > 0:
        logger.info(f"\n✓ Successfully fetched {success_count}/{len(underlyings)} underlyings")
    else:
        logger.error(f"\n✗ Failed to fetch any data")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
