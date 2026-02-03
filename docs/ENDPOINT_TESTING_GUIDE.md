# Comprehensive Endpoint Testing Guide

## Overview

This document provides testing procedures for all 14 new high-priority endpoints plus verification of existing expired instrument endpoints.

---

## Testing Setup

### Prerequisites
```bash
# 1. Ensure API server is running
cd /home/runner/work/UPSTOX-PROJECT/UPSTOX-PROJECT
python3 scripts/api_server.py

# 2. Ensure valid authentication token
# Login via http://localhost:5050 if needed

# 3. Get your API base URL
API_BASE="http://localhost:9000/api"
```

### Test Tools
- **cURL** - Command-line testing
- **Postman** - GUI-based testing
- **Python requests** - Programmatic testing

---

## 1. Authentication Endpoints

### DELETE /api/logout

**Purpose:** Logout and revoke access token

**Test:**
```bash
curl -X DELETE "$API_BASE/logout" \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Logged out successfully",
  "tokens_revoked": 1,
  "timestamp": "2026-02-03T12:00:00"
}
```

**Validation:**
- Check `success` is `true`
- Verify subsequent API calls fail with 401 (unauthorized)
- Check database: `SELECT * FROM auth_tokens WHERE is_active = 0`

---

### GET /api/auth/status

**Purpose:** Check authentication status

**Test:**
```bash
curl "$API_BASE/auth/status"
```

**Expected Response (authenticated):**
```json
{
  "is_authenticated": true,
  "user_id": "user123",
  "token_expires_at": "2026-02-03T18:00:00",
  "timestamp": "2026-02-03T12:00:00"
}
```

**Expected Response (not authenticated):**
```json
{
  "is_authenticated": false,
  "message": "No active authentication",
  "timestamp": "2026-02-03T12:00:00"
}
```

---

## 2. Market Quote v3 Endpoints

### GET /api/v3/market-quote/ltp

**Purpose:** Get Last Traded Price (v3)

**Test (single symbol):**
```bash
curl "$API_BASE/v3/market-quote/ltp?symbol=NSE_EQ%7CINE669E01016"
```

**Test (multiple symbols):**
```bash
curl "$API_BASE/v3/market-quote/ltp?symbol=NSE_EQ%7CINE669E01016,NSE_EQ%7CINE009A01021"
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "NSE_EQ|INE669E01016": {
      "last_price": 1450.50,
      "instrument_token": "NSE_EQ|INE669E01016"
    }
  },
  "timestamp": "2026-02-03T12:00:00"
}
```

**Validation:**
- Verify `last_price` is present and numeric
- For multiple symbols, all should be in response
- Check response time < 2 seconds

---

### GET /api/v3/market-quote/ohlc

**Purpose:** Get OHLC data (v3)

**Test:**
```bash
curl "$API_BASE/v3/market-quote/ohlc?symbol=NSE_EQ%7CINE669E01016&interval=1day"
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "NSE_EQ|INE669E01016": {
      "ohlc": {
        "open": 1445.00,
        "high": 1455.00,
        "low": 1440.00,
        "close": 1450.50
      },
      "volume": 1234567
    }
  },
  "timestamp": "2026-02-03T12:00:00"
}
```

**Validation:**
- Verify high >= low
- Verify high >= open, close
- Verify low <= open, close
- Volume should be positive

---

### GET /api/v3/market-quote/option-greek

**Purpose:** Get Option Greeks (v3)

**Test:**
```bash
curl "$API_BASE/v3/market-quote/option-greek?symbol=NSE_FO%7CNIFTY24FEB24000CE"
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "NSE_FO|NIFTY24FEB24000CE": {
      "greeks": {
        "delta": 0.65,
        "gamma": 0.002,
        "theta": -15.5,
        "vega": 18.2,
        "rho": 5.3
      },
      "iv": 15.5
    }
  },
  "timestamp": "2026-02-03T12:00:00"
}
```

**Validation:**
- Delta: -1 to 1 (calls positive, puts negative)
- Gamma: always positive
- Theta: usually negative (time decay)
- Vega: always positive
- IV (Implied Volatility) > 0

---

## 3. Historical Data v3 Endpoints

### GET /api/v3/historical-candle/...

**Purpose:** Get historical candle data (v3)

**Test:**
```bash
curl "$API_BASE/v3/historical-candle/NSE_EQ%7CINE669E01016/days%2F1/100/2024-01-31/2024-01-01"
```

**Expected Response:**
```json
{
  "success": true,
  "instrument_key": "NSE_EQ|INE669E01016",
  "interval": "days/1",
  "count": 20,
  "data": {
    "candles": [
      ["2024-01-31T00:00:00", 1450, 1460, 1445, 1455, 123456, 0],
      ["2024-01-30T00:00:00", 1440, 1450, 1435, 1450, 98765, 0]
    ]
  },
  "timestamp": "2026-02-03T12:00:00"
}
```

**Validation:**
- Candles array not empty
- Each candle: [timestamp, open, high, low, close, volume, oi]
- Dates in descending order (newest first)
- High >= Low for all candles

---

### GET /api/v3/historical-candle/intraday/...

**Purpose:** Get intraday candle data (v3)

**Test (15-minute candles):**
```bash
curl "$API_BASE/v3/historical-candle/intraday/NSE_EQ%7CINE669E01016/minutes%2F15/100"
```

**Expected Response:**
```json
{
  "success": true,
  "instrument_key": "NSE_EQ|INE669E01016",
  "interval": "minutes/15",
  "count": 78,
  "data": {
    "candles": [
      ["2026-02-03T15:15:00", 1450, 1452, 1449, 1451, 12345, 0]
    ]
  },
  "timestamp": "2026-02-03T15:30:00"
}
```

**Validation:**
- Only today's data returned
- Timestamps within market hours (9:15 AM - 3:30 PM)
- Candles in 15-minute intervals

---

## 4. Market Information Endpoints

### GET /api/market/status/<exchange>

**Purpose:** Get market status (open/closed)

**Test:**
```bash
curl "$API_BASE/market/status/NSE?segment=EQ"
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "exchange": "NSE",
    "segment": "EQ",
    "is_open": true,
    "status": "open",
    "next_open_time": null,
    "next_close_time": "2026-02-03T15:30:00"
  },
  "timestamp": "2026-02-03T12:00:00"
}
```

**Validation:**
- `is_open` is boolean
- If market closed, `next_open_time` should be present
- Status: "open", "closed", "pre-open", "post-close"

---

### GET /api/market/holidays

**Purpose:** Get market holiday calendar

**Test:**
```bash
curl "$API_BASE/market/holidays?year=2024&exchange=NSE"
```

**Expected Response:**
```json
{
  "success": true,
  "data": [
    {
      "date": "2024-01-26",
      "name": "Republic Day",
      "exchange": "NSE",
      "segment": "EQ"
    },
    {
      "date": "2024-03-08",
      "name": "Mahashivratri",
      "exchange": "NSE",
      "segment": "EQ"
    }
  ],
  "count": 15,
  "timestamp": "2026-02-03T12:00:00"
}
```

**Validation:**
- Dates in YYYY-MM-DD format
- At least 10-15 holidays in a year
- All dates should be in the requested year

---

### GET /api/market/holidays/<date>

**Purpose:** Check if specific date is a holiday

**Test:**
```bash
curl "$API_BASE/market/holidays/2024-01-26"
```

**Expected Response:**
```json
{
  "success": true,
  "date": "2024-01-26",
  "is_holiday": true,
  "holiday_info": {
    "date": "2024-01-26",
    "name": "Republic Day",
    "exchange": "NSE"
  },
  "timestamp": "2026-02-03T12:00:00"
}
```

**Validation:**
- `is_holiday` is boolean
- If `is_holiday` is true, `holiday_info` should be present

---

### GET /api/market/timings/<date>

**Purpose:** Get market timings for a date

**Test:**
```bash
curl "$API_BASE/market/timings/2024-01-31?exchange=NSE&segment=EQ"
```

**Expected Response:**
```json
{
  "success": true,
  "date": "2024-01-31",
  "data": {
    "exchange": "NSE",
    "segment": "EQ",
    "open_time": "09:15:00",
    "close_time": "15:30:00",
    "pre_open_start": "09:00:00",
    "pre_open_end": "09:15:00"
  },
  "timestamp": "2026-02-03T12:00:00"
}
```

**Validation:**
- Times in HH:MM:SS format
- pre_open_start < pre_open_end < open_time < close_time

---

## 5. Charges Endpoints

### GET /api/charges/brokerage

**Purpose:** Calculate brokerage charges

**Test:**
```bash
curl "$API_BASE/charges/brokerage?instrument_token=NSE_EQ%7CINE669E01016&quantity=100&price=1450&transaction_type=BUY&product=D"
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "charges": {
      "brokerage": 20.00,
      "stt_ctt": 14.50,
      "transaction_charges": 3.62,
      "gst": 3.60,
      "sebi_charges": 0.15,
      "stamp_duty": 18.12,
      "total_charges": 59.99,
      "order_value": 145000.00,
      "total_cost": 145059.99,
      "breakeven_price": 1450.60,
      "charges_percentage": 0.0413
    }
  },
  "timestamp": "2026-02-03T12:00:00"
}
```

**Validation:**
- All charges >= 0
- total_charges = sum of all individual charges
- breakeven_price > price (for BUY)
- breakeven_price < price (for SELL)
- charges_percentage < 1% typically

---

### GET /api/charges/margin

**Purpose:** Calculate margin requirements

**Test:**
```bash
curl "$API_BASE/charges/margin?instrument_token=NSE_FO%7CNIFTY24FEB&quantity=50&transaction_type=BUY&price=21500"
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "required_margin": 120000.00,
    "span_margin": 95000.00,
    "exposure_margin": 25000.00,
    "premium_margin": 0,
    "additional_margin": 0
  },
  "timestamp": "2026-02-03T12:00:00"
}
```

**Validation:**
- required_margin > 0
- required_margin >= span_margin + exposure_margin
- Futures margin typically 10-20% of contract value

---

## 6. WebSocket Feed Endpoints

### GET /api/feed/portfolio-stream-feed/authorize

**Purpose:** Get WebSocket authorization for portfolio stream

**Test:**
```bash
curl "$API_BASE/feed/portfolio-stream-feed/authorize"
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "authorized_redirect_uri": "wss://api.upstox.com/v2/feed/portfolio-stream-feed",
    "websocket_url": "wss://api.upstox.com/v2/feed/portfolio-stream-feed",
    "access_token": "eyJ...",
    "instructions": {
      "1": "Use the websocket_url to establish WebSocket connection",
      "2": "Send access_token in connection parameters",
      "3": "Subscribe to portfolio stream for real-time updates"
    }
  },
  "timestamp": "2026-02-03T12:00:00"
}
```

**Validation:**
- websocket_url starts with "wss://"
- access_token is present and non-empty

---

### GET /api/feed/market-data-feed/authorize

**Purpose:** Get WebSocket authorization for market data stream

**Test:**
```bash
curl "$API_BASE/feed/market-data-feed/authorize"
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "authorized_redirect_uri": "wss://api.upstox.com/v2/feed/market-data-feed",
    "websocket_url": "wss://api.upstox.com/v2/feed/market-data-feed",
    "access_token": "eyJ...",
    "instructions": {
      "1": "Use the websocket_url for market data WebSocket connection",
      "2": "Subscribe to specific instruments for real-time quotes"
    }
  },
  "timestamp": "2026-02-03T12:00:00"
}
```

**Validation:**
- websocket_url starts with "wss://"
- Different URL from portfolio feed

---

## 7. Existing Expired Instruments Endpoints (Verification)

### GET /api/expired/expiries

**Purpose:** Get available expiries for an underlying

**Test:**
```bash
curl "$API_BASE/expired/expiries?underlying=NIFTY"
```

**Expected Response:**
```json
{
  "success": true,
  "underlying": "NIFTY",
  "expiries": [
    "2024-01-25",
    "2024-01-18",
    "2024-01-11"
  ]
}
```

**Validation:**
- Array of dates in YYYY-MM-DD format
- Dates in descending order (most recent first)
- All dates should be in the past

---

### POST /api/expired/download

**Purpose:** Download expired option chain data

**Test:**
```bash
curl -X POST "$API_BASE/expired/download" \
  -H "Content-Type: application/json" \
  -d '{
    "underlying": "NIFTY",
    "expiries": ["2024-01-25"],
    "download_candles": false
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "underlying": "NIFTY",
  "expiries_processed": 1,
  "contracts_downloaded": 50,
  "contracts_stored": 50
}
```

**Validation:**
- contracts_downloaded > 0
- contracts_stored > 0
- expiries_processed matches input count

---

## Automated Test Script

```python
#!/usr/bin/env python3
"""
Automated endpoint testing script
Usage: python test_endpoints.py
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:9000/api"

def test_endpoint(method, endpoint, params=None, data=None, expected_status=200):
    """Test a single endpoint"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, timeout=30)
        
        status_ok = response.status_code == expected_status
        has_success = response.json().get("success", False)
        
        print(f"{'✅' if status_ok and has_success else '❌'} {method} {endpoint} - Status: {response.status_code}")
        
        return status_ok and has_success
        
    except Exception as e:
        print(f"❌ {method} {endpoint} - Error: {str(e)}")
        return False

def run_all_tests():
    """Run all endpoint tests"""
    print("=" * 70)
    print("ENDPOINT TESTING SUITE")
    print("=" * 70)
    
    tests = [
        # Auth
        ("GET", "/auth/status", None, None),
        
        # Market Quotes v3
        ("GET", "/v3/market-quote/ltp", {"symbol": "NSE_EQ|INE669E01016"}, None),
        ("GET", "/v3/market-quote/ohlc", {"symbol": "NSE_EQ|INE669E01016"}, None),
        ("GET", "/v3/market-quote/option-greek", {"symbol": "NSE_FO|NIFTY24FEB24000CE"}, None),
        
        # Historical v3
        ("GET", "/v3/historical-candle/NSE_EQ|INE669E01016/days/1/10/2024-01-31", None, None),
        ("GET", "/v3/historical-candle/intraday/NSE_EQ|INE669E01016/minutes/15/50", None, None),
        
        # Market Info
        ("GET", "/market/status/NSE", {"segment": "EQ"}, None),
        ("GET", "/market/holidays", {"year": 2024}, None),
        ("GET", "/market/timings", {"exchange": "NSE"}, None),
        
        # Charges
        ("GET", "/charges/brokerage", {
            "instrument_token": "NSE_EQ|INE669E01016",
            "quantity": 100,
            "price": 1450,
            "transaction_type": "BUY",
            "product": "D"
        }, None),
        
        # WebSocket
        ("GET", "/feed/portfolio-stream-feed/authorize", None, None),
        ("GET", "/feed/market-data-feed/authorize", None, None),
        
        # Expired Instruments
        ("GET", "/expired/expiries", {"underlying": "NIFTY"}, None),
    ]
    
    passed = 0
    failed = 0
    
    for method, endpoint, params, data in tests:
        if test_endpoint(method, endpoint, params, data):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

if __name__ == "__main__":
    run_all_tests()
```

---

## Summary

### Total Endpoints Tested: 14

**By Category:**
- Auth: 2 endpoints
- Market Quote v3: 3 endpoints
- Historical Data v3: 2 endpoints
- Market Information: 4 endpoints
- Charges: 2 endpoints
- WebSocket: 2 endpoints
- Expired Instruments (verified): 2+ endpoints

### Testing Checklist

- [ ] All 14 new endpoints return 200 status
- [ ] All responses include `success: true`
- [ ] All responses include `timestamp`
- [ ] Authentication required endpoints return 401 without token
- [ ] Invalid parameters return appropriate error codes
- [ ] Response data structure matches documentation
- [ ] Numeric values are within expected ranges
- [ ] Dates are in correct format
- [ ] WebSocket URLs are valid (wss://)

---

**Document Version:** 1.0  
**Last Updated:** February 3, 2026  
**Purpose:** Comprehensive testing guide for all endpoints
