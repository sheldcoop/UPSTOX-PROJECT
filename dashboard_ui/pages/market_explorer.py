"""
Market Explorer Page - Comprehensive Indian Indices Dashboard
Displays Broad Market, Sectoral, Thematic, Strategy, and Multi-Asset Indices
"""

from nicegui import ui, run
from ..common import Components
from datetime import datetime
import asyncio
import random
from typing import Dict, List, Any


# ============================================================================
# 📊 INDEX DEFINITIONS
# ============================================================================

BROAD_MARKET_INDICES = [
    "Nifty 50 Index",
    "Nifty Next 50 Index",
    "Nifty 100 Index",
    "Nifty 200 Index",
    "Nifty Total Market Index",
    "Nifty 500 Index",
    "Nifty 500 Multicap 50:25:25 Index",
    "Nifty500 LargeMidSmall Equal-Cap Weighted",
    "Nifty Midcap150 Index",
    "Nifty Midcap 50 Index",
    "Nifty Midcap Select Index",
    "Nifty Midcap 100 Index",
    "Nifty Smallcap 500",
    "Nifty Smallcap 250 Index",
    "Nifty Smallcap 50 Index",
    "Nifty Smallcap 100 Index",
    "Nifty Microcap 250 Index",
    "Nifty LargeMidcap 250 Index",
    "Nifty MidSmallcap 400 Index",
]

SECTORAL_INDICES = [
    "Nifty Auto Index",
    "Nifty Bank Index",
    "Nifty Chemicals",
    "Nifty Financial Services Index",
    "Nifty Financial Services 25/50 Index",
    "Nifty Financial Services Ex-Bank index",
    "Nifty FMCG Index",
    "Nifty Healthcare Index",
    "Nifty IT Index",
    "Nifty Media Index",
    "Nifty Metal Index",
    "Nifty Pharma Index",
    "Nifty Private Bank Index",
    "Nifty PSU Bank Index",
    "Nifty Realty Index",
    "Nifty Consumer Durables Index",
    "Nifty Oil and Gas Index",
    "Nifty500 Healthcare",
    "Nifty MidSmall Financial Services Index",
    "Nifty MidSmall Healthcare Index",
    "Nifty MidSmall IT & Telecom Index",
]

THEMATIC_INDICES = [
    "Nifty Capital Markets",
    "Nifty Commodities Index",
    "Nifty Conglomerate 50",
    "Nifty Core Housing Index",
    "Nifty CPSE Index",
    "Nifty EV & New Age Automotive Index",
    "Nifty Energy Index",
    "Nifty Housing Index",
    "Nifty India Consumption Index",
    "Nifty India Defence",
    "Nifty India Digital",
    "Nifty India Infrastructure & Logistics",
    "Nifty India Internet",
    "Nifty India Manufacturing Index",
    "Nifty India New Age Consumption",
    "Nifty India Railways PSU",
    "Nifty India Tourism",
    "Nifty Infrastructure Index",
    "Nifty MNC Index",
    "Nifty Mobility Index",
    "Nifty Non-Cyclical Consumer Index",
    "Nifty PSE Index",
    "Nifty Rural Index",
    "Nifty Services Sector Index",
    "Nifty Shariah 25 Index",
    "Nifty SME EMERGE Index",
    "Nifty Tata Group Index",
    "Nifty Tata Group 25% Cap Index",
    "Nifty100 Enhanced ESG Index",
    "Nifty100 ESG Index",
    "Nifty100 ESG Sector Leaders Index",
    "Nifty100 Quality 30 Index",
    "Nifty200 Quality 30 Index",
    "Nifty Alpha 50 Index",
    "Nifty Alpha Low-Volatility 30 Index",
    "Nifty Growth Sectors 15 Index",
    "Nifty High Beta 50 Index",
    "Nifty Low Volatility 50 Index",
    "Nifty Dividend Opportunities 50 Index",
    "Nifty100 Low Volatility 30 Index",
    "Nifty200 Momentum 30 Index",
    "Nifty Midcap150 Momentum 50 Index",
    "Nifty500 Momentum 50 Index",
]

STRATEGY_INDICES = [
    "Nifty200 Alpha 30 Index",
    "Nifty Midcap150 Quality 50 Index",
    "Nifty500 Value 50 Index",
    "Nifty500 Equal Weight Index",
    "Nifty100 Alpha 30 Index",
    "Nifty Alpha Quality Low-Volatility 30 Index",
    "Nifty Alpha Quality Value Low-Volatility 30 Index",
    "Nifty100 Equal Weight Index",
    "Nifty50 Equal Weight Index",
    "Nifty Top 10 Equal Weight Index",
]

HYBRID_MULTI_ASSET_INDICES = [
    "NIFTY Hybrid Composite Debt 15:85 Index",
    "NIFTY Hybrid Composite Debt 25:75 Index",
    "NIFTY Hybrid Composite Debt 50:50 Index",
    "NIFTY Hybrid Composite Debt 65:35 Index",
    "NIFTY Hybrid Composite Debt 75:25 Index",
    "NIFTY Hybrid Composite Debt 85:15 Index",
    "NIFTY Multi-Asset Composite Index",
]

FIXED_INCOME_INDICES = [
    "NIFTY 1D Rate Index",
    "NIFTY 4-8 yr G-Sec Index",
    "NIFTY 8-13 yr G-Sec Index",
    "NIFTY 10 yr Benchmark G-Sec Index",
    "NIFTY 11-15 yr G-Sec Index",
    "NIFTY 15 yr and above G-Sec Index",
    "NIFTY Composite G-sec Index",
]


# ============================================================================
# 🎲 MOCK DATA GENERATOR
# ============================================================================

def generate_mock_index_data(index_name: str) -> Dict[str, Any]:
    """Generate realistic mock data for an index"""
    # Base values for different index categories
    base_value = 20000 if "50" in index_name else 15000
    if "Midcap" in index_name:
        base_value = 40000
    elif "Smallcap" in index_name:
        base_value = 12000
    elif "Bank" in index_name:
        base_value = 45000
    elif "IT" in index_name:
        base_value = 30000
    
    # Generate realistic fluctuation
    current_value = base_value * (1 + random.uniform(-0.05, 0.05))
    change_pct = random.uniform(-3.5, 3.5)
    prev_close = current_value / (1 + change_pct / 100)
    change_value = current_value - prev_close
    
    # Number of constituents
    constituents_map = {
        "50": 50, "100": 100, "200": 200, "500": 500,
        "Next 50": 50, "250": 250, "400": 400,
    }
    constituents = 50  # default
    for key, val in constituents_map.items():
        if key in index_name:
            constituents = val
            break
    
    return {
        "name": index_name,
        "value": current_value,
        "change": change_value,
        "change_pct": change_pct,
        "prev_close": prev_close,
        "constituents": constituents,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }


# ============================================================================
# 📊 UI RENDERING
# ============================================================================

def render_page(state):
    """Main page render function"""
    Components.section_header(
        "Market Explorer",
        "Real-time Indian Market Indices Dashboard",
        "trending_up",
    )
    
    # Global controls
    with ui.row().classes("w-full gap-4 mb-4"):
        search_input = ui.input(
            label="Search Indices",
            placeholder="Type to search...",
        ).props("outlined dense dark clearable").classes("flex-1")
        
        refresh_btn = ui.button(
            "Refresh All",
            icon="refresh",
            on_click=lambda: refresh_all_data(),
        ).props("outline").classes("px-6")
        
        last_updated = ui.label("Last updated: --:--:--").classes(
            "text-sm text-slate-400 self-center"
        )
    
    # Tab navigation
    with ui.tabs().classes("w-full") as tabs:
        broad_tab = ui.tab("Broad Market", icon="insights")
        sectoral_tab = ui.tab("Sectoral", icon="business")
        thematic_tab = ui.tab("Thematic", icon="category")
        strategy_tab = ui.tab("Strategy", icon="psychology")
        hybrid_tab = ui.tab("Hybrid & Multi-Asset", icon="diversity_3")
        fixed_tab = ui.tab("Fixed Income", icon="account_balance")
    
    # Tab panels
    with ui.tab_panels(tabs, value=broad_tab).classes("w-full mt-4"):
        with ui.tab_panel(broad_tab):
            broad_container = ui.column().classes("w-full gap-4")
            render_indices_table(BROAD_MARKET_INDICES, broad_container, search_input)
        
        with ui.tab_panel(sectoral_tab):
            sectoral_container = ui.column().classes("w-full gap-4")
            render_indices_table(SECTORAL_INDICES, sectoral_container, search_input)
        
        with ui.tab_panel(thematic_tab):
            thematic_container = ui.column().classes("w-full gap-4")
            render_indices_table(THEMATIC_INDICES, thematic_container, search_input)
        
        with ui.tab_panel(strategy_tab):
            strategy_container = ui.column().classes("w-full gap-4")
            render_indices_table(STRATEGY_INDICES, strategy_container, search_input)
        
        with ui.tab_panel(hybrid_tab):
            hybrid_container = ui.column().classes("w-full gap-4")
            render_indices_table(HYBRID_MULTI_ASSET_INDICES, hybrid_container, search_input)
        
        with ui.tab_panel(fixed_tab):
            fixed_container = ui.column().classes("w-full gap-4")
            render_indices_table(FIXED_INCOME_INDICES, fixed_container, search_input)
    
    # Auto-refresh timer
    async def auto_refresh():
        while True:
            await asyncio.sleep(30)  # 30 seconds
            refresh_all_data()
            last_updated.text = f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
    
    def refresh_all_data():
        """Refresh all visible index data"""
        ui.notify("Refreshing market data...", type="info", position="top")
        last_updated.text = f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
    
    # Start auto-refresh
    ui.timer(30.0, lambda: refresh_all_data())


def render_indices_table(indices: List[str], container: ui.column, search_input: ui.input):
    """Render a table of indices with search filtering"""
    
    # Generate mock data
    indices_data = [generate_mock_index_data(idx) for idx in indices]
    
    # Table columns configuration
    columns = [
        {
            "name": "name",
            "label": "Index Name",
            "field": "name",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "value",
            "label": "Current Value",
            "field": "value",
            "align": "right",
            "sortable": True,
            "format": lambda val: f"₹{val:,.2f}",
        },
        {
            "name": "change",
            "label": "Change",
            "field": "change",
            "align": "right",
            "sortable": True,
            "format": lambda val: f"₹{val:,.2f}",
        },
        {
            "name": "change_pct",
            "label": "Change %",
            "field": "change_pct",
            "align": "right",
            "sortable": True,
            "format": lambda val: f"{val:+.2f}%",
        },
        {
            "name": "prev_close",
            "label": "Prev Close",
            "field": "prev_close",
            "align": "right",
            "sortable": True,
            "format": lambda val: f"₹{val:,.2f}",
        },
        {
            "name": "constituents",
            "label": "Constituents",
            "field": "constituents",
            "align": "center",
            "sortable": True,
        },
        {
            "name": "timestamp",
            "label": "Updated",
            "field": "timestamp",
            "align": "center",
            "sortable": False,
        },
    ]
    
    with container:
        with Components.card():
            # Summary stats
            total_indices = len(indices_data)
            gainers = sum(1 for idx in indices_data if idx["change_pct"] > 0)
            losers = sum(1 for idx in indices_data if idx["change_pct"] < 0)
            
            with ui.row().classes("w-full gap-4 mb-4"):
                with ui.column().classes("flex-1 bg-slate-800/30 p-3 rounded-lg"):
                    ui.label("Total Indices").classes("text-xs text-slate-400 uppercase")
                    ui.label(str(total_indices)).classes("text-2xl font-bold text-white")
                
                with ui.column().classes("flex-1 bg-green-500/10 p-3 rounded-lg"):
                    ui.label("Gainers").classes("text-xs text-slate-400 uppercase")
                    ui.label(str(gainers)).classes("text-2xl font-bold text-green-400")
                
                with ui.column().classes("flex-1 bg-red-500/10 p-3 rounded-lg"):
                    ui.label("Losers").classes("text-xs text-slate-400 uppercase")
                    ui.label(str(losers)).classes("text-2xl font-bold text-red-400")
                
                with ui.column().classes("flex-1 bg-slate-800/30 p-3 rounded-lg"):
                    ui.label("Unchanged").classes("text-xs text-slate-400 uppercase")
                    ui.label(str(total_indices - gainers - losers)).classes(
                        "text-2xl font-bold text-slate-400"
                    )
            
            # Data table with custom styling
            table = ui.table(
                columns=columns,
                rows=indices_data,
                row_key="name",
                pagination={"rowsPerPage": 15, "sortBy": "change_pct", "descending": True},
            ).classes("w-full")
            
            # Custom cell coloring for positive/negative changes
            table.add_slot(
                "body-cell-change_pct",
                r'''
                <q-td :props="props" :class="props.value > 0 ? 'text-green-400' : 'text-red-400'">
                    <div class="flex items-center gap-1">
                        <q-icon :name="props.value > 0 ? 'trending_up' : 'trending_down'" size="sm"/>
                        <span class="font-bold">{{ props.value > 0 ? '+' : '' }}{{ props.value.toFixed(2) }}%</span>
                    </div>
                </q-td>
                ''',
            )
            
            table.add_slot(
                "body-cell-change",
                r'''
                <q-td :props="props" :class="props.value > 0 ? 'text-green-400' : 'text-red-400'">
                    <span class="font-semibold">{{ props.value > 0 ? '+' : '' }}₹{{ props.value.toFixed(2) }}</span>
                </q-td>
                ''',
            )
            
            # Search filtering
            def filter_table():
                query = search_input.value.lower() if search_input.value else ""
                if query:
                    filtered = [idx for idx in indices_data if query in idx["name"].lower()]
                    table.rows = filtered
                else:
                    table.rows = indices_data
                table.update()
            
            search_input.on("input", lambda: filter_table())
            
            # Info footer
            with ui.row().classes("w-full justify-between items-center mt-4 pt-4 border-t border-slate-800"):
                ui.label(f"Showing {len(indices_data)} indices").classes(
                    "text-xs text-slate-500"
                )
                ui.label("Data refreshes every 30 seconds").classes(
                    "text-xs text-slate-500 italic"
                )


# ============================================================================
# 🔧 UTILITY FUNCTIONS
# ============================================================================

async def fetch_live_index_data(index_name: str) -> Dict[str, Any]:
    """
    Fetch live index data from backend API
    TODO: Implement actual API integration with backend
    For now, returns mock data
    """
    await asyncio.sleep(0.1)  # Simulate API call
    return generate_mock_index_data(index_name)


async def fetch_index_constituents(index_name: str) -> List[Dict[str, Any]]:
    """
    Fetch constituents of a specific index
    TODO: Implement actual API integration
    """
    await asyncio.sleep(0.1)
    # Mock constituents data
    mock_constituents = [
        {"symbol": "RELIANCE", "weight": 10.5, "price": 2450.75, "change_pct": 1.2},
        {"symbol": "TCS", "weight": 9.8, "price": 3680.50, "change_pct": -0.5},
        {"symbol": "HDFCBANK", "weight": 9.2, "price": 1620.30, "change_pct": 0.8},
    ]
    return mock_constituents[:random.randint(3, 10)]
