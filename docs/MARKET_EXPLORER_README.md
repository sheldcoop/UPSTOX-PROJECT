# Market Explorer Page Documentation

## Overview
The **Market Explorer** is a comprehensive indices dashboard for the UPSTOX trading platform that displays real-time data for 100+ Indian market indices across 6 major categories.

## Location
**File:** `/dashboard_ui/pages/market_explorer.py`

## Features

### 1. **Six Major Categories**
   - **Broad Market Indices** (19 indices)
     - Nifty 50, Nifty Next 50, Nifty 100, Nifty 200
     - Nifty Total Market, Nifty 500, Nifty Midcap, Smallcap variants
     - Microcap, LargeMidcap, MidSmallcap indices
   
   - **Sectoral Indices** (21 indices)
     - Auto, Bank, Chemicals, Financial Services
     - FMCG, Healthcare, IT, Media, Metal, Pharma
     - Private Bank, PSU Bank, Realty, Consumer Durables
     - Oil and Gas, and specialized sector indices
   
   - **Thematic Indices** (40+ indices)
     - Capital Markets, Commodities, Conglomerate
     - Defence, Digital, Infrastructure, Manufacturing
     - Tourism, ESG, Quality, Alpha, Momentum
     - Low Volatility, Dividend, Growth Sectors
   
   - **Strategy Indices** (10 indices)
     - Alpha, Quality, Value, Equal Weight strategies
     - Multi-factor combinations
   
   - **Hybrid & Multi-Asset Indices** (7 indices)
     - Hybrid Composite Debt variants (15:85 to 85:15)
     - Multi-Asset Composite
   
   - **Fixed Income Indices** (7 indices)
     - G-Sec indices across various maturity ranges
     - 1D Rate, 4-8yr, 8-13yr, 10yr Benchmark, 11-15yr, 15yr+

### 2. **Interactive UI Components**

#### Global Search
- Real-time search filter across all indices
- Works across all tabs simultaneously
- Case-insensitive search

#### Tab Navigation
- Six dedicated tabs for each category
- Clean, organized layout
- Material Design icons

#### Auto-Refresh
- Automatic data refresh every 30 seconds
- Manual refresh button available
- Last update timestamp display

#### Data Table Features
- **Columns:**
  - Index Name (sortable)
  - Current Value (formatted as ₹)
  - Change (absolute value in ₹)
  - Change % (with trend icons)
  - Previous Close
  - Number of Constituents
  - Last Updated timestamp

- **Visual Indicators:**
  - Green text + up arrow for positive changes
  - Red text + down arrow for negative changes
  - Bold formatting for emphasis

- **Sorting:**
  - Default sort by Change % (descending)
  - All columns sortable
  - 15 rows per page pagination

#### Summary Statistics
Each tab displays:
- **Total Indices** - Total count in category
- **Gainers** - Indices with positive change (green)
- **Losers** - Indices with negative change (red)
- **Unchanged** - Indices with zero change

### 3. **Mock Data Generation**
Currently uses realistic mock data with:
- Base values appropriate for each index type
- Random fluctuations within ±5% range
- Change percentages within ±3.5%
- Accurate constituent counts
- Realistic timestamp generation

### 4. **Design Patterns**
Follows established UPSTOX dashboard patterns:
- Uses `Components.section_header()` for page title
- Uses `Components.card()` for content containers
- Matches dark theme (slate color scheme)
- Consistent with other pages (orders_alerts, analytics, etc.)
- Responsive design

## Usage

### Navigation
Access via sidebar menu:
**Tools → Market Explorer**

### Search
1. Type in the global search box
2. Results filter across all tabs in real-time
3. Clear search to show all indices

### View Details
- Click column headers to sort
- Use pagination to navigate large lists
- Monitor gainers/losers summary cards

### Auto-Refresh
- Data refreshes automatically every 30 seconds
- Manual refresh available via "Refresh All" button
- Last update time shown at top

## Code Structure

### Main Components

```python
def render_page(state):
    """Main entry point - renders header, tabs, and content"""

def render_indices_table(indices, container, search_input):
    """Renders data table for a specific category"""

def generate_mock_index_data(index_name):
    """Generates realistic mock data for testing"""
```

### Data Constants
- `BROAD_MARKET_INDICES` - 19 broad market indices
- `SECTORAL_INDICES` - 21 sector-specific indices
- `THEMATIC_INDICES` - 40+ thematic indices
- `STRATEGY_INDICES` - 10 strategy-based indices
- `HYBRID_MULTI_ASSET_INDICES` - 7 hybrid/multi-asset indices
- `FIXED_INCOME_INDICES` - 7 fixed income indices

### Future Integration Points

```python
async def fetch_live_index_data(index_name):
    """
    TODO: Connect to backend API
    Endpoint: /api/indices/{index_name}
    """

async def fetch_index_constituents(index_name):
    """
    TODO: Fetch constituent stocks
    Endpoint: /api/indices/{index_name}/constituents
    """
```

## Integration with Backend

### Recommended API Endpoints
```
GET /api/indices - List all available indices
GET /api/indices/{index_name} - Get specific index data
GET /api/indices/{index_name}/constituents - Get index constituents
GET /api/indices/category/{category} - Get indices by category
```

### Expected API Response Format
```json
{
  "name": "Nifty 50 Index",
  "value": 21456.75,
  "change": 145.30,
  "change_pct": 0.68,
  "prev_close": 21311.45,
  "constituents": 50,
  "timestamp": "2024-02-03T15:30:00Z"
}
```

## Customization

### Add New Index Category
1. Create new constant list (e.g., `COMMODITY_INDICES`)
2. Add new tab in `render_page()`
3. Add corresponding tab panel with `render_indices_table()`

### Modify Auto-Refresh Interval
```python
ui.timer(30.0, lambda: refresh_all_data())  # Change 30.0 to desired seconds
```

### Customize Table Appearance
Modify the Quasar table slots in `render_indices_table()`:
- `body-cell-change_pct` - Change percentage styling
- `body-cell-change` - Change value styling

## Dependencies
- **nicegui** - UI framework
- **asyncio** - Async operations
- **random** - Mock data generation (remove in production)
- **datetime** - Timestamp handling

## Performance Considerations
- Mock data generation is instant
- Table pagination (15 rows/page) for performance
- Search filtering is client-side (fast)
- Auto-refresh on 30-second timer
- No backend calls in current mock version

## Browser Compatibility
Works in all modern browsers supporting:
- ES6+ JavaScript
- CSS Grid & Flexbox
- WebSockets (for NiceGUI)

## Mobile Responsiveness
- Sidebar collapses on mobile
- Tables scroll horizontally on small screens
- Touch-friendly buttons and controls
- Responsive card layouts

## Testing Checklist
- [x] Page loads without errors
- [x] All 6 tabs display correctly
- [x] Search filters work across tabs
- [x] Sorting works on all columns
- [x] Pagination works correctly
- [x] Auto-refresh timer functions
- [x] Manual refresh button works
- [x] Positive/negative changes display correctly
- [x] Summary statistics calculate correctly
- [ ] Backend API integration (pending)
- [ ] Real-time data updates (pending)

## Future Enhancements
1. **Live Data Integration**
   - Connect to Upstox API or NSE data feed
   - Real-time WebSocket updates
   - Historical chart overlays

2. **Advanced Features**
   - Click index to view constituents modal
   - Export data to CSV/Excel
   - Watchlist/favorites functionality
   - Price alerts for indices
   - Comparison mode (compare multiple indices)

3. **Visualizations**
   - Heatmap view of all indices
   - Sector performance charts
   - Index correlation matrix
   - Historical performance graphs

4. **Filters & Controls**
   - Filter by gainers/losers
   - Filter by change % threshold
   - Sort by multiple columns
   - Custom column visibility

## Maintenance Notes
- Mock data uses `random` module - replace with real API calls
- Update index lists when NSE introduces new indices
- Monitor API rate limits when implementing live data
- Consider caching strategies for frequently accessed data
- Implement error boundaries for failed API calls

## Support
For issues or questions:
- Check main dashboard logs (System Logs button)
- Review browser console for JavaScript errors
- Verify NiceGUI server is running
- Test with mock data first before connecting to live APIs

---

**Last Updated:** 2024-02-03  
**Version:** 1.0.0  
**Status:** Production Ready (Mock Data)
