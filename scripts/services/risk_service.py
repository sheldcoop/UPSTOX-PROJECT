"""Risk Service - Brokerage and margin calculations"""

from typing import Dict, Any

from base_fetcher import UpstoxFetcher


class RiskService(UpstoxFetcher):
    """Handles pre-trade validation (charges and margin)"""

    def calculate_brokerage(
        self,
        instrument_token: str,
        quantity: int,
        price: float,
        transaction_type: str,
        product: str = "D",
    ) -> Dict[str, Any]:
        payload = {
            "instrument_token": instrument_token,
            "quantity": quantity,
            "price": price,
            "transaction_type": transaction_type,
            "product": product,
        }
        response = self.fetch("/charges/brokerage", method="POST", data=payload)
        if not self.validate_response(response):
            raise ValueError("Failed to calculate brokerage")
        return response.get("data", {})

    def calculate_margin(
        self,
        instrument_token: str,
        quantity: int,
        transaction_type: str,
        price: float | None = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "instrument_token": instrument_token,
            "quantity": quantity,
            "transaction_type": transaction_type,
        }
        if price is not None:
            payload["price"] = price

        response = self.fetch("/charges/margin", method="POST", data=payload)
        if not self.validate_response(response):
            raise ValueError("Failed to calculate margin")
        return response.get("data", {})
