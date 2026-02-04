from nicegui import ui
from datetime import datetime, timedelta
from ..common import Components
from ..state import async_post
import asyncio


def render_page(state):
    Components.section_header(
        "Data Center", "Direct Instrument Download & Snapshot", "cloud_download"
    )

    # Main Container
    with ui.column().classes("w-full gap-6"):
        # --- 1. Instrument Input (Direct Key) ---
        with Components.card():
            ui.label("Step 1: Target Instruments").classes("text-lg font-bold mb-2")

            with ui.row().classes("w-full items-start gap-4"):
                # Left: Main Input
                with ui.column().classes("flex-1"):
                    ui.label("Enter Instrument Keys (comma separated/newline)").classes(
                        "text-xs text-slate-400"
                    )

                    # Store keys in state list or use a bound variable
                    # We'll use the existing state.selected_symbols but treat them as Keys now

                    def keys_updated(e):
                        val = e.value
                        if val:
                            # Handle newline or comma
                            keys = val.replace("\n", ",").split(",")
                            state.selected_symbols = [
                                k.strip() for k in keys if k.strip()
                            ]
                        else:
                            state.selected_symbols = []

                    # Initial value from state
                    init_val = (
                        ", ".join(state.selected_symbols)
                        if state.selected_symbols
                        else ""
                    )

                    key_input = (
                        ui.textarea(
                            value=init_val,
                            placeholder="NSE_EQ|INE848E01016, NSE_FO|50911...",
                        )
                        .props(
                            'outlined dense dark input-style="font-family: monospace" rows=3'
                        )
                        .classes("w-full font-mono text-sm")
                    )

                    key_input.on("input", keys_updated)

                    ui.label(
                        f"{len(state.selected_symbols)} keys ready"
                    ).bind_text_from(
                        state, "selected_symbols", lambda s: f"{len(s)} keys ready"
                    ).classes(
                        "text-xs text-indigo-400 mt-1"
                    )

                # Right: Quick Helper (Search)
                with ui.column().classes(
                    "w-full md:w-1/3 bg-slate-800/50 p-3 rounded border border-slate-700"
                ):
                    ui.label("Instrument Key Finder").classes(
                        "text-sm font-bold text-indigo-300"
                    )

                    search_input = (
                        ui.input(placeholder="Search Name (e.g. RELIANCE)")
                        .props("dense outlined dark append-icon=search")
                        .classes("w-full text-xs")
                    )

                    results_container = ui.column().classes(
                        "w-full gap-1 mt-2 max-h-[150px] overflow-y-auto pr-1"
                    )

                    async def perform_search(e=None):
                        # Use the input value directly to support different event types (Change, Key, Button)
                        val = search_input.value
                        if not val:
                            return
                        if len(val) < 2:
                            ui.notify(
                                "Enter at least 2 characters",
                                type="warning",
                                position="bottom-right",
                            )
                            return

                        results_container.clear()
                        with results_container:
                            ui.spinner("dots", size="sm")

                        rows = await state.search_instrument_details(val)

                        results_container.clear()
                        with results_container:
                            if not rows:
                                ui.label(f'No results for "{val}"').classes(
                                    "text-xs text-slate-500 italic"
                                )
                                return

                            for row in rows:
                                key = row["instrument_key"]
                                sym = row["symbol"]
                                seg = row["segment_id"]
                                exch = row["trading_symbol"]

                                def add_key(k=key):
                                    current = key_input.value
                                    if current:
                                        if k not in current:
                                            key_input.set_value(current + ", " + k)
                                            # Also trigger update manually since set_value might not fire input
                                            current_list = [
                                                x.strip() for x in current.split(",")
                                            ]
                                            current_list.append(k)
                                            state.selected_symbols = current_list
                                    else:
                                        key_input.set_value(k)
                                        state.selected_symbols = [k]
                                    ui.notify(f"Added {k}", position="bottom-right")

                                with ui.row().classes(
                                    "w-full justify-between items-center bg-slate-900/50 p-1 rounded hover:bg-slate-700 cursor-pointer text-xs"
                                ):
                                    with ui.row().classes("gap-2 items-center"):
                                        ui.label(sym).classes("font-bold")
                                        ui.label(seg).classes(
                                            "text-[10px] text-slate-400"
                                        )
                                        ui.label(exch).classes(
                                            "text-[10px] text-slate-500 truncate max-w-[80px]"
                                        )
                                    ui.button(icon="add", on_click=add_key).props(
                                        "flat dense size=xs color=green"
                                    )

                    # Bindings
                    search_input.on("keydown.enter", perform_search)
                    search_input.on("blur", perform_search)
                    # Debounce for typing
                    search_input_timer = None

                    def on_type(e):
                        nonlocal search_input_timer
                        if search_input_timer:
                            search_input_timer.cancel()
                        if len(e.value) > 2:
                            search_input_timer = asyncio.create_task(asyncio.sleep(0.5))
                            search_input_timer.add_done_callback(
                                lambda _: asyncio.create_task(perform_search())
                            )

                    search_input.on("input", on_type)

            # --- Configurations ---
            ui.separator().classes("my-4 border-slate-800")
            ui.label("Step 2: Action & Settings").classes("text-lg font-bold mb-2")

            mode_select = (
                ui.toggle(
                    ["Historical OHLC", "Market Snapshot"], value="Historical OHLC"
                )
                .props("no-caps spread color=indigo toggle-color=indigo-900")
                .classes("w-full mb-4")
            )

            with (
                ui.row()
                .classes("w-full gap-6 mt-2")
                .bind_visibility_from(
                    mode_select, "value", lambda v: v == "Historical OHLC"
                )
            ):
                # Date Selection
                with ui.column().classes("flex-1"):
                    ui.label("Time Period").classes(
                        "text-sm font-bold text-slate-400 mb-2"
                    )
                    with ui.row().classes("w-full gap-4"):
                        d_from = Components.date_input(
                            "Start From",
                            value=(datetime.now() - timedelta(30)).strftime("%Y-%m-%d"),
                        )
                        d_to = Components.date_input(
                            "End To", value=datetime.now().strftime("%Y-%m-%d")
                        )

                    # Quick Ranges
                    with ui.row().classes("gap-2 mt-2"):

                        def set_range(days: int):
                            d_to.value = datetime.now().strftime("%Y-%m-%d")
                            d_from.value = (
                                datetime.now() - timedelta(days=days)
                            ).strftime("%Y-%m-%d")

                        for label, days in [
                            ("1W", 7),
                            ("1M", 30),
                            ("3M", 90),
                            (
                                "YTD",
                                (
                                    datetime.now() - datetime(datetime.now().year, 1, 1)
                                ).days,
                            ),
                        ]:
                            ui.chip(label, on_click=lambda d=days: set_range(d)).props(
                                "clickable dense square outline icon=calendar_today"
                            ).classes("hover:bg-indigo-500 hover:text-white text-xs")

                # Options
                with ui.column().classes("flex-1"):
                    ui.label("Output Settings").classes(
                        "text-sm font-bold text-slate-400 mb-2"
                    )
                    interval_select = (
                        ui.select(
                            options={
                                "1m": "1 Minute",
                                "5m": "5 Minutes",
                                "15m": "15 Minutes",
                                "30m": "30 Minutes",
                                "1h": "1 Hour",
                                "1d": "Daily (EOD)",
                                "week": "Weekly",
                                "month": "Monthly",
                            },
                            value="1d",
                            label="Candle Interval",
                        )
                        .props("outlined dense dark options-dense")
                        .classes("w-full")
                    )

                    with ui.row().classes("gap-4 mt-2"):
                        save_db_switch = ui.switch("Save to SQLite", value=True).props(
                            "color=green dense dark"
                        )
                        download_local_switch = ui.switch(
                            "Download File", value=False
                        ).props("color=blue dense dark")
                        file_format = (
                            ui.select(
                                ["parquet", "csv"], value="parquet", label="Format"
                            )
                            .props("dense outlined dark options-dense")
                            .classes("w-24")
                            .bind_visibility_from(download_local_switch, "value")
                        )

            # --- Actions ---
            status_label = ui.label("").classes("text-sm mt-2")
            result_area = ui.column().classes("w-full mt-4")

            async def run_download():
                # Re-fetch from input to be sure
                raw = key_input.value or ""
                keys = [
                    k.strip() for k in raw.replace("\n", ",").split(",") if k.strip()
                ]

                if not keys:
                    ui.notify(
                        "Please enter at least one Instrument Key", type="warning"
                    )
                    return

                status_label.text = f"⏳ Processing {len(keys)} instruments..."
                result_area.clear()

                # MODE: MARKET SNAPSHOT
                if mode_select.value == "Market Snapshot":
                    res = await async_post("/api/market-quote", {"symbols": keys})

                    if "error" in res:
                        status_label.text = f"❌ Error: {res['error']}"
                        return

                    status_label.text = "✅ Complete"

                    with result_area:
                        with ui.card().classes(
                            "w-full bg-slate-900 border border-slate-700"
                        ):
                            with ui.row().classes("justify-between w-full"):
                                ui.label("Market Snapshot (Live)").classes(
                                    "text-lg font-bold"
                                )
                                ui.button(
                                    "Clear", on_click=result_area.clear, icon="close"
                                ).props("flat dense")

                            data_map = res.get("data", {})
                            with ui.column().classes("gap-4 w-full"):
                                # Grid view for quotes usually better
                                with ui.grid(columns=2).classes("w-full gap-4"):
                                    for key, quote in data_map.items():
                                        with ui.card().classes(
                                            "bg-slate-800 p-3 w-full"
                                        ):
                                            with ui.row().classes(
                                                "justify-between w-full border-b border-slate-700 pb-2 mb-2"
                                            ):
                                                ui.label(key).classes(
                                                    "font-mono font-bold text-xs text-indigo-300"
                                                )
                                                ui.label(
                                                    f"₹{quote.get('last_price', 'N/A')}"
                                                ).classes(
                                                    "text-lg font-bold text-white"
                                                )

                                            with ui.grid(columns=2).classes(
                                                "w-full gap-2 text-xs text-slate-400"
                                            ):
                                                ohlc = quote.get("ohlc", {})
                                                ui.label(f"Open: {ohlc.get('open')}")
                                                ui.label(f"High: {ohlc.get('high')}")
                                                ui.label(f"Low: {ohlc.get('low')}")
                                                ui.label(f"Close: {ohlc.get('close')}")
                                                ui.label(f"Vol: {quote.get('volume')}")
                                                ui.label(f"OI: {quote.get('oi')}")

                    return

                # MODE: HISTORICAL OHLC
                if not save_db_switch.value and not download_local_switch.value:
                    ui.notify("Select at least one output option", type="warning")
                    return

                fmt = file_format.value if download_local_switch.value else None

                res = await async_post(
                    "/api/download/stocks",
                    {
                        "symbols": keys,
                        "start_date": d_from.value,
                        "end_date": d_to.value,
                        "interval": interval_select.value,
                        "save_db": save_db_switch.value,
                        "export_format": fmt,
                    },
                )

                if "error" in res:
                    status_label.text = f"❌ Failed: {res['error']}"
                    status_label.classes("text-red-400")
                else:
                    status_label.text = f"✅ Success: {res.get('rows', 0)} rows fetched."
                    status_label.classes("text-green-400")
                    if download_local_switch.value and res.get("filepath"):
                        ui.download(res["filepath"])
                        ui.notify("File download started", type="positive")
                    await refresh_dl_list()

            # Dynamic Button Label
            btn = ui.button(
                "Execute", icon="play_arrow", on_click=run_download
            ).classes("w-full mt-4 bg-indigo-600 hover:bg-indigo-500")
            btn.bind_text_from(
                mode_select,
                "value",
                lambda v: (
                    "Get Snapshot" if v == "Market Snapshot" else "Download History"
                ),
            )
            btn.bind_prop_from(
                mode_select,
                "value",
                lambda v: "icon=bolt" if v == "Market Snapshot" else "icon=history",
            )

        # --- 2. Recent Files ---
        with Components.card():
            ui.label("Recent Downloads").classes(
                "text-sm font-bold mb-4 text-slate-400"
            )
            history_list = ui.column().classes("w-full gap-2")

            async def refresh_dl_list():
                hist = await state.fetch_download_history()
                history_list.clear()
                with history_list:
                    if not hist.get("files"):
                        ui.label("No files found").classes(
                            "text-slate-500 italic text-xs"
                        )
                    for f in hist["files"][:8]:
                        with ui.row().classes(
                            "w-full justify-between items-center bg-slate-800/30 p-2 rounded hover:bg-slate-800/50 transition"
                        ):
                            with ui.row().classes("gap-3 items-center"):
                                ui.icon("description", size="xs").classes(
                                    "text-indigo-400"
                                )
                                ui.label(f["filename"]).classes("font-mono text-xs")
                            ui.label(f"{f['size']/1024:.0f} KB").classes(
                                "text-[10px] text-slate-500"
                            )

            ui.timer(1.0, refresh_dl_list)
