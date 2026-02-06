"""
NSE 500 Quote Poller (Table D)
------------------------------
Polls 5-minute Market Quote snapshots for NSE Mainboard Stocks (Nifty 500 proxy).
Features:
- Identifies Mainboard instruments (NSE EQ/BE).
- Fetches full market depth (Top 5).
- Batches API requests (50 instruments per call).
- Flattens depth structure for SQL storage.

Usage:
    python backend/data/etl/nse500_quote_poller.py
"""

import asyncio
import aiohttp
import sqlite3
import logging
import os
import sys
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, time as dt_time
from urllib.parse import quote

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.utils.auth.manager import AuthManager

# Configuration
DB_PATH = "market_data.db"
LOG_FILE = "logs/nse500_poller.log"
BATCH_SIZE = 50           # Upstox Quote API limit (safe value)
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
logger = logging.getLogger("NSE500Poller")

class NSE500QuotePoller:
    def __init__(self):
        self.auth_manager = AuthManager(db_path=DB_PATH)
        self.base_url = "https://api.upstox.com/v2/market-quote/quotes"

    def is_market_open(self) -> bool:
        """Check if market is open (09:15 - 15:30 IST)"""
        now = datetime.now()
        if now.weekday() >= 5: return False
        
        current_time = now.time()
        return dt_time(9, 15) <= current_time <= dt_time(15, 30)

    def get_mainboard_instruments(self) -> List[str]:
        """Fetch active NSE Mainboard instrument keys from DB."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # NSE Mainboard = Segment 'NSE_EQ' AND Type in ('EQ', 'BE')
            # Supersets Nifty 500 (~2410 NSE EQ + ~98 BE)
            query = """
                SELECT instrument_key 
                FROM instrument_master 
                WHERE is_active = 1
                AND segment = 'NSE_EQ'
                AND instrument_type IN ('EQ', 'BE')
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            keys = [r[0] for r in rows]
            
            logger.info(f"Loaded {len(keys)} Mainboard instruments (Filter: NSE EQ/BE).")
            conn.close()
            return keys
        except Exception as e:
            logger.error(f"Failed to load Mainboard instruments: {e}")
            return []

    def get_instrument_map(self) -> Dict[str, str]:
        """Create a map of Trading Symbol -> Instrument Key (Canonical)"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            query = "SELECT trading_symbol, instrument_key FROM instrument_master WHERE segment='NSE_EQ' AND is_active=1"
            cursor.execute(query)
            # Map 'NSE_EQ:RELIANCE' -> 'NSE_EQ|INE002A01018'
            # API returns 'NSE_EQ:SYMBOL', so we match on symbol
            key_map = {f"NSE_EQ:{row[0]}": row[1] for row in cursor.fetchall()}
            conn.close()
            return key_map
        except Exception as e:
            logger.error(f"Failed to load key map: {e}")
            return {}

    async def fetch_quotes_batch(self, session: aiohttp.ClientSession, keys: List[str], headers: Dict) -> Dict:
        try:
            if not keys: return {}
            keys_str = ",".join(keys)
            params = {'instrument_key': keys_str}
            async with session.get(self.base_url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', {})
                elif response.status == 429:
                    logger.warning("Rate limit hit")
                    await asyncio.sleep(2)
                else:
                    logger.warning(f"Batch failed: {response.status}")
            return {}
        except Exception as e:
            logger.error(f"Batch Fetch Error: {e}")
            return {}

    def flatten_depth(self, depth_list: List[Dict], prefix: str, target_dict: Dict):
        for i in range(5):
            idx = i + 1
            if i < len(depth_list):
                item = depth_list[i]
                target_dict[f'{prefix}_price_{idx}'] = item.get('price', 0)
                target_dict[f'{prefix}_qty_{idx}'] = item.get('quantity', 0)
                target_dict[f'{prefix}_orders_{idx}'] = item.get('orders', 0)
            else:
                target_dict[f'{prefix}_price_{idx}'] = 0
                target_dict[f'{prefix}_qty_{idx}'] = 0
                target_dict[f'{prefix}_orders_{idx}'] = 0

    def save_batch(self, quotes: Dict, key_map: Dict[str, str]):
        if not quotes: return

        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("PRAGMA journal_mode=WAL;")
            
            timestamp = datetime.now().isoformat()
            data_to_insert = []
            
            for api_key, data in quotes.items():
                if not data: continue
                
                # NORMALIZE KEY: Convert API key (NSE_EQ:REL) to Canonical (NSE_EQ|INE...)
                # If mapping fails, fallback to API key (though this shouldn't happen for valid stocks)
                canonical_key = key_map.get(api_key, api_key)
                
                ohlc = data.get('ohlc', {})
                depth = data.get('depth', {})
                
                row_dict = {
                    'instrument_key': canonical_key,
                    'timestamp': timestamp,
                    'open': ohlc.get('open'),
                    'high': ohlc.get('high'),
                    'low': ohlc.get('low'),
                    'close': ohlc.get('close'),
                    'volume': data.get('volume'),
                    'average_price': data.get('average_price'),
                    'total_buy_quantity': data.get('total_buy_quantity'),
                    'total_sell_quantity': data.get('total_sell_quantity'),
                    'oi': data.get('oi')
                }
                
                self.flatten_depth(depth.get('buy', []), 'bid', row_dict)
                self.flatten_depth(depth.get('sell', []), 'ask', row_dict)
                data_to_insert.append(row_dict)

            columns = [
                'instrument_key', 'timestamp', 'open', 'high', 'low', 'close', 'volume', 'average_price',
                'total_buy_quantity', 'total_sell_quantity', 'oi',
                'bid_price_1', 'bid_qty_1', 'bid_orders_1', 'bid_price_2', 'bid_qty_2', 'bid_orders_2',
                'bid_price_3', 'bid_qty_3', 'bid_orders_3', 'bid_price_4', 'bid_qty_4', 'bid_orders_4',
                'bid_price_5', 'bid_qty_5', 'bid_orders_5',
                'ask_price_1', 'ask_qty_1', 'ask_orders_1', 'ask_price_2', 'ask_qty_2', 'ask_orders_2',
                'ask_price_3', 'ask_qty_3', 'ask_orders_3', 'ask_price_4', 'ask_qty_4', 'ask_orders_4',
                'ask_price_5', 'ask_qty_5', 'ask_orders_5'
            ]
            
            placeholders = ",".join(["?" for _ in columns])
            col_str = ",".join(columns)
            
            values_list = []
            for row in data_to_insert:
                values_list.append(tuple(row.get(c) for c in columns))
                
            conn.executemany(f"""
                INSERT OR IGNORE INTO market_quota_nse500_data 
                ({col_str}) VALUES ({placeholders})
            """, values_list)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"DB Save Error: {e}")

    async def run_poll_cycle(self):
        token = self.auth_manager.get_valid_token()
        if not token: return
        
        headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
        all_keys = self.get_mainboard_instruments()
        # Load Mapping dynamically each cycle (or cache it)
        key_map = self.get_instrument_map()
        
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(all_keys), BATCH_SIZE):
                batch_keys = all_keys[i:i+BATCH_SIZE]
                quotes = await self.fetch_quotes_batch(session, batch_keys, headers)
                self.save_batch(quotes, key_map)
                await asyncio.sleep(0.2)
                
        logger.info(f"Polled {len(all_keys)} instruments.")

    async def start(self):
        logger.info("NSE 500 Poller Started.")
        while True:
            if not self.is_market_open() and not os.getenv("FORCE_RUN"):
                logger.info("Market Closed. Sleeping...")
                await asyncio.sleep(300)
                continue
                
            start_ts = datetime.now()
            await self.run_poll_cycle()
            
            elapsed = (datetime.now() - start_ts).total_seconds()
            sleep_time = max(0, POLL_INTERVAL - elapsed)
            # logger.info(f"Sleeping {sleep_time:.1f}s") # User wanted silent efficiency? No, keep logs.
            await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run one cycle")
    args = parser.parse_args()
    
    poller = NSE500QuotePoller()
    try:
        if args.once:
            asyncio.run(poller.run_poll_cycle())
        else:
            asyncio.run(poller.start())
    except KeyboardInterrupt:
        pass
