# Technical Proposal: The Oracle Market Sentinel 🛡️

**To**: Lead Developer / Technical Reviewer
**From**: Oracle Architect
**Subject**: Proposed Architecture for "Market Sentinel" Autonomous Monitoring System

## 1. Executive Summary
The client has requested an autonomous monitoring solution ("Sentinel") to provide real-time alerts on market anomalies and system health without requiring manual dashboard checks. This document outlines a low-latency, zero-cost architecture using local Python daemons and statistical analysis.

## 2. Architecture Overview

### 2.1 The "Sidecar" Pattern
The Sentinel will run as a standalone background process (`sentinel_daemon.py`), decoupled from the core ingestion pipeline.
*   **Role**: Observer.
*   **Permissions**: Read-Only access to `market_data.db`.
*   **Isolation**: Crashing the Sentinel does NOT stop data ingestion.

```mermaid
graph TD
    A[Upstox WebSocket] -->|Writes| B(market_data.db)
    C[Sentinel Daemon] -->|Reads (Async)| B
    C -->|Statistical Logic| D{Anomaly Detected?}
    D -- Yes --> E[Telegram Bot API]
    E -->|Push Notification| F[Client Phone]
```

## 3. Core Capabilities (The 3 Modules)

### Module A: Statistical Anomaly Detection (No-AI)
Instead of expensive LLM calls, we use robust statistics (Z-Scores) to detect outliers.
*   **Logic**: Calculate Rolling Mean (µ) and Std Dev (σ) for Price/Volume over last 50 candles.
*   **Trigger**: `if (Current_Volume > µ + 3σ): Alert("3-Sigma Volume Spike")`
*   **Benefit**: Instant execution (<10ms), Zero cost, Mathematically objective.

### Module B: The "Heartbeat" (System Health)
Monitors the "freshness" of the data tables.
*   **Logic**: Check `MAX(timestamp)` of `market_quota_nse500_data`.
*   **Trigger**: `if (Now - Last_Update > 5 mins): Alert("CRITICAL: Data Feed Stalled")`
*   **Benefit**: Prevents "flying blind" if the ingestion script silently fails.

### Module C: Discovery Engine
Scans for structural market shifts.
*   **Logic**: Scans `instrument_master` sectors for aggregate moves.
*   **Trigger**: `if (Avg(Chemical_Sector_Change) > 2%): Alert("Chemical Sector is Moving")`

## 4. Technology Stack & Costs

| Component | Technology | Cost (Recurring) | Notes |
| :--- | :--- | :--- | :--- |
| **Compute** | Local Python Process | **$0.00** | Runs on client's existing mac. |
| **Database** | SQLite (WAL Mode) | **$0.00** | Uses existing DB. Read-Only mode prevents locks. |
| **Alerts** | Telegram Bot API | **$0.00** | Free simplified webhook/polling. |
| **Logic** | NumPy / Pandas | **$0.00** | Open source libraries. |

## 5. Implementation Plan

1.  **Bot Setup**: client generates Token via @BotFather.
2.  **Dev Phase**: Implement `backend/sentinel/daemon.py`.
3.  **Deployment**: Add to `start.sh` or run as `systemd` / `launchd` service.

## 6. Security Implications
*   **Read-Only**: The Sentinel cannot corrupt market data.
*   **Token Safety**: Telegram Token stored in `.env` (gitignored).
*   **Privacy**: No data leaves the local machine except the alert text sent to Telegram.

---
**Recommendation**: Proceed with implementation. High value, zero risk, zero operational cost.
