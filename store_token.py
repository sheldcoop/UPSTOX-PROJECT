import os
import sys
from scripts.auth_manager import AuthManager

# Current token details
token = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIyWkNEUTkiLCJqdGkiOiI2OTdlOTViYzFhY2FiMjBhNzE3ZTQ4NTAiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc2OTkwMzU0OCwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzY5OTgzMjAwfQ.y5xey_vjMP7kjTScnGSRdQcF1VZmod7M0DTrS17JhO0"
expires_in = 86400  # Default 24 hours

# Add scripts to path if needed
sys.path.append(os.path.join(os.getcwd(), "scripts"))

try:
    auth = AuthManager()
    token_data = {"access_token": token, "refresh_token": "", "expires_in": expires_in}

    auth.save_token("default", token_data)
    print("✅ Token stored successfully using AuthManager!")

    # Verify
    saved_token = auth.get_valid_token("default")
    if saved_token == token:
        print("✅ Verification successful: Retreived token matches.")
    else:
        print("❌ Verification failed: Retrieved token differs.")

except Exception as e:
    print(f"❌ Error: {e}")
