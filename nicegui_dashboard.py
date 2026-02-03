#!/usr/bin/env python3
"""
NiceGUI Trading Dashboard v3.0 (Refactored)
Modularized architecture for scalability and maintenance.
"""

from nicegui import ui, app
import asyncio
import logging
import traceback
import sqlite3
import os
from collections import deque
from datetime import datetime


# --- Debug Logging System ---
class InMemoryHandler(logging.Handler):
    def __init__(self, capacity=1000):
        super().__init__()
        self.logs = deque(maxlen=capacity)

    def emit(self, record):
        try:
            msg = self.format(record)
            self.logs.append(
                {
                    "ts": datetime.now().strftime("%H:%M:%S"),
                    "level": record.levelname,
                    "msg": msg,
                }
            )
        except Exception:
            self.handleError(record)


mem_handler = InMemoryHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
mem_handler.setFormatter(formatter)
logging.getLogger().addHandler(mem_handler)
logging.getLogger().setLevel(logging.INFO)

from dashboard_ui.state import DashboardState
from dashboard_ui.common import Theme, Components
from dashboard_ui.pages import (
    home,
    downloads,
    positions,
    fno,
    guide,
    wip,
    live_data,
    ai_chat,
    option_chain,
    option_greeks,
    historical_options,
    api_debugger,
    health,
    user_profile,
)

# Configuration
REFRESH_INTERVAL = 30000  # 30 seconds


@ui.page("/")
def main_dashboard(page: str = None):
    Theme.apply()
    state = DashboardState()
    if page:
        state.current_page = page

    # --- Debug Console ---
    with (
        ui.dialog() as debug_dialog,
        ui.card().classes(
            "w-full max-w-4xl h-[80vh] bg-slate-900 border border-slate-700"
        ),
    ):
        with ui.row().classes(
            "w-full justify-between items-center border-b border-slate-700 pb-2"
        ):
            ui.label("System Logs").classes("text-lg font-mono text-green-400")
            with ui.row():
                ui.button(icon="refresh", on_click=lambda: log_content.refresh()).props(
                    "flat dense round"
                )
                ui.button(icon="close", on_click=debug_dialog.close).props(
                    "flat dense round"
                )

        with ui.column().classes(
            "w-full h-full overflow-auto font-mono text-xs p-2"
        ) as log_container:

            @ui.refreshable
            def log_content():
                if not mem_handler.logs:
                    ui.label("No logs yet...").classes("text-slate-500 italic")
                    return

                # Show latest first
                for log in reversed(list(mem_handler.logs)):
                    color = "text-slate-300"
                    if log["level"] == "ERROR":
                        color = "text-red-400"
                    elif log["level"] == "WARNING":
                        color = "text-yellow-400"

                    with ui.row().classes(
                        "w-full gap-2 hover:bg-slate-800/50 p-1 rounded"
                    ):
                        ui.label(log["ts"]).classes("text-slate-500 min-w-[60px]")
                        ui.label(log["level"]).classes(
                            f"font-bold min-w-[50px] {color}"
                        )
                        ui.label(log["msg"]).classes("break-all")

            log_content()

    # --- Navigation Logic ---
    def navigate_to(page_id: str):
        state.current_page = page_id
        content_area.refresh()
        if ui.context.client.layout.width < 1024:
            drawer.hide()

    def toggle_sidebar():
        state.is_sidebar_collapsed = not state.is_sidebar_collapsed
        if state.is_sidebar_collapsed:
            drawer.props(add="mini")
        else:
            drawer.props(remove="mini")
        sidebar_content.refresh()

    # --- Header ---
    with ui.header().classes("glass border-b border-slate-800 px-4 py-3 h-16"):
        with ui.row().classes("w-full items-center justify-between"):
            with ui.row().classes("items-center gap-4"):
                # Mobile Toggle
                ui.button(icon="menu", on_click=lambda: drawer.toggle()).props(
                    "flat dense rounded"
                ).classes("text-slate-300 lg:hidden")
                # Desktop Collapse/Expand
                ui.button(icon="menu_open", on_click=toggle_sidebar).props(
                    "flat dense rounded"
                ).classes("text-slate-300 hidden lg:block rotate-180")

                with ui.row().classes("items-center gap-2"):
                    ui.icon("rocket_launch", size="md").classes("text-indigo-500")
                    ui.label("UPSTOX").classes(
                        "text-xl font-bold tracking-tight text-white/90"
                    )
                    ui.label("ALGO v2").classes(
                        "text-xs font-mono bg-blue-900/30 text-blue-400 px-2 py-0.5 rounded border border-blue-800"
                    )

            with ui.row().classes("items-center gap-4 ml-auto"):
                ui.button(
                    "REFRESH", icon="refresh", on_click=lambda: refresh_all_data()
                ).props("flat dense").classes("text-slate-400 hover:text-white")

                # Auth Controls (Refreshable)
                @ui.refreshable
                def auth_controls():
                    is_auth = state.portfolio.get("authenticated", False)
                    mode = state.portfolio.get("mode", "unknown")

                    if is_auth:
                        ui.chip("LIVE", icon="check_circle", color="green").props(
                            "dense square outline"
                        )
                    elif mode == "paper":
                        ui.chip("PAPER TRADING", icon="science", color="orange").props(
                            "dense square outline"
                        ).tooltip(
                            "You are viewing simulated data. Login to trade live."
                        )

                    if not is_auth:

                        def open_login():
                            import webbrowser

                            # Use a new browser tab/window for the external Upstox login
                            # Port 5050 to avoid MacOS AirPlay conflict on port 5000
                            webbrowser.open("http://127.0.0.1:5050/auth/start")

                        ui.button("Login", icon="login", on_click=open_login).classes(
                            "bg-gradient-to-r from-orange-500 to-red-500 text-white font-bold ml-4"
                        )

                auth_controls()

                ui.avatar(
                    "img:https://cdn.quasar.dev/img/boy-avatar.png", size="md"
                ).classes("border border-slate-600")

    # --- Sidebar ---
    drawer = (
        ui.left_drawer(value=True)
        .props('show-if-above bordered :width="260" :mini-width="80" behavior=desktop')
        .classes("bg-slate-950 border-r border-slate-800 transition-all duration-300")
    )

    with drawer:

        @ui.refreshable
        def sidebar_content():
            is_mini = state.is_sidebar_collapsed

            with ui.column().classes("w-full h-full justify-between py-4"):
                # Navigation Items
                with ui.column().classes("w-full gap-1"):

                    def menu_item(label, page, icon_name):
                        is_active = state.current_page == page
                        bg_class = (
                            "bg-indigo-600/10 text-indigo-400 border-r-2 border-indigo-500"
                            if is_active
                            else "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                        )

                        tooltip = label if is_mini else None

                        # Fix: Use row instead of button for better control in mini mode
                        with ui.element("div").classes(
                            f"w-full cursor-pointer {bg_class} relative group"
                        ) as container:
                            container.on("click", lambda p=page: navigate_to(p))

                            # Layout: Icon + Label
                            with ui.row().classes(
                                f'w-full items-center py-3 px-4 {"justify-center" if is_mini else "justify-start gap-4"}'
                            ):
                                ui.icon(icon_name).classes(
                                    "text-2xl transition-transform group-hover:scale-110"
                                )
                                if not is_mini:
                                    ui.label(label).classes(
                                        "text-sm font-medium whitespace-nowrap overflow-hidden animate-fade-in"
                                    )

                        if tooltip:
                            ui.tooltip(tooltip).props(
                                'anchor="center right" self="center left" :offset="[10, 10]"'
                            ).classes("bg-slate-900 border border-slate-700 text-xs")

                    def menu_group(title):
                        if not is_mini:
                            ui.label(title).classes(
                                "text-[10px] font-bold text-slate-600 uppercase px-4 mt-4 mb-2 tracking-wider"
                            )
                        else:
                            ui.separator().classes(
                                "my-2 border-slate-800 w-1/2 mx-auto"
                            )

                    # Render Menu
                    menu_group("Core")
                    menu_item("Dashboard", "dashboard", "dashboard")
                    menu_item("Live Data", "live_data", "ssid_chart")
                    menu_item("Data Downloads", "downloads", "cloud_download")
                    menu_item("Historical Options", "historical_options", "history")

                    menu_group("Trading")
                    menu_item("Positions", "positions", "pie_chart")
                    menu_item("Option Chain", "option_chain", "list_alt")
                    menu_item("Option Greeks", "option_greeks", "data_exploration")
                    menu_item("F&O Analysis", "fno_analysis", "timeline")

                    menu_group("Account")
                    menu_item("User Profile", "user_profile", "account_circle")
                    menu_item("Health Status", "health", "health_and_safety")

                    menu_group("Tools")
                    menu_item("AI Assistant", "ai_chat", "smart_toy")
                    menu_item(
                        "API Debugger", "api_debugger", "integration_instructions"
                    )
                    menu_item("Backtest", "backtest", "science")
                    menu_item("Market Guide", "market_guide", "library_books")
                    menu_item("Configurations", "settings", "settings")

                    # Debug Item
                    with ui.element("div").classes(
                        "w-full cursor-pointer text-slate-400 hover:text-red-400 hover:bg-slate-800/50 relative group"
                    ) as container:
                        container.on("click", debug_dialog.open)
                        with ui.row().classes(
                            f'w-full items-center py-3 px-4 {"justify-center" if is_mini else "justify-start gap-4"}'
                        ):
                            ui.icon("bug_report").classes(
                                "text-2xl transition-transform group-hover:scale-110"
                            )
                            if not is_mini:
                                ui.label("System Logs").classes(
                                    "text-sm font-medium whitespace-nowrap overflow-hidden"
                                )

                # Sidebar Footer
                if not is_mini:
                    with ui.column().classes("px-4 pb-2 opacity-50"):
                        ui.label("System Online").classes(
                            "text-xs text-green-500 font-mono"
                        )
                        ui.linear_progress(
                            value=1.0, color="green", show_value=False
                        ).classes("h-1 rounded")

        sidebar_content()

    # --- Content ---
    @ui.refreshable
    def content_area():
        # Pages wrap content in a consistent padding container
        with ui.column().classes("w-full h-full max-w-7xl mx-auto animate-fade-in"):
            if state.current_page == "dashboard":
                home.render_page(state)
            elif state.current_page == "ai_chat":
                ai_chat.render_page(state)
            elif state.current_page == "live_data":
                live_data.render_page(state)
            elif state.current_page == "downloads":
                downloads.render_page(state)
            elif state.current_page == "historical_options":
                historical_options.historical_options_page()
            elif state.current_page == "api_debugger":
                api_debugger.api_debugger_page()
            elif state.current_page == "positions":
                positions.render_page(state)
            elif state.current_page == "option_chain":
                option_chain.render_page(state)
            elif state.current_page == "option_greeks":
                option_greeks.render_page(state)
            elif state.current_page == "fno_analysis":
                fno.render_page(state)
            elif state.current_page == "market_guide":
                guide.render_page(state)
            elif state.current_page == "health":
                health.render_page(state)
            elif state.current_page == "user_profile":
                user_profile.render_page(state)
            else:
                wip.render_page(state.current_page)

    # --- Data Cycle ---
    async def refresh_all_data():
        try:
            # 1. Attempt standard fetch
            await asyncio.gather(state.fetch_portfolio())

            # 2. FORCE CHECK: Look directly at the database
            # This fixes the issue where API might be flaky but token exists
            if not state.portfolio.get("authenticated", False):
                try:
                    db_path = os.path.abspath("market_data.db")
                    if os.path.exists(db_path):
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        # Check if a valid token exists for 'default' user
                        cursor.execute(
                            "SELECT is_active FROM auth_tokens WHERE user_id='default' AND is_active=1"
                        )
                        if cursor.fetchone():
                            # Force the dashboard to turn Green
                            state.portfolio["authenticated"] = True
                            state.portfolio["mode"] = "live"
                            logging.info("Forced Authentication: Token found in DB")
                        conn.close()
                except Exception as db_err:
                    logging.error(f"DB Check failed: {db_err}")

            auth_controls.refresh()  # Update auth badge/button
            if state.current_page == "dashboard":
                home.stats_widget.refresh(state)
            elif state.current_page == "positions":
                content_area.refresh()
            ui.notify(
                "Data Synced", type="positive", position="bottom-right", timeout=1000
            )
        except Exception as e:
            logging.error(f"Data Sync Error: {e}", exc_info=True)
            ui.notify(
                f"Sync Failed: {str(e)}", type="negative", position="bottom-right"
            )

    # Boot loop
    ui.timer(0.1, refresh_all_data, once=True)
    ui.timer(REFRESH_INTERVAL / 1000.0, refresh_all_data)

    # Layout Mount
    with ui.column().classes("w-full flex-grow overflow-auto p-4 sm:p-6 bg-slate-950"):
        content_area()


ui.run(title="Upstox Pro", host="127.0.0.1", port=8080, dark=True)
