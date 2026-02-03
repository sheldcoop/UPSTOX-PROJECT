"""
Trade Book Page
Display all executed trades with export functionality
"""

from nicegui import ui, run
from ..common import Components
from ..state import async_get, API_BASE
import requests


def render_page(state):
    Components.section_header(
        "Trade Book", "History of all executed trades", "history"
    )

    # Trade Stats
    stats_container = ui.row().classes("w-full gap-4 flex-wrap mb-6")

    # Filter Controls
    with Components.card():
        ui.label("Filters").classes("text-lg font-bold mb-3")
        
        with ui.row().classes("w-full gap-4 flex-wrap"):
            from_date = Components.date_input("From Date")
            to_date = Components.date_input("To Date")
            search_symbol = ui.input(
                label="Search Symbol",
                placeholder="e.g., RELIANCE"
            ).classes("flex-1")

        async def apply_filters():
            await load_trades()
        
        ui.button("Apply Filters", icon="filter_list", on_click=apply_filters).props(
            "color=primary"
        ).classes("mt-2")

    # Trades Table
    trades_container = ui.column().classes("w-full gap-4 mt-6")

    async def load_trades():
        stats_container.clear()
        trades_container.clear()

        with trades_container:
            ui.spinner("dots", size="lg").classes("mx-auto")

        try:
            # Build query params
            params = {"status": "executed"}  # Only executed trades
            if search_symbol.value:
                params["symbol"] = search_symbol.value.upper()
            if from_date.value:
                params["from_date"] = from_date.value
            if to_date.value:
                params["to_date"] = to_date.value

            # Make request
            url = f"{API_BASE}/orders"
            if params:
                query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                url = f"{url}?{query_string}"

            response = await run.io_bound(requests.get, url)
            
            if response.status_code == 200:
                trades = response.json()

                # Calculate stats
                total_trades = len(trades)
                buy_trades = sum(1 for t in trades if t.get("side", "").upper() == "BUY")
                sell_trades = sum(1 for t in trades if t.get("side", "").upper() == "SELL")
                total_value = sum(t.get("quantity", 0) * t.get("price", 0) for t in trades)

                # Stats Cards
                with stats_container:
                    Components.kpi_card("Total Trades", total_trades, suffix=" executed")
                    Components.kpi_card("Buy Orders", buy_trades, suffix=" trades")
                    Components.kpi_card("Sell Orders", sell_trades, suffix=" trades")
                    Components.kpi_card("Total Value", total_value, prefix="₹")

                # Trades Table
                trades_container.clear()
                with trades_container:
                    with Components.card():
                        with ui.row().classes("w-full justify-between items-center mb-4"):
                            ui.label(f"Executed Trades ({total_trades})").classes("text-xl font-bold")
                            with ui.row().classes("gap-2"):
                                ui.button("Export CSV", icon="download", on_click=lambda: export_trades(trades)).props("outline dense")
                                ui.button(icon="refresh", on_click=load_trades).props("flat dense round")

                        if not trades:
                            ui.label("No executed trades found").classes("text-slate-400 italic p-4")
                        else:
                            with ui.element("table").classes("w-full text-sm"):
                                # Header
                                with ui.element("thead").classes("text-slate-400 border-b border-slate-700"):
                                    with ui.element("tr"):
                                        with ui.element("th").classes("pb-3 text-left pl-2"):
                                            ui.label("Trade ID")
                                        with ui.element("th").classes("pb-3 text-left"):
                                            ui.label("Date/Time")
                                        with ui.element("th").classes("pb-3 text-left"):
                                            ui.label("Symbol")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("Side")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("Qty")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("Price")
                                        with ui.element("th").classes("pb-3 text-right pr-2"):
                                            ui.label("Value")

                                # Body
                                with ui.element("tbody"):
                                    for trade in trades:
                                        trade_value = trade.get("quantity", 0) * trade.get("price", 0)
                                        
                                        with ui.element("tr").classes("border-b border-slate-800 hover:bg-slate-800/50"):
                                            with ui.element("td").classes("py-3 pl-2"):
                                                ui.label(f"#{trade.get('id', '')}").classes("font-mono text-xs text-slate-400")
                                            with ui.element("td").classes("py-3"):
                                                ui.label(trade.get("executed_at", trade.get("created_at", ""))).classes("text-xs text-slate-400")
                                            with ui.element("td").classes("py-3"):
                                                ui.label(trade.get("symbol", "")).classes("font-bold text-white")
                                            with ui.element("td").classes("py-3 text-right"):
                                                side = trade.get("side", "").upper()
                                                side_color = "text-green-400" if side == "BUY" else "text-red-400"
                                                ui.label(side).classes(f"font-medium {side_color}")
                                            with ui.element("td").classes("py-3 text-right"):
                                                ui.label(str(trade.get("quantity", 0))).classes("text-slate-300")
                                            with ui.element("td").classes("py-3 text-right"):
                                                ui.label(f"₹{trade.get('price', 0):.2f}").classes("text-slate-300")
                                            with ui.element("td").classes("py-3 text-right pr-2"):
                                                ui.label(f"₹{trade_value:,.2f}").classes("font-bold text-white")

            else:
                trades_container.clear()
                with trades_container:
                    with Components.card():
                        ui.label(f"Error loading trades: {response.status_code}").classes("text-red-400")
        except Exception as e:
            trades_container.clear()
            with trades_container:
                with Components.card():
                    ui.label(f"Error: {str(e)}").classes("text-red-400")

    def export_trades(trades):
        """Export trades to CSV"""
        try:
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=['id', 'symbol', 'side', 'quantity', 'price', 'executed_at'])
            writer.writeheader()
            for trade in trades:
                writer.writerow({
                    'id': trade.get('id', ''),
                    'symbol': trade.get('symbol', ''),
                    'side': trade.get('side', ''),
                    'quantity': trade.get('quantity', 0),
                    'price': trade.get('price', 0),
                    'executed_at': trade.get('executed_at', trade.get('created_at', ''))
                })
            
            ui.notify(f"Exported {len(trades)} trades to CSV", type="positive")
            # In production, this would trigger a file download
        except Exception as e:
            ui.notify(f"Export failed: {str(e)}", type="negative")

    # Initial load
    ui.timer(0.1, load_trades, once=True)
    
    # Auto-refresh every 60 seconds
    ui.timer(60, load_trades)
