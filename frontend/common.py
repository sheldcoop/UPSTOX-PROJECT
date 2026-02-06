from nicegui import ui
from typing import Dict, Any, List

# ============================================================================
# 🎨 Theme & Appearance
# ============================================================================


class Theme:
    """Centralized Theme Configuration"""

    PRIMARY = "#6366f1"  # Indigo-500
    SECONDARY = "#ec4899"  # Pink-500
    ACCENT = "#3b82f6"  # Blue-500
    DARK_BG = "#0b1220"  # Slate-950 equivalent
    CARD_BG = "#0f172a"  # Slate-900
    SUCCESS = "#10b981"  # Emerald-500
    DANGER = "#ef4444"  # Red-500
    WARNING = "#f59e0b"

    @staticmethod
    def apply():
        ui.colors(
            primary=Theme.PRIMARY,
            secondary=Theme.SECONDARY,
            accent=Theme.ACCENT,
            dark=Theme.DARK_BG,
            positive=Theme.SUCCESS,
            negative=Theme.DANGER,
        )
        ui.add_css(
            f"""
            body {{ background-color: {Theme.DARK_BG}; }}
            .glass {{ background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(10px); }}
            ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
            ::-webkit-scrollbar-thumb {{ background: #1f2937; border-radius: 8px; }}
            ::-webkit-scrollbar-track {{ background: {Theme.DARK_BG}; }}
        """
        )


# ============================================================================
# 🧩 Reusable Components
# ============================================================================


class Components:
    """Library of reusable UI components for consistency"""

    @staticmethod
    def section_header(title: str, subtitle: str = None, icon: str = None):
        """Standardized page header with gradient text"""
        with ui.row().classes("items-center gap-3 mb-6 animate-fade-in"):
            if icon:
                ui.label(icon).classes("text-3xl text-indigo-400")
            with ui.column().classes("gap-0"):
                ui.label(title).classes(
                    "text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-pink-400"
                )
                if subtitle:
                    ui.label(subtitle).classes("text-sm text-slate-400 font-medium")

    @staticmethod
    def card(classes: str = "") -> ui.card:
        """Standardized card with consistent styling"""
        return ui.card().classes(
            f"w-full bg-slate-900/50 border border-slate-800 p-6 rounded-xl shadow-lg backdrop-blur-sm {classes}"
        )

    @staticmethod
    def kpi_card(
        title: str,
        value: Any,
        delta: float = 0,
        prefix: str = "",
        suffix: str = "",
        subtext: str = "",
    ):
        """Metric card with trend indicator"""
        with Components.card().classes(
            "flex-1 min-w-[240px] hover:border-indigo-500/50 transition-colors duration-300"
        ):
            with ui.row().classes("w-full justify-between items-start"):
                ui.label(title).classes(
                    "text-xs font-bold text-slate-400 uppercase tracking-wider"
                )
                if delta != 0:
                    color = "text-green-400" if delta > 0 else "text-red-400"
                    icon = "trending_up" if delta > 0 else "trending_down"
                    with ui.row().classes(
                        f"items-center gap-1 {color} bg-slate-800/50 px-2 py-0.5 rounded-full text-xs"
                    ):
                        ui.icon(icon, size="xs")
                        ui.label(f"{abs(delta):.2f}%")

            # Value Rendering
            val_display = (
                f"{prefix}{value:,.2f}{suffix}"
                if isinstance(value, (int, float))
                else str(value)
            )
            ui.label(val_display).classes("text-2xl font-bold text-white mt-2")

            if subtext:
                ui.label(subtext).classes("text-xs text-slate-500 mt-1")

    @staticmethod
    def date_input(label: str, value: str = None) -> ui.input:
        """Input field with popup calendar"""
        with (
            ui.input(label=label, value=value)
            .props("outlined dense dark readonly")
            .classes("flex-1") as input_field
        ):
            with ui.menu().props("no-parent-event") as menu:
                with ui.date().bind_value(input_field).props("dark square"):
                    with ui.row().classes("justify-end p-2"):
                        ui.button("Select", on_click=menu.close).props(
                            "flat dense color=primary"
                        )

            with input_field.add_slot("append"):
                ui.icon("event").on("click", menu.open).classes(
                    "cursor-pointer text-slate-400 hover:text-white"
                )
        return input_field

    @staticmethod
    def data_table(columns: List[Dict], rows: List[Dict], title: str = None):
        """Configured AgGrid for data display"""
        if title:
            ui.label(title).classes("text-lg font-bold mb-2 text-slate-300")

        return ui.table(
            columns=columns, rows=rows, pagination={"rowsPerPage": 10}
        ).classes("w-full bg-slate-900 border border-slate-800 shadow-sm rounded-lg")
