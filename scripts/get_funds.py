#!/usr/bin/env python3
"""
Fetch Upstox Fund & Margin Information
Displays available balance, margin, and fund details
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth_manager import AuthManager
import requests
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_fund_margin():
    """Fetch fund and margin details from Upstox API"""
    
    # Initialize auth manager
    auth = AuthManager()
    
    # Get valid token
    token = auth.get_valid_token()
    if not token:
        print("❌ No valid token found. Please authenticate first:")
        print("   ./authenticate.sh")
        return None
    
    # API endpoint
    url = "https://api.upstox.com/v2/user/get-funds-and-margin"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    try:
        logger.info("🔄 Fetching funds and margin...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") == "success":
            fund_data = data.get("data", {})
            
            print("\n" + "="*60)
            print("💰 UPSTOX FUND & MARGIN DETAILS")
            print("="*60)
            
            # Equity funds
            equity = fund_data.get("equity", {})
            if equity:
                print("\n📊 EQUITY SEGMENT")
                print(f"   Available Margin: ₹{equity.get('available_margin', 0):,.2f}")
                print(f"   Used Margin: ₹{equity.get('used_margin', 0):,.2f}")
                print(f"   Payin Amount: ₹{equity.get('payin_amount', 0):,.2f}")
                print(f"   Span Margin: ₹{equity.get('span_margin', 0):,.2f}")
                print(f"   Adhoc Margin: ₹{equity.get('adhoc_margin', 0):,.2f}")
                print(f"   Notional Cash: ₹{equity.get('notional_cash', 0):,.2f}")
            
            # Commodity funds
            commodity = fund_data.get("commodity", {})
            if commodity:
                print("\n🌾 COMMODITY SEGMENT")
                print(f"   Available Margin: ₹{commodity.get('available_margin', 0):,.2f}")
                print(f"   Used Margin: ₹{commodity.get('used_margin', 0):,.2f}")
                print(f"   Payin Amount: ₹{commodity.get('payin_amount', 0):,.2f}")
                print(f"   Span Margin: ₹{commodity.get('span_margin', 0):,.2f}")
                print(f"   Adhoc Margin: ₹{commodity.get('adhoc_margin', 0):,.2f}")
                print(f"   Notional Cash: ₹{commodity.get('notional_cash', 0):,.2f}")
            
            print("\n" + "="*60)
            print("\n📋 Full Response:")
            print(json.dumps(fund_data, indent=2))
            
            return fund_data
        else:
            print(f"❌ API Error: {data.get('message', 'Unknown error')}")
            return None
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("❌ Authentication failed. Token may be expired.")
            print("   Run: ./authenticate.sh")
        else:
            print(f"❌ HTTP Error: {e}")
            print(f"Response: {e.response.text}")
        return None
    
    except Exception as e:
        logger.error(f"❌ Error fetching funds: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    get_fund_margin()
