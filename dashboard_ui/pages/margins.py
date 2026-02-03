"""
Margin Requirements Calculator Page
Display available margins and calculate required margins for orders
"""

from nicegui import ui, run
from ..common import Components
from ..state import async_get, async_post, API_BASE
import requests


def render_page(state):
    Components.section_header(
        "Margins", "Margin requirements and calculator", "account_balance"
    )

    # Margin Summary
    margin_summary_container = ui.row().classes("w-full gap-4 flex-wrap mb-6")

    # Margin Calculator
    with Components.card():
        ui.label("Margin Calculator").classes("text-xl font-bold mb-4")

        with ui.row().classes("w-full gap-4"):
            symbol_input = ui.input(label="Symbol", placeholder="e.g., RELIANCE").classes("flex-1")
            exchange_select = ui.select(
                label="Exchange",
                options=["NSE", "BSE", "NFO", "MCX"],
                value="NSE"
            ).classes("flex-1")

        with ui.row().classes("w-full gap-4"):
            transaction_type = ui.select(
                label="Transaction Type",
                options=["BUY", "SELL"],
                value="BUY"
            ).classes("flex-1")
            product_type = ui.select(
                label="Product Type",
                options=["DELIVERY", "INTRADAY", "MARGIN"],
                value="INTRADAY"
            ).classes("flex-1")

        with ui.row().classes("w-full gap-4"):
            quantity_input = ui.number(label="Quantity", value=1, min=1, step=1).classes("flex-1")
            price_input = ui.number(label="Price", value=0, step=0.05).classes("flex-1")

        margin_result_container = ui.column().classes("w-full mt-4")

        async def calculate_margin():
            if not symbol_input.value or not price_input.value:
                ui.notify("Please enter symbol and price", type="warning")
                return

            margin_result_container.clear()
            with margin_result_container:
                ui.spinner("dots").classes("mx-auto")

            try:
                response = await run.io_bound(
                    requests.post,
                    f"{API_BASE}/margins/calculate",
                    json={
                        "symbol": symbol_input.value.upper(),
                        "exchange": exchange_select.value,
                        "transaction_type": transaction_type.value,
                        "product_type": product_type.value,
                        "quantity": int(quantity_input.value),
                        "price": float(price_input.value)
                    }
                )

                margin_result_container.clear()
                
                if response.status_code == 200:
                    margin_data = response.json()
                    
                    with margin_result_container:
                        with ui.card().classes("w-full bg-slate-800/50 border border-indigo-500/30"):
                            ui.label("Margin Requirement").classes("text-lg font-bold mb-4 text-indigo-400")
                            
                            with ui.grid(columns=2).classes("w-full gap-4"):
                                # Required Margin
                                with ui.column().classes("gap-1"):
                                    ui.label("Required Margin").classes("text-xs text-slate-400 uppercase")
                                    ui.label(f"₹{margin_data.get('required_margin', 0):,.2f}").classes(
                                        "text-2xl font-bold text-white"
                                    )

                                # Total Amount
                                with ui.column().classes("gap-1"):
                                    ui.label("Total Amount").classes("text-xs text-slate-400 uppercase")
                                    ui.label(f"₹{margin_data.get('total_amount', 0):,.2f}").classes(
                                        "text-2xl font-bold text-white"
                                    )

                                # Exposure
                                with ui.column().classes("gap-1"):
                                    ui.label("Exposure").classes("text-xs text-slate-400 uppercase")
                                    ui.label(f"₹{margin_data.get('exposure', 0):,.2f}").classes(
                                        "text-lg text-slate-300"
                                    )

                                # Span Margin
                                with ui.column().classes("gap-1"):
                                    ui.label("Span Margin").classes("text-xs text-slate-400 uppercase")
                                    ui.label(f"₹{margin_data.get('span_margin', 0):,.2f}").classes(
                                        "text-lg text-slate-300"
                                    )
                else:
                    with margin_result_container:
                        ui.label(f"Error calculating margin: {response.json().get('error', 'Unknown error')}").classes(
                            "text-red-400"
                        )
            except Exception as e:
                margin_result_container.clear()
                with margin_result_container:
                    ui.label(f"Error: {str(e)}").classes("text-red-400")

        ui.button("Calculate Margin", on_click=calculate_margin, icon="calculate").props(
            "color=primary size=lg"
        ).classes("mt-4")

    # Available Margins Display
    available_margins_container = ui.column().classes("w-full mt-6")

    async def load_available_margins():
        margin_summary_container.clear()
        available_margins_container.clear()

        with available_margins_container:
            ui.spinner("dots", size="lg").classes("mx-auto")

        try:
            response = await run.io_bound(requests.get, f"{API_BASE}/margins")
            if response.status_code == 200:
                margin_info = response.json()

                # Summary Cards
                with margin_summary_container:
                    Components.kpi_card(
                        "Available Cash",
                        margin_info.get("available_cash", 0),
                        prefix="₹"
                    )
                    Components.kpi_card(
                        "Collateral",
                        margin_info.get("collateral", 0),
                        prefix="₹"
                    )
                    Components.kpi_card(
                        "Used Margin",
                        margin_info.get("used_margin", 0),
                        prefix="₹",
                        delta=-0.5
                    )
                    Components.kpi_card(
                        "Available Margin",
                        margin_info.get("available_margin", 0),
                        prefix="₹",
                        delta=0.5
                    )

                # Detailed Breakdown
                available_margins_container.clear()
                with available_margins_container:
                    with Components.card():
                        ui.label("Margin Breakdown").classes("text-xl font-bold mb-4")

                        segments = margin_info.get("segments", {})
                        
                        if not segments:
                            ui.label("No margin data available").classes("text-slate-400 italic")
                        else:
                            with ui.element("table").classes("w-full text-sm"):
                                # Header
                                with ui.element("thead").classes("text-slate-400 border-b border-slate-700"):
                                    with ui.element("tr"):
                                        with ui.element("th").classes("pb-3 text-left pl-2"):
                                            ui.label("Segment")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("Available")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("Used")
                                        with ui.element("th").classes("pb-3 text-right pr-2"):
                                            ui.label("Total")

                                # Body
                                with ui.element("tbody"):
                                    for segment, data in segments.items():
                                        with ui.element("tr").classes("border-b border-slate-800"):
                                            with ui.element("td").classes("py-3 pl-2"):
                                                ui.label(segment).classes("font-bold text-white")
                                            with ui.element("td").classes("py-3 text-right"):
                                                ui.label(f"₹{data.get('available', 0):,.2f}").classes("text-green-400")
                                            with ui.element("td").classes("py-3 text-right"):
                                                ui.label(f"₹{data.get('used', 0):,.2f}").classes("text-red-400")
                                            with ui.element("td").classes("py-3 text-right pr-2"):
                                                ui.label(f"₹{data.get('total', 0):,.2f}").classes("text-slate-300")

            else:
                available_margins_container.clear()
                with available_margins_container:
                    with Components.card():
                        ui.label(f"Error loading margin data: {response.status_code}").classes("text-red-400")
        except Exception as e:
            available_margins_container.clear()
            with available_margins_container:
                with Components.card():
                    ui.label(f"Error: {str(e)}").classes("text-red-400")

    # Initial load
    ui.timer(0.1, load_available_margins, once=True)
    
    # Auto-refresh every 30 seconds
    ui.timer(30, load_available_margins)
