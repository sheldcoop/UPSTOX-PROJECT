"""
Orders & Alerts Management Page
Handles paper trading orders and price alerts
"""

from nicegui import ui, run
from ..common import Components
import sys
from pathlib import Path
import asyncio
import requests
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))

API_BASE = "http://localhost:8000/api"


def render_page(state):
    Components.section_header(
        "Orders & Alerts", "Manage paper trading orders and price alerts", "receipt"
    )

    # Tabs for Orders and Alerts
    with ui.tabs().classes("w-full") as tabs:
        orders_tab = ui.tab("Orders", icon="shopping_cart")
        alerts_tab = ui.tab("Alerts", icon="notifications")

    with ui.tab_panels(tabs, value=orders_tab).classes("w-full mt-4"):
        # Orders Panel
        with ui.tab_panel(orders_tab):
            render_orders_section()

        # Alerts Panel
        with ui.tab_panel(alerts_tab):
            render_alerts_section()


def render_orders_section():
    """Render orders management section"""
    orders_container = ui.column().classes("w-full gap-4")

    # Place Order Form
    with Components.card():
        ui.label("Place New Order").classes("text-xl font-bold mb-4")

        with ui.row().classes("w-full gap-4"):
            symbol_input = ui.input(
                label="Symbol", placeholder="e.g., RELIANCE"
            ).classes("flex-1")
            side_select = ui.select(
                label="Side",
                options=["BUY", "SELL"],
                value="BUY",
            ).classes("flex-1")

        with ui.row().classes("w-full gap-4"):
            quantity_input = ui.number(
                label="Quantity", value=1, min=1, step=1
            ).classes("flex-1")
            order_type_select = ui.select(
                label="Order Type",
                options=["MARKET", "LIMIT", "STOP_LOSS"],
                value="MARKET",
            ).classes("flex-1")

        price_input = ui.number(label="Price (for LIMIT orders)", value=0).classes(
            "w-full"
        )

        async def place_order():
            if not symbol_input.value:
                ui.notify("Please enter a symbol", type="warning")
                return

            try:
                response = await run.io_bound(
                    requests.post,
                    f"{API_BASE}/orders",
                    json={
                        "symbol": symbol_input.value.upper(),
                        "side": side_select.value,
                        "quantity": int(quantity_input.value),
                        "order_type": order_type_select.value,
                        "price": (
                            float(price_input.value) if price_input.value else None
                        ),
                    },
                )

                if response.status_code == 201:
                    ui.notify("Order placed successfully!", type="positive")
                    symbol_input.value = ""
                    quantity_input.value = 1
                    price_input.value = 0
                    await load_orders()
                else:
                    ui.notify(f"Error: {response.json().get('error')}", type="negative")
            except Exception as e:
                ui.notify(f"Error placing order: {str(e)}", type="negative")

        ui.button("Place Order", on_click=place_order, icon="add_shopping_cart").props(
            "color=primary"
        ).classes("mt-4")

    # Orders List
    with Components.card():
        with ui.row().classes("w-full justify-between items-center mb-4"):
            ui.label("Order History").classes("text-xl font-bold")
            ui.button(icon="refresh", on_click=lambda: load_orders()).props(
                "flat dense round"
            )

        orders_table_container = ui.column().classes("w-full")

    async def load_orders():
        try:
            response = await run.io_bound(requests.get, f"{API_BASE}/orders")
            if response.status_code == 200:
                orders = response.json()
                orders_table_container.clear()

                with orders_table_container:
                    if not orders:
                        ui.label("No orders yet").classes("text-slate-400 italic")
                    else:
                        columns = [
                            {
                                "name": "id",
                                "label": "ID",
                                "field": "id",
                                "align": "left",
                            },
                            {
                                "name": "symbol",
                                "label": "Symbol",
                                "field": "symbol",
                                "align": "left",
                            },
                            {
                                "name": "side",
                                "label": "Side",
                                "field": "side",
                                "align": "left",
                            },
                            {
                                "name": "quantity",
                                "label": "Qty",
                                "field": "quantity",
                                "align": "right",
                            },
                            {
                                "name": "order_type",
                                "label": "Type",
                                "field": "order_type",
                                "align": "left",
                            },
                            {
                                "name": "price",
                                "label": "Price",
                                "field": "price",
                                "align": "right",
                            },
                            {
                                "name": "status",
                                "label": "Status",
                                "field": "status",
                                "align": "left",
                            },
                            {
                                "name": "created_at",
                                "label": "Created",
                                "field": "created_at",
                                "align": "left",
                            },
                            {
                                "name": "actions",
                                "label": "Actions",
                                "field": "id",
                                "align": "center",
                            },
                        ]

                        table = ui.table(columns=columns, rows=orders, row_key="id")
                        table.add_slot(
                            "body-cell-actions",
                            """
                            <q-td :props="props">
                                <q-btn flat dense round icon="cancel" color="negative" size="sm"
                                       @click="$parent.$emit('cancel_order', props.row.id)"
                                       v-if="props.row.status === 'pending' || props.row.status === 'open'">
                                    <q-tooltip>Cancel Order</q-tooltip>
                                </q-btn>
                            </q-td>
                        """,
                        )

                        async def cancel_order(e):
                            order_id = e.args
                            try:
                                response = await run.io_bound(
                                    requests.delete, f"{API_BASE}/orders/{order_id}"
                                )
                                if response.status_code == 200:
                                    ui.notify("Order cancelled", type="positive")
                                    await load_orders()
                                else:
                                    ui.notify("Error cancelling order", type="negative")
                            except Exception as ex:
                                ui.notify(f"Error: {str(ex)}", type="negative")

                        table.on("cancel_order", cancel_order)

            else:
                orders_table_container.clear()
                with orders_table_container:
                    ui.label("Error loading orders").classes("text-red-400")
        except Exception as e:
            orders_table_container.clear()
            with orders_table_container:
                ui.label(f"Error: {str(e)}").classes("text-red-400")

    # Initial load
    ui.timer(0.1, load_orders, once=True)


def render_alerts_section():
    """Render alerts management section"""
    alerts_container = ui.column().classes("w-full gap-4")

    # Create Alert Form
    with Components.card():
        ui.label("Create Price Alert").classes("text-xl font-bold mb-4")

        with ui.row().classes("w-full gap-4"):
            alert_symbol_input = ui.input(
                label="Symbol", placeholder="e.g., NIFTY"
            ).classes("flex-1")
            alert_type_select = ui.select(
                label="Alert Type",
                options=["price_above", "price_below", "volume_spike"],
                value="price_above",
            ).classes("flex-1")

        with ui.row().classes("w-full gap-4"):
            threshold_input = ui.number(
                label="Threshold Value", value=0, step=0.01
            ).classes("flex-1")
            priority_select = ui.select(
                label="Priority",
                options=["LOW", "MEDIUM", "HIGH"],
                value="MEDIUM",
            ).classes("flex-1")

        async def create_alert():
            if not alert_symbol_input.value or not threshold_input.value:
                ui.notify("Please fill all required fields", type="warning")
                return

            try:
                response = await run.io_bound(
                    requests.post,
                    f"{API_BASE}/alerts",
                    json={
                        "symbol": alert_symbol_input.value.upper(),
                        "alert_type": alert_type_select.value,
                        "threshold": float(threshold_input.value),
                        "priority": priority_select.value,
                    },
                )

                if response.status_code == 201:
                    ui.notify("Alert created successfully!", type="positive")
                    alert_symbol_input.value = ""
                    threshold_input.value = 0
                    await load_alerts()
                else:
                    ui.notify(f"Error: {response.json().get('error')}", type="negative")
            except Exception as e:
                ui.notify(f"Error creating alert: {str(e)}", type="negative")

        ui.button("Create Alert", on_click=create_alert, icon="add_alert").props(
            "color=primary"
        ).classes("mt-4")

    # Alerts List
    with Components.card():
        with ui.row().classes("w-full justify-between items-center mb-4"):
            ui.label("Active Alerts").classes("text-xl font-bold")
            ui.button(icon="refresh", on_click=lambda: load_alerts()).props(
                "flat dense round"
            )

        alerts_table_container = ui.column().classes("w-full")

    async def load_alerts():
        try:
            response = await run.io_bound(requests.get, f"{API_BASE}/alerts")
            if response.status_code == 200:
                alerts = response.json()
                alerts_table_container.clear()

                with alerts_table_container:
                    if not alerts:
                        ui.label("No active alerts").classes("text-slate-400 italic")
                    else:
                        columns = [
                            {
                                "name": "id",
                                "label": "ID",
                                "field": "id",
                                "align": "left",
                            },
                            {
                                "name": "symbol",
                                "label": "Symbol",
                                "field": "symbol",
                                "align": "left",
                            },
                            {
                                "name": "alert_type",
                                "label": "Type",
                                "field": "alert_type",
                                "align": "left",
                            },
                            {
                                "name": "threshold",
                                "label": "Threshold",
                                "field": "threshold",
                                "align": "right",
                            },
                            {
                                "name": "priority",
                                "label": "Priority",
                                "field": "priority",
                                "align": "left",
                            },
                            {
                                "name": "created_at",
                                "label": "Created",
                                "field": "created_at",
                                "align": "left",
                            },
                            {
                                "name": "actions",
                                "label": "Actions",
                                "field": "id",
                                "align": "center",
                            },
                        ]

                        table = ui.table(columns=columns, rows=alerts, row_key="id")
                        table.add_slot(
                            "body-cell-actions",
                            """
                            <q-td :props="props">
                                <q-btn flat dense round icon="delete" color="negative" size="sm"
                                       @click="$parent.$emit('delete_alert', props.row.id)">
                                    <q-tooltip>Delete Alert</q-tooltip>
                                </q-btn>
                            </q-td>
                        """,
                        )

                        async def delete_alert(e):
                            alert_id = e.args
                            try:
                                response = await run.io_bound(
                                    requests.delete, f"{API_BASE}/alerts/{alert_id}"
                                )
                                if response.status_code == 200:
                                    ui.notify("Alert deleted", type="positive")
                                    await load_alerts()
                                else:
                                    ui.notify("Error deleting alert", type="negative")
                            except Exception as ex:
                                ui.notify(f"Error: {str(ex)}", type="negative")

                        table.on("delete_alert", delete_alert)

            else:
                alerts_table_container.clear()
                with alerts_table_container:
                    ui.label("Error loading alerts").classes("text-red-400")
        except Exception as e:
            alerts_table_container.clear()
            with alerts_table_container:
                ui.label(f"Error: {str(e)}").classes("text-red-400")

    # Initial load
    ui.timer(0.1, load_alerts, once=True)
