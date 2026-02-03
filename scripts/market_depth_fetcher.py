#!/usr/bin/env python3
"""
Market Depth and Order Book Fetcher for Upstox

Get real-time market depth data including bid-ask spread and order book levels.
Analyze liquidity, volume profile, and market structure.

Features:
  - Level 1: Bid/Ask with top volumes
  - Level 2: Multiple bid/ask levels (5-10 levels deep)
  - Bid-ask spread analysis
  - Volume at each level
  - Market depth visualization
  - Liquidity analysis
  - Order book snapshots
  - Spread history tracking

Usage:
  # Get Level 1 market depth
  python scripts/market_depth_fetcher.py --symbol INFY --level 1

  # Get Level 2 market depth (10 levels)
  python scripts/market_depth_fetcher.py --symbol NIFTY --level 2

  # Get bid-ask spread
  python scripts/market_depth_fetcher.py --symbol BANKNIFTY --spread

  # Compare spreads across symbols
  python scripts/market_depth_fetcher.py --symbols NIFTY,BANKNIFTY,INFY --compare-spread

  # Analyze liquidity
  python scripts/market_depth_fetcher.py --symbol INFY --analyze-liquidity

  # Display depth visualization
  python scripts/market_depth_fetcher.py --symbol NIFTY --visualize

  # Monitor market depth changes
  python scripts/market_depth_fetcher.py --symbol INFY --monitor --interval 5 --duration 300
"""

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from typing import Optional, Dict, List
import requests


class MarketDepthFetcher:
    """Fetches and analyzes market depth data from Upstox."""

    def __init__(self, access_token: str, db_path: str = "market_data.db"):
        """
        Initialize Market Depth Fetcher.

        Args:
            access_token: Upstox API access token
            db_path: Path to SQLite database
        """
        self.access_token = access_token
        self.db_path = db_path
        self.base_url = "https://api.upstox.com/v2"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        self._init_database()

    def _init_database(self):
        """Initialize database for market depth data."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS market_depth (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT NOT NULL,
                level INTEGER,
                bid_price REAL,
                bid_qty INTEGER,
                ask_price REAL,
                ask_qty INTEGER,
                bid_volume REAL,
                ask_volume REAL,
                spread REAL,
                spread_pct REAL,
                market_type TEXT,
                UNIQUE(timestamp, symbol, level)
            )
        """
        )

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS spread_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT NOT NULL,
                bid_price REAL,
                ask_price REAL,
                spread REAL,
                spread_pct REAL,
                mid_price REAL,
                top_bid_qty INTEGER,
                top_ask_qty INTEGER,
                UNIQUE(timestamp, symbol)
            )
        """
        )

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS order_book (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT NOT NULL,
                side TEXT,
                price REAL,
                quantity INTEGER,
                level INTEGER
            )
        """
        )

        conn.commit()
        conn.close()

    def get_market_depth(self, symbol: str) -> Optional[Dict]:
        """
        Get market depth for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Market depth data or None
        """
        try:
            url = f"{self.base_url}/market-quote/depth"
            params = {"mode": "FULL", "exchange_tokens": symbol}

            response = requests.get(
                url, params=params, headers=self.headers, timeout=10
            )

            if response.status_code == 200:
                data = response.json().get("data", {})

                if symbol in data:
                    depth = data[symbol].get("depth", {})

                    # Store in database
                    self._store_depth(symbol, depth)

                    print(f"✅ Market depth retrieved for {symbol}")
                    return depth
                else:
                    print(f"❌ No depth data for {symbol}")
                    return None
            else:
                print(f"❌ Failed to get market depth: {response.json().get('message')}")
                return None

        except Exception as e:
            print(f"❌ Error getting market depth: {e}")
            return None

    def get_bid_ask(self, symbol: str) -> Optional[Dict]:
        """
        Get bid-ask information for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Bid-ask details or None
        """
        try:
            url = f"{self.base_url}/market-quote/ltp"
            params = {"mode": "FULL", "exchange_tokens": symbol}

            response = requests.get(
                url, params=params, headers=self.headers, timeout=10
            )

            if response.status_code == 200:
                data = response.json().get("data", {})

                if symbol in data:
                    quote = data[symbol]

                    # Extract bid-ask
                    bid_price = quote.get("bids", [{}])[0].get("price", 0)
                    bid_qty = quote.get("bids", [{}])[0].get("quantity", 0)
                    ask_price = quote.get("asks", [{}])[0].get("price", 0)
                    ask_qty = quote.get("asks", [{}])[0].get("quantity", 0)
                    ltp = quote.get("ltp", 0)

                    # Calculate spread
                    spread = ask_price - bid_price
                    spread_pct = (spread / ltp * 100) if ltp else 0

                    bid_ask_data = {
                        "symbol": symbol,
                        "ltp": ltp,
                        "bid_price": bid_price,
                        "bid_qty": bid_qty,
                        "ask_price": ask_price,
                        "ask_qty": ask_qty,
                        "spread": spread,
                        "spread_pct": spread_pct,
                        "mid_price": (bid_price + ask_price) / 2,
                    }

                    # Store spread history
                    self._store_spread(bid_ask_data)

                    return bid_ask_data
                else:
                    print(f"❌ No quote data for {symbol}")
                    return None
            else:
                print(f"❌ Failed to get quote: {response.json().get('message')}")
                return None

        except Exception as e:
            print(f"❌ Error getting bid-ask: {e}")
            return None

    def analyze_liquidity(self, symbol: str) -> Optional[Dict]:
        """
        Analyze liquidity at different price levels.

        Args:
            symbol: Trading symbol

        Returns:
            Liquidity analysis or None
        """
        try:
            depth = self.get_market_depth(symbol)
            bid_ask = self.get_bid_ask(symbol)

            if not depth or not bid_ask:
                return None

            bids = depth.get("bids", [])
            asks = depth.get("asks", [])

            # Calculate cumulative volume
            bid_volumes = [b.get("quantity", 0) for b in bids[:5]]
            ask_volumes = [a.get("quantity", 0) for a in asks[:5]]

            bid_cum_vol = sum(bid_volumes)
            ask_cum_vol = sum(ask_volumes)

            # Analyze order imbalance
            imbalance = (
                (bid_cum_vol - ask_cum_vol) / (bid_cum_vol + ask_cum_vol)
                if (bid_cum_vol + ask_cum_vol) > 0
                else 0
            )

            liquidity_analysis = {
                "symbol": symbol,
                "bid_volume_5_levels": bid_cum_vol,
                "ask_volume_5_levels": ask_cum_vol,
                "total_depth_volume": bid_cum_vol + ask_cum_vol,
                "order_imbalance": imbalance,
                "bid_dominant": "YES" if imbalance > 0.1 else "NO",
                "ask_dominant": "YES" if imbalance < -0.1 else "NO",
                "spread_pct": bid_ask.get("spread_pct", 0),
                "liquidity_score": self._calculate_liquidity_score(
                    bid_cum_vol, ask_cum_vol, bid_ask.get("spread_pct", 0)
                ),
            }

            return liquidity_analysis

        except Exception as e:
            print(f"❌ Error analyzing liquidity: {e}")
            return None

    def _calculate_liquidity_score(
        self, bid_vol: float, ask_vol: float, spread_pct: float
    ) -> float:
        """Calculate liquidity score (0-100)."""
        # Higher volume = higher score
        # Lower spread = higher score
        vol_score = min((bid_vol + ask_vol) / 100000, 1) * 50
        spread_score = max(50 - (spread_pct * 100), 0)

        return vol_score + spread_score

    def _store_depth(self, symbol: str, depth: Dict):
        """Store market depth in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            bids = depth.get("bids", [])
            asks = depth.get("asks", [])

            for level, bid in enumerate(bids[:10], 1):
                bid_price = bid.get("price", 0)
                bid_qty = bid.get("quantity", 0)

                ask = asks[level - 1] if level <= len(asks) else {}
                ask_price = ask.get("price", 0)
                ask_qty = ask.get("quantity", 0)

                spread = ask_price - bid_price if ask_price and bid_price else 0

                c.execute(
                    """
                    INSERT OR REPLACE INTO market_depth
                    (timestamp, symbol, level, bid_price, bid_qty, ask_price, ask_qty, spread)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        datetime.now(),
                        symbol,
                        level,
                        bid_price,
                        bid_qty,
                        ask_price,
                        ask_qty,
                        spread,
                    ),
                )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"⚠️  Error storing depth: {e}")

    def _store_spread(self, bid_ask_data: Dict):
        """Store spread history."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            c.execute(
                """
                INSERT INTO spread_history
                (symbol, bid_price, ask_price, spread, spread_pct, mid_price, 
                 top_bid_qty, top_ask_qty)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    bid_ask_data.get("symbol"),
                    bid_ask_data.get("bid_price"),
                    bid_ask_data.get("ask_price"),
                    bid_ask_data.get("spread"),
                    bid_ask_data.get("spread_pct"),
                    bid_ask_data.get("mid_price"),
                    bid_ask_data.get("bid_qty"),
                    bid_ask_data.get("ask_qty"),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"⚠️  Error storing spread: {e}")

    def get_spread_history(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Get spread history for symbol."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            c.execute(
                """
                SELECT * FROM spread_history
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (symbol, limit),
            )

            history = [dict(row) for row in c.fetchall()]
            conn.close()
            return history

        except Exception as e:
            print(f"❌ Error getting spread history: {e}")
            return []

    def display_market_depth(self, symbol: str, depth: Dict):
        """Display market depth in formatted view."""
        print("\n" + "=" * 100)
        print(f"MARKET DEPTH - {symbol}")
        print("=" * 100)

        bids = depth.get("bids", [])[:10]
        asks = depth.get("asks", [])[:10]

        print(f"\n{'BID SIDE':^45} | {'ASK SIDE':^45}")
        print(
            f"{'Price':>10} {'Qty':>10} {'Vol':>20} | {'Vol':>20} {'Qty':>10} {'Price':>10}"
        )
        print("-" * 100)

        for level in range(max(len(bids), len(asks))):
            bid = bids[level] if level < len(bids) else {}
            ask = asks[level] if level < len(asks) else {}

            bid_price = bid.get("price", "")
            bid_qty = bid.get("quantity", "")
            ask_price = ask.get("price", "")
            ask_qty = ask.get("quantity", "")

            print(
                f"{float(bid_price) if bid_price else 0:>10.2f} "
                f"{int(bid_qty) if bid_qty else 0:>10} "
                f"{'':>20} | {'':>20} "
                f"{int(ask_qty) if ask_qty else 0:>10} "
                f"{float(ask_price) if ask_price else 0:>10.2f}"
            )

        print("=" * 100)

    def display_bid_ask(self, bid_ask: Dict):
        """Display bid-ask information."""
        print("\n" + "=" * 80)
        print(f"BID-ASK SPREAD - {bid_ask.get('symbol')}")
        print("=" * 80)

        print(f"\nLast Traded Price (LTP): {bid_ask.get('ltp', 0):12.2f}")
        print(f"Mid Price:               {bid_ask.get('mid_price', 0):12.2f}")

        print(f"\n{'BID SIDE':20} | {'ASK SIDE':20}")
        print(
            f"  Price: {bid_ask.get('bid_price', 0):12.2f} |   Price: {bid_ask.get('ask_price', 0):12.2f}"
        )
        print(
            f"  Qty:   {bid_ask.get('bid_qty', 0):12} |   Qty:   {bid_ask.get('ask_qty', 0):12}"
        )

        print(f"\n📊 SPREAD ANALYSIS:")
        print(f"  Absolute Spread: {bid_ask.get('spread', 0):12.2f}")
        print(f"  Spread %:        {bid_ask.get('spread_pct', 0):12.3f}%")

        print("=" * 80)

    def display_liquidity(self, analysis: Dict):
        """Display liquidity analysis."""
        print("\n" + "=" * 80)
        print(f"LIQUIDITY ANALYSIS - {analysis.get('symbol')}")
        print("=" * 80)

        print(f"\n📊 VOLUME AT 5 LEVELS:")
        print(f"  Bid Volume:      {analysis.get('bid_volume_5_levels', 0):15,.0f}")
        print(f"  Ask Volume:      {analysis.get('ask_volume_5_levels', 0):15,.0f}")
        print(f"  Total Depth Vol: {analysis.get('total_depth_volume', 0):15,.0f}")

        print(f"\n📈 ORDER IMBALANCE:")
        imbalance = analysis.get("order_imbalance", 0)
        print(f"  Imbalance Ratio: {imbalance:15.3f}")
        print(
            f"  Direction:       {'BID DOMINANT' if imbalance > 0.1 else 'ASK DOMINANT' if imbalance < -0.1 else 'BALANCED'}"
        )

        print(f"\n💧 LIQUIDITY SCORE:")
        score = analysis.get("liquidity_score", 0)
        print(f"  Score:           {score:15.1f}/100")

        if score > 75:
            print("  Rating:          🟢 Excellent")
        elif score > 50:
            print("  Rating:          🟡 Good")
        elif score > 25:
            print("  Rating:          🟠 Fair")
        else:
            print("  Rating:          🔴 Poor")

        print("=" * 80)

    def monitor_depth(self, symbol: str, interval: int = 5, duration: int = 300):
        """Monitor market depth changes."""
        print(
            f"📡 Monitoring {symbol} (interval: {interval}s, duration: {duration}s)..."
        )
        print("=" * 80)

        start_time = time.time()

        while time.time() - start_time < duration:
            try:
                bid_ask = self.get_bid_ask(symbol)

                if bid_ask:
                    spread_pct = bid_ask.get("spread_pct", 0)
                    bid = bid_ask.get("bid_price", 0)
                    ask = bid_ask.get("ask_price", 0)

                    print(
                        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                        f"Bid: {bid:8.2f} | Ask: {ask:8.2f} | "
                        f"Spread: {spread_pct:6.3f}%"
                    )

                time.sleep(interval)

            except KeyboardInterrupt:
                print("\n✅ Monitoring stopped")
                break
            except Exception as e:
                print(f"⚠️  Error: {e}")
                time.sleep(interval)

    def compare_spreads(self, symbols: List[str]) -> List[Dict]:
        """Compare spreads across multiple symbols."""
        spreads = []

        for symbol in symbols:
            bid_ask = self.get_bid_ask(symbol)
            if bid_ask:
                spreads.append(bid_ask)

        return spreads


def main():
    parser = argparse.ArgumentParser(
        description="Upstox Market Depth and Order Book Fetcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("--token", type=str, help="Upstox access token")
    parser.add_argument("--symbol", type=str, help="Trading symbol")
    parser.add_argument("--symbols", type=str, help="Comma-separated symbols")
    parser.add_argument(
        "--action",
        type=str,
        choices=[
            "depth",
            "spread",
            "liquidity",
            "history",
            "compare",
            "monitor",
            "visualize",
        ],
        default="spread",
        help="Action to perform",
    )
    parser.add_argument(
        "--level", type=int, choices=[1, 2], default=1, help="Depth level"
    )
    parser.add_argument(
        "--interval", type=int, default=5, help="Monitor interval in seconds"
    )
    parser.add_argument(
        "--duration", type=int, default=300, help="Monitor duration in seconds"
    )
    parser.add_argument("--limit", type=int, default=50, help="History limit")

    args = parser.parse_args()

    token = args.token or os.getenv("UPSTOX_ACCESS_TOKEN")
    if not token:
        print("❌ Access token required. Set UPSTOX_ACCESS_TOKEN or use --token")
        sys.exit(1)

    fetcher = MarketDepthFetcher(token)

    if args.action == "depth":
        if not args.symbol:
            print("❌ --symbol required for depth action")
            sys.exit(1)

        depth = fetcher.get_market_depth(args.symbol)
        if depth:
            fetcher.display_market_depth(args.symbol, depth)

    elif args.action == "spread":
        if not args.symbol:
            print("❌ --symbol required for spread action")
            sys.exit(1)

        bid_ask = fetcher.get_bid_ask(args.symbol)
        if bid_ask:
            fetcher.display_bid_ask(bid_ask)

    elif args.action == "liquidity":
        if not args.symbol:
            print("❌ --symbol required for liquidity action")
            sys.exit(1)

        analysis = fetcher.analyze_liquidity(args.symbol)
        if analysis:
            fetcher.display_liquidity(analysis)

    elif args.action == "history":
        if not args.symbol:
            print("❌ --symbol required for history action")
            sys.exit(1)

        history = fetcher.get_spread_history(args.symbol, args.limit)
        if history:
            print(f"\n📊 SPREAD HISTORY FOR {args.symbol} ({len(history)} records)")
            print("=" * 100)
            for h in history:
                print(
                    f"{h['timestamp']} | Bid: {h['bid_price']:8.2f} | Ask: {h['ask_price']:8.2f} | "
                    f"Spread: {h['spread_pct']:6.3f}%"
                )

    elif args.action == "compare":
        if not args.symbols:
            print("❌ --symbols required for compare action (comma-separated)")
            sys.exit(1)

        symbols = [s.strip() for s in args.symbols.split(",")]
        spreads = fetcher.compare_spreads(symbols)

        if spreads:
            print(f"\n📊 SPREAD COMPARISON")
            print("=" * 100)
            print(
                f"{'Symbol':10} | {'Bid':10} | {'Ask':10} | {'Spread':10} | {'Spread %':10}"
            )
            print("=" * 100)
            for spread in spreads:
                print(
                    f"{spread['symbol']:10} | "
                    f"{spread['bid_price']:10.2f} | "
                    f"{spread['ask_price']:10.2f} | "
                    f"{spread['spread']:10.2f} | "
                    f"{spread['spread_pct']:10.3f}%"
                )

    elif args.action == "monitor":
        if not args.symbol:
            print("❌ --symbol required for monitor action")
            sys.exit(1)

        fetcher.monitor_depth(args.symbol, args.interval, args.duration)


if __name__ == "__main__":
    main()
