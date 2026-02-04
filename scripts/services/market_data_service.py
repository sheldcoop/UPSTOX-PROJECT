"""Market Data Service - Quotes, LTP, OHLC, Depth, Option Greeks"""

from typing import Dict, Any, List, Optional, Tuple
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_fetcher import UpstoxFetcher
from scripts.config_loader import get_api_base_url, get_api_base_url_v3


class MarketDataService(UpstoxFetcher):
    """Handles market data operations"""

    def __init__(self, base_url: Optional[str] = None, cache_ttl: float = 1.0):
        super().__init__(base_url=base_url or get_api_base_url())
        self._cache_ttl = cache_ttl
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._base_url_v3 = get_api_base_url_v3()

    def _cache_get(self, key: str) -> Optional[Any]:
        cached = self._cache.get(key)
        if not cached:
            return None
        timestamp, value = cached
        if (time.time() - timestamp) > self._cache_ttl:
            self._cache.pop(key, None)
            return None
        return value

    def _cache_set(self, key: str, value: Any):
        self._cache[key] = (time.time(), value)
    
    def get_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """Get full quotes for symbols"""
        symbol_param = ",".join(symbols)
        cache_key = f"quotes:{symbol_param}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        response = self.fetch("/market-quote/quotes", params={"instrument_key": symbol_param})
        if not self.validate_response(response):
            raise ValueError("Failed to fetch quotes")
        data = response.get("data", {})
        self._cache_set(cache_key, data)
        return data
    
    def get_ltp(self, symbols: List[str]) -> Dict[str, float]:
        """Get last traded price"""
        symbol_param = ",".join(symbols)
        cache_key = f"ltp:{symbol_param}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        response = self.fetch("/market-quote/ltp", params={"instrument_key": symbol_param})
        if not self.validate_response(response):
            raise ValueError("Failed to fetch LTP")
        data = response.get("data", {})
        result = {k: v.get("last_price", 0.0) for k, v in data.items()}
        self._cache_set(cache_key, result)
        return result
    
    def get_ohlc(self, symbols: List[str]) -> Dict[str, Any]:
        """Get OHLC data"""
        symbol_param = ",".join(symbols)
        cache_key = f"ohlc:{symbol_param}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        response = self.fetch("/market-quote/ohlc", params={"instrument_key": symbol_param})
        if not self.validate_response(response):
            raise ValueError("Failed to fetch OHLC")
        data = response.get("data", {})
        self._cache_set(cache_key, data)
        return data
    
    def get_market_depth(self, symbol: str) -> Dict[str, Any]:
        """Get market depth (order book)"""
        cache_key = f"depth:{symbol}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        response = self.fetch("/market-quote/depth", params={"instrument_key": symbol})
        if not self.validate_response(response):
            raise ValueError("Failed to fetch market depth")
        data = response.get("data", {}).get(symbol, {})
        depth = data.get("depth", {})
        self._cache_set(cache_key, depth)
        return depth

    def get_option_greeks(self, symbols: List[str]) -> Dict[str, Any]:
        """Get option greeks via V3 endpoint"""
        symbol_param = ",".join(symbols)
        cache_key = f"greeks:{symbol_param}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        url = f"{self._base_url_v3}/market-quote/option-greek"
        self._rate_limit()
        response = self.session.get(
            url,
            headers=self._get_headers(),
            params={"instrument_key": symbol_param},
            timeout=30,
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch option greeks: {response.status_code}")
        data = response.json().get("data", {})
        self._cache_set(cache_key, data)
        return data
