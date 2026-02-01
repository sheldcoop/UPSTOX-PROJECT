#!/usr/bin/env python3
"""
Real-time Alert System
Monitors prices, technical indicators, volume spikes, and triggers notifications.
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertType:
    """Alert type constants"""
    PRICE_ABOVE = "PRICE_ABOVE"
    PRICE_BELOW = "PRICE_BELOW"
    VOLUME_SPIKE = "VOLUME_SPIKE"
    RSI_OVERBOUGHT = "RSI_OVERBOUGHT"
    RSI_OVERSOLD = "RSI_OVERSOLD"
    MACD_CROSSOVER = "MACD_CROSSOVER"
    SUPPORT_BREAK = "SUPPORT_BREAK"
    RESISTANCE_BREAK = "RESISTANCE_BREAK"
    PERCENTAGE_CHANGE = "PERCENTAGE_CHANGE"


class AlertPriority:
    """Alert priority levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Alert:
    """Represents a trading alert"""
    
    def __init__(self, symbol: str, alert_type: str, condition: str,
                 current_value: float, threshold: float,
                 priority: str = AlertPriority.MEDIUM,
                 message: Optional[str] = None):
        self.symbol = symbol
        self.alert_type = alert_type
        self.condition = condition
        self.current_value = current_value
        self.threshold = threshold
        self.priority = priority
        self.message = message or self._generate_message()
        self.timestamp = datetime.now()
    
    def _generate_message(self) -> str:
        """Generate alert message"""
        if self.alert_type == AlertType.PRICE_ABOVE:
            return f"{self.symbol} price ₹{self.current_value:.2f} crossed above ₹{self.threshold:.2f}"
        elif self.alert_type == AlertType.PRICE_BELOW:
            return f"{self.symbol} price ₹{self.current_value:.2f} fell below ₹{self.threshold:.2f}"
        elif self.alert_type == AlertType.VOLUME_SPIKE:
            return f"{self.symbol} volume spike: {self.current_value:.0f} ({self.threshold:.0f}x average)"
        elif self.alert_type == AlertType.RSI_OVERBOUGHT:
            return f"{self.symbol} RSI overbought: {self.current_value:.1f}"
        elif self.alert_type == AlertType.RSI_OVERSOLD:
            return f"{self.symbol} RSI oversold: {self.current_value:.1f}"
        elif self.alert_type == AlertType.PERCENTAGE_CHANGE:
            return f"{self.symbol} changed {self.current_value:.2f}% (threshold: {self.threshold:.2f}%)"
        else:
            return f"{self.symbol} alert: {self.alert_type}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'alert_type': self.alert_type,
            'condition': self.condition,
            'current_value': self.current_value,
            'threshold': self.threshold,
            'priority': self.priority,
            'message': self.message,
            'timestamp': self.timestamp.isoformat()
        }


class AlertSystem:
    """
    Real-time alert monitoring and notification system.
    
    Features:
    - Price threshold alerts
    - Technical indicator alerts (RSI, MACD)
    - Volume spike detection
    - Support/resistance level breaks
    - Multi-channel notifications (console, email, database)
    """
    
    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path
        self.alert_callbacks: List[Callable] = []
        self.active_alerts: Dict[str, List[Dict]] = {}
        self._init_alert_db()
    
    def _init_alert_db(self):
        """Initialize database tables for alerts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Alert rules
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                condition TEXT,
                threshold REAL,
                priority TEXT DEFAULT 'MEDIUM',
                enabled BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                triggered_count INTEGER DEFAULT 0,
                last_triggered DATETIME
            )
        """)
        
        # Alert history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id INTEGER,
                symbol TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                current_value REAL,
                threshold REAL,
                priority TEXT,
                message TEXT,
                triggered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                acknowledged BOOLEAN DEFAULT 0,
                acknowledged_at DATETIME,
                FOREIGN KEY (rule_id) REFERENCES alert_rules(id)
            )
        """)
        
        # Alert notifications (email, SMS, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id INTEGER NOT NULL,
                channel TEXT NOT NULL,
                status TEXT DEFAULT 'PENDING',
                sent_at DATETIME,
                error_message TEXT,
                FOREIGN KEY (alert_id) REFERENCES alert_history(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_price_alert(self, symbol: str, price: float, above: bool = True,
                       priority: str = AlertPriority.MEDIUM) -> int:
        """
        Add a price threshold alert.
        
        Args:
            symbol: Trading symbol
            price: Alert price
            above: True for "price above", False for "price below"
            priority: Alert priority
        
        Returns:
            Alert rule ID
        """
        alert_type = AlertType.PRICE_ABOVE if above else AlertType.PRICE_BELOW
        condition = f"price {'>' if above else '<'} {price}"
        
        return self._add_alert_rule(
            symbol=symbol,
            alert_type=alert_type,
            condition=condition,
            threshold=price,
            priority=priority
        )
    
    def add_rsi_alert(self, symbol: str, rsi_level: float, overbought: bool = True,
                     priority: str = AlertPriority.MEDIUM) -> int:
        """Add RSI threshold alert"""
        alert_type = AlertType.RSI_OVERBOUGHT if overbought else AlertType.RSI_OVERSOLD
        condition = f"RSI {'>' if overbought else '<'} {rsi_level}"
        
        return self._add_alert_rule(
            symbol=symbol,
            alert_type=alert_type,
            condition=condition,
            threshold=rsi_level,
            priority=priority
        )
    
    def add_volume_spike_alert(self, symbol: str, multiplier: float = 2.0,
                              priority: str = AlertPriority.HIGH) -> int:
        """Add volume spike alert"""
        condition = f"volume > {multiplier}x average"
        
        return self._add_alert_rule(
            symbol=symbol,
            alert_type=AlertType.VOLUME_SPIKE,
            condition=condition,
            threshold=multiplier,
            priority=priority
        )
    
    def add_percentage_change_alert(self, symbol: str, percentage: float,
                                   priority: str = AlertPriority.MEDIUM) -> int:
        """Add percentage change alert"""
        condition = f"daily_change > {percentage}%"
        
        return self._add_alert_rule(
            symbol=symbol,
            alert_type=AlertType.PERCENTAGE_CHANGE,
            condition=condition,
            threshold=percentage,
            priority=priority
        )
    
    def _add_alert_rule(self, symbol: str, alert_type: str, condition: str,
                       threshold: float, priority: str) -> int:
        """Add alert rule to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO alert_rules
            (symbol, alert_type, condition, threshold, priority)
            VALUES (?, ?, ?, ?, ?)
        """, (symbol, alert_type, condition, threshold, priority))
        
        rule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Alert rule added: {symbol} - {alert_type} (ID: {rule_id})")
        
        return rule_id
    
    def check_price_alerts(self, symbol: str, current_price: float) -> List[Alert]:
        """Check price-based alerts for a symbol"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, alert_type, threshold, priority
            FROM alert_rules
            WHERE symbol = ?
            AND alert_type IN ('PRICE_ABOVE', 'PRICE_BELOW')
            AND enabled = 1
        """, (symbol,))
        
        rules = cursor.fetchall()
        conn.close()
        
        triggered_alerts = []
        
        for rule_id, alert_type, threshold, priority in rules:
            triggered = False
            
            if alert_type == AlertType.PRICE_ABOVE and current_price > threshold:
                triggered = True
            elif alert_type == AlertType.PRICE_BELOW and current_price < threshold:
                triggered = True
            
            if triggered:
                alert = Alert(
                    symbol=symbol,
                    alert_type=alert_type,
                    condition=f"price {'>=' if alert_type == AlertType.PRICE_ABOVE else '<='} {threshold}",
                    current_value=current_price,
                    threshold=threshold,
                    priority=priority
                )
                
                triggered_alerts.append(alert)
                self._trigger_alert(rule_id, alert)
        
        return triggered_alerts
    
    def check_volume_alerts(self, symbol: str, current_volume: int) -> List[Alert]:
        """Check volume spike alerts"""
        # Get average volume
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT AVG(volume) as avg_volume
            FROM market_data
            WHERE symbol = ?
            AND timestamp >= datetime('now', '-30 days')
        """, (symbol,))
        
        avg_volume = cursor.fetchone()[0] or 0
        
        # Get volume alert rules
        cursor.execute("""
            SELECT id, threshold, priority
            FROM alert_rules
            WHERE symbol = ?
            AND alert_type = 'VOLUME_SPIKE'
            AND enabled = 1
        """, (symbol,))
        
        rules = cursor.fetchall()
        conn.close()
        
        if avg_volume == 0:
            return []
        
        triggered_alerts = []
        volume_multiple = current_volume / avg_volume
        
        for rule_id, threshold, priority in rules:
            if volume_multiple > threshold:
                alert = Alert(
                    symbol=symbol,
                    alert_type=AlertType.VOLUME_SPIKE,
                    condition=f"volume > {threshold}x average",
                    current_value=current_volume,
                    threshold=threshold,
                    priority=priority
                )
                
                triggered_alerts.append(alert)
                self._trigger_alert(rule_id, alert)
        
        return triggered_alerts
    
    def check_percentage_change_alerts(self, symbol: str) -> List[Alert]:
        """Check percentage change alerts"""
        # Get today's change
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT open, close
            FROM market_data
            WHERE symbol = ?
            AND DATE(timestamp) = DATE('now')
            ORDER BY timestamp DESC
            LIMIT 1
        """, (symbol,))
        
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return []
        
        open_price, current_price = result
        percentage_change = ((current_price - open_price) / open_price) * 100
        
        # Get percentage change rules
        cursor.execute("""
            SELECT id, threshold, priority
            FROM alert_rules
            WHERE symbol = ?
            AND alert_type = 'PERCENTAGE_CHANGE'
            AND enabled = 1
        """, (symbol,))
        
        rules = cursor.fetchall()
        conn.close()
        
        triggered_alerts = []
        
        for rule_id, threshold, priority in rules:
            if abs(percentage_change) > threshold:
                alert = Alert(
                    symbol=symbol,
                    alert_type=AlertType.PERCENTAGE_CHANGE,
                    condition=f"change > {threshold}%",
                    current_value=percentage_change,
                    threshold=threshold,
                    priority=priority
                )
                
                triggered_alerts.append(alert)
                self._trigger_alert(rule_id, alert)
        
        return triggered_alerts
    
    def _trigger_alert(self, rule_id: int, alert: Alert):
        """Trigger an alert and store in history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Store in alert history
        cursor.execute("""
            INSERT INTO alert_history
            (rule_id, symbol, alert_type, current_value, threshold, priority, message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            rule_id,
            alert.symbol,
            alert.alert_type,
            alert.current_value,
            alert.threshold,
            alert.priority,
            alert.message
        ))
        
        alert_id = cursor.lastrowid
        
        # Update rule trigger count
        cursor.execute("""
            UPDATE alert_rules
            SET triggered_count = triggered_count + 1,
                last_triggered = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (rule_id,))
        
        conn.commit()
        conn.close()
        
        # Send notifications
        self._send_notification(alert_id, alert)
        
        # Execute callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {str(e)}")
    
    def _send_notification(self, alert_id: int, alert: Alert):
        """Send alert notification through various channels"""
        # Console notification
        priority_emoji = {
            AlertPriority.LOW: "ℹ️",
            AlertPriority.MEDIUM: "⚠️",
            AlertPriority.HIGH: "🚨",
            AlertPriority.CRITICAL: "🔴"
        }
        
        emoji = priority_emoji.get(alert.priority, "📢")
        logger.info(f"{emoji} ALERT [{alert.priority}]: {alert.message}")
        
        # Store notification attempt
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO alert_notifications
            (alert_id, channel, status, sent_at)
            VALUES (?, 'CONSOLE', 'SENT', CURRENT_TIMESTAMP)
        """, (alert_id,))
        
        conn.commit()
        conn.close()
    
    def register_callback(self, callback: Callable):
        """Register a callback function for alerts"""
        self.alert_callbacks.append(callback)
    
    def get_active_alerts(self, priority: Optional[str] = None) -> List[Dict]:
        """Get unacknowledged alerts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT id, symbol, alert_type, message, priority, triggered_at
            FROM alert_history
            WHERE acknowledged = 0
        """
        
        if priority:
            query += f" AND priority = '{priority}'"
        
        query += " ORDER BY triggered_at DESC LIMIT 50"
        
        cursor.execute(query)
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                'id': row[0],
                'symbol': row[1],
                'alert_type': row[2],
                'message': row[3],
                'priority': row[4],
                'triggered_at': row[5]
            })
        
        conn.close()
        
        return alerts
    
    def acknowledge_alert(self, alert_id: int):
        """Mark an alert as acknowledged"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE alert_history
            SET acknowledged = 1,
                acknowledged_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (alert_id,))
        
        conn.commit()
        conn.close()
    
    def delete_alert_rule(self, rule_id: int):
        """Delete an alert rule"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM alert_rules WHERE id = ?", (rule_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Alert rule {rule_id} deleted")
    
    def get_alert_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get alert statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total alerts
        cursor.execute("""
            SELECT COUNT(*) FROM alert_history
            WHERE triggered_at >= datetime('now', '-{} days')
        """.format(days))
        total_alerts = cursor.fetchone()[0]
        
        # Alerts by type
        cursor.execute("""
            SELECT alert_type, COUNT(*) as count
            FROM alert_history
            WHERE triggered_at >= datetime('now', '-{} days')
            GROUP BY alert_type
            ORDER BY count DESC
        """.format(days))
        alerts_by_type = dict(cursor.fetchall())
        
        # Alerts by priority
        cursor.execute("""
            SELECT priority, COUNT(*) as count
            FROM alert_history
            WHERE triggered_at >= datetime('now', '-{} days')
            GROUP BY priority
        """.format(days))
        alerts_by_priority = dict(cursor.fetchall())
        
        # Most active symbols
        cursor.execute("""
            SELECT symbol, COUNT(*) as count
            FROM alert_history
            WHERE triggered_at >= datetime('now', '-{} days')
            GROUP BY symbol
            ORDER BY count DESC
            LIMIT 10
        """.format(days))
        top_symbols = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_alerts': total_alerts,
            'alerts_by_type': alerts_by_type,
            'alerts_by_priority': alerts_by_priority,
            'top_symbols': top_symbols,
            'period_days': days
        }


def main():
    """Test alert system"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Alert System")
    parser.add_argument('--action',
                       choices=['add', 'check', 'list', 'stats'],
                       default='list',
                       help='Action to perform')
    parser.add_argument('--symbol', type=str, help='Trading symbol')
    parser.add_argument('--price', type=float, help='Alert price')
    parser.add_argument('--above', action='store_true', help='Price above alert')
    
    args = parser.parse_args()
    
    alert_system = AlertSystem()
    
    if args.action == 'add':
        if not all([args.symbol, args.price]):
            print("Error: --symbol and --price required")
            return
        
        rule_id = alert_system.add_price_alert(
            symbol=args.symbol,
            price=args.price,
            above=args.above,
            priority=AlertPriority.MEDIUM
        )
        
        print(f"Alert rule added: ID {rule_id}")
        print(f"{args.symbol} price {'above' if args.above else 'below'} ₹{args.price}")
    
    elif args.action == 'check':
        if not all([args.symbol, args.price]):
            print("Error: --symbol and --price required")
            return
        
        alerts = alert_system.check_price_alerts(args.symbol, args.price)
        
        print(f"\n=== Triggered Alerts for {args.symbol} @ ₹{args.price} ===")
        if alerts:
            for alert in alerts:
                print(f"\n{alert.priority}: {alert.message}")
        else:
            print("No alerts triggered")
    
    elif args.action == 'list':
        alerts = alert_system.get_active_alerts()
        
        print(f"\n=== Active Alerts ({len(alerts)}) ===")
        for alert in alerts:
            print(f"\n[{alert['priority']}] {alert['symbol']}")
            print(f"  {alert['message']}")
            print(f"  Triggered: {alert['triggered_at']}")
    
    elif args.action == 'stats':
        stats = alert_system.get_alert_statistics(days=7)
        
        print("\n=== Alert Statistics (7 Days) ===")
        print(f"Total Alerts: {stats['total_alerts']}")
        
        print("\nBy Type:")
        for alert_type, count in stats['alerts_by_type'].items():
            print(f"  {alert_type}: {count}")
        
        print("\nBy Priority:")
        for priority, count in stats['alerts_by_priority'].items():
            print(f"  {priority}: {count}")
        
        print("\nTop Symbols:")
        for symbol, count in stats['top_symbols'].items():
            print(f"  {symbol}: {count}")


if __name__ == "__main__":
    main()
