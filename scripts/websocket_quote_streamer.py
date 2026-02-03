#!/usr/bin/env python3
"""
Websocket Real-time Quote Streamer for Upstox

Streams live tick-by-tick market data for stocks and options.
Supports subscribing to multiple symbols, auto-reconnect, and persistent storage.

Features:
  - Real-time quote streaming via websocket
  - Subscribe/unsubscribe to multiple symbols
  - Auto-reconnect on connection loss
  - Persistent tick database storage
  - Live price display with bid-ask spread
  - Market depth Level 1 data
  - Volume and time tracking

Usage:
  # Start streaming for symbols
  python scripts/websocket_quote_streamer.py --symbols NIFTY,BANKNIFTY,INFY --duration 300

  # Start with callback handler
  python scripts/websocket_quote_streamer.py --symbols NIFTY --duration 60

  # View streaming stats
  python scripts/websocket_quote_streamer.py --stats

  # Query tick history
  python scripts/websocket_quote_streamer.py --query-ticks NIFTY --limit 10

  # Live price display mode
  python scripts/websocket_quote_streamer.py --symbols NIFTY,INFY --live-display --duration 120
"""

import argparse
import asyncio
import json
import sqlite3
import sys
import time
from datetime import datetime
from typing import Optional, Callable, Dict, List
import websocket
import threading


class WebsocketQuoteStreamer:
    """
    Manages websocket connection to Upstox for real-time quotes.
    Handles subscription, reconnection, and data persistence.
    """

    def __init__(self, access_token: str, db_path: str = "market_data.db"):
        """
        Initialize websocket quote streamer.

        Args:
            access_token: Upstox API access token
            db_path: Path to SQLite database for storing ticks
        """
        self.access_token = access_token
        self.db_path = db_path
        self.ws = None
        self.connected = False
        self.subscribed_symbols = set()
        self.callbacks: Dict[str, List[Callable]] = {}
        self.current_quotes: Dict[str, Dict] = {}
        self.tick_count = 0
        self.start_time = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5  # seconds

        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for storing ticks."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Create ticks table if not exists
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS quote_ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT NOT NULL,
                ltp REAL,
                bid_price REAL,
                bid_qty INTEGER,
                ask_price REAL,
                ask_qty INTEGER,
                volume INTEGER,
                open_interest INTEGER,
                day_high REAL,
                day_low REAL,
                oi INTEGER,
                iv REAL,
                exchange TEXT,
                UNIQUE(timestamp, symbol)
            )
        """
        )

        # Create index for faster queries
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_symbol_timestamp ON quote_ticks(symbol, timestamp)"
        )

        conn.commit()
        conn.close()

    def connect(self, on_open: Optional[Callable] = None) -> bool:
        """
        Connect to Upstox websocket server.

        Args:
            on_open: Optional callback when connection opens

        Returns:
            True if connection successful, False otherwise
        """
        try:
            websocket_url = "wss://api.upstox.com/v1/feed/stream"

            self.ws = websocket.WebSocketApp(
                websocket_url,
                header=[f"Authorization: Bearer {self.access_token}"],
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
            )

            # Store external callback
            self._external_on_open = on_open

            # Run websocket in separate thread
            self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
            self.ws_thread.start()

            # Wait for connection
            for _ in range(10):
                if self.connected:
                    self.reconnect_attempts = 0
                    return True
                time.sleep(0.5)

            return False

        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

    def _on_open(self, ws):
        """Handle websocket open event."""
        self.connected = True
        self.start_time = datetime.now()
        print(
            f"✅ Websocket connected at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    def _on_message(self, ws, message):
        """Handle incoming websocket messages (quotes)."""
        try:
            data = json.loads(message)

            if "ltp" in data:
                symbol = data.get("symbol", "UNKNOWN")
                self.current_quotes[symbol] = data

                # Store in database
                self._store_tick(data)

                # Trigger callbacks
                self._trigger_callbacks(symbol, data)

                self.tick_count += 1

        except json.JSONDecodeError:
            print(f"⚠️  Invalid JSON: {message[:100]}")
        except Exception as e:
            print(f"⚠️  Message processing error: {e}")

    def _on_error(self, ws, error):
        """Handle websocket error."""
        print(f"❌ Websocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle websocket close."""
        self.connected = False
        print(f"⚠️  Websocket closed (code: {close_status_code}, msg: {close_msg})")

        # Attempt reconnect
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            wait_time = self.reconnect_delay * self.reconnect_attempts
            print(
                f"🔄 Attempting reconnect #{self.reconnect_attempts} in {wait_time}s..."
            )
            time.sleep(wait_time)
            self.connect()

    def subscribe(self, symbols: List[str]) -> bool:
        """
        Subscribe to symbols for real-time quotes.

        Args:
            symbols: List of symbol strings (e.g., ['NIFTY', 'BANKNIFTY', 'INFY'])

        Returns:
            True if subscription successful
        """
        if not self.connected:
            print("❌ Not connected to websocket")
            return False

        try:
            for symbol in symbols:
                if symbol not in self.subscribed_symbols:
                    subscribe_msg = {
                        "guid": "clientId-1",
                        "method": "sub",
                        "data": {
                            "mode": "LTP",  # LTP = Last Traded Price
                            "tokenized": False,
                        },
                    }

                    # For Upstox, send subscription request
                    self.ws.send(json.dumps(subscribe_msg))
                    self.subscribed_symbols.add(symbol)
                    print(f"📌 Subscribed to {symbol}")

            return True

        except Exception as e:
            print(f"❌ Subscription error: {e}")
            return False

    def unsubscribe(self, symbols: List[str]) -> bool:
        """
        Unsubscribe from symbols.

        Args:
            symbols: List of symbol strings

        Returns:
            True if unsubscription successful
        """
        if not self.connected:
            print("❌ Not connected to websocket")
            return False

        try:
            for symbol in symbols:
                if symbol in self.subscribed_symbols:
                    unsubscribe_msg = {
                        "guid": "clientId-1",
                        "method": "unsub",
                        "data": {"mode": "LTP"},
                    }

                    self.ws.send(json.dumps(unsubscribe_msg))
                    self.subscribed_symbols.discard(symbol)
                    print(f"📌 Unsubscribed from {symbol}")

            return True

        except Exception as e:
            print(f"❌ Unsubscription error: {e}")
            return False

    def on_quote(self, symbol: str, callback: Callable):
        """
        Register callback for quote updates.

        Args:
            symbol: Symbol to listen for
            callback: Function to call with quote data
        """
        if symbol not in self.callbacks:
            self.callbacks[symbol] = []
        self.callbacks[symbol].append(callback)
        print(f"✅ Registered callback for {symbol}")

    def _trigger_callbacks(self, symbol: str, data: Dict):
        """Trigger registered callbacks for symbol."""
        if symbol in self.callbacks:
            for callback in self.callbacks[symbol]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"⚠️  Callback error: {e}")

    def _store_tick(self, data: Dict):
        """Store tick data in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute(
                """
                INSERT OR REPLACE INTO quote_ticks
                (timestamp, symbol, ltp, bid_price, bid_qty, ask_price, ask_qty, 
                 volume, oi, day_high, day_low, exchange)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    datetime.now(),
                    data.get("symbol"),
                    data.get("ltp"),
                    data.get("bid_price"),
                    data.get("bid_qty"),
                    data.get("ask_price"),
                    data.get("ask_qty"),
                    data.get("volume"),
                    data.get("oi"),
                    data.get("day_high"),
                    data.get("day_low"),
                    data.get("exchange"),
                ),
            )

            conn.commit()
            conn.close()

        except sqlite3.IntegrityError:
            # Duplicate, skip
            pass
        except Exception as e:
            print(f"⚠️  Database store error: {e}")

    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get latest quote for symbol."""
        return self.current_quotes.get(symbol)

    def get_all_quotes(self) -> Dict:
        """Get all current quotes."""
        return self.current_quotes.copy()

    def get_bid_ask_spread(self, symbol: str) -> Optional[Dict]:
        """Get bid-ask spread for symbol."""
        quote = self.get_quote(symbol)
        if not quote:
            return None

        bid = quote.get("bid_price", 0)
        ask = quote.get("ask_price", 0)
        ltp = quote.get("ltp", 0)

        spread = ask - bid if ask and bid else 0
        spread_pct = (spread / ltp * 100) if ltp else 0

        return {
            "symbol": symbol,
            "bid": bid,
            "bid_qty": quote.get("bid_qty"),
            "ask": ask,
            "ask_qty": quote.get("ask_qty"),
            "ltp": ltp,
            "spread": spread,
            "spread_pct": spread_pct,
        }

    def get_tick_history(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get historical ticks for symbol."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            c.execute(
                """
                SELECT * FROM quote_ticks
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (symbol, limit),
            )

            ticks = [dict(row) for row in c.fetchall()]
            conn.close()
            return ticks

        except Exception as e:
            print(f"❌ Error getting tick history: {e}")
            return []

    def get_stats(self) -> Dict:
        """Get streaming stats."""
        uptime = (
            (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        )

        return {
            "connected": self.connected,
            "subscribed_symbols": len(self.subscribed_symbols),
            "symbols": list(self.subscribed_symbols),
            "total_ticks": self.tick_count,
            "uptime_seconds": uptime,
            "current_quotes": len(self.current_quotes),
            "reconnect_attempts": self.reconnect_attempts,
        }

    def display_live_quotes(self, refresh_interval: int = 2):
        """Display live quotes in real-time."""
        try:
            while self.connected:
                # Clear screen
                print("\033[2J\033[H")
                print("=" * 80)
                print(f"LIVE QUOTES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 80)

                for symbol in sorted(self.subscribed_symbols):
                    quote = self.get_quote(symbol)
                    spread_info = self.get_bid_ask_spread(symbol)

                    if quote and spread_info:
                        ltp = quote.get("ltp", 0)
                        vol = quote.get("volume", 0)
                        open_interest = quote.get("oi", 0)
                        spread_pct = spread_info.get("spread_pct", 0)

                        print(
                            f"{symbol:12} | LTP: {ltp:10.2f} | Bid: {spread_info['bid']:8.2f} "
                            f"| Ask: {spread_info['ask']:8.2f} | Spread: {spread_pct:6.3f}% "
                            f"| Vol: {vol:8d} | OI: {open_interest:8d}"
                        )

                print("=" * 80)
                print(
                    f"Ticks received: {self.tick_count} | Uptime: {self.get_stats()['uptime_seconds']:.0f}s"
                )

                time.sleep(refresh_interval)

        except KeyboardInterrupt:
            print("\n📴 Live display stopped")

    def disconnect(self):
        """Disconnect websocket."""
        if self.ws:
            self.ws.close()
            self.connected = False
            print("✅ Disconnected from websocket")


def main():
    parser = argparse.ArgumentParser(
        description="Upstox Websocket Quote Streamer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("--symbols", type=str, help="Comma-separated symbols to stream")
    parser.add_argument("--duration", type=int, help="Stream duration in seconds")
    parser.add_argument(
        "--live-display", action="store_true", help="Show live quote display"
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show streaming statistics"
    )
    parser.add_argument("--query-ticks", type=str, help="Query tick history for symbol")
    parser.add_argument("--limit", type=int, default=10, help="Limit for tick history")
    parser.add_argument("--token", type=str, help="Upstox access token")

    args = parser.parse_args()

    # Get token from args or environment
    token = args.token or os.getenv("UPSTOX_ACCESS_TOKEN")
    if not token:
        print("❌ Access token required. Set UPSTOX_ACCESS_TOKEN or use --token")
        sys.exit(1)

    streamer = WebsocketQuoteStreamer(token)

    if args.stats:
        # Show stats only (query database)
        print("\n📊 WEBSOCKET QUOTE STREAMING STATISTICS")
        print("=" * 60)
        stats = streamer.get_stats()
        print(f"Connected: {stats['connected']}")
        print(f"Subscribed symbols: {stats['subscribed_symbols']}")
        print(f"Total ticks stored: {stats['total_ticks']}")
        print(f"Uptime: {stats['uptime_seconds']:.0f}s")
        print("=" * 60)

    elif args.query_ticks:
        # Query tick history
        print(f"\n📊 TICK HISTORY FOR {args.query_ticks}")
        print("=" * 80)

        ticks = streamer.get_tick_history(args.query_ticks, args.limit)
        if ticks:
            for tick in ticks:
                print(
                    f"{tick['timestamp']} | LTP: {tick['ltp']:.2f} | Bid: {tick['bid_price']:.2f} "
                    f"| Ask: {tick['ask_price']:.2f} | Vol: {tick['volume']}"
                )
        else:
            print("No ticks found")

    elif args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",")]
        print(f"\n✅ Connecting to Upstox websocket...")

        if streamer.connect():
            print(f"✅ Connected!")
            streamer.subscribe(symbols)

            if args.live_display:
                try:
                    streamer.display_live_quotes()
                except KeyboardInterrupt:
                    print("\n📴 Stopped")
            else:
                # Stream for specified duration
                duration = args.duration or 60
                print(f"📡 Streaming for {duration} seconds...")

                start = time.time()
                try:
                    while time.time() - start < duration:
                        if streamer.connected:
                            quotes = streamer.get_all_quotes()
                            if quotes:
                                print(
                                    f"📊 {len(quotes)} quotes received | Total ticks: {streamer.tick_count}"
                                )
                        time.sleep(2)
                except KeyboardInterrupt:
                    print("\n📴 Stopped")

            streamer.disconnect()
        else:
            print("❌ Failed to connect")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    import os

    main()
