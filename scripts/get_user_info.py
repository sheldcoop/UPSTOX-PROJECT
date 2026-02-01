#!/usr/bin/env python3
"""
Fetch Upstox User Profile Information
Displays account details, email, name, etc.
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


def get_user_profile():
    """Fetch user profile from Upstox API"""
    
    # Initialize auth manager
    auth = AuthManager()
    
    # Get valid token
    token = auth.get_valid_token()
    if not token:
        print("❌ No valid token found. Please authenticate first:")
        print("   ./authenticate.sh")
        return None
    
    # API endpoint
    url = "https://api.upstox.com/v2/user/profile"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    try:
        logger.info("🔄 Fetching user profile...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") == "success":
            user_data = data.get("data", {})
            
            print("\n" + "="*60)
            print("👤 UPSTOX USER PROFILE")
            print("="*60)
            
            print(f"\n📧 Email: {user_data.get('email', 'N/A')}")
            print(f"👤 Name: {user_data.get('user_name', 'N/A')}")
            print(f"📱 User ID: {user_data.get('user_id', 'N/A')}")
            print(f"🏢 User Type: {user_data.get('user_type', 'N/A')}")
            print(f"📊 Broker: {user_data.get('broker', 'N/A')}")
            
            # Exchange information
            exchanges = user_data.get('exchanges', [])
            if exchanges:
                print(f"\n📈 Enabled Exchanges: {', '.join(exchanges)}")
            
            # Products
            products = user_data.get('products', [])
            if products:
                print(f"💼 Enabled Products: {', '.join(products)}")
            
            # Additional details
            if user_data.get('is_active'):
                print(f"\n✅ Account Status: Active")
            
            print("\n" + "="*60)
            print("\n📋 Full Response:")
            print(json.dumps(user_data, indent=2))
            
            return user_data
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
        logger.error(f"❌ Error fetching profile: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    get_user_profile()
