#!/usr/bin/env python3
"""
Risk Management System for Trading
Provides position sizing, stop-loss automation, circuit breakers, and risk metrics.
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal
import json
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskManager:
    """
    Comprehensive risk management system for trading.

    Features:
    - Position sizing based on risk percentage
    - Automatic stop-loss execution
    - Circuit breaker (daily loss limits)
    - Risk metrics (VAR, Sharpe, Beta)
    - Maximum position limits
    - Correlation analysis
    """

    def __init__(
        self,
        db_path: str = "market_data.db",
        max_position_size: float = 100000,
        max_daily_loss: float = 5000,
        max_risk_per_trade: float = 0.02,
    ):  # 2% max risk per trade
        self.db_path = db_path
        self.max_position_size = max_position_size
        self.max_daily_loss = max_daily_loss
        self.max_risk_per_trade = max_risk_per_trade
        self.circuit_breaker_triggered = False
        self._init_risk_db()

    def _init_risk_db(self):
        """Initialize database tables for risk tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Risk configurations table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_name TEXT UNIQUE NOT NULL,
                max_position_size REAL,
                max_daily_loss REAL,
                max_risk_per_trade REAL,
                max_open_positions INTEGER DEFAULT 10,
                max_sector_exposure REAL DEFAULT 0.3,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Stop-loss orders table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stop_loss_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                entry_price REAL NOT NULL,
                stop_loss_price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                order_id TEXT,
                status TEXT DEFAULT 'ACTIVE',
                triggered_at DATETIME,
                exit_price REAL,
                pnl REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Circuit breaker events table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS circuit_breaker_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trigger_reason TEXT NOT NULL,
                daily_loss REAL,
                loss_percentage REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                reset_at DATETIME
            )
        """
        )

        # Risk metrics table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_date DATE DEFAULT CURRENT_DATE,
                portfolio_value REAL,
                var_95 REAL,
                var_99 REAL,
                sharpe_ratio REAL,
                beta REAL,
                max_drawdown REAL,
                volatility REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: float,
        account_balance: float,
        risk_percentage: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate optimal position size based on risk parameters.

        Args:
            symbol: Trading symbol
            entry_price: Planned entry price
            stop_loss_price: Stop-loss price
            account_balance: Current account balance
            risk_percentage: Risk per trade (defaults to max_risk_per_trade)

        Returns:
            Dict with quantity, risk_amount, position_value, and risk_reward
        """
        if risk_percentage is None:
            risk_percentage = self.max_risk_per_trade

        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss_price)

        if risk_per_share == 0:
            logger.warning(f"Stop-loss price equals entry price for {symbol}")
            return {
                "quantity": 0,
                "risk_amount": 0,
                "position_value": 0,
                "error": "Invalid stop-loss price",
            }

        # Calculate maximum risk amount
        max_risk_amount = account_balance * risk_percentage

        # Calculate quantity based on risk
        raw_quantity = max_risk_amount / risk_per_share
        quantity = int(raw_quantity)  # Round down to nearest whole share

        # Check against maximum position size
        position_value = quantity * entry_price
        if position_value > self.max_position_size:
            quantity = int(self.max_position_size / entry_price)
            position_value = quantity * entry_price
            logger.warning(
                f"Position size limited by max_position_size. "
                f"Quantity reduced to {quantity}"
            )

        # Actual risk amount
        actual_risk_amount = quantity * risk_per_share
        actual_risk_percentage = (actual_risk_amount / account_balance) * 100

        return {
            "symbol": symbol,
            "quantity": quantity,
            "entry_price": entry_price,
            "stop_loss_price": stop_loss_price,
            "risk_per_share": risk_per_share,
            "risk_amount": actual_risk_amount,
            "risk_percentage": actual_risk_percentage,
            "position_value": position_value,
            "recommendation": "PROCEED" if quantity > 0 else "SKIP",
        }

    def set_stop_loss(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: float,
        quantity: int,
        order_id: Optional[str] = None,
    ) -> int:
        """
        Set a stop-loss order for a position.

        Returns:
            stop_loss_id: ID of the created stop-loss order
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO stop_loss_orders 
            (symbol, entry_price, stop_loss_price, quantity, order_id, status)
            VALUES (?, ?, ?, ?, ?, 'ACTIVE')
        """,
            (symbol, entry_price, stop_loss_price, quantity, order_id),
        )

        stop_loss_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(
            f"Stop-loss set for {symbol}: Entry={entry_price}, "
            f"SL={stop_loss_price}, Qty={quantity}"
        )

        return stop_loss_id

    def check_stop_losses(self, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Check all active stop-losses and return positions that should be exited.

        Args:
            current_prices: Dict of {symbol: current_price}

        Returns:
            List of positions that hit stop-loss
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, symbol, entry_price, stop_loss_price, quantity, order_id
            FROM stop_loss_orders
            WHERE status = 'ACTIVE'
        """
        )

        active_stops = cursor.fetchall()
        triggered_stops = []

        for stop_id, symbol, entry_price, sl_price, quantity, order_id in active_stops:
            current_price = current_prices.get(symbol)

            if current_price is None:
                logger.warning(f"No current price available for {symbol}")
                continue

            # Check if stop-loss is hit
            is_long = entry_price > sl_price  # True = long (SL below entry), False = short (SL above entry)
            stop_hit = False

            if is_long:
                # Long position: exit if price drops below SL
                stop_hit = current_price <= sl_price
            else:
                # Short position: exit if price rises above SL
                stop_hit = current_price >= sl_price

            if stop_hit:
                # Calculate P&L
                pnl = (current_price - entry_price) * quantity

                # Update stop-loss status
                cursor.execute(
                    """
                    UPDATE stop_loss_orders
                    SET status = 'TRIGGERED',
                        triggered_at = CURRENT_TIMESTAMP,
                        exit_price = ?,
                        pnl = ?
                    WHERE id = ?
                """,
                    (current_price, pnl, stop_id),
                )

                triggered_stops.append(
                    {
                        "stop_id": stop_id,
                        "symbol": symbol,
                        "entry_price": entry_price,
                        "stop_loss_price": sl_price,
                        "exit_price": current_price,
                        "quantity": quantity,
                        "pnl": pnl,
                        "order_id": order_id,
                    }
                )

                logger.warning(
                    f"STOP-LOSS TRIGGERED: {symbol} @ {current_price}, "
                    f"P&L: {pnl:.2f}"
                )

        conn.commit()
        conn.close()

        return triggered_stops

    def check_daily_loss(self) -> Dict[str, Any]:
        """
        Check if daily loss limit has been breached.

        Returns:
            Dict with daily_pnl, loss_limit, breached, and circuit_breaker status
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calculate today's P&L from orders/trades
        cursor.execute(
            """
            SELECT SUM(pnl) as daily_pnl
            FROM stop_loss_orders
            WHERE DATE(triggered_at) = DATE('now')
            AND status = 'TRIGGERED'
        """
        )

        result = cursor.fetchone()
        daily_pnl = result[0] if result[0] is not None else 0

        # Check if circuit breaker is already active today
        cursor.execute(
            """
            SELECT COUNT(*) FROM circuit_breaker_events
            WHERE DATE(timestamp) = DATE('now')
            AND reset_at IS NULL
        """
        )

        active_breaker = cursor.fetchone()[0] > 0

        conn.close()

        # Determine if loss limit breached
        loss_breached = daily_pnl < -self.max_daily_loss

        if loss_breached and not active_breaker and not self.circuit_breaker_triggered:
            self._trigger_circuit_breaker(daily_pnl)

        return {
            "daily_pnl": daily_pnl,
            "loss_limit": self.max_daily_loss,
            "loss_percentage": (
                (abs(daily_pnl) / self.max_daily_loss * 100) if daily_pnl < 0 else 0
            ),
            "breached": loss_breached,
            "circuit_breaker_active": self.circuit_breaker_triggered or active_breaker,
        }

    def _trigger_circuit_breaker(self, daily_loss: float):
        """Trigger circuit breaker to stop all trading"""
        self.circuit_breaker_triggered = True

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        loss_percentage = abs(daily_loss) / self.max_daily_loss * 100

        cursor.execute(
            """
            INSERT INTO circuit_breaker_events
            (trigger_reason, daily_loss, loss_percentage)
            VALUES (?, ?, ?)
        """,
            (
                f"Daily loss limit exceeded: {daily_loss:.2f}",
                daily_loss,
                loss_percentage,
            ),
        )

        conn.commit()
        conn.close()

        logger.critical(
            f"🚨 CIRCUIT BREAKER TRIGGERED! Daily loss: {daily_loss:.2f} "
            f"({loss_percentage:.1f}% of limit)"
        )

    def reset_circuit_breaker(self):
        """Reset circuit breaker (typically done at start of new trading day)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE circuit_breaker_events
            SET reset_at = CURRENT_TIMESTAMP
            WHERE reset_at IS NULL
        """
        )

        conn.commit()
        conn.close()

        self.circuit_breaker_triggered = False
        logger.info("Circuit breaker reset for new trading session")

    def calculate_var(
        self, returns: List[float], confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Value at Risk (VAR) at given confidence level.

        Args:
            returns: List of daily returns
            confidence_level: Confidence level (0.95 for 95%, 0.99 for 99%)

        Returns:
            VAR value (negative number representing potential loss)
        """
        if not returns:
            return 0.0

        sorted_returns = sorted(returns)
        index = int((1 - confidence_level) * len(sorted_returns))

        var = (
            sorted_returns[index] if index < len(sorted_returns) else sorted_returns[0]
        )

        return var

    def calculate_sharpe_ratio(
        self, returns: List[float], risk_free_rate: float = 0.05
    ) -> float:
        """
        Calculate Sharpe Ratio.

        Args:
            returns: List of daily returns
            risk_free_rate: Annual risk-free rate (default 5%)

        Returns:
            Sharpe ratio
        """
        if not returns or len(returns) < 2:
            return 0.0

        # Convert annual risk-free rate to daily
        daily_rf = risk_free_rate / 252

        # Calculate excess returns
        excess_returns = [r - daily_rf for r in returns]

        # Mean and std of excess returns
        mean_excess = sum(excess_returns) / len(excess_returns)

        variance = sum((r - mean_excess) ** 2 for r in excess_returns) / (
            len(excess_returns) - 1
        )
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return 0.0

        # Annualized Sharpe ratio
        sharpe = (mean_excess / std_dev) * math.sqrt(252)

        return sharpe

    def calculate_max_drawdown(self, equity_curve: List[float]) -> Dict[str, Any]:
        """
        Calculate maximum drawdown from equity curve.

        Args:
            equity_curve: List of portfolio values over time

        Returns:
            Dict with max_drawdown (percentage), peak, trough, and recovery info
        """
        if not equity_curve or len(equity_curve) < 2:
            return {
                "max_drawdown": 0.0,
                "max_drawdown_pct": 0.0,
                "peak": 0,
                "trough": 0,
            }

        max_dd = 0
        max_dd_pct = 0
        peak_idx = 0
        trough_idx = 0

        peak = equity_curve[0]
        peak_temp_idx = 0

        for i, value in enumerate(equity_curve):
            if value > peak:
                peak = value
                peak_temp_idx = i

            dd = peak - value
            dd_pct = (dd / peak * 100) if peak > 0 else 0

            if dd_pct > max_dd_pct:
                max_dd = dd
                max_dd_pct = dd_pct
                peak_idx = peak_temp_idx
                trough_idx = i

        return {
            "max_drawdown": max_dd,
            "max_drawdown_pct": max_dd_pct,
            "peak_value": equity_curve[peak_idx],
            "trough_value": equity_curve[trough_idx],
            "peak_index": peak_idx,
            "trough_index": trough_idx,
        }

    def get_risk_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate comprehensive risk metrics for the portfolio.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with VAR, Sharpe ratio, max drawdown, volatility
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get daily returns (simulated from P&L)
        cursor.execute(
            """
            SELECT DATE(triggered_at) as trade_date, SUM(pnl) as daily_pnl
            FROM stop_loss_orders
            WHERE triggered_at >= datetime('now', '-{} days')
            GROUP BY DATE(triggered_at)
            ORDER BY trade_date
        """.format(
                days
            )
        )

        daily_pnls = [row[1] for row in cursor.fetchall()]

        # Calculate returns (assuming starting capital)
        starting_capital = 100000  # TODO: Get from account balance
        returns = [pnl / starting_capital for pnl in daily_pnls]

        # Calculate equity curve
        equity_curve = [starting_capital]
        for pnl in daily_pnls:
            equity_curve.append(equity_curve[-1] + pnl)

        # Calculate metrics
        var_95 = self.calculate_var(returns, 0.95)
        var_99 = self.calculate_var(returns, 0.99)
        sharpe = self.calculate_sharpe_ratio(returns)
        drawdown_info = self.calculate_max_drawdown(equity_curve)

        # Calculate volatility
        if len(returns) > 1:
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
            volatility = math.sqrt(variance) * math.sqrt(252) * 100  # Annualized %
        else:
            volatility = 0.0

        conn.close()

        metrics = {
            "period_days": days,
            "var_95_pct": var_95 * 100,
            "var_99_pct": var_99 * 100,
            "sharpe_ratio": sharpe,
            "max_drawdown_pct": drawdown_info["max_drawdown_pct"],
            "volatility_pct": volatility,
            "total_trades": len(daily_pnls),
            "current_equity": equity_curve[-1] if equity_curve else starting_capital,
        }

        # Store metrics in database
        self._store_risk_metrics(metrics)

        return metrics

    def _store_risk_metrics(self, metrics: Dict[str, Any]):
        """Store calculated risk metrics in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO risk_metrics
                (portfolio_value, var_95, var_99, sharpe_ratio, max_drawdown, volatility)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    metrics.get("current_equity", 0),
                    metrics.get("var_95_pct", 0),
                    metrics.get("var_99_pct", 0),
                    metrics.get("sharpe_ratio", 0),
                    metrics.get("max_drawdown_pct", 0),
                    metrics.get("volatility_pct", 0),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store risk metrics: {str(e)}")

    def get_position_limits(self) -> Dict[str, Any]:
        """Get current position limits and usage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Count active positions
        cursor.execute(
            """
            SELECT COUNT(*) FROM stop_loss_orders
            WHERE status = 'ACTIVE'
        """
        )
        active_positions = cursor.fetchone()[0]

        # Sum total position value
        cursor.execute(
            """
            SELECT SUM(entry_price * quantity) as total_value
            FROM stop_loss_orders
            WHERE status = 'ACTIVE'
        """
        )
        total_position_value = cursor.fetchone()[0] or 0

        conn.close()

        return {
            "active_positions": active_positions,
            "max_positions": 10,  # TODO: Make configurable
            "total_position_value": total_position_value,
            "max_position_value": self.max_position_size,
            "utilization_pct": (
                (total_position_value / self.max_position_size * 100)
                if self.max_position_size > 0
                else 0
            ),
        }


def main():
    """Test risk management system"""
    import argparse

    parser = argparse.ArgumentParser(description="Risk Management System")
    parser.add_argument(
        "--action",
        choices=["size", "check-sl", "metrics", "limits", "breaker"],
        default="metrics",
        help="Action to perform",
    )
    parser.add_argument("--symbol", type=str, help="Trading symbol")
    parser.add_argument("--entry", type=float, help="Entry price")
    parser.add_argument("--stop-loss", type=float, help="Stop-loss price")
    parser.add_argument("--balance", type=float, default=100000, help="Account balance")

    args = parser.parse_args()

    risk_mgr = RiskManager()

    if args.action == "size":
        if not all([args.symbol, args.entry, args.stop_loss]):
            print(
                "Error: --symbol, --entry, and --stop-loss required for position sizing"
            )
            return

        result = risk_mgr.calculate_position_size(
            symbol=args.symbol,
            entry_price=args.entry,
            stop_loss_price=args.stop_loss,
            account_balance=args.balance,
        )

        print("\n=== Position Sizing ===")
        print(f"Symbol: {result['symbol']}")
        print(f"Entry Price: ₹{result['entry_price']}")
        print(f"Stop-Loss: ₹{result['stop_loss_price']}")
        print(f"Risk per Share: ₹{result['risk_per_share']:.2f}")
        print(f"\nRecommended Quantity: {result['quantity']}")
        print(f"Position Value: ₹{result['position_value']:,.2f}")
        print(f"Risk Amount: ₹{result['risk_amount']:,.2f}")
        print(f"Risk %: {result['risk_percentage']:.2f}%")
        print(f"\n⚠️  Recommendation: {result['recommendation']}")

    elif args.action == "check-sl":
        # Simulate current prices
        current_prices = {"INFY": 1450.50, "TCS": 3200.75, "RELIANCE": 2450.00}

        triggered = risk_mgr.check_stop_losses(current_prices)

        print("\n=== Stop-Loss Check ===")
        if triggered:
            for stop in triggered:
                print(f"\n🚨 {stop['symbol']}")
                print(f"  Entry: ₹{stop['entry_price']}")
                print(f"  Stop-Loss: ₹{stop['stop_loss_price']}")
                print(f"  Exit: ₹{stop['exit_price']}")
                print(f"  P&L: ₹{stop['pnl']:.2f}")
        else:
            print("No stop-losses triggered")

    elif args.action == "metrics":
        metrics = risk_mgr.get_risk_metrics(days=30)

        print("\n=== Risk Metrics (30 Days) ===")
        print(f"VAR (95%): {metrics['var_95_pct']:.2f}%")
        print(f"VAR (99%): {metrics['var_99_pct']:.2f}%")
        print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")
        print(f"Volatility: {metrics['volatility_pct']:.2f}%")
        print(f"Total Trades: {metrics['total_trades']}")

    elif args.action == "limits":
        limits = risk_mgr.get_position_limits()

        print("\n=== Position Limits ===")
        print(
            f"Active Positions: {limits['active_positions']} / {limits['max_positions']}"
        )
        print(f"Total Value: ₹{limits['total_position_value']:,.2f}")
        print(f"Max Value: ₹{limits['max_position_value']:,.2f}")
        print(f"Utilization: {limits['utilization_pct']:.1f}%")

    elif args.action == "breaker":
        status = risk_mgr.check_daily_loss()

        print("\n=== Circuit Breaker Status ===")
        print(f"Daily P&L: ₹{status['daily_pnl']:,.2f}")
        print(f"Loss Limit: ₹{status['loss_limit']:,.2f}")
        print(f"Loss %: {status['loss_percentage']:.1f}%")
        print(f"Breached: {'YES 🚨' if status['breached'] else 'NO ✅'}")
        print(
            f"Circuit Breaker: {'ACTIVE 🛑' if status['circuit_breaker_active'] else 'INACTIVE'}"
        )


if __name__ == "__main__":
    main()
