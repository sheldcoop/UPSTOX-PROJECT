"""
Instruments Browser Page
Search and browse instruments by symbol, exchange, and segment
"""

from nicegui import ui, run
from ..common import Components
from ..state import async_get, API_BASE
import requests


def render_page(state):
    Components.section_header(
        "Instruments Browser", "Search and explore trading instruments", "search"
    )

    # Search Controls
    with Components.card():
        ui.label("Search Instruments").classes("text-xl font-bold mb-4")

        with ui.row().classes("w-full gap-4"):
            search_input = ui.input(
                label="Search Symbol",
                placeholder="Enter symbol name..."
            ).classes("flex-1")
            
            exchange_filter = ui.select(
                label="Exchange",
                options=["ALL", "NSE", "BSE", "NFO", "MCX", "BFO"],
                value="ALL"
            ).classes("flex-1")

        with ui.row().classes("w-full gap-4"):
            segment_filter = ui.select(
                label="Segment",
                options=["ALL", "NSE_EQ", "BSE_EQ", "NSE_FO", "NSE_INDEX", "MCX_FO"],
                value="ALL"
            ).classes("flex-1")
            
            instrument_type = ui.select(
                label="Instrument Type",
                options=["ALL", "EQUITY", "INDEX", "FUTURES", "OPTIONS", "COMMODITY"],
                value="ALL"
            ).classes("flex-1")

        async def search_instruments():
            if not search_input.value or len(search_input.value) < 2:
                ui.notify("Please enter at least 2 characters to search", type="warning")
                return
            await load_instruments()

        ui.button("Search", icon="search", on_click=search_instruments).props(
            "color=primary size=lg"
        ).classes("mt-4")

    # Results Container
    results_container = ui.column().classes("w-full gap-4 mt-6")

    async def load_instruments():
        results_container.clear()

        with results_container:
            ui.spinner("dots", size="lg").classes("mx-auto")

        try:
            # Build query params
            params = {}
            if search_input.value:
                params["query"] = search_input.value.upper()
            if exchange_filter.value != "ALL":
                params["exchange"] = exchange_filter.value
            if segment_filter.value != "ALL":
                params["segment"] = segment_filter.value
            if instrument_type.value != "ALL":
                params["type"] = instrument_type.value

            # Make request - Using instruments/nse-eq as base endpoint
            # In production, this would be a more generic /api/instruments endpoint
            url = f"{API_BASE}/instruments/nse-eq"
            if params:
                query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                url = f"{url}?{query_string}"

            response = await run.io_bound(requests.get, url)
            
            if response.status_code == 200:
                instruments = response.json()

                results_container.clear()
                with results_container:
                    # Results Summary
                    with ui.row().classes("w-full gap-4 mb-4 flex-wrap"):
                        Components.kpi_card("Total Results", len(instruments), suffix=" instruments")

                    # Results Table
                    with Components.card():
                        with ui.row().classes("w-full justify-between items-center mb-4"):
                            ui.label(f"Search Results ({len(instruments)})").classes("text-xl font-bold")
                            ui.button(icon="refresh", on_click=load_instruments).props("flat dense round")

                        if not instruments:
                            ui.label("No instruments found").classes("text-slate-400 italic p-4 text-center")
                        else:
                            with ui.element("table").classes("w-full text-sm"):
                                # Header
                                with ui.element("thead").classes("text-slate-400 border-b border-slate-700"):
                                    with ui.element("tr"):
                                        with ui.element("th").classes("pb-3 text-left pl-2"):
                                            ui.label("Symbol")
                                        with ui.element("th").classes("pb-3 text-left"):
                                            ui.label("Trading Symbol")
                                        with ui.element("th").classes("pb-3 text-left"):
                                            ui.label("Exchange")
                                        with ui.element("th").classes("pb-3 text-left"):
                                            ui.label("Segment")
                                        with ui.element("th").classes("pb-3 text-left"):
                                            ui.label("Type")
                                        with ui.element("th").classes("pb-3 text-right pr-2"):
                                            ui.label("Actions")

                                # Body
                                with ui.element("tbody"):
                                    for instrument in instruments[:100]:  # Limit to 100 results
                                        with ui.element("tr").classes("border-b border-slate-800 hover:bg-slate-800/50"):
                                            with ui.element("td").classes("py-3 pl-2"):
                                                ui.label(instrument.get("symbol", "")).classes("font-bold text-white")
                                            with ui.element("td").classes("py-3"):
                                                ui.label(instrument.get("trading_symbol", "-")).classes("text-slate-300")
                                            with ui.element("td").classes("py-3"):
                                                exchange = instrument.get("exchange", "")
                                                exchange_color = {
                                                    "NSE": "text-blue-400",
                                                    "BSE": "text-green-400",
                                                    "NFO": "text-purple-400",
                                                    "MCX": "text-orange-400"
                                                }.get(exchange, "text-slate-300")
                                                ui.label(exchange).classes(exchange_color)
                                            with ui.element("td").classes("py-3"):
                                                ui.label(instrument.get("segment", "-")).classes("text-slate-300")
                                            with ui.element("td").classes("py-3"):
                                                ui.label(instrument.get("instrument_type", "-")).classes("text-slate-400")
                                            with ui.element("td").classes("py-3 text-right pr-2"):
                                                instrument_key = instrument.get("instrument_key", "")
                                                
                                                def make_view_handler(key):
                                                    async def handler():
                                                        await view_instrument_details(key)
                                                    return handler
                                                
                                                ui.button(
                                                    icon="visibility",
                                                    on_click=make_view_handler(instrument_key)
                                                ).props("flat dense round size=sm color=primary")

            else:
                results_container.clear()
                with results_container:
                    with Components.card():
                        ui.label(f"Error loading instruments: {response.status_code}").classes("text-red-400")
        except Exception as e:
            results_container.clear()
            with results_container:
                with Components.card():
                    ui.label(f"Error: {str(e)}").classes("text-red-400")

    async def view_instrument_details(instrument_key):
        """Show detailed view of an instrument"""
        try:
            response = await run.io_bound(requests.get, f"{API_BASE}/instruments/{instrument_key}")
            
            if response.status_code == 200:
                instrument = response.json()
                
                # Create dialog for instrument details
                with ui.dialog() as details_dialog, ui.card().classes(
                    "w-full max-w-2xl bg-slate-900 border border-slate-700"
                ):
                    # Header
                    with ui.row().classes("w-full items-center justify-between border-b border-slate-700 pb-4"):
                        with ui.row().classes("items-center gap-3"):
                            ui.icon("info", size="lg").classes("text-indigo-500")
                            with ui.column().classes("gap-1"):
                                ui.label(instrument.get("symbol", "")).classes("text-2xl font-bold text-white")
                                ui.label(instrument.get("trading_symbol", "")).classes("text-sm text-slate-400")

                        ui.button(icon="close", on_click=details_dialog.close).props("flat round")

                    # Details Grid
                    with ui.grid(columns=2).classes("w-full gap-4 mt-4"):
                        # Exchange
                        with ui.column().classes("gap-1"):
                            ui.label("Exchange").classes("text-xs text-slate-400 uppercase")
                            ui.label(instrument.get("exchange", "-")).classes("text-lg font-bold text-white")

                        # Segment
                        with ui.column().classes("gap-1"):
                            ui.label("Segment").classes("text-xs text-slate-400 uppercase")
                            ui.label(instrument.get("segment", "-")).classes("text-lg font-bold text-white")

                        # Instrument Type
                        with ui.column().classes("gap-1"):
                            ui.label("Instrument Type").classes("text-xs text-slate-400 uppercase")
                            ui.label(instrument.get("instrument_type", "-")).classes("text-lg text-white")

                        # Lot Size
                        with ui.column().classes("gap-1"):
                            ui.label("Lot Size").classes("text-xs text-slate-400 uppercase")
                            ui.label(str(instrument.get("lot_size", 1))).classes("text-lg text-white")

                        # Tick Size
                        with ui.column().classes("gap-1"):
                            ui.label("Tick Size").classes("text-xs text-slate-400 uppercase")
                            ui.label(str(instrument.get("tick_size", "-"))).classes("text-lg text-white")

                        # ISIN
                        with ui.column().classes("gap-1"):
                            ui.label("ISIN").classes("text-xs text-slate-400 uppercase")
                            ui.label(instrument.get("isin", "-")).classes("text-sm text-white font-mono")

                details_dialog.open()
            else:
                ui.notify("Error loading instrument details", type="negative")
        except Exception as e:
            ui.notify(f"Error: {str(e)}", type="negative")

    # Popular Instruments Quick Access
    with Components.card().classes("mt-6"):
        ui.label("Popular Instruments").classes("text-lg font-bold mb-3")
        
        popular_symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "NIFTY", "BANKNIFTY"]
        
        with ui.row().classes("w-full gap-2 flex-wrap"):
            for symbol in popular_symbols:
                def make_quick_search(sym):
                    async def handler():
                        search_input.value = sym
                        await search_instruments()
                    return handler
                
                ui.button(
                    symbol,
                    on_click=make_quick_search(symbol)
                ).props("outline dense")
