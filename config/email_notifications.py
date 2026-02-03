"""
Email Notification Service
Sends trading alerts and reports via email
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailNotifier:
    """
    Email notification service for trading alerts
    """

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_from = os.getenv("EMAIL_FROM")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.email_to = os.getenv("EMAIL_TO", os.getenv("EMAIL_FROM"))

        self.enabled = bool(self.email_from and self.email_password)

        if not self.enabled:
            logger.warning(
                "Email notifications not configured (EMAIL_FROM or EMAIL_PASSWORD missing)"
            )
        else:
            logger.info(f"Email notifications enabled: {self.email_from}")

    def send_email(
        self,
        subject: str,
        body: str,
        html: bool = False,
        attachments: Optional[List[str]] = None,
    ) -> bool:
        """
        Send an email

        Args:
            subject: Email subject
            body: Email body (plain text or HTML)
            html: Whether body is HTML
            attachments: List of file paths to attach

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug(f"Email disabled, would have sent: {subject}")
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.email_from
            msg["To"] = self.email_to
            msg["Subject"] = subject
            msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

            # Add body
            if html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

            # Add attachments
            if attachments:
                for filepath in attachments:
                    if os.path.exists(filepath):
                        with open(filepath, "rb") as f:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                "Content-Disposition",
                                f"attachment; filename={os.path.basename(filepath)}",
                            )
                            msg.attach(part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_alert_email(
        self, alert_type: str, message: str, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a formatted alert email

        Args:
            alert_type: Type of alert (PRICE, ORDER, RISK, etc.)
            message: Alert message
            data: Optional additional data

        Returns:
            True if successful
        """
        subject = f"🚨 Trading Alert: {alert_type}"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #d32f2f;">{alert_type} Alert</h2>
            <p>{message}</p>
            
            <p style="color: #666; font-size: 12px;">
                Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        """

        if data:
            body += "<h3>Details:</h3><ul>"
            for key, value in data.items():
                body += f"<li><strong>{key}:</strong> {value}</li>"
            body += "</ul>"

        body += """
            <hr>
            <p style="color: #999; font-size: 11px;">
                This is an automated message from Upstox Trading Platform.
            </p>
        </body>
        </html>
        """

        return self.send_email(subject, body, html=True)

    def send_price_alert_email(
        self, symbol: str, price: float, condition: str, threshold: float
    ) -> bool:
        """Send price alert email"""
        subject = f"Price Alert: {symbol}"
        message = f"{symbol} {condition} ₹{threshold:,.2f} (Current: ₹{price:,.2f})"

        data = {
            "Symbol": symbol,
            "Current Price": f"₹{price:,.2f}",
            "Condition": condition,
            "Threshold": f"₹{threshold:,.2f}",
        }

        return self.send_alert_email("PRICE", message, data)

    def send_order_notification_email(
        self,
        order_id: str,
        symbol: str,
        action: str,
        quantity: int,
        price: float,
        status: str,
    ) -> bool:
        """Send order notification email"""
        subject = f"Order {status}: {symbol}"
        message = f"Your {action} order for {quantity} shares of {symbol} is {status}"

        data = {
            "Order ID": order_id,
            "Symbol": symbol,
            "Action": action,
            "Quantity": quantity,
            "Price": f"₹{price:,.2f}",
            "Status": status,
            "Total Value": f"₹{price * quantity:,.2f}",
        }

        return self.send_alert_email("ORDER", message, data)

    def send_daily_summary_email(self, summary_data: Dict[str, Any]) -> bool:
        """Send daily trading summary email"""
        subject = "Daily Trading Summary"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #1976d2;">Daily Trading Summary</h2>
            <p style="color: #666;">{datetime.now().strftime('%A, %B %d, %Y')}</p>
            
            <h3>Portfolio Overview</h3>
            <table style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Total Value</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">₹{summary_data.get('total_value', 0):,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>P&L Today</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: {'green' if summary_data.get('day_pnl', 0) >= 0 else 'red'};">
                        ₹{summary_data.get('day_pnl', 0):,.2f} ({summary_data.get('day_pnl_percent', 0):+.2f}%)
                    </td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Open Positions</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{summary_data.get('positions_count', 0)}</td>
                </tr>
            </table>
            
            <h3>Trading Activity</h3>
            <ul>
                <li>Orders Placed: {summary_data.get('orders_placed', 0)}</li>
                <li>Orders Filled: {summary_data.get('orders_filled', 0)}</li>
                <li>Trades Executed: {summary_data.get('trades_executed', 0)}</li>
            </ul>
        """

        top_gainers = summary_data.get("top_gainers", [])
        if top_gainers:
            body += "<h3>Top Performers</h3><ul>"
            for stock in top_gainers[:5]:
                body += f"<li>{stock['symbol']}: {stock['pnl_percent']:+.2f}%</li>"
            body += "</ul>"

        body += """
            <hr>
            <p style="color: #999; font-size: 11px;">
                This is an automated report from Upstox Trading Platform.
            </p>
        </body>
        </html>
        """

        return self.send_email(subject, body, html=True)

    def send_risk_alert_email(
        self,
        alert_level: str,
        message: str,
        recommendations: Optional[List[str]] = None,
    ) -> bool:
        """Send risk management alert email"""
        subject = f"⚠️ Risk Alert - {alert_level}"

        color = (
            "#d32f2f"
            if alert_level == "HIGH"
            else "#ff9800"
            if alert_level == "MEDIUM"
            else "#4caf50"
        )

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: {color};">Risk Alert: {alert_level}</h2>
            <p>{message}</p>
        """

        if recommendations:
            body += "<h3>Recommendations:</h3><ul>"
            for rec in recommendations:
                body += f"<li>{rec}</li>"
            body += "</ul>"

        body += """
            <p style="margin-top: 20px;">
                <strong>Action Required:</strong> Please review your positions and risk exposure immediately.
            </p>
            <hr>
            <p style="color: #999; font-size: 11px;">
                This is an automated alert from Upstox Trading Platform.
            </p>
        </body>
        </html>
        """

        return self.send_email(subject, body, html=True)


# Global instance
_email_notifier = None


def get_email_notifier() -> EmailNotifier:
    """Get global email notifier instance"""
    global _email_notifier
    if _email_notifier is None:
        _email_notifier = EmailNotifier()
    return _email_notifier


def send_email_alert(
    alert_type: str, message: str, data: Optional[Dict] = None
) -> bool:
    """
    Convenience function to send email alert

    Args:
        alert_type: Type of alert
        message: Alert message
        data: Optional data dict

    Returns:
        True if successful
    """
    notifier = get_email_notifier()
    return notifier.send_alert_email(alert_type, message, data)


if __name__ == "__main__":
    # Test the email notifier
    notifier = EmailNotifier()

    if notifier.enabled:
        print("Sending test email...")
        success = notifier.send_email(
            subject="Test Email - Upstox Trading Platform",
            body="<h2>Test Email</h2><p>Email integration is working!</p>",
            html=True,
        )
        print(f"Result: {'Success' if success else 'Failed'}")
    else:
        print(
            "Email not configured. Set EMAIL_FROM and EMAIL_PASSWORD environment variables."
        )
        print("\nFor Gmail:")
        print("1. Enable 2-factor authentication")
        print("2. Generate an App Password")
        print("3. Use that App Password as EMAIL_PASSWORD")
