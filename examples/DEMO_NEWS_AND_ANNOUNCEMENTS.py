#!/usr/bin/env python3
"""
DEMO: News & Corporate Announcements System

Comprehensive demonstration of all news and announcement features:
1. Corporate Announcements Fetcher
2. Economic Calendar Fetcher
3. News Alerts Manager

This demo shows real-world usage patterns and integration workflows.

Author: Upstox Backend Team
Date: 2026-01-31
"""


def print_header(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100 + "\n")


def print_section(section_num: int, title: str):
    """Print section divider."""
    print("\n" + "-" * 100)
    print(f"  SECTION {section_num}: {title}")
    print("-" * 100 + "\n")


def main():
    print_header("📰 NEWS & CORPORATE ANNOUNCEMENTS DEMO")

    print(
        """
This demonstration covers THREE powerful features for staying informed about market-moving events:

1️⃣  CORPORATE ANNOUNCEMENTS - Track company-specific events
2️⃣  ECONOMIC CALENDAR - Monitor macro events affecting markets
3️⃣  NEWS ALERTS - Real-time news monitoring with sentiment analysis

Each feature helps you make better-informed trading decisions by providing:
- Advance notice of volatility-inducing events
- Sentiment analysis for positioning
- Automated alerts for critical news
- Historical tracking for pattern recognition
    """
    )

    # ============================================================================
    # FEATURE 1: CORPORATE ANNOUNCEMENTS
    # ============================================================================

    print_section(1, "CORPORATE ANNOUNCEMENTS FETCHER")

    print(
        """
📊 WHAT IT DOES:
   Tracks company-specific events that directly impact stock prices:
   - Quarterly earnings releases (Q1, Q2, Q3, Q4)
   - Dividend announcements (interim, final)
   - Stock splits and bonus shares
   - Corporate actions (M&A, rights issues, buybacks)
   - Board meetings and regulatory filings
   - AGM/EGM dates

💡 WHY IT MATTERS:
   - Earnings can cause 5-15% price movements in a single day
   - Advance knowledge helps you prepare positions
   - Avoid getting caught in earnings volatility
   - Plan GTT orders around key dates
   - Adjust stop-losses before high-impact events
    """
    )

    print("\n📋 COMMAND EXAMPLES:\n")

    commands_1 = [
        (
            "Get upcoming earnings for INFY",
            "python scripts/corporate_announcements_fetcher.py --action earnings --symbol INFY",
        ),
        (
            "Get all earnings in next 90 days",
            "python scripts/corporate_announcements_fetcher.py --action earnings --days 90",
        ),
        (
            "Get dividend announcements",
            "python scripts/corporate_announcements_fetcher.py --action dividends --symbol TCS",
        ),
        (
            "Get all upcoming events (next 30 days)",
            "python scripts/corporate_announcements_fetcher.py --action upcoming --days 30",
        ),
        (
            "Get only HIGH-IMPACT events",
            "python scripts/corporate_announcements_fetcher.py --action high-impact --days 60",
        ),
        (
            "Set alert 7 days before INFY earnings",
            "python scripts/corporate_announcements_fetcher.py --action set-alert --symbol INFY --announcement-type EARNINGS --days-before 7",
        ),
        (
            "Check pending alerts",
            "python scripts/corporate_announcements_fetcher.py --action check-alerts",
        ),
        (
            "Monitor announcements (check every hour)",
            "python scripts/corporate_announcements_fetcher.py --action monitor --interval 3600",
        ),
    ]

    for i, (desc, cmd) in enumerate(commands_1, 1):
        print(f"{i}. {desc}:")
        print(f"   {cmd}\n")

    print("\n📊 SAMPLE OUTPUT:\n")
    print(
        """
════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
UPCOMING CORPORATE EVENTS
════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
Symbol       | Event Type           | Event Date   | Impact   | Days Away  | Description
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
INFY         | EARNINGS             | 2026-02-10   | 🔴 HIGH  | 10 days    | Q3 FY26 Earnings Release
TCS          | FINAL_DIVIDEND       | 2026-02-05   | 🟡 MEDIUM| 5 days     | Final dividend ₹10/share
RELIANCE     | BOARD_MEETING        | 2026-02-15   | 🟡 MEDIUM| 15 days    | Board meeting - strategic
HDFC         | EARNINGS             | 2026-02-12   | 🔴 HIGH  | 12 days    | Q3 FY26 Results
════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
Total events: 4
    """
    )

    print("\n🎯 REAL-WORLD WORKFLOW:\n")
    print(
        """
SCENARIO: You hold 100 shares of INFY @ ₹1,800

STEP 1: Check earnings date (2 weeks in advance)
   → python scripts/corporate_announcements_fetcher.py --action earnings --symbol INFY
   → Result: INFY earnings on Feb 10, 2026

STEP 2: Set alert 7 days before
   → python scripts/corporate_announcements_fetcher.py --action set-alert --symbol INFY --announcement-type EARNINGS --days-before 7
   → Alert will trigger on Feb 3

STEP 3: When alert fires (Feb 3):
   - Review position size (reduce if needed)
   - Widen stop-loss (earnings volatility)
   - Consider setting GTT sell at resistance
   - Prepare for 5-15% swing

STEP 4: Day before earnings (Feb 9):
   - Check market depth (liquidity)
   - Set bracket order if planning to hold
   - OR exit position to avoid volatility

STEP 5: After earnings (Feb 10):
   - Monitor news sentiment
   - Check actual vs estimated results
   - Decide on re-entry if exited
    """
    )

    # ============================================================================
    # FEATURE 2: ECONOMIC CALENDAR
    # ============================================================================

    print_section(2, "ECONOMIC CALENDAR FETCHER")

    print(
        """
📅 WHAT IT DOES:
   Tracks macro events that affect overall market sentiment:
   - RBI Monetary Policy Committee decisions (repo rate)
   - GDP growth announcements (quarterly)
   - Inflation data (CPI, WPI monthly releases)
   - PMI manufacturing and services indices
   - Federal Reserve FOMC decisions (global impact)
   - Trade balance and employment data

💡 WHY IT MATTERS:
   - RBI policy changes can move NIFTY 2-5% in a day
   - GDP misses can trigger market-wide sell-offs
   - Fed decisions impact FII flows to India
   - Inflation data affects rate expectations
   - Plan market-wide hedges around these dates
   - Reduce leverage before high-impact events
    """
    )

    print("\n📋 COMMAND EXAMPLES:\n")

    commands_2 = [
        (
            "Get upcoming RBI policy dates",
            "python scripts/economic_calendar_fetcher.py --action rbi-policy --days 180",
        ),
        (
            "Get complete economic calendar (30 days)",
            "python scripts/economic_calendar_fetcher.py --action calendar --days 30",
        ),
        (
            "Get only HIGH-IMPACT events",
            "python scripts/economic_calendar_fetcher.py --action high-impact --days 60",
        ),
        (
            "Get GDP announcement dates",
            "python scripts/economic_calendar_fetcher.py --action gdp --days 180",
        ),
        (
            "Get inflation data release dates",
            "python scripts/economic_calendar_fetcher.py --action inflation --days 90",
        ),
        (
            "Get PMI release calendar",
            "python scripts/economic_calendar_fetcher.py --action pmi --days 90",
        ),
        (
            "Get Fed FOMC meeting dates",
            "python scripts/economic_calendar_fetcher.py --action fed-policy --days 180",
        ),
        (
            "Set alert for next RBI policy",
            "python scripts/economic_calendar_fetcher.py --action set-alert --event-name 'RBI Monetary Policy' --days-before 3",
        ),
        (
            "Monitor economic events",
            "python scripts/economic_calendar_fetcher.py --action monitor --interval 3600",
        ),
    ]

    for i, (desc, cmd) in enumerate(commands_2, 1):
        print(f"{i}. {desc}:")
        print(f"   {cmd}\n")

    print("\n📊 SAMPLE OUTPUT:\n")
    print(
        """
════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
RBI MONETARY POLICY CALENDAR
════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
Date         | Country  | Event                               | Impact   | Days Away  | Category
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
2026-02-07   | INDIA    | RBI Monetary Policy Decision        | 🔴 HIGH  | 7 days     | CENTRAL_BANK
2026-04-10   | INDIA    | RBI Monetary Policy Decision        | 🔴 HIGH  | 70 days    | CENTRAL_BANK
2026-06-08   | INDIA    | RBI Monetary Policy Decision        | 🔴 HIGH  | 129 days   | CENTRAL_BANK
════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
Total events: 3
    """
    )

    print("\n🎯 REAL-WORLD WORKFLOW:\n")
    print(
        """
SCENARIO: Managing a ₹10L portfolio, RBI policy meeting in 7 days

STEP 1: Check calendar for upcoming events
   → python scripts/economic_calendar_fetcher.py --action high-impact --days 30
   → RBI policy on Feb 7
   → Fed FOMC on Feb 18
   → GDP data on Feb 28

STEP 2: Analyze current positions
   → Total exposure: ₹8L (80% margin utilization)
   → Portfolio beta: 1.2 (moves 20% more than NIFTY)
   → VIX level: 15 (moderate volatility)

STEP 3: Risk mitigation 3 days before RBI (Feb 4):
   - Reduce position size to 60% (₹6L exposure)
   - Move stop-losses wider (avoid whipsaw)
   - Consider VIX hedge (buy NIFTY puts)
   - Exit momentum trades

STEP 4: Day of RBI policy (Feb 7):
   - No new positions until announcement
   - Watch for rate change:
     * Rate hike → Banks up, growth stocks down
     * Rate cut → Growth stocks up, defensive down
     * Unchanged → Market relief rally

STEP 5: Post-announcement (Feb 7 afternoon):
   - Assess market reaction
   - Re-enter positions with reduced risk
   - Align portfolio with new rate environment
    """
    )

    # ============================================================================
    # FEATURE 3: NEWS ALERTS
    # ============================================================================

    print_section(3, "NEWS ALERTS MANAGER")

    print(
        """
📰 WHAT IT DOES:
   Real-time monitoring of market news with intelligent analysis:
   - Company-specific news (management changes, contracts won)
   - Sector news (regulatory changes, policy shifts)
   - Breaking market news (circuit filters, trading halts)
   - Sentiment analysis (POSITIVE/NEGATIVE/NEUTRAL)
   - Position-based alerts (news for your holdings)
   - Keyword tracking (earnings, dividend, merger, etc.)

💡 WHY IT MATTERS:
   - Breaking news can move stocks 10-20% instantly
   - Sentiment shifts indicate trend changes
   - Early news detection = trading edge
   - Avoid holding during negative news
   - Capitalize on positive sentiment surges
   - Automated monitoring = never miss critical news
    """
    )

    print("\n📋 COMMAND EXAMPLES:\n")

    commands_3 = [
        (
            "Get latest news for INFY",
            "python scripts/news_alerts_manager.py --action latest --symbol INFY --limit 10",
        ),
        (
            "Get breaking news (last 30 minutes)",
            "python scripts/news_alerts_manager.py --action breaking --minutes 30",
        ),
        (
            "Search news by keyword",
            "python scripts/news_alerts_manager.py --action search --keyword 'dividend' --days 7",
        ),
        (
            "Get sentiment analysis for INFY",
            "python scripts/news_alerts_manager.py --action sentiment --symbol INFY --days 30",
        ),
        (
            "Monitor news for multiple symbols",
            "python scripts/news_alerts_manager.py --action monitor --symbols INFY,TCS,RELIANCE --interval 300",
        ),
        (
            "Add symbol to watchlist",
            "python scripts/news_alerts_manager.py --action add-watchlist --symbol INFY --priority HIGH",
        ),
    ]

    for i, (desc, cmd) in enumerate(commands_3, 1):
        print(f"{i}. {desc}:")
        print(f"   {cmd}\n")

    print("\n📊 SAMPLE OUTPUT (Latest News):\n")
    print(
        """
════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
LATEST NEWS - INFY
════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

1. 🟢 INFY reports strong Q3 earnings, beats estimates
   Published: 2026-01-31 14:30:00 | Source: Economic Times
   Symbols: INFY
   INFY posted Q3 profit of ₹1,250 crore, beating analyst estimates of ₹1,150 crore. Revenue grew 15% YoY...

2. 🟢 Analysts upgrade INFY to BUY, raise target price
   Published: 2026-01-31 14:15:00 | Source: Moneycontrol
   Symbols: INFY
   Leading brokerage firms have upgraded INFY with increased price targets citing strong fundamentals...

3. 🟢 INFY announces ₹15 per share dividend
   Published: 2026-01-31 14:00:00 | Source: Economic Times
   Symbols: INFY
   Board of INFY approved final dividend of ₹15 per share for FY2026...

════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
Total articles: 3
    """
    )

    print("\n📊 SAMPLE OUTPUT (Sentiment Analysis):\n")
    print(
        """
════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
SENTIMENT ANALYSIS - INFY
════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
Period: Last 30 days
Total Articles: 15

📊 SENTIMENT BREAKDOWN:
   🟢 Positive: 10 (66.7%)
   🔴 Negative: 2 (13.3%)
   ⚪ Neutral:  3 (20.0%)

📈 OVERALL SENTIMENT:
   Score: 0.53
   Rating: BULLISH

════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
    """
    )

    print("\n🎯 REAL-WORLD WORKFLOW:\n")
    print(
        """
SCENARIO: Monitoring INFY for entry opportunity

STEP 1: Add to watchlist
   → python scripts/news_alerts_manager.py --action add-watchlist --symbol INFY --priority HIGH

STEP 2: Check current sentiment
   → python scripts/news_alerts_manager.py --action sentiment --symbol INFY --days 30
   → Result: 66.7% positive, Rating: BULLISH

STEP 3: Monitor real-time (check every 5 minutes)
   → python scripts/news_alerts_manager.py --action monitor --symbols INFY --interval 300

STEP 4: When positive news breaks:
   🟢 "INFY wins $500M contract with US client"
   → Action: Quick entry at market price
   → Check market depth first
   → Set tight stop-loss (2-3%)

STEP 5: When negative news breaks:
   🔴 "INFY faces regulatory investigation"
   → Action: Exit immediately if holding
   → Wait for clarification before re-entry
   → Monitor sentiment shift

STEP 6: Sentiment shift detection:
   - Was BULLISH (70% positive) → Now BEARISH (60% negative)
   - Multiple negative articles in 24 hours
   - Action: Exit position, reassess fundamentals
    """
    )

    # ============================================================================
    # INTEGRATED WORKFLOW
    # ============================================================================

    print_section(4, "INTEGRATED WORKFLOW - COMPLETE EXAMPLE")

    print(
        """
🎯 SCENARIO: Professional trader managing ₹20L portfolio

GOAL: Maximize returns while avoiding event-driven volatility
HOLDINGS: INFY (100 shares), TCS (50 shares), RELIANCE (20 shares)
    """
    )

    print("\n📅 MORNING ROUTINE (9:00 AM - Before Market Open):\n")
    print(
        """
1. CHECK ECONOMIC CALENDAR (market-wide events)
   → python scripts/economic_calendar_fetcher.py --action calendar --days 7
   
   OUTPUT:
   - Feb 7: RBI Policy (7 days away) - 🔴 HIGH IMPACT
   - Feb 12: CPI Inflation data - 🟡 MEDIUM IMPACT
   
   DECISION: Reduce leverage before RBI policy (Feb 4)

2. CHECK CORPORATE ANNOUNCEMENTS (stock-specific events)
   → python scripts/corporate_announcements_fetcher.py --action upcoming --days 7
   
   OUTPUT:
   - Feb 5: TCS Dividend (5 days) - 🟡 MEDIUM IMPACT
   - Feb 10: INFY Earnings (10 days) - 🔴 HIGH IMPACT
   
   DECISION: 
   - Hold TCS until ex-dividend date
   - Prepare for INFY earnings volatility

3. CHECK NEWS SENTIMENT (current market mood)
   → python scripts/news_alerts_manager.py --action sentiment --symbol INFY --days 7
   → python scripts/news_alerts_manager.py --action sentiment --symbol TCS --days 7
   
   OUTPUT:
   - INFY: BULLISH (70% positive) ✓
   - TCS: NEUTRAL (50% positive) ⚠️
   
   DECISION:
   - INFY: Favorable for holding/adding
   - TCS: Monitor closely, reduce size if sentiment turns
    """
    )

    print("\n📊 DURING MARKET HOURS (9:15 AM - 3:30 PM):\n")
    print(
        """
TERMINAL 1: Monitor breaking news (every 5 minutes)
   → python scripts/news_alerts_manager.py --action monitor --symbols INFY,TCS,RELIANCE --interval 300

TERMINAL 2: Monitor account margin
   → python scripts/account_fetcher.py --action monitor --interval 300

TERMINAL 3: Real-time quotes
   → python scripts/websocket_quote_streamer.py --symbols INFY,TCS,RELIANCE --live-display

⚡ BREAKING NEWS ALERT (11:30 AM):
   🔴 "INFY faces client attrition in Q3"
   
   IMMEDIATE ACTIONS:
   1. Check news details:
      → python scripts/news_alerts_manager.py --action latest --symbol INFY --limit 5
   
   2. Assess impact: Major client loss announced
   
   3. Check market reaction:
      → Price dropped 3% in 10 minutes
      → Volume surged 200%
   
   4. DECISION: Exit INFY position
      → python scripts/order_manager.py --action place --symbol INFY --side SELL --qty 100 --type MARKET
   
   5. Update sentiment:
      → Wait 24 hours for full news cycle
      → Re-check sentiment before considering re-entry
    """
    )

    print("\n🌙 POST-MARKET ANALYSIS (After 3:30 PM):\n")
    print(
        """
1. REVIEW NEWS IMPACT
   → python scripts/news_alerts_manager.py --action latest --symbol INFY --limit 20
   
   Analysis:
   - 5 negative articles published
   - Sentiment shifted from BULLISH to BEARISH
   - Exit decision was correct

2. CHECK UPCOMING EVENTS (next 7 days)
   → python scripts/corporate_announcements_fetcher.py --action upcoming --days 7
   → python scripts/economic_calendar_fetcher.py --action calendar --days 7
   
   Planning:
   - Set alerts for TCS dividend (Feb 5)
   - Prepare for RBI policy (Feb 7)
   - Mark INFY earnings calendar (Feb 10)

3. SET ALERTS FOR TOMORROW
   → python scripts/corporate_announcements_fetcher.py --action set-alert --symbol TCS --announcement-type DIVIDEND --days-before 1
   → python scripts/economic_calendar_fetcher.py --action set-alert --event-name 'RBI' --days-before 3

4. PLAN NEXT DAY STRATEGY
   - Monitor INFY sentiment recovery
   - Hold TCS until ex-dividend
   - Reduce overall exposure before RBI policy
    """
    )

    # ============================================================================
    # KEY METRICS & SUMMARY
    # ============================================================================

    print_section(5, "KEY METRICS & BEST PRACTICES")

    print(
        """
📊 EVENT IMPACT LEVELS (Historical Data):

HIGH-IMPACT EVENTS (2-10% market/stock movement):
   • RBI Policy Rate Changes
   • GDP Miss/Beat by >0.5%
   • Earnings Surprises (>10% beat/miss)
   • Major Corporate Announcements (M&A, CEO changes)
   • Fed Rate Decisions

MEDIUM-IMPACT EVENTS (0.5-2% movement):
   • Dividend Announcements
   • Inflation Data Releases
   • PMI Data
   • Board Meetings
   • Sector-specific News

LOW-IMPACT EVENTS (<0.5% movement):
   • Minor Regulatory Filings
   • AGM/EGM Announcements
   • Routine Board Meetings
    """
    )

    print("\n🛡️ RISK MANAGEMENT RULES:\n")
    print(
        """
BEFORE HIGH-IMPACT EVENTS:
   1. Reduce position size by 30-50%
   2. Widen stop-losses by 50%
   3. Lower margin utilization below 50%
   4. Hedge with options if holding large positions
   5. Exit momentum trades completely

DURING EVENT ANNOUNCEMENTS:
   1. No new positions during announcement
   2. Monitor real-time news
   3. Be ready to exit on adverse news
   4. Wait for initial volatility to settle

AFTER EVENT ANNOUNCEMENTS:
   1. Reassess market direction
   2. Check sentiment shift
   3. Adjust positions based on outcome
   4. Look for mean reversion opportunities
    """
    )

    print("\n⏰ ALERT TIMING GUIDELINES:\n")
    print(
        """
EARNINGS ANNOUNCEMENTS:
   • 7 days before: Review position, plan adjustments
   • 3 days before: Reduce size if uncertain
   • 1 day before: Final decision to hold/exit

RBI POLICY MEETINGS:
   • 7 days before: Assess market-wide exposure
   • 3 days before: Reduce leverage, hedge portfolio
   • 1 day before: No new aggressive positions

BREAKING NEWS:
   • Real-time monitoring during market hours
   • 5-minute check intervals for active positions
   • Immediate action on HIGH-PRIORITY alerts
    """
    )

    print("\n📈 SENTIMENT-BASED TRADING:\n")
    print(
        """
BULLISH SENTIMENT (>60% positive):
   ✅ Safe to hold existing positions
   ✅ Consider adding on dips
   ✅ Use tighter stop-losses (momentum)
   ✅ Look for breakout opportunities

NEUTRAL SENTIMENT (40-60% positive):
   ⚠️  Hold with wider stops
   ⚠️  Reduce position size
   ⚠️  Wait for clearer direction
   ⚠️  Focus on support/resistance levels

BEARISH SENTIMENT (<40% positive):
   🔴 Exit or reduce positions
   🔴 Avoid new longs
   🔴 Consider shorts (if experienced)
   🔴 Wait for sentiment reversal
    """
    )

    # ============================================================================
    # CONCLUSION
    # ============================================================================

    print_section(6, "NEXT STEPS")

    print(
        """
✅ YOU NOW HAVE THREE POWERFUL INFORMATION TOOLS:

1️⃣  Corporate Announcements Fetcher (scripts/corporate_announcements_fetcher.py)
   → Track earnings, dividends, corporate actions
   → 8 action modes with full CLI support
   → Alert system for advance warnings

2️⃣  Economic Calendar Fetcher (scripts/economic_calendar_fetcher.py)
   → Monitor RBI, Fed, GDP, inflation, PMI
   → Pre-loaded 2026 calendar
   → Impact analysis and historical tracking

3️⃣  News Alerts Manager (scripts/news_alerts_manager.py)
   → Real-time news monitoring
   → Sentiment analysis (POSITIVE/NEGATIVE/NEUTRAL)
   → Position-based alerts

🎯 RECOMMENDED SETUP:

TERMINAL 1: Real-time monitoring
   → python scripts/news_alerts_manager.py --action monitor --symbols <your_holdings> --interval 300

TERMINAL 2: Daily morning routine
   → Check economic calendar (7 days)
   → Check corporate announcements (7 days)
   → Review sentiment for holdings

TERMINAL 3: Trading operations
   → Place orders based on news/events
   → Manage risk around announcements
   → Execute strategy

📚 FOR MORE DETAILS:
   → See LIVE_TRADING_GUIDE.md for comprehensive documentation
   → Check individual script help: python <script>.py --help
   → Review database schema in each script's docstring

🚀 START USING NOW:
   1. Set up alerts for your current holdings
   2. Monitor news during trading hours
   3. Adjust positions before high-impact events
   4. Track sentiment to gauge market mood
   5. Integrate with your existing trading strategy

Remember: Information = Edge in trading. Use these tools to stay ahead! 📊
    """
    )

    print("\n" + "=" * 100)
    print("  END OF DEMO")
    print("=" * 100 + "\n")


if __name__ == "__main__":
    main()
