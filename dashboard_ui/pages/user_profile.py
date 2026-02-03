from nicegui import ui
from ..common import Components
from ..state import async_get


def render_page(state):
    """User Profile Page"""
    Components.section_header(
        "User Profile", "View your account information", "account_circle"
    )

    # Container for profile data
    profile_container = ui.column().classes("w-full gap-4")

    async def load_profile_data():
        """Load user profile data from API"""
        profile_data = await async_get("/api/user/profile")

        profile_container.clear()
        with profile_container:
            if "error" in profile_data or not profile_data.get("authenticated", False):
                # Not authenticated - show login prompt
                with Components.card().classes("items-center justify-center py-12"):
                    ui.icon("account_circle", size="4xl").classes("text-slate-700 mb-4")
                    ui.label("Not Authenticated").classes(
                        "text-2xl font-bold text-slate-400 mb-2"
                    )
                    ui.label("Please login to view your profile").classes(
                        "text-slate-500 mb-6"
                    )

                    def open_login():
                        import webbrowser
                        import os

                        # Use environment variable or default to localhost
                        oauth_url = os.getenv(
                            "OAUTH_SERVER_URL", "http://127.0.0.1:5050"
                        )
                        webbrowser.open(f"{oauth_url}/auth/start")

                    ui.button(
                        "Login to Upstox", icon="login", on_click=open_login
                    ).classes(
                        "bg-gradient-to-r from-orange-500 to-red-500 text-white font-bold px-6 py-3"
                    )

                    if "error" in profile_data:
                        ui.label(f"Error: {profile_data['error']}").classes(
                            "text-xs text-red-400 mt-4"
                        )
            else:
                # Authenticated - show profile

                # Profile Header Card
                with Components.card():
                    with ui.row().classes("w-full items-center justify-between"):
                        with ui.row().classes("items-center gap-4"):
                            # Avatar - use icon instead of external CDN
                            with ui.element("div").classes(
                                "w-16 h-16 rounded-full bg-indigo-600 flex items-center justify-center border-2 border-indigo-500"
                            ):
                                ui.icon("account_circle", size="3xl").classes(
                                    "text-white"
                                )

                            with ui.column():
                                ui.label(profile_data.get("name", "User")).classes(
                                    "text-2xl font-bold text-white"
                                )
                                ui.label(profile_data.get("email", "")).classes(
                                    "text-slate-400"
                                )

                                with ui.row().classes("items-center gap-2 mt-2"):
                                    ui.chip(
                                        "AUTHENTICATED",
                                        icon="check_circle",
                                        color="green",
                                    ).props("dense square outline")

                        ui.button(icon="refresh", on_click=load_profile_data).props(
                            "flat round"
                        ).classes("text-slate-400 hover:text-white")

                # Account Details Grid
                with ui.row().classes("w-full gap-4 flex-wrap"):
                    # User ID Card
                    with Components.card().classes("flex-1 min-w-[280px]"):
                        with ui.row().classes("items-center gap-3 mb-2"):
                            ui.icon("badge", size="lg").classes("text-blue-400")
                            ui.label("User ID").classes(
                                "text-sm font-bold text-slate-300"
                            )

                        ui.label(profile_data.get("user_id", "N/A")).classes(
                            "text-lg font-mono text-white break-all"
                        )

                    # Broker Card
                    with Components.card().classes("flex-1 min-w-[280px]"):
                        with ui.row().classes("items-center gap-3 mb-2"):
                            ui.icon("business", size="lg").classes("text-purple-400")
                            ui.label("Broker").classes(
                                "text-sm font-bold text-slate-300"
                            )

                        ui.label(profile_data.get("broker", "N/A")).classes(
                            "text-lg font-bold text-white"
                        )

                    # Account Type Card
                    with Components.card().classes("flex-1 min-w-[280px]"):
                        with ui.row().classes("items-center gap-3 mb-2"):
                            ui.icon("person", size="lg").classes("text-green-400")
                            ui.label("Account Type").classes(
                                "text-sm font-bold text-slate-300"
                            )

                        user_type = profile_data.get("user_type", "individual")
                        ui.label(user_type.capitalize()).classes(
                            "text-lg font-bold text-white"
                        )

                # Exchanges Card
                exchanges = profile_data.get("exchanges", [])
                if exchanges:
                    with Components.card():
                        ui.label("Enabled Exchanges").classes(
                            "text-lg font-bold text-white mb-4"
                        )

                        with ui.row().classes("gap-2 flex-wrap"):
                            for exchange in exchanges:
                                ui.chip(exchange, color="indigo").props(
                                    "outline square"
                                )

                # Additional Information Card
                with Components.card():
                    ui.label("Profile Details").classes(
                        "text-lg font-bold text-white mb-4"
                    )

                    with ui.grid(columns=2).classes("w-full gap-4"):
                        # Name
                        with ui.column().classes("gap-1"):
                            ui.label("Full Name").classes(
                                "text-xs text-slate-400 uppercase tracking-wider"
                            )
                            ui.label(profile_data.get("name", "N/A")).classes(
                                "text-sm font-medium text-white"
                            )

                        # Email
                        with ui.column().classes("gap-1"):
                            ui.label("Email").classes(
                                "text-xs text-slate-400 uppercase tracking-wider"
                            )
                            ui.label(profile_data.get("email", "N/A")).classes(
                                "text-sm font-medium text-white"
                            )

                        # User ID
                        with ui.column().classes("gap-1"):
                            ui.label("User ID").classes(
                                "text-xs text-slate-400 uppercase tracking-wider"
                            )
                            ui.label(profile_data.get("user_id", "N/A")).classes(
                                "text-sm font-mono text-blue-400"
                            )

                        # Broker
                        with ui.column().classes("gap-1"):
                            ui.label("Broker").classes(
                                "text-xs text-slate-400 uppercase tracking-wider"
                            )
                            ui.label(profile_data.get("broker", "N/A")).classes(
                                "text-sm font-medium text-white"
                            )

    # Initial load
    ui.timer(0.1, load_profile_data, once=True)
