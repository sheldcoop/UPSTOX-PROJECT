# Copilot / AI Agent Instructions — Upstox Trading Platform

Purpose: help an AI agent understand the complete trading platform architecture and contribute effectively to both backend and frontend development.

## 🎯 Project Overview

This is a **production-grade algorithmic trading platform** built on the Upstox API:
- **Backend:** 11 production features (authentication, risk management, strategies, analytics, paper trading, etc.)
- **Database:** SQLite with 40+ tables for market data, trades, performance tracking
- **Frontend:** [TO BE BUILT] Modern trading dashboard with real-time data visualization
- **Data Sources:** NewsAPI, FinBERT AI sentiment, NSE corporate actions scraping

**Current Status:** Backend complete (6,500+ lines), ready for frontend development.

## 🏗️ Backend Architecture (Completed)

### Core Systems
1. **auth_manager.py** - OAuth 2.0 with auto-refresh, Fernet encryption
2. **error_handler.py** - Retry logic, exponential backoff, API caching
3. **risk_manager.py** - Position sizing, circuit breaker, VAR/Sharpe calculation
4. **database_validator.py** - Data quality, constraints, repair utilities
5. **strategy_runner.py** - RSI/MACD strategies with signal generation
6. **alert_system.py** - Price/volume/technical alerts with notifications
7. **data_sync_manager.py** - Scheduled sync, gap detection, backfill
8. **logger_config.py** - Centralized logging with system metrics (psutil)
9. **performance_analytics.py** - Win rate, Sharpe/Sortino, equity curve
10. **paper_trading.py** - Virtual portfolio with realistic order matching
11. **config/trading.yaml** - YAML configuration management

### Database Schema
- **40+ tables** across market data, authentication, risk, strategies, alerts, performance
- **Key tables:** ohlc_data, trading_signals, paper_orders, risk_metrics, alert_rules
- **Validation:** Constraints on OHLC (high >= low), duplicate detection, indexes

### Integration Points
When building frontend or extending backend:
- Use `AuthManager.get_valid_token()` for API calls
- Wrap API calls with `@with_retry()` decorator
- Check `RiskManager.check_daily_loss()` before orders
- Query `trading_signals` table for strategy outputs
- Use `PerformanceAnalytics` for metrics display

### API Base URL
- Production: `https://api.upstox.com/v2/`
- All endpoints require Bearer token from AuthManager
- Rate limits: 429 errors trigger 60s wait (handled by ErrorHandler)

---

## 🐛 Debugging Protocol

**CRITICAL:** For ALL bugs, errors, or unexpected behavior, follow the **God-Mode Debugging Protocol**:

**File:** [.github/debugging-protocol.md](.github/debugging-protocol.md)

**Required Steps:**
1. **Triage:** Generate 3-5 ranked hypotheses with probability scores
2. **Instrument:** Add trace_id logging and state snapshots
3. **Isolate:** Create minimal `repro_debug.py` script
4. **Fix:** Implement with assertions and validation
5. **Verify:** Test + add to regression suite

**Auto-Triggers:**
- Any Flask 500 error → Full trace logging
- Any OHLC validation failure → State dump
- Any P&L calculation error → Hypothesis ranking
- Any frontend state issue → Component lifecycle tracing

**Logging Standards:**
```python
logger.debug(f"[TraceID: {g.trace_id}] Function: {func_name}, Input: {params}")
logger.info(f"[TraceID: {g.trace_id}] Result: {result}")
logger.error(f"[TraceID: {g.trace_id}] Error: {e}", exc_info=True)
```

See full protocol for platform-specific patterns (Phantom P&L, Ghost Orders, Data Gaps).

---

## 📖 API Documentation Reference

**File:** [Upstox.md](Upstox.md) - Scraped Upstox developer docs

**Structure to preserve:**
- Source blocks: `---` + `# Source: <URL>` + `---` + content
- Base URL: `https://api.upstox.com/v2/`
- OAuth params: `client_id`, `redirect_uri`, `response_type`, `code`
- Keep `curl` examples and absolute image URLs intact
