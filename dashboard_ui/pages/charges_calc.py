"""
Brokerage & Charges Calculator Page
Calculate brokerage and all applicable charges for orders
"""

from nicegui import ui, run
from ..common import Components
from ..state import async_post, API_BASE
import requests


def render_page(state):
    Components.section_header(
        "Charges Calculator", "Calculate brokerage and transaction charges", "calculate"
    )

    # Calculator Form
    with Components.card():
        ui.label("Calculate Charges").classes("text-xl font-bold mb-4")

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
                options=["DELIVERY", "INTRADAY"],
                value="INTRADAY"
            ).classes("flex-1")

        with ui.row().classes("w-full gap-4"):
            quantity_input = ui.number(label="Quantity", value=1, min=1, step=1).classes("flex-1")
            price_input = ui.number(label="Price per Unit", value=0, step=0.05).classes("flex-1")

        charges_result_container = ui.column().classes("w-full mt-6")

        async def calculate_charges():
            if not symbol_input.value or not price_input.value:
                ui.notify("Please enter symbol and price", type="warning")
                return

            charges_result_container.clear()
            with charges_result_container:
                ui.spinner("dots").classes("mx-auto")

            try:
                response = await run.io_bound(
                    requests.post,
                    f"{API_BASE}/charges/brokerage",
                    json={
                        "symbol": symbol_input.value.upper(),
                        "exchange": exchange_select.value,
                        "transaction_type": transaction_type.value,
                        "product_type": product_type.value,
                        "quantity": int(quantity_input.value),
                        "price": float(price_input.value)
                    }
                )

                charges_result_container.clear()
                
                if response.status_code == 200:
                    charges_data = response.json()
                    
                    with charges_result_container:
                        # Summary Card
                        with ui.card().classes("w-full bg-gradient-to-br from-indigo-900/50 to-purple-900/50 border border-indigo-500/50"):
                            ui.label("Charges Breakdown").classes("text-2xl font-bold mb-6 text-white")
                            
                            # Order Value
                            order_value = charges_data.get("order_value", 0)
                            with ui.row().classes("w-full justify-between items-center mb-4 pb-4 border-b border-slate-700"):
                                ui.label("Order Value").classes("text-lg text-slate-300")
                                ui.label(f"₹{order_value:,.2f}").classes("text-2xl font-bold text-white")

                            # Individual Charges
                            with ui.column().classes("w-full gap-3 mb-4"):
                                # Brokerage
                                brokerage = charges_data.get("brokerage", 0)
                                with ui.row().classes("w-full justify-between"):
                                    ui.label("Brokerage").classes("text-slate-400")
                                    ui.label(f"₹{brokerage:.2f}").classes("text-slate-200")

                                # STT/CTT
                                stt = charges_data.get("stt", 0)
                                with ui.row().classes("w-full justify-between"):
                                    ui.label("STT/CTT").classes("text-slate-400")
                                    ui.label(f"₹{stt:.2f}").classes("text-slate-200")

                                # Exchange Transaction Charge
                                exchange_charge = charges_data.get("exchange_charge", 0)
                                with ui.row().classes("w-full justify-between"):
                                    ui.label("Exchange Transaction Charge").classes("text-slate-400")
                                    ui.label(f"₹{exchange_charge:.2f}").classes("text-slate-200")

                                # GST
                                gst = charges_data.get("gst", 0)
                                with ui.row().classes("w-full justify-between"):
                                    ui.label("GST (18%)").classes("text-slate-400")
                                    ui.label(f"₹{gst:.2f}").classes("text-slate-200")

                                # SEBI Charges
                                sebi_charges = charges_data.get("sebi_charges", 0)
                                with ui.row().classes("w-full justify-between"):
                                    ui.label("SEBI Charges").classes("text-slate-400")
                                    ui.label(f"₹{sebi_charges:.2f}").classes("text-slate-200")

                                # Stamp Duty
                                stamp_duty = charges_data.get("stamp_duty", 0)
                                with ui.row().classes("w-full justify-between"):
                                    ui.label("Stamp Duty").classes("text-slate-400")
                                    ui.label(f"₹{stamp_duty:.2f}").classes("text-slate-200")

                            # Total Charges
                            total_charges = charges_data.get("total_charges", 0)
                            with ui.row().classes("w-full justify-between items-center pt-4 border-t border-indigo-500/50"):
                                ui.label("Total Charges").classes("text-xl font-bold text-indigo-400")
                                ui.label(f"₹{total_charges:.2f}").classes("text-2xl font-bold text-red-400")

                            # Net Amount
                            net_amount = charges_data.get("net_amount", 0)
                            with ui.row().classes("w-full justify-between items-center mt-2"):
                                ui.label("Net Amount").classes("text-xl font-bold text-slate-300")
                                ui.label(f"₹{net_amount:,.2f}").classes("text-2xl font-bold text-white")

                        # Info Cards
                        with ui.row().classes("w-full gap-4 mt-4 flex-wrap"):
                            # Break-even
                            with Components.card().classes("flex-1 min-w-[200px]"):
                                ui.label("Break-even Price").classes("text-xs text-slate-400 uppercase mb-2")
                                breakeven = charges_data.get("breakeven_price", 0)
                                ui.label(f"₹{breakeven:.2f}").classes("text-xl font-bold text-yellow-400")
                                ui.label("Price needed to break even").classes("text-xs text-slate-500 mt-1")

                            # Effective Rate
                            with Components.card().classes("flex-1 min-w-[200px]"):
                                ui.label("Effective Rate").classes("text-xs text-slate-400 uppercase mb-2")
                                effective_rate = (total_charges / order_value * 100) if order_value > 0 else 0
                                ui.label(f"{effective_rate:.4f}%").classes("text-xl font-bold text-orange-400")
                                ui.label("% of order value").classes("text-xs text-slate-500 mt-1")

                else:
                    with charges_result_container:
                        ui.label(f"Error calculating charges: {response.json().get('error', 'Unknown error')}").classes(
                            "text-red-400"
                        )
            except Exception as e:
                charges_result_container.clear()
                with charges_result_container:
                    ui.label(f"Error: {str(e)}").classes("text-red-400")

        ui.button("Calculate Charges", on_click=calculate_charges, icon="calculate").props(
            "color=primary size=lg"
        ).classes("mt-4")

    # Information Section
    with Components.card().classes("mt-6"):
        with ui.expansion("Understanding Charges", icon="info").classes("w-full"):
            with ui.column().classes("gap-2 p-2"):
                ui.label("Brokerage: Commission charged by the broker for executing trades").classes("text-sm text-slate-400")
                ui.label("STT/CTT: Securities/Commodities Transaction Tax levied by the government").classes("text-sm text-slate-400")
                ui.label("Exchange Charge: Fee charged by the stock exchange").classes("text-sm text-slate-400")
                ui.label("GST: 18% Goods and Services Tax on brokerage and transaction charges").classes("text-sm text-slate-400")
                ui.label("SEBI Charges: Regulatory fee charged by SEBI").classes("text-sm text-slate-400")
                ui.label("Stamp Duty: State government tax on transfer of securities").classes("text-sm text-slate-400")
