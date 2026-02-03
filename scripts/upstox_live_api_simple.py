"""
Simple Upstox API - Just the essentials
Gets user profile, funds, and holdings from live Upstox API
"""

import requests
import logging
from typing import Dict, Optional, List
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.auth_manager import AuthManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleUpstoxAPI:
    """Simple Upstox API client - just the basics"""

    BASE_URL = "https://api.upstox.com/v2"

    def __init__(self):
        self.auth_manager = AuthManager()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with fresh token"""
        token = self.auth_manager.get_valid_token()
        if not token:
            logger.error("No valid token available. Please run oauth_server.py")
            return {}

        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        }

    def get_profile(self) -> Optional[Dict]:
        """Get user profile (name, email, user_id)"""
        try:
            headers = self._get_headers()
            if not headers:
                return None

            response = requests.get(
                f"{self.BASE_URL}/user/profile", headers=headers, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(
                    f"Profile fetched for user: {data.get('data', {}).get('user_name', 'Unknown')}"
                )
                return data.get("data")
            else:
                logger.error(
                    f"Profile failed: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Profile error: {e}")
            return None

    def get_funds(self) -> Optional[Dict]:
        """Get funds and margin info"""
        try:
            headers = self._get_headers()
            if not headers:
                return None

            response = requests.get(
                f"{self.BASE_URL}/user/get-funds-and-margin",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                funds = data.get("data")
                if funds:
                    logger.info(
                        f"Funds fetched - Available: ₹{funds.get('available_margin', 0):,.2f}"
                    )
                return funds
            else:
                logger.error(f"Funds failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Funds error: {e}")
            return None

    def get_holdings(self) -> List[Dict]:
        """Get current stock holdings"""
        try:
            headers = self._get_headers()
            if not headers:
                return []

            response = requests.get(
                f"{self.BASE_URL}/portfolio/long-term-holdings",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                holdings = data.get("data", [])
                logger.info(f"Holdings fetched: {len(holdings)} positions")
                return holdings
            else:
                logger.error(f"Holdings failed: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Holdings error: {e}")
            return []


# Test the API
if __name__ == "__main__":
    api = SimpleUpstoxAPI()

    print("🚀 Testing Simple Upstox API...")

    print("\n📋 User Profile:")
    profile = api.get_profile()
    if profile:
        print(f"   Name: {profile.get('user_name')}")
        print(f"   Email: {profile.get('email')}")
        print(f"   User ID: {profile.get('user_id')}")

    print("\n💰 Funds & Margin:")
    funds = api.get_funds()
    if funds:
        print(f"   Available Margin: ₹{funds.get('available_margin', 0):,.2f}")
        print(f"   Used Margin: ₹{funds.get('used_margin', 0):,.2f}")

    print("\n📊 Holdings:")
    holdings = api.get_holdings()
    print(f"   Total Holdings: {len(holdings)}")
    if holdings:
        for h in holdings[:3]:  # Show first 3
            print(
                f"   - {h.get('tradingsymbol', 'Unknown')}: {h.get('quantity', 0)} shares"
            )
