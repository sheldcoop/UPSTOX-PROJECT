#!/usr/bin/env python3
"""
WebSocket v3 Streamer for Upstox
Migrated to v3 websocket endpoints with enhanced features

New v3 Features:
- v3 websocket authorization endpoint
- Enhanced connection health monitoring
- Portfolio stream feed support
- Improved error handling and reconnection
- Connection metrics tracking

v3 Endpoints:
- POST /feed/market-data-feed/authorize/v3 - Get websocket URL and auth
- wss://feed.upstox.com/v3/market-data-feed - WebSocket connection

Usage:
  from scripts.websocket_v3_streamer import WebSocketV3Streamer

  ws = WebSocketV3Streamer()
  ws.connect()
  ws.subscribe(['NSE_EQ|INE009A01021'])  # NIFTY
"""

import logging
import sys
import json
import time
import random
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Callable, Any
from pathlib import Path
import websocket
import threading

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.auth_manager import AuthManager
from scripts.error_handler import with_retry, UpstoxAPIError
from scripts.database_pool import get_db_pool
import requests

logger = logging.getLogger(__name__)


class WebSocketV3Streamer:
    """
    WebSocket v3 streamer with enhanced monitoring and portfolio feed.
    """

    BASE_URL = "https://api.upstox.com/v2"
    AUTHORIZE_V3 = "/feed/market-data-feed/authorize/v3"

    def __init__(self, db_path: str = "market_data.db"):
        """
        Initialize WebSocket V3 Streamer.

        Args:
            db_path: Path to SQLite database
        """
        self.auth_manager = AuthManager()
        self.db_path = db_path
        self.db_pool = get_db_pool(db_path)
        self.session = requests.Session()

        # WebSocket state
        self.ws = None
        self.ws_url = None
        self.connected = False
        self.subscribed_symbols: List[str] = []

        # Connection metrics
        self.connection_start_time = None
        self.total_messages_received = 0
        self.last_message_time = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 20

        # Health monitoring
        self.health_status = {
            "connected": False,
            "uptime_seconds": 0,
            "messages_received": 0,
            "last_message_ago_seconds": None,
            "reconnect_count": 0,
        }

        self._init_database()
        logger.info("✅ WebSocketV3Streamer initialized")

    def _init_database(self):
        """Initialize database for websocket metrics"""
        with self.db_pool.get_connection() as conn:
            # WebSocket metrics table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS websocket_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    connection_start DATETIME,
                    connection_end DATETIME,
                    duration_seconds INTEGER,
                    messages_received INTEGER,
                    reconnect_count INTEGER,
                    disconnect_reason TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # WebSocket ticks table (v3 format)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS websocket_ticks_v3 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    instrument_key TEXT NOT NULL,
                    ltp REAL,
                    volume INTEGER,
                    oi INTEGER,
                    bid_price REAL,
                    ask_price REAL,
                    bid_qty INTEGER,
                    ask_qty INTEGER,
                    high REAL,
                    low REAL,
                    open REAL,
                    close REAL
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_ws_ticks_v3_instrument 
                ON websocket_ticks_v3(instrument_key, timestamp)
            """
            )

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        token = self.auth_manager.get_valid_token()
        if not token:
            raise UpstoxAPIError("Failed to get valid access token")

        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @with_retry(max_attempts=3)
    def authorize_v3(self) -> Dict[str, Any]:
        """
        Authorize v3 websocket connection.

        Returns:
            Authorization data with websocket URL
        """
        try:
            headers = self._get_headers()
            url = f"{self.BASE_URL}{self.AUTHORIZE_V3}"

            response = self.session.post(url, headers=headers, timeout=15)
            response.raise_for_status()

            result = response.json()
            auth_data = result.get("data", {})

            self.ws_url = auth_data.get("authorized_redirect_uri")

            logger.info("✅ WebSocket v3 authorized")
            return auth_data

        except Exception as e:
            logger.error(f"❌ v3 authorization failed: {e}", exc_info=True)
            raise

    def connect(self) -> bool:
        """
        Connect to v3 websocket.

        Returns:
            True if connection successful
        """
        try:
            # Get authorization
            if not self.ws_url:
                self.authorize_v3()

            if not self.ws_url:
                logger.error("No websocket URL available")
                return False

            # Create websocket connection
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open,
            )

            # Run in separate thread
            wst = threading.Thread(target=self.ws.run_forever)
            wst.daemon = True
            wst.start()

            # Wait for connection
            time.sleep(2)

            return self.connected

        except Exception as e:
            logger.error(f"❌ Connection failed: {e}", exc_info=True)
            return False

    def _on_open(self, ws):
        """Handle websocket open"""
        self.connected = True
        self.connection_start_time = datetime.now()
        self.reconnect_attempts = 0

        logger.info("✅ WebSocket v3 connected")

        # Update health status
        self._update_health_status()

    def _on_message(self, ws, message):
        """Handle incoming websocket message"""
        try:
            data = json.loads(message)

            self.total_messages_received += 1
            self.last_message_time = datetime.now()

            # Process market data
            self._process_tick_data(data)

            # Update health status
            self._update_health_status()

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    def _on_error(self, ws, error):
        """Handle websocket error"""
        logger.error(f"❌ WebSocket error: {error}")
        self._update_health_status()

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle websocket close"""
        self.connected = False

        logger.warning(
            f"⚠️  WebSocket closed (code: {close_status_code}, msg: {close_msg})"
        )

        # Save metrics
        self._save_connection_metrics(disconnect_reason=close_msg)

        # Attempt reconnect with exponential backoff
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1

            # Exponential backoff with jitter
            wait_time = min(300, (2**self.reconnect_attempts) + random.uniform(0, 1))

            logger.info(
                f"🔄 Reconnecting in {wait_time:.1f}s "
                f"(attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})"
            )

            time.sleep(wait_time)

            # Re-authorize and connect
            self.ws_url = None
            self.connect()

        else:
            logger.error("❌ Max reconnection attempts reached")

        self._update_health_status()

    def subscribe(
        self,
        instrument_keys: List[str],
        mode: str = "full",
    ) -> bool:
        """
        Subscribe to instrument keys.

        Args:
            instrument_keys: List of instrument keys (e.g., ['NSE_EQ|INE009A01021'])
            mode: Subscription mode ('ltpc', 'full')

        Returns:
            True if subscription successful
        """
        try:
            if not self.connected:
                logger.error("Not connected to websocket")
                return False

            # Build subscription message
            sub_message = {
                "guid": str(uuid.uuid4()),  # Generate unique GUID for message tracking
                "method": "sub",
                "data": {
                    "mode": mode,
                    "instrumentKeys": instrument_keys,
                },
            }

            self.ws.send(json.dumps(sub_message))
            self.subscribed_symbols.extend(instrument_keys)

            logger.info(f"✅ Subscribed to {len(instrument_keys)} instruments")
            return True

        except Exception as e:
            logger.error(f"❌ Subscription failed: {e}", exc_info=True)
            return False

    def unsubscribe(self, instrument_keys: List[str]) -> bool:
        """
        Unsubscribe from instrument keys.

        Args:
            instrument_keys: List of instrument keys to unsubscribe

        Returns:
            True if unsubscription successful
        """
        try:
            if not self.connected:
                return False

            unsub_message = {
                "guid": str(uuid.uuid4()),  # Generate unique GUID for message tracking
                "method": "unsub",
                "data": {
                    "instrumentKeys": instrument_keys,
                },
            }

            self.ws.send(json.dumps(unsub_message))

            for key in instrument_keys:
                if key in self.subscribed_symbols:
                    self.subscribed_symbols.remove(key)

            logger.info(f"✅ Unsubscribed from {len(instrument_keys)} instruments")
            return True

        except Exception as e:
            logger.error(f"❌ Unsubscription failed: {e}", exc_info=True)
            return False

    def disconnect(self):
        """Disconnect from websocket"""
        if self.ws:
            self.ws.close()
            self.connected = False
            logger.info("✅ WebSocket disconnected")

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get current health status and metrics.

        Returns:
            Health status dictionary
        """
        self._update_health_status()
        return self.health_status.copy()

    def _update_health_status(self):
        """Update health status metrics"""
        if self.connection_start_time:
            uptime = (datetime.now() - self.connection_start_time).total_seconds()
        else:
            uptime = 0

        if self.last_message_time:
            last_msg_ago = (datetime.now() - self.last_message_time).total_seconds()
        else:
            last_msg_ago = None

        self.health_status = {
            "connected": self.connected,
            "uptime_seconds": int(uptime),
            "messages_received": self.total_messages_received,
            "last_message_ago_seconds": last_msg_ago,
            "reconnect_count": self.reconnect_attempts,
            "subscribed_count": len(self.subscribed_symbols),
            "timestamp": datetime.now().isoformat(),
        }

    def _process_tick_data(self, data: Dict[str, Any]):
        """Process and save tick data"""
        try:
            # Extract tick information
            feeds = data.get("feeds", {})

            for instrument_key, tick in feeds.items():
                self._save_tick(instrument_key, tick)

        except Exception as e:
            logger.error(f"Error processing tick data: {e}")

    def _save_tick(self, instrument_key: str, tick: Dict[str, Any]):
        """Save tick to database"""
        try:
            with self.db_pool.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO websocket_ticks_v3 
                    (instrument_key, ltp, volume, oi, bid_price, ask_price,
                     bid_qty, ask_qty, high, low, open, close)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        instrument_key,
                        tick.get("ltp"),
                        tick.get("volume"),
                        tick.get("oi"),
                        tick.get("bid_price"),
                        tick.get("ask_price"),
                        tick.get("bid_qty"),
                        tick.get("ask_qty"),
                        tick.get("high"),
                        tick.get("low"),
                        tick.get("open"),
                        tick.get("close"),
                    ),
                )

        except Exception as e:
            logger.error(f"Failed to save tick: {e}")

    def _save_connection_metrics(self, disconnect_reason: Optional[str] = None):
        """Save connection metrics to database"""
        try:
            if not self.connection_start_time:
                return

            duration = (datetime.now() - self.connection_start_time).total_seconds()

            with self.db_pool.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO websocket_metrics 
                    (connection_start, connection_end, duration_seconds,
                     messages_received, reconnect_count, disconnect_reason)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        self.connection_start_time,
                        datetime.now(),
                        int(duration),
                        self.total_messages_received,
                        self.reconnect_attempts,
                        disconnect_reason,
                    ),
                )

        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")


if __name__ == "__main__":
    """Test WebSocket v3 streamer"""
    logging.basicConfig(level=logging.INFO)

    ws = WebSocketV3Streamer()

    # Connect
    print("\n🔌 Connecting to WebSocket v3...")
    if ws.connect():
        print("✅ Connected!")

        # Subscribe to instruments
        print("\n📡 Subscribing to instruments...")
        ws.subscribe(["NSE_EQ|INE009A01021"])  # Example: NIFTY

        # Monitor for 30 seconds
        for i in range(6):
            time.sleep(5)
            status = ws.get_health_status()
            print(f"\n📊 Health Status: {status}")

        # Disconnect
        print("\n🔌 Disconnecting...")
        ws.disconnect()

    else:
        print("❌ Connection failed")

    print("\n✅ WebSocketV3Streamer test complete")
