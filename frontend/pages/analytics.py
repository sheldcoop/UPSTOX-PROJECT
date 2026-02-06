"""
Analytics Dashboard Page
Shows performance metrics, equity curve, and trading analytics
"""

from nicegui import ui, run
from ..common import Components
import sys
from pathlib import Path
import asyncio
import requests
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))

import os
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000") + "/api"


def render_page(state):
    Components.section_header(
        "Analytics Dashboard",
        "Performance metrics & trading analytics",
        "analytics",
    )

    content_container = ui.column().classes("w-full mt-6 gap-6")

    async def load_analytics():
        content_container.clear()

        with content_container:
            ui.spinner("dots", size="lg").classes("mx-auto text-indigo-500")

        try:
            # Load all analytics data in parallel
            performance_response = await run.io_bound(
                requests.get, f"{API_BASE}/performance"
            )
            full_analytics_response = await run.io_bound(
                requests.get, f"{API_BASE}/analytics/performance"
            )
            equity_curve_response = await run.io_bound(
                requests.get, f"{API_BASE}/analytics/equity-curve"
            )

            content_container.clear()

            with content_container:
                # Performance Summary Card
                if performance_response.status_code == 200:
                    perf = performance_response.json()
                    render_performance_summary(perf)
                else:
                    with Components.card():
                        ui.label("Unable to load performance data").classes(
                            "text-red-400"
                        )

                # Full Analytics Card
                if full_analytics_response.status_code == 200:
                    analytics = full_analytics_response.json()
                    render_full_analytics(analytics)
                else:
                    with Components.card():
                        ui.label("Unable to load analytics data").classes(
                            "text-red-400"
                        )

                # Equity Curve Chart
                if equity_curve_response.status_code == 200:
                    equity_data = equity_curve_response.json()
                    render_equity_curve(equity_data)
                else:
                    with Components.card():
                        ui.label("Unable to load equity curve data").classes(
                            "text-red-400"
                        )

        except Exception as e:
            content_container.clear()
            with content_container:
                with Components.card():
                    ui.label(f"Error loading analytics: {str(e)}").classes(
                        "text-red-400"
                    )

    def render_performance_summary(perf):
        """Render 30-day performance summary"""
        with Components.card():
            ui.label("30-Day Performance Summary").classes("text-2xl font-bold mb-4")

            # Metrics Grid
            with ui.grid(columns=4).classes("w-full gap-4"):
                # Total P&L
                total_pnl = perf.get("total_pnl", 0)
                pnl_color = "text-green-400" if total_pnl >= 0 else "text-red-400"
                with ui.column().classes("gap-1"):
                    ui.label("Total P&L").classes("text-slate-400 text-xs uppercase")
                    ui.label(f"₹{total_pnl:,.2f}").classes(
                        f"text-2xl font-mono font-bold {pnl_color}"
                    )

                # Win Rate
                win_rate = perf.get("win_rate", 0)
                with ui.column().classes("gap-1"):
                    ui.label("Win Rate").classes("text-slate-400 text-xs uppercase")
                    ui.label(f"{win_rate:.1f}%").classes(
                        "text-2xl font-mono font-bold text-indigo-400"
                    )

                # Total Trades
                total_trades = perf.get("total_trades", 0)
                with ui.column().classes("gap-1"):
                    ui.label("Total Trades").classes("text-slate-400 text-xs uppercase")
                    ui.label(f"{total_trades:,}").classes(
                        "text-2xl font-mono font-bold text-cyan-400"
                    )

                # Average P&L per Trade
                avg_pnl = perf.get("avg_pnl_per_trade", 0)
                avg_color = "text-green-400" if avg_pnl >= 0 else "text-red-400"
                with ui.column().classes("gap-1"):
                    ui.label("Avg P&L/Trade").classes(
                        "text-slate-400 text-xs uppercase"
                    )
                    ui.label(f"₹{avg_pnl:,.2f}").classes(
                        f"text-2xl font-mono font-bold {avg_color}"
                    )

    def render_full_analytics(analytics):
        """Render full analytics metrics"""
        with Components.card():
            ui.label("Detailed Analytics").classes("text-2xl font-bold mb-4")

            # Two-column layout for metrics
            with ui.row().classes("w-full gap-6"):
                # Left Column - Risk Metrics
                with ui.column().classes("flex-1 gap-3"):
                    ui.label("Risk Metrics").classes("text-lg font-bold mb-2")

                    metrics = [
                        ("Sharpe Ratio", analytics.get("sharpe_ratio", 0), "N/A"),
                        ("Sortino Ratio", analytics.get("sortino_ratio", 0), "N/A"),
                        ("Max Drawdown", analytics.get("max_drawdown", 0), "%"),
                        (
                            "Value at Risk (95%)",
                            analytics.get("var_95", 0),
                            "₹",
                        ),
                    ]

                    for label, value, unit in metrics:
                        with ui.row().classes("justify-between items-center"):
                            ui.label(label).classes("text-slate-300")
                            if value == 0 and unit == "N/A":
                                ui.label("N/A").classes("text-slate-500 font-mono")
                            elif unit == "%":
                                ui.label(f"{value:.2f}%").classes(
                                    "text-slate-200 font-mono"
                                )
                            elif unit == "₹":
                                ui.label(f"₹{value:,.2f}").classes(
                                    "text-slate-200 font-mono"
                                )
                            else:
                                ui.label(f"{value:.2f}").classes(
                                    "text-slate-200 font-mono"
                                )

                # Right Column - Trade Metrics
                with ui.column().classes("flex-1 gap-3"):
                    ui.label("Trade Metrics").classes("text-lg font-bold mb-2")

                    metrics = [
                        ("Winning Trades", analytics.get("winning_trades", 0), ""),
                        ("Losing Trades", analytics.get("losing_trades", 0), ""),
                        (
                            "Largest Win",
                            analytics.get("largest_win", 0),
                            "₹",
                        ),
                        (
                            "Largest Loss",
                            analytics.get("largest_loss", 0),
                            "₹",
                        ),
                    ]

                    for label, value, unit in metrics:
                        with ui.row().classes("justify-between items-center"):
                            ui.label(label).classes("text-slate-300")
                            if unit == "₹":
                                ui.label(f"₹{abs(value):,.2f}").classes(
                                    "text-slate-200 font-mono"
                                )
                            else:
                                ui.label(f"{value:,}").classes(
                                    "text-slate-200 font-mono"
                                )

    def render_equity_curve(equity_data):
        """Render equity curve chart"""
        with Components.card():
            ui.label("Equity Curve").classes("text-2xl font-bold mb-4")

            if not equity_data or not isinstance(equity_data, list):
                ui.label("No equity curve data available").classes(
                    "text-slate-400 italic"
                )
                return

            # Prepare chart data
            dates = [point.get("date", "") for point in equity_data]
            equity = [point.get("equity", 0) for point in equity_data]

            # Create line chart using ECharts
            chart_options = {
                "backgroundColor": "transparent",
                "grid": {"left": "10%", "right": "5%", "top": "10%", "bottom": "15%"},
                "xAxis": {
                    "type": "category",
                    "data": dates,
                    "axisLabel": {"color": "#94a3b8"},
                    "axisLine": {"lineStyle": {"color": "#334155"}},
                },
                "yAxis": {
                    "type": "value",
                    "axisLabel": {"color": "#94a3b8", "formatter": "₹{value}"},
                    "axisLine": {"lineStyle": {"color": "#334155"}},
                    "splitLine": {"lineStyle": {"color": "#1e293b"}},
                },
                "series": [
                    {
                        "data": equity,
                        "type": "line",
                        "smooth": True,
                        "lineStyle": {"color": "#6366f1", "width": 2},
                        "areaStyle": {
                            "color": {
                                "type": "linear",
                                "x": 0,
                                "y": 0,
                                "x2": 0,
                                "y2": 1,
                                "colorStops": [
                                    {"offset": 0, "color": "rgba(99, 102, 241, 0.3)"},
                                    {"offset": 1, "color": "rgba(99, 102, 241, 0)"},
                                ],
                            }
                        },
                    }
                ],
                "tooltip": {
                    "trigger": "axis",
                    "backgroundColor": "#1e293b",
                    "borderColor": "#334155",
                    "textStyle": {"color": "#e2e8f0"},
                    "formatter": "{b}<br/>Equity: ₹{c}",
                },
            }

            ui.echart(chart_options).classes("w-full h-96")

    # Refresh button
    with ui.row().classes("w-full justify-end mb-4"):
        ui.button("Refresh Analytics", on_click=load_analytics, icon="refresh").props(
            "color=primary"
        )

    # Initial load
    ui.timer(0.1, load_analytics, once=True)
