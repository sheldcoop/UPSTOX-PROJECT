#!/usr/bin/env python3
"""
Debug candle fetch - check raw API response
"""
import sys

sys.path.insert(0, "/Users/prince/Desktop/UPSTOX-project/scripts")

from candle_fetcher import get_access_token
import requests
from datetime import datetime, timedelta

token = get_access_token()
print(f"Token: {token[:20]}...")

# Try with dates from 2025
end_date = "2025-01-31"
start_date = "2025-01-26"

url = f"https://api.upstox.com/v2/historical-candle/NSE_EQ|INE002A01018/day/{start_date}/{end_date}"

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json",
}

print(f"\nURL: {url}")
print(f"Headers: {headers}")

response = requests.get(url, headers=headers, timeout=15)
print(f"\nStatus: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    data = response.json()
    print(f"\nCandles count: {len(data.get('data', {}).get('candles', []))}")
