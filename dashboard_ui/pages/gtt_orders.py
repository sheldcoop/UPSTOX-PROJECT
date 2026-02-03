"""
GTT (Good Till Triggered) Orders Management Page
Manage GTT orders with create, modify, and cancel functionality
"""

from nicegui import ui, run
from ..common import Components
from ..state import async_get, async_post, API_BASE
import requests


def render_page(state):
    Components.section_header(
        "GTT Orders", "Good Till Triggered order management", "schedule"
    )

    # Tabs for GTT Management
    with ui.tabs().classes("w-full") as tabs:
        active_tab = ui.tab("Active GTT", icon="list")
        create_tab = ui.tab("Create GTT", icon="add_circle")

    with ui.tab_panels(tabs, value=active_tab).classes("w-full mt-4"):
        # Active GTT Orders Panel
        with ui.tab_panel(active_tab):
            render_active_gtt_section()

        # Create GTT Panel
        with ui.tab_panel(create_tab):
            render_create_gtt_section()


def render_active_gtt_section():
    """Display and manage active GTT orders"""
    gtt_container = ui.column().classes("w-full gap-4")

    with Components.card():
        with ui.row().classes("w-full justify-between items-center mb-4"):
            ui.label("Active GTT Orders").classes("text-xl font-bold")
            ui.button(icon="refresh", on_click=lambda: load_gtt_orders()).props(
                "flat dense round"
            )

        gtt_table_container = ui.column().classes("w-full")

    async def load_gtt_orders():
        gtt_table_container.clear()
        with gtt_table_container:
            ui.spinner("dots", size="lg").classes("mx-auto")

        try:
            response = await run.io_bound(requests.get, f"{API_BASE}/gtt")
            if response.status_code == 200:
                gtt_orders = response.json()
                gtt_table_container.clear()

                with gtt_table_container:
                    if not gtt_orders:
                        ui.label("No active GTT orders").classes("text-slate-400 italic p-4")
                    else:
                        # Summary Stats
                        total_gtt = len(gtt_orders)
                        active_gtt = sum(1 for g in gtt_orders if g.get("status") == "active")

                        with ui.row().classes("w-full gap-4 mb-4 flex-wrap"):
                            Components.kpi_card("Total GTT", total_gtt, suffix=" orders")
                            Components.kpi_card("Active", active_gtt, suffix=" orders")

                        # GTT Table
                        with ui.element("table").classes("w-full text-sm"):
                            # Header
                            with ui.element("thead").classes("text-slate-400 border-b border-slate-700"):
                                with ui.element("tr"):
                                    with ui.element("th").classes("pb-3 text-left pl-2"):
                                        ui.label("Symbol")
                                    with ui.element("th").classes("pb-3 text-left"):
                                        ui.label("Type")
                                    with ui.element("th").classes("pb-3 text-right"):
                                        ui.label("Trigger Price")
                                    with ui.element("th").classes("pb-3 text-right"):
                                        ui.label("Limit Price")
                                    with ui.element("th").classes("pb-3 text-right"):
                                        ui.label("Quantity")
                                    with ui.element("th").classes("pb-3 text-left"):
                                        ui.label("Status")
                                    with ui.element("th").classes("pb-3 text-center pr-2"):
                                        ui.label("Actions")

                            # Body
                            with ui.element("tbody"):
                                for gtt in gtt_orders:
                                    with ui.element("tr").classes("border-b border-slate-800 hover:bg-slate-800/50"):
                                        with ui.element("td").classes("py-3 pl-2"):
                                            ui.label(gtt.get("symbol", "")).classes("font-bold text-white")
                                        with ui.element("td").classes("py-3"):
                                            ui.label(gtt.get("order_type", "")).classes("text-slate-300")
                                        with ui.element("td").classes("py-3 text-right"):
                                            ui.label(f"₹{gtt.get('trigger_price', 0):.2f}").classes("text-slate-300")
                                        with ui.element("td").classes("py-3 text-right"):
                                            ui.label(f"₹{gtt.get('limit_price', 0):.2f}").classes("text-slate-300")
                                        with ui.element("td").classes("py-3 text-right"):
                                            ui.label(str(gtt.get("quantity", 0))).classes("text-slate-300")
                                        with ui.element("td").classes("py-3"):
                                            status = gtt.get("status", "").upper()
                                            status_color = "text-green-400" if status == "ACTIVE" else "text-slate-400"
                                            ui.label(status).classes(status_color)
                                        with ui.element("td").classes("py-3 text-center pr-2"):
                                            gtt_id = gtt.get("id")
                                            
                                            def make_cancel_handler(order_id):
                                                async def handler():
                                                    await cancel_gtt(order_id)
                                                return handler
                                            
                                            ui.button(
                                                icon="cancel",
                                                on_click=make_cancel_handler(gtt_id)
                                            ).props("flat dense round size=sm color=negative")

            else:
                gtt_table_container.clear()
                with gtt_table_container:
                    ui.label(f"Error loading GTT orders: {response.status_code}").classes("text-red-400")
        except Exception as e:
            gtt_table_container.clear()
            with gtt_table_container:
                ui.label(f"Error: {str(e)}").classes("text-red-400")

    async def cancel_gtt(gtt_id):
        try:
            response = await run.io_bound(requests.delete, f"{API_BASE}/gtt/{gtt_id}")
            if response.status_code == 200:
                ui.notify("GTT order cancelled successfully", type="positive")
                await load_gtt_orders()
            else:
                ui.notify(f"Error cancelling GTT order", type="negative")
        except Exception as e:
            ui.notify(f"Error: {str(e)}", type="negative")

    # Initial load
    ui.timer(0.1, load_gtt_orders, once=True)


def render_create_gtt_section():
    """Form to create new GTT order"""
    with Components.card():
        ui.label("Create New GTT Order").classes("text-xl font-bold mb-4")

        with ui.row().classes("w-full gap-4"):
            symbol_input = ui.input(label="Symbol", placeholder="e.g., RELIANCE").classes("flex-1")
            transaction_type = ui.select(
                label="Transaction Type",
                options=["BUY", "SELL"],
                value="BUY"
            ).classes("flex-1")

        with ui.row().classes("w-full gap-4"):
            quantity_input = ui.number(label="Quantity", value=1, min=1, step=1).classes("flex-1")
            order_type = ui.select(
                label="Order Type",
                options=["SINGLE", "OCO"],
                value="SINGLE"
            ).classes("flex-1")

        with ui.row().classes("w-full gap-4"):
            trigger_price = ui.number(label="Trigger Price", value=0, step=0.05).classes("flex-1")
            limit_price = ui.number(label="Limit Price (optional)", value=0, step=0.05).classes("flex-1")

        condition_type = ui.select(
            label="Condition Type",
            options=["LTP_ABOVE", "LTP_BELOW", "LTP_AT_OR_ABOVE", "LTP_AT_OR_BELOW"],
            value="LTP_ABOVE"
        ).classes("w-full")

        async def create_gtt():
            if not symbol_input.value or not trigger_price.value:
                ui.notify("Please fill required fields (Symbol, Trigger Price)", type="warning")
                return

            try:
                response = await run.io_bound(
                    requests.post,
                    f"{API_BASE}/gtt",
                    json={
                        "symbol": symbol_input.value.upper(),
                        "transaction_type": transaction_type.value,
                        "quantity": int(quantity_input.value),
                        "order_type": order_type.value,
                        "trigger_price": float(trigger_price.value),
                        "limit_price": float(limit_price.value) if limit_price.value else None,
                        "condition_type": condition_type.value,
                    }
                )

                if response.status_code in [200, 201]:
                    ui.notify("GTT order created successfully!", type="positive")
                    # Reset form
                    symbol_input.value = ""
                    quantity_input.value = 1
                    trigger_price.value = 0
                    limit_price.value = 0
                else:
                    error_msg = response.json().get("error", "Unknown error")
                    ui.notify(f"Error: {error_msg}", type="negative")
            except Exception as e:
                ui.notify(f"Error creating GTT: {str(e)}", type="negative")

        ui.button("Create GTT Order", on_click=create_gtt, icon="add_task").props(
            "color=primary size=lg"
        ).classes("mt-4")

        # Help Text
        with ui.expansion("GTT Order Help", icon="help").classes("w-full mt-4 bg-slate-800/30"):
            ui.label("GTT (Good Till Triggered) orders are standing orders that execute when price conditions are met.").classes("text-sm text-slate-400 mb-2")
            ui.label("• Single: Basic GTT order").classes("text-xs text-slate-500")
            ui.label("• OCO (One Cancels Other): Two orders, one execution cancels the other").classes("text-xs text-slate-500")
