"""
Order Book Page
Comprehensive view of all orders (pending, executed, cancelled)
"""

from nicegui import ui, run
from ..common import Components
from ..state import async_get, API_BASE
import requests


def render_page(state):
    Components.section_header(
        "Order Book", "Complete history of all orders", "receipt_long"
    )

    # Order Stats
    stats_container = ui.row().classes("w-full gap-4 flex-wrap mb-6")

    # Filter Controls
    with Components.card():
        ui.label("Filters").classes("text-lg font-bold mb-3")
        
        with ui.row().classes("w-full gap-4 flex-wrap"):
            status_filter = ui.select(
                label="Status",
                options=["ALL", "PENDING", "EXECUTED", "CANCELLED", "REJECTED"],
                value="ALL"
            ).classes("flex-1")
            
            order_type_filter = ui.select(
                label="Order Type",
                options=["ALL", "MARKET", "LIMIT", "STOP_LOSS"],
                value="ALL"
            ).classes("flex-1")
            
            search_symbol = ui.input(
                label="Search Symbol",
                placeholder="e.g., RELIANCE"
            ).classes("flex-1")

        async def apply_filters():
            await load_orders()
        
        ui.button("Apply Filters", icon="filter_list", on_click=apply_filters).props(
            "color=primary"
        ).classes("mt-2")

    # Orders Table
    orders_container = ui.column().classes("w-full gap-4 mt-6")

    async def load_orders():
        stats_container.clear()
        orders_container.clear()

        with orders_container:
            ui.spinner("dots", size="lg").classes("mx-auto")

        try:
            # Build query params
            params = {}
            if status_filter.value != "ALL":
                params["status"] = status_filter.value.lower()
            if order_type_filter.value != "ALL":
                params["order_type"] = order_type_filter.value.lower()
            if search_symbol.value:
                params["symbol"] = search_symbol.value.upper()

            # Make request
            url = f"{API_BASE}/orders"
            if params:
                query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                url = f"{url}?{query_string}"

            response = await run.io_bound(requests.get, url)
            
            if response.status_code == 200:
                orders = response.json()

                # Calculate stats
                total_orders = len(orders)
                pending = sum(1 for o in orders if o.get("status", "").upper() == "PENDING")
                executed = sum(1 for o in orders if o.get("status", "").upper() == "EXECUTED")
                cancelled = sum(1 for o in orders if o.get("status", "").upper() == "CANCELLED")

                # Stats Cards
                with stats_container:
                    Components.kpi_card("Total Orders", total_orders, suffix=" orders")
                    Components.kpi_card("Pending", pending, suffix=" orders")
                    Components.kpi_card("Executed", executed, suffix=" orders")
                    Components.kpi_card("Cancelled", cancelled, suffix=" orders")

                # Orders Table
                orders_container.clear()
                with orders_container:
                    with Components.card():
                        with ui.row().classes("w-full justify-between items-center mb-4"):
                            ui.label(f"Orders ({total_orders})").classes("text-xl font-bold")
                            ui.button(icon="refresh", on_click=load_orders).props("flat dense round")

                        if not orders:
                            ui.label("No orders found").classes("text-slate-400 italic p-4")
                        else:
                            with ui.element("table").classes("w-full text-sm"):
                                # Header
                                with ui.element("thead").classes("text-slate-400 border-b border-slate-700"):
                                    with ui.element("tr"):
                                        with ui.element("th").classes("pb-3 text-left pl-2"):
                                            ui.label("Order ID")
                                        with ui.element("th").classes("pb-3 text-left"):
                                            ui.label("Symbol")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("Type")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("Side")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("Qty")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("Price")
                                        with ui.element("th").classes("pb-3 text-left"):
                                            ui.label("Status")
                                        with ui.element("th").classes("pb-3 text-left pr-2"):
                                            ui.label("Time")

                                # Body
                                with ui.element("tbody"):
                                    for order in orders:
                                        status = order.get("status", "").upper()
                                        status_colors = {
                                            "PENDING": "text-yellow-400",
                                            "EXECUTED": "text-green-400",
                                            "CANCELLED": "text-red-400",
                                            "REJECTED": "text-red-600"
                                        }
                                        status_color = status_colors.get(status, "text-slate-400")

                                        with ui.element("tr").classes("border-b border-slate-800 hover:bg-slate-800/50"):
                                            with ui.element("td").classes("py-3 pl-2"):
                                                ui.label(f"#{order.get('id', '')}").classes("font-mono text-xs text-slate-400")
                                            with ui.element("td").classes("py-3"):
                                                ui.label(order.get("symbol", "")).classes("font-bold text-white")
                                            with ui.element("td").classes("py-3 text-right"):
                                                ui.label(order.get("order_type", "")).classes("text-slate-300")
                                            with ui.element("td").classes("py-3 text-right"):
                                                side = order.get("side", "").upper()
                                                side_color = "text-green-400" if side == "BUY" else "text-red-400"
                                                ui.label(side).classes(side_color)
                                            with ui.element("td").classes("py-3 text-right"):
                                                ui.label(str(order.get("quantity", 0))).classes("text-slate-300")
                                            with ui.element("td").classes("py-3 text-right"):
                                                price = order.get("price", 0)
                                                price_text = f"₹{price:.2f}" if price > 0 else "MKT"
                                                ui.label(price_text).classes("text-slate-300")
                                            with ui.element("td").classes("py-3"):
                                                ui.label(status).classes(f"font-medium {status_color}")
                                            with ui.element("td").classes("py-3 pr-2"):
                                                ui.label(order.get("created_at", "")).classes("text-xs text-slate-400")

            else:
                orders_container.clear()
                with orders_container:
                    with Components.card():
                        ui.label(f"Error loading orders: {response.status_code}").classes("text-red-400")
        except Exception as e:
            orders_container.clear()
            with orders_container:
                with Components.card():
                    ui.label(f"Error: {str(e)}").classes("text-red-400")

    # Initial load
    ui.timer(0.1, load_orders, once=True)
    
    # Auto-refresh every 30 seconds
    ui.timer(30, load_orders)
