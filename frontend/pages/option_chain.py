from nicegui import ui
from ..common import Components
import sys
from pathlib import Path
import asyncio
from datetime import datetime
from ..services.websocket_service import get_websocket_service

# Import Service
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.services.market_data.options_chain import OptionsChainService

service = OptionsChainService()

class OptionChainPage:
    def __init__(self):
        self.ws = get_websocket_service()
        self.selected_symbol = "NIFTY"
        self.selected_expiry = None
        self.expiry_dates = []
        self.available_symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY", "RELIANCE", "HDFCBANK", "INFY", "TCS"] # Default fallback
        
        # UI References
        self.chain_container = None
        self.spot_label = None
        self.timestamp_label = None
        self.status_badge = None
        self.sector_label = None
        self.index_badge = None
        self.nifty100_badge = None
        self.nifty200_badge = None
        self.nifty500_badge = None
        self.next50_badge = None
        self.midcap_badge = None
        self.smallcap_badge = None
        
        # Filter State
        self.filter_options = {"indices": ["ALL"], "sectors": ["ALL"]}
        self.selected_index_filter = "ALL"
        self.selected_sector_filter = "ALL"
        
        # State
        self.current_data = None
        self.is_connected = False

    async def initialize(self):
        """Initialize page data"""
        # Fetch Available Symbols
        try:
            import requests
            # Use internal direct call if possible, or http request
            # Since this is running in the same process group, we can use the service directly if imported, 
            # but to be safe and consistent with architecture, let's use the service instance we already have:
            fno_data = await asyncio.to_thread(service.get_fno_symbols)
            if fno_data:
                # Combine all categories: Indices first, then Equities, Commodities, Currencies, IRD
                self.available_symbols = (
                    fno_data.get("indices", []) + 
                    sorted(fno_data.get("equities", [])) +
                    sorted(fno_data.get("commodities", [])) +
                    sorted(fno_data.get("currencies", [])) +
                    sorted(fno_data.get("ird", []))
                )
                
                # Update dropdown if it exists (it's created before initialize is called)
                if hasattr(self, 'symbol_select') and self.symbol_select:
                    self.symbol_select.options = self.available_symbols
                    self.symbol_select.update()
                
                # Check if current selection is valid
                if self.selected_symbol not in self.available_symbols:
                    self.selected_symbol = self.available_symbols[0]
                    if hasattr(self, 'symbol_select') and self.symbol_select:
                        self.symbol_select.value = self.selected_symbol

            # Update Metadata UI
            await self.update_metadata_ui(self.selected_symbol)
            
            # Fetch Filter Options
            self.filter_options = await asyncio.to_thread(service.get_filter_options)
            if self.filter_options and hasattr(self, 'sector_filter_select'):
                self.sector_filter_select.options = self.filter_options.get("sectors", ["ALL"])
                self.sector_filter_select.update()
                    
        except Exception as e:
            print(f"Error fetching symbols: {e}")

    async def update_metadata_ui(self, symbol: str):
        """Update Sector and Index labels for the selected symbol"""
        try:
            meta = await asyncio.to_thread(service.get_symbol_metadata, symbol)
            if meta and self.sector_label:
                self.sector_label.text = meta.get("sector", "Other")
                
                # Update Index Badge
                if meta.get("is_nifty50"):
                    self.index_badge.text = "NIFTY 50"
                    self.index_badge.set_visibility(True)
                elif meta.get("is_nifty_bank"):
                    self.index_badge.text = "BANK NIFTY"
                    self.index_badge.set_visibility(True)
                else:
                    self.index_badge.set_visibility(False)
                
                # NIFTY 100 Badge
                if meta.get("is_nifty100"):
                    self.nifty100_badge.set_visibility(True)
                else:
                    self.nifty100_badge.set_visibility(False)
                
                # NIFTY 200 Badge
                if meta.get("is_nifty200"):
                    self.nifty200_badge.set_visibility(True)
                else:
                    self.nifty200_badge.set_visibility(False)

                # NIFTY 500 Badge
                if meta.get("is_nifty500"):
                    self.nifty500_badge.set_visibility(True)
                else:
                    self.nifty500_badge.set_visibility(False)
                
                # NEXT 50 Badge
                if meta.get("is_nifty_next50"):
                    self.next50_badge.set_visibility(True)
                else:
                    self.next50_badge.set_visibility(False)

                # MIDCAP Badge (Grouped)
                is_midcap = any([meta.get("is_nifty_midcap50"), meta.get("is_nifty_midcap100"), meta.get("is_nifty_midcap150")])
                self.midcap_badge.set_visibility(is_midcap)

                # SMALLCAP Badge (Grouped)
                is_smallcap = any([meta.get("is_nifty_smallcap50"), meta.get("is_nifty_smallcap100"), meta.get("is_nifty_smallcap250")])
                self.smallcap_badge.set_visibility(is_smallcap)
        except Exception as e:
            print(f"Error updating metadata UI: {e}")

    async def handle_filter_change(self, e):
        """Handle Index or Sector filter change"""
        self.selected_index_filter = self.index_filter_select.value
        self.selected_sector_filter = self.sector_filter_select.value
        
        # Fetch filtered symbols
        filtered_symbols = await asyncio.to_thread(
            service.get_filtered_symbols, 
            self.selected_index_filter, 
            self.selected_sector_filter
        )
        
        if filtered_symbols:
            # Expert Addition: Always have "ALL" as first option in list
            self.available_symbols = ["ALL"] + filtered_symbols
            self.symbol_select.options = self.available_symbols
            # If current selection not in new list, pick first
            if self.selected_symbol not in self.available_symbols:
                self.selected_symbol = "ALL"
                self.symbol_select.value = self.selected_symbol
            self.symbol_select.update()
        else:
            ui.notify("No instruments matching filters", type="warning")


        # Get initial expiries from database (no API call needed)
        self.expiry_dates = await asyncio.to_thread(
            service.get_expiry_dates_from_db, self.selected_symbol
        )
        if self.expiry_dates:
            self.selected_expiry = self.expiry_dates[0]

        # Setup WebSocket callbacks
        self.ws.on_options_update = self.handle_live_update
        
        # Connect if not connected
        if not self.ws.connected:
            await self.ws.connect()
            
        # Initial Subscribe
        await self.ws.subscribe_options(self.selected_symbol, self.selected_expiry)

    async def handle_change_symbol(self, e):
        """Handle symbol change"""
        new_symbol = e.value
        if new_symbol == self.selected_symbol:
            return
            
        # Unsubscribe old
        await self.ws.unsubscribe_options(self.selected_symbol)
        
        self.selected_symbol = new_symbol
        ui.notify(f"Switching to {new_symbol}...", type="info")

        # Update Metadata UI
        await self.update_metadata_ui(new_symbol)
        
        # Fetch new expiries from database (no API call needed)
        self.expiry_dates = await asyncio.to_thread(
            service.get_expiry_dates_from_db, new_symbol
        )
        
        select_widget = e.sender
        expiry_widget = self.expiry_select
        
        expiry_widget.options = self.expiry_dates
        if self.expiry_dates:
            self.selected_expiry = self.expiry_dates[0]
            expiry_widget.value = self.selected_expiry
        else:
            self.selected_expiry = None
            expiry_widget.value = None
            
        # Subscribe new
        await self.ws.subscribe_options(self.selected_symbol, self.selected_expiry)
        
        # Force a refresh of the table view with loading state
        await self.load_initial_data()

    async def load_initial_data(self):
        """Load initial static data before WS kicks in"""
        if self.selected_symbol == "ALL":
             with self.chain_container:
                self.chain_container.clear()
                with ui.column().classes("w-full items-center justify-center py-12"):
                    ui.icon("filter_list", size="xl").classes("text-slate-600 mb-4")
                    ui.label("Select an Instrument").classes("text-slate-500 font-medium")
                    ui.label("Please select a specific stock from the filtered list to view its Option Chain").classes("text-slate-600 text-sm")
             return

        if self.chain_container:
            self.chain_container.clear()
            with self.chain_container:
                ui.spinner("dots", size="lg").classes("mx-auto my-12 text-cyan-400")
        
        # Fetch REST API data first for immediate display
        data = await asyncio.to_thread(
            service.get_option_chain, self.selected_symbol, self.selected_expiry
        )
        self.render_chain_table(data)

    async def handle_live_update(self, data):
        """Handle incoming WebSocket data"""
        # Only process if matching current symbol
        if self.selected_symbol == "ALL":
            return
            
        if data.get("symbol") != self.selected_symbol:
            return
            
        # Update full table vs partial update?
        # For now, simplistic re-render is safest to ensure consistency
        # In a highly optimized version, we'd update individual cells binding to a reactive dict
        self.render_chain_table(data.get("data"))

    def render_chain_table(self, data):
        """Render the full option chain table"""
        if not self.chain_container:
            return
            
        self.chain_container.clear()
        
        # Check for empty data
        is_empty = not data or not data.get("strikes")
        
        # Update Header Status
        if self.status_badge:
            if is_empty:
                self.status_badge.text = "NO DATA"
                self.status_badge.props("color=red text-color=white")
                
                if self.spot_label:
                    self.spot_label.text = "---"
                    self.timestamp_label.text = "Last Upd: --:--"
            else:
                self.status_badge.text = "LIVE"
                self.status_badge.props("color=green text-color=white")
                
                # Update Spot Price
                spot = data.get("underlying_price", 0)
                timestamp = data.get("timestamp_str") or datetime.now().strftime("%H:%M:%S")
                if self.spot_label:
                    self.spot_label.text = f"{spot:,.2f}"
                    self.timestamp_label.text = f"Last Upd: {timestamp}"

        if is_empty:
            with self.chain_container:
                with ui.column().classes("w-full items-center justify-center py-12"):
                    ui.icon("sentiment_dissatisfied", size="xl").classes("text-slate-600 mb-4")
                    ui.label("No Options Data Available").classes("text-slate-500 font-medium")
                    ui.label("Please check your API Token or Market Hours").classes("text-slate-600 text-sm")
            return

        strikes = data["strikes"]
        spot = data.get("underlying_price", 0)

        # --- THE GRID ---
        # Columns: 
        # [CALLS] Delta | IV | OI | Vol | LTP 
        # [CENTER] STRIKE 
        # [PUTS] LTP | Vol | OI | IV | Delta
        
        # Grid Template: 
        # 5 cols (Calls) + 1 col (Strike) + 5 cols (Puts) = 11 columns
        # Widths: 
        # Delta(50) IV(50) OI(60) Vol(60) LTP(70) | Strike(80) | LTP(70) Vol(60) OI(60) IV(50) Delta(50)
        cols = "minmax(50px, 1fr) minmax(50px, 1fr) minmax(60px, 1.2fr) minmax(60px, 1.2fr) minmax(70px, 1.5fr) " \
               "90px " \
               "minmax(70px, 1.5fr) minmax(60px, 1.2fr) minmax(60px, 1.2fr) minmax(50px, 1fr) minmax(50px, 1fr)"

        with self.chain_container:
            # Header Row
            with ui.grid(columns=cols).classes(
                "w-full gap-[1px] text-center font-mono text-[11px] font-bold tracking-wider "
                "bg-slate-900 border-b border-slate-700 sticky top-0 z-20 shadow-lg text-slate-400 uppercase"
            ):
                # Calls Header
                ui.label("Delta").classes("py-3")
                ui.label("IV").classes("py-3")
                ui.label("OI").classes("py-3")
                ui.label("Vol").classes("py-3")
                ui.label("LTP").classes("py-3 text-cyan-400")
                
                # Strike Header
                ui.label("Strike").classes("py-3 text-white bg-slate-800")
                
                # Puts Header
                ui.label("LTP").classes("py-3 text-cyan-400")
                ui.label("Vol").classes("py-3")
                ui.label("OI").classes("py-3")
                ui.label("IV").classes("py-3")
                ui.label("Delta").classes("py-3")

            # Data Rows
            # Use a virtual scroll container if lists get massive, but for 20-30 strikes regular grid is fine
            with ui.grid(columns=cols).classes(
                "w-full gap-[1px] gap-y-[1px] items-stretch text-center font-mono text-xs bg-slate-900"
            ):
                for s in strikes:
                    strike_price = s["strike"]
                    
                    # Determine ITM/OTM
                    # Call ITM: Spot > Strike (Strike < Spot)
                    is_call_itm = strike_price < spot
                    # Put ITM: Spot < Strike (Strike > Spot)
                    is_put_itm = strike_price > spot
                    
                    # ATM Highlight (within 0.2%)
                    is_atm = abs(strike_price - spot) / spot < 0.002
                    
                    # Background Colors
                    # ITM gets subtle tint
                    # ATM gets specific glow
                    
                    call_bg = "bg-green-900/10" if is_call_itm else "bg-slate-900"
                    put_bg = "bg-red-900/10" if is_put_itm else "bg-slate-900"
                    
                    if is_atm:
                        strike_bg = "bg-yellow-500/20 text-yellow-400 border-x-2 border-yellow-500/50"
                        row_hover = "hover:brightness-110"
                    else:
                        strike_bg = "bg-slate-800 text-slate-200"
                        row_hover = "hover:bg-white/5"

                    # Data Extraction
                    c = s.get("call", {})
                    p = s.get("put", {})
                    
                    # Format Helpers
                    def fmt(val, decimals=2, default="-"):
                        if val is None: return default
                        return f"{val:,.{decimals}f}"
                    
                    def fmt_int(val):
                        if not val: return "-"
                        if val > 100000: return f"{val/100000:.2f}L"
                        if val > 1000: return f"{val/1000:.1f}k"
                        return str(val)

                    # --- RENDER CELLS ---
                    
                    # CALLS
                    # Delta
                    ui.label(fmt(c.get("delta"), 2)).classes(f"py-2 flex items-center justify-center {call_bg} text-slate-500 {row_hover}")
                    # IV
                    ui.label(fmt(c.get("iv"), 1)).classes(f"py-2 flex items-center justify-center {call_bg} text-amber-200/70 {row_hover}")
                    # OI
                    ui.label(fmt_int(c.get("oi"))).classes(f"py-2 flex items-center justify-center {call_bg} text-slate-300 {row_hover}")
                    # Vol
                    ui.label(fmt_int(c.get("volume"))).classes(f"py-2 flex items-center justify-center {call_bg} text-slate-400 {row_hover}")
                    # LTP (Green if ITM)
                    ltp_color = "text-green-400 font-bold" if is_call_itm else "text-slate-200"
                    ui.label(fmt(c.get("ltp"))).classes(f"py-2 flex items-center justify-center {call_bg} {ltp_color} {row_hover}")
                    
                    # STRIKE
                    ui.label(f"{int(strike_price)}").classes(
                        f"py-2 flex items-center justify-center font-bold tracking-wide {strike_bg}"
                    )
                    
                    # PUTS
                    # LTP (Red if ITM)
                    ltp_color = "text-red-400 font-bold" if is_put_itm else "text-slate-200"
                    ui.label(fmt(p.get("ltp"))).classes(f"py-2 flex items-center justify-center {put_bg} {ltp_color} {row_hover}")
                    # Vol
                    ui.label(fmt_int(p.get("volume"))).classes(f"py-2 flex items-center justify-center {put_bg} text-slate-400 {row_hover}")
                    # OI
                    ui.label(fmt_int(p.get("oi"))).classes(f"py-2 flex items-center justify-center {put_bg} text-slate-300 {row_hover}")
                    # IV
                    ui.label(fmt(p.get("iv"), 1)).classes(f"py-2 flex items-center justify-center {put_bg} text-amber-200/70 {row_hover}")
                    # Delta
                    ui.label(fmt(p.get("delta"), 2)).classes(f"py-2 flex items-center justify-center {put_bg} text-slate-500 {row_hover}")


    def render(self):
        """Main Render Entry Point"""
        ui.add_head_html("""
            <style>
            .options-grid {
                display: grid;
                grid-template-columns: repeat(11, 1fr);
            }
            </style>
        """)
        
        # Async Init
        ui.timer(0.1, self.initialize, once=True)
        ui.timer(0.2, self.load_initial_data, once=True)

        # Header Section
        with ui.row().classes("w-full justify-between items-center mb-6 pl-1"):
            with ui.column().classes("gap-0"):
                Components.section_header(
                    "Option Chain", "Premium Real-time Analytics", "hub"
                )
            
            # Spot Price Display
            with ui.row().classes("items-center gap-4 bg-slate-900/50 px-6 py-2 rounded-lg border border-slate-800"):
                with ui.column().classes("items-end gap-0"):
                    ui.label("SPOT PRICE").classes("text-[10px] tracking-widest text-slate-500 font-bold")
                    self.spot_label = ui.label("Loading...").classes("text-2xl font-mono font-bold text-white")
                
                ui.separator().props("vertical").classes("h-8 mx-2 bg-slate-700")
                
                with ui.column().classes("items-start gap-0"):
                    self.timestamp_label = ui.label("Last Upd: --:--:--").classes("text-[10px] text-slate-500")
                    with ui.row().classes("items-center gap-2"):
                        self.status_badge = ui.badge("LIVE", color="green").props("rounded").classes("text-[10px] px-2")


        # Control Bar
        with ui.row().classes(
            "w-full gap-4 items-center bg-[#0F1419] p-3 rounded-xl border border-slate-800 mb-2 shadow-sm"
        ):
            # Symbol Selector
            self.symbol_select = ui.select(
                self.available_symbols,
                label="Instrument",
                value=self.selected_symbol,
                on_change=self.handle_change_symbol,
            ).props(
                "outlined dense dark options-dense bg-slate-900 color=cyan behavior=menu" # behavior=menu for better scrolling
            ).classes("w-48 font-bold")

            # NEW: Sector & Index "Columns" (Metadata Badges)
            with ui.row().classes("items-center gap-3 px-4 border-l border-slate-800"):
                with ui.column().classes("gap-0"):
                    ui.label("SECTOR").classes("text-[10px] tracking-widest text-slate-500 font-bold")
                    self.sector_label = ui.label("---").classes("text-sm font-bold text-slate-200")
                
                with ui.column().classes("gap-0"):
                    ui.label("INDEX").classes("text-[10px] tracking-widest text-slate-500 font-bold")
                    with ui.row().classes("gap-1 items-center"):
                        self.index_badge = ui.badge("NIFTY 50", color="indigo").props("rounded").classes("text-[10px] font-bold px-2")
                        self.index_badge.set_visibility(False)
                        self.nifty100_badge = ui.badge("NIFTY 100", color="blue-700").props("rounded").classes("text-[10px] font-bold px-2")
                        self.nifty100_badge.set_visibility(False)
                        self.nifty200_badge = ui.badge("NIFTY 200", color="blue-800").props("rounded").classes("text-[10px] font-bold px-2")
                        self.nifty200_badge.set_visibility(False)
                        self.nifty500_badge = ui.badge("NIFTY 500", color="slate-700").props("rounded").classes("text-[10px] font-bold px-2")
                        self.nifty500_badge.set_visibility(False)
                        self.next50_badge = ui.badge("NEXT 50", color="teal-700").props("rounded").classes("text-[10px] font-bold px-2")
                        self.next50_badge.set_visibility(False)
                        self.midcap_badge = ui.badge("MIDCAP", color="orange-800").props("rounded").classes("text-[10px] font-bold px-2")
                        self.midcap_badge.set_visibility(False)
                        self.smallcap_badge = ui.badge("SMALLCAP", color="brown-700").props("rounded").classes("text-[10px] font-bold px-2")
                        self.smallcap_badge.set_visibility(False)

            # --- NEW: Filter Bar Row ---
            ui.separator().classes("bg-slate-800 my-1")
            with ui.row().classes("w-full gap-4 items-center px-1"):
                ui.label("FILTERS:").classes("text-[10px] font-bold text-slate-500 tracking-tighter")
                
                self.index_filter_select = ui.select(
                    [
                        "ALL", "NIFTY 50", "NIFTY 100", "NIFTY 200", "NIFTY 500", 
                        "NIFTY NEXT 50", "NIFTY MIDCAP 100", "NIFTY SMALLCAP 100",
                        "BANK NIFTY"
                    ],
                    value="ALL",
                    on_change=self.handle_filter_change,
                    label="Index Group"
                ).props("outlined dense dark color=indigo").classes("w-48 scale-90 origin-left")
                
                # We'll populate sectors in initialize
                self.sector_filter_select = ui.select(
                    ["ALL"],
                    value="ALL",
                    on_change=self.handle_filter_change,
                    label="Sector"
                ).props("outlined dense dark color=primary").classes("w-56 scale-90 origin-left")

            # Expiry Selector
            self.expiry_select = ui.select(
                self.expiry_dates,
                label="Expiry",
                value=self.selected_expiry,
                on_change=lambda e: self.load_initial_data() # Reload data on expiry change
            ).props(
                "outlined dense dark options-dense bg-slate-900"
            ).classes("w-40")

            ui.separator().props("vertical").classes("h-8 mx-2 bg-slate-800")

            # Quick Filters (Visual only for now)
            with ui.row().classes("gap-2"):
                ui.chip("Near ATM", icon="center_focus_strong").props("dense outline square color=grey-7")
                ui.chip("High Vol", icon="bolt").props("dense outline square color=grey-7")

            ui.space()

            # Refresh Button
            ui.button(on_click=self.load_initial_data, icon="refresh").props(
                "flat round dense color=grey-5"
            ).tooltip("Force Refresh")

        # Main Table Container
        # Full height scrollable area
        self.chain_container = ui.column().classes(
            "w-full h-[calc(100vh-280px)] overflow-auto rounded-lg border border-slate-800 bg-[#0F1419] relative scrollbar-thin"
        )
        
        # Initial Spinner
        with self.chain_container:
            ui.spinner("dots", size="lg").classes("absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-cyan-500")


def render_page(state):
    """Render the Option Chain Page"""
    page = OptionChainPage()
    page.render()
