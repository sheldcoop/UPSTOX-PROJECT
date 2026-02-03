"""
Enhanced Telegram Bot Integration
Provides trading alerts and notifications via Telegram
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Enhanced Telegram notification service
    """

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.bot_token and self.chat_id)

        if not self.enabled:
            logger.warning(
                "Telegram bot not configured (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing)"
            )
        else:
            logger.info("Telegram bot initialized")

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message via Telegram

        Args:
            text: Message text
            parse_mode: Formatting mode (HTML or Markdown)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug(f"Telegram disabled, would have sent: {text}")
            return False

        try:
            import requests

            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {"chat_id": self.chat_id, "text": text, "parse_mode": parse_mode}

            response = requests.post(url, json=data, timeout=10)

            if response.status_code == 200:
                logger.debug("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Failed to send Telegram message: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False

    def send_alert(
        self, alert_type: str, message: str, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a formatted alert

        Args:
            alert_type: Type of alert (PRICE, ORDER, RISK, etc.)
            message: Alert message
            data: Optional additional data

        Returns:
            True if successful
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        formatted_message = f"""
🚨 <b>{alert_type} ALERT</b>

{message}

<i>Time: {timestamp}</i>
"""

        if data:
            formatted_message += "\n<b>Details:</b>\n"
            for key, value in data.items():
                formatted_message += f"• {key}: {value}\n"

        return self.send_message(formatted_message)

    def send_price_alert(
        self, symbol: str, price: float, condition: str, threshold: float
    ) -> bool:
        """Send price alert"""
        message = f"""
📈 <b>Price Alert: {symbol}</b>

Current Price: ₹{price:,.2f}
Condition: {condition}
Threshold: ₹{threshold:,.2f}
"""
        return self.send_message(message)

    def send_order_notification(
        self,
        order_id: str,
        symbol: str,
        action: str,
        quantity: int,
        price: float,
        status: str,
    ) -> bool:
        """Send order notification"""
        emoji = "✅" if status == "COMPLETE" else "⏳" if status == "PENDING" else "❌"

        message = f"""
{emoji} <b>Order {status}</b>

Order ID: {order_id}
Symbol: {symbol}
Action: {action}
Quantity: {quantity}
Price: ₹{price:,.2f}
Status: {status}
"""
        return self.send_message(message)

    def send_risk_alert(self, alert_level: str, message: str) -> bool:
        """Send risk management alert"""
        emoji = (
            "🔴" if alert_level == "HIGH" else "🟡" if alert_level == "MEDIUM" else "🟢"
        )

        formatted_message = f"""
{emoji} <b>RISK ALERT - {alert_level}</b>

{message}

<i>Please review your positions and risk exposure.</i>
"""
        return self.send_message(formatted_message)

    def send_daily_summary(self, summary_data: Dict[str, Any]) -> bool:
        """Send daily trading summary"""
        message = f"""
📊 <b>Daily Trading Summary</b>

<b>Portfolio:</b>
• Total Value: ₹{summary_data.get('total_value', 0):,.2f}
• P&L Today: ₹{summary_data.get('day_pnl', 0):,.2f}
• P&L %: {summary_data.get('day_pnl_percent', 0):+.2f}%

<b>Trading Activity:</b>
• Orders Placed: {summary_data.get('orders_placed', 0)}
• Orders Filled: {summary_data.get('orders_filled', 0)}
• Positions: {summary_data.get('positions_count', 0)}

<b>Top Performers:</b>
"""

        top_gainers = summary_data.get("top_gainers", [])
        for stock in top_gainers[:3]:
            message += f"• {stock['symbol']}: {stock['pnl_percent']:+.2f}%\n"

        return self.send_message(message)

    def send_news_alert(
        self, title: str, summary: str, url: Optional[str] = None
    ) -> bool:
        """Send news alert"""
        message = f"""
📰 <b>Market News</b>

<b>{title}</b>

{summary}
"""

        if url:
            message += f"\n<a href='{url}'>Read more</a>"

        return self.send_message(message)

    def send_strategy_signal(
        self,
        symbol: str,
        signal: str,
        strategy: str,
        confidence: float,
        entry_price: float,
    ) -> bool:
        """Send trading strategy signal"""
        emoji = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "⚪"

        message = f"""
{emoji} <b>Strategy Signal: {signal}</b>

Symbol: {symbol}
Strategy: {strategy}
Confidence: {confidence:.1f}%
Entry Price: ₹{entry_price:,.2f}
"""
        return self.send_message(message)


# Global instance
_notifier = None


def get_telegram_notifier() -> TelegramNotifier:
    """Get global Telegram notifier instance"""
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier()
    return _notifier


def send_telegram_alert(
    alert_type: str, message: str, data: Optional[Dict] = None
) -> bool:
    """
    Convenience function to send alert

    Args:
        alert_type: Type of alert
        message: Alert message
        data: Optional data dict

    Returns:
        True if successful
    """
    notifier = get_telegram_notifier()
    return notifier.send_alert(alert_type, message, data)


if __name__ == "__main__":
    # Test the notifier
    notifier = TelegramNotifier()

    if notifier.enabled:
        print("Sending test message...")
        success = notifier.send_message(
            "✅ <b>Test Alert</b>\n\nTelegram integration is working!"
        )
        print(f"Result: {'Success' if success else 'Failed'}")
    else:
        print(
            "Telegram bot not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables."
        )
