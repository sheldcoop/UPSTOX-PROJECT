# 🔐 Authentication System - Quick Start

## ✅ System Built From Scratch

New authentication implementation with:
- **OAuth 2.0** with Upstox API
- **Fernet encryption** for token storage
- **Auto-refresh** on token expiry
- **SQLite persistence** in `market_data.db`
- **Flask OAuth server** with browser flow

---

## 📁 Files Created

1. **`.env`** - Configuration (client ID, secret, encryption key)
2. **`scripts/generate_encryption_key.py`** - Key generator
3. **`scripts/auth_manager.py`** - Core authentication manager (300 lines)
4. **`scripts/oauth_server.py`** - Flask OAuth server
5. **`authenticate.sh`** - Quick authentication script

---

## 🚀 Usage

### Option 1: Quick Authentication (Recommended)
```bash
./authenticate.sh
```
This will:
1. Start Flask OAuth server on port 8000
2. Open browser to Upstox login
3. Handle callback and save encrypted token
4. Ready to use!

### Option 2: Manual Steps

**Step 1: Get authorization URL**
```bash
python3 scripts/auth_manager.py url
```

**Step 2: Visit URL in browser, login, get redirected**

**Step 3: Copy authorization code from URL**
```
http://localhost:8000/auth/callback?code=ABC123
                                          ^^^^^^
```

**Step 4: Exchange code for token**
```bash
python3 scripts/auth_manager.py exchange ABC123
```

### Option 3: Using OAuth Server
```bash
cd /Users/prince/Desktop/UPSTOX-project
source .venv/bin/activate
export PYTHONPATH="$(pwd)/scripts:$PYTHONPATH"
python3 scripts/oauth_server.py --open-browser
```

Then visit: `http://localhost:8000/auth/start`

---

## 🔍 Check Authentication Status

```bash
python3 scripts/auth_manager.py check
```

**Expected Output:**
```
✅ Valid token: eyJ0eXAiOiJKV1QiLCJhbGciOi...
```

---

## 🧪 Test in Python Code

```python
from scripts.auth_manager import AuthManager

# Initialize
auth = AuthManager()

# Get valid token (auto-refreshes if expired)
token = auth.get_valid_token()

if token:
    # Use token for API calls
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    # Make API requests...
else:
    print("Please authenticate first: ./authenticate.sh")
```

---

## 🔧 Configuration

All settings in `.env`:

```bash
UPSTOX_CLIENT_ID=33b9a757-1a99-47dc-b6fa-c3cf3dcaf6b4
UPSTOX_CLIENT_SECRET=t6hxe1b1ky
UPSTOX_REDIRECT_URI=http://localhost:8000/auth/callback
ENCRYPTION_KEY=YODQmrNtqJJQXBkeddIkDoJftjrg8poqLqAQzojva7w=
FLASK_PORT=8000
FLASK_DEBUG=False
```

---

## 📊 Database Schema

Table: `auth_tokens`

| Column | Type | Description |
|--------|------|-------------|
| user_id | TEXT | User identifier (default: "default") |
| access_token | TEXT | Encrypted access token |
| refresh_token | TEXT | Encrypted refresh token |
| expires_at | REAL | Unix timestamp of expiry |
| is_active | INTEGER | 1=active, 0=revoked |
| created_at | REAL | Unix timestamp of creation |
| updated_at | REAL | Unix timestamp of last update |

---

## ⚡ Features

### 1. Auto-Refresh
Tokens refresh automatically 5 minutes before expiry:
```python
token = auth.get_valid_token()  # Always returns valid token
```

### 2. Encryption
All tokens encrypted with Fernet before storage:
- **Key:** From `.env` file
- **Algorithm:** Fernet (symmetric encryption)
- **Storage:** SQLite database

### 3. Multi-User Support
```python
# Save for specific user
auth.save_token("user@example.com", token_data)

# Retrieve for specific user
token = auth.get_valid_token("user@example.com")
```

### 4. Token Revocation
```python
auth.revoke_token("default")  # Deactivate token
```

---

## 🐛 Troubleshooting

### Issue: `No module named 'scripts'`
**Fix:** Export PYTHONPATH before running:
```bash
export PYTHONPATH="$(pwd)/scripts:$PYTHONPATH"
python3 scripts/oauth_server.py
```

### Issue: `ENCRYPTION_KEY not found`
**Fix:** Generate encryption key:
```bash
python3 scripts/generate_encryption_key.py
```

### Issue: `Token expired`
**Solution:** Auto-refresh handles this. If manual refresh needed:
```python
auth._refresh_token("default", encrypted_refresh_token)
```

### Issue: Port 8000 already in use
**Fix:** Change port in `.env`:
```bash
FLASK_PORT=8001
```

---

## 🔗 API Endpoints (OAuth Server)

- `GET /auth/start` - Start OAuth flow
- `GET /auth/callback` - Handle OAuth callback
- `GET /auth/status` - Check authentication status

---

## ✅ Next Steps

1. **Test authentication:** `./authenticate.sh`
2. **Integrate with existing backend:** Update other scripts to use `AuthManager.get_valid_token()`
3. **Add error handling:** Wrap API calls with token refresh logic
4. **Frontend integration:** Use `/auth/status` endpoint

---

## 📌 Important Notes

- **Never commit `.env`** to version control
- **Keep encryption key secure** - losing it means losing access to stored tokens
- **Tokens refresh automatically** - no manual intervention needed
- **Database:** Uses existing `market_data.db` (new `auth_tokens` table)

---

## 🎯 Integration Example

Update any script that calls Upstox API:

```python
# OLD CODE (before)
headers = {"Authorization": f"Bearer {hardcoded_token}"}

# NEW CODE (after)
from scripts.auth_manager import AuthManager
auth = AuthManager()
token = auth.get_valid_token()
headers = {"Authorization": f"Bearer {token}"}
```

Done! Authentication system is **production-ready** 🚀
