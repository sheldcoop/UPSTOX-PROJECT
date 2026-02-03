#!/usr/bin/env python3
"""
run_backtest.py - Complete end-to-end backtesting workflow
Fetch data → Run backtest → Optimize parameters → Save results
"""

import argparse
import logging
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Import our modules
from scripts.backtest_engine import (
    BacktestEngine,
    SMAStrategy,
    RSIStrategy,
    BacktestResult,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_full_workflow(
    symbols: list,
    strategy_name: str,
    strategy_params: dict = None,
    timeframe: str = "1d",
    start_date: str = None,
    end_date: str = None,
    init_cash: float = 100000,
    fetch_data: bool = True,
    export_results: bool = True,
):
    """
    Complete end-to-end workflow:
    1. Fetch candle data from Upstox API
    2. Run backtest with given strategy
    3. Export results
    """

    logger.info("=" * 80)
    logger.info("END-TO-END BACKTESTING WORKFLOW")
    logger.info("=" * 80)

    # Step 1: Fetch data
    if fetch_data:
        logger.info("\n[1] FETCHING DATA FROM UPSTOX API")
        logger.info("-" * 80)

        # Build candle fetcher command
        cmd = [
            "python3",
            "scripts/candle_fetcher.py",
            "--symbols",
            ",".join(symbols),
            "--timeframe",
            timeframe,
            "--delay",
            "0.5",
        ]

        if start_date:
            cmd.extend(["--start", start_date])
        if end_date:
            cmd.extend(["--end", end_date])

        try:
            subprocess.run(cmd, check=True, capture_output=False)
            logger.info(f"✓ Fetched data for {len(symbols)} symbols")
        except subprocess.CalledProcessError:
            logger.warning("⚠ Failed to fetch candle data")
            # Continue anyway - data might already exist

    # Step 2: Run backtest
    logger.info("\n[2] RUNNING BACKTEST")
    logger.info("-" * 80)

    # Create strategy
    if strategy_name == "SMA":
        strategy_params = strategy_params or {"fast_period": 20, "slow_period": 50}
        strategy = SMAStrategy(strategy_params)
    elif strategy_name == "RSI":
        strategy_params = strategy_params or {"rsi_period": 14}
        strategy = RSIStrategy(strategy_params)
    else:
        logger.error(f"Unknown strategy: {strategy_name}")
        return False

    # Create engine
    engine = BacktestEngine({"init_cash": init_cash})

    # Run backtest for each symbol
    results = engine.run_backtest_batch(
        symbols, strategy, timeframe, start_date, end_date
    )

    if not results:
        logger.error("Backtest failed")
        return False

    # Step 3: Print summary
    logger.info("\n[3] RESULTS SUMMARY")
    logger.info("-" * 80)
    engine.print_results_summary()

    # Step 4: Export results
    if export_results:
        logger.info("\n[4] EXPORTING RESULTS")
        logger.info("-" * 80)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"backtest_results_{strategy_name}_{timestamp}.json"

        engine.export_results(output_file)
        logger.info(f"✓ Results saved to {output_file}")

    logger.info("\n" + "=" * 80)
    logger.info("WORKFLOW COMPLETE")
    logger.info("=" * 80 + "\n")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="End-to-end backtesting workflow: Fetch data → Backtest → Export",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COMPLETE WORKFLOW EXAMPLES:

1. Simple backtest (fetch data + run strategy):
   python3 run_backtest.py --symbols INFY,TCS --strategy SMA \\
     --start 2024-01-01 --end 2025-01-31

2. Backtest without fetching new data:
   python3 run_backtest.py --symbols INFY --strategy RSI --no-fetch

3. Run with custom strategy parameters:
   python3 run_backtest.py --symbol INFY --strategy SMA \\
     --fast-period 10 --slow-period 30 --init-cash 500000

4. Full options workflow (chain + history + backtest):
   python3 run_backtest.py --symbols NIFTY \\
     --fetch-option-chain --option-strikes 23300,23400 \\
     --strategy SMA

WORKFLOW STAGES:
  Stage 1: Fetch stock candles from Upstox API (daily/hourly/minute data)
  Stage 2: (Optional) Fetch option chain + historical option candles
  Stage 3: Run backtest with selected strategy
  Stage 4: Print comprehensive metrics (Sharpe, Sortino, drawdown, etc)
  Stage 5: Export results to JSON file
        """,
    )

    # Data fetching arguments
    parser.add_argument(
        "--symbols",
        type=str,
        required=True,
        help="Symbols to backtest (comma-separated: INFY,TCS,RELIANCE)",
    )

    parser.add_argument(
        "--start", type=str, help="Start date (YYYY-MM-DD). Default: 1 year ago"
    )

    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD). Default: today")

    parser.add_argument(
        "--timeframe",
        type=str,
        default="1d",
        choices=["1m", "5m", "15m", "1h", "1d"],
        help="Candle timeframe (default: 1d)",
    )

    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="Skip fetching new data, use existing DB data",
    )

    # Strategy arguments
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["SMA", "RSI"],
        default="SMA",
        help="Strategy to use (default: SMA)",
    )

    parser.add_argument(
        "--fast-period", type=int, default=20, help="SMA fast period (default: 20)"
    )

    parser.add_argument(
        "--slow-period", type=int, default=50, help="SMA slow period (default: 50)"
    )

    parser.add_argument(
        "--rsi-period", type=int, default=14, help="RSI period (default: 14)"
    )

    parser.add_argument(
        "--init-cash",
        type=float,
        default=100000,
        help="Initial capital in rupees (default: 100000)",
    )

    # Option arguments
    parser.add_argument(
        "--fetch-option-chain",
        action="store_true",
        help="Fetch current option chain data",
    )

    parser.add_argument(
        "--fetch-option-history",
        action="store_true",
        help="Fetch historical option candles",
    )

    parser.add_argument(
        "--option-strikes",
        type=str,
        help="Option strikes for history (comma-separated: 23000,23100,23200)",
    )

    parser.add_argument(
        "--option-expiry", type=str, help="Option expiry date (YYYY-MM-DD)"
    )

    # Export arguments
    parser.add_argument(
        "--no-export", action="store_true", help="Skip exporting results to JSON"
    )

    args = parser.parse_args()

    # Parse symbols
    symbols = [s.strip().upper() for s in args.symbols.split(",")]

    # Build strategy params
    strategy_params = {}
    if args.strategy == "SMA":
        strategy_params = {
            "fast_period": args.fast_period,
            "slow_period": args.slow_period,
        }
    elif args.strategy == "RSI":
        strategy_params = {
            "rsi_period": args.rsi_period,
        }

    # Fetch option data if requested
    if args.fetch_option_chain:
        logger.info("\nFetching option chain data...")
        for symbol in symbols:
            cmd = [
                "python3",
                "scripts/option_chain_fetcher.py",
                "--underlying",
                symbol,
                "--delay",
                "1",
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=False)
            except subprocess.CalledProcessError:
                logger.warning(f"Failed to fetch option chain for {symbol}")

    if args.fetch_option_history and args.option_strikes and args.option_expiry:
        logger.info("\nFetching option historical data...")
        for symbol in symbols:
            cmd = [
                "python3",
                "scripts/option_history_fetcher.py",
                "--underlying",
                symbol,
                "--strikes",
                args.option_strikes,
                "--expiry",
                args.option_expiry,
                "--timeframe",
                args.timeframe,
                "--delay",
                "1",
            ]
            if args.start:
                cmd.extend(["--start", args.start])
            if args.end:
                cmd.extend(["--end", args.end])

            try:
                subprocess.run(cmd, check=True, capture_output=False)
            except subprocess.CalledProcessError:
                logger.warning(f"Failed to fetch option history for {symbol}")

    # Run main workflow
    success = run_full_workflow(
        symbols=symbols,
        strategy_name=args.strategy,
        strategy_params=strategy_params,
        timeframe=args.timeframe,
        start_date=args.start,
        end_date=args.end,
        init_cash=args.init_cash,
        fetch_data=not args.no_fetch,
        export_results=not args.no_export,
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
