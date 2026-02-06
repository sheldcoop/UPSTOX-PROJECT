"""
Market Calendar Page
Display market holidays and trading timings
"""

from nicegui import ui, run
from ..common import Components
from ..state import async_get, API_BASE
import requests
from datetime import datetime


def render_page(state):
    Components.section_header(
        "Market Calendar", "Trading holidays and market timings", "calendar_month"
    )

    # Tabs for Holidays and Timings
    with ui.tabs().classes("w-full") as tabs:
        holidays_tab = ui.tab("Holidays", icon="event_busy")
        timings_tab = ui.tab("Trading Hours", icon="schedule")

    with ui.tab_panels(tabs, value=holidays_tab).classes("w-full mt-4"):
        # Holidays Panel
        with ui.tab_panel(holidays_tab):
            render_holidays_section()

        # Timings Panel
        with ui.tab_panel(timings_tab):
            render_timings_section()


def render_holidays_section():
    """Display market holidays"""
    holidays_container = ui.column().classes("w-full gap-4")

    with Components.card():
        with ui.row().classes("w-full justify-between items-center mb-4"):
            ui.label("Market Holidays").classes("text-xl font-bold")
            ui.button(icon="refresh", on_click=lambda: load_holidays()).props("flat dense round")

        holidays_table_container = ui.column().classes("w-full")

    async def load_holidays():
        holidays_table_container.clear()
        with holidays_table_container:
            ui.spinner("dots", size="lg").classes("mx-auto")

        try:
            response = await run.io_bound(requests.get, f"{API_BASE}/market/holidays")
            if response.status_code == 200:
                holidays_data = response.json()
                holidays = holidays_data.get("holidays", [])

                holidays_table_container.clear()
                with holidays_table_container:
                    if not holidays:
                        ui.label("No upcoming holidays").classes("text-slate-400 italic p-4")
                    else:
                        # Summary
                        upcoming = sum(1 for h in holidays if datetime.strptime(h.get("date", ""), "%Y-%m-%d").date() >= datetime.now().date())
                        
                        with ui.row().classes("w-full gap-4 mb-4 flex-wrap"):
                            Components.kpi_card("Total Holidays", len(holidays), suffix=" days")
                            Components.kpi_card("Upcoming", upcoming, suffix=" days")

                        # Holidays Table
                        with ui.element("table").classes("w-full text-sm"):
                            # Header
                            with ui.element("thead").classes("text-slate-400 border-b border-slate-700"):
                                with ui.element("tr"):
                                    with ui.element("th").classes("pb-3 text-left pl-2"):
                                        ui.label("Date")
                                    with ui.element("th").classes("pb-3 text-left"):
                                        ui.label("Day")
                                    with ui.element("th").classes("pb-3 text-left"):
                                        ui.label("Holiday Name")
                                    with ui.element("th").classes("pb-3 text-left pr-2"):
                                        ui.label("Type")

                            # Body
                            with ui.element("tbody"):
                                for holiday in holidays:
                                    date_str = holiday.get("date", "")
                                    try:
                                        holiday_date = datetime.strptime(date_str, "%Y-%m-%d")
                                        is_past = holiday_date.date() < datetime.now().date()
                                        row_class = "opacity-50" if is_past else ""
                                    except:
                                        row_class = ""

                                    with ui.element("tr").classes(f"border-b border-slate-800 hover:bg-slate-800/50 {row_class}"):
                                        with ui.element("td").classes("py-3 pl-2"):
                                            ui.label(date_str).classes("font-bold text-white")
                                        with ui.element("td").classes("py-3"):
                                            day_name = datetime.strptime(date_str, "%Y-%m-%d").strftime("%A") if date_str else ""
                                            ui.label(day_name).classes("text-slate-300")
                                        with ui.element("td").classes("py-3"):
                                            ui.label(holiday.get("name", "")).classes("text-slate-300")
                                        with ui.element("td").classes("py-3 pr-2"):
                                            h_type = holiday.get("type", "").upper()
                                            type_color = "text-orange-400" if h_type == "TRADING" else "text-slate-400"
                                            ui.label(h_type).classes(type_color)

            else:
                holidays_table_container.clear()
                with holidays_table_container:
                    ui.label(f"Error loading holidays: {response.status_code}").classes("text-red-400")
        except Exception as e:
            holidays_table_container.clear()
            with holidays_table_container:
                ui.label(f"Error: {str(e)}").classes("text-red-400")

    # Initial load
    ui.timer(0.1, load_holidays, once=True)


def render_timings_section():
    """Display trading hours"""
    timings_container = ui.column().classes("w-full gap-4")

    with Components.card():
        with ui.row().classes("w-full justify-between items-center mb-4"):
            ui.label("Trading Hours").classes("text-xl font-bold")
            ui.button(icon="refresh", on_click=lambda: load_timings()).props("flat dense round")

        timings_table_container = ui.column().classes("w-full")

    async def load_timings():
        timings_table_container.clear()
        with timings_table_container:
            ui.spinner("dots", size="lg").classes("mx-auto")

        try:
            response = await run.io_bound(requests.get, f"{API_BASE}/market/timings")
            if response.status_code == 200:
                timings_data = response.json()
                segments = timings_data.get("segments", {})

                timings_table_container.clear()
                with timings_table_container:
                    if not segments:
                        ui.label("No timing information available").classes("text-slate-400 italic p-4")
                    else:
                        # Timings Table
                        with ui.element("table").classes("w-full text-sm"):
                            # Header
                            with ui.element("thead").classes("text-slate-400 border-b border-slate-700"):
                                with ui.element("tr"):
                                    with ui.element("th").classes("pb-3 text-left pl-2"):
                                        ui.label("Segment")
                                    with ui.element("th").classes("pb-3 text-left"):
                                        ui.label("Market Type")
                                    with ui.element("th").classes("pb-3 text-right"):
                                        ui.label("Opening Time")
                                    with ui.element("th").classes("pb-3 text-right pr-2"):
                                        ui.label("Closing Time")

                            # Body
                            with ui.element("tbody"):
                                for segment_name, timing_info in segments.items():
                                    with ui.element("tr").classes("border-b border-slate-800 hover:bg-slate-800/50"):
                                        with ui.element("td").classes("py-3 pl-2"):
                                            ui.label(segment_name).classes("font-bold text-white")
                                        with ui.element("td").classes("py-3"):
                                            ui.label(timing_info.get("type", "Regular")).classes("text-slate-300")
                                        with ui.element("td").classes("py-3 text-right"):
                                            ui.label(timing_info.get("opening", "-")).classes("text-green-400 font-mono")
                                        with ui.element("td").classes("py-3 text-right pr-2"):
                                            ui.label(timing_info.get("closing", "-")).classes("text-red-400 font-mono")

                        # Additional Info
                        with ui.column().classes("w-full mt-6 gap-2 bg-slate-800/30 p-4 rounded-lg"):
                            ui.label("Important Notes").classes("text-sm font-bold text-indigo-400 mb-2")
                            ui.label("• Pre-market session: 9:00 AM - 9:15 AM").classes("text-xs text-slate-400")
                            ui.label("• Regular trading: 9:15 AM - 3:30 PM").classes("text-xs text-slate-400")
                            ui.label("• Post-market session: 3:40 PM - 4:00 PM").classes("text-xs text-slate-400")

            else:
                timings_table_container.clear()
                with timings_table_container:
                    ui.label(f"Error loading timings: {response.status_code}").classes("text-red-400")
        except Exception as e:
            timings_table_container.clear()
            with timings_table_container:
                ui.label(f"Error: {str(e)}").classes("text-red-400")

    # Initial load
    ui.timer(0.1, load_timings, once=True)
