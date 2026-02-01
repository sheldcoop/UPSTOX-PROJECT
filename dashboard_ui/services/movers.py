
import sqlite3
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor

# Import Upstox API
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from scripts.upstox_live_api import get_upstox_api

class MarketMoversService:
    """
    Service to calculate Top Gainers/Losers for NSE, BSE, and SME.
    Uses caching to avoid hitting API rate limits.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    # Cache duration (e.g., 2 minutes)
    CACHE_DURATION = 120 
    
    def __init__(self):
        self.api = get_upstox_api()
        self.db_path = Path(__file__).parent.parent.parent / "market_data.db"
        self._cache = {} # {category_key: {'data': df, 'timestamp': datetime}}
        
    @staticmethod
    def get_instance():
        if MarketMoversService._instance is None:
            with MarketMoversService._lock:
                if MarketMoversService._instance is None:
                    MarketMoversService._instance = MarketMoversService()
        return MarketMoversService._instance

    def _get_instruments_from_db(self, category: str) -> List[tuple]:
        """Get (instrument_key, symbol, trading_symbol) for a category"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Based on DB Verification findings
            if category == 'NSE_MAIN':
                query = "SELECT instrument_key, symbol, trading_symbol FROM instruments WHERE segment_id='NSE_EQ' AND type_code IN ('EQ', 'BE')"
            
            elif category == 'NSE_SME':
                query = "SELECT instrument_key, symbol, trading_symbol FROM instruments WHERE segment_id='NSE_EQ' AND type_code IN ('SM', 'ST')"
            
            elif category == 'BSE_MAIN':
                query = "SELECT instrument_key, symbol, trading_symbol FROM instruments WHERE segment_id='BSE_EQ' AND type_code IN ('A', 'B')"
            
            elif category == 'BSE_SME':
                query = "SELECT instrument_key, symbol, trading_symbol FROM instruments WHERE segment_id='BSE_EQ' AND type_code IN ('M', 'MT')"
            
            else:
                return []

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print(f"DB Error in Movers Service: {e}")
            return []

    def get_movers(self, category: str = 'NSE_MAIN') -> Dict[str, List]:
        """
        Returns {'gainers': [...top 10...], 'losers': [...top 10...]}
        """
        
        # 1. Check Cache
        print(f"[Movers] Request for {category}")
        cached = self._cache.get(category)
        if cached:
            age = (datetime.now() - cached['timestamp']).total_seconds()
            print(f"[Movers] Cache hit for {category}, age: {age:.1f}s")
            if age < self.CACHE_DURATION:
                return cached['data']
        
        # 2. Fetch Instruments
        instruments = self._get_instruments_from_db(category)
        print(f"[Movers] DB returned {len(instruments)} instruments for {category}")
        if not instruments:
            return {'gainers': [], 'losers': []}
            
        print(f"Refreshing logic for {category} ({len(instruments)} instruments)...")
        
        # 3. Batch Fetch Prices (This takes time, maybe 2-3s for 2000 stocks)
        # Create mapping key -> symbol
        key_map = {row[0]: {'symbol': row[1], 'name': row[2]} for row in instruments}
        keys_to_fetch = list(key_map.keys())
        
        # DEBUG: Print first 3 keys
        print(f"[Movers] First 3 keys for {category}: {keys_to_fetch[:3]}")
        
        # Use existing batch function
        quotes = self.api.get_batch_market_quotes(keys_to_fetch)
        
        if not quotes:
            return {'gainers': [], 'losers': []}
            
        # 4. Process Data
        processed_data = []
        
        # DEBUG: Print sample keys to diagnose mismatch
        if quotes:
            sample_api_key = list(quotes.keys())[0]
            print(f"DEBUG: API Key Sample: '{sample_api_key}'")
            if instruments:
                print(f"DEBUG: DB Key Sample: '{instruments[0][0]}'")
                
        for _, q_data in quotes.items():
            if not q_data: continue
            
            # UPSTOX API FIX: Response keys are 'NSE_EQ:SYMBOL' but we need 'NSE_EQ|INE...'
            # We must use the 'instrument_token' field inside the quote object to map back to DB.
            token = q_data.get('instrument_token')
            
            # Try to find symbol info using the token (reliable)
            info = key_map.get(token)
            
            # Fallback if token is missing (unlikely but safe)
            if not info:
                # Try simple symbol name matching if available
                sym = q_data.get('symbol')
                if sym: info = {'symbol': sym}
                else: info = {}

            ltp = q_data.get('last_price', 0)
            
            # SAFEGUARD: ohlc can be None for some BSE stocks
            ohlc = q_data.get('ohlc')
            if not ohlc: ohlc = {}
            close = ohlc.get('close', 0) # Previous Close
            
            # Compute Change %
            # Note: q_data has 'net_change' but calculating Pct Change safely is better
            change = q_data.get('net_change', 0)
            
            # If prev close is valid, use it for % change
            # Default API usually provides it, but calculating ensures control
            if close and close > 0:
                pct_change = (change / close) * 100
            else:
                pct_change = 0.0
                
            vol = q_data.get('volume', 0)
            
            processed_data.append({
                'symbol': info.get('symbol', 'UNKNOWN'),
                'price': ltp,
                'change': change,
                'pct_change': pct_change,
                'volume': vol
            })
            
        # 5. Sort
        # Sort by Pct Change
        df = pd.DataFrame(processed_data)
        
        if df.empty:
             return {'gainers': [], 'losers': []}

        # Return ALL records sorted properly
        # Frontend will handle pagination
        gainers = df.sort_values('pct_change', ascending=False).to_dict('records')
        losers = df.sort_values('pct_change', ascending=True).to_dict('records')
        
        result = {'gainers': gainers, 'losers': losers}
        
        # 6. Update Cache
        self._cache[category] = {
            'data': result,
            'timestamp': datetime.now()
        }
        
        return result

