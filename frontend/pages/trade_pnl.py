"""
Trade Profit & Loss Tracking Page
Daily P&L summary and trade-wise breakdown
"""

from nicegui import ui, run
from ..common import Components
from ..state import async_get, API_BASE
import requests


def render_page(state):
    Components.section_header(
        "Trade P&L", "Profit & Loss analysis and tracking", "attach_money"
    )

    # Summary Stats
    summary_container = ui.row().classes("w-full gap-4 flex-wrap mb-6")

    # P&L Details
    pnl_container = ui.column().classes("w-full gap-4")

    async def load_pnl_data():
        summary_container.clear()
        pnl_container.clear()

        with pnl_container:
            ui.spinner("dots", size="lg").classes("mx-auto")

        try:
            response = await run.io_bound(requests.get, f"{API_BASE}/trade-profit-loss")
            if response.status_code == 200:
                pnl_data = response.json()
                
                # Summary Stats
                with summary_container:
                    total_pnl = pnl_data.get("total_pnl", 0)
                    daily_pnl = pnl_data.get("daily_pnl", 0)
                    total_trades = pnl_data.get("total_trades", 0)
                    winning_trades = pnl_data.get("winning_trades", 0)
                    
                    Components.kpi_card(
                        "Total P&L",
                        total_pnl,
                        prefix="₹",
                        delta=1.5 if total_pnl > 0 else -1.5
                    )
                    Components.kpi_card(
                        "Today's P&L",
                        daily_pnl,
                        prefix="₹",
                        delta=0.8 if daily_pnl > 0 else -0.8
                    )
                    Components.kpi_card(
                        "Total Trades",
                        total_trades,
                        suffix=" trades"
                    )
                    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                    Components.kpi_card(
                        "Win Rate",
                        win_rate,
                        suffix="%",
                        delta=0.5 if win_rate > 50 else -0.5
                    )

                # Trade-wise P&L Table
                pnl_container.clear()
                with pnl_container:
                    with Components.card():
                        with ui.row().classes("w-full justify-between items-center mb-4"):
                            ui.label("Trade-wise P&L Breakdown").classes("text-xl font-bold")
                            ui.button(icon="refresh", on_click=load_pnl_data).props("flat dense round")

                        trades = pnl_data.get("trades", [])
                        
                        if not trades:
                            ui.label("No trades found").classes("text-slate-400 italic p-4")
                        else:
                            with ui.element("table").classes("w-full text-sm"):
                                # Header
                                with ui.element("thead").classes("text-slate-400 border-b border-slate-700"):
                                    with ui.element("tr"):
                                        with ui.element("th").classes("pb-3 text-left pl-2"):
                                            ui.label("Date")
                                        with ui.element("th").classes("pb-3 text-left"):
                                            ui.label("Symbol")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("Side")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("Quantity")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("Entry")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("Exit")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("P&L")
                                        with ui.element("th").classes("pb-3 text-right pr-2"):
                                            ui.label("P&L %")

                                # Body
                                with ui.element("tbody"):
                                    for trade in trades:
                                        pnl = trade.get("pnl", 0)
                                        pnl_pct = trade.get("pnl_percent", 0)
                                        pnl_color = "text-green-400" if pnl >= 0 else "text-red-400"

                                        with ui.element("tr").classes("border-b border-slate-800 hover:bg-slate-800/50"):
                                            with ui.element("td").classes("py-3 pl-2"):
                                                ui.label(trade.get("date", "")).classes("text-slate-300")
                                            with ui.element("td").classes("py-3"):
                                                ui.label(trade.get("symbol", "")).classes("font-bold text-white")
                                            with ui.element("td").classes("py-3 text-right"):
                                                side = trade.get("side", "").upper()
                                                side_color = "text-green-400" if side == "BUY" else "text-red-400"
                                                ui.label(side).classes(side_color)
                                            with ui.element("td").classes("py-3 text-right"):
                                                ui.label(str(trade.get("quantity", 0))).classes("text-slate-300")
                                            with ui.element("td").classes("py-3 text-right"):
                                                ui.label(f"₹{trade.get('entry_price', 0):.2f}").classes("text-slate-300")
                                            with ui.element("td").classes("py-3 text-right"):
                                                ui.label(f"₹{trade.get('exit_price', 0):.2f}").classes("text-slate-300")
                                            with ui.element("td").classes("py-3 text-right"):
                                                ui.label(f"₹{pnl:.2f}").classes(f"font-bold {pnl_color}")
                                            with ui.element("td").classes("py-3 text-right pr-2"):
                                                icon = "trending_up" if pnl_pct >= 0 else "trending_down"
                                                with ui.row().classes(f"items-center gap-1 justify-end {pnl_color}"):
                                                    ui.icon(icon, size="xs")
                                                    ui.label(f"{abs(pnl_pct):.2f}%")

                    # P&L Chart (placeholder for future enhancement)
                    with Components.card():
                        ui.label("P&L Trend Chart").classes("text-lg font-bold mb-4")
                        ui.label("Chart visualization coming soon...").classes("text-slate-400 italic p-8 text-center")

            else:
                pnl_container.clear()
                with pnl_container:
                    with Components.card():
                        ui.label(f"Error loading P&L data: {response.status_code}").classes("text-red-400")
        except Exception as e:
            pnl_container.clear()
            with pnl_container:
                with Components.card():
                    ui.label(f"Error: {str(e)}").classes("text-red-400")

    # Initial load
    ui.timer(0.1, load_pnl_data, once=True)
    
    # Auto-refresh every 60 seconds
    ui.timer(60, load_pnl_data)
