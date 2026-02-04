"""
Centralized Authentication Helper
Single source of truth for all authentication operations
"""

import os
import sys
from typing import Optional, Dict

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from auth_manager import AuthManager


class AuthHelper:
    """
    Singleton authentication helper.
    Provides simple interface for all auth operations.
    
    Usage:
        from scripts.auth_helper import auth
        
        # Get token
        token = auth.get_token()
        
        # Get headers
        headers = auth.get_headers()
        
        # Check auth status
        if auth.is_authenticated():
            print("Logged in!")
    """
    
    _instance = None
    _auth_manager = None
    
    def __new__(cls):
        """Singleton pattern - only one instance exists"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._auth_manager = AuthManager()
        return cls._instance
    
    def get_token(self, user_id: str = "default") -> Optional[str]:
        """
        Get valid access token (auto-refreshes if needed).
        
        Args:
            user_id: User identifier (default: "default")
            
        Returns:
            Access token or None if not authenticated
        """
        return self._auth_manager.get_valid_token(user_id)
    
    def get_headers(self, user_id: str = "default") -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Args:
            user_id: User identifier (default: "default")
            
        Returns:
            Dict with Authorization and Accept headers
            
        Raises:
            Exception: If not authenticated
        """
        token = self.get_token(user_id)
        if not token:
            raise Exception(
                "Not authenticated. Please run: python3 scripts/oauth_server.py\n"
                "Then open: http://localhost:5050/auth/start"
            )
        
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
    
    def is_authenticated(self, user_id: str = "default") -> bool:
        """
        Check if user is authenticated.
        
        Args:
            user_id: User identifier (default: "default")
            
        Returns:
            True if authenticated, False otherwise
        """
        return self.get_token(user_id) is not None
    
    def revoke(self, user_id: str = "default") -> bool:
        """
        Revoke/logout user.
        
        Args:
            user_id: User identifier (default: "default")
            
        Returns:
            True if successful
        """
        return self._auth_manager.revoke_token(user_id)
    
    def get_auth_url(self) -> str:
        """
        Get OAuth authorization URL.
        
        Returns:
            Authorization URL to open in browser
        """
        return self._auth_manager.get_authorization_url()

    def exchange_code_for_token(self, auth_code: str) -> Dict[str, any]:
        return self._auth_manager.exchange_code_for_token(auth_code)

    def save_token(self, user_id: str, token_data: Dict[str, any]):
        return self._auth_manager.save_token(user_id, token_data)


# Singleton instance - import this everywhere
auth = AuthHelper()


# Convenience functions (optional - can use auth.method() directly)
def get_token() -> Optional[str]:
    """Get valid access token"""
    return auth.get_token()


def get_headers() -> Dict[str, str]:
    """Get authentication headers"""
    return auth.get_headers()


def is_authenticated() -> bool:
    """Check if authenticated"""
    return auth.is_authenticated()


if __name__ == "__main__":
    # Demo usage
    print("🔐 Authentication Helper Demo\n")
    
    if auth.is_authenticated():
        print("✅ Authenticated!")
        print(f"   Token: {auth.get_token()[:20]}...")
        print(f"   Headers: {auth.get_headers()}")
    else:
        print("❌ Not authenticated")
        print(f"   Auth URL: {auth.get_auth_url()}")
