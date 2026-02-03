from nicegui import ui, run
import logging
import asyncio
import json
import requests
from datetime import datetime, timedelta
import sys
import os

# Import backend logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from scripts.expired_options_fetcher import (
    get_available_expiries,
    fetch_expired_option_contracts,
    API_BASE_URL,
    ensure_token_valid,
    get_instrument_key,
)

# --- GLOBAL STATE (Persists across navigation) ---
DRILL_DOWN_STATE = {
    "symbol": "NIFTY",
    "expiry": None,
    "contracts": [],
    "selected_contract": None,
    "step": 1,  # 1: Broad, 2: Date, 3: Contract, 4: Data
}


def api_debugger_page():
    # State is now global module-level var to persist across nav
    state = DRILL_DOWN_STATE

    with ui.column().classes("w-full max-w-5xl mx-auto p-4 space-y-6"):
        # Header
        with ui.row().classes("items-center gap-2"):
            ui.icon("travel_explore", size="lg").classes("text-blue-500")
            ui.label('Expired Data "Drill Down"').classes(
                "text-2xl font-bold text-slate-200"
            )
            with ui.row().classes("ml-auto"):
                ui.button("Reset", on_click=lambda: reset_state()).props(
                    "flat color=grey icon=restart_alt"
                )

        ui.label(
            "Follow the logical flow: Symbol -> Date -> Contract -> Data."
        ).classes("text-slate-400 -mt-4")

        # Warning / Clarification Box
        with ui.expansion(
            "Why can't I just search by key?", icon="help_outline"
        ).classes("w-full bg-slate-900 border border-slate-700"):
            ui.markdown(
                """
             **Understanding the Logic:**
             1. **Master Search**: You search for `NIFTY` -> Upstox gives us `NSE_INDEX|Nifty 50`.
             2. **Date Search**: We ask "What dates did this index have valid options?".
             3. **Contract Search**: We get the list. Each contract has a UNIQUE key like `NSE_FO|...|27-01-2026`.
             
             **Direct Key Mode:** If you ALREADY have the full key (e.g. from a previous search), you CAN verify it directly below.
             """
            )

        # Start of Tabs
        with ui.tabs().classes("w-full") as tabs:
            tab_wizard = ui.tab("Wizard Mode (Recommended)")
            tab_direct = ui.tab("Direct Key Mode")

        with ui.tab_panels(tabs, value=tab_wizard).classes("w-full bg-transparent"):
            # --- WIZARD MODE ---
            with ui.tab_panel(tab_wizard).classes("p-0 space-y-4"):
                # STEP 1: BROAD SEARCH
                with ui.card().classes(
                    "w-full border-l-4 border-blue-500 bg-slate-900"
                ):
                    ui.label("Step 1: The Broad Search").classes(
                        "text-lg font-bold text-blue-400"
                    )
                    with ui.row().classes("w-full items-end gap-4"):
                        symbol_input = (
                            ui.input(
                                "Underlying Symbol",
                                value=state["symbol"],
                                placeholder="e.g. NIFTY",
                            )
                            .classes("w-64")
                            .props("dark")
                        )

                        async def step1_find_expiries():
                            sym = symbol_input.value.strip().upper()
                            if not sym:
                                return

                            state["symbol"] = sym
                            state["step"] = 2

                            step1_btn.props("loading=true")
                            try:
                                expiries = await run.io_bound(
                                    get_available_expiries, sym
                                )
                                if expiries:
                                    # Update UI
                                    expiry_select.options = sorted(
                                        expiries, reverse=True
                                    )
                                    expiry_select.value = expiries[0]
                                    step2_container.classes(remove="hidden")
                                    ui.notify(
                                        f"✅ Found {len(expiries)} dates",
                                        type="positive",
                                    )
                                else:
                                    ui.notify(
                                        f"❌ No expiries found for {sym}",
                                        type="negative",
                                    )
                            finally:
                                step1_btn.props("loading=false")

                        step1_btn = ui.button(
                            "Find Expiries", on_click=step1_find_expiries
                        ).props("color=blue icon=calendar_month")

                # STEP 2: DATE SEARCH
                step2_container = ui.column().classes(
                    f'w-full {"hidden" if state["step"] < 2 else ""} space-y-4'
                )
                with step2_container:
                    with ui.card().classes(
                        "w-full border-l-4 border-purple-500 bg-slate-900"
                    ):
                        ui.label("Step 2: The Date Search").classes(
                            "text-lg font-bold text-purple-400"
                        )

                        with ui.row().classes("w-full items-end gap-4"):
                            expiry_select = (
                                ui.select([], label="Select Date")
                                .classes("w-64")
                                .props("dark")
                            )
                            # Pre-fill if we have state
                            if state["expiry"]:
                                expiry_select.value = state["expiry"]

                            async def step2_find_contracts():
                                if not expiry_select.value:
                                    return
                                state["expiry"] = expiry_select.value
                                state["step"] = 3

                                step2_btn.props("loading=true")
                                try:
                                    contracts = await run.io_bound(
                                        fetch_expired_option_contracts,
                                        state["symbol"],
                                        state["expiry"],
                                    )
                                    if contracts:
                                        state["contracts"] = contracts
                                        render_contracts_table(contracts)
                                        step3_container.classes(remove="hidden")
                                        ui.notify(
                                            f"✅ Found {len(contracts)} contracts",
                                            type="positive",
                                        )
                                    else:
                                        ui.notify(
                                            "❌ No contracts found", type="warning"
                                        )
                                finally:
                                    step2_btn.props("loading=false")

                            step2_btn = ui.button(
                                "Get Contracts", on_click=step2_find_contracts
                            ).props("color=purple icon=list")

                # STEP 3: CONTRACT SEARCH
                step3_container = ui.column().classes(
                    f'w-full {"hidden" if state["step"] < 3 else ""} space-y-4'
                )
                table_container = ui.element("div")

                def render_contracts_table(contracts):
                    table_container.clear()
                    with step3_container:
                        with ui.card().classes(
                            "w-full border-l-4 border-orange-500 bg-slate-900"
                        ):
                            ui.label("Step 3: The Contract Search").classes(
                                "text-lg font-bold text-orange-400"
                            )

                            # Filters
                            with ui.row().classes("gap-4 mb-2"):
                                search_box = (
                                    ui.input("Search Name")
                                    .classes("w-48")
                                    .props("dark dense")
                                )
                                type_filter = ui.select(
                                    ["ALL", "CE", "PE"], value="ALL", label="Type"
                                ).props("dark dense")

                            rows = []
                            for c in contracts:
                                name = c.get("trading_symbol", "") or c.get(
                                    "tradingsymbol", ""
                                )
                                strike = c.get("strike_price", 0)
                                otype = c.get("instrument_type", "") or (
                                    "CE" if "CE" in name else "PE"
                                )
                                rows.append(
                                    {
                                        "name": name,
                                        "type": otype,
                                        "strike": float(strike) if strike else 0,
                                        "key": c.get("instrument_key"),
                                        "expiry": c.get("expiry_date"),
                                    }
                                )

                            columns = [
                                {
                                    "name": "name",
                                    "label": "Trading Symbol",
                                    "field": "name",
                                    "align": "left",
                                    "sortable": True,
                                },
                                {
                                    "name": "type",
                                    "label": "Type",
                                    "field": "type",
                                    "sortable": True,
                                },
                                {
                                    "name": "strike",
                                    "label": "Strike",
                                    "field": "strike",
                                    "sortable": True,
                                },
                                {
                                    "name": "key",
                                    "label": "Instrument Key (ID)",
                                    "field": "key",
                                    "align": "left",
                                    "classes": "font-mono text-xs text-secondary cursor-pointer",
                                },
                            ]

                            # Table with sticky header
                            table = ui.table(
                                columns=columns, rows=rows, pagination=10
                            ).classes("w-full cursor-pointer")

                            # Filter Logic
                            def do_filter():
                                term = search_box.value.upper()
                                t_type = type_filter.value
                                filtered = []
                                for r in rows:
                                    if t_type != "ALL" and r["type"] != t_type:
                                        continue
                                    if term and term not in r["name"]:
                                        continue
                                    filtered.append(r)
                                table.rows = filtered
                                table.update()

                            search_box.on_value_change(do_filter)
                            type_filter.on_value_change(do_filter)

                            # Selection Logic
                            async def on_row_click(e):
                                if len(e.args) < 2:
                                    return
                                row = e.args[1]
                                state["selected_contract"] = row
                                state["step"] = 4

                                prepare_step4(row)
                                step4_container.classes(remove="hidden")
                                ui.run_javascript(
                                    "window.scrollTo(0, document.body.scrollHeight)"
                                )

                            table.on("row-click", on_row_click)
                            table_container.move(table)

                # Initialize table if we have state
                if state["contracts"]:
                    render_contracts_table(state["contracts"])

                # STEP 4: DATA DOWNLOAD (Universal for Wizard & Direct)
                step4_container = ui.column().classes(
                    f'w-full {"hidden" if state["step"] < 4 else ""} space-y-4'
                )

            # --- DIRECT KEY MODE ---
            with ui.tab_panel(tab_direct):
                with ui.card().classes("w-full bg-slate-900 border border-slate-700"):
                    ui.label("Direct Key Input").classes("text-lg font-bold text-white")
                    ui.label(
                        "Paste a full Instrument Key to fetch candles immediately."
                    ).classes("text-xs text-gray-400")

                    direct_key_input = (
                        ui.input("Instrument Key", placeholder="NSE_FO|...")
                        .classes("w-full")
                        .props("dark")
                    )
                    direct_date_input = (
                        ui.input(
                            "Expiry Date (YYYY-MM-DD)",
                            placeholder="Required for calculation",
                        )
                        .classes("w-48")
                        .props("dark")
                    )

                    async def direct_fetch_setup():
                        key = direct_key_input.value.strip()
                        date = direct_date_input.value.strip()
                        if not key or not date:
                            ui.notify(
                                "Both Key and Expiry Date are required", type="warning"
                            )
                            return

                        # Mock a "row" object to reuse Step 4 logic
                        mock_row = {
                            "name": "Custom Key Request",
                            "key": key,
                            "expiry": date,
                        }
                        state["step"] = 4
                        state["selected_contract"] = mock_row  # Ensure persistence

                        prepare_step4(mock_row)
                        step4_container.classes(remove="hidden")

                    ui.button("Load Inspector", on_click=direct_fetch_setup).props(
                        "color=green icon=fast_forward"
                    )

    # --- SHARED STEP 4 LOGIC (Outside tab panels to be accessible by both) ---
    def prepare_step4(contract_row):
        step4_container.clear()
        with step4_container:
            with ui.card().classes("w-full border-l-4 border-green-500 bg-slate-900"):
                ui.label("Step 4: The Data Download").classes(
                    "text-lg font-bold text-green-400"
                )

                with ui.row().classes("items-center gap-4 mb-2"):
                    ui.label(f"Target: {contract_row['name']}").classes(
                        "text-xl font-bold text-white"
                    )

                    # Copy Button
                    ui.button(
                        on_click=lambda: (
                            ui.clipboard.write(contract_row["key"]),
                            ui.notify("Copied!"),
                        ),
                        icon="content_copy",
                    ).props("flat round size=sm").tooltip("Copy Key")

                    ui.chip(contract_row["key"], icon="key").props(
                        "square outline dense"
                    )

                # Date Config
                with ui.row().classes("items-center gap-4"):
                    try:
                        exp_dt = datetime.strptime(contract_row["expiry"], "%Y-%m-%d")
                        from_dt = exp_dt - timedelta(days=5)
                        def_from = from_dt.strftime("%Y-%m-%d")
                    except:
                        def_from = contract_row["expiry"]

                    d_from = ui.input("From", value=def_from).props("dark dense")
                    d_to = ui.input("To (Expiry)", value=contract_row["expiry"]).props(
                        "dark dense"
                    )
                    interval = ui.select(
                        ["1minute", "30minute", "day"],
                        value="30minute",
                        label="Interval",
                    ).props("dark dense")

                    log_area = ui.column().classes("w-full mt-2")

                    async def fetch_loot():
                        log_area.clear()
                        with log_area:
                            log_view = ui.log().classes(
                                "w-full h-48 bg-black text-green-400 font-mono text-xs p-2 rounded"
                            )
                            log_view.push(
                                f"🚀 Requesting candles for {contract_row['key']}..."
                            )

                            url = f"{API_BASE_URL}/expired-instruments/historical-candle/{contract_row['key']}/{interval.value}/{d_to.value}/{d_from.value}"
                            log_view.push(f"🔗 URL: {url}")

                            try:
                                token = ensure_token_valid()
                                headers = {
                                    "Authorization": f"Bearer {token}",
                                    "Accept": "application/json",
                                }
                                resp = await run.io_bound(
                                    requests.get, url, headers=headers
                                )

                                if resp.status_code == 200:
                                    data = resp.json()
                                    candles = data.get("data", {}).get(
                                        "candles", []
                                    ) or data.get("data", [])

                                    if candles:
                                        log_view.push(
                                            f"✅ SUCCESS! Received {len(candles)} candles."
                                        )

                                        # Data Table Preview
                                        with ui.expansion(
                                            "View Data Table", icon="table_chart"
                                        ).classes("w-full mt-2"):
                                            c_rows = [
                                                {
                                                    "ts": c[0],
                                                    "open": c[1],
                                                    "high": c[2],
                                                    "low": c[3],
                                                    "close": c[4],
                                                    "vol": c[5],
                                                }
                                                for c in candles[:20]
                                            ]
                                            ui.table(
                                                columns=[
                                                    {
                                                        "name": k,
                                                        "label": k.upper(),
                                                        "field": k,
                                                    }
                                                    for k in [
                                                        "ts",
                                                        "open",
                                                        "high",
                                                        "low",
                                                        "close",
                                                        "vol",
                                                    ]
                                                ],
                                                rows=c_rows,
                                                pagination=10,
                                            ).classes("w-full")
                                            if len(candles) > 20:
                                                ui.label("... and more").classes(
                                                    "text-xs text-gray-500"
                                                )

                                    else:
                                        log_view.push(
                                            "⚠️ Valid Reaponse but NO CANDLES found (No Volume?)"
                                        )
                                else:
                                    log_view.push(
                                        f"❌ Error {resp.status_code}: {resp.text}"
                                    )
                            except Exception as e:
                                log_view.push(f"💥 Exception: {str(e)}")

                    ui.button("Get the Loot", on_click=fetch_loot).props(
                        "color=green icon=download"
                    )

    # Render Step 4 if valid
    if state["step"] >= 4 and state["selected_contract"]:
        prepare_step4(state["selected_contract"])


def reset_state():
    global DRILL_DOWN_STATE
    DRILL_DOWN_STATE["step"] = 1
    DRILL_DOWN_STATE["contracts"] = []
    DRILL_DOWN_STATE["expiry"] = None
    DRILL_DOWN_STATE["selected_contract"] = None
    ui.notify("Drill Down Reset", type="info")
    # Use javascript reload to refresh page content fully
    ui.run_javascript("location.reload()")
