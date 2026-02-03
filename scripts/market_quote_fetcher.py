import sqlite3
import requests
import logging
from typing import List, Dict, Any, Optional
from scripts.auth_manager import AuthManager

logger = logging.getLogger(__name__)

DB_PATH = "market_data.db"


class MarketQuoteFetcher:
    API_URL = "https://api.upstox.com/v2/market-quote/quotes"

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.auth = AuthManager(db_path=db_path)

    def resolve_instrument_keys(self, symbols: List[str]) -> Dict[str, str]:
        """
        Resolve symbol names (e.g., 'NHPC', 'INFY') to Instrument Keys.
        Returns a dict mapping {symbol: instrument_key}
        """
        if not symbols:
            return {}

        # Prepare placeholders
        placeholders = ",".join(["?"] * len(symbols))

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Try exact match on 'symbol' or 'trading_symbol'
        # Prefer NSE_EQ for equities if duplicate symbols exist across exchanges
        query = f"""
            SELECT symbol, instrument_key, segment_id 
            FROM instruments 
            WHERE symbol IN ({placeholders}) 
            ORDER BY CASE WHEN segment_id = 'NSE_EQ' THEN 1 ELSE 2 END
        """

        cursor.execute(query, symbols)
        rows = cursor.fetchall()
        conn.close()

        mapping = {}
        # Use the first match (NSE_EQ preferred due to order by)
        for row in rows:
            sym, key, seg = row
            if sym not in mapping:
                mapping[sym] = key

        return mapping

    def fetch_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Fetch full market quotes for a list of symbols.
        """
        # 1. Resolve symbols to keys
        # If the input looks like an instrument key (contains '|'), use it directly
        keys_to_fetch = []
        symbol_map = {}  # key -> original_symbol

        resolved_map = self.resolve_instrument_keys(
            [s for s in symbols if "|" not in s]
        )

        for sym in symbols:
            if "|" in sym:
                keys_to_fetch.append(sym)
                symbol_map[sym] = sym
            elif sym in resolved_map:
                key = resolved_map[sym]
                keys_to_fetch.append(key)
                symbol_map[key] = sym
            else:
                logger.warning(f"Could not resolve symbol: {sym}")

        if not keys_to_fetch:
            return {"error": "No valid instruments resolved"}

        # 2. Get Token
        try:
            token = self.auth.get_valid_token()
            if not token:
                raise Exception("Auth token retrieval failed")
        except Exception as e:
            logger.error(f"Auth Error: {e}")
            return {"error": "Authentication Failed"}

        # 3. Call API
        # Upstox allows comma separated keys
        # Max limit per call is 100 usually, but let's batch if needed (not implementing batching for now)

        str_keys = ",".join(keys_to_fetch)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        }

        try:
            response = requests.get(
                self.API_URL,
                headers=headers,
                params={"instrument_key": str_keys},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    # Enhance result with original symbol request
                    result_data = data.get("data", {})
                    # Map back to original requested symbols if possible?
                    # The response is keyed by instrument_key.
                    # e.g. "NSE_EQ|...": { ... }
                    return result_data
                else:
                    return {"error": data.get("message", "Unknown API error")}
            else:
                return {"error": f"API Error {response.status_code}: {response.text}"}

        except Exception as e:
            logger.error(f"Quote Fetch Error: {e}")
            return {"error": str(e)}


if __name__ == "__main__":
    # Test
    fetcher = MarketQuoteFetcher()
    res = fetcher.fetch_quotes(["NHPC", "INFY"])
    print(res)
