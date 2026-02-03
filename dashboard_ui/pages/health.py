from nicegui import ui
from ..common import Components
from ..state import async_get


def render_page(state):
    """Health & System Status Page"""
    Components.section_header(
        "System Health", "Monitor system status and health", "health_and_safety"
    )

    # Container for health data
    health_container = ui.column().classes("w-full gap-4")

    async def load_health_data():
        """Load health check data from API"""
        health_data = await async_get("/api/health")

        health_container.clear()
        with health_container:
            if "error" in health_data:
                with Components.card():
                    with ui.row().classes("items-center gap-4"):
                        ui.icon("error", size="3xl").classes("text-red-500")
                        with ui.column():
                            ui.label("Health Check Failed").classes(
                                "text-xl font-bold text-red-400"
                            )
                            ui.label(f"Error: {health_data['error']}").classes(
                                "text-slate-400"
                            )
            else:
                # Status Overview Card
                with Components.card():
                    with ui.row().classes("w-full items-center justify-between"):
                        with ui.row().classes("items-center gap-4"):
                            status = health_data.get("status", "unknown")
                            if status == "healthy":
                                ui.icon("check_circle", size="3xl").classes(
                                    "text-green-500"
                                )
                            else:
                                ui.icon("warning", size="3xl").classes(
                                    "text-yellow-500"
                                )

                            with ui.column():
                                ui.label("System Status").classes(
                                    "text-lg font-bold text-white"
                                )
                                ui.label(status.upper()).classes(
                                    f"text-2xl font-bold {'text-green-400' if status == 'healthy' else 'text-yellow-400'}"
                                )

                        ui.button(icon="refresh", on_click=load_health_data).props(
                            "flat round"
                        ).classes("text-slate-400 hover:text-white")

                # Details Grid
                with ui.row().classes("w-full gap-4 flex-wrap"):
                    # Version Info
                    with Components.card().classes("flex-1 min-w-[280px]"):
                        with ui.row().classes("items-center gap-3 mb-2"):
                            ui.icon("info", size="lg").classes("text-blue-400")
                            ui.label("Version Information").classes(
                                "text-sm font-bold text-slate-300"
                            )

                        with ui.column().classes("gap-2"):
                            ui.label(
                                f"v{health_data.get('version', 'Unknown')}"
                            ).classes("text-xl font-bold text-white")
                            ui.label("API Version").classes("text-xs text-slate-500")

                    # Timestamp Info
                    with Components.card().classes("flex-1 min-w-[280px]"):
                        with ui.row().classes("items-center gap-3 mb-2"):
                            ui.icon("schedule", size="lg").classes("text-purple-400")
                            ui.label("Last Check").classes(
                                "text-sm font-bold text-slate-300"
                            )

                        with ui.column().classes("gap-2"):
                            timestamp = health_data.get("timestamp", "")
                            # Format timestamp for display
                            from datetime import datetime

                            try:
                                dt = datetime.fromisoformat(timestamp)
                                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                            except:
                                formatted_time = timestamp

                            ui.label(formatted_time).classes(
                                "text-lg font-mono text-white"
                            )
                            ui.label("Server Time").classes("text-xs text-slate-500")

                # System Metrics Card
                with Components.card():
                    ui.label("System Information").classes(
                        "text-lg font-bold text-white mb-4"
                    )

                    with ui.grid(columns=2).classes("w-full gap-4"):
                        # Status
                        with ui.column().classes("gap-1"):
                            ui.label("Health Status").classes(
                                "text-xs text-slate-400 uppercase tracking-wider"
                            )
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("radio_button_checked", size="sm").classes(
                                    "text-green-500"
                                )
                                ui.label(health_data.get("status", "Unknown")).classes(
                                    "text-sm font-medium text-white capitalize"
                                )

                        # Version
                        with ui.column().classes("gap-1"):
                            ui.label("API Version").classes(
                                "text-xs text-slate-400 uppercase tracking-wider"
                            )
                            ui.label(f"v{health_data.get('version', 'N/A')}").classes(
                                "text-sm font-medium text-white"
                            )

                        # Endpoint
                        with ui.column().classes("gap-1"):
                            ui.label("Endpoint").classes(
                                "text-xs text-slate-400 uppercase tracking-wider"
                            )
                            ui.label("/api/health").classes(
                                "text-sm font-mono text-blue-400"
                            )

                        # Uptime (placeholder)
                        with ui.column().classes("gap-1"):
                            ui.label("Status").classes(
                                "text-xs text-slate-400 uppercase tracking-wider"
                            )
                            ui.label("Online").classes(
                                "text-sm font-medium text-green-400"
                            )

    # Initial load
    ui.timer(0.1, load_health_data, once=True)

    # Auto-refresh every 30 seconds
    ui.timer(30, load_health_data)
