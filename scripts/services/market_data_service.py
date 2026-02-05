"""Market Data Service - Quotes, LTP, OHLC"""

from typing import Dict, Any, List
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_fetcher import UpstoxFetcher


class MarketDataService(UpstoxFetcher):
    """Handles market data operations"""
    
    def get_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """Get full quotes for symbols"""
        symbol_param = ",".join(symbols)
        response = self.fetch("/market-quote/quotes", params={"instrument_key": symbol_param})
        if not self.validate_response(response):
            raise ValueError("Failed to fetch quotes")
        return response.get("data", {})
    
    def get_ltp(self, symbols: List[str]) -> Dict[str, float]:
        """Get last traded price"""
        symbol_param = ",".join(symbols)
        response = self.fetch("/market-quote/ltp", params={"instrument_key": symbol_param})
        if not self.validate_response(response):
            raise ValueError("Failed to fetch LTP")
        data = response.get("data", {})
        return {k: v.get("last_price", 0.0) for k, v in data.items()}
    
    def get_ohlc(self, symbols: List[str]) -> Dict[str, Any]:
        """Get OHLC data"""
        symbol_param = ",".join(symbols)
        response = self.fetch("/market-quote/ohlc", params={"instrument_key": symbol_param})
        if not self.validate_response(response):
            raise ValueError("Failed to fetch OHLC")
        return response.get("data", {})
    
    def get_market_depth(self, symbol: str) -> Dict[str, Any]:
        """Get market depth (order book)"""
        response = self.fetch("/market-quote/quotes", params={"instrument_key": symbol})
        if not self.validate_response(response):
            raise ValueError("Failed to fetch market depth")
        data = response.get("data", {}).get(symbol, {})
        return data.get("depth", {})
