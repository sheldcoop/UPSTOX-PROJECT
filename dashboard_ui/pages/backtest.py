"""
Backtest Results Page
Run backtests and view historical backtest results
"""

from nicegui import ui, run
from ..common import Components
import sys
from pathlib import Path
import asyncio
import requests

sys.path.append(str(Path(__file__).parent.parent.parent))

API_BASE = "http://localhost:8000/api"


def render_page(state):
    Components.section_header(
        "Backtesting", "Test trading strategies on historical data", "science"
    )

    # Tabs for Run Backtest and View Results
    with ui.tabs().classes("w-full") as tabs:
        run_tab = ui.tab("Run Backtest", icon="play_arrow")
        results_tab = ui.tab("Results", icon="assessment")

    with ui.tab_panels(tabs, value=run_tab).classes("w-full mt-4"):
        # Run Backtest Panel
        with ui.tab_panel(run_tab):
            render_run_backtest()

        # Results Panel
        with ui.tab_panel(results_tab):
            render_results()


def render_run_backtest():
    """Render run backtest section"""
    # Strategy Selection
    with Components.card():
        ui.label("Run New Backtest").classes("text-xl font-bold mb-4")

        strategies_container = ui.column().classes("w-full")
        strategy_select = ui.select(
            label="Select Strategy", options=[], value=None
        ).classes("w-full")

        with ui.row().classes("w-full gap-4 mt-4"):
            start_date = ui.input(label="Start Date", value="2023-01-01").classes(
                "flex-1"
            )
            end_date = ui.input(label="End Date", value="2023-12-31").classes("flex-1")

        symbol_input = ui.input(
            label="Symbol (optional)", placeholder="e.g., NIFTY"
        ).classes("w-full mt-2")

        results_container = ui.column().classes("w-full mt-4")

        async def load_strategies():
            try:
                response = await run.io_bound(
                    requests.get, f"{API_BASE}/backtest/strategies"
                )
                if response.status_code == 200:
                    strategies = response.json()
                    strategy_select.options = strategies.get("strategies", [])
                    if strategy_select.options:
                        strategy_select.value = strategy_select.options[0]
            except Exception as e:
                ui.notify(f"Error loading strategies: {str(e)}", type="warning")

        async def run_backtest():
            if not strategy_select.value:
                ui.notify("Please select a strategy", type="warning")
                return

            results_container.clear()
            with results_container:
                ui.spinner("dots", size="lg").classes("mx-auto text-indigo-500")

            try:
                response = await run.io_bound(
                    requests.post,
                    f"{API_BASE}/backtest/run",
                    json={
                        "strategy": strategy_select.value,
                        "start_date": start_date.value,
                        "end_date": end_date.value,
                        "symbol": symbol_input.value if symbol_input.value else None,
                    },
                )

                results_container.clear()

                if response.status_code == 200:
                    results = response.json()
                    with results_container:
                        render_backtest_results(results)
                else:
                    with results_container:
                        ui.label(
                            f"Error: {response.json().get('error', 'Unknown error')}"
                        ).classes("text-red-400")
            except Exception as e:
                results_container.clear()
                with results_container:
                    ui.label(f"Error running backtest: {str(e)}").classes(
                        "text-red-400"
                    )

        ui.button("Run Backtest", on_click=run_backtest, icon="play_arrow").props(
            "color=primary"
        ).classes("mt-4")

        # Load strategies on mount
        ui.timer(0.1, load_strategies, once=True)


def render_backtest_results(results):
    """Render backtest results"""
    with Components.card():
        ui.label("Backtest Results").classes("text-xl font-bold mb-4")

        # Summary Metrics
        with ui.grid(columns=4).classes("w-full gap-4 mb-4"):
            metrics = [
                ("Total Trades", results.get("total_trades", 0), ""),
                ("Win Rate", results.get("win_rate", 0), "%"),
                ("Total P&L", results.get("total_pnl", 0), "₹"),
                ("Sharpe Ratio", results.get("sharpe_ratio", 0), ""),
            ]

            for label, value, unit in metrics:
                with ui.column().classes("gap-1"):
                    ui.label(label).classes("text-slate-400 text-xs uppercase")
                    if unit == "₹":
                        color = "text-green-400" if value >= 0 else "text-red-400"
                        ui.label(f"₹{value:,.2f}").classes(
                            f"text-xl font-mono font-bold {color}"
                        )
                    elif unit == "%":
                        ui.label(f"{value:.1f}%").classes(
                            "text-xl font-mono font-bold text-indigo-400"
                        )
                    else:
                        ui.label(f"{value:,.2f}").classes(
                            "text-xl font-mono font-bold text-cyan-400"
                        )

        # Trades Table
        if results.get("trades"):
            ui.label("Trade Details").classes("text-lg font-bold mt-4 mb-2")
            columns = [
                {"name": "date", "label": "Date", "field": "date", "align": "left"},
                {
                    "name": "symbol",
                    "label": "Symbol",
                    "field": "symbol",
                    "align": "left",
                },
                {"name": "side", "label": "Side", "field": "side", "align": "left"},
                {
                    "name": "quantity",
                    "label": "Qty",
                    "field": "quantity",
                    "align": "right",
                },
                {"name": "price", "label": "Price", "field": "price", "align": "right"},
                {"name": "pnl", "label": "P&L", "field": "pnl", "align": "right"},
            ]
            ui.table(columns=columns, rows=results["trades"], row_key="date")


def render_results():
    """Render historical backtest results"""
    results_container = ui.column().classes("w-full")

    async def load_results():
        results_container.clear()

        with results_container:
            ui.spinner("dots", size="lg").classes("mx-auto text-indigo-500")

        try:
            response = await run.io_bound(requests.get, f"{API_BASE}/backtest/results")
            results_container.clear()

            if response.status_code == 200:
                results_list = response.json()

                with results_container:
                    if not results_list:
                        with Components.card():
                            ui.label("No backtest results yet").classes(
                                "text-slate-400 italic"
                            )
                    else:
                        for result in results_list:
                            with Components.card():
                                with ui.row().classes("w-full justify-between"):
                                    ui.label(
                                        f"{result.get('strategy', 'Unknown')} - {result.get('date', 'N/A')}"
                                    ).classes("text-lg font-bold")
                                    pnl = result.get("total_pnl", 0)
                                    color = (
                                        "text-green-400" if pnl >= 0 else "text-red-400"
                                    )
                                    ui.label(f"₹{pnl:,.2f}").classes(
                                        f"text-xl font-mono font-bold {color}"
                                    )

                                with ui.row().classes("w-full gap-4 mt-2"):
                                    ui.label(
                                        f"Trades: {result.get('total_trades', 0)}"
                                    ).classes("text-sm text-slate-400")
                                    ui.label(
                                        f"Win Rate: {result.get('win_rate', 0):.1f}%"
                                    ).classes("text-sm text-slate-400")
                                    ui.label(
                                        f"Sharpe: {result.get('sharpe_ratio', 0):.2f}"
                                    ).classes("text-sm text-slate-400")
            else:
                with results_container:
                    with Components.card():
                        ui.label("Error loading results").classes("text-red-400")
        except Exception as e:
            results_container.clear()
            with results_container:
                with Components.card():
                    ui.label(f"Error: {str(e)}").classes("text-red-400")

    with ui.row().classes("w-full justify-end mb-4"):
        ui.button("Refresh", on_click=load_results, icon="refresh").props("flat")

    # Initial load
    ui.timer(0.1, load_results, once=True)
