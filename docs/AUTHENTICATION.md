# Authentication Guide

**UPSTOX Trading Platform**

---

## Quick Start

### How to Authenticate

**Option 1: Web Browser (Recommended)**
```bash
# Start OAuth server
python3.11 scripts/oauth_server.py

# Open browser to:
http://localhost:5050/auth/start

# Follow Upstox login → Token saved automatically to database
```

**Option 2: Command Line**
```bash
# Get authorization URL
python3.11 scripts/auth_manager.py url

# Copy URL to browser → Get code → Exchange for token
python3.11 scripts/auth_manager.py exchange <code>
```

---

## How It Works

### AuthManager (Database-Based)

All scripts now use **AuthManager** for authentication:

```python
from scripts.auth_manager import AuthManager

# Initialize
auth = AuthManager()

# Get valid token (auto-refreshes if needed)
token = auth.get_valid_token()

if not token:
    print("❌ Not authenticated. Run OAuth server.")
    sys.exit(1)

# Use token
headers = {"Authorization": f"Bearer {token}"}
```

**Features**:
- ✅ Auto-refresh on expiry
- ✅ Encrypted storage in `market_data.db`
- ✅ Multi-user support
- ✅ Token expiry tracking

---

## OAuth Flow

```
User → OAuth Server (5050) → Upstox Authorization
  ↓
Upstox Callback → /auth/callback
  ↓
AuthManager.exchange_code_for_token()
  ↓
AuthManager.save_token() → market_data.db (encrypted)
  ↓
Redirect to Dashboard (5001)
```

### Components

**1. OAuth Server** (`scripts/oauth_server.py`)
- **Port**: 5050
- **Endpoints**:
  - `GET /auth/start` - Initiates OAuth flow
  - `GET /auth/callback` - Receives auth code from Upstox
  - `GET /auth/status` - Check authentication status

**2. AuthManager** (`scripts/auth_manager.py`)
- Token management, encryption, auto-refresh
- **Database**: `market_data.db` → `auth_tokens` table
- **Encryption**: Fernet (requires `ENCRYPTION_KEY` in `.env`)

**3. Flask Auth Blueprint** (`scripts/blueprints/auth.py`)
- API endpoints for frontend
- **Endpoints**:
  - `DELETE /api/logout` - Revoke token
  - `GET /api/auth/status` - Check auth status

---

## Check Token Status

```bash
# Check if token is valid
python3.11 scripts/auth_manager.py check

# Or via API
curl http://localhost:8000/api/auth/status

# Or via OAuth server
curl http://localhost:5050/auth/status
```

---

## Database Schema

### `auth_tokens` Table

```sql
CREATE TABLE auth_tokens (
    user_id TEXT PRIMARY KEY,
    access_token TEXT NOT NULL,      -- Encrypted
    refresh_token TEXT NOT NULL,     -- Encrypted
    expires_at REAL NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at REAL,
    updated_at REAL
);
```

**Current Token**:
- **user_id**: default
- **is_active**: 1 (active)
- **expires**: Auto-refreshed when needed
- **encryption**: Fernet symmetric encryption

---

## Troubleshooting

### Issue: "No valid token found"

**Solution**:
```bash
# Run OAuth server
python3.11 scripts/oauth_server.py

# Open browser to:
http://localhost:5050/auth/start

# Complete Upstox login
```

---

### Issue: "ENCRYPTION_KEY not found"

**Solution**:
```bash
# Generate encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env
ENCRYPTION_KEY=<generated_key>
```

---

### Issue: "Token expired"

**Solution**: AuthManager auto-refreshes tokens. If it fails:
```bash
# Re-authenticate
python3.11 scripts/oauth_server.py
# Open: http://localhost:5050/auth/start
```

---

### Issue: Script fails with "Authentication error"

**Check**:
1. Is OAuth server running? (`python3.11 scripts/oauth_server.py`)
2. Is token valid? (`python3.11 scripts/auth_manager.py check`)
3. Is database accessible? (`ls -la market_data.db`)
4. Is encryption key set? (`grep ENCRYPTION_KEY .env`)

---

## Environment Variables

### Required

```bash
# Upstox API Credentials
UPSTOX_CLIENT_ID=your-client-id
UPSTOX_CLIENT_SECRET=your-client-secret
UPSTOX_REDIRECT_URI=http://localhost:5050/auth/callback

# Encryption (for token storage)
ENCRYPTION_KEY=<generated-fernet-key>
```

### Optional

```bash
# Base URL (for deployment)
BASE_URL=http://localhost:5050

# OAuth URL
OAUTH_URL=http://localhost:5050/auth/start
```

---

## Security Best Practices

1. **Never commit tokens** to version control
2. **Use `.env` file** for credentials (already in `.gitignore`)
3. **Rotate encryption key** periodically
4. **Monitor token expiry** (AuthManager handles this)
5. **Revoke tokens** when not in use (`DELETE /api/logout`)

---

## Migration from Old Pattern

### Old Pattern (Broken)
```python
# ❌ OLD - Don't use
access_token = os.getenv("UPSTOX_ACCESS_TOKEN")
if not token:
    print("❌ UPSTOX_ACCESS_TOKEN not set")
    sys.exit(1)
```

### New Pattern (Working)
```python
# ✅ NEW - Use this
from scripts.auth_manager import AuthManager

auth = AuthManager()
access_token = auth.get_valid_token()

if not access_token:
    print("❌ No valid token. Run: python3 scripts/oauth_server.py")
    sys.exit(1)
```

---

## Scripts Using AuthManager

All scripts now use AuthManager:

- ✅ `scripts/brokerage_calculator.py`
- ✅ `scripts/holdings_manager.py`
- ✅ `scripts/order_manager.py`
- ✅ `scripts/account_fetcher.py`
- ✅ `scripts/market_depth_fetcher.py`
- ✅ `scripts/gtt_orders_manager.py`
- ✅ `scripts/websocket_quote_streamer.py`
- ✅ `scripts/get_funds.py`
- ✅ `scripts/candle_fetcher.py`
- ✅ `dashboard_ui/services/movers.py`
- ✅ 20+ more files...

---

## FAQ

**Q: Do I need to set `UPSTOX_ACCESS_TOKEN` env var?**  
A: No! AuthManager handles tokens automatically. Just run OAuth server once.

**Q: How long do tokens last?**  
A: Upstox tokens expire after 24 hours. AuthManager auto-refreshes them.

**Q: Can I use multiple accounts?**  
A: Yes! AuthManager supports multi-user via `user_id` field.

**Q: Where are tokens stored?**  
A: Encrypted in `market_data.db` → `auth_tokens` table.

**Q: What if I delete the database?**  
A: Re-authenticate via OAuth server (`http://localhost:5050/auth/start`).

---

## Support

For issues:
1. Check [auth_audit_report.md](file:///Users/prince/.gemini/antigravity/brain/9662ef4a-0802-4685-9440-f5c1904a24d8/auth_audit_report.md)
2. Run diagnostics: `python3.11 scripts/auth_manager.py check`
3. Check OAuth server logs
4. Verify `.env` configuration
