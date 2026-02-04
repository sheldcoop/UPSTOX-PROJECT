#!/usr/bin/env python3
"""
Telegram Alert Bot - Real-time Trading Alerts

Sends trading alerts via Telegram:
- Breaking news alerts
- Corporate announcement reminders
- Economic event notifications
- Price alerts
- Order fill notifications
- Margin alerts
- GTT trigger notifications

Setup:
1. Create bot via @BotFather on Telegram
2. Get bot token
3. Get your chat_id (message bot, run with --get-chat-id)
4. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars

Usage:
    # Get your chat ID
    python telegram_bot.py --get-chat-id

    # Send test alert
    python telegram_bot.py --test

    # Monitor and send alerts
    python telegram_bot.py --monitor --interval 300

    # Send custom message
    python telegram_bot.py --send "Your message here"

Author: Upstox Backend Team
Date: 2026-01-31
"""

import os
import sys
import json
import sqlite3
import requests
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot for trading alerts."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        db_path: str = "market_data.db",
    ):
        """
        Initialize Telegram bot.

        Args:
            bot_token: Telegram bot token
            chat_id: Your Telegram chat ID
            db_path: Database path
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.db_path = db_path

        if not self.bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not set")
            logger.info(
                "Create bot via @BotFather and set: export TELEGRAM_BOT_TOKEN='your_token'"
            )

        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """
        Send message via Telegram.

        Args:
            text: Message text
            parse_mode: Markdown or HTML

        Returns:
            True if sent successfully
        """
        if not self.bot_token or not self.chat_id:
            logger.error("Bot token or chat ID not configured")
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text, "parse_mode": parse_mode}

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Message sent successfully")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to send message: {e}")
            return False

    def get_updates(self, offset: Optional[int] = None) -> List[Dict]:
        """Get updates from Telegram (for finding chat_id)."""
        if not self.bot_token:
            return []

        url = f"{self.base_url}/getUpdates"
        params = {"offset": offset} if offset else {}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("result", [])
        except requests.RequestException as e:
            logger.error(f"Failed to get updates: {e}")
            return []

    def get_chat_id(self):
        """Get chat ID by reading recent messages."""
        print("\n📱 Getting your Telegram Chat ID...")
        print("Please send any message to your bot now.\n")

        time.sleep(2)

        updates = self.get_updates()

        if not updates:
            print("❌ No messages found. Make sure you:")
            print("   1. Started a chat with your bot")
            print("   2. Sent at least one message")
            print("   3. Bot token is correct")
            return

        print("\n✅ Found chat(s):\n")
        for update in updates[-5:]:  # Last 5 messages
            message = update.get("message", {})
            chat = message.get("chat", {})
            chat_id = chat.get("id")
            username = chat.get("username", "N/A")
            first_name = chat.get("first_name", "N/A")

            print(f"Chat ID: {chat_id}")
            print(f"Username: @{username}")
            print(f"Name: {first_name}")
            print(f"\nSet this in your environment:")
            print(f"export TELEGRAM_CHAT_ID='{chat_id}'")
            print("-" * 50)

    def send_price_alert(
        self, symbol: str, price: float, alert_type: str, trigger_price: float
    ):
        """Send price alert."""
        emoji = "🚀" if alert_type == "ABOVE" else "📉"

        message = f"""
{emoji} *PRICE ALERT*

Symbol: `{symbol}`
Current Price: ₹{price:,.2f}
Trigger: {alert_type} ₹{trigger_price:,.2f}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message)

    def send_order_alert(
        self, order_id: str, symbol: str, side: str, qty: int, status: str
    ):
        """Send order status alert."""
        emoji = "✅" if status == "FILLED" else "⏳" if status == "PENDING" else "❌"

        message = f"""
{emoji} *ORDER {status}*

Order ID: `{order_id}`
Symbol: `{symbol}`
Side: {side}
Quantity: {qty}

Status: {status}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message)

    def send_margin_alert(self, available: float, used: float, utilization_pct: float):
        """Send margin alert."""
        emoji = "🚨" if utilization_pct > 90 else "⚠️"

        message = f"""
{emoji} *MARGIN ALERT*

Available: ₹{available:,.2f}
Used: ₹{used:,.2f}
Utilization: {utilization_pct:.1f}%

{"🔴 CRITICAL - Reduce positions!" if utilization_pct > 90 else "⚠️ HIGH - Monitor closely"}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message)

    def send_news_alert(self, headline: str, symbol: str, sentiment: str, summary: str):
        """Send breaking news alert."""
        emoji = (
            "🟢" if sentiment == "POSITIVE" else "🔴" if sentiment == "NEGATIVE" else "⚪"
        )

        message = f"""
{emoji} *BREAKING NEWS*

*{headline}*

Symbol: `{symbol}`
Sentiment: {sentiment}

{summary[:200]}...

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message)

    def send_announcement_alert(
        self, symbol: str, event_type: str, event_date: str, days_away: int
    ):
        """Send corporate announcement reminder."""
        emoji = "🔴" if days_away <= 3 else "🟡"

        message = f"""
{emoji} *UPCOMING EVENT*

Symbol: `{symbol}`
Event: {event_type}
Date: {event_date}
Days Away: {days_away}

{"⚠️ Prepare positions!" if days_away <= 3 else "📅 Mark your calendar"}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message)

    def send_economic_alert(
        self, event_name: str, event_date: str, impact_level: str, days_away: int
    ):
        """Send economic event reminder."""
        emoji = "🔴" if impact_level == "HIGH" else "🟡"

        message = f"""
{emoji} *ECONOMIC EVENT*

Event: {event_name}
Date: {event_date}
Impact: {impact_level}
Days Away: {days_away}

{"⚠️ High market impact expected!" if impact_level == "HIGH" else "📊 Monitor market"}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message)

    def send_gtt_trigger_alert(
        self, symbol: str, trigger_price: float, condition: str, order_type: str
    ):
        """Send GTT trigger notification."""
        message = f"""
🎯 *GTT ORDER TRIGGERED*

Symbol: `{symbol}`
Trigger Price: ₹{trigger_price:,.2f}
Condition: {condition}
Order Type: {order_type}

✅ GTT order has been executed!

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message)

    def check_and_send_alerts(self):
        """Check database for pending alerts and send."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        alerts_sent = 0

        # Check corporate announcement alerts
        try:
            cursor.execute(
                """
                SELECT a.*, c.event_date, c.description, c.announcement_type
                FROM announcement_alerts a
                JOIN corporate_announcements c ON a.announcement_id = c.id
                WHERE a.status = 'PENDING'
                AND date(a.alert_date) <= date('now')
                LIMIT 10
            """
            )

            for row in cursor.fetchall():
                symbol = row[2]
                event_type = row[-1]
                event_date = row[-3]
                description = row[-2]

                # Calculate days away
                try:
                    event_dt = datetime.strptime(event_date, "%Y-%m-%d")
                    days_away = (event_dt - datetime.now()).days
                except:
                    days_away = 0

                self.send_announcement_alert(symbol, event_type, event_date, days_away)

                # Mark as sent
                cursor.execute(
                    """
                    UPDATE announcement_alerts
                    SET status = 'SENT', sent_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (row[0],),
                )

                alerts_sent += 1
        except Exception as e:
            logger.error(f"Error checking corporate alerts: {e}")

        # Check economic event alerts
        try:
            cursor.execute(
                """
                SELECT a.*, e.event_date, e.impact_level
                FROM economic_alerts a
                JOIN economic_events e ON a.event_id = e.id
                WHERE a.status = 'PENDING'
                AND date(a.alert_date) <= date('now')
                LIMIT 10
            """
            )

            for row in cursor.fetchall():
                event_name = row[2]
                event_date = row[-2]
                impact_level = row[-1]

                # Calculate days away
                try:
                    event_dt = datetime.strptime(event_date, "%Y-%m-%d")
                    days_away = (event_dt - datetime.now()).days
                except:
                    days_away = 0

                self.send_economic_alert(
                    event_name, event_date, impact_level, days_away
                )

                # Mark as sent
                cursor.execute(
                    """
                    UPDATE economic_alerts
                    SET status = 'SENT', sent_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (row[0],),
                )

                alerts_sent += 1
        except Exception as e:
            logger.error(f"Error checking economic alerts: {e}")

        # Check margin alerts
        try:
            cursor.execute(
                """
                SELECT available_margin, used_margin, margin_utilization_pct
                FROM margin_history
                ORDER BY timestamp DESC
                LIMIT 1
            """
            )

            result = cursor.fetchone()
            if result:
                available, used, utilization = result

                # Send alert if utilization > 80%
                if utilization > 80:
                    self.send_margin_alert(available, used, utilization)
                    alerts_sent += 1
        except Exception as e:
            logger.error(f"Error checking margin: {e}")

        conn.commit()
        conn.close()

        return alerts_sent

    def monitor_alerts(self, interval: int = 300, duration: Optional[int] = None):
        """
        Monitor and send alerts continuously.

        Args:
            interval: Check interval in seconds
            duration: Total duration in seconds
        """
        start_time = time.time()
        print(f"\n🤖 Telegram Bot Monitoring (checking every {interval}s)")
        print(f"Sending alerts to chat_id: {self.chat_id}")
        print("Press Ctrl+C to stop\n")

        # Send startup message
        self.send_message("🤖 *Alert Bot Started*\n\nMonitoring for trading alerts...")

        try:
            while True:
                alerts_sent = self.check_and_send_alerts()

                if alerts_sent > 0:
                    logger.info(f"Sent {alerts_sent} alerts")

                print(
                    f"✓ Checked at {datetime.now().strftime('%H:%M:%S')} - {alerts_sent} alerts sent"
                )

                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    print("\n✅ Monitoring duration completed")
                    self.send_message(
                        "🤖 *Alert Bot Stopped*\n\nMonitoring session ended."
                    )
                    break

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n✅ Monitoring stopped by user")
            self.send_message("🤖 *Alert Bot Stopped*\n\nMonitoring stopped by user.")


def main():
    parser = argparse.ArgumentParser(
        description="Telegram Alert Bot for Trading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--get-chat-id", action="store_true", help="Get your Telegram chat ID"
    )

    parser.add_argument("--test", action="store_true", help="Send test message")

    parser.add_argument("--send", type=str, help="Send custom message")

    parser.add_argument(
        "--monitor", action="store_true", help="Monitor and send alerts"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Monitoring interval in seconds (default: 300)",
    )

    parser.add_argument("--duration", type=int, help="Monitoring duration in seconds")

    parser.add_argument("--bot-token", type=str, help="Telegram bot token")

    parser.add_argument("--chat-id", type=str, help="Telegram chat ID")

    parser.add_argument(
        "--db-path", type=str, default="market_data.db", help="Database path"
    )

    args = parser.parse_args()

    # Initialize bot
    bot = TelegramBot(
        bot_token=args.bot_token, chat_id=args.chat_id, db_path=args.db_path
    )

    # Execute action
    if args.get_chat_id:
        bot.get_chat_id()

    elif args.test:
        print("\n📤 Sending test message...")
        success = bot.send_message(
            """
🤖 *Test Message*

This is a test alert from your Upstox Trading Bot!

✅ If you see this, your bot is configured correctly.

Time: """
            + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        if success:
            print("✅ Test message sent successfully!")
        else:
            print("❌ Failed to send test message")

    elif args.send:
        print(f"\n📤 Sending message: {args.send}")
        success = bot.send_message(args.send)

        if success:
            print("✅ Message sent!")
        else:
            print("❌ Failed to send message")

    elif args.monitor:
        bot.monitor_alerts(interval=args.interval, duration=args.duration)

    else:
        print("\n❌ No action specified. Use --help for options.")
        print("\nQuick start:")
        print("  1. Get chat ID:  python telegram_bot.py --get-chat-id")
        print("  2. Test bot:     python telegram_bot.py --test")
        print("  3. Monitor:      python telegram_bot.py --monitor")


if __name__ == "__main__":
    main()
