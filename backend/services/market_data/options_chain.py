"""
Options Chain Service - Fetch and process live options data from Upstox
Handles market hours, Greeks calculation, and real-time updates
"""

import logging
import requests
import sys
import os
from datetime import datetime, timedelta, time as dt_time
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.utils.auth.manager import AuthManager
from backend.utils.auth.headers import build_bearer_headers

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/options_chain.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Create logs directory
Path("logs").mkdir(exist_ok=True)


class OptionsChainService:
    """Service for fetching and processing options chain data from Upstox"""

    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path
        self.base_url = "https://api.upstox.com/v2"
        self.auth_manager = AuthManager(db_path=db_path)
        logger.info(f"Initialized OptionsChainService with db={db_path}")

    def get_expiry_dates(self, instrument_key: str) -> List[str]:
        """
        Fetch available expiry dates for an instrument.
        Uses active contracts api or option chain API to find valid dates.
        """
        try:
            # Strategy: Use v2/option/contract to get all contracts, then extract unique expiries
            token = self.auth_manager.get_valid_token()
            if not token:
                return []

            headers = build_bearer_headers(token, include_json=True)
            url = f"{self.base_url}/option/contract"
            params = {"instrument_key": instrument_key}

            response = requests.get(url, headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json().get("data", [])
                # Extract unique expiry dates
                dates = sorted(list(set([c["expiry"] for c in data])))
                return dates
            return []
        except Exception as e:
            logger.error(f"Error fetching expiries: {e}")
            return []

    def get_fno_symbols(self) -> Dict[str, List[str]]:
        """
        Get list of all FnO symbols (Indices and Stocks) by querying
        the parent-child relationship: Find unique underlying_symbol 
        from all CE/PE option contracts.
        
        This ensures we only return instruments that actually have 
        active options, not just instruments in the FnO segment.
        
        Returns: {'indices': [...], 'equities': [...], 'commodities': [...], 'currencies': [...], 'ird': [...]}
        """
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query for unique underlying symbols from actual option contracts (CE/PE)
            # This is the definitive way to find optionable instruments
            cursor.execute("""
                SELECT DISTINCT underlying_symbol, underlying_type 
                FROM exchange_listings 
                WHERE instrument_type IN ('CE', 'PE') 
                  AND underlying_symbol IS NOT NULL
                ORDER BY underlying_symbol
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            indices = []
            equities = []
            commodities = []
            currencies = []
            ird = []
            
            for symbol, type_ in rows:
                if type_ == 'INDEX':
                    indices.append(symbol)
                elif type_ == 'COM':
                    commodities.append(symbol)
                elif type_ == 'CUR':
                    currencies.append(symbol)
                elif type_ == 'IRD':
                    ird.append(symbol)
                else:
                    equities.append(symbol)
            
            # Ensure major indices are at the top
            major_indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
            for idx in reversed(major_indices):
                if idx in indices:
                    indices.remove(idx)
                    indices.insert(0, idx)
                    
            return {
                "indices": indices,
                "equities": equities,
                "commodities": commodities,
                "currencies": currencies,
                "ird": ird
            }
            
        except Exception as e:
            logger.error(f"Error fetching FnO symbols: {e}")
            # Fallback
            return {
                "indices": ["NIFTY", "BANKNIFTY", "FINNIFTY"],
                "equities": ["RELIANCE", "TCS", "INFY", "HDFCBANK"],
                "commodities": [],
                "currencies": [],
                "ird": []
            }
    def get_symbol_metadata(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch metadata (Sector, Index Membership) for a given symbol
        from stock_metadata table.
        """
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT sector, is_nifty50, is_nifty100, is_nifty500, is_nifty_bank 
                FROM stock_metadata 
                WHERE symbol = ?
            """, (symbol.upper(),))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "sector": row[0] or "Diversified",
                    "is_nifty50": bool(row[1]),
                    "is_nifty100": bool(row[2]),
                    "is_nifty500": bool(row[3]),
                    "is_nifty_bank": bool(row[4])
                }
            
            # Default for indices or unknown
            return {
                "sector": "Index" if "NIFTY" in symbol.upper() or "SENSEX" in symbol.upper() else "Other",
                "is_nifty50": symbol.upper() == "NIFTY" or "NIFTY50" in symbol.upper(),
                "is_nifty100": symbol.upper() == "NIFTY" or "NIFTY100" in symbol.upper(),
                "is_nifty500": False,
                "is_nifty_bank": "BANKNIFTY" in symbol.upper()
            }
            
        except Exception as e:
            logger.error(f"Error fetching metadata for {symbol}: {e}")
            return {"sector": "N/A", "is_nifty50": False, "is_nifty100": False, "is_nifty500": False, "is_nifty_bank": False}

    def get_filter_options(self) -> Dict[str, List[str]]:
        """
        Get all available sectors and indices for filtering.
        """
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get Sectors
            cursor.execute("SELECT DISTINCT sector FROM stock_metadata WHERE sector IS NOT NULL ORDER BY sector")
            sectors = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                "indices": ["ALL", "NIFTY 50", "NIFTY 100", "BANK NIFTY"],
                "sectors": ["ALL"] + sectors
            }
        except Exception as e:
            logger.error(f"Error fetching filter options: {e}")
            return {"indices": ["ALL"], "sectors": ["ALL"]}

    def get_filtered_symbols(self, index_filter: str = "ALL", sector_filter: str = "ALL") -> List[str]:
        """
        Get symbols filtered by index or sector.
        """
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT symbol FROM stock_metadata WHERE 1=1"
            params = []
            
            if index_filter == "NIFTY 50":
                query += " AND is_nifty50 = 1"
            elif index_filter == "NIFTY 100":
                query += " AND is_nifty100 = 1"
            elif index_filter == "BANK NIFTY":
                query += " AND is_nifty_bank = 1"
                
            if sector_filter != "ALL":
                query += " AND sector = ?"
                params.append(sector_filter)
                
            query += " ORDER BY symbol"
            
            cursor.execute(query, params)
            symbols = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            # If no results (e.g. for non-stocks), return the standard FnO list if it's "ALL"
            if not symbols and index_filter == "ALL" and sector_filter == "ALL":
                all_fno = self.get_fno_symbols()
                symbols = all_fno.get("indices", []) + all_fno.get("equities", [])
                
            return symbols
        except Exception as e:
            logger.error(f"Error fetching filtered symbols: {e}")
            return []


    def get_expiry_dates_from_db(self, underlying_symbol: str) -> List[str]:
        """
        Extract expiry dates directly from database by parsing trading_symbol
        of CE/PE contracts. This eliminates the need for API calls.
        
        Trading symbol format: "NIFTY 18000 CE 30 JUN 26"
        Expiry is in the last 3 tokens: "30 JUN 26"
        
        Args:
            underlying_symbol: The underlying instrument symbol (e.g., "NIFTY")
            
        Returns:
            Sorted list of expiry date strings (e.g., ["2026-02-06", "2026-02-13", ...])
        """
        try:
            import sqlite3
            from datetime import datetime
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query all option contracts for this underlying
            cursor.execute("""
                SELECT DISTINCT trading_symbol 
                FROM exchange_listings 
                WHERE underlying_symbol = ? 
                  AND instrument_type IN ('CE', 'PE')
                ORDER BY trading_symbol
            """, (underlying_symbol,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Extract and parse expiry dates
            expiry_dates = set()
            for (trading_symbol,) in rows:
                # Format: "NIFTY 18000 CE 30 JUN 26"
                # Split and get last 3 tokens
                parts = trading_symbol.split()
                if len(parts) >= 3:
                    # Last 3 parts: day, month, year
                    day = parts[-3]
                    month = parts[-2]
                    year = parts[-1]
                    
                    try:
                        # Parse to datetime for proper sorting
                        date_str = f"{day} {month} {year}"
                        dt = datetime.strptime(date_str, "%d %b %y")
                        # Format as YYYY-MM-DD for consistency
                        expiry_dates.add(dt.strftime("%Y-%m-%d"))
                    except ValueError:
                        # Skip invalid dates
                        continue
            
            # Return sorted list (nearest expiry first)
            return sorted(list(expiry_dates))
            
        except Exception as e:
            logger.error(f"Error extracting expiry dates from DB: {e}")
            return []


    def get_option_greeks(self, instrument_keys: List[str]) -> Dict:
        """
        Fetch detailed option greeks using v3 API.
        Response includes: theta, delta, gamma, vega, iv, etc.
        """
        try:
            token = self.auth_manager.get_valid_token()
            if not token:
                logger.error("No token for greeks")
                return {}

            # v3 endpoint
            url = "https://api.upstox.com/v3/market-quote/option-greek"
            headers = build_bearer_headers(token, include_json=True)

            # API supports comma separated keys
            keys_str = ",".join(instrument_keys)
            params = {"instrument_key": keys_str}

            response = requests.get(url, headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json().get("data", {})
                return data
            else:
                logger.error(
                    f"Greeks API failed: {response.status_code} {response.text}"
                )
                return {}
        except Exception as e:
            logger.error(f"Error fetching greeks: {e}")
            return {}

    def is_market_open(self) -> Tuple[bool, str]:
        """
        Check if Indian stock market is currently open
        NSE: Mon-Fri 9:15 AM - 3:30 PM IST
        Returns: (is_open, message)
        """
        now = datetime.now()
        current_time = now.time()
        weekday = now.weekday()  # 0 = Monday, 6 = Sunday

        # Market closed on weekends
        if weekday >= 5:  # Saturday or Sunday
            logger.debug("Market closed: Weekend")
            return False, "Market is closed on weekends"

        # Market hours: 9:15 AM - 3:30 PM IST
        market_open = dt_time(9, 15)
        market_close = dt_time(15, 30)

        if current_time < market_open:
            logger.debug(f"Market closed: Before opening (current: {current_time})")
            return (
                False,
                f"Market opens at 9:15 AM (current time: {current_time.strftime('%H:%M')})",
            )

        if current_time > market_close:
            logger.debug(f"Market closed: After closing (current: {current_time})")
            return (
                False,
                f"Market closed at 3:30 PM (current time: {current_time.strftime('%H:%M')})",
            )

        logger.debug("Market is open")
        return True, "Market is open"

    def get_option_chain(self, symbol: str, expiry_date: Optional[str] = None) -> Dict:
        """
        Fetch options chain from Upstox API

        Args:
            symbol: Underlying symbol (e.g., 'NIFTY', 'BANKNIFTY', 'RELIANCE')
            expiry_date: Expiry date in YYYY-MM-DD format (optional, uses nearest expiry if not provided)

        Returns:
            {
                'symbol': str,
                'expiry_date': str,
                'underlying_price': float,
                'timestamp': str,
                'market_open': bool,
                'strikes': [
                    {
                        'strike': float,
                        'call': {...},
                        'put': {...}
                    }
                ]
            }
        """
        logger.info(f"[OPTIONS] Fetching chain for {symbol}, expiry={expiry_date}")

        # Check market status
        market_open, market_msg = self.is_market_open()
        logger.info(f"[OPTIONS] Market status: {market_msg}")

        # For now, try to fetch real data
        logger.info(f"[OPTIONS] Fetching live data for {symbol} Expiry: {expiry_date}")

        try:
            # Get valid token
            token = self.auth_manager.get_valid_token()
            if not token:
                logger.error("[OPTIONS] No valid Upstox token available")
                return {}

            # Construct API request
            headers = build_bearer_headers(token, include_json=True)

            # Map symbol to key
            inst_key = self._get_instrument_key(symbol)
            params = {"instrument_key": inst_key}

            if expiry_date:
                params["expiry_date"] = expiry_date

            # If no expiry provided for Live API, we MUST provide one
            if not expiry_date:
                # auto-fetch expiries from DB (optimized)
                dates = self.get_expiry_dates_from_db(symbol)
                if dates:
                    params["expiry_date"] = dates[0]
                    # Also update result to show we picked this date
                    expiry_date = dates[0]
                else:
                    logger.warning(f"Could not find expiry dates for {symbol}")
                    return {}

            logger.debug(
                f"[OPTIONS] API request: {self.base_url}/option/chain, params={params}"
            )

            response = requests.get(
                f"{self.base_url}/option/chain",
                headers=headers,
                params=params,
                timeout=5,
            )

            if response.status_code == 200:
                data = response.json()
                # Parse
                return self._process_upstox_response(data, symbol, market_open)

            logger.warning(f"API Failed {response.status_code}: {response.text}")
            return {}

        except Exception as e:
            logger.error(f"[OPTIONS] Error fetching chain: {e}", exc_info=True)
            return {}

        # TODO: Uncomment below when Upstox option chain API is properly configured
        """
        try:
            # Get valid token
            token = self.auth_manager.get_valid_token()
            if not token:
                logger.error("[OPTIONS] No valid Upstox token available")
                return self._mock_option_chain(symbol, expiry_date, market_open)
            
            # Construct API request
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }
            
            # Build URL
            # Upstox API endpoint: https://api.upstox.com/v2/option/chain?instrument_key=NSE_INDEX|Nifty%2050&expiry_date=2025-02-06
            params = {
                'instrument_key': self._get_instrument_key(symbol)
            }
            
            if expiry_date:
                params['expiry_date'] = expiry_date
            
            logger.debug(f"[OPTIONS] API request: {self.base_url}/option/chain, params={params}")
            
            response = requests.get(
                f"{self.base_url}/option/chain",
                headers=headers,
                params=params,
                timeout=5  # Reduced timeout
            )
            
            logger.debug(f"[OPTIONS] API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"[OPTIONS] Successfully fetched chain data")
                return self._process_upstox_response(data, symbol, market_open)
            
            elif response.status_code == 401:
                logger.warning("[OPTIONS] Token expired, attempting refresh")
                # Token expired, try refresh
                token = self.auth_manager.get_valid_token(force_refresh=True)
                if token:
                    # Retry with new token
                    headers['Authorization'] = f'Bearer {token}'
                    response = requests.get(
                        f"{self.base_url}/option/chain",
                        headers=headers,
                        params=params,
                        timeout=5
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return self._process_upstox_response(data, symbol, market_open)
            
            # If API fails, return mock data
            logger.warning(f"[OPTIONS] API failed with status {response.status_code}, using mock data")
            return self._mock_option_chain(symbol, expiry_date, market_open)
            
        except Exception as e:
            logger.error(f"[OPTIONS] Error fetching chain: {e}", exc_info=True)
            # Return mock data on error
            return self._mock_option_chain(symbol, expiry_date, market_open)
        """

    def _get_instrument_key(self, symbol: str) -> str:
        """
        Convert symbol to Upstox instrument key by searching the database.
        This dynamically resolves keys for all instruments (Indices, Equities, etc.)
        including ISIN-based keys for equities.
        """
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Lookup the instrument_key in the database
            # We prefer INDEX over EQ for same symbol if it exists (e.g. NIFTY)
            cursor.execute("""
                SELECT instrument_key 
                FROM exchange_listings 
                WHERE symbol = ? 
                ORDER BY CASE 
                    WHEN instrument_type = 'INDEX' THEN 1 
                    WHEN instrument_type = 'EQ' THEN 2 
                    ELSE 3 
                END ASC
                LIMIT 1
            """, (symbol.upper(),))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return row[0]
                
            # Fallback for common indices if DB lookup fails
            if symbol.upper() == "NIFTY":
                return "NSE_INDEX|Nifty 50"
            elif symbol.upper() == "BANKNIFTY":
                return "NSE_INDEX|Nifty Bank"
            elif symbol.upper() == "FINNIFTY":
                return "NSE_INDEX|Nifty Fin Services"
            
            # Generic fallback (likely to fail for many equities but better than nothing)
            return f"NSE_EQ|{symbol.upper()}"
            
        except Exception as e:
            logger.error(f"Error resolving instrument key for {symbol}: {e}")
            return f"NSE_EQ|{symbol.upper()}"

    def _process_upstox_response(
        self, data: Dict, symbol: str, market_open: bool
    ) -> Dict:
        """Process Upstox API response into standardized format"""
        # data structure based on v2 API documentation
        if not data:
            return {}

        # Extract the list of strikes from the 'data' key
        options_list = data.get("data", [])
        if not options_list or not isinstance(options_list, list):
            return {}

        strikes_data = []
        underlying_price = 0
        expiry_date = ""

        # Sort by strike price
        try:
            sorted_data = sorted(options_list, key=lambda x: x.get("strike_price", 0))

            for item in sorted_data:
                # Capture metadata from first item
                if not underlying_price:
                    underlying_price = item.get("underlying_spot_price", 0)
                if not expiry_date:
                    expiry_date = item.get("expiry", "")

                # Call Data
                call = item.get("call_options", {})
                call_md = call.get("market_data", {})
                call_greeks = call.get("option_greeks", {})

                # Put Data
                put = item.get("put_options", {})
                put_md = put.get("market_data", {})
                put_greeks = put.get("option_greeks", {})

                strike = {
                    "strike": item.get("strike_price"),
                    "call": {
                        "instrument_key": call.get("instrument_key"),
                        "ltp": call_md.get("ltp"),
                        "volume": call_md.get("volume"),
                        "oi": call_md.get("oi"),
                        "iv": call_greeks.get("iv"),
                        "delta": call_greeks.get("delta"),
                        "gamma": call_greeks.get("gamma"),
                        "theta": call_greeks.get("theta"),
                        "vega": call_greeks.get("vega"),
                        "bid": call_md.get("bid_price"),
                        "ask": call_md.get("ask_price"),
                    },
                    "put": {
                        "instrument_key": put.get("instrument_key"),
                        "ltp": put_md.get("ltp"),
                        "volume": put_md.get("volume"),
                        "oi": put_md.get("oi"),
                        "iv": put_greeks.get("iv"),
                        "delta": put_greeks.get("delta"),
                        "gamma": put_greeks.get("gamma"),
                        "theta": put_greeks.get("theta"),
                        "vega": put_greeks.get("vega"),
                        "bid": put_md.get("bid_price"),
                        "ask": put_md.get("ask_price"),
                    },
                }
                strikes_data.append(strike)

        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return {}

        result = {
            "symbol": symbol,
            "expiry_date": expiry_date,
            "underlying_price": underlying_price,
            "timestamp": datetime.now().isoformat(),
            "market_open": market_open,
            "strikes": strikes_data,
        }

        logger.info(f"[OPTIONS] Processed {len(strikes_data)} strikes")
        return result

    def _validate_mock_option_chain_removed(self):
        """Mock data removed as per user request"""
        pass


# Testing
if __name__ == "__main__":
    service = OptionsChainService()

    # Test market status
    is_open, msg = service.is_market_open()
    print(f"Market Status: {msg}")

    # Test option chain fetch
    chain = service.get_option_chain("NIFTY")
    
    if chain:
        print(f"\nOption Chain for {chain.get('symbol', 'Unknown')}:")
        print(f"Underlying: ₹{chain.get('underlying_price', 0)}")
        print(f"Expiry: {chain.get('expiry_date', 'N/A')}")
        print(f"Strikes: {len(chain.get('strikes', []))}")
        print(f"Data source: {chain.get('data_source', 'live')}")
    else:
        print("\n❌ No option chain data available (Token expired or Market closed)")
