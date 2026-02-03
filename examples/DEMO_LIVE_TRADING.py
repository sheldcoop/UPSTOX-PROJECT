#!/usr/bin/env python3
"""
Comprehensive Live Trading Demo

Demonstrates all 5 new live trading features:
1. Websocket Real-time Quote Streaming
2. Order Placement & Management
3. GTT Orders (Good-Till-Triggered)
4. Account & Margin Monitoring
5. Market Depth Analysis

Real-world trading workflows with detailed examples.
"""

import os
from datetime import datetime

# Color codes for terminal output
BOLD = "\033[1m"
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
END = "\033[0m"


def print_section(title, level=1):
    """Print formatted section title."""
    if level == 1:
        print(f"\n{BOLD}{'=' * 100}{END}")
        print(f"{BOLD}{title:^100}{END}")
        print(f"{BOLD}{'=' * 100}{END}\n")
    elif level == 2:
        print(f"\n{BLUE}{title}{END}")
        print(f"{BLUE}{'-' * len(title)}{END}")


def demo_websocket_streaming():
    """Demo: Real-time Quote Streaming."""
    print_section("FEATURE 1: WEBSOCKET REAL-TIME QUOTE STREAMING", 1)

    print(
        f"""
{GREEN}✨ OVERVIEW{END}
Real-time tick-by-tick market data directly from Upstox websocket.
Ideal for live price monitoring, algorithmic trading, and decision-making.

{YELLOW}KEY CAPABILITIES:{END}
  ✓ Subscribe to multiple symbols simultaneously
  ✓ Auto-reconnect on connection loss
  ✓ Real-time bid-ask data with volumes
  ✓ Persistent database storage of all ticks
  ✓ Live display with continuous updates
  ✓ Historical tick analysis and queries

{YELLOW}USE CASES:{END}
  1. Live price monitoring for risk management
  2. Real-time entry/exit signal generation
  3. Liquidity analysis during market hours
  4. Speed-based trading strategies
  5. Market microstructure analysis

{BOLD}COMMAND EXAMPLES:{END}
"""
    )

    examples = [
        (
            "Start streaming for NIFTY",
            "python scripts/websocket_quote_streamer.py --symbols NIFTY --duration 300",
        ),
        (
            "Stream multiple symbols live display",
            "python scripts/websocket_quote_streamer.py --symbols NIFTY,BANKNIFTY,INFY --live-display --duration 120",
        ),
        (
            "Query tick history",
            "python scripts/websocket_quote_streamer.py --query-ticks NIFTY --limit 100",
        ),
        (
            "View streaming statistics",
            "python scripts/websocket_quote_streamer.py --stats",
        ),
    ]

    for desc, cmd in examples:
        print(f"  📌 {desc}")
        print(f"     {cmd}\n")

    print(
        f"""
{BOLD}DATABASE STORAGE:{END}
All ticks automatically stored in `quote_ticks` table:
  • Timestamp, symbol, LTP, bid/ask prices and quantities
  • Volume, open interest, daily highs/lows
  • Auto-indexed for fast queries

{BOLD}WORKFLOW INTEGRATION:{END}
➜ Start websocket streaming for NIFTY
➜ Get real-time quotes every second
➜ Query bid-ask spread analysis
➜ Monitor for entry conditions
➜ Trigger orders when conditions met (see Feature 2)
"""
    )


def demo_order_placement():
    """Demo: Order Placement & Management."""
    print_section("FEATURE 2: ORDER PLACEMENT & MANAGEMENT", 1)

    print(
        f"""
{GREEN}✨ OVERVIEW{END}
Complete order lifecycle management - place, modify, cancel, and track orders.
Supports market, limit, and stop-loss orders with full API integration.

{YELLOW}KEY CAPABILITIES:{END}
  ✓ Place market and limit orders
  ✓ Modify price and quantity
  ✓ Cancel pending orders
  ✓ Get real-time order status
  ✓ Bracket orders (entry + stop loss + target)
  ✓ Full order history tracking
  ✓ Order updates and status notifications

{YELLOW}USE CASES:{END}
  1. Execute trades based on technical signals
  2. Implement stop-loss automation
  3. Scale in/out positions
  4. Hedging with counter-positions
  5. Portfolio rebalancing

{BOLD}COMMAND EXAMPLES:{END}
"""
    )

    examples = [
        (
            "Place market order to BUY",
            "python scripts/order_manager.py --action place --symbol INFY --side BUY --qty 1 --type MARKET",
        ),
        (
            "Place limit order to SELL",
            "python scripts/order_manager.py --action place --symbol NIFTY --side SELL --qty 25 --type LIMIT --price 23500",
        ),
        (
            "Modify order price",
            "python scripts/order_manager.py --action modify --order-id ORD123 --new-price 1750",
        ),
        (
            "Cancel pending order",
            "python scripts/order_manager.py --action cancel --order-id ORD123",
        ),
        (
            "Get order status",
            "python scripts/order_manager.py --action status --order-id ORD123",
        ),
        (
            "Place bracket order",
            "python scripts/order_manager.py --action place-bracket --symbol INFY --qty 1 --entry-price 1800 --stop-loss 1750 --target 1850",
        ),
        (
            "List all active orders",
            "python scripts/order_manager.py --action list-active",
        ),
        (
            "Get order history",
            "python scripts/order_manager.py --action history --limit 50",
        ),
    ]

    for desc, cmd in examples:
        print(f"  📌 {desc}")
        print(f"     {cmd}\n")

    print(
        f"""
{BOLD}DATABASE STORAGE:{END}
All orders stored in `orders` and `bracket_orders` tables:
  • Order ID, symbol, side, quantity, price
  • Status tracking, fills, pending quantity
  • Timestamps and product type
  • Bracket order relationships

{BOLD}WORKFLOW INTEGRATION:{END}
➜ Monitor live prices (Feature 1)
➜ When entry signal detected
➜ Place market order immediately
➜ Set stop-loss at key level
➜ Set target for profit-taking
➜ Monitor order status in real-time
➜ Modify if needed (price/quantity)
"""
    )


def demo_gtt_orders():
    """Demo: GTT Orders (Good-Till-Triggered)."""
    print_section("FEATURE 3: GTT ORDERS (GOOD-TILL-TRIGGERED)", 1)

    print(
        f"""
{GREEN}✨ OVERVIEW{END}
Conditional orders that automatically trigger when price reaches specified levels.
Perfect for 'set and forget' trading strategies - no manual monitoring needed.

{YELLOW}KEY CAPABILITIES:{END}
  ✓ Create conditional orders with trigger prices
  ✓ Conditions: GTE (>=), LTE (<=), GT (>), LT (<)
  ✓ Automatic order execution on trigger
  ✓ Modify trigger conditions
  ✓ Cancel GTT orders
  ✓ GTT order history and status
  ✓ Real-time monitoring and alerts

{YELLOW}USE CASES:{END}
  1. Buy limit orders when price drops
  2. Sell at predetermined targets
  3. Trailing stop-loss automation
  4. Range breakout trading
  5. Multi-level entry strategies

{BOLD}COMMAND EXAMPLES:{END}
"""
    )

    examples = [
        (
            "Create GTT: Buy when price falls",
            "python scripts/gtt_orders_manager.py --action create --symbol INFY --quantity 1 --trigger-price 1750 --condition LTE --order-type LIMIT --order-price 1750",
        ),
        (
            "Create GTT: Sell at target",
            "python scripts/gtt_orders_manager.py --action create --symbol NIFTY --quantity 25 --trigger-price 23500 --condition GTE --order-type MARKET",
        ),
        (
            "Modify GTT trigger price",
            "python scripts/gtt_orders_manager.py --action modify --gtt-id GTT_ABC --new-trigger-price 1800",
        ),
        (
            "Cancel GTT order",
            "python scripts/gtt_orders_manager.py --action cancel --gtt-id GTT_ABC",
        ),
        ("List all GTT orders", "python scripts/gtt_orders_manager.py --action list"),
        (
            "Get GTT details",
            "python scripts/gtt_orders_manager.py --action details --gtt-id GTT_ABC",
        ),
        (
            "Monitor GTT orders (auto-trigger checking)",
            "python scripts/gtt_orders_manager.py --action monitor --check-interval 5 --duration 3600",
        ),
        (
            "Get GTT history",
            "python scripts/gtt_orders_manager.py --action history --limit 50",
        ),
    ]

    for desc, cmd in examples:
        print(f"  📌 {desc}")
        print(f"     {cmd}\n")

    print(
        f"""
{BOLD}DATABASE STORAGE:{END}
All GTT orders stored in `gtt_orders` and `gtt_triggers` tables:
  • GTT ID, symbol, quantity, trigger price
  • Condition, order type, execution price
  • Status, trigger events, timestamps

{BOLD}WORKFLOW INTEGRATION:{END}
➜ Setup GTT order at market close
➜ Set buy trigger: price <= 1750
➜ Set sell trigger: price >= 1850
➜ Monitor system throughout the day
➜ Orders trigger automatically
➜ Modify triggers as market evolves
➜ Cancel if conditions no longer apply
"""
    )


def demo_account_margin():
    """Demo: Account & Margin Monitoring."""
    print_section("FEATURE 4: ACCOUNT & MARGIN MONITORING", 1)

    print(
        f"""
{GREEN}✨ OVERVIEW{END}
Real-time account information including margin, buying power, and balance.
Critical for risk management and position sizing in live trading.

{YELLOW}KEY CAPABILITIES:{END}
  ✓ Account profile (user, email, client ID)
  ✓ Real-time margin info (available, used, required)
  ✓ Buying power calculation for each segment
  ✓ Account balance and cash position
  ✓ Margin utilization percentage
  ✓ Account alerts (low margin, liquidation risk)
  ✓ Historical margin tracking

{YELLOW}USE CASES:{END}
  1. Prevent over-leveraging positions
  2. Calculate maximum position size
  3. Monitor margin utilization throughout day
  4. Alerts for low margin situations
  5. Portfolio risk assessment

{BOLD}COMMAND EXAMPLES:{END}
"""
    )

    examples = [
        ("Get account profile", "python scripts/account_fetcher.py --action profile"),
        (
            "Get current margin info",
            "python scripts/account_fetcher.py --action margin",
        ),
        (
            "Get buying power for all segments",
            "python scripts/account_fetcher.py --action buying-power",
        ),
        (
            "Get full account summary",
            "python scripts/account_fetcher.py --action summary",
        ),
        ("Get account holdings", "python scripts/account_fetcher.py --action holdings"),
        (
            "View margin history",
            "python scripts/account_fetcher.py --action history --limit 100",
        ),
        (
            "Monitor account real-time",
            "python scripts/account_fetcher.py --action monitor --interval 30 --duration 3600",
        ),
    ]

    for desc, cmd in examples:
        print(f"  📌 {desc}")
        print(f"     {cmd}\n")

    print(
        f"""
{BOLD}KEY METRICS EXPLAINED:{END}

Available Margin:
  • Funds available for trading without liquidation
  • Equity (2x), Commodity (5x), MTF (1x) leverage

Margin Utilization %:
  • (Used / Total) × 100
  • >80% = High risk ⚠️
  • >90% = Critical risk 🚨

Buying Power:
  • Available margin × leverage multiplier
  • Equity: ×2 (intraday), ×1 (delivery)
  • Commodity: ×5 (MCX)
  • MTF: ×1 (margin trading fund)

{BOLD}WORKFLOW INTEGRATION:{END}
➜ Check available buying power at market open
➜ Place order respecting margin limits
➜ Monitor margin utilization during trades
➜ Alert if margin usage > 80%
➜ Cancel or reduce positions if needed
➜ Track margin history for analysis
"""
    )


def demo_market_depth():
    """Demo: Market Depth Analysis."""
    print_section("FEATURE 5: MARKET DEPTH & ORDER BOOK ANALYSIS", 1)

    print(
        f"""
{GREEN}✨ OVERVIEW{END}
Real-time order book data including bid-ask spread, depth levels, and liquidity.
Essential for analyzing market microstructure and finding optimal entry/exit prices.

{YELLOW}KEY CAPABILITIES:{END}
  ✓ Level 1 depth: Top bid/ask with volumes
  ✓ Level 2 depth: 5-10 levels of bid/ask
  ✓ Bid-ask spread analysis
  ✓ Liquidity scoring
  ✓ Order imbalance detection
  ✓ Market depth visualization
  ✓ Spread history tracking

{YELLOW}USE CASES:{END}
  1. Find best entry/exit prices
  2. Detect order imbalance signals
  3. Analyze market depth before large orders
  4. Avoid slippage on market orders
  5. Liquidity-based strategy triggers

{BOLD}COMMAND EXAMPLES:{END}
"""
    )

    examples = [
        (
            "Get Level 1 market depth",
            "python scripts/market_depth_fetcher.py --symbol INFY --action depth --level 1",
        ),
        (
            "Get Level 2 market depth",
            "python scripts/market_depth_fetcher.py --symbol NIFTY --action depth --level 2",
        ),
        (
            "Get bid-ask spread",
            "python scripts/market_depth_fetcher.py --symbol BANKNIFTY --action spread",
        ),
        (
            "Analyze liquidity",
            "python scripts/market_depth_fetcher.py --symbol INFY --action liquidity",
        ),
        (
            "Compare spreads across symbols",
            "python scripts/market_depth_fetcher.py --symbols NIFTY,BANKNIFTY,FINNIFTY --action compare",
        ),
        (
            "View spread history",
            "python scripts/market_depth_fetcher.py --symbol NIFTY --action history --limit 100",
        ),
        (
            "Monitor market depth changes",
            "python scripts/market_depth_fetcher.py --symbol INFY --action monitor --interval 5 --duration 300",
        ),
    ]

    for desc, cmd in examples:
        print(f"  📌 {desc}")
        print(f"     {cmd}\n")

    print(
        f"""
{BOLD}DEPTH METRICS EXPLAINED:{END}

Bid-Ask Spread:
  • Difference between ask and bid prices
  • Tight spread (<0.1%) = Good liquidity
  • Wide spread (>0.5%) = Poor liquidity
  • Indicator of transaction costs

Order Imbalance:
  • Bid volume > Ask volume = Bullish
  • Ask volume > Bid volume = Bearish
  • Equal = Neutral sentiment

Liquidity Score (0-100):
  • Based on volume depth and spread
  • >75 = Excellent liquidity ✓
  • 50-75 = Good liquidity
  • 25-50 = Fair liquidity
  • <25 = Poor liquidity (avoid large orders)

{BOLD}WORKFLOW INTEGRATION:{END}
➜ Check market depth for symbol
➜ Analyze bid-ask spread
➜ Detect order imbalance signal
➜ Place order at favorable price
➜ Monitor spread as price moves
➜ Avoid slippage on large orders
"""
    )


def demo_integrated_workflow():
    """Demo: Complete integrated trading workflow."""
    print_section("INTEGRATED LIVE TRADING WORKFLOW", 1)

    print(
        f"""
{GREEN}✨ REAL-WORLD EXAMPLE: Intraday Trading Setup{END}

This example shows how all 5 features work together for a complete trading system.

{BOLD}SCENARIO: Breakout Trading on NIFTY{END}
Goal: Trade NIFTY's resistance breakout at 23,500 with proper risk management

{YELLOW}STEP 1: PRE-MARKET SETUP (Before 9:15 AM){END}
  1. Check account status
     $ python scripts/account_fetcher.py --action margin
     
     Result: Available margin ₹5,00,000, buying power ₹10,00,000
     ✓ Sufficient for 50-unit position (₹11,75,000 required)

  2. Setup GTT orders for limit entry
     $ python scripts/gtt_orders_manager.py --action create \\
       --symbol NIFTY --quantity 25 --trigger-price 23500 \\
       --condition GTE --order-type LIMIT --order-price 23500
     
     (If price >= 23,500, buy 25 units @ 23,500)

  3. Setup GTT for stop-loss exit
     $ python scripts/gtt_orders_manager.py --action create \\
       --symbol NIFTY --quantity 25 --trigger-price 23400 \\
       --condition LTE --order-type MARKET
     
     (If price <= 23,400, sell 25 units at market)

{YELLOW}STEP 2: MARKET HOURS - REAL-TIME MONITORING (9:15 AM - 3:30 PM){END}
  
  1. Start live price streaming
     $ python scripts/websocket_quote_streamer.py \\
       --symbols NIFTY,BANKNIFTY --live-display --duration 23400
     
     Receive real-time ticks every 100ms
     Monitor bid-ask spread and volume

  2. Monitor order book depth periodically
     $ python scripts/market_depth_fetcher.py \\
       --symbol NIFTY --action liquidity
     
     Check: Liquidity Score, Order Imbalance, Spread
     Avoid placing large orders if spread widens

  3. Monitor GTT orders for triggers
     $ python scripts/gtt_orders_manager.py --action monitor \\
       --check-interval 5 --duration 23400
     
     Watch for automatic trigger execution

{YELLOW}STEP 3: POSITION MANAGEMENT (After GTT Triggers){END}
  
  1. GTT buy order triggered at 23,500
     Database logs: Entry filled at 23,500 for 25 units
     Position P&L starts tracking

  2. Monitor market depth for exit opportunity
     $ python scripts/market_depth_fetcher.py \\
       --symbol NIFTY --action spread
     
     Check bid-ask spread quality
     If price reaches target (23,600), exit

  3. Manual exit if GTT target not triggered
     $ python scripts/order_manager.py --action place \\
       --symbol NIFTY --side SELL --qty 25 \\
       --type LIMIT --price 23600
     
     Place exit limit order

  4. Monitor account margin continuously
     $ python scripts/account_fetcher.py \\
       --action monitor --interval 60 --duration 23400
     
     Alert if margin utilization > 85%

{YELLOW}STEP 4: POST-MARKET ANALYSIS (After 3:30 PM){END}
  
  1. Get order history
     $ python scripts/order_manager.py --action history
     
     Review all executed orders and prices

  2. Get GTT history
     $ python scripts/gtt_orders_manager.py --action history
     
     Review which GTT orders triggered

  3. View P&L
     (Use with portfolio tracking)
     Calculate actual profit/loss vs expected

  4. Analyze spread history
     $ python scripts/market_depth_fetcher.py \\
       --symbol NIFTY --action history
     
     Review spread patterns throughout the day

{BOLD}KEY METRICS FROM THIS WORKFLOW:{END}
  ✓ Entry: 23,500 (GTT triggered)
  ✓ Stop Loss: 23,400 (Set via GTT)
  ✓ Target: 23,600 (Exited)
  ✓ Profit: 100 × 25 = ₹2,500
  ✓ Risk: 100 × 25 = ₹2,500 (1:1 risk-reward)
  ✓ Margin Used: ₹1,17,500
  ✓ Margin Utilization: 23.5%
  ✓ Trade Duration: 2 hours 15 minutes
"""
    )


def main():
    """Run complete demo."""
    print(f"\n{BOLD}{'=' * 100}{END}")
    print(f"{BOLD}UPSTOX LIVE TRADING SYSTEM - COMPREHENSIVE DEMO{END}")
    print(f"{BOLD}{'=' * 100}{END}")
    print(f"\n{BOLD}Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{END}")
    print(f"{BOLD}All 5 Live Trading Features{END}\n")

    demo_websocket_streaming()
    demo_order_placement()
    demo_gtt_orders()
    demo_account_margin()
    demo_market_depth()
    demo_integrated_workflow()

    print_section("FEATURE SUMMARY TABLE", 1)

    summary = [
        ["FEATURE", "PURPOSE", "KEY COMMAND", "DATABASE TABLE"],
        ["-" * 30, "-" * 50, "-" * 50, "-" * 30],
        [
            "Websocket Streaming",
            "Real-time quotes",
            "websocket_quote_streamer.py",
            "quote_ticks",
        ],
        [
            "Order Management",
            "Place/modify/cancel orders",
            "order_manager.py",
            "orders",
        ],
        [
            "GTT Orders",
            "Conditional auto-triggers",
            "gtt_orders_manager.py",
            "gtt_orders",
        ],
        ["Account & Margin", "Risk management", "account_fetcher.py", "margin_history"],
        [
            "Market Depth",
            "Order book analysis",
            "market_depth_fetcher.py",
            "market_depth",
        ],
    ]

    print()
    for row in summary:
        print(f"  {row[0]:30} | {row[1]:50} | {row[2]:50} | {row[3]:30}")

    print(f"\n{BOLD}{'=' * 100}{END}")
    print(f"{BOLD}NEXT STEPS:{END}")
    print(
        f"""
1. Set UPSTOX_ACCESS_TOKEN environment variable:
   export UPSTOX_ACCESS_TOKEN="your_token_here"

2. Start with Market Depth analysis (no position changes):
   python scripts/market_depth_fetcher.py --symbol NIFTY --action spread

3. Monitor account status:
   python scripts/account_fetcher.py --action margin

4. Start websocket streaming:
   python scripts/websocket_quote_streamer.py --symbols NIFTY --duration 300

5. Create GTT orders for automated trading:
   python scripts/gtt_orders_manager.py --action create \\
     --symbol NIFTY --quantity 25 --trigger-price 23500 \\
     --condition GTE --order-type LIMIT --order-price 23500

6. Place manual orders as needed:
   python scripts/order_manager.py --action place \\
     --symbol NIFTY --side BUY --qty 25 --type MARKET

{BOLD}DOCUMENTATION & SCRIPTS:{END}
  • websocket_quote_streamer.py - Real-time quotes
  • order_manager.py - Order management
  • gtt_orders_manager.py - Conditional orders
  • account_fetcher.py - Account & margin
  • market_depth_fetcher.py - Order book analysis
  • LIVE_TRADING_GUIDE.md - Complete guide

{BOLD}SAFETY REMINDERS:{END}
  🔒 Never hardcode tokens in scripts
  🔒 Test with small positions first
  🔒 Always set stop-losses
  🔒 Monitor margin constantly
  🔒 Understand all parameters before executing
  🔒 Verify test orders in SANDBOX mode first

{BOLD}Good luck with your live trading! 🚀{END}
{BOLD}{'=' * 100}{END}
"""
    )


if __name__ == "__main__":
    main()
