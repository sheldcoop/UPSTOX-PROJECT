from scripts.auth_manager import AuthManager
import time
import base64
import json

auth = AuthManager()
token = auth.get_valid_token()
print("Token length:", len(token) if token else 0)

if token:
    try:
        # Decode JWT manually
        parts = token.split(".")
        if len(parts) >= 2:
            # Add padding if needed
            payload = parts[1]
            payload += "=" * (4 - len(payload) % 4)
            decoded_bytes = base64.urlsafe_b64decode(payload)
            decoded = json.loads(decoded_bytes)

            current_time = int(time.time())
            exp_time = decoded.get("exp", 0)
            print(f"Current time: {current_time}")
            print(f"Token expires: {exp_time}")
            print(f"Time left: {exp_time - current_time} seconds")
            print(f"Is expired: {current_time >= exp_time}")
            print(f'Subject: {decoded.get("sub", "Unknown")}')
    except Exception as e:
        print(f"Token decode error: {e}")
