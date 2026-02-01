"""
Upstox OAuth 2.0 Authentication Manager
Handles token generation, refresh, encryption, and storage
"""

import os
import time
import sqlite3
import requests
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Manages Upstox OAuth 2.0 authentication with:
    - Token encryption (Fernet)
    - Auto-refresh on expiry
    - SQLite persistence
    - Error handling with retries
    """
    
    # Upstox API endpoints
    AUTH_URL = "https://api.upstox.com/v2/login/authorization/dialog"
    TOKEN_URL = "https://api.upstox.com/v2/login/authorization/token"
    
    def __init__(self, db_path: str = "market_data.db"):
        """Initialize auth manager with credentials from .env"""
        self.client_id = os.getenv("UPSTOX_CLIENT_ID")
        self.client_secret = os.getenv("UPSTOX_CLIENT_SECRET")
        self.redirect_uri = os.getenv("UPSTOX_REDIRECT_URI", "http://localhost:8000/auth/callback")
        
        # Encryption key
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            raise ValueError("ENCRYPTION_KEY not found in .env - run generate_encryption_key.py")
        
        self.cipher = Fernet(encryption_key.encode())
        
        # Database
        self.db_path = db_path
        self._init_database()
        
        logger.info("✅ AuthManager initialized")
    
    def _init_database(self):
        """Create auth_tokens table if not exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_tokens (
                user_id TEXT PRIMARY KEY,
                access_token TEXT NOT NULL,
                refresh_token TEXT NOT NULL,
                expires_at REAL NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                updated_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)
        
        conn.commit()
        conn.close()
        logger.debug("Database initialized")
    
    def get_authorization_url(self) -> str:
        """
        Generate Upstox authorization URL
        
        Returns:
            str: Full OAuth URL to redirect user
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{self.AUTH_URL}?{query_string}"
        
        logger.info(f"🔗 Authorization URL: {url}")
        return url
    
    def exchange_code_for_token(self, auth_code: str) -> Dict[str, any]:
        """
        Exchange authorization code for access + refresh tokens
        
        Args:
            auth_code: Authorization code from OAuth callback
        
        Returns:
            dict: Token response with access_token, refresh_token, expires_in
        
        Raises:
            Exception: If token exchange fails
        """
        payload = {
            "code": auth_code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code"
        }
        
        headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        logger.debug(f"🔄 Exchanging code for token: {auth_code[:6]}...")
        
        try:
            response = requests.post(self.TOKEN_URL, data=payload, headers=headers)
            response.raise_for_status()
            
            token_data = response.json()
            logger.info(f"✅ Token received: {token_data['access_token'][:20]}...")
            
            return token_data
        
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Token exchange failed: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise
    
    def save_token(self, user_id: str, token_data: Dict[str, any]):
        """
        Encrypt and save tokens to database
        
        Args:
            user_id: User identifier (email/username)
            token_data: Token response from Upstox API
        """
        # Encrypt tokens
        access_token_encrypted = self.cipher.encrypt(token_data["access_token"].encode()).decode()
        refresh_token_encrypted = self.cipher.encrypt(token_data.get("refresh_token", "").encode()).decode()
        
        # Calculate expiry time (default 24 hours if not provided)
        expires_in = token_data.get("expires_in", 86400)
        expires_at = time.time() + expires_in
        current_time = time.time()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if token already exists for this user
            cursor.execute("SELECT user_id FROM auth_tokens WHERE user_id = ?", (user_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing token
                cursor.execute("""
                    UPDATE auth_tokens 
                    SET access_token = ?, refresh_token = ?, expires_at = ?, is_active = 1, updated_at = ?
                    WHERE user_id = ?
                """, (access_token_encrypted, refresh_token_encrypted, expires_at, current_time, user_id))
                logger.info(f"✅ Token updated for user: {user_id}")
            else:
                # Insert new token
                cursor.execute("""
                    INSERT INTO auth_tokens (user_id, access_token, refresh_token, expires_at, is_active, updated_at)
                    VALUES (?, ?, ?, ?, 1, ?)
                """, (user_id, access_token_encrypted, refresh_token_encrypted, expires_at, current_time))
                logger.info(f"✅ Token created for user: {user_id}")
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Failed to save token: {e}")
            raise
        finally:
            conn.close()
        
        logger.info(f"✅ Token saved for user: {user_id} (expires: {datetime.fromtimestamp(expires_at)})")
    
    def get_valid_token(self, user_id: str = "default") -> Optional[str]:
        """
        Get valid access token, auto-refresh if expired
        
        Args:
            user_id: User identifier
        
        Returns:
            str: Decrypted access token or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT access_token, refresh_token, expires_at 
            FROM auth_tokens 
            WHERE user_id = ? AND is_active = 1
            ORDER BY updated_at DESC
            LIMIT 1
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            logger.warning(f"⚠️  No token found for user: {user_id}")
            return None
        
        access_token_encrypted, refresh_token_encrypted, expires_at = result
        current_time = time.time()
        
        # Check if expired (with 5-minute buffer)
        if current_time >= (expires_at - 300):
            logger.info("🔄 Token expired, refreshing...")
            return self._refresh_token(user_id, refresh_token_encrypted)
        
        # Decrypt and return
        access_token = self.cipher.decrypt(access_token_encrypted.encode()).decode()
        logger.debug(f"✅ Valid token retrieved for: {user_id}")
        return access_token
    
    def _refresh_token(self, user_id: str, refresh_token_encrypted: str) -> Optional[str]:
        """
        Refresh access token using refresh token
        
        Args:
            user_id: User identifier
            refresh_token_encrypted: Encrypted refresh token
        
        Returns:
            str: New access token or None if refresh fails
        """
        try:
            refresh_token = self.cipher.decrypt(refresh_token_encrypted.encode()).decode()
            
            payload = {
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token"
            }
            
            headers = {
                "accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            response = requests.post(self.TOKEN_URL, data=payload, headers=headers)
            response.raise_for_status()
            
            token_data = response.json()
            self.save_token(user_id, token_data)
            
            logger.info(f"✅ Token refreshed for: {user_id}")
            return token_data["access_token"]
        
        except Exception as e:
            logger.error(f"❌ Token refresh failed: {e}")
            return None
    
    def revoke_token(self, user_id: str = "default"):
        """
        Deactivate user's token
        
        Args:
            user_id: User identifier
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE auth_tokens SET is_active = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Token revoked for: {user_id}")


# CLI for testing
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    auth = AuthManager()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "url":
            print("\n🔗 Authorization URL:")
            print(auth.get_authorization_url())
            print("\n👉 Copy this URL to your browser to authorize")
        
        elif sys.argv[1] == "exchange" and len(sys.argv) > 2:
            code = sys.argv[2]
            token_data = auth.exchange_code_for_token(code)
            auth.save_token("default", token_data)
            print("\n✅ Token saved successfully!")
        
        elif sys.argv[1] == "check":
            token = auth.get_valid_token()
            if token:
                print(f"\n✅ Valid token: {token[:30]}...")
            else:
                print("\n❌ No valid token found")
    else:
        print("""
Usage:
  python3 scripts/auth_manager.py url              # Get authorization URL
  python3 scripts/auth_manager.py exchange <code>  # Exchange auth code for token
  python3 scripts/auth_manager.py check            # Check if token is valid
        """)
