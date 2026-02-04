"""
Upstox Live Data Page
Real-time data from Upstox API
"""

from nicegui import ui, run
from ..common import Components
import sys
from pathlib import Path
import asyncio
import requests

sys.path.append(str(Path(__file__).parent.parent.parent))

import os
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api"


def render_page(state):
    Components.section_header(
        "Upstox Live", "Real-time data from Upstox API", "cloud_sync"
    )

    # Tabs for different Upstox data
    with ui.tabs().classes("w-full") as tabs:
        holdings_tab = ui.tab("Holdings", icon="account_balance_wallet")
        positions_tab = ui.tab("Positions", icon="trending_up")
        funds_tab = ui.tab("Funds", icon="account_balance")
        data_tab = ui.tab("Market Data", icon="show_chart")

    with ui.tab_panels(tabs, value=holdings_tab).classes("w-full mt-4"):
        # Holdings Panel
        with ui.tab_panel(holdings_tab):
            render_holdings_section()

        # Positions Panel
        with ui.tab_panel(positions_tab):
            render_positions_section()

        # Funds Panel
        with ui.tab_panel(funds_tab):
            render_funds_section()

        # Market Data Panel
        with ui.tab_panel(data_tab):
            render_market_data_section()


def render_holdings_section():
    """Render holdings from Upstox"""
    holdings_container = ui.column().classes("w-full")

    async def load_holdings():
        holdings_container.clear()
        with holdings_container:
            ui.spinner("dots", size="lg").classes("mx-auto text-indigo-500")

        try:
            response = await run.io_bound(requests.get, f"{API_BASE}/upstox/holdings")
            holdings_container.clear()

            if response.status_code == 200:
                holdings = response.json()

                with holdings_container:
                    if not holdings:
                        with Components.card():
                            ui.label("No holdings found").classes(
                                "text-slate-400 italic"
                            )
                    else:
                        with Components.card():
                            ui.label("Your Holdings").classes("text-xl font-bold mb-4")

                            columns = [
                                {
                                    "name": "symbol",
                                    "label": "Symbol",
                                    "field": "symbol",
                                    "align": "left",
                                },
                                {
                                    "name": "quantity",
                                    "label": "Quantity",
                                    "field": "quantity",
                                    "align": "right",
                                },
                                {
                                    "name": "avg_price",
                                    "label": "Avg Price",
                                    "field": "avg_price",
                                    "align": "right",
                                },
                                {
                                    "name": "current_price",
                                    "label": "LTP",
                                    "field": "current_price",
                                    "align": "right",
                                },
                                {
                                    "name": "pnl",
                                    "label": "P&L",
                                    "field": "pnl",
                                    "align": "right",
                                },
                                {
                                    "name": "pnl_percent",
                                    "label": "P&L %",
                                    "field": "pnl_percent",
                                    "align": "right",
                                },
                            ]

                            ui.table(columns=columns, rows=holdings, row_key="symbol")
            else:
                with holdings_container:
                    with Components.card():
                        ui.label(
                            f"Error: {response.json().get('error', 'Failed to load holdings')}"
                        ).classes("text-red-400")
        except Exception as e:
            holdings_container.clear()
            with holdings_container:
                with Components.card():
                    ui.label(f"Error: {str(e)}").classes("text-red-400")

    ui.button("Refresh Holdings", on_click=load_holdings, icon="refresh").props("flat")
    ui.timer(0.1, load_holdings, once=True)


def render_positions_section():
    """Render positions from Upstox"""
    positions_container = ui.column().classes("w-full")

    async def load_positions():
        positions_container.clear()
        with positions_container:
            ui.spinner("dots", size="lg").classes("mx-auto text-indigo-500")

        try:
            response = await run.io_bound(requests.get, f"{API_BASE}/upstox/positions")
            positions_container.clear()

            if response.status_code == 200:
                data = response.json()
                day_positions = data.get("day", [])
                net_positions = data.get("net", [])

                with positions_container:
                    # Day Positions
                    with Components.card():
                        ui.label("Day Positions").classes("text-xl font-bold mb-4")

                        if not day_positions:
                            ui.label("No day positions").classes(
                                "text-slate-400 italic"
                            )
                        else:
                            columns = [
                                {
                                    "name": "symbol",
                                    "label": "Symbol",
                                    "field": "symbol",
                                    "align": "left",
                                },
                                {
                                    "name": "quantity",
                                    "label": "Qty",
                                    "field": "quantity",
                                    "align": "right",
                                },
                                {
                                    "name": "buy_price",
                                    "label": "Buy Price",
                                    "field": "buy_price",
                                    "align": "right",
                                },
                                {
                                    "name": "sell_price",
                                    "label": "Sell Price",
                                    "field": "sell_price",
                                    "align": "right",
                                },
                                {
                                    "name": "pnl",
                                    "label": "P&L",
                                    "field": "pnl",
                                    "align": "right",
                                },
                            ]

                            ui.table(
                                columns=columns, rows=day_positions, row_key="symbol"
                            )

                    # Net Positions
                    with Components.card().classes("mt-4"):
                        ui.label("Net Positions").classes("text-xl font-bold mb-4")

                        if not net_positions:
                            ui.label("No net positions").classes(
                                "text-slate-400 italic"
                            )
                        else:
                            ui.table(
                                columns=columns, rows=net_positions, row_key="symbol"
                            )
            else:
                with positions_container:
                    with Components.card():
                        ui.label(
                            f"Error: {response.json().get('error', 'Failed to load positions')}"
                        ).classes("text-red-400")
        except Exception as e:
            positions_container.clear()
            with positions_container:
                with Components.card():
                    ui.label(f"Error: {str(e)}").classes("text-red-400")

    ui.button("Refresh Positions", on_click=load_positions, icon="refresh").props(
        "flat"
    )
    ui.timer(0.1, load_positions, once=True)


def render_funds_section():
    """Render funds/margin from Upstox"""
    funds_container = ui.column().classes("w-full")

    async def load_funds():
        funds_container.clear()
        with funds_container:
            ui.spinner("dots", size="lg").classes("mx-auto text-indigo-500")

        try:
            response = await run.io_bound(requests.get, f"{API_BASE}/upstox/funds")
            funds_container.clear()

            if response.status_code == 200:
                funds = response.json()

                with funds_container:
                    with Components.card():
                        ui.label("Account Funds & Margin").classes(
                            "text-xl font-bold mb-4"
                        )

                        with ui.grid(columns=3).classes("w-full gap-4"):
                            metrics = [
                                ("Available Margin", funds.get("available_margin", 0)),
                                ("Used Margin", funds.get("used_margin", 0)),
                                ("Total Balance", funds.get("total_balance", 0)),
                                ("Opening Balance", funds.get("opening_balance", 0)),
                                ("Collateral", funds.get("collateral", 0)),
                                ("Withdrawable", funds.get("withdrawable", 0)),
                            ]

                            for label, value in metrics:
                                with ui.column().classes("gap-1"):
                                    ui.label(label).classes(
                                        "text-slate-400 text-xs uppercase"
                                    )
                                    ui.label(f"₹{value:,.2f}").classes(
                                        "text-xl font-mono font-bold text-indigo-400"
                                    )
            else:
                with funds_container:
                    with Components.card():
                        ui.label(
                            f"Error: {response.json().get('error', 'Failed to load funds')}"
                        ).classes("text-red-400")
        except Exception as e:
            funds_container.clear()
            with funds_container:
                with Components.card():
                    ui.label(f"Error: {str(e)}").classes("text-red-400")

    ui.button("Refresh Funds", on_click=load_funds, icon="refresh").props("flat")
    ui.timer(0.1, load_funds, once=True)


def render_market_data_section():
    """Render market data (option chain and quotes)"""
    with Components.card():
        ui.label("Market Quote").classes("text-xl font-bold mb-4")

        symbol_input = ui.input(
            label="Symbol", placeholder="e.g., NSE_EQ|INE009A01021"
        ).classes("w-full mb-4")

        quote_container = ui.column().classes("w-full")

        async def get_quote():
            if not symbol_input.value:
                ui.notify("Please enter a symbol", type="warning")
                return

            quote_container.clear()
            with quote_container:
                ui.spinner("dots", size="lg").classes("mx-auto text-indigo-500")

            try:
                response = await run.io_bound(
                    requests.get,
                    f"{API_BASE}/upstox/market-quote",
                    params={"symbol": symbol_input.value},
                )

                quote_container.clear()

                if response.status_code == 200:
                    quote = response.json()

                    with quote_container:
                        with ui.grid(columns=3).classes("w-full gap-4"):
                            ui.label(f"LTP: ₹{quote.get('ltp', 0):,.2f}").classes(
                                "text-lg font-mono"
                            )
                            ui.label(f"Open: ₹{quote.get('open', 0):,.2f}").classes(
                                "text-lg font-mono"
                            )
                            ui.label(f"Close: ₹{quote.get('close', 0):,.2f}").classes(
                                "text-lg font-mono"
                            )
                            ui.label(f"High: ₹{quote.get('high', 0):,.2f}").classes(
                                "text-lg font-mono"
                            )
                            ui.label(f"Low: ₹{quote.get('low', 0):,.2f}").classes(
                                "text-lg font-mono"
                            )
                            ui.label(f"Volume: {quote.get('volume', 0):,}").classes(
                                "text-lg font-mono"
                            )
                else:
                    with quote_container:
                        ui.label(
                            f"Error: {response.json().get('error', 'Failed to get quote')}"
                        ).classes("text-red-400")
            except Exception as e:
                quote_container.clear()
                with quote_container:
                    ui.label(f"Error: {str(e)}").classes("text-red-400")

        ui.button("Get Quote", on_click=get_quote, icon="search").props("color=primary")
