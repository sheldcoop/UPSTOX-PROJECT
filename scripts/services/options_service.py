"""Options Service - Option chains and Greeks"""

from typing import Dict, Any, List
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_fetcher import UpstoxFetcher


class OptionsService(UpstoxFetcher):
    """Handles options-related operations"""
    
    def get_option_chain(self, symbol: str, expiry_date: str) -> Dict[str, Any]:
        """Get option chain for symbol and expiry"""
        params = {
            "instrument_key": symbol,
            "expiry_date": expiry_date
        }
        response = self.fetch("/option/chain", params=params)
        if not self.validate_response(response):
            raise ValueError("Failed to fetch option chain")
        return response.get("data", {})
    
    def get_option_greeks(self, symbols: List[str]) -> Dict[str, Any]:
        """Get option Greeks for symbols"""
        symbol_param = ",".join(symbols)
        response = self.fetch("/market-quote/option-greek", params={"instrument_key": symbol_param})
        if not self.validate_response(response):
            raise ValueError("Failed to fetch option Greeks")
        return response.get("data", {})
    
    def get_expiry_dates(self, symbol: str) -> List[str]:
        """Get available expiry dates for symbol"""
        response = self.fetch("/option/contract", params={"instrument_key": symbol})
        if not self.validate_response(response):
            raise ValueError("Failed to fetch expiry dates")
        data = response.get("data", [])
        return sorted(set(item.get("expiry") for item in data if item.get("expiry")))
