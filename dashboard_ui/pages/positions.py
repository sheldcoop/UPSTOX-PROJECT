from nicegui import ui
from ..common import Components
from ..state import async_get


def render_page(state):
    """Enhanced Positions Page with detailed views"""
    Components.section_header("Live Positions", "Manage and monitor your open trades", "pie_chart")
    
    # Container for positions data
    positions_container = ui.column().classes("w-full gap-4")
    selected_position = {"symbol": None}
    
    async def load_positions_data():
        """Load positions data from API"""
        positions_data = await async_get("/api/positions")
        
        positions_container.clear()
        with positions_container:
            if "error" in positions_data:
                # Error loading positions
                with Components.card():
                    with ui.row().classes("items-center gap-4"):
                        ui.icon("error", size="3xl").classes("text-red-500")
                        with ui.column():
                            ui.label("Failed to Load Positions").classes("text-xl font-bold text-red-400")
                            ui.label(f"Error: {positions_data['error']}").classes("text-slate-400")
            elif isinstance(positions_data, list) and len(positions_data) == 0:
                # No positions
                with Components.card().classes("items-center justify-center py-12"):
                    ui.icon("inbox", size="4xl").classes("text-slate-700 mb-4")
                    ui.label("No Active Positions").classes("text-2xl font-bold text-slate-400 mb-2")
                    ui.label("Your open positions will appear here").classes("text-slate-500")
            elif isinstance(positions_data, list):
                # Positions Summary Stats
                total_positions = len(positions_data)
                total_pnl = sum(p.get("pnl", 0) for p in positions_data)
                winning_positions = sum(1 for p in positions_data if p.get("pnl", 0) > 0)
                
                # Summary Cards
                with ui.row().classes("w-full gap-4 flex-wrap mb-4"):
                    Components.kpi_card(
                        "Total Positions", 
                        total_positions,
                        suffix=" open"
                    )
                    Components.kpi_card(
                        "Total P&L", 
                        total_pnl,
                        prefix="₹",
                        delta=1.2 if total_pnl > 0 else -1.2
                    )
                    Components.kpi_card(
                        "Winning Positions", 
                        winning_positions,
                        suffix=f" / {total_positions}"
                    )
                    
                    win_rate = (winning_positions / total_positions * 100) if total_positions > 0 else 0
                    Components.kpi_card(
                        "Win Rate", 
                        win_rate,
                        suffix="%"
                    )
                
                # Positions Table
                with Components.card():
                    with ui.row().classes("w-full items-center justify-between mb-4"):
                        ui.label("Open Positions").classes("text-lg font-bold text-white")
                        ui.button(icon="refresh", on_click=load_positions_data).props("flat round").classes(
                            "text-slate-400 hover:text-white"
                        )
                    
                    # Table
                    with ui.element("table").classes("w-full text-sm"):
                        # Header
                        with ui.element("thead").classes("text-slate-400 border-b border-slate-700"):
                            with ui.element("tr"):
                                with ui.element("th").classes("pb-3 text-left pl-2"):
                                    ui.label("Symbol")
                                with ui.element("th").classes("pb-3 text-right"):
                                    ui.label("Side")
                                with ui.element("th").classes("pb-3 text-right"):
                                    ui.label("Quantity")
                                with ui.element("th").classes("pb-3 text-right"):
                                    ui.label("Entry Price")
                                with ui.element("th").classes("pb-3 text-right"):
                                    ui.label("Current Price")
                                with ui.element("th").classes("pb-3 text-right"):
                                    ui.label("P&L")
                                with ui.element("th").classes("pb-3 text-right pr-2"):
                                    ui.label("P&L %")
                        
                        # Body
                        with ui.element("tbody"):
                            for position in positions_data:
                                pnl = position.get("pnl", 0)
                                pnl_percent = position.get("pnl_percent", 0)
                                pnl_color = "text-green-400" if pnl >= 0 else "text-red-400"
                                
                                with ui.element("tr").classes(
                                    "border-b border-slate-800 hover:bg-slate-800/50 cursor-pointer transition-colors"
                                ) as row:
                                    # Click handler for row
                                    def make_click_handler(sym):
                                        async def handler():
                                            selected_position["symbol"] = sym
                                            await show_position_details(sym)
                                        return handler
                                    
                                    row.on("click", make_click_handler(position["symbol"]))
                                    
                                    with ui.element("td").classes("py-3 pl-2"):
                                        ui.label(position.get("symbol", "")).classes("font-bold text-white")
                                    with ui.element("td").classes("py-3 text-right"):
                                        side = position.get("side", "").upper()
                                        side_color = "text-green-400" if side == "LONG" else "text-red-400"
                                        ui.label(side).classes(f"font-medium {side_color}")
                                    with ui.element("td").classes("py-3 text-right"):
                                        ui.label(str(position.get("quantity", 0))).classes("text-slate-300")
                                    with ui.element("td").classes("py-3 text-right"):
                                        ui.label(f"₹{position.get('entry_price', 0):.2f}").classes("text-slate-300")
                                    with ui.element("td").classes("py-3 text-right"):
                                        ui.label(f"₹{position.get('current_price', 0):.2f}").classes("text-slate-300")
                                    with ui.element("td").classes("py-3 text-right"):
                                        ui.label(f"₹{pnl:.2f}").classes(f"font-bold {pnl_color}")
                                    with ui.element("td").classes("py-3 text-right pr-2"):
                                        icon = "trending_up" if pnl_percent >= 0 else "trending_down"
                                        with ui.row().classes(f"items-center gap-1 justify-end {pnl_color}"):
                                            ui.icon(icon, size="xs")
                                            ui.label(f"{abs(pnl_percent):.2f}%").classes("font-bold")
    
    async def show_position_details(symbol):
        """Show detailed view of a specific position"""
        position_data = await async_get(f"/api/positions/{symbol}")
        
        # Create dialog for position details
        with ui.dialog() as details_dialog, ui.card().classes(
            "w-full max-w-2xl bg-slate-900 border border-slate-700"
        ):
            if "error" in position_data:
                ui.label(f"Error: {position_data['error']}").classes("text-red-400")
            else:
                # Header
                with ui.row().classes("w-full items-center justify-between border-b border-slate-700 pb-4"):
                    with ui.row().classes("items-center gap-3"):
                        ui.icon("trending_up", size="lg").classes("text-indigo-500")
                        with ui.column().classes("gap-1"):
                            ui.label(position_data.get("symbol", "")).classes("text-2xl font-bold text-white")
                            side = position_data.get("side", "").upper()
                            side_color = "text-green-400" if side == "LONG" else "text-red-400"
                            ui.label(f"{side} Position").classes(f"text-sm {side_color}")
                    
                    ui.button(icon="close", on_click=details_dialog.close).props("flat round")
                
                # Details Grid
                with ui.grid(columns=2).classes("w-full gap-4 mt-4"):
                    # Quantity
                    with ui.column().classes("gap-1"):
                        ui.label("Quantity").classes("text-xs text-slate-400 uppercase")
                        ui.label(str(position_data.get("quantity", 0))).classes("text-xl font-bold text-white")
                    
                    # Entry Date
                    with ui.column().classes("gap-1"):
                        ui.label("Entry Date").classes("text-xs text-slate-400 uppercase")
                        ui.label(position_data.get("entry_date", "")).classes("text-lg text-white")
                    
                    # Entry Price
                    with ui.column().classes("gap-1"):
                        ui.label("Entry Price").classes("text-xs text-slate-400 uppercase")
                        ui.label(f"₹{position_data.get('entry_price', 0):.2f}").classes("text-xl font-bold text-white")
                    
                    # Current Price
                    with ui.column().classes("gap-1"):
                        ui.label("Current Price").classes("text-xs text-slate-400 uppercase")
                        ui.label(f"₹{position_data.get('current_price', 0):.2f}").classes("text-xl font-bold text-white")
                    
                    # P&L
                    pnl = position_data.get("pnl", 0)
                    pnl_color = "text-green-400" if pnl >= 0 else "text-red-400"
                    with ui.column().classes("gap-1"):
                        ui.label("Profit/Loss").classes("text-xs text-slate-400 uppercase")
                        ui.label(f"₹{pnl:.2f}").classes(f"text-2xl font-bold {pnl_color}")
                    
                    # P&L Percentage
                    pnl_percent = position_data.get("pnl_percent", 0)
                    with ui.column().classes("gap-1"):
                        ui.label("P&L %").classes("text-xs text-slate-400 uppercase")
                        with ui.row().classes("items-center gap-2"):
                            icon = "trending_up" if pnl_percent >= 0 else "trending_down"
                            ui.icon(icon, size="lg").classes(pnl_color)
                            ui.label(f"{pnl_percent:.2f}%").classes(f"text-2xl font-bold {pnl_color}")
        
        details_dialog.open()
    
    # Initial load
    ui.timer(0.1, load_positions_data, once=True)
    
    # Auto-refresh every 30 seconds
    ui.timer(30, load_positions_data)
