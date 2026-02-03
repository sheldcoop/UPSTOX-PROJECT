"""
Strategy Backtesting Engine
Test option strategies on historical data with P&L simulation
"""

import sys
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class OptionLeg:
    """Represents one leg of an option strategy"""

    def __init__(
        self, option_type: str, action: str, strike: float, premium: float, qty: int = 1
    ):
        self.option_type = option_type  # CALL or PUT
        self.action = action  # BUY or SELL
        self.strike = strike
        self.premium = premium
        self.qty = qty

    def calculate_pnl(self, underlying_price: float) -> float:
        """Calculate P&L at expiry"""
        if self.option_type == "CALL":
            intrinsic = max(0, underlying_price - self.strike)
        else:  # PUT
            intrinsic = max(0, self.strike - underlying_price)

        # For BUY: P&L = (intrinsic - premium) * qty
        # For SELL: P&L = (premium - intrinsic) * qty
        if self.action == "BUY":
            return (intrinsic - self.premium) * self.qty
        else:  # SELL
            return (self.premium - intrinsic) * self.qty


class BacktestStrategy:
    """Strategy configuration for backtesting"""

    def __init__(self, name: str, legs: List[OptionLeg], entry_price: float):
        self.name = name
        self.legs = legs
        self.entry_price = entry_price
        self.entry_cost = sum(
            leg.premium * leg.qty * (1 if leg.action == "BUY" else -1) for leg in legs
        )

    def calculate_pnl(self, exit_price: float) -> float:
        """Calculate total P&L at exit"""
        return sum(leg.calculate_pnl(exit_price) for leg in self.legs)

    def get_max_profit(self, price_range: tuple) -> tuple:
        """Find max profit and price"""
        max_pnl = -float("inf")
        max_price = 0

        for price in np.linspace(price_range[0], price_range[1], 1000):
            pnl = self.calculate_pnl(price)
            if pnl > max_pnl:
                max_pnl = pnl
                max_price = price

        return max_pnl, max_price

    def get_max_loss(self, price_range: tuple) -> tuple:
        """Find max loss and price"""
        max_loss = float("inf")
        loss_price = 0

        for price in np.linspace(price_range[0], price_range[1], 1000):
            pnl = self.calculate_pnl(price)
            if pnl < max_loss:
                max_loss = pnl
                loss_price = price

        return max_loss, loss_price

    def find_breakevens(self, price_range: tuple) -> List[float]:
        """Find breakeven points"""
        breakevens = []

        prices = np.linspace(price_range[0], price_range[1], 10000)
        pnls = [self.calculate_pnl(p) for p in prices]

        for i in range(len(pnls) - 1):
            if (pnls[i] < 0 and pnls[i + 1] >= 0) or (pnls[i] >= 0 and pnls[i + 1] < 0):
                breakevens.append(prices[i])

        return breakevens


class Backtester:
    """Backtesting engine for option strategies"""

    def __init__(self):
        self.results = []

    def run_backtest(
        self,
        strategy: BacktestStrategy,
        historical_data: pd.DataFrame,
        entry_date: str,
        exit_date: str,
    ) -> Dict:
        """
        Run backtest on historical data

        Args:
            strategy: Strategy to test
            historical_data: DataFrame with columns ['date', 'open', 'high', 'low', 'close']
            entry_date: Entry date (YYYY-MM-DD)
            exit_date: Exit date (YYYY-MM-DD)

        Returns:
            Backtest results dictionary
        """
        try:
            # Filter data for backtest period
            historical_data["date"] = pd.to_datetime(historical_data["date"])
            backtest_data = historical_data[
                (historical_data["date"] >= entry_date)
                & (historical_data["date"] <= exit_date)
            ].copy()

            if backtest_data.empty:
                logger.error(f"No data found for period {entry_date} to {exit_date}")
                return {"error": "No data available for this period"}

            # Entry and exit prices
            entry_price = backtest_data.iloc[0]["close"]
            exit_price = backtest_data.iloc[-1]["close"]

            # Calculate P&L
            pnl = strategy.calculate_pnl(exit_price)
            pnl_percent = (
                (pnl / abs(strategy.entry_cost)) * 100
                if strategy.entry_cost != 0
                else 0
            )

            # Track daily P&L
            daily_pnl = []
            for _, row in backtest_data.iterrows():
                daily_pnl.append(
                    {
                        "date": row["date"].strftime("%Y-%m-%d"),
                        "price": row["close"],
                        "pnl": strategy.calculate_pnl(row["close"]),
                    }
                )

            # Calculate statistics
            min_pnl = min(d["pnl"] for d in daily_pnl)
            max_pnl = max(d["pnl"] for d in daily_pnl)

            # Price range for analysis
            price_range = (
                backtest_data["low"].min() * 0.95,
                backtest_data["high"].max() * 1.05,
            )

            max_profit, max_profit_price = strategy.get_max_profit(price_range)
            max_loss, max_loss_price = strategy.get_max_loss(price_range)
            breakevens = strategy.find_breakevens(price_range)

            result = {
                "strategy_name": strategy.name,
                "entry_date": entry_date,
                "exit_date": exit_date,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "entry_cost": strategy.entry_cost,
                "final_pnl": pnl,
                "pnl_percent": pnl_percent,
                "min_pnl_during_period": min_pnl,
                "max_pnl_during_period": max_pnl,
                "max_profit_possible": max_profit,
                "max_profit_at_price": max_profit_price,
                "max_loss_possible": max_loss,
                "max_loss_at_price": max_loss_price,
                "breakeven_points": breakevens,
                "days_held": len(backtest_data),
                "daily_pnl": daily_pnl,
                "win": pnl > 0,
            }

            self.results.append(result)
            logger.info(
                f"Backtest complete: {strategy.name} | P&L: ₹{pnl:.2f} ({pnl_percent:.2f}%)"
            )

            return result

        except Exception as e:
            logger.error(f"Error in backtest: {e}", exc_info=True)
            return {"error": str(e)}

    def run_multiple_backtests(
        self,
        strategy: BacktestStrategy,
        historical_data: pd.DataFrame,
        start_date: str,
        end_date: str,
        hold_days: int = 7,
    ) -> List[Dict]:
        """
        Run multiple backtests with rolling window

        Args:
            strategy: Strategy to test
            historical_data: Historical price data
            start_date: Overall start date
            end_date: Overall end date
            hold_days: Days to hold each position

        Returns:
            List of backtest results
        """
        results = []

        historical_data["date"] = pd.to_datetime(historical_data["date"])
        data = (
            historical_data[
                (historical_data["date"] >= start_date)
                & (historical_data["date"] <= end_date)
            ]
            .copy()
            .reset_index(drop=True)
        )

        # Rolling window backtests
        for i in range(0, len(data) - hold_days, hold_days):
            entry_idx = i
            exit_idx = min(i + hold_days, len(data) - 1)

            entry_date = data.iloc[entry_idx]["date"].strftime("%Y-%m-%d")
            exit_date = data.iloc[exit_idx]["date"].strftime("%Y-%m-%d")

            result = self.run_backtest(strategy, historical_data, entry_date, exit_date)
            if "error" not in result:
                results.append(result)

        # Calculate aggregate statistics
        if results:
            total_trades = len(results)
            winning_trades = sum(1 for r in results if r["win"])
            win_rate = (winning_trades / total_trades) * 100

            avg_pnl = np.mean([r["final_pnl"] for r in results])
            total_pnl = sum(r["final_pnl"] for r in results)

            logger.info(
                f"Backtest summary: {total_trades} trades | Win rate: {win_rate:.1f}% | Total P&L: ₹{total_pnl:.2f}"
            )

            return {
                "individual_results": results,
                "summary": {
                    "total_trades": total_trades,
                    "winning_trades": winning_trades,
                    "losing_trades": total_trades - winning_trades,
                    "win_rate": win_rate,
                    "avg_pnl": avg_pnl,
                    "total_pnl": total_pnl,
                    "best_trade": max(results, key=lambda x: x["final_pnl"]),
                    "worst_trade": min(results, key=lambda x: x["final_pnl"]),
                },
            }

        return {"error": "No valid backtests completed"}


# Example strategies
def create_iron_condor(underlying_price: float) -> BacktestStrategy:
    """Create Iron Condor strategy"""
    legs = [
        OptionLeg("PUT", "BUY", underlying_price - 200, 30, 50),
        OptionLeg("PUT", "SELL", underlying_price - 100, 60, 50),
        OptionLeg("CALL", "SELL", underlying_price + 100, 60, 50),
        OptionLeg("CALL", "BUY", underlying_price + 200, 30, 50),
    ]
    return BacktestStrategy("Iron Condor", legs, underlying_price)


def create_bull_call_spread(underlying_price: float) -> BacktestStrategy:
    """Create Bull Call Spread strategy"""
    legs = [
        OptionLeg("CALL", "BUY", underlying_price, 120, 50),
        OptionLeg("CALL", "SELL", underlying_price + 200, 60, 50),
    ]
    return BacktestStrategy("Bull Call Spread", legs, underlying_price)


if __name__ == "__main__":
    # Test backtesting engine
    print("Testing Backtesting Engine...")

    # Create mock historical data
    dates = pd.date_range("2026-01-01", "2026-01-31", freq="D")
    prices = 21800 + np.cumsum(np.random.randn(len(dates)) * 50)

    historical_data = pd.DataFrame(
        {
            "date": dates,
            "open": prices + np.random.randn(len(dates)) * 10,
            "high": prices + abs(np.random.randn(len(dates)) * 20),
            "low": prices - abs(np.random.randn(len(dates)) * 20),
            "close": prices,
        }
    )

    # Create strategy
    strategy = create_iron_condor(21800)

    # Run backtest
    backtester = Backtester()
    result = backtester.run_backtest(
        strategy, historical_data, "2026-01-01", "2026-01-07"
    )

    print(f"\nBacktest Result:")
    print(f"  Strategy: {result.get('strategy_name')}")
    print(f"  P&L: ₹{result.get('final_pnl', 0):.2f}")
    print(f"  P&L %: {result.get('pnl_percent', 0):.2f}%")
    print(f"  Win: {result.get('win')}")
    print(f"  Breakevens: {result.get('breakeven_points', [])}")
