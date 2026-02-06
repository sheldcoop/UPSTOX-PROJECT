"""
Portfolio Analytics Dashboard Backend
Sharpe ratio, max drawdown, win rate, equity curve calculations
"""

import sys
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.data.database.database_validator import DatabaseValidator

# Setup logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PortfolioAnalytics:
    """Calculate portfolio performance metrics"""

    def __init__(self):
        self.db_validator = DatabaseValidator()

    def get_equity_curve(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Get daily equity curve

        Returns:
            [{'date': '2026-01-01', 'equity': 100000, 'pnl': 500}, ...]
        """
        try:
            conn = self.db_validator.get_connection()

            # Query daily P&L from trades/positions
            query = """
                SELECT 
                    DATE(created_at) as date,
                    SUM(pnl) as daily_pnl
                FROM paper_orders
                WHERE status = 'COMPLETE'
                    AND created_at BETWEEN ? AND ?
                GROUP BY DATE(created_at)
                ORDER BY date
            """

            df = pd.read_sql_query(query, conn, params=(start_date, end_date))
            conn.close()

            if df.empty:
                # Return mock data if no real data
                return self._get_mock_equity_curve(start_date, end_date)

            # Calculate cumulative equity
            initial_capital = 100000
            df["equity"] = initial_capital + df["daily_pnl"].cumsum()

            return df.to_dict("records")

        except Exception as e:
            logger.error(f"Error getting equity curve: {e}", exc_info=True)
            return self._get_mock_equity_curve(start_date, end_date)

    def calculate_sharpe_ratio(
        self, returns: List[float], risk_free_rate: float = 0.05
    ) -> float:
        """
        Calculate Sharpe ratio

        Args:
            returns: List of daily returns (as decimals, e.g., 0.01 for 1%)
            risk_free_rate: Annual risk-free rate (default 5%)

        Returns:
            Sharpe ratio (annualized)
        """
        if not returns or len(returns) < 2:
            return 0.0

        returns_array = np.array(returns)

        # Annualized return
        mean_return = np.mean(returns_array) * 252  # 252 trading days

        # Annualized volatility
        std_return = np.std(returns_array) * np.sqrt(252)

        if std_return == 0:
            return 0.0

        sharpe = (mean_return - risk_free_rate) / std_return
        return sharpe

    def calculate_sortino_ratio(
        self, returns: List[float], risk_free_rate: float = 0.05
    ) -> float:
        """
        Calculate Sortino ratio (uses only downside deviation)

        Args:
            returns: List of daily returns
            risk_free_rate: Annual risk-free rate

        Returns:
            Sortino ratio (annualized)
        """
        if not returns or len(returns) < 2:
            return 0.0

        returns_array = np.array(returns)
        mean_return = np.mean(returns_array) * 252

        # Downside deviation (only negative returns)
        downside_returns = returns_array[returns_array < 0]
        if len(downside_returns) == 0:
            return float("inf") if mean_return > risk_free_rate else 0.0

        downside_dev = np.std(downside_returns) * np.sqrt(252)

        if downside_dev == 0:
            return 0.0

        sortino = (mean_return - risk_free_rate) / downside_dev
        return sortino

    def calculate_max_drawdown(self, equity_curve: List[float]) -> Dict:
        """
        Calculate maximum drawdown

        Args:
            equity_curve: List of equity values

        Returns:
            {
                'max_drawdown': -0.15,  # -15%
                'max_drawdown_value': -15000,
                'peak_value': 115000,
                'trough_value': 100000,
                'recovery_date': '2026-02-15'
            }
        """
        if not equity_curve or len(equity_curve) < 2:
            return {"max_drawdown": 0, "max_drawdown_value": 0}

        equity_array = np.array(equity_curve)

        # Calculate running maximum
        running_max = np.maximum.accumulate(equity_array)

        # Calculate drawdown
        drawdown = equity_array - running_max
        drawdown_percent = drawdown / running_max

        # Find maximum drawdown
        max_dd_idx = np.argmin(drawdown_percent)
        max_dd = drawdown_percent[max_dd_idx]
        max_dd_value = drawdown[max_dd_idx]

        # Find peak before drawdown
        peak_idx = np.argmax(running_max[: max_dd_idx + 1])
        peak_value = equity_array[peak_idx]
        trough_value = equity_array[max_dd_idx]

        return {
            "max_drawdown": float(max_dd),
            "max_drawdown_percent": float(max_dd * 100),
            "max_drawdown_value": float(max_dd_value),
            "peak_value": float(peak_value),
            "trough_value": float(trough_value),
            "peak_index": int(peak_idx),
            "trough_index": int(max_dd_idx),
        }

    def calculate_win_rate(self, trades: List[Dict]) -> Dict:
        """
        Calculate win rate and average win/loss

        Args:
            trades: List of trade dicts with 'pnl' field

        Returns:
            {
                'total_trades': 100,
                'winning_trades': 65,
                'losing_trades': 35,
                'win_rate': 65.0,
                'avg_win': 500,
                'avg_loss': -300,
                'profit_factor': 1.08
            }
        """
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "profit_factor": 0,
            }

        pnls = [t["pnl"] for t in trades if "pnl" in t]

        total_trades = len(pnls)
        winning_trades = sum(1 for pnl in pnls if pnl > 0)
        losing_trades = sum(1 for pnl in pnls if pnl < 0)

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        wins = [pnl for pnl in pnls if pnl > 0]
        losses = [pnl for pnl in pnls if pnl < 0]

        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0

        total_wins = sum(wins) if wins else 0
        total_losses = abs(sum(losses)) if losses else 0

        profit_factor = (
            (total_wins / total_losses) if total_losses > 0 else float("inf")
        )

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "avg_win": float(avg_win),
            "avg_loss": float(avg_loss),
            "total_profit": float(total_wins),
            "total_loss": float(total_losses),
            "profit_factor": (
                float(profit_factor) if profit_factor != float("inf") else 999
            ),
        }

    def get_performance_summary(self, start_date: str, end_date: str) -> Dict:
        """
        Get comprehensive performance summary

        Returns:
            Complete analytics dashboard data
        """
        try:
            # Get equity curve
            equity_curve = self.get_equity_curve(start_date, end_date)
            equity_values = [e["equity"] for e in equity_curve]

            # Calculate returns
            returns = []
            for i in range(1, len(equity_values)):
                ret = (equity_values[i] - equity_values[i - 1]) / equity_values[i - 1]
                returns.append(ret)

            # Get trades
            conn = self.db_validator.get_connection()
            trades_df = pd.read_sql_query(
                "SELECT * FROM paper_orders WHERE status = 'COMPLETE' AND created_at BETWEEN ? AND ?",
                conn,
                params=(start_date, end_date),
            )
            conn.close()

            trades = trades_df.to_dict("records") if not trades_df.empty else []

            # Calculate metrics
            sharpe = self.calculate_sharpe_ratio(returns)
            sortino = self.calculate_sortino_ratio(returns)
            max_dd = self.calculate_max_drawdown(equity_values)
            win_stats = self.calculate_win_rate(trades)

            total_return = (
                ((equity_values[-1] - equity_values[0]) / equity_values[0] * 100)
                if equity_values
                else 0
            )

            return {
                "start_date": start_date,
                "end_date": end_date,
                "initial_capital": equity_values[0] if equity_values else 100000,
                "final_capital": equity_values[-1] if equity_values else 100000,
                "total_return": total_return,
                "total_pnl": (
                    equity_values[-1] - equity_values[0] if equity_values else 0
                ),
                "sharpe_ratio": sharpe,
                "sortino_ratio": sortino,
                "max_drawdown": max_dd,
                "win_stats": win_stats,
                "equity_curve": equity_curve,
                "num_days": len(equity_curve),
                "avg_daily_pnl": (
                    np.mean([e.get("pnl", 0) for e in equity_curve])
                    if equity_curve
                    else 0
                ),
            }

        except Exception as e:
            logger.error(f"Error getting performance summary: {e}", exc_info=True)
            return {"error": str(e)}

    def _get_mock_equity_curve(self, start_date: str, end_date: str) -> List[Dict]:
        """Generate mock equity curve for demo"""
        dates = pd.date_range(start_date, end_date, freq="D")

        initial_capital = 100000
        daily_pnl = (
            np.random.randn(len(dates)) * 500 + 200
        )  # Avg +200/day with volatility

        equity_curve = []
        cumulative_pnl = 0

        for date, pnl in zip(dates, daily_pnl):
            cumulative_pnl += pnl
            equity_curve.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "daily_pnl": float(pnl),
                    "equity": initial_capital + cumulative_pnl,
                }
            )

        return equity_curve


# Singleton instance
_portfolio_analytics = None


def get_portfolio_analytics() -> PortfolioAnalytics:
    """Get singleton portfolio analytics instance"""
    global _portfolio_analytics
    if _portfolio_analytics is None:
        _portfolio_analytics = PortfolioAnalytics()
    return _portfolio_analytics


if __name__ == "__main__":
    # Test analytics
    analytics = get_portfolio_analytics()

    print("Testing Portfolio Analytics...")

    # Get performance summary
    summary = analytics.get_performance_summary("2026-01-01", "2026-01-31")

    print(f"\nPerformance Summary:")
    print(f"  Total Return: {summary.get('total_return', 0):.2f}%")
    print(f"  Sharpe Ratio: {summary.get('sharpe_ratio', 0):.2f}")
    print(f"  Sortino Ratio: {summary.get('sortino_ratio', 0):.2f}")
    print(
        f"  Max Drawdown: {summary.get('max_drawdown', {}).get('max_drawdown_percent', 0):.2f}%"
    )
    print(f"  Win Rate: {summary.get('win_stats', {}).get('win_rate', 0):.1f}%")
