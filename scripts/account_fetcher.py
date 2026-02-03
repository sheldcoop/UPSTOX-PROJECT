#!/usr/bin/env python3
"""
Account and Margin Information Fetcher for Upstox

Get account details, margin info, buying power, and balance.
Real-time account monitoring with persistent caching.

Features:
  - Get account profile and details
  - Margin information (available, used, required)
  - Buying power calculation
  - Account balance and cash
  - Equity position values
  - Margin utilization ratio
  - Real-time updates
  - Account alerts (low margin, etc.)

Usage:
  # Get account profile
  python scripts/account_fetcher.py --action profile

  # Get margin details
  python scripts/account_fetcher.py --action margin

  # Get buying power
  python scripts/account_fetcher.py --action buying-power

  # Get full account summary
  python scripts/account_fetcher.py --action summary

  # Get account alerts
  python scripts/account_fetcher.py --action alerts

  # Monitor account real-time
  python scripts/account_fetcher.py --action monitor --interval 30

  # Get account history
  python scripts/account_fetcher.py --action history --limit 100
"""

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from typing import Optional, Dict
import requests


class AccountFetcher:
    """Fetches account and margin information from Upstox."""

    def __init__(self, access_token: str, db_path: str = "market_data.db"):
        """
        Initialize Account Fetcher.

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
        """Initialize database for account info."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS account_info (
                timestamp DATETIME PRIMARY KEY DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                email TEXT,
                client_id TEXT,
                status TEXT,
                day_trading_buying_power REAL,
                equity_buying_power REAL,
                commodity_buying_power REAL,
                collateral_available REAL,
                available_margin REAL,
                used_margin REAL,
                margin_required REAL,
                net_worth REAL,
                cash_balance REAL,
                opening_balance REAL,
                adhoc_margin REAL,
                margin_utilization_pct REAL,
                pnl_today REAL,
                pnl_mtd REAL
            )
        """
        )

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS margin_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                available_margin REAL,
                used_margin REAL,
                margin_utilization_pct REAL,
                buying_power REAL
            )
        """
        )

        conn.commit()
        conn.close()

    def get_profile(self) -> Optional[Dict]:
        """Get user profile information."""
        try:
            url = f"{self.base_url}/user/profile"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json().get("data", {})
                print("✅ Profile retrieved successfully")
                return data
            else:
                print(f"❌ Failed to get profile: {response.json().get('message')}")
                return None

        except Exception as e:
            print(f"❌ Error getting profile: {e}")
            return None

    def get_margin(self) -> Optional[Dict]:
        """Get margin information."""
        try:
            url = f"{self.base_url}/user/get-margin"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json().get("data", {})
                self._store_margin_info(data)
                print("✅ Margin info retrieved successfully")
                return data
            else:
                print(f"❌ Failed to get margin: {response.json().get('message')}")
                return None

        except Exception as e:
            print(f"❌ Error getting margin: {e}")
            return None

    def get_account_details(self) -> Optional[Dict]:
        """Get complete account details including profile and margin."""
        try:
            profile = self.get_profile()
            margin = self.get_margin()

            if profile and margin:
                account_data = {
                    "profile": profile,
                    "margin": margin,
                    "retrieved_at": datetime.now().isoformat(),
                }

                # Calculate buying power
                available_margin = margin.get("available", {}).get("equity_margin", 0)
                buying_power = available_margin * 5  # Typical leverage

                account_data["calculated_buying_power"] = buying_power
                account_data["margin_utilization"] = self._calculate_margin_utilization(
                    margin
                )

                return account_data
            else:
                return None

        except Exception as e:
            print(f"❌ Error getting account details: {e}")
            return None

    def get_buying_power(self) -> Optional[Dict]:
        """Get buying power for different product types."""
        try:
            margin = self.get_margin()

            if not margin:
                return None

            available = margin.get("available", {})
            utilised = margin.get("utilised", {})

            # Calculate buying power
            equity_margin = available.get("equity_margin", 0)
            commodity_margin = available.get("commodity_margin", 0)
            mtf_margin = available.get("mtf_margin", 0)

            buying_power = {
                "equity": {
                    "available": equity_margin,
                    "buying_power": equity_margin * 2,  # Typical intraday leverage
                    "segment": "NSE/BSE",
                },
                "commodity": {
                    "available": commodity_margin,
                    "buying_power": commodity_margin * 5,  # Commodity leverage
                    "segment": "MCX",
                },
                "mtf": {
                    "available": mtf_margin,
                    "buying_power": mtf_margin,
                    "segment": "Margin Trading",
                },
                "total_available": equity_margin + commodity_margin + mtf_margin,
                "total_buying_power": (
                    equity_margin * 2 + commodity_margin * 5 + mtf_margin
                ),
            }

            print("✅ Buying power calculated")
            return buying_power

        except Exception as e:
            print(f"❌ Error getting buying power: {e}")
            return None

    def get_holdings(self) -> Optional[Dict]:
        """Get holdings/portfolio."""
        try:
            url = f"{self.base_url}/portfolio/long-term-holdings"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                holdings = response.json().get("data", {})
                print(f"✅ Holdings retrieved ({len(holdings)} positions)")
                return holdings
            else:
                print(f"❌ Failed to get holdings: {response.json().get('message')}")
                return None

        except Exception as e:
            print(f"❌ Error getting holdings: {e}")
            return None

    def _calculate_margin_utilization(self, margin: Dict) -> float:
        """Calculate margin utilization percentage."""
        try:
            available = margin.get("available", {}).get("equity_margin", 0)
            utilised = margin.get("utilised", {}).get("equity_margin", 0)

            total = available + utilised

            if total > 0:
                return (utilised / total) * 100
            else:
                return 0.0

        except Exception:
            return 0.0

    def _store_margin_info(self, margin: Dict):
        """Store margin info in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            available = margin.get("available", {}).get("equity_margin", 0)
            utilised = margin.get("utilised", {}).get("equity_margin", 0)
            margin_util = self._calculate_margin_utilization(margin)

            c.execute(
                """
                INSERT INTO margin_history
                (available_margin, used_margin, margin_utilization_pct, buying_power)
                VALUES (?, ?, ?, ?)
            """,
                (available, utilised, margin_util, available * 2),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"⚠️  Error storing margin: {e}")

    def get_margin_history(self, limit: int = 100) -> list:
        """Get margin history."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            c.execute(
                """
                SELECT * FROM margin_history
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (limit,),
            )

            history = [dict(row) for row in c.fetchall()]
            conn.close()
            return history

        except Exception as e:
            print(f"❌ Error getting margin history: {e}")
            return []

    def display_margin_details(self, margin: Dict):
        """Display margin details in formatted view."""
        print("\n" + "=" * 80)
        print("MARGIN DETAILS")
        print("=" * 80)

        available = margin.get("available", {})
        utilised = margin.get("utilised", {})

        print("\n📊 AVAILABLE MARGIN:")
        print(f"  Equity:          {available.get('equity_margin', 0):15,.2f}")
        print(f"  Commodity:       {available.get('commodity_margin', 0):15,.2f}")
        print(f"  MTF:             {available.get('mtf_margin', 0):15,.2f}")
        print(
            f"  Total:           {available.get('equity_margin', 0) + available.get('commodity_margin', 0) + available.get('mtf_margin', 0):15,.2f}"
        )

        print("\n📊 UTILISED MARGIN:")
        print(f"  Equity:          {utilised.get('equity_margin', 0):15,.2f}")
        print(f"  Commodity:       {utilised.get('commodity_margin', 0):15,.2f}")
        print(f"  MTF:             {utilised.get('mtf_margin', 0):15,.2f}")
        print(
            f"  Total:           {utilised.get('equity_margin', 0) + utilised.get('commodity_margin', 0) + utilised.get('mtf_margin', 0):15,.2f}"
        )

        util_pct = self._calculate_margin_utilization(margin)
        print(f"\n📈 Margin Utilization: {util_pct:6.2f}%")

        if util_pct > 80:
            print("⚠️  HIGH MARGIN UTILIZATION - Low on margin!")
        elif util_pct > 90:
            print("🚨 CRITICAL MARGIN - Risk of liquidation!")

        print("=" * 80)

    def display_buying_power(self, buying_power: Dict):
        """Display buying power details."""
        print("\n" + "=" * 80)
        print("BUYING POWER")
        print("=" * 80)

        print("\n💰 EQUITY SEGMENT (NSE/BSE):")
        print(f"  Available Margin:  {buying_power['equity']['available']:15,.2f}")
        print(f"  Buying Power (2x): {buying_power['equity']['buying_power']:15,.2f}")

        print("\n💰 COMMODITY SEGMENT (MCX):")
        print(f"  Available Margin:  {buying_power['commodity']['available']:15,.2f}")
        print(
            f"  Buying Power (5x): {buying_power['commodity']['buying_power']:15,.2f}"
        )

        print("\n💰 MARGIN TRADING (MTF):")
        print(f"  Available Margin:  {buying_power['mtf']['available']:15,.2f}")
        print(f"  Buying Power (1x): {buying_power['mtf']['buying_power']:15,.2f}")

        print("\n💰 TOTAL:")
        print(f"  Total Available:   {buying_power['total_available']:15,.2f}")
        print(f"  Total Buying Power: {buying_power['total_buying_power']:15,.2f}")

        print("=" * 80)

    def display_profile(self, profile: Dict):
        """Display profile information."""
        print("\n" + "=" * 80)
        print("ACCOUNT PROFILE")
        print("=" * 80)

        print(f"\nUser ID:           {profile.get('user_id', 'N/A')}")
        print(f"Email:             {profile.get('email', 'N/A')}")
        print(f"Client ID:         {profile.get('client_id', 'N/A')}")
        print(f"Status:            {profile.get('status', 'N/A')}")
        print(f"Account Type:      {profile.get('account_type', 'N/A')}")

        print("=" * 80)

    def monitor_account(self, interval: int = 30, duration: int = 3600):
        """Monitor account in real-time."""
        print(
            f"📡 Starting account monitoring (interval: {interval}s, duration: {duration}s)..."
        )

        start_time = time.time()

        while time.time() - start_time < duration:
            try:
                print(
                    f"\n📊 Account update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )

                margin = self.get_margin()
                if margin:
                    self._store_margin_info(margin)
                    available = margin.get("available", {}).get("equity_margin", 0)
                    utilised = margin.get("utilised", {}).get("equity_margin", 0)
                    util_pct = self._calculate_margin_utilization(margin)

                    print(
                        f"  Available: ₹{available:12,.0f} | Used: ₹{utilised:12,.0f} | "
                        f"Util: {util_pct:6.2f}%"
                    )

                time.sleep(interval)

            except KeyboardInterrupt:
                print("\n✅ Monitoring stopped")
                break
            except Exception as e:
                print(f"⚠️  Error: {e}")
                time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(
        description="Upstox Account and Margin Fetcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("--token", type=str, help="Upstox access token")
    parser.add_argument(
        "--action",
        type=str,
        required=True,
        choices=[
            "profile",
            "margin",
            "buying-power",
            "summary",
            "holdings",
            "history",
            "monitor",
        ],
        help="Action to perform",
    )
    parser.add_argument(
        "--interval", type=int, default=30, help="Monitor interval in seconds"
    )
    parser.add_argument(
        "--duration", type=int, default=3600, help="Monitor duration in seconds"
    )
    parser.add_argument("--limit", type=int, default=100, help="History limit")

    args = parser.parse_args()

    token = args.token or os.getenv("UPSTOX_ACCESS_TOKEN")
    if not token:
        print("❌ Access token required. Set UPSTOX_ACCESS_TOKEN or use --token")
        sys.exit(1)

    fetcher = AccountFetcher(token)

    if args.action == "profile":
        profile = fetcher.get_profile()
        if profile:
            fetcher.display_profile(profile)

    elif args.action == "margin":
        margin = fetcher.get_margin()
        if margin:
            fetcher.display_margin_details(margin)

    elif args.action == "buying-power":
        buying_power = fetcher.get_buying_power()
        if buying_power:
            fetcher.display_buying_power(buying_power)

    elif args.action == "summary":
        account = fetcher.get_account_details()
        if account:
            fetcher.display_profile(account["profile"])
            fetcher.display_margin_details(account["margin"])
            print(
                f"\nCalculated Buying Power: ₹{account.get('calculated_buying_power', 0):,.0f}"
            )

    elif args.action == "holdings":
        holdings = fetcher.get_holdings()
        if holdings:
            print(f"\n✅ Holdings: {len(holdings)} positions")

    elif args.action == "history":
        history = fetcher.get_margin_history(args.limit)
        if history:
            print(f"\n📊 MARGIN HISTORY ({len(history)} records)")
            print("=" * 80)
            print(
                f"{'Timestamp':19} | {'Available':15} | {'Used':15} | {'Util %':8} | {'Buying Power':15}"
            )
            print("=" * 80)
            for h in history:
                print(
                    f"{h['timestamp']} | "
                    f"{h['available_margin']:15,.0f} | "
                    f"{h['used_margin']:15,.0f} | "
                    f"{h['margin_utilization_pct']:8.2f} | "
                    f"{h['buying_power']:15,.0f}"
                )

    elif args.action == "monitor":
        fetcher.monitor_account(args.interval, args.duration)


if __name__ == "__main__":
    main()
