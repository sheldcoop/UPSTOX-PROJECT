from nicegui import ui, run
from ..common import Components
from ..services.movers import MarketMoversService
import asyncio

# Service Instance
movers_service = MarketMoversService.get_instance()


@ui.refreshable
def stats_widget(state):
    """Refreshes independently for high-frequency updates"""
    pf = state.portfolio
    with ui.row().classes("w-full gap-4 flex-wrap"):
        Components.kpi_card(
            "Total Value", pf.get("total_value", 0), delta=0.5, prefix="₹"
        )
        Components.kpi_card("Day P&L", pf.get("total_pnl", 0), delta=1.2, prefix="₹")
        Components.kpi_card("Cash Balance", pf.get("cash", 0), prefix="₹")
        Components.kpi_card(
            "Active Positions", len(pf.get("positions", [])), suffix=" open"
        )


def render_gainers_losers_widget():
    """Renders the Market Movers Widget with Tabs"""

    with Components.card():
        with ui.row().classes("w-full items-center justify-between mb-2"):
            ui.label("Market Movers (Top 10)").classes("text-lg font-bold text-white")
            # Global Refresh for this widget
            ui.button(icon="refresh", on_click=lambda: load_active_tab()).props(
                "flat dense round color=slate-400"
            )

        # Category Tabs
        with ui.tabs().classes("w-full text-slate-400") as cat_tabs:
            t_nse = ui.tab("NSE EQ")
            t_bse = ui.tab("BSE EQ")
            t_nse_sme = ui.tab("NSE SME")
            t_bse_sme = ui.tab("BSE SME")
            t_nse_fut = ui.tab("NSE FUT")
            t_fo_eq = ui.tab("NSE F&O EQ")
            t_vol = ui.tab("Vol Shockers")
            # New Indices Tabs
            t_n50 = ui.tab("NIFTY 50")
            t_n500 = ui.tab("NIFTY 500")
            t_nbank = ui.tab("NIFTY BANK")

        # State tracking
        state_tracker = {
            "view": "gainers",  # gainers | losers
            "tab": "NSE_MAIN",  # NSE_MAIN | BSE_MAIN | NSE_SME
            "container": None,
            "page": 0,  # Current page
            "page_size": 10,  # Items per page
            "data_cache": [],  # Current full list of rows to paginate
        }

        # Shared Container for Table (Optimization: Don't duplicate table logic 3 times)
        content_area = ui.column().classes("w-full mt-4 min-h-[200px]")
        state_tracker["container"] = content_area

        # Pagination Controls Container
        pagination_area = ui.row().classes(
            "w-full justify-between items-center mt-2 px-2"
        )

        def render_table(rows_page):
            # Clear previous table
            content_area.clear()

            with content_area:
                if not rows_page:
                    ui.label("No data available.").classes(
                        "text-slate-500 italic p-4 text-center w-full"
                    )
                    return

                with ui.element("table").classes("w-full text-right text-xs"):
                    with ui.element("thead").classes(
                        "text-slate-500 border-b border-slate-700"
                    ):
                        with ui.element("tr"):
                            with ui.element("th").classes("pb-2 text-left pl-2"):
                                ui.label("Symbol")
                            with ui.element("th").classes(
                                "pb-2 text-left hidden md:table-cell"
                            ):
                                ui.label("Sector")
                            with ui.element("th").classes("pb-2"):
                                ui.label("Price")
                            with ui.element("th").classes("pb-2"):
                                ui.label("% Chg")
                            with ui.element("th").classes(
                                "pb-2 hidden sm:table-cell pr-2"
                            ):
                                ui.label("Vol")

                    with ui.element("tbody"):
                        for r in rows_page:
                            color = (
                                "text-green-400"
                                if r["pct_change"] >= 0
                                else "text-red-400"
                            )
                            bg_hover = "hover:bg-slate-800/50 transition-colors"

                            with ui.element("tr").classes(
                                f"border-b border-slate-800/30 {bg_hover}"
                            ):
                                # Symbol
                                with ui.element("td").classes(
                                    "py-2 font-bold text-left pl-2"
                                ):
                                    ui.label(r["symbol"])

                                # Sector (New)
                                with ui.element("td").classes(
                                    "py-2 text-xs text-slate-500 text-left hidden md:table-cell truncate max-w-[150px]"
                                ):
                                    ui.label(r.get("sector", "-"))

                                # Price
                                with ui.element("td").classes("py-2 font-mono"):
                                    ui.label(f"₹{r['price']:,.2f}")
                                # Change
                                with ui.element("td").classes(
                                    "py-2 font-mono " + color
                                ):
                                    ui.label(f"{r['pct_change']:+.2f}%")
                                # Volume
                                with ui.element("td").classes(
                                    "py-2 text-slate-500 hidden sm:table-cell pr-2"
                                ):
                                    ui.label(f"{r['volume']/1000:.1f}k")

        def update_pagination_view():
            full_data = state_tracker["data_cache"]
            page = state_tracker["page"]
            size = state_tracker["page_size"]

            total_items = len(full_data)
            max_page = max(0, (total_items + size - 1) // size - 1)

            # Clamp page
            if page < 0:
                page = 0
            if page > max_page:
                page = max_page
            state_tracker["page"] = page

            start = page * size
            end = start + size
            current_rows = full_data[start:end]

            render_table(current_rows)

            # Update Pagination Controls
            pagination_area.clear()
            with pagination_area:
                ui.label(
                    f"Showing {start+1}-{min(end, total_items)} of {total_items}"
                ).classes("text-xs text-slate-500")

                with ui.row().classes("gap-1"):

                    def change_page(delta):
                        state_tracker["page"] += delta
                        update_pagination_view()

                    ui.button(
                        icon="chevron_left", on_click=lambda: change_page(-1)
                    ).props("flat dense round").bind_enabled_from(
                        state_tracker, "page", backward=lambda p: p > 0
                    )
                    ui.button(
                        icon="chevron_right", on_click=lambda: change_page(1)
                    ).props("flat dense round").bind_enabled_from(
                        state_tracker, "page", backward=lambda p: p < max_page
                    )

        async def load_active_tab():
            key = state_tracker["tab"]
            v_type = state_tracker["view"]
            cnt = state_tracker["container"]

            cnt.clear()
            pagination_area.clear()

            with cnt:
                ui.spinner("dots", size="lg").classes("mx-auto text-indigo-500 mt-8")

            try:
                # Log to terminal for debugging
                print(f"Fetching movers for {key}...")
                data = await run.io_bound(movers_service.get_movers, key)

                if not data:
                    cnt.clear()
                    with cnt:
                        ui.label("Data service returned empty result.").classes(
                            "text-red-400 text-center w-full"
                        )
                    return

                # Get ALL rows (sorted)
                rows = data.get(v_type, [])

                # Update Cache & Reset Page
                state_tracker["data_cache"] = rows
                state_tracker["page"] = 0

                # Render First Page
                update_pagination_view()

            except Exception as e:
                cnt.clear()
                with cnt:
                    ui.label(f"Error loading data: {str(e)}").classes(
                        "text-red-400 text-sm font-mono p-2"
                    )
                    print(f"Movers Error: {e}", exc_info=True)

        # Controls (Toggle)
        with ui.row().classes("w-full justify-center -mt-2 mb-2"):
            tgl = ui.toggle(["Gainers", "Losers"], value="Gainers").props(
                "no-caps dense spread outline color=indigo"
            )

            async def on_toggle(e):
                state_tracker["view"] = e.value.lower()
                # Just re-render from existing data if possible, or fetch?
                # Service caches results so fetch is cheap
                await load_active_tab()

            tgl.on_value_change(on_toggle)

        # Tab Handling
        async def on_tab_change(e):
            val = e.value
            # DEBUG: Notify user of tab switch
            ui.notify(f"Switched to {val}", position="bottom-right", type="info")

            if val == "NSE EQ":
                state_tracker["tab"] = "NSE_MAIN"
            elif val == "BSE EQ":
                state_tracker["tab"] = "BSE_MAIN"
            elif val == "NSE SME":
                state_tracker["tab"] = "NSE_SME"
            elif val == "BSE SME":
                state_tracker["tab"] = "BSE_SME"
            elif val == "NSE FUT":
                state_tracker["tab"] = "NSE_FUT"
            elif val == "NSE F&O EQ":
                state_tracker["tab"] = "NSE_FO_EQ"
            elif val == "Vol Shockers":
                state_tracker["tab"] = "VOLUME_SHOCKERS"
            elif val == "NIFTY 50":
                state_tracker["tab"] = "NIFTY_50"
            elif val == "NIFTY 500":
                state_tracker["tab"] = "NIFTY_500"
            elif val == "NIFTY BANK":
                state_tracker["tab"] = "NIFTY_BANK"
            else:
                print(f"Unknown tab: {val}")

            await load_active_tab()

        cat_tabs.on_value_change(on_tab_change)

        # Initial Load
        ui.timer(0.1, load_active_tab, once=True)


def render_page(state):
    Components.section_header("Dashboard", "Real-time portfolio overview", "analytics")

    # Stats Grid
    stats_widget(state)

    # Full Width Layout
    with ui.column().classes("w-full mt-6"):
        # Market Status Card -> REPLACED WITH MOVERS
        render_gainers_losers_widget()
