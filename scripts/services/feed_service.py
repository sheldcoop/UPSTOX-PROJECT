"""Feed Service - WebSocket client with Protobuf decoding"""

from typing import Dict, Any, Optional, Callable, List
import json
import time
import uuid
import threading
import requests
import websocket
import os
import importlib

from google.protobuf.json_format import MessageToDict
from base_fetcher import UpstoxFetcher
from scripts.auth_helper import auth
from scripts.config_loader import get_api_base_url, get_api_base_url_v3, get_api_timeout
from scripts.logger_config import get_logger

logger = get_logger(__name__)


class FeedService(UpstoxFetcher):
    """Handles feed authorization and websocket connection"""
    MAX_SYMBOLS_PER_SOCKET = 100
    MAX_SYMBOLS_FULL_D30_GLOBAL = 50
    MAX_SOCKETS = 5

    def __init__(self, auth_manager: Optional[object] = None, base_url: Optional[str] = None):
        super().__init__(base_url=base_url or get_api_base_url())
        self.session = self.session
        self.auth = auth
        self._base_url_v3 = get_api_base_url_v3()

        self.ws = None
        self.ws_url = None
        self.connected = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10

        self._on_message_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._on_error_callback: Optional[Callable[[Exception], None]] = None
        self._feed_type: Optional[str] = None
        self._proto_module = None

    def _get_headers(self) -> Dict[str, str]:
        return self.auth.get_headers()

    def authorize_market_data_feed(self) -> Dict[str, Any]:
        self._rate_limit()
        response = self.session.get(
            f"{self._base_url_v3}/feed/market-data-feed/authorize",
            headers=self._get_headers(),
            timeout=get_api_timeout(),
        )
        if response.status_code != 200:
            raise ValueError(f"Market data feed auth failed: {response.status_code}")
        return response.json().get("data", {})

    def _ensure_proto_compiled(self):
        if self._proto_module:
            return

        proto_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "proto"
        )

        candidates = [
            ("scripts.proto.MarketDataFeedV3_pb2", "MarketDataFeedV3.proto"),
            ("scripts.proto.market_data_feed_pb2", "market_data_feed.proto"),
        ]

        for module_name, proto_file in candidates:
            try:
                self._proto_module = importlib.import_module(module_name)
                return
            except Exception:
                proto_path = os.path.join(proto_dir, proto_file)
                if not os.path.exists(proto_path):
                    continue

        raise ValueError("No precompiled market data proto found")

    def authorize_portfolio_stream(self, update_types: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/feed/portfolio-stream-feed/authorize"
        params = {"update_types": update_types} if update_types else None
        self._rate_limit()
        response = self.session.get(
            url, headers=self._get_headers(), params=params, timeout=get_api_timeout()
        )
        if response.status_code != 200:
            raise ValueError(f"Portfolio stream auth failed: {response.status_code}")
        return response.json().get("data", {})

    def authorize_order_updates(self) -> Dict[str, Any]:
        return self.authorize_portfolio_stream(update_types="order")

    def connect(self, feed_type: str, update_types: Optional[str] = None) -> bool:
        self._feed_type = feed_type

        if feed_type == "market-data":
            auth_data = self.authorize_market_data_feed()
        elif feed_type == "portfolio":
            auth_data = self.authorize_portfolio_stream(update_types=update_types)
        elif feed_type == "order-update":
            auth_data = self.authorize_order_updates()
        else:
            raise ValueError("Invalid feed_type")

        self.ws_url = auth_data.get("authorized_redirect_uri")
        if not self.ws_url:
            raise ValueError("No websocket URL returned")

        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open,
        )

        thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        thread.start()

        for _ in range(10):
            if self.connected:
                self._reconnect_attempts = 0
                return True
            time.sleep(0.5)

        return False

    def connect_market_data(self) -> bool:
        return self.connect("market-data")

    def connect_order_updates(self) -> bool:
        return self.connect("order-update")

    def connect_portfolio(self, update_types: Optional[str] = None) -> bool:
        return self.connect("portfolio", update_types=update_types)

    def authorize(self, access_token: str) -> Dict[str, Any]:
        return {"access_token": access_token}

    def subscribe(self, instrument_keys: List[str], mode: str = "ltpc"):
        if not self.connected or not self.ws:
            raise ValueError("WebSocket not connected")

        if mode == "option_chain":
            mode = "option_greeks"

        payload = {
            "guid": str(uuid.uuid4()),
            "method": "sub",
            "data": {"mode": mode, "instrumentKeys": instrument_keys},
        }
        self.ws.send(
            json.dumps(payload).encode("utf-8"), opcode=websocket.ABNF.OPCODE_BINARY
        )

    def unsubscribe(self, instrument_keys: List[str]):
        if not self.connected or not self.ws:
            raise ValueError("WebSocket not connected")

        payload = {
            "guid": str(uuid.uuid4()),
            "method": "unsub",
            "data": {"instrumentKeys": instrument_keys},
        }
        self.ws.send(
            json.dumps(payload).encode("utf-8"), opcode=websocket.ABNF.OPCODE_BINARY
        )

    def change_mode(self, instrument_keys: List[str], mode: str):
        if not self.connected or not self.ws:
            raise ValueError("WebSocket not connected")

        if mode == "option_chain":
            mode = "option_greeks"

        payload = {
            "guid": str(uuid.uuid4()),
            "method": "change_mode",
            "data": {"mode": mode, "instrumentKeys": instrument_keys},
        }
        self.ws.send(
            json.dumps(payload).encode("utf-8"), opcode=websocket.ABNF.OPCODE_BINARY
        )

    def on_message(self, callback: Callable[[Dict[str, Any]], None]):
        self._on_message_callback = callback

    def on_error(self, callback: Callable[[Exception], None]):
        self._on_error_callback = callback

    def disconnect(self):
        if self.ws:
            self.ws.close()
        self.connected = False

    @staticmethod
    def prioritize_symbols(
        active_symbols: List[str],
        other_symbols: Optional[List[str]] = None,
        limit: int = MAX_SYMBOLS_FULL_D30_GLOBAL,
    ) -> List[str]:
        seen = set()
        prioritized: List[str] = []

        for symbol in active_symbols or []:
            if symbol not in seen:
                seen.add(symbol)
                prioritized.append(symbol)
            if len(prioritized) >= limit:
                return prioritized

        for symbol in other_symbols or []:
            if symbol not in seen:
                seen.add(symbol)
                prioritized.append(symbol)
            if len(prioritized) >= limit:
                break

        return prioritized

    @staticmethod
    def _chunk_list(items: List[str], size: int) -> List[List[str]]:
        return [items[i : i + size] for i in range(0, len(items), size)]

    def connect_market_data_multi(
        self,
        instrument_keys: List[str],
        mode: str = "ltpc",
        max_sockets: int = MAX_SOCKETS,
        on_message: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> List["FeedService"]:
        if mode == "option_chain":
            mode = "option_greeks"

        limit = (
            self.MAX_SYMBOLS_FULL_D30_GLOBAL
            if mode == "full_d30"
            else self.MAX_SYMBOLS_PER_SOCKET
        )
        if mode == "full_d30" and len(instrument_keys) > limit:
            raise ValueError(
                f"full_d30 is limited to {limit} symbols per user"
            )
        chunks = self._chunk_list(instrument_keys, limit)
        if len(chunks) > max_sockets:
            raise ValueError(
                f"Too many symbols for {max_sockets} sockets: {len(chunks)} required"
            )

        services: List[FeedService] = []
        for chunk in chunks:
            service = FeedService(base_url=self.base_url)
            if on_message:
                service.on_message(on_message)
            if on_error:
                service.on_error(on_error)

            if not service.connect_market_data():
                raise ValueError("Failed to connect market data socket")
            service.subscribe(chunk, mode=mode)
            services.append(service)

        return services

    def _on_open(self, ws):
        self.connected = True
        logger.info("✅ WebSocket connected")

    def _on_message(self, ws, message):
        parsed: Dict[str, Any]

        if isinstance(message, bytes):
            parsed = self._decode_protobuf(message)
        else:
            try:
                parsed = json.loads(message)
            except Exception:
                parsed = {"raw": message}

        if self._on_message_callback:
            self._on_message_callback(parsed)

    def _decode_protobuf(self, message: bytes) -> Dict[str, Any]:
        if self._feed_type != "market-data":
            return {"raw_bytes": message}

        self._ensure_proto_compiled()
        feed = self._proto_module.FeedResponse()
        feed.ParseFromString(message)
        return MessageToDict(feed, preserving_proto_field_name=True)

    def _on_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")
        if self._on_error_callback:
            self._on_error_callback(error)

    def _on_close(self, ws, close_status_code, close_msg):
        self.connected = False
        logger.warning(f"WebSocket closed: {close_status_code} {close_msg}")

        if self._reconnect_attempts < self._max_reconnect_attempts:
            self._reconnect_attempts += 1
            wait_time = min(60, 2 ** self._reconnect_attempts)
            time.sleep(wait_time)
            if self._feed_type:
                self.connect(self._feed_type)
