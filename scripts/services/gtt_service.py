"""GTT Service - Create, modify, cancel, retrieve GTT orders"""

from typing import Dict, Any, List, Optional
import time

from base_fetcher import UpstoxFetcher
from scripts.config_loader import get_api_base_url, get_api_base_url_v3
from scripts.services.v3_fetch_mixin import V3FetcherMixin


class GTTService(V3FetcherMixin, UpstoxFetcher):
    """Handles Good-Till-Triggered order operations"""

    def __init__(self, base_url: Optional[str] = None):
        super().__init__(base_url=base_url or get_api_base_url())
        self._base_url_v3 = get_api_base_url_v3()


    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize incoming payload to v3 GTT format when possible"""
        instrument_token = (
            payload.get("instrument_token")
            or payload.get("instrument_key")
            or payload.get("symbol")
        )

        order_type = payload.get("order_type", "SINGLE")
        gtt_type = "MULTIPLE" if order_type == "OCO" else "SINGLE"

        condition_type = payload.get("condition_type", "LTP_ABOVE")
        if "BELOW" in condition_type:
            trigger_type = "BELOW"
        else:
            trigger_type = "ABOVE"

        trigger_price = payload.get("trigger_price")
        limit_price = payload.get("limit_price")

        rules = [
            {
                "strategy": "ENTRY",
                "trigger_type": trigger_type,
                "trigger_price": trigger_price,
            }
        ]

        if gtt_type == "MULTIPLE" and limit_price is not None:
            rules.append(
                {
                    "strategy": "TARGET",
                    "trigger_type": "IMMEDIATE",
                    "trigger_price": limit_price,
                }
            )

        return {
            "type": gtt_type,
            "quantity": payload.get("quantity"),
            "product": payload.get("product", "D"),
            "rules": rules,
            "instrument_token": instrument_token,
            "transaction_type": payload.get("transaction_type"),
        }

    @staticmethod
    def _looks_like_v3(payload: Dict[str, Any]) -> bool:
        return "rules" in payload or "type" in payload or "instrument_token" in payload

    def create_gtt(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GTT order"""
        try:
            response = self.fetch("/gtt/create", method="POST", data=payload)
            if not self.validate_response(response):
                raise ValueError("Failed to create GTT")
            return response.get("data", {})
        except Exception:
            v3_payload = payload if self._looks_like_v3(payload) else self._normalize_payload(payload)
            response = self._fetch_v3("/order/gtt/place", method="POST", data=v3_payload)
            if not self.validate_response(response):
                raise ValueError("Failed to create GTT (v3)")
            return response.get("data", {})

    def modify_gtt(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Modify a GTT order"""
        try:
            response = self.fetch("/gtt/modify", method="PUT", data=payload)
            if not self.validate_response(response):
                raise ValueError("Failed to modify GTT")
            return response.get("data", {})
        except Exception:
            response = self._fetch_v3("/order/gtt/modify", method="PUT", data=payload)
            if not self.validate_response(response):
                raise ValueError("Failed to modify GTT (v3)")
            return response.get("data", {})

    def cancel_gtt(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel a GTT order"""
        try:
            response = self.fetch("/gtt/cancel", method="DELETE", data=payload)
            if not self.validate_response(response):
                raise ValueError("Failed to cancel GTT")
            return response.get("data", {})
        except Exception:
            response = self._fetch_v3("/order/gtt/cancel", method="DELETE", data=payload)
            if not self.validate_response(response):
                raise ValueError("Failed to cancel GTT (v3)")
            return response.get("data", {})

    def retrieve_all(self) -> List[Dict[str, Any]]:
        """Retrieve all GTT orders"""
        try:
            response = self.fetch("/gtt/retrieve-all")
            if not self.validate_response(response):
                raise ValueError("Failed to retrieve GTT orders")
            return response.get("data", [])
        except Exception:
            response = self._fetch_v3("/order/gtt", method="GET")
            if not self.validate_response(response):
                raise ValueError("Failed to retrieve GTT orders (v3)")
            return response.get("data", [])
