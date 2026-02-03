"""
Funds Management Page
Display available funds and fund transfer interface
"""

from nicegui import ui, run
from ..common import Components
from ..state import async_get, async_post, API_BASE
import requests


def render_page(state):
    Components.section_header(
        "Funds & Limits", "Manage your trading funds and view limits", "account_balance_wallet"
    )

    # Funds Summary
    funds_summary_container = ui.row().classes("w-full gap-4 flex-wrap mb-6")

    # Detailed Breakdown
    funds_detail_container = ui.column().classes("w-full gap-4")

    async def load_funds_data():
        funds_summary_container.clear()
        funds_detail_container.clear()

        with funds_detail_container:
            ui.spinner("dots", size="lg").classes("mx-auto")

        try:
            response = await run.io_bound(requests.get, f"{API_BASE}/upstox/funds")
            if response.status_code == 200:
                funds_data = response.json()

                # Summary Cards
                with funds_summary_container:
                    Components.kpi_card(
                        "Available Balance",
                        funds_data.get("available_balance", 0),
                        prefix="₹",
                        delta=0.5
                    )
                    Components.kpi_card(
                        "Used Margin",
                        funds_data.get("used_margin", 0),
                        prefix="₹",
                        delta=-0.3
                    )
                    Components.kpi_card(
                        "Payin Amount",
                        funds_data.get("payin", 0),
                        prefix="₹"
                    )
                    Components.kpi_card(
                        "Payout Amount",
                        funds_data.get("payout", 0),
                        prefix="₹"
                    )

                # Detailed Funds Breakdown
                funds_detail_container.clear()
                with funds_detail_container:
                    # Equity Segment
                    with Components.card():
                        ui.label("Equity Segment").classes("text-xl font-bold mb-4 text-indigo-400")
                        
                        equity = funds_data.get("equity", {})
                        
                        with ui.grid(columns=3).classes("w-full gap-4"):
                            # Available Cash
                            with ui.column().classes("gap-1"):
                                ui.label("Available Cash").classes("text-xs text-slate-400 uppercase")
                                ui.label(f"₹{equity.get('available_cash', 0):,.2f}").classes(
                                    "text-xl font-bold text-green-400"
                                )

                            # Collateral
                            with ui.column().classes("gap-1"):
                                ui.label("Collateral").classes("text-xs text-slate-400 uppercase")
                                ui.label(f"₹{equity.get('collateral', 0):,.2f}").classes(
                                    "text-xl font-bold text-white"
                                )

                            # Used Margin
                            with ui.column().classes("gap-1"):
                                ui.label("Used Margin").classes("text-xs text-slate-400 uppercase")
                                ui.label(f"₹{equity.get('used_margin', 0):,.2f}").classes(
                                    "text-xl font-bold text-red-400"
                                )

                    # Commodity Segment
                    with Components.card():
                        ui.label("Commodity Segment").classes("text-xl font-bold mb-4 text-orange-400")
                        
                        commodity = funds_data.get("commodity", {})
                        
                        with ui.grid(columns=3).classes("w-full gap-4"):
                            # Available Cash
                            with ui.column().classes("gap-1"):
                                ui.label("Available Cash").classes("text-xs text-slate-400 uppercase")
                                ui.label(f"₹{commodity.get('available_cash', 0):,.2f}").classes(
                                    "text-xl font-bold text-green-400"
                                )

                            # Collateral
                            with ui.column().classes("gap-1"):
                                ui.label("Collateral").classes("text-xs text-slate-400 uppercase")
                                ui.label(f"₹{commodity.get('collateral', 0):,.2f}").classes(
                                    "text-xl font-bold text-white"
                                )

                            # Used Margin
                            with ui.column().classes("gap-1"):
                                ui.label("Used Margin").classes("text-xs text-slate-400 uppercase")
                                ui.label(f"₹{commodity.get('used_margin', 0):,.2f}").classes(
                                    "text-xl font-bold text-red-400"
                                )

                    # Margin Summary Table
                    with Components.card():
                        ui.label("Margin Breakdown").classes("text-xl font-bold mb-4")

                        margin_breakdown = funds_data.get("margin_breakdown", [])
                        
                        if not margin_breakdown:
                            ui.label("No margin details available").classes("text-slate-400 italic")
                        else:
                            with ui.element("table").classes("w-full text-sm"):
                                # Header
                                with ui.element("thead").classes("text-slate-400 border-b border-slate-700"):
                                    with ui.element("tr"):
                                        with ui.element("th").classes("pb-3 text-left pl-2"):
                                            ui.label("Category")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("Amount")
                                        with ui.element("th").classes("pb-3 text-right pr-2"):
                                            ui.label("Percentage")

                                # Body
                                with ui.element("tbody"):
                                    for item in margin_breakdown:
                                        with ui.element("tr").classes("border-b border-slate-800"):
                                            with ui.element("td").classes("py-3 pl-2"):
                                                ui.label(item.get("category", "")).classes("text-white")
                                            with ui.element("td").classes("py-3 text-right"):
                                                ui.label(f"₹{item.get('amount', 0):,.2f}").classes("text-slate-300")
                                            with ui.element("td").classes("py-3 text-right pr-2"):
                                                ui.label(f"{item.get('percentage', 0):.2f}%").classes("text-slate-400")

            else:
                funds_detail_container.clear()
                with funds_detail_container:
                    with Components.card():
                        ui.label(f"Error loading funds data: {response.status_code}").classes("text-red-400")
        except Exception as e:
            funds_detail_container.clear()
            with funds_detail_container:
                with Components.card():
                    ui.label(f"Error: {str(e)}").classes("text-red-400")

    # Refresh Button (Top Right)
    with ui.row().classes("w-full justify-end mb-4"):
        ui.button("Refresh Funds", icon="refresh", on_click=load_funds_data).props("outline")

    # Initial load
    ui.timer(0.1, load_funds_data, once=True)
    
    # Auto-refresh every 30 seconds
    ui.timer(30, load_funds_data)
