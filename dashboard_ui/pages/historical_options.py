from nicegui import ui, run
import asyncio
from datetime import datetime, timedelta
import logging
import sys
import os
import traceback

# Ensure project root is in path to import scripts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

IMPORT_ERROR = None
try:
    from scripts.expired_options_fetcher import (
        get_available_expiries,
        fetch_expired_option_contracts,
        parse_option_data,
        store_expired_options,
        get_stored_expired_options,
        ensure_expired_options_table,
        fetch_expired_historical_candles,
        store_expired_candles,
    )
except ImportError as e:
    IMPORT_ERROR = str(e)
    # Stub functions to prevent NameError, but we will block usage
    get_available_expiries = lambda x: []
    fetch_expired_option_contracts = lambda x, y: []
    parse_option_data = lambda x, y, z: {}
    store_expired_options = lambda x: 0
    get_stored_expired_options = lambda x: []
    ensure_expired_options_table = lambda: None
    fetch_expired_historical_candles = lambda w, x, y, z: []
    store_expired_candles = lambda x, y, z: 0

# Configure logger
logger = logging.getLogger(__name__)


def historical_options_page():
    # --- UI Layout ---
    with ui.column().classes("w-full p-4 space-y-4"):
        # Header
        ui.label("Historical Option Data").classes("text-2xl font-bold text-blue-600")
        ui.label("Download expired option chains from Upstox Historical API").classes(
            "text-gray-600"
        )

        # --- Import Error Check ---
        if IMPORT_ERROR:
            with ui.card().classes("w-full bg-red-100 border-l-4 border-red-500 p-4"):
                ui.label("Configuration Error").classes("font-bold text-red-700")
                ui.label(f"Could not import backend scripts: {IMPORT_ERROR}").classes(
                    "text-red-600 font-mono text-sm"
                )
                ui.label(
                    "Please check that commands are run from the project root and requirements are installed."
                ).classes("text-red-600 text-xs mt-1")
            return  # Stop rendering

        # Ensure DB table exists
        try:
            ensure_expired_options_table()
        except Exception as e:
            logger.error(f"Failed to init DB: {e}")
            ui.notify(f"DB Init Warning: {e}", type="warning")

        # --- Filters Section ---
        with ui.card().classes("w-full p-4 space-y-4"):
            with ui.row().classes("w-full justify-between items-start"):
                ui.label("Step 1: Select Underlying").classes("text-lg font-bold")

                # --- NEW: Drill Down Link ---
                ui.button(
                    "Drill Down / Inspector",
                    on_click=lambda: ui.open("/?page=api_debugger", new_tab=True),
                ).props("flat dense icon=travel_explore color=blue").tooltip(
                    "Open Advanced Debugger"
                )

                # Log Toggle
                log_view = ui.log().classes(
                    "w-full h-32 bg-slate-900 text-xs font-mono text-green-400 p-2 rounded hidden"
                )
                ui.switch(
                    "Show Logs",
                    on_change=lambda e: (
                        log_view.classes(remove="hidden")
                        if e.value
                        else log_view.classes(add="hidden")
                    ),
                )

            with ui.row().classes("items-end gap-4"):
                underlying_input = ui.input(
                    label="Underlying Symbol",
                    value="NIFTY",
                    placeholder="e.g. NIFTY, BANKNIFTY",
                ).classes("w-64")

                fetch_btn = ui.button("Fetch Expiries", icon="search").props(
                    "color=primary"
                )

        # --- Results / Selection Section ---
        # Container to hold the dynamic expiry list
        expiry_container = ui.column().classes("w-full hidden")

        # State variables
        selected_expiries = []

        async def on_fetch_click():
            log_view.push(f"[{datetime.now().strftime('%H:%M:%S')}] Button Clicked")

            symbol = underlying_input.value.strip()

            # --- Smart Detection & Validation ---
            if "|" in symbol:
                # Case 1: Likely a specific Option/Future contract (NSE_FO)
                if "NSE_FO" in symbol:
                    ui.notify(
                        "⚠️ You entered a specific Contract Key (NSE_FO), not an Underlying.",
                        type="warning",
                        timeout=5000,
                    )
                    ui.notify(
                        "This page downloads Chains. For specific contracts, use 'Drill Down' -> 'Direct Key Mode'.",
                        type="info",
                        timeout=7000,
                    )
                    # We do NOT block, but we warn, because fetch_expiries will likely return 0.

                # Case 2: Valid Underlying Keys (NSE_INDEX, NSE_EQ)
                elif "NSE_INDEX" in symbol or "NSE_EQ" in symbol:
                    # This is fine, let it pass
                    pass
                else:
                    ui.notify(
                        "⚠️ Unknown Key Format. Expecting NIFTY, BANKNIFTY or NSE_INDEX|...",
                        type="warning",
                    )

            symbol = symbol.upper()
            if not symbol:
                ui.notify("Please enter an underlying symbol", type="warning")
                return

            try:
                fetch_btn.props("loading=true")

                # DIRECT KEY MODE (User entered NSE_FO|...)
                if "|" in symbol:
                    ui.notify("Direct Key Mode Active", type="info")

                    # Try Extract Expiry for pre-fill
                    try:
                        # format: ..|03-10-2024
                        raw_date = symbol.split("|")[-1]
                        exp_dt = datetime.strptime(raw_date, "%d-%m-%Y")
                        to_date_def = exp_dt.strftime("%Y-%m-%d")
                    except:
                        to_date_def = datetime.now().strftime("%Y-%m-%d")  # Fallback

                    expiry_container.clear()
                    expiry_container.classes(remove="hidden")

                    with expiry_container:
                        ui.separator()
                        ui.label(f"Target: {symbol}").classes(
                            "text-xl font-mono text-green-400 font-bold"
                        )

                        # Just show "Download" config (Simplified)
                        with ui.card().classes(
                            "w-full bg-slate-900 border border-green-700"
                        ):
                            with ui.row().classes("gap-4 items-end"):
                                d_days = ui.select(
                                    {
                                        "0": "Expiry Day",
                                        "5": "Last 5 Days",
                                        "30": "Last 30 Days",
                                    },
                                    value="5",
                                    label="History Depth",
                                ).props("dark")
                                d_int = ui.select(
                                    ["1minute", "30minute", "day"],
                                    value="30minute",
                                    label="Interval",
                                ).props("dark")

                            async def do_single_download():
                                log_view.classes(remove="hidden")
                                log_view.push(f"Fetching candles for {symbol}...")

                                # Calc Dates
                                days = int(d_days.value)
                                try:
                                    # Parse date from key again
                                    end_d = datetime.strptime(
                                        symbol.split("|")[-1], "%d-%m-%Y"
                                    )
                                    start_d = end_d - timedelta(days=days)

                                    from_s = start_d.strftime("%Y-%m-%d")
                                    to_s = end_d.strftime(
                                        "%Y-%m-%d"
                                    )  # Upstox historic uses YYYY-MM-DD in URL path

                                    candles = await run.io_bound(
                                        fetch_expired_historical_candles,
                                        symbol,
                                        d_int.value,
                                        from_s,
                                        to_s,
                                    )

                                    if candles:
                                        log_view.push(
                                            f"SUCCESS: Got {len(candles)} candles."
                                        )

                                        # Prepare CSV
                                        import io
                                        import csv

                                        output = io.StringIO()
                                        writer = csv.writer(output)
                                        writer.writerow(
                                            [
                                                "timestamp",
                                                "open",
                                                "high",
                                                "low",
                                                "close",
                                                "volume",
                                                "oi",
                                            ]
                                        )
                                        for c in candles:
                                            writer.writerow(c)

                                        fname = f"candle_{symbol.replace('|','_')}.csv"
                                        ui.download(
                                            output.getvalue().encode("utf-8"), fname
                                        )
                                        ui.notify("Download Started", type="positive")
                                    else:
                                        log_view.push(
                                            "No data found (Empty Response). Check contract liquidity."
                                        )

                                except Exception as e:
                                    log_view.push(f"Error: {e}")

                            ui.button(
                                "Download CSV",
                                on_click=do_single_download,
                                icon="download",
                            ).props("color=green")

                    return  # Stop standard flow

                # --- Standard Flow (Underlying -> Expiries) ---
                # Check Token Validity Check (Mock check or via script)
                import os

                if not os.path.exists("access_token.txt"):
                    log_view.push("WARNING: access_token.txt not found in root")

                # Call script function directly in thread pool
                log_view.push(f"Fetching available expiries for {symbol}...")

                # Use run.io_bound to avoid blocking UI
                start_time = datetime.now()
                expiries = await run.io_bound(get_available_expiries, symbol)
                duration = (datetime.now() - start_time).total_seconds()

                log_view.push(
                    f"Fetch completed in {duration:.2f}s. Found {len(expiries) if expiries else 0} expiries."
                )

                if not expiries:
                    ui.notify(
                        f"No expiries found for {symbol}. (Check logs)", type="warning"
                    )
                    log_view.push("RESULT: Empty list returned. Possible causes:")
                    log_view.push("1. Upstox Token expired/invalid")
                    log_view.push("2. Incorrect Symbol")
                    log_view.push("3. API Rate Limit or Network Issue")

                    # Try to read token file to debug
                    try:
                        with open("access_token.txt", "r") as f:
                            tok = f.read().strip()
                            log_view.push(
                                f"Current Token (First 10 chars): {tok[:10]}..."
                            )
                    except:
                        log_view.push("Could not read access_token.txt")
                    return

                # Build the selection UI
                expiry_container.clear()
                expiry_container.classes(remove="hidden")

                with expiry_container:
                    ui.separator()
                    ui.label(f"Step 2: Select Expiries for {symbol}").classes(
                        "text-lg font-bold mt-2"
                    )

                    # Selection controls
                    with ui.row().classes("gap-4 mb-2"):
                        ui.button(
                            "Select All", on_click=lambda: set_all_checkboxes(True)
                        ).props("size=sm outline")
                        ui.button(
                            "Deselect All", on_click=lambda: set_all_checkboxes(False)
                        ).props("size=sm outline")

                    # Grid of checkboxes (Show latest first)
                    expiry_checkboxes = []
                    # Limit to last 50 to avoid UI lag if huge history
                    sorted_expiries = sorted(expiries, reverse=True)[:50]

                    with ui.scroll_area().classes(
                        "h-64 border border-gray-200 rounded p-2"
                    ):
                        with ui.grid(columns=4).classes("w-full gap-2"):
                            for exp in sorted_expiries:
                                cb = ui.checkbox(exp, value=False)
                                expiry_checkboxes.append(cb)

                    if len(expiries) > 50:
                        ui.label(
                            f"Showing newest 50 of {len(expiries)} expiries"
                        ).classes("text-xs text-gray-400")

                    def set_all_checkboxes(val):
                        for cb in expiry_checkboxes:
                            cb.value = val

                    # Step 3: Configuration (Download Options)
                    ui.separator().classes("mt-4")
                    ui.label("Step 3: Download Options").classes(
                        "text-lg font-bold mt-2"
                    )

                    with ui.row().classes("gap-4 items-center"):
                        chk_save_local = ui.checkbox("Save Locally (CSV)", value=True)
                        chk_save_db = ui.checkbox("Save to Database", value=False)

                    with ui.expansion(
                        "Candle Configuration (OHLC)", icon="candlestick_chart"
                    ).classes("w-full border border-slate-700 rounded"):
                        with ui.column().classes("p-2 gap-2"):
                            chk_download_candles = ui.checkbox(
                                "Download OHLC Candles", value=False
                            )
                            with ui.row().classes("gap-4"):
                                sel_interval = ui.select(
                                    ["1minute", "30minute", "day"],
                                    value="30minute",
                                    label="Interval",
                                )
                                sel_days = ui.select(
                                    {
                                        "0": "Expiry Day Only",
                                        "5": "Last 5 Days",
                                        "30": "Last 30 Days",
                                    },
                                    value="0",
                                    label="History Depth",
                                )

                            ui.label(
                                "⚠️ Warning: Downloading candles for 150+ contracts may take time and hit API limits."
                            ).classes("text-xs text-orange-400")

                    async def start_download():
                        selected = [cb.text for cb in expiry_checkboxes if cb.value]
                        if not selected:
                            ui.notify(
                                "Please select at least one expiry date", type="warning"
                            )
                            return

                        if not chk_save_local.value and not chk_save_db.value:
                            ui.notify(
                                "Please select at least one save method", type="warning"
                            )
                            return

                        ui.notify(
                            f"Starting download for {len(selected)} expiries...",
                            type="info",
                        )
                        log_view.classes(remove="hidden")  # Auto show logs
                        log_view.push(f"Starting batch download for: {selected}")

                        results = []
                        all_csv_data = []  # List to hold all rows for CSV

                        # Progress Bar
                        prog = ui.linear_progress(value=0).classes("w-full mt-2")

                        for i, expiry in enumerate(selected):
                            try:
                                prog.value = (i) / len(selected)
                                ui.notify(
                                    f"Processing {expiry}...",
                                    type="ongoing",
                                    timeout=1000,
                                )
                                log_view.push(f"Processing {expiry}...")

                                # 1. Fetch Option Chain
                                raw_contracts = await run.io_bound(
                                    fetch_expired_option_contracts, symbol, expiry
                                )
                                if not raw_contracts:
                                    results.append(
                                        {
                                            "expiry": expiry,
                                            "status": "failed",
                                            "msg": "No data returned",
                                        }
                                    )
                                    log_view.push(f"  FAILED: No data for {expiry}")
                                    continue

                                # Determine Date Range for Candles
                                from datetime import timedelta

                                try:
                                    # Expiry string to date obj
                                    exp_date_obj = datetime.strptime(expiry, "%Y-%m-%d")
                                    days_back = int(sel_days.value)
                                    start_date_obj = exp_date_obj - timedelta(
                                        days=days_back if days_back > 0 else 0
                                    )
                                    from_date_str = start_date_obj.strftime("%Y-%m-%d")
                                    to_date_str = expiry  # Upstox API often uses same day for simple checks, or expiry date
                                except ValueError:
                                    from_date_str = expiry
                                    to_date_str = expiry

                                # 2. Process Contracts (and optionally candles)
                                parsed_options = []
                                contracts_with_candles = 0

                                total_contracts = len(raw_contracts)
                                log_view.push(
                                    f"  Found {total_contracts} contracts. Starting processing..."
                                )

                                for idx, c in enumerate(raw_contracts):
                                    # Update UI every 10 items to show responsiveness
                                    if idx % 10 == 0:
                                        await asyncio.sleep(0.01)

                                    opt = parse_option_data(c, symbol, expiry)

                                    # Fetch Candle if requested
                                    if chk_download_candles.value:
                                        inst_key = c.get("instrument_key")
                                        if inst_key:
                                            # Rate limit pause (very crude)
                                            await asyncio.sleep(0.1)
                                            candles = await run.io_bound(
                                                fetch_expired_historical_candles,
                                                inst_key,
                                                sel_interval.value,
                                                from_date_str,
                                                to_date_str,
                                            )
                                            if candles:
                                                opt["has_candles"] = True
                                                opt["candle_count"] = len(candles)
                                                contracts_with_candles += 1

                                                # Save candles to DB if requested
                                                if chk_save_db.value:
                                                    await run.io_bound(
                                                        store_expired_candles,
                                                        inst_key,
                                                        sel_interval.value,
                                                        candles,
                                                    )

                                                # Attach to object for CSV (Top 5 candles summary?)
                                                if chk_save_local.value:
                                                    # Flatten simple stats
                                                    opt["candle_open_start"] = (
                                                        candles[0][1] if candles else ""
                                                    )
                                                    opt["candle_close_end"] = (
                                                        candles[-1][4]
                                                        if candles
                                                        else ""
                                                    )
                                            else:
                                                opt["has_candles"] = False

                                    parsed_options.append(opt)
                                    if chk_save_local.value:
                                        all_csv_data.append(opt)

                                if chk_download_candles.value:
                                    log_view.push(
                                        f"  Fetched candles for {contracts_with_candles}/{total_contracts} contracts."
                                    )

                                # 3. Store (Optional)
                                count = 0
                                if chk_save_db.value:
                                    count = await run.io_bound(
                                        store_expired_options, parsed_options
                                    )
                                    log_view.push(
                                        f"  SUCCESS: Stored {count} contracts in DB."
                                    )
                                else:
                                    count = len(parsed_options)
                                    log_view.push(
                                        f"  SUCCESS: Processed {count} contracts (Skipped DB)."
                                    )

                                results.append(
                                    {
                                        "expiry": expiry,
                                        "status": "success",
                                        "count": count,
                                        "candles": (
                                            contracts_with_candles
                                            if chk_download_candles.value
                                            else "N/A"
                                        ),
                                    }
                                )

                            except Exception as e:
                                logger.error(f"Error processing {expiry}: {e}")
                                results.append(
                                    {"expiry": expiry, "status": "error", "msg": str(e)}
                                )
                                log_view.push(f"  ERROR: {e}")

                        prog.value = 1.0

                        # Handle CSV Download
                        if chk_save_local.value and all_csv_data:
                            try:
                                import io
                                import csv

                                output = io.StringIO()
                                # Get headers from first dict
                                headers = list(all_csv_data[0].keys())
                                writer = csv.DictWriter(output, fieldnames=headers)
                                writer.writeheader()
                                writer.writerows(all_csv_data)

                                filename = f"{symbol}_options_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                                ui.download(output.getvalue().encode("utf-8"), filename)
                                ui.notify("CSV Download Started", type="positive")
                                log_view.push(f"Generated CSV: {filename}")
                            except Exception as e:
                                log_view.push(f"CSV Generation Error: {e}")

                        # Show Summary
                        total_processed = sum(
                            r.get("count", 0)
                            for r in results
                            if r["status"] == "success"
                        )
                        ui.notify(
                            f"Completed! Processed {total_processed} options.",
                            type="positive",
                        )

                        with ui.expansion(
                            f"Download Report ({total_processed} contracts)", value=True
                        ).classes("w-full mt-2 bg-green-50"):
                            for res in results:
                                icon = "✅" if res["status"] == "success" else "❌"
                                msg = (
                                    f"{res.get('count', 0)} contracts"
                                    if res["status"] == "success"
                                    else res.get("msg", "Error")
                                )
                                ui.label(f"{icon} {res['expiry']}: {msg}").classes(
                                    "ml-2"
                                )

                        # Trigger refresh of data view only if DB updated
                        if chk_save_db.value:
                            await refresh_data_view(symbol)

                    ui.button(
                        "Download Selected Option Chains",
                        on_click=start_download,
                        icon="cloud_download",
                    ).props("color=green size=lg").classes("mt-4 w-full")

                    # --- Data Viewer ---
                    ui.separator().classes("mt-8")
                    ui.label(f"Stored Data for {symbol}").classes("text-xl font-bold")
                    data_container = ui.column().classes("w-full")

                    async def refresh_data_view(sym):
                        data_container.clear()
                        with data_container:
                            ui.label("Loading stored data...").classes("animate-pulse")
                            stored_data = await run.io_bound(
                                get_stored_expired_options, sym
                            )
                            data_container.clear()

                            if not stored_data:
                                ui.label("No data found in database.").classes(
                                    "text-gray-500 italic"
                                )
                                return

                            # Group by Expiry
                            by_expiry = {}
                            for row in stored_data:
                                exp = row["expiry_date"]
                                opt_type = row.get("option_type", "")

                                if exp not in by_expiry:
                                    by_expiry[exp] = {"CE": 0, "PE": 0, "Total": 0}

                                by_expiry[exp]["Total"] += 1
                                if opt_type == "CE":
                                    by_expiry[exp]["CE"] += 1
                                elif opt_type == "PE":
                                    by_expiry[exp]["PE"] += 1

                            # Create a table
                            columns = [
                                {
                                    "name": "expiry",
                                    "label": "Expiry Date",
                                    "field": "expiry",
                                    "sortable": True,
                                    "align": "left",
                                },
                                {
                                    "name": "ce",
                                    "label": "Call (CE)",
                                    "field": "ce",
                                    "sortable": True,
                                    "align": "center",
                                },
                                {
                                    "name": "pe",
                                    "label": "Put (PE)",
                                    "field": "pe",
                                    "sortable": True,
                                    "align": "center",
                                },
                                {
                                    "name": "total",
                                    "label": "Total Contracts",
                                    "field": "total",
                                    "sortable": True,
                                    "align": "right",
                                },
                            ]
                            rows = [
                                {
                                    "expiry": k,
                                    "ce": v["CE"],
                                    "pe": v["PE"],
                                    "total": v["Total"],
                                }
                                for k, v in sorted(by_expiry.items(), reverse=True)
                            ]

                            ui.table(columns=columns, rows=rows, pagination=10).classes(
                                "w-full"
                            )

                    # Initial load of stored data
                    await refresh_data_view(symbol)

            except Exception as e:
                logger.error(f"Fetch failed: {e}")
                err_msg = traceback.format_exc()
                ui.notify(f"Critical Error: {str(e)}", type="negative")
                log_view.push("CRITICAL ERROR:")
                log_view.push(err_msg)
            finally:
                fetch_btn.props("loading=false")

        fetch_btn.on("click", on_fetch_click)
