# 📸 Frontend UI Screenshots Guide

Since this is a NiceGUI-based frontend, here's how to view and capture the UI:

## Starting the Frontend

```bash
# Terminal 1: Start API server
cd /home/runner/work/UPSTOX-PROJECT/UPSTOX-PROJECT
python scripts/api_server.py

# Terminal 2: Start frontend  
cd /home/runner/work/UPSTOX-PROJECT/UPSTOX-PROJECT
python nicegui_dashboard.py
```

The dashboard will be available at: **http://localhost:5001**

## Page URLs

### Dashboard
- 🏠 **Home**: `http://localhost:5001/`
- 💚 **Health**: `http://localhost:5001/health`

### Trading
- 📊 **Positions**: `http://localhost:5001/positions`
- 📝 **Orders & Alerts**: `http://localhost:5001/orders-alerts`
- ⚡ **Live Trading**: `http://localhost:5001/live-trading`

### Data
- 📡 **Live Data**: `http://localhost:5001/live-data`
- 🔗 **Option Chain**: `http://localhost:5001/option-chain`
- 📜 **Historical Options**: `http://localhost:5001/historical-options`
- 📥 **Downloads**: `http://localhost:5001/downloads`

### Strategies
- 🔬 **Backtest**: `http://localhost:5001/backtest`
- 📊 **Signals**: `http://localhost:5001/signals`
- 🏗️ **Strategy Builder**: `http://localhost:5001/strategies`

### Analytics
- 📈 **Performance**: `http://localhost:5001/analytics`
- 🎲 **Option Greeks**: `http://localhost:5001/option-greeks`

### Upstox
- 🔴 **Upstox Live**: `http://localhost:5001/upstox-live`
- 👤 **User Profile**: `http://localhost:5001/user-profile`

### Tools
- 🤖 **AI Chat**: `http://localhost:5001/ai-chat`
- 🔧 **API Debugger**: `http://localhost:5001/api-debugger`
- 📖 **Guide**: `http://localhost:5001/guide`

### F&O
- 📊 **FNO Instruments**: `http://localhost:5001/fno`

## UI Features

### Modern Design
- **Framework**: NiceGUI (Python-based reactive UI)
- **Styling**: Tailwind CSS classes
- **Layout**: Responsive sidebar navigation
- **Theme**: Dark/Light mode support
- **Icons**: Material Design Icons

### Interactive Elements
- **Tables**: Sortable, filterable data grids
- **Charts**: Plotly interactive charts
- **Forms**: Validated input forms
- **Buttons**: Action buttons with loading states
- **Cards**: Information cards with stats
- **Modals**: Popup dialogs for confirmations

### Real-time Features
- **Live Updates**: Auto-refreshing data
- **WebSocket**: Real-time market data streaming
- **Notifications**: Toast messages for actions
- **Loading States**: Spinners for async operations

## Screenshot Checklist

To document the UI, capture:

- [ ] Home page with dashboard overview
- [ ] Positions page with sample data
- [ ] Orders & Alerts page with forms
- [ ] Analytics page with charts
- [ ] Backtest page with results
- [ ] Strategy Builder with form
- [ ] API Debugger with endpoint tests
- [ ] Option Chain with data table
- [ ] Live Trading with order placement
- [ ] User Profile with account info

## UI Components Used

### Layout Components
- `ui.page()` - Page container
- `ui.row()` - Horizontal layout
- `ui.column()` - Vertical layout
- `ui.card()` - Content cards
- `ui.expansion()` - Collapsible sections

### Data Display
- `ui.table()` - Data tables
- `ui.chart()` - Plotly charts
- `ui.label()` - Text labels
- `ui.html()` - Custom HTML
- `ui.markdown()` - Markdown rendering

### Input Components
- `ui.input()` - Text input
- `ui.number()` - Number input
- `ui.select()` - Dropdown
- `ui.button()` - Action button
- `ui.switch()` - Toggle switch
- `ui.checkbox()` - Checkbox
- `ui.date()` - Date picker

### Feedback Components
- `ui.notify()` - Toast notifications
- `ui.spinner()` - Loading spinner
- `ui.dialog()` - Modal dialogs
- `ui.tooltip()` - Hover tooltips

## Customization

All pages use shared components from:
- `dashboard_ui/common.py` - Theme & component utilities
- `dashboard_ui/state.py` - Global state management

### Theme Colors
```python
PRIMARY = "#1976d2"  # Blue
SECONDARY = "#424242"  # Gray
SUCCESS = "#4caf50"  # Green
WARNING = "#ff9800"  # Orange
ERROR = "#f44336"  # Red
INFO = "#2196f3"  # Light Blue
```

## Mobile Responsive

All pages are responsive and work on:
- 📱 Mobile (320px+)
- 📱 Tablet (768px+)
- 💻 Desktop (1024px+)
- 🖥️ Large Desktop (1920px+)

---

**Note:** To capture actual screenshots, run the application and use browser screenshot tools (F12 → Cmd+Shift+P → "Screenshot") or browser extensions like "Full Page Screen Capture".

**Last Updated:** February 3, 2026
