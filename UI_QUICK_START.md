# 🚀 Quick Start - Test the New UI

## Prerequisites
```bash
# Make sure requirements are installed
cd /Users/prince/Desktop/UPSTOX-project
pip install -q -r requirements.txt
```

## Start the Server

```bash
# Option 1: Default port (8000)
python3 scripts/api_server.py

# Option 2: Custom port (9000)
python3 scripts/api_server.py --port 9000

# Option 3: Custom host and port
python3 scripts/api_server.py --host 127.0.0.1 --port 9000
```

Server will start with output:
```
 * Running on http://0.0.0.0:9000
 * Press CTRL+C to quit
```

## Access the Dashboard

Open your browser to:
- **Dashboard**: http://localhost:9000
- **Downloads**: http://localhost:9000/api/page/downloads

Or use VS Code's Simple Browser:
1. Open Command Palette (Cmd+Shift+P)
2. Type "Open with Live Server" or "Simple Browser"
3. Navigate to `http://localhost:9000`

## Test the Features

### 1. Dashboard Navigation
- ✅ Click "📥 Downloads" in sidebar
- ✅ Click "📊 Dashboard" to return
- ✅ Notice active page highlight
- ✅ Header title updates dynamically

### 2. Real-time Portfolio Data
- ✅ Click "⟳ Refresh" button
- ✅ Portfolio stats should update
- ✅ Data auto-refreshes every 30 seconds
- ✅ Check browser console for API calls (F12 → Console)

### 3. Downloads Page Form
- ✅ Type "INFY" in symbol input → Press Enter
- ✅ Symbol appears as tag "INFY ✕"
- ✅ Click "✕" to remove symbol
- ✅ Click popular symbols (INFY, TCS, RELIANCE, etc)
- ✅ Set date range (default: last 30 days)
- ✅ Select timeframe (1D, 1H, 30M, 15M, 5M, 1M)
- ✅ Choose export format (Parquet, CSV, JSON)
- ✅ Check "Save to Database" and "Validate Data"
- ✅ Click "Download Data" button

### 4. Download Submission (if API ready)
- 📥 Form will show "Downloading data... This may take a minute."
- 📥 On success: "✅ Downloaded X rows for Y symbols"
- 📥 Downloaded files appear in "Download History" section
- 📥 On error: Error message is displayed

## Troubleshooting

### Server Won't Start
```bash
# Check if port is in use
lsof -i :9000

# Kill existing process
pkill -f "api_server.py"

# Try different port
python3 scripts/api_server.py --port 8888
```

### Page Blank or Errors
```bash
# Check server logs
tail -f /tmp/server.log

# Clear browser cache and refresh
Cmd+Shift+Delete (open cache clearing)
Refresh page (Cmd+R)
```

### API Calls Failing
```bash
# Test API endpoint manually
curl http://localhost:9000/api/portfolio

# Check if blueprints are loaded
curl http://localhost:9000/api/health
```

## Browser Console Debugging

Open browser Developer Tools (F12 or Cmd+Shift+I):

**Console tab:**
- Shows any JavaScript errors
- Shows API fetch requests
- Shows console logs from page scripts

**Network tab:**
- Shows HTTP requests to backend
- Shows `/api/portfolio` calls
- Shows `/api/page/downloads` render
- Shows download history requests

**Elements tab:**
- Inspect page structure
- See dark theme CSS
- Verify responsive breakpoints

## Responsive Testing

### Desktop View
- Press F12 to open DevTools
- Click device toolbar icon
- Select "Responsive" → 1400x900

### Tablet View
- Select "iPad" or "iPad Pro" (768x1024)
- Sidebar should narrow to 200px
- Cards stack to single column

### Mobile View
- Select "iPhone 12" or any mobile
- Sidebar collapses to 60px (icon-only)
- All content stacks vertically
- Navigation becomes compact

## Testing Checklist

### UI/UX
- [ ] Sidebar navigation works
- [ ] Page transitions are smooth
- [ ] Dark theme is applied
- [ ] Gradients and colors are visible
- [ ] Status indicators pulse correctly
- [ ] Hover effects work on cards
- [ ] Mobile view is responsive

### Functionality
- [ ] Portfolio data loads
- [ ] Refresh button works
- [ ] Downloads form accepts input
- [ ] Symbol tags work (add/remove)
- [ ] Date picker works
- [ ] Form submission works
- [ ] Navigation without page reload

### Data Integration
- [ ] `/api/portfolio` returns data
- [ ] `/api/page/downloads` renders
- [ ] Dashboard updates automatically
- [ ] Download history loads

## Sample Test Data

### Manual API Test
```bash
# Get portfolio data
curl -s http://localhost:9000/api/portfolio | jq .

# Get download history
curl -s http://localhost:9000/api/download/history | jq .

# Get market status
curl -s http://localhost:9000/api/health | jq .
```

### Example Response
```json
{
  "total_value": 1000000,
  "cash": 50000,
  "total_invested": 950000,
  "total_pnl": 25000,
  "positions": [],
  "orders": []
}
```

## Performance Tips

### Speed up loading
1. Close other tabs/apps
2. Use Chrome DevTools "Performance" tab
3. Check "Reduce motion" in system settings (if animations lag)

### Monitor resource usage
1. Open Activity Monitor
2. Search for "python"
3. Check CPU and Memory usage
4. Should be < 50MB for Flask app

## Next Steps After Testing

1. **Create Positions Page** - List open positions
2. **Create Options Page** - Show options chains
3. **Add WebSocket** - Real-time price updates
4. **Create Settings** - User preferences
5. **Add Notifications** - Desktop alerts for trades
6. **Mobile App** - React Native companion

---

**Status**: ✅ Ready to test! Start the server and open http://localhost:9000
