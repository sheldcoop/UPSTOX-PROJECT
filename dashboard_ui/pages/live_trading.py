"""
Live Trading Page
Place, modify, and cancel live orders through Upstox
"""

from nicegui import ui, run
from ..common import Components
import sys
from pathlib import Path
import asyncio
import requests

sys.path.append(str(Path(__file__).parent.parent.parent))

API_BASE = "http://localhost:9000/api"


def render_page(state):
    Components.section_header(
        "Live Trading",
        "⚠️ Place REAL orders on Upstox - USE WITH CAUTION",
        "local_atm",
    )

    # Warning Banner
    with ui.card().classes("w-full bg-red-900 border-2 border-red-500 mb-6"):
        with ui.row().classes("items-center gap-4"):
            ui.icon("warning", size="xl").classes("text-yellow-400")
            with ui.column():
                ui.label("⚠️ LIVE TRADING MODE - REAL MONEY").classes(
                    "text-xl font-bold text-white"
                )
                ui.label(
                    "Orders placed here are REAL and will be executed on the market. Double-check all details before submitting."
                ).classes("text-sm text-red-200")

    content_container = ui.column().classes("w-full gap-6")

    # Place Order Form
    with Components.card():
        ui.label("Place Live Order").classes("text-xl font-bold mb-4")

        with ui.row().classes("w-full gap-4"):
            symbol_input = ui.input(
                label="Symbol",
                placeholder="e.g., NSE_EQ|INE002A01018",
            ).classes("flex-1")
            transaction_type = ui.select(
                label="Transaction Type",
                options=["BUY", "SELL"],
                value="BUY",
            ).classes("flex-1")

        with ui.row().classes("w-full gap-4 mt-2"):
            quantity_input = ui.number(
                label="Quantity", value=1, min=1, step=1
            ).classes("flex-1")
            order_type = ui.select(
                label="Order Type",
                options=["MARKET", "LIMIT", "STOP_LOSS_LIMIT", "STOP_LOSS_MARKET"],
                value="MARKET",
            ).classes("flex-1")

        with ui.row().classes("w-full gap-4 mt-2"):
            price_input = ui.number(
                label="Price (for LIMIT orders)", value=0, step=0.05
            ).classes("flex-1")
            trigger_price_input = ui.number(
                label="Trigger Price (for SL orders)", value=0, step=0.05
            ).classes("flex-1")

        order_result_container = ui.column().classes("w-full mt-4")

        async def place_order():
            if not symbol_input.value or not quantity_input.value:
                ui.notify("Please fill all required fields", type="warning")
                return

            # Confirmation dialog
            with ui.dialog() as confirm_dialog, ui.card().classes(
                "bg-slate-800 border border-slate-700"
            ):
                ui.label("⚠️ Confirm Live Order").classes("text-xl font-bold mb-4")

                ui.label(f"Symbol: {symbol_input.value}").classes("text-slate-200")
                ui.label(
                    f"Type: {transaction_type.value} {quantity_input.value} @ {order_type.value}"
                ).classes("text-slate-200")

                if order_type.value == "LIMIT" and price_input.value:
                    ui.label(f"Price: ₹{price_input.value}").classes("text-slate-200")

                if (
                    order_type.value
                    in [
                        "STOP_LOSS_LIMIT",
                        "STOP_LOSS_MARKET",
                    ]
                    and trigger_price_input.value
                ):
                    ui.label(f"Trigger: ₹{trigger_price_input.value}").classes(
                        "text-slate-200"
                    )

                ui.label("This is a REAL order. Are you sure?").classes(
                    "text-yellow-400 font-bold mt-4"
                )

                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=confirm_dialog.close).props("flat")
                    ui.button(
                        "Confirm & Place Order",
                        on_click=lambda: [
                            confirm_dialog.close(),
                            execute_order(),
                        ],
                    ).props("color=negative")

            confirm_dialog.open()

        async def execute_order():
            order_result_container.clear()
            with order_result_container:
                ui.spinner("dots", size="lg").classes("mx-auto text-indigo-500")

            try:
                response = await run.io_bound(
                    requests.post,
                    f"{API_BASE}/order/place",
                    json={
                        "symbol": symbol_input.value,
                        "quantity": int(quantity_input.value),
                        "order_type": order_type.value,
                        "transaction_type": transaction_type.value,
                        "price": (
                            float(price_input.value) if price_input.value else None
                        ),
                        "trigger_price": (
                            float(trigger_price_input.value)
                            if trigger_price_input.value
                            else None
                        ),
                    },
                )

                order_result_container.clear()

                if response.status_code == 200:
                    result = response.json()
                    with order_result_container:
                        with ui.card().classes("bg-green-900 border border-green-500"):
                            ui.label("✅ Order Placed Successfully").classes(
                                "text-xl font-bold text-green-200 mb-2"
                            )
                            ui.label(f"Order ID: {result.get('order_id')}").classes(
                                "text-slate-200 font-mono"
                            )
                            ui.label(f"Status: {result.get('status')}").classes(
                                "text-slate-200"
                            )
                else:
                    with order_result_container:
                        with ui.card().classes("bg-red-900 border border-red-500"):
                            ui.label("❌ Order Failed").classes(
                                "text-xl font-bold text-red-200 mb-2"
                            )
                            ui.label(
                                f"Error: {response.json().get('error', 'Unknown error')}"
                            ).classes("text-red-200")
            except Exception as e:
                order_result_container.clear()
                with order_result_container:
                    with ui.card().classes("bg-red-900 border border-red-500"):
                        ui.label("❌ Error").classes(
                            "text-xl font-bold text-red-200 mb-2"
                        )
                        ui.label(f"Error: {str(e)}").classes("text-red-200")

        ui.button("Place Order", on_click=place_order, icon="send").props(
            "color=negative"
        ).classes("mt-4")

    # Order Status Checker
    with Components.card():
        ui.label("Check Order Status").classes("text-xl font-bold mb-4")

        order_id_input = ui.input(
            label="Order ID", placeholder="Enter order ID"
        ).classes("w-full")

        status_container = ui.column().classes("w-full mt-4")

        async def check_status():
            if not order_id_input.value:
                ui.notify("Please enter an order ID", type="warning")
                return

            status_container.clear()
            with status_container:
                ui.spinner("dots", size="lg").classes("mx-auto text-indigo-500")

            try:
                response = await run.io_bound(
                    requests.get, f"{API_BASE}/order/status/{order_id_input.value}"
                )

                status_container.clear()

                if response.status_code == 200:
                    status = response.json()

                    with status_container:
                        with Components.card():
                            ui.label("Order Status").classes("text-lg font-bold mb-2")

                            with ui.column().classes("gap-2"):
                                for key, value in status.items():
                                    with ui.row().classes("justify-between"):
                                        ui.label(key.replace("_", " ").title()).classes(
                                            "text-slate-400"
                                        )
                                        ui.label(str(value)).classes(
                                            "text-slate-200 font-mono"
                                        )
                else:
                    with status_container:
                        ui.label(
                            f"Error: {response.json().get('error', 'Order not found')}"
                        ).classes("text-red-400")
            except Exception as e:
                status_container.clear()
                with status_container:
                    ui.label(f"Error: {str(e)}").classes("text-red-400")

        ui.button("Check Status", on_click=check_status, icon="search").props(
            "color=primary"
        )

    # Order Management
    with Components.card():
        ui.label("Order Management").classes("text-xl font-bold mb-4")

        manage_order_id = ui.input(
            label="Order ID to Modify/Cancel", placeholder="Enter order ID"
        ).classes("w-full")

        with ui.row().classes("w-full gap-4 mt-4"):
            # Cancel Order
            async def cancel_order():
                if not manage_order_id.value:
                    ui.notify("Please enter an order ID", type="warning")
                    return

                try:
                    response = await run.io_bound(
                        requests.delete,
                        f"{API_BASE}/order/cancel/{manage_order_id.value}",
                    )

                    if response.status_code == 200:
                        ui.notify("Order cancelled successfully", type="positive")
                    else:
                        ui.notify(
                            f"Error: {response.json().get('error', 'Failed to cancel')}",
                            type="negative",
                        )
                except Exception as e:
                    ui.notify(f"Error: {str(e)}", type="negative")

            ui.button("Cancel Order", on_click=cancel_order, icon="cancel").props(
                "color=negative"
            )

            # Modify Order (simplified - opens dialog)
            async def show_modify_dialog():
                if not manage_order_id.value:
                    ui.notify("Please enter an order ID", type="warning")
                    return

                with ui.dialog() as modify_dialog, ui.card().classes(
                    "bg-slate-800 border border-slate-700"
                ):
                    ui.label("Modify Order").classes("text-xl font-bold mb-4")

                    new_quantity = ui.number(label="New Quantity", value=1, min=1)
                    new_price = ui.number(label="New Price", value=0, step=0.05)
                    new_trigger = ui.number(
                        label="New Trigger Price", value=0, step=0.05
                    )

                    async def execute_modify():
                        try:
                            response = await run.io_bound(
                                requests.put,
                                f"{API_BASE}/order/modify/{manage_order_id.value}",
                                json={
                                    "quantity": (
                                        int(new_quantity.value)
                                        if new_quantity.value
                                        else None
                                    ),
                                    "price": (
                                        float(new_price.value)
                                        if new_price.value
                                        else None
                                    ),
                                    "trigger_price": (
                                        float(new_trigger.value)
                                        if new_trigger.value
                                        else None
                                    ),
                                },
                            )

                            if response.status_code == 200:
                                ui.notify(
                                    "Order modified successfully", type="positive"
                                )
                                modify_dialog.close()
                            else:
                                ui.notify(
                                    f"Error: {response.json().get('error', 'Failed to modify')}",
                                    type="negative",
                                )
                        except Exception as e:
                            ui.notify(f"Error: {str(e)}", type="negative")

                    with ui.row().classes("w-full justify-end gap-2 mt-4"):
                        ui.button("Cancel", on_click=modify_dialog.close).props("flat")
                        ui.button("Modify Order", on_click=execute_modify).props(
                            "color=primary"
                        )

                modify_dialog.open()

            ui.button("Modify Order", on_click=show_modify_dialog, icon="edit").props(
                "color=primary"
            )
