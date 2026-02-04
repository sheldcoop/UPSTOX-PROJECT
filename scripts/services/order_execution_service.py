"""Order Execution Service - Place, modify, cancel, order book, trades"""

from typing import Dict, Any, List, Optional
import time

from base_fetcher import UpstoxFetcher
from scripts.config_loader import get_api_base_url, get_api_base_url_v3
from scripts.logger_config import get_logger
from scripts.services.identity_service import IdentityService
from scripts.services.risk_service import RiskService
from scripts.services.v3_fetch_mixin import V3FetcherMixin

logger = get_logger(__name__)


class OrderExecutionService(V3FetcherMixin, UpstoxFetcher):
    """Handles order lifecycle operations"""

    def __init__(self, base_url: Optional[str] = None, use_v3: bool = True):
        super().__init__(base_url=base_url or get_api_base_url())
        self._base_url_v3 = get_api_base_url_v3()
        self._use_v3 = use_v3


    def place_order(
        self,
        instrument_key: str,
        quantity: int,
        transaction_type: str,
        order_type: str = "MARKET",
        price: Optional[float] = None,
        product: str = "D",
        trigger_price: Optional[float] = None,
        disclosed_quantity: Optional[int] = None,
        is_amo: bool = False,
        validity: str = "DAY",
        tag: str = "string",
        validate_margin: bool = False,
    ) -> Dict[str, Any]:
        if validate_margin:
            self._validate_pre_trade(
                instrument_key=instrument_key,
                quantity=quantity,
                transaction_type=transaction_type,
                price=price,
            )

        payload: Dict[str, Any] = {
            "quantity": quantity,
            "product": product,
            "validity": validity,
            "price": price or 0,
            "tag": tag,
            "instrument_key": instrument_key,
            "order_type": order_type,
            "transaction_type": transaction_type,
            "disclosed_quantity": disclosed_quantity or 0,
            "trigger_price": trigger_price or 0,
            "is_amo": is_amo,
        }

        if self._use_v3:
            try:
                response = self._fetch_v3("/order/place", method="POST", data=payload)
                if not self.validate_response(response):
                    raise ValueError("Failed to place order (v3)")
                return response.get("data", {})
            except Exception:
                pass

        response = self.fetch("/order/place", method="POST", data=payload)
        if not self.validate_response(response):
            raise ValueError("Failed to place order")
        return response.get("data", {})

    def _validate_pre_trade(
        self,
        instrument_key: str,
        quantity: int,
        transaction_type: str,
        price: Optional[float],
    ):
        try:
            risk = RiskService()
            identity = IdentityService()

            margin_data = risk.calculate_margin(
                instrument_token=instrument_key,
                quantity=quantity,
                transaction_type=transaction_type,
                price=price,
            )
            required = self._extract_required_margin(margin_data)
            available = identity.get_balance()

            if required is None:
                logger.warning("Unable to determine required margin; skipping check")
                return

            if available < required:
                raise ValueError(
                    f"Insufficient funds: required {required}, available {available}"
                )
        except Exception as e:
            raise ValueError(f"Pre-trade validation failed: {e}")

    def _extract_required_margin(self, data: Dict[str, Any]) -> Optional[float]:
        if not isinstance(data, dict):
            return None

        for key in [
            "required_margin",
            "required",
            "margin",
            "total",
            "total_margin",
            "requiredMargin",
        ]:
            if key in data and data[key] is not None:
                try:
                    return float(data[key])
                except Exception:
                    continue

        span = data.get("span")
        exposure = data.get("exposure")
        if span is not None or exposure is not None:
            try:
                return float(span or 0) + float(exposure or 0)
            except Exception:
                return None

        return None

    def place_multi_order(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        response = self.fetch("/order/multi/place", method="POST", data={"orders": orders})
        if not self.validate_response(response):
            raise ValueError("Failed to place multi order")
        return response.get("data", {})

    def modify_order(self, order_id: str, **kwargs) -> Dict[str, Any]:
        payload = {"order_id": order_id, **kwargs}

        if self._use_v3:
            try:
                response = self._fetch_v3("/order/modify", method="PUT", data=payload)
                if not self.validate_response(response):
                    raise ValueError("Failed to modify order (v3)")
                return response.get("data", {})
            except Exception:
                pass

        response = self.fetch("/order/modify", method="PUT", data=payload)
        if not self.validate_response(response):
            raise ValueError("Failed to modify order")
        return response.get("data", {})

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        payload = {"order_id": order_id}

        if self._use_v3:
            try:
                response = self._fetch_v3("/order/cancel", method="DELETE", data=payload)
                if not self.validate_response(response):
                    raise ValueError("Failed to cancel order (v3)")
                return response.get("data", {})
            except Exception:
                pass

        response = self.fetch("/order/cancel", method="DELETE", data=payload)
        if not self.validate_response(response):
            raise ValueError("Failed to cancel order")
        return response.get("data", {})

    def get_order_book(self) -> List[Dict[str, Any]]:
        response = self.fetch("/order/retrieve-all")
        if not self.validate_response(response):
            raise ValueError("Failed to fetch order book")
        return response.get("data", [])

    def get_order_details(self, order_id: str) -> Dict[str, Any]:
        response = self.fetch("/order/details", params={"order_id": order_id})
        if not self.validate_response(response):
            raise ValueError("Failed to fetch order details")
        return response.get("data", {})

    def get_order_history(self, order_id: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"order_id": order_id} if order_id else None
        response = self.fetch("/order/history", params=params)
        if not self.validate_response(response):
            raise ValueError("Failed to fetch order history")
        return response.get("data", [])

    def get_trades_for_day(self) -> List[Dict[str, Any]]:
        response = self.fetch("/order/trades/get-trades-for-day")
        if not self.validate_response(response):
            raise ValueError("Failed to fetch trades for day")
        return response.get("data", [])

    def get_trades_by_order(self, order_id: str) -> List[Dict[str, Any]]:
        response = self.fetch(
            "/order/trades/get-trades-by-order",
            params={"order_id": order_id},
        )
        if not self.validate_response(response):
            raise ValueError("Failed to fetch trades by order")
        return response.get("data", [])
