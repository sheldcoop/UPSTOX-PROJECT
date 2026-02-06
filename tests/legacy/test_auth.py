#!/usr/bin/env python3
"""
Test Authentication System
Verifies all components are working correctly
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from auth_manager import AuthManager
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def test_auth_system():
    """Run comprehensive authentication tests"""

    print("\n" + "=" * 60)
    print("🧪 AUTHENTICATION SYSTEM TEST")
    print("=" * 60 + "\n")

    # Test 1: AuthManager initialization
    print("✓ Test 1: Initializing AuthManager...")
    try:
        auth = AuthManager()
        print("  ✅ AuthManager initialized successfully")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

    # Test 2: Configuration check
    print("\n✓ Test 2: Checking configuration...")
    try:
        assert auth.client_id, "Client ID missing"
        assert auth.client_secret, "Client secret missing"
        assert auth.redirect_uri, "Redirect URI missing"
        assert auth.cipher, "Encryption cipher missing"
        print(f"  ✅ Client ID: {auth.client_id[:20]}...")
        print(f"  ✅ Redirect URI: {auth.redirect_uri}")
        print(f"  ✅ Database: {auth.db_path}")
    except AssertionError as e:
        print(f"  ❌ Failed: {e}")
        return False

    # Test 3: Authorization URL generation
    print("\n✓ Test 3: Generating authorization URL...")
    try:
        auth_url = auth.get_authorization_url()
        assert "api.upstox.com" in auth_url, "Invalid URL"
        assert auth.client_id in auth_url, "Client ID not in URL"
        print(f"  ✅ URL generated: {auth_url[:80]}...")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

    # Test 4: Database connection
    print("\n✓ Test 4: Testing database...")
    try:
        import sqlite3

        conn = sqlite3.connect(auth.db_path)
        cursor = conn.cursor()

        # Check if auth_tokens table exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='auth_tokens'
        """
        )
        result = cursor.fetchone()
        assert result, "auth_tokens table not found"

        # Count tokens
        cursor.execute("SELECT COUNT(*) FROM auth_tokens WHERE is_active = 1")
        count = cursor.fetchone()[0]
        conn.close()

        print(f"  ✅ Database connected")
        print(f"  ✅ Active tokens: {count}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

    # Test 5: Token retrieval (may not exist yet)
    print("\n✓ Test 5: Checking for existing tokens...")
    try:
        token = auth.get_valid_token()
        if token:
            print(f"  ✅ Valid token found: {token[:30]}...")
        else:
            print(f"  ⚠️  No token found (run ./authenticate.sh to authenticate)")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

    # Test 6: Encryption test
    print("\n✓ Test 6: Testing encryption...")
    try:
        test_data = "test_token_12345"
        encrypted = auth.cipher.encrypt(test_data.encode())
        decrypted = auth.cipher.decrypt(encrypted).decode()
        assert decrypted == test_data, "Encryption/decryption mismatch"
        print(f"  ✅ Encryption working correctly")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)

    print("\n📋 Next Steps:")
    print("   1. Run: ./authenticate.sh")
    print("   2. Login to Upstox in browser")
    print("   3. Test with: python3 scripts/auth_manager.py check")
    print()

    return True


if __name__ == "__main__":
    success = test_auth_system()
    sys.exit(0 if success else 1)
