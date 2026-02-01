# 🔐 Authentication & User Setup Guide

## Current Status

**❌ NOT AUTHENTICATED** - You're seeing empty data because:
1. No connection to Upstox API (not logged in)
2. Portfolio data is from paper trading system (virtual money)
3. User details need authentication first

## What You're Missing

Without authentication, you DON'T have:
- ✗ Real portfolio data (holdings, P&L, positions)
- ✗ User profile (name, email, account details)
- ✗ Live market data from Upstox
- ✗ Order placement capability
- ✗ Real-time account balance

With authentication, you WILL have:
- ✓ Real portfolio from your Upstox account
- ✓ User profile information
- ✓ Live positions and holdings
- ✓ Order history and trades
- ✓ Account balance and margins

## How to Authenticate (3 Steps)

### Step 1: Run Authentication Script

```bash
cd /Users/prince/Desktop/UPSTOX-project
./authenticate.sh
```

This will:
1. Open your browser
2. Redirect to Upstox login
3. Ask you to authorize the app
4. Store tokens securely

### Step 2: Login to Upstox

In the browser:
1. Enter your Upstox mobile number/email
2. Enter your password
3. Click "Authorize"
4. You'll be redirected back

### Step 3: Verify Connection

```bash
# Check authentication status
python3 scripts/auth_manager.py --action status

# Test API connection
curl http://localhost:5001/api/portfolio
```

## After Authentication

Once authenticated, the dashboard will show:

**Portfolio Value**: Your real portfolio value from Upstox
**Today's P&L**: Actual profit/loss for today
**Open Positions**: Your real positions (options, stocks, futures)
**User Profile**: Your name and account details
**Orders**: Your real order history
**Holdings**: Your actual holdings

## Features Requiring Authentication

1. **Portfolio API** (`/api/portfolio`)
   - Real account balance
   - Holdings value
   - Day P&L
   - Total returns

2. **User API** (`/api/user/profile`)
   - User name
   - Email
   - Account type
   - Upstox client ID

3. **Positions API** (`/api/positions`)
   - Live positions
   - Unrealized P&L
   - Current prices
   - Quantity held

4. **Orders API** (`/api/orders`)
   - Order history
   - Order status
   - Filled/pending orders

5. **Live Market Data**
   - Real-time prices
   - Options chain
   - Greeks calculation
   - IV data

## Paper Trading vs Live Trading

**Current Mode: Paper Trading**
- Virtual ₹100,000 balance
- No real money risk
- Practice strategies
- Test features

**After Authentication: Live Mode**
- Real Upstox account
- Real money trades
- Live portfolio data
- Actual P&L

## Troubleshooting

### "No authentication" error
```bash
# Run authentication
./authenticate.sh
```

### "Token expired" error
```bash
# Refresh token
python3 scripts/auth_manager.py --action refresh
```

### "API not responding"
```bash
# Restart servers
./start.sh
```

## Security Notes

- Tokens are encrypted using Fernet (AES)
- Stored in `~/.upstox_key`
- Database: `market_data.db` (auth_tokens table)
- Never commit credentials to git

## Quick Commands

```bash
# Authenticate (first time)
./authenticate.sh

# Check auth status
export UPSTOX_CLIENT_ID='33b9a757-1a99-47dc-b6fa-c3cf3dcaf6b4'
export UPSTOX_CLIENT_SECRET='t6hxe1b1ky'
python3 scripts/auth_manager.py --action status

# Refresh token
python3 scripts/auth_manager.py --action refresh

# Start platform
./start.sh
```

## Next Steps

1. **Run `./authenticate.sh`** - Connect to Upstox
2. **Refresh dashboard** - See real portfolio data
3. **Explore features** - All components will show live data
4. **Place orders** - Use real trading features

---

**Remember**: Paper trading (current) = Safe practice mode with fake money
**After auth**: Live trading = Real Upstox account with real money
