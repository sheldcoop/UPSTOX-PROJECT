#!/usr/bin/env python3
"""
Fetch Historical OHLC Data from Upstox
Downloads historical candle data for any instrument
"""

import sys
import os

# Add scripts directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Now import after path is set
import requests
import json
from datetime import datetime, timedelta
import logging

# Import auth_manager AFTER fixing path
from auth_manager import AuthManager

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_historical_data(instrument_key, interval="day", days_back=30):
    """
    Fetch historical candle data from Upstox
    
    Args:
        instrument_key: Instrument identifier (e.g., "NSE_EQ|INE467B01029" for TCS)
        interval: Candle interval (1minute, 30minute, day, week, month)
        days_back: Number of days to fetch data for
    
    Returns:
        dict: Historical candle data
    """
    
    # Initialize auth manager
    auth = AuthManager()
    
    # Get valid token
    token = auth.get_valid_token()
    if not token:
        print("❌ No valid token found. Please authenticate first:")
        print("   ./authenticate.sh")
        return None
    
    # Calculate date range
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days_back)
    
    # Format dates as required by API (YYYY-MM-DD)
    to_date_str = to_date.strftime("%Y-%m-%d")
    from_date_str = from_date.strftime("%Y-%m-%d")
    
    # API endpoint
    url = f"https://api.upstox.com/v2/historical-candle/{instrument_key}/{interval}/{to_date_str}/{from_date_str}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    try:
        logger.info(f"🔄 Fetching historical data for {instrument_key}...")
        logger.info(f"   Interval: {interval}, Period: {from_date_str} to {to_date_str}")
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") == "success":
            candles = data.get("data", {}).get("candles", [])
            
            print("\n" + "="*80)
            print(f"📊 HISTORICAL DATA: {instrument_key}")
            print("="*80)
            print(f"Interval: {interval}")
            print(f"Period: {from_date_str} to {to_date_str}")
            print(f"Total Candles: {len(candles)}")
            print("="*80)
            
            if candles:
                print("\nLatest 10 Candles:")
                print(f"{'Timestamp':<20} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10} {'Volume':>12}")
                print("-" * 80)
                
                for candle in candles[:10]:
                    timestamp_str = candle[0]
                    open_price = candle[1]
                    high_price = candle[2]
                    low_price = candle[3]
                    close_price = candle[4]
                    volume = candle[5]
                    
                    print(f"{timestamp_str:<20} {open_price:>10.2f} {high_price:>10.2f} {low_price:>10.2f} {close_price:>10.2f} {volume:>12,}")
                
                print("\n" + "="*80)
                
                # Calculate some basic stats
                close_prices = [candle[4] for candle in candles]
                if close_prices:
                    print("\n📈 Statistics:")
                    print(f"   Highest Close: ₹{max(close_prices):,.2f}")
                    print(f"   Lowest Close: ₹{min(close_prices):,.2f}")
                    print(f"   Latest Close: ₹{close_prices[0]:,.2f}")
                    print(f"   Average Close: ₹{sum(close_prices)/len(close_prices):,.2f}")
                    
                    # Calculate return
                    if len(close_prices) > 1:
                        first_close = close_prices[-1]
                        last_close = close_prices[0]
                        returns = ((last_close - first_close) / first_close) * 100
                        print(f"   Period Return: {returns:+.2f}%")
            
            print("\n" + "="*80)
            return data
        else:
            print(f"❌ API Error: {data.get('message', 'Unknown error')}")
            return None
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("❌ Authentication failed. Token may be expired.")
            print("   Run: ./authenticate.sh")
        elif e.response.status_code == 400:
            print(f"❌ Bad Request: {e.response.text}")
            print("\nℹ️  Common issues:")
            print("   - Invalid instrument_key format")
            print("   - Invalid date range")
            print("   - Invalid interval")
        else:
            print(f"❌ HTTP Error: {e}")
            print(f"Response: {e.response.text}")
        return None
    
    except Exception as e:
        logger.error(f"❌ Error fetching data: {e}", exc_info=True)
        return None


# Popular instrument keys for testing
INSTRUMENTS = {
    "RELIANCE": "NSE_EQ|INE002A01018",
    "TCS": "NSE_EQ|INE467B01029",
    "INFY": "NSE_EQ|INE009A01021",
    "HDFC": "NSE_EQ|INE040A01034",
    "ICICIBANK": "NSE_EQ|INE090A01021",
    "SBIN": "NSE_EQ|INE062A01020",
    "NIFTY50": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank"
}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch historical data from Upstox")
    parser.add_argument("--symbol", "-s", default="TCS", help="Stock symbol (e.g., TCS, RELIANCE)")
    parser.add_argument("--interval", "-i", default="day", 
                        help="Candle interval (1minute, 30minute, day, week, month)")
    parser.add_argument("--days", "-d", type=int, default=30, help="Number of days to fetch")
    parser.add_argument("--instrument-key", "-k", help="Direct instrument key (overrides symbol)")
    
    args = parser.parse_args()
    
    # Get instrument key
    if args.instrument_key:
        instrument_key = args.instrument_key
    elif args.symbol.upper() in INSTRUMENTS:
        instrument_key = INSTRUMENTS[args.symbol.upper()]
    else:
        print(f"❌ Unknown symbol: {args.symbol}")
        print(f"\nℹ️  Available symbols: {', '.join(INSTRUMENTS.keys())}")
        print(f"\nOr use --instrument-key to specify directly")
        sys.exit(1)
    
    # Fetch data
    get_historical_data(instrument_key, args.interval, args.days)
