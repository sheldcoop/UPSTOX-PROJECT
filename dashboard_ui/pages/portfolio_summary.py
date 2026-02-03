"""
Portfolio Summary Page
Complete overview of holdings, positions, and asset allocation
"""

from nicegui import ui, run
from ..common import Components
from ..state import async_get, API_BASE
import requests


def render_page(state):
    Components.section_header(
        "Portfolio Summary", "Complete portfolio overview and analytics", "pie_chart"
    )

    # Portfolio Summary Stats
    summary_container = ui.row().classes("w-full gap-4 flex-wrap mb-6")

    # Main Content
    content_container = ui.column().classes("w-full gap-4")

    async def load_portfolio_data():
        summary_container.clear()
        content_container.clear()

        with content_container:
            ui.spinner("dots", size="lg").classes("mx-auto")

        try:
            # Fetch portfolio and holdings data
            portfolio_response = await run.io_bound(requests.get, f"{API_BASE}/portfolio")
            holdings_response = await run.io_bound(requests.get, f"{API_BASE}/upstox/holdings")

            if portfolio_response.status_code == 200 and holdings_response.status_code == 200:
                portfolio = portfolio_response.json()
                holdings = holdings_response.json()

                # Summary Stats
                with summary_container:
                    Components.kpi_card(
                        "Total Portfolio Value",
                        portfolio.get("total_value", 0),
                        prefix="₹",
                        delta=1.2
                    )
                    Components.kpi_card(
                        "Total P&L",
                        portfolio.get("total_pnl", 0),
                        prefix="₹",
                        delta=0.8 if portfolio.get("total_pnl", 0) > 0 else -0.8
                    )
                    Components.kpi_card(
                        "Invested Amount",
                        portfolio.get("invested_amount", 0),
                        prefix="₹"
                    )
                    Components.kpi_card(
                        "Total Holdings",
                        len(holdings),
                        suffix=" stocks"
                    )

                # Main Content
                content_container.clear()
                with content_container:
                    # Holdings Table
                    with Components.card():
                        ui.label("Holdings").classes("text-xl font-bold mb-4")

                        if not holdings:
                            ui.label("No holdings found").classes("text-slate-400 italic")
                        else:
                            with ui.element("table").classes("w-full text-sm"):
                                # Header
                                with ui.element("thead").classes("text-slate-400 border-b border-slate-700"):
                                    with ui.element("tr"):
                                        with ui.element("th").classes("pb-3 text-left pl-2"):
                                            ui.label("Symbol")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("Quantity")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("Avg Price")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("LTP")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("Invested")
                                        with ui.element("th").classes("pb-3 text-right"):
                                            ui.label("Current Value")
                                        with ui.element("th").classes("pb-3 text-right pr-2"):
                                            ui.label("P&L")

                                # Body
                                with ui.element("tbody"):
                                    for holding in holdings:
                                        pnl = holding.get("pnl", 0)
                                        pnl_color = "text-green-400" if pnl >= 0 else "text-red-400"

                                        with ui.element("tr").classes("border-b border-slate-800 hover:bg-slate-800/50"):
                                            with ui.element("td").classes("py-3 pl-2"):
                                                ui.label(holding.get("symbol", "")).classes("font-bold text-white")
                                            with ui.element("td").classes("py-3 text-right"):
                                                ui.label(str(holding.get("quantity", 0))).classes("text-slate-300")
                                            with ui.element("td").classes("py-3 text-right"):
                                                ui.label(f"₹{holding.get('avg_price', 0):.2f}").classes("text-slate-300")
                                            with ui.element("td").classes("py-3 text-right"):
                                                ui.label(f"₹{holding.get('ltp', 0):.2f}").classes("text-slate-300")
                                            with ui.element("td").classes("py-3 text-right"):
                                                invested = holding.get("quantity", 0) * holding.get("avg_price", 0)
                                                ui.label(f"₹{invested:,.2f}").classes("text-slate-300")
                                            with ui.element("td").classes("py-3 text-right"):
                                                current_value = holding.get("quantity", 0) * holding.get("ltp", 0)
                                                ui.label(f"₹{current_value:,.2f}").classes("text-white")
                                            with ui.element("td").classes("py-3 text-right pr-2"):
                                                pnl_pct = holding.get("pnl_percent", 0)
                                                with ui.row().classes(f"items-center gap-1 justify-end {pnl_color}"):
                                                    ui.label(f"₹{pnl:.2f}").classes("font-bold")
                                                    ui.label(f"({pnl_pct:+.2f}%)").classes("text-xs")

                    # Two Column Layout
                    with ui.row().classes("w-full gap-4 flex-wrap"):
                        # Current Positions
                        with ui.column().classes("flex-1 min-w-[300px]"):
                            with Components.card():
                                ui.label("Open Positions").classes("text-lg font-bold mb-4")
                                
                                positions = portfolio.get("positions", [])
                                if not positions:
                                    ui.label("No open positions").classes("text-slate-400 italic")
                                else:
                                    for pos in positions[:5]:  # Show top 5
                                        with ui.row().classes("w-full justify-between items-center py-2 border-b border-slate-800"):
                                            ui.label(pos.get("symbol", "")).classes("font-bold text-white")
                                            pnl = pos.get("pnl", 0)
                                            pnl_color = "text-green-400" if pnl >= 0 else "text-red-400"
                                            ui.label(f"₹{pnl:.2f}").classes(f"font-bold {pnl_color}")

                        # Asset Allocation
                        with ui.column().classes("flex-1 min-w-[300px]"):
                            with Components.card():
                                ui.label("Asset Allocation").classes("text-lg font-bold mb-4")
                                
                                allocation = portfolio.get("allocation", {})
                                
                                if not allocation:
                                    ui.label("No allocation data").classes("text-slate-400 italic")
                                else:
                                    for asset_type, percentage in allocation.items():
                                        with ui.row().classes("w-full items-center gap-2 mb-2"):
                                            ui.label(asset_type).classes("text-slate-300 flex-1")
                                            ui.linear_progress(percentage / 100).props("color=indigo").classes("flex-1")
                                            ui.label(f"{percentage:.1f}%").classes("text-white font-bold w-12 text-right")

            else:
                content_container.clear()
                with content_container:
                    with Components.card():
                        ui.label("Error loading portfolio data").classes("text-red-400")
        except Exception as e:
            content_container.clear()
            with content_container:
                with Components.card():
                    ui.label(f"Error: {str(e)}").classes("text-red-400")

    # Refresh Button
    with ui.row().classes("w-full justify-end mb-4"):
        ui.button("Refresh Portfolio", icon="refresh", on_click=load_portfolio_data).props("outline")

    # Initial load
    ui.timer(0.1, load_portfolio_data, once=True)
    
    # Auto-refresh every 60 seconds
    ui.timer(60, load_portfolio_data)
