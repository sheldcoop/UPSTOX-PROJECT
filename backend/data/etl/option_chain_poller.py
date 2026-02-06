"""
Option Chain Intraday Poller (Table B)
--------------------------------------
Polls full Option Chain (Greeks, Pricing) for 212 F&O Stocks.
Features:
- Fetches "Monthly" expiry option chain.
- Flattens nested JSON (Call/Put) to Wide Schema.
- Stores in `optionchain_intrday_schema`.
- Handles Rate Limits & Market Hours.

Usage:
    python backend/data/etl/option_chain_poller.py
"""

import asyncio
import aiohttp
import sqlite3
import logging
import os
import sys
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, time as dt_time
from urllib.parse import quote

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.utils.auth.manager import AuthManager

# Configuration
DB_PATH = "market_data.db"
LOG_FILE = "logs/option_chain_poller.log"
CONCURRENT_REQUESTS = 5   # Lower concurrency due to heavy payload
POLL_INTERVAL = 300       # 5 minutes

# Logging Setup
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("OptionChainPoller")

class OptionChainPoller:
    def __init__(self):
        self.auth_manager = AuthManager(db_path=DB_PATH)
        self.base_url = "https://api.upstox.com/v2/option/chain"

    def is_market_open(self) -> bool:
        """Check if market is open (09:15 - 15:30 IST)"""
        now = datetime.now()
        if now.weekday() >= 5: return False
        
        current_time = now.time()
        return dt_time(9, 15) <= current_time <= dt_time(15, 30)

    def get_monthly_expiry(self) -> str:
        """
        Get the current month's expiry date (last Thursday).
        Logic: Find last Thursday of current month. 
        If today > last Thursday, find next month's last Thursday.
        """
        today = datetime.now().date()
        
        def get_last_thursday(year, month):
            # Start from last day of month and go back
            next_month = month % 12 + 1
            next_year = year + (month // 12)
            last_day = (datetime(next_year, next_month, 1) - timedelta(days=1)).date()
            
            # 3 = Thursday (0=Mon, 6=Sun)
            offset = (last_day.weekday() - 3) % 7
            return last_day - timedelta(days=offset)

        current_expiry = get_last_thursday(today.year, today.month)
        
        if today > current_expiry:
            # Move to next month
            next_month = today.month % 12 + 1
            next_year = today.year + (today.month // 12)
            current_expiry = get_last_thursday(next_year, next_month)
            
        return current_expiry.strftime("%Y-%m-%d")

    def get_target_instruments(self) -> List[tuple]:
        """Fetch (symbol, instrument_key) for F&O stocks."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # We want the underlying keys (NSE_INDEX|Nifty 50 or NSE_EQ|RELIANCE)
            # Assumption: keys in instrument_master are valid for option chain 'instrument_key' param
            cursor.execute("""
                SELECT trading_symbol, instrument_key 
                FROM instrument_master 
                WHERE segment IN ('NSE_EQ', 'NSE_INDEX') AND is_active=1
                ORDER BY 
                    CASE 
                        WHEN trading_symbol IN ('Nifty 50', 'Nifty Bank') THEN 0 
                        WHEN segment='NSE_INDEX' THEN 1 
                        ELSE 2 
                    END, 
                    trading_symbol
            """)
            rows = cursor.fetchall()
            conn.close()
            # Filter specifically for F&O capable (simplified: take all active EQ/Indices)
            # In production, join with a whitelist or check 'derivatives_exist' flag if available
            return rows
        except Exception as e:
            logger.error(f"Failed to load instruments: {e}")
            return []

    async def fetch_chain(self, session: aiohttp.ClientSession, symbol: str, key: str, expiry: str, headers: Dict) -> Optional[List[Dict]]:
        """Fetch Option Chain for a specific key and expiry."""
        try:
            await asyncio.sleep(random.uniform(0.5, 1.5)) # More jitter for heavy endpoint
            
            params = {
                'instrument_key': key,
                'expiry_date': expiry
            }
            
            async with session.get(self.base_url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    # Return the list of strikes
                    return data.get('data', [])
                elif response.status == 400:
                    # Expiry might be invalid for this specific stock (e.g. some only have weekly?)
                    # Logger warning but continue
                    logger.warning(f"Bad Request for {symbol} ({expiry}): Maybe invalid expiry?")
                    return None
                elif response.status == 429:
                    logger.warning(f"Rate limited on {symbol}")
                    await asyncio.sleep(5)
                    return None
                else:
                    logger.warning(f"Failed {symbol}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return None

    def flatten_and_save(self, underlying_key: str, expiry: str, chain_data: List[Dict]):
        """Flatten nested JSON and save to DB."""
        if not chain_data: return

        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("PRAGMA journal_mode=WAL;")
            
            timestamp = datetime.now().isoformat()
            data_to_insert = []
            
            for strike in chain_data:
                # API Structure:
                # { "strike_price": 22000, "pcr": 0.8, "call_options": {...}, "put_options": {...} }
                s_price = strike.get('strike_price')
                pcr = strike.get('pcr')
                
                # Call Data
                ce = strike.get('call_options', {})
                ce_md = ce.get('market_data', {})
                ce_greeks = ce.get('option_greeks', {})
                
                # Put Data
                pe = strike.get('put_options', {})
                pe_md = pe.get('market_data', {})
                pe_greeks = pe.get('option_greeks', {})
                
                row = (
                    underlying_key, expiry, timestamp, s_price, pcr,
                    # CE
                    ce.get('instrument_key'),
                    ce_md.get('ltp'), ce_md.get('volume'), ce_md.get('oi'),
                    ce_md.get('bid_price'), ce_md.get('ask_price'),
                    ce_greeks.get('iv'), ce_greeks.get('delta'), ce_greeks.get('gamma'),
                    ce_greeks.get('theta'), ce_greeks.get('vega'), ce_greeks.get('rho'),
                    # PE
                    pe.get('instrument_key'),
                    pe_md.get('ltp'), pe_md.get('volume'), pe_md.get('oi'),
                    pe_md.get('bid_price'), pe_md.get('ask_price'),
                    pe_greeks.get('iv'), pe_greeks.get('delta'), pe_greeks.get('gamma'),
                    pe_greeks.get('theta'), pe_greeks.get('vega'), pe_greeks.get('rho')
                )
                data_to_insert.append(row)
            
            conn.executemany("""
                INSERT OR IGNORE INTO optionchain_intrday_schema (
                    underlying_key, expiry_date, timestamp, strike_price, pcr,
                    ce_instrument_key, ce_ltp, ce_volume, ce_oi, ce_bid_price, ce_ask_price,
                    ce_iv, ce_delta, ce_gamma, ce_theta, ce_vega, ce_rho,
                    pe_instrument_key, pe_ltp, pe_volume, pe_oi, pe_bid_price, pe_ask_price,
                    pe_iv, pe_delta, pe_gamma, pe_theta, pe_vega, pe_rho
                ) VALUES (?,?,?,?,?,  ?,?,?,?,?,?,?,?,?,?,?,  ?,?,?,?,?,?,?,?,?,?,?,?)
            """, data_to_insert)
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"DB Save Error: {e}")

    async def run_poll_cycle(self):
        token = self.auth_manager.get_valid_token()
        if not token: return
        
        headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
        expiry = self.get_monthly_expiry()
        instruments = self.get_target_instruments()
        
        logger.info(f"Starting Poll: {len(instruments)} instruments. Expiry: {expiry}")
        
        # Limit for safety
        if len(instruments) > 250: instruments = instruments[:250]
        
        async with aiohttp.ClientSession() as session:
            sem = asyncio.Semaphore(CONCURRENT_REQUESTS)
            
            async def process(sym, key):
                async with sem:
                    data = await self.fetch_chain(session, sym, key, expiry, headers)
                    if data:
                        self.flatten_and_save(key, expiry, data)
            
            tasks = [process(sym, key) for sym, key in instruments]
            await asyncio.gather(*tasks)
            
        logger.info("Cycle Complete.")

    async def start(self):
        logger.info(f"Option Chain Poller Started. Target Expiry: {self.get_monthly_expiry()}")
        while True:
            if not self.is_market_open() and not os.getenv("FORCE_RUN"):
                logger.info("Market Closed. Sleeping...")
                await asyncio.sleep(300)
                continue
                
            start_ts = datetime.now()
            await self.run_poll_cycle()
            
            elapsed = (datetime.now() - start_ts).total_seconds()
            sleep_time = max(0, POLL_INTERVAL - elapsed)
            logger.info(f"Sleeping {sleep_time:.1f}s")
            await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run one cycle")
    args = parser.parse_args()
    
    poller = OptionChainPoller()
    try:
        if args.once:
            asyncio.run(poller.run_poll_cycle())
        else:
            asyncio.run(poller.start())
    except KeyboardInterrupt:
        pass
