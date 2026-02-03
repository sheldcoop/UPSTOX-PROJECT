"""
Strategy Builder Page
Build and execute advanced options strategies
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
        "Strategy Builder",
        "Build advanced options strategies",
        "settings_suggest",
    )

    content_container = ui.column().classes("w-full mt-6 gap-6")

    # Available Strategies
    with Components.card():
        ui.label("Available Strategies").classes("text-xl font-bold mb-4")

        strategies_container = ui.column().classes("w-full")

        async def load_available_strategies():
            strategies_container.clear()
            with strategies_container:
                ui.spinner("dots", size="lg").classes("mx-auto text-indigo-500")

            try:
                response = await run.io_bound(
                    requests.get, f"{API_BASE}/strategies/available"
                )

                strategies_container.clear()

                if response.status_code == 200:
                    strategies = response.json()
                    with strategies_container:
                        if not strategies or not strategies.get("strategies"):
                            ui.label("No strategies available").classes(
                                "text-slate-400 italic"
                            )
                        else:
                            for strategy in strategies["strategies"]:
                                with ui.card().classes(
                                    "w-full bg-slate-800 border border-slate-700 p-4"
                                ):
                                    with ui.row().classes(
                                        "w-full justify-between items-center"
                                    ):
                                        with ui.column().classes("gap-1"):
                                            ui.label(strategy["name"]).classes(
                                                "text-lg font-bold"
                                            )
                                            ui.label(strategy["description"]).classes(
                                                "text-sm text-slate-400"
                                            )
                                        ui.button(
                                            "Build",
                                            on_click=lambda s=strategy: build_strategy(
                                                s["id"]
                                            ),
                                            icon="build",
                                        ).props("color=primary")
                else:
                    with strategies_container:
                        ui.label("Error loading strategies").classes("text-red-400")
            except Exception as e:
                strategies_container.clear()
                with strategies_container:
                    ui.label(f"Error: {str(e)}").classes("text-red-400")

        ui.timer(0.1, load_available_strategies, once=True)

    # Strategy Builder Forms
    builder_container = ui.column().classes("w-full")

    def build_strategy(strategy_id):
        """Show strategy builder form"""
        builder_container.clear()

        if strategy_id == "calendar-spread":
            render_calendar_spread_builder(builder_container)
        elif strategy_id == "diagonal-spread":
            render_diagonal_spread_builder(builder_container)
        elif strategy_id == "double-calendar":
            render_double_calendar_builder(builder_container)


def render_calendar_spread_builder(container):
    """Render calendar spread builder"""
    with container:
        with Components.card():
            ui.label("Calendar Spread Builder").classes("text-xl font-bold mb-4")
            ui.label(
                "A calendar spread involves buying and selling options of the same strike but different expiries"
            ).classes("text-sm text-slate-400 mb-4")

            with ui.row().classes("w-full gap-4"):
                symbol_input = ui.input(
                    label="Symbol", placeholder="e.g., NIFTY", value="NIFTY"
                ).classes("flex-1")
                strike_input = ui.number(
                    label="Strike Price", value=18000, step=50
                ).classes("flex-1")

            with ui.row().classes("w-full gap-4 mt-2"):
                near_expiry = ui.input(
                    label="Near Expiry (YYYY-MM-DD)", value="2024-03-28"
                ).classes("flex-1")
                far_expiry = ui.input(
                    label="Far Expiry (YYYY-MM-DD)", value="2024-04-25"
                ).classes("flex-1")

            option_type = ui.select(
                label="Option Type",
                options=["CALL", "PUT"],
                value="CALL",
            ).classes("w-full mt-2")

            result_container = ui.column().classes("w-full mt-4")

            async def execute_calendar_spread():
                result_container.clear()
                with result_container:
                    ui.spinner("dots", size="lg").classes("mx-auto text-indigo-500")

                try:
                    response = await run.io_bound(
                        requests.post,
                        f"{API_BASE}/strategies/calendar-spread",
                        json={
                            "symbol": symbol_input.value,
                            "strike": float(strike_input.value),
                            "near_expiry": near_expiry.value,
                            "far_expiry": far_expiry.value,
                            "option_type": option_type.value,
                        },
                    )

                    result_container.clear()

                    if response.status_code == 200:
                        result = response.json()
                        with result_container:
                            render_strategy_result(result)
                    else:
                        with result_container:
                            ui.label(
                                f"Error: {response.json().get('error', 'Unknown error')}"
                            ).classes("text-red-400")
                except Exception as e:
                    result_container.clear()
                    with result_container:
                        ui.label(f"Error: {str(e)}").classes("text-red-400")

            ui.button(
                "Execute Calendar Spread",
                on_click=execute_calendar_spread,
                icon="play_arrow",
            ).props("color=primary").classes("mt-4")


def render_diagonal_spread_builder(container):
    """Render diagonal spread builder"""
    with container:
        with Components.card():
            ui.label("Diagonal Spread Builder").classes("text-xl font-bold mb-4")
            ui.label("A diagonal spread uses different strikes and expiries").classes(
                "text-sm text-slate-400 mb-4"
            )

            with ui.row().classes("w-full gap-4"):
                symbol_input = ui.input(
                    label="Symbol", placeholder="e.g., NIFTY", value="NIFTY"
                ).classes("flex-1")

            with ui.row().classes("w-full gap-4 mt-2"):
                near_strike = ui.number(
                    label="Near Strike", value=18000, step=50
                ).classes("flex-1")
                far_strike = ui.number(
                    label="Far Strike", value=18100, step=50
                ).classes("flex-1")

            with ui.row().classes("w-full gap-4 mt-2"):
                near_expiry = ui.input(
                    label="Near Expiry (YYYY-MM-DD)", value="2024-03-28"
                ).classes("flex-1")
                far_expiry = ui.input(
                    label="Far Expiry (YYYY-MM-DD)", value="2024-04-25"
                ).classes("flex-1")

            option_type = ui.select(
                label="Option Type",
                options=["CALL", "PUT"],
                value="CALL",
            ).classes("w-full mt-2")

            result_container = ui.column().classes("w-full mt-4")

            async def execute_diagonal_spread():
                result_container.clear()
                with result_container:
                    ui.spinner("dots", size="lg").classes("mx-auto text-indigo-500")

                try:
                    response = await run.io_bound(
                        requests.post,
                        f"{API_BASE}/strategies/diagonal-spread",
                        json={
                            "symbol": symbol_input.value,
                            "near_strike": float(near_strike.value),
                            "far_strike": float(far_strike.value),
                            "near_expiry": near_expiry.value,
                            "far_expiry": far_expiry.value,
                            "option_type": option_type.value,
                        },
                    )

                    result_container.clear()

                    if response.status_code == 200:
                        result = response.json()
                        with result_container:
                            render_strategy_result(result)
                    else:
                        with result_container:
                            ui.label(
                                f"Error: {response.json().get('error', 'Unknown error')}"
                            ).classes("text-red-400")
                except Exception as e:
                    result_container.clear()
                    with result_container:
                        ui.label(f"Error: {str(e)}").classes("text-red-400")

            ui.button(
                "Execute Diagonal Spread",
                on_click=execute_diagonal_spread,
                icon="play_arrow",
            ).props("color=primary").classes("mt-4")


def render_double_calendar_builder(container):
    """Render double calendar spread builder"""
    with container:
        with Components.card():
            ui.label("Double Calendar Spread Builder").classes("text-xl font-bold mb-4")
            ui.label("A double calendar combines two calendar spreads").classes(
                "text-sm text-slate-400 mb-4"
            )

            symbol_input = ui.input(
                label="Symbol", placeholder="e.g., NIFTY", value="NIFTY"
            ).classes("w-full")

            with ui.row().classes("w-full gap-4 mt-2"):
                call_strike = ui.number(
                    label="Call Strike", value=18100, step=50
                ).classes("flex-1")
                put_strike = ui.number(
                    label="Put Strike", value=17900, step=50
                ).classes("flex-1")

            with ui.row().classes("w-full gap-4 mt-2"):
                near_expiry = ui.input(
                    label="Near Expiry (YYYY-MM-DD)", value="2024-03-28"
                ).classes("flex-1")
                far_expiry = ui.input(
                    label="Far Expiry (YYYY-MM-DD)", value="2024-04-25"
                ).classes("flex-1")

            result_container = ui.column().classes("w-full mt-4")

            async def execute_double_calendar():
                result_container.clear()
                with result_container:
                    ui.spinner("dots", size="lg").classes("mx-auto text-indigo-500")

                try:
                    response = await run.io_bound(
                        requests.post,
                        f"{API_BASE}/strategies/double-calendar",
                        json={
                            "symbol": symbol_input.value,
                            "call_strike": float(call_strike.value),
                            "put_strike": float(put_strike.value),
                            "near_expiry": near_expiry.value,
                            "far_expiry": far_expiry.value,
                        },
                    )

                    result_container.clear()

                    if response.status_code == 200:
                        result = response.json()
                        with result_container:
                            render_strategy_result(result)
                    else:
                        with result_container:
                            ui.label(
                                f"Error: {response.json().get('error', 'Unknown error')}"
                            ).classes("text-red-400")
                except Exception as e:
                    result_container.clear()
                    with result_container:
                        ui.label(f"Error: {str(e)}").classes("text-red-400")

            ui.button(
                "Execute Double Calendar",
                on_click=execute_double_calendar,
                icon="play_arrow",
            ).props("color=primary").classes("mt-4")


def render_strategy_result(result):
    """Render strategy execution result"""
    with Components.card():
        ui.label("Strategy Result").classes("text-xl font-bold mb-4")

        if result.get("success"):
            ui.label("✅ Strategy executed successfully").classes(
                "text-green-400 font-bold mb-4"
            )

            # Result details
            with ui.grid(columns=2).classes("w-full gap-4"):
                for key, value in result.items():
                    if key != "success":
                        with ui.column().classes("gap-1"):
                            ui.label(key.replace("_", " ").title()).classes(
                                "text-slate-400 text-xs uppercase"
                            )
                            ui.label(str(value)).classes(
                                "text-lg font-mono text-slate-200"
                            )
        else:
            ui.label("❌ Strategy execution failed").classes(
                "text-red-400 font-bold mb-4"
            )
            ui.label(result.get("error", "Unknown error")).classes("text-slate-300")
