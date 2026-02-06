#!/usr/bin/env python3
"""
Backtest Engine - VectorBT-based backtesting for stocks and options
Supports multiple strategies with portfolio management and comprehensive metrics
"""

import sqlite3
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from datetime import datetime
import json

try:
    import vectorbt as vbt
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning(
        "vectorbt not installed. Backtesting functionality will be limited. Install with: pip install vectorbt[full]"
    )
    vbt = None

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DB_PATH = "market_data.db"

# Common default parameters
DEFAULT_BACKTEST_PARAMS = {
    "init_cash": 100000,  # Initial capital in rupees
    "commission": 0.0005,  # 0.05% commission (Upstox typical)
    "slippage": 0.001,  # 0.1% slippage
    "use_log_returns": False,  # Use arithmetic vs log returns
    "freq": "D",  # Daily frequency
}


@dataclass
class BacktestResult:
    """Container for backtest results"""

    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    init_cash: float
    final_value: float
    total_return: float  # percentage
    cagr: float  # Compound annual growth rate
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    win_rate: float  # percentage
    total_trades: int
    duration_days: int

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "strategy": self.strategy_name,
            "symbol": self.symbol,
            "period": f"{self.start_date} to {self.end_date}",
            "init_cash": self.init_cash,
            "final_value": round(self.final_value, 2),
            "total_return_pct": round(self.total_return * 100, 2),
            "cagr_pct": round(self.cagr * 100, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 3),
            "sortino_ratio": round(self.sortino_ratio, 3),
            "calmar_ratio": round(self.calmar_ratio, 3),
            "max_drawdown_pct": round(self.max_drawdown * 100, 2),
            "win_rate_pct": round(self.win_rate * 100, 2),
            "trades": self.total_trades,
            "duration_days": self.duration_days,
        }


@dataclass
class Signal:
    """Buy/sell signal container"""

    timestamp: int
    action: str  # 'BUY', 'SELL', 'HOLD'
    price: float
    quantity: int = 1
    metadata: Dict = None  # Strategy-specific metadata


class BaseStrategy:
    """Base class for all trading strategies"""

    def __init__(self, name: str, params: Dict = None):
        self.name = name
        self.params = params or {}

    def generate_signals(self, ohlcv_data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate buy/sell signals from OHLCV data
        Returns DataFrame with 'signal' column: 1=buy, -1=sell, 0=hold
        """
        raise NotImplementedError("Subclass must implement generate_signals()")

    def validate_data(self, ohlcv_data: pd.DataFrame) -> bool:
        """Validate required columns exist"""
        required = ["open", "high", "low", "close", "volume"]
        return all(col in ohlcv_data.columns for col in required)


class SMAStrategy(BaseStrategy):
    """Simple Moving Average crossover strategy"""

    def __init__(self, params: Dict = None):
        defaults = {
            "fast_period": 20,
            "slow_period": 50,
        }
        merged_params = {**defaults, **(params or {})}
        super().__init__("SMA Crossover", merged_params)

    def generate_signals(self, ohlcv_data: pd.DataFrame) -> pd.DataFrame:
        """Generate signals when fast MA crosses slow MA"""
        if not self.validate_data(ohlcv_data):
            logger.error("Invalid OHLCV data columns")
            return None

        df = ohlcv_data.copy()
        fast_period = self.params["fast_period"]
        slow_period = self.params["slow_period"]

        df["sma_fast"] = df["close"].rolling(window=fast_period).mean()
        df["sma_slow"] = df["close"].rolling(window=slow_period).mean()

        # Generate signals: 1 (buy) when fast > slow, -1 (sell) when fast < slow
        df["signal"] = 0
        df.loc[df["sma_fast"] > df["sma_slow"], "signal"] = 1
        df.loc[df["sma_fast"] < df["sma_slow"], "signal"] = -1

        # Generate trading signals (buy/sell on crossover)
        df["trade_signal"] = 0
        df["trade_signal"] = df["signal"].diff()

        return df[["close", "signal", "trade_signal"]]


class RSIStrategy(BaseStrategy):
    """RSI (Relative Strength Index) mean-reversion strategy"""

    def __init__(self, params: Dict = None):
        defaults = {
            "rsi_period": 14,
            "oversold_threshold": 30,
            "overbought_threshold": 70,
        }
        merged_params = {**defaults, **(params or {})}
        super().__init__("RSI Mean Reversion", merged_params)

    def generate_signals(self, ohlcv_data: pd.DataFrame) -> pd.DataFrame:
        """Generate signals based on RSI oversold/overbought"""
        if not self.validate_data(ohlcv_data):
            logger.error("Invalid OHLCV data columns")
            return None

        df = ohlcv_data.copy()
        rsi_period = self.params["rsi_period"]
        oversold = self.params["oversold_threshold"]
        overbought = self.params["overbought_threshold"]

        # Calculate RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

        # Generate signals
        df["signal"] = 0
        df.loc[df["rsi"] < oversold, "signal"] = 1  # Buy oversold
        df.loc[df["rsi"] > overbought, "signal"] = -1  # Sell overbought

        # Trading signals on threshold crossovers
        df["trade_signal"] = 0
        df["trade_signal"] = df["signal"].diff()

        return df[["close", "signal", "trade_signal", "rsi"]]


class SimpleOptionSpreadStrategy(BaseStrategy):
    """Bull call spread strategy for options"""

    def __init__(self, params: Dict = None):
        defaults = {
            "long_strike_offset": -2,  # 2 strikes below current
            "short_strike_offset": 0,  # ATM
            "entry_days_to_expiry": 7,  # Enter 7 days before expiry
        }
        merged_params = {**defaults, **(params or {})}
        super().__init__("Bull Call Spread", merged_params)

    def generate_signals(self, ohlcv_data: pd.DataFrame) -> pd.DataFrame:
        """Generate entry/exit signals for bull call spread"""
        # Placeholder - full implementation needs additional strike data
        logger.warning(
            "Bull call spread strategy requires strike data not yet implemented"
        )
        return None


class BacktestEngine:
    """Main backtesting engine"""

    def __init__(self, params: Dict = None):
        self.params = {**DEFAULT_BACKTEST_PARAMS, **(params or {})}
        self.results = []

    def load_candle_data(
        self,
        symbol: str,
        timeframe: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Optional[pd.DataFrame]:
        """Load candle data from database"""
        try:
            conn = sqlite3.connect(DB_PATH)

            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM candles_new
                WHERE symbol = ? AND timeframe = ?
            """
            params = [symbol, timeframe]

            if start_date:
                start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
                query += " AND timestamp >= ?"
                params.append(start_ts)

            if end_date:
                end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
                query += " AND timestamp <= ?"
                params.append(end_ts)

            query += " ORDER BY timestamp ASC"

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            if df.empty:
                logger.error(f"No data found for {symbol} {timeframe}")
                return None

            # Convert timestamp to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
            df.set_index("timestamp", inplace=True)

            logger.info(
                f"✓ Loaded {len(df)} candles for {symbol} from {df.index[0].date()} to {df.index[-1].date()}"
            )
            return df

        except Exception as e:
            logger.error(f"✗ Failed to load candle data: {e}")
            return None

    def run_backtest(
        self,
        symbol: str,
        strategy: BaseStrategy,
        timeframe: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Optional[BacktestResult]:
        """
        Run backtest for a single symbol with given strategy
        Returns BacktestResult with comprehensive metrics
        """
        # Load data
        data = self.load_candle_data(symbol, timeframe, start_date, end_date)
        if data is None or data.empty:
            return None

        logger.info(f"\nRunning {strategy.name} backtest for {symbol}...")

        # Generate signals
        signals_df = strategy.generate_signals(data)
        if signals_df is None or signals_df.empty:
            logger.error(f"Failed to generate signals for {symbol}")
            return None

        # Merge signals with data
        backtest_data = data.copy()
        backtest_data["signal"] = signals_df["signal"]
        backtest_data["trade_signal"] = signals_df["trade_signal"]

        # Use vectorbt for portfolio simulation
        try:
            # Create entries and exits based on signals
            entries = backtest_data["trade_signal"] == 1
            exits = backtest_data["trade_signal"] == -1

            # Run portfolio
            pf = vbt.Portfolio.from_signals(
                close=backtest_data["close"],
                entries=entries,
                exits=exits,
                init_cash=self.params["init_cash"],
                fees=self.params["commission"],
                freq=self.params["freq"],
            )

            # Extract metrics
            total_return = pf.total_return()
            sharpe_ratio = pf.sharpe_ratio()
            sortino_ratio = pf.sortino_ratio()
            calmar_ratio = pf.calmar_ratio()
            max_drawdown = pf.max_drawdown()
            win_rate = pf.win_rate if hasattr(pf, "win_rate") else 0

            # Calculate CAGR
            duration_years = (
                backtest_data.index[-1] - backtest_data.index[0]
            ).days / 365.25
            if duration_years > 0:
                cagr = (pf.final_value() / self.params["init_cash"]) ** (
                    1 / duration_years
                ) - 1
            else:
                cagr = 0

            # Count trades
            total_trades = int(entries.sum() + exits.sum())

            result = BacktestResult(
                strategy_name=strategy.name,
                symbol=symbol,
                start_date=backtest_data.index[0].strftime("%Y-%m-%d"),
                end_date=backtest_data.index[-1].strftime("%Y-%m-%d"),
                init_cash=self.params["init_cash"],
                final_value=pf.final_value(),
                total_return=total_return,
                cagr=cagr,
                sharpe_ratio=sharpe_ratio if not np.isnan(sharpe_ratio) else 0,
                sortino_ratio=sortino_ratio if not np.isnan(sortino_ratio) else 0,
                calmar_ratio=calmar_ratio if not np.isnan(calmar_ratio) else 0,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                total_trades=total_trades,
                duration_days=(backtest_data.index[-1] - backtest_data.index[0]).days,
            )

            self.results.append(result)

            logger.info(f"✓ Backtest complete:")
            logger.info(
                f"  Return: {result.total_return*100:.2f}% | Sharpe: {result.sharpe_ratio:.2f} | Max DD: {result.max_drawdown*100:.2f}%"
            )
            logger.info(
                f"  Trades: {result.total_trades} | Win Rate: {result.win_rate*100:.1f}%"
            )

            return result

        except Exception as e:
            logger.error(f"✗ Backtest execution failed: {e}")
            import traceback

            traceback.print_exc()
            return None

    def run_backtest_batch(
        self,
        symbols: List[str],
        strategy: BaseStrategy,
        timeframe: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[BacktestResult]:
        """Run backtest for multiple symbols"""
        results = []

        for symbol in symbols:
            result = self.run_backtest(
                symbol, strategy, timeframe, start_date, end_date
            )
            if result:
                results.append(result)

        return results

    def print_results_summary(self):
        """Print summary of all backtest results"""
        if not self.results:
            logger.warning("No backtest results to display")
            return

        logger.info(f"\n{'='*80}")
        logger.info("BACKTEST SUMMARY")
        logger.info(f"{'='*80}")

        for result in self.results:
            logger.info(f"\n{result.strategy_name} - {result.symbol}")
            logger.info(
                f"  Period: {result.start_date} to {result.end_date} ({result.duration_days} days)"
            )
            logger.info(f"  Initial Cash: ₹{result.init_cash:,.0f}")
            logger.info(f"  Final Value: ₹{result.final_value:,.0f}")
            logger.info(f"  Total Return: {result.total_return*100:.2f}%")
            logger.info(f"  CAGR: {result.cagr*100:.2f}%")
            logger.info(f"  Sharpe Ratio: {result.sharpe_ratio:.3f}")
            logger.info(f"  Sortino Ratio: {result.sortino_ratio:.3f}")
            logger.info(f"  Calmar Ratio: {result.calmar_ratio:.3f}")
            logger.info(f"  Max Drawdown: {result.max_drawdown*100:.2f}%")
            logger.info(f"  Win Rate: {result.win_rate*100:.1f}%")
            logger.info(f"  Total Trades: {result.total_trades}")

        logger.info(f"{'='*80}\n")

    def export_results(self, filepath: str):
        """Export backtest results to JSON"""
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "backtest_params": self.params,
                "results": [r.to_dict() for r in self.results],
            }

            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"✓ Results exported to {filepath}")

        except Exception as e:
            logger.error(f"✗ Failed to export results: {e}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Run backtests with various strategies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backtest INFY with SMA strategy
  python3 scripts/backtest_engine.py --symbol INFY --strategy SMA
  
  # Backtest multiple stocks with RSI strategy
  python3 scripts/backtest_engine.py --symbols INFY,TCS,RELIANCE --strategy RSI
  
  # Backtest with custom parameters
  python3 scripts/backtest_engine.py --symbol INFY --strategy SMA \\
    --fast-period 10 --slow-period 30
  
  # Backtest with date range
  python3 scripts/backtest_engine.py --symbol INFY --strategy SMA \\
    --start 2024-01-01 --end 2025-01-31
        """,
    )

    parser.add_argument(
        "--symbol", type=str, help="Single symbol to backtest (e.g., INFY)"
    )

    parser.add_argument(
        "--symbols",
        type=str,
        help="Multiple symbols comma-separated (e.g., INFY,TCS,RELIANCE)",
    )

    parser.add_argument(
        "--strategy",
        type=str,
        choices=["SMA", "RSI"],
        default="SMA",
        help="Strategy to use (default: SMA)",
    )

    parser.add_argument(
        "--timeframe",
        type=str,
        default="1d",
        choices=["1m", "5m", "15m", "30m", "1h", "1d"],
        help="Candle timeframe (default: 1d)",
    )

    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")

    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")

    parser.add_argument(
        "--init-cash", type=float, default=100000, help="Initial cash (default: 100000)"
    )

    # Strategy-specific parameters
    parser.add_argument(
        "--fast-period", type=int, default=20, help="SMA fast period (default: 20)"
    )

    parser.add_argument(
        "--slow-period", type=int, default=50, help="SMA slow period (default: 50)"
    )

    parser.add_argument(
        "--rsi-period", type=int, default=14, help="RSI period (default: 14)"
    )

    parser.add_argument("--export", type=str, help="Export results to JSON file")

    args = parser.parse_args()

    # Determine symbols
    symbols = []
    if args.symbol:
        symbols = [args.symbol]
    elif args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",")]
    else:
        parser.error("Must specify --symbol or --symbols")

    # Create strategy
    if args.strategy == "SMA":
        strategy_params = {
            "fast_period": args.fast_period,
            "slow_period": args.slow_period,
        }
        strategy = SMAStrategy(strategy_params)
    elif args.strategy == "RSI":
        strategy_params = {
            "rsi_period": args.rsi_period,
        }
        strategy = RSIStrategy(strategy_params)

    # Create engine and run backtest
    engine_params = {
        "init_cash": args.init_cash,
    }
    engine = BacktestEngine(engine_params)

    results = engine.run_backtest_batch(
        symbols, strategy, args.timeframe, args.start, args.end
    )

    # Print and export results
    engine.print_results_summary()

    if args.export:
        engine.export_results(args.export)

    return 0 if results else 1


if __name__ == "__main__":
    exit(main())
