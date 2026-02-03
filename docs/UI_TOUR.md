# 🎬 UI Tour - What You'll See

## Dashboard Home Page

When you open `http://localhost:9000/`, you'll see:

### Left Sidebar (250px fixed)
```
📈 Upstox
Trading Platform
─────────────────
MAIN
🏠 Dashboard        [ACTIVE]
📥 Downloads
📊 Positions  
💱 Options
─────────────────
TOOLS
🧪 Backtest
🎯 Strategies
🔔 Alerts

[Footer: v1.0, Production]
```

### Main Content Area

#### Header Bar
```
📊 Dashboard          ● Market Closed    ⟳ Refresh
```

#### Statistics Grid (4 cards)
```
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│  Portfolio      │   Cash          │  Today's P&L    │  Total          │
│  Value          │  Available      │                 │  Invested       │
│                 │                 │                 │                 │
│  ₹ 0            │  ₹ 0            │  ₹ 0            │  ₹ 0            │
│  0% up today    │  Ready to       │  0%             │  Across all     │
│                 │  invest         │                 │  positions      │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

#### Market Status Section
```
📈 Market Status
├─ NIFTY 50:      19,250.15
├─ Sensex:        63,412.05
├─ Bank Nifty:    48,620.30
└─ VIX:           16.45
```

#### Recent Activity Section
```
📝 Recent Activity
├─ Last Trade:     —
├─ Open Positions: 0
├─ Win Rate:       —
└─ Alerts:         3
```

---

## Downloads Page

Click "📥 Downloads" in the sidebar, you'll see:

### Page Header
```
📊 Data Download Center

Download OHLC (Open, High, Low, Close) historical data for 
backtesting, analysis, and strategy development. 
Supports multiple timeframes and export formats.
```

### Left Column (2/3 width) - Download Form
```
📥 Download Historical Data
┌──────────────────────────────┐
│ ℹ️ How it works               │
│ Select symbols, date range,  │
│ and timeframe. Data will be  │
│ downloaded from Yahoo Finance│
│ and saved locally.           │
└──────────────────────────────┘

Symbols (Enter stock symbol)
┌──────────────────────────────┐
│ [INFY ✕] [TCS ✕] [Input...] │
└──────────────────────────────┘
Press Enter or comma to add symbols

Start Date    │  End Date
┌─────────┐  │  ┌─────────┐
│ [Date]  │  │  │ [Date]  │
└─────────┘  │  └─────────┘

Timeframe              │  Export Format
┌─────────────────┐  │  ┌─────────────────┐
│ ▼ Daily (1D)    │  │  │ ▼ Parquet       │
└─────────────────┘  │  └─────────────────┘

Options
☑ Save to Database
☑ Validate Data

[Status Message Area]

┌──────────────────────┬──────────────────┐
│ ⬇️  Download Data    │  Clear Form      │
└──────────────────────┴──────────────────┘
```

### Right Column (1/3 width) - Stats & Shortcuts
```
📈 Quick Stats
┌────────────────────┐
│  0                 │
│  Symbols Selected  │
└────────────────────┘
┌────────────────────┐
│  0                 │
│  Days Range        │
└────────────────────┘
┌────────────────────┐
│  0                 │
│  Files Downloaded  │
└────────────────────┘

⭐ Popular Symbols
[INFY] [TCS] [RELIANCE]
[HDFCBANK] [ICICIBANK] [SBIN]
```

### Bottom Section - Download History
```
📁 Download History
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   📄         │  │   📄         │  │   📄         │  
│ INFY_1d.csv  │  │ TCS_5m.csv   │  │ RELIANCE_...│
│ 245.2 KB     │  │ 512.1 KB     │  │ 892.4 KB     │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## Color Scheme

**Dark Theme**
- Background: `#0f1419` (very dark blue)
- Cards: `#1a1f2e` (dark blue)
- Borders: `#2a3142` (subtle)
- Text: `#e0e0e0` (light gray)
- Muted: `#999` (gray)

**Accents**
- Primary: Gradient `#667eea` → `#764ba2` (purple/blue)
- Success: `#4ade80` (green)
- Danger: `#f87171` (red)

---

## Interactive Features

### Navigation
- Click any nav item to switch pages
- Active nav item highlighted
- Smooth transitions

### Form Interaction (Downloads Page)
```
1. Type symbol in input → Press Enter or , → Symbol added as tag
2. Click ✕ on tag → Symbol removed
3. Select dates, timeframe, format
4. Click "Download Data" → Shows loading status
5. On success → File appears in Download History
6. On error → Shows error message
```

### Dashboard Updates
- Automatic refresh every 30 seconds
- Click "⟳ Refresh" button for manual refresh
- Real-time data from `/api/portfolio`

---

## Responsive Behavior

### Desktop (>768px)
- Full sidebar (250px) with text labels
- Multi-column grids
- All features visible

### Tablet (768px-640px)
- Slightly narrower sidebar (200px)
- Single column for cards
- Stacked layout

### Mobile (<640px)
- Collapsed sidebar (60px, icon-only)
- Single column for everything
- Hamburger-style navigation
- Large touch targets

---

## Status Indicators

**Market Status Badge**
```
● Market Closed  (Red pulse animation)
● Market Open    (Green pulse animation)
```

**P&L Colors**
```
↑ Green positive P&L
↓ Red negative P&L
```

**Loading Animation**
```
⟳ (Spinning icon while loading)
```

---

## Data Flow

```
Dashboard
├─ loads on page start
├─ fetches /api/portfolio
└─ auto-refreshes every 30s

Downloads Page
├─ displays download form
├─ on submit: POST to /api/download/stocks
├─ shows loading state
├─ fetches /api/download/history
└─ displays downloaded files
```

---

## Keyboard Shortcuts (Future)

```
Ctrl+K    - Quick search
Ctrl+D    - Download page
Ctrl+P    - Positions page
Ctrl+R    - Refresh data
```

(Currently keyboard shortcuts are not implemented, but UI is ready for them)
