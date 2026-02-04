"""Trade P&L Service - Profit/Loss data, metadata, charges"""

from typing import Dict, Any

from base_fetcher import UpstoxFetcher


class TradePnLService(UpstoxFetcher):
    """Handles trade P&L endpoints"""

    def get_pnl_data(self) -> Dict[str, Any]:
        response = self.fetch("/trade/profit-loss/data")
        if not self.validate_response(response):
            raise ValueError("Failed to fetch P&L data")
        return response.get("data", {})

    def get_pnl_metadata(self) -> Dict[str, Any]:
        response = self.fetch("/trade/profit-loss/metadata")
        if not self.validate_response(response):
            raise ValueError("Failed to fetch P&L metadata")
        return response.get("data", {})

    def get_pnl_charges(self) -> Dict[str, Any]:
        response = self.fetch("/trade/profit-loss/charges")
        if not self.validate_response(response):
            raise ValueError("Failed to fetch P&L charges")
        return response.get("data", {})
