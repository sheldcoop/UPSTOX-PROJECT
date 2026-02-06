"""
Live Upstox API Integration Service
Connects to real Upstox API for market data, positions, and orders
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from backend.utils.auth.manager import AuthManager
from backend.utils.logging.error_handler import with_retry

# Setup logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

import sqlite3


class UpstoxLiveAPI:
    """Live Upstox API integration with real-time data"""

    def __init__(self):
        self.auth_manager = AuthManager()
        self.session = requests.Session()

    def _log_no_token(self, message: str, level: str = "warning"):
        if level == "error":
            logger.error(message)
        else:
            logger.warning(message)

    def _get_headers(self) -> Dict[str, str]:
        token = self.auth_manager.get_valid_token()
        if not token:
            self._log_no_token("No valid Upstox token available", level="warning")
            return {}

        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        }

    def _build_url(self, endpoint: str) -> str:
        return f"{self.BASE_URL}{endpoint}"

    def _get(self, endpoint: str, timeout: int):
        headers = self._get_headers()
        if not headers:
            return None
        return self.session.get(self._build_url(endpoint), headers=headers, timeout=timeout)

    @with_retry(max_attempts=2)
    def get_profile(self) -> Optional[Dict]:
        """Get user profile"""
        try:
            response = self._get("/user/profile", timeout=10)
            if response is None:
                return None

            if response.status_code == 200:
                data = response.json()
                logger.info(
                    f"Profile fetched: {data.get('data', {}).get('user_name', 'Unknown')}"
                )
                return data.get("data")
            else:
                logger.error(
                    f"Profile fetch failed: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Error fetching profile: {e}", exc_info=True)
            return None

    @with_retry(max_attempts=2)
    def get_holdings(self) -> List[Dict]:
        """Get user holdings"""
        try:
            response = self._get("/portfolio/long-term-holdings", timeout=10)
            if response is None:
                return []

            if response.status_code == 200:
                data = response.json()
                holdings = data.get("data", [])
                logger.info(f"Fetched {len(holdings)} holdings")
                return holdings
            else:
                logger.error(f"Holdings fetch failed: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error fetching holdings: {e}", exc_info=True)
            return []

    @with_retry(max_attempts=2)
    def get_positions(self) -> Dict[str, List[Dict]]:
        """Get open positions"""
        try:
            response = self._get("/portfolio/short-term-positions", timeout=10)
            if response is None:
                return {"day": [], "net": []}

            if response.status_code == 200:
                data = response.json()
                positions = data.get("data", {})
                logger.info(
                    f"Fetched positions: {len(positions.get('day', []))} day, {len(positions.get('net', []))} net"
                )
                return positions
            else:
                logger.error(f"Positions fetch failed: {response.status_code}")
                return {"day": [], "net": []}

        except Exception as e:
            logger.error(f"Error fetching positions: {e}", exc_info=True)
            return {"day": [], "net": []}

    @with_retry(max_attempts=2)
    def get_option_chain(
        self, symbol: str, expiry_date: Optional[str] = None
    ) -> Optional[Dict]:
        """Get live option chain data"""
        try:
            headers = self._get_headers()
            if not headers:
                return None

            # Get instrument key for the symbol
            instrument_key = self._get_instrument_key(symbol)
            if not instrument_key:
                logger.warning(f"Could not find instrument key for {symbol}")
                return None

            # Fetch option chain
            params = {"instrument_key": instrument_key}
            if expiry_date:
                params["expiry_date"] = expiry_date

            response = self.session.get(
                f"{self.BASE_URL}/option/chain",
                headers=headers,
                params=params,
                timeout=15,
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Fetched option chain for {symbol}")
                return data.get("data")
            else:
                logger.error(f"Option chain fetch failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error fetching option chain: {e}", exc_info=True)
            return None

    @with_retry(max_attempts=2)
    def get_market_quote(self, symbol: str) -> Optional[Dict]:
        """Get live market quote"""
        try:
            headers = self._get_headers()
            if not headers:
                return None

            instrument_key = self._get_instrument_key(symbol)
            if not instrument_key:
                return None

            response = self.session.get(
                f"{self.BASE_URL}/market-quote/quotes",
                headers=headers,
                params={"instrument_key": instrument_key},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get(instrument_key)
            else:
                logger.error(f"Market quote fetch failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error fetching market quote: {e}", exc_info=True)
            return None

    @with_retry(max_attempts=3)
    def get_batch_market_quotes(self, instrument_keys: List[str]) -> Dict[str, Any]:
        """
        Get live market quotes for multiple instruments (Max 500 automatically handled in batches)
        Returns a dictionary mapping instrument_key -> quote_data
        """
        try:
            headers = self._get_headers()
            if not headers or not instrument_keys:
                return {}

            # Remove duplicates and empty keys
            unique_keys = list(set([k for k in instrument_keys if k]))
            results = {}

            # Upstox Limit: 500 keys per call
            BATCH_SIZE = 450  # Safety margin

            for i in range(0, len(unique_keys), BATCH_SIZE):
                batch = unique_keys[i : i + BATCH_SIZE]
                keys_str = ",".join(batch)

                try:
                    response = self.session.get(
                        f"{self.BASE_URL}/market-quote/quotes",
                        headers=headers,
                        params={"instrument_key": keys_str},
                        timeout=15,
                    )

                    if response.status_code == 200:
                        data = response.json().get("data", {})
                        results.update(data)
                    else:
                        logger.error(
                            f"Batch quote fetch failed {response.status_code} for batch {i}"
                        )

                except Exception as batch_err:
                    logger.error(f"Batch fetch error: {batch_err}")
                    continue

            return results

        except Exception as e:
            logger.error(f"Error fetching batch quotes: {e}", exc_info=True)
            return {}

    @with_retry(max_attempts=2)
    def get_historical_candles(
        self, instrument_key: str, interval: str, to_date: str, from_date: str
    ) -> List[List[Any]]:
        """
        Fetch historical candles for an active instrument
        Endpoint: /v2/historical-candle/{instrumentKey}/{interval}/{toDate}/{fromDate}

        Args:
            instrument_key: Upstox instrument key (e.g., 'NSE_EQ|INE002A01018')
            interval: Candle interval ('1minute', '30minute', 'day', etc.)
            to_date: End date (YYYY-MM-DD)
            from_date: Start date (YYYY-MM-DD)

        Returns:
            List of candles [[timestamp, open, high, low, close, volume, oi], ...]
        """
        try:
            headers = self._get_headers()
            if not headers:
                return []

            # Construct URL
            url = f"{self.BASE_URL}/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"

            response = self.session.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                candles = data.get("data", {}).get("candles", [])
                if candles:
                    logger.info(f"Fetched {len(candles)} candles for {instrument_key}")
                else:
                    logger.warning(f"No candles found for {instrument_key}")
                return candles
            else:
                logger.error(
                    f"Historical candle fetch failed: {response.status_code} - {response.text}"
                )
                return []

        except Exception as e:
            logger.error(f"Error fetching historical candles: {e}", exc_info=True)
            return []

    @with_retry(max_attempts=2)
    def get_funds(self) -> Optional[Dict]:
        """Get account funds/margin"""
        try:
            headers = self._get_headers()
            if not headers:
                return None

            response = self.session.get(
                f"{self.BASE_URL}/user/get-funds-and-margin",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("data")
            else:
                logger.error(f"Funds fetch failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error fetching funds: {e}", exc_info=True)
            return None

    def _get_instrument_key(self, symbol: str) -> Optional[str]:
        """Get instrument key from local database"""

        # 1. Try common indices first (Hardcoded for speed)
        common_map = {
            "NIFTY": "NSE_INDEX|Nifty 50",
            "BANKNIFTY": "NSE_INDEX|Nifty Bank",
            "FINNIFTY": "NSE_INDEX|Nifty Fin Service",
        }
        if symbol.upper() in common_map:
            return common_map[symbol.upper()]

        # 2. Look up in SQLite database
        try:
            # Fix: DB is in Project Root
            root_dir = Path(__file__).resolve().parent.parent.parent.parent
            db_path = root_dir / "market_data.db"
            
            # Ensure we're not blocking on a long query
            conn = sqlite3.connect(db_path, timeout=1)
            cursor = conn.cursor()

            # Try to match Symbol exactly or Trading Symbol
            # The user might type "RELIANCE" or "RELIANCE-EQ"
            target = symbol.upper()

            # Optimized Query: Check exact matches first in instrument_master
            cursor.execute(
                """
                SELECT instrument_key 
                FROM instrument_master 
                WHERE trading_symbol = ? 
                   OR name = ? 
                LIMIT 1
            """,
                (target, target),
            )

            row = cursor.fetchone()
            if row:
                conn.close()
                return row[0]

            # Fallback: Try fuzzy search or "NSE_EQ" segment if not specified
            cursor.execute(
                """
                SELECT instrument_key 
                FROM instrument_master 
                WHERE trading_symbol = ? AND segment = 'NSE_EQ'
                LIMIT 1
            """,
                (target,),
            )
            row = cursor.fetchone()

            conn.close()
            return row[0] if row else None

        except Exception as e:
            logger.error(f"Error looking up instrument key for {symbol}: {e}")
            return None

    def place_order(self, order_params: Dict) -> Optional[Dict]:
        """Place order (to be implemented in order placement system)"""
        logger.info("Order placement feature coming in next module")
        return None


# Singleton instance
_upstox_live_api = None


def get_upstox_api() -> UpstoxLiveAPI:
    """Get singleton Upstox API instance"""
    global _upstox_live_api
    if _upstox_live_api is None:
        _upstox_live_api = UpstoxLiveAPI()
    return _upstox_live_api


if __name__ == "__main__":
    # Test the API
    api = get_upstox_api()

    print("Testing Upstox Live API...")
    print("\n1. Profile:")
    profile = api.get_profile()
    if profile:
        print(f"   User: {profile.get('user_name')}")
        print(f"   Email: {profile.get('email')}")

    print("\n2. Holdings:")
    holdings = api.get_holdings()
    print(f"   Total holdings: {len(holdings)}")

    print("\n3. Positions:")
    positions = api.get_positions()
    print(f"   Day positions: {len(positions.get('day', []))}")
    print(f"   Net positions: {len(positions.get('net', []))}")

    print("\n4. Funds:")
    funds = api.get_funds()
    if funds:
        print(f"   Available margin: ₹{funds.get('available_margin', 0):,.2f}")

    print("\n5. Market Quote (NIFTY):")
    quote = api.get_market_quote("NIFTY")
    if quote:
        print(f"   LTP: {quote.get('last_price', 0)}")
