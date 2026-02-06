from backend.utils.auth.manager import AuthManager
import requests

auth = AuthManager()
token = auth.get_valid_token()

if token:
    print(f"Using token: {token[:50]}...")
else:
    print("❌ No valid token found in AuthManager.")
    token = "MOCK_TOKEN"

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

url = "https://api.upstox.com/v2/user/profile"

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status code: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    print(f"Response text: {response.text}")

    if response.status_code == 200:
        data = response.json()
        print(f"Profile data: {data}")

except Exception as e:
    print(f"Error: {e}")
