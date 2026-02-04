from nicegui import ui
from ..common import Components
import sys
from pathlib import Path
import asyncio

# Import Service
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.services.market_data.options_chain import OptionsChainService

service = OptionsChainService()


def render_page(state):
    Components.section_header(
        "Option Chain", "Professional Live Options Chain", "list_alt"
    )

    # State
    selected_symbol = {"val": "NIFTY"}
    selected_expiry = {"val": None}
    expiry_options = {"val": []}

    # --- Control Bar ---
    with ui.row().classes("w-full gap-4 items-center bg-slate-900 p-4 rounded mb-4"):
        # Symbol Selector
        ui.select(
            [
                "NIFTY",
                "BANKNIFTY",
                "FINNIFTY",
                "RELIANCE",
                "HDFCBANK",
                "INFY",
                "TCS",
                "SBIN",
            ],
            label="Instrument",
            value=selected_symbol["val"],
            on_change=lambda e: update_expiries(e.value),
        ).props("outlined dense dark options-dense").classes("w-40")

        # Expiry Selector
        expiry_select = (
            ui.select(
                expiry_options["val"], label="Expiry", value=selected_expiry["val"]
            )
            .props("outlined dense dark options-dense")
            .classes("w-40")
        )

        # Refresh Button
        ui.button(icon="refresh", on_click=lambda: load_chain()).props(
            "flat round dense"
        ).tooltip("Refresh Data")

        # Market Status
        with ui.row().classes("ml-auto items-center"):
            # Only checking market open status for display
            is_open, msg = service.is_market_open()
            color = "green" if is_open else "red"
            ui.icon("fiber_manual_record", color=color).classes("text-xs")
            ui.label(msg).classes("text-xs text-slate-400")

    # --- Chain Container ---
    chain_container = ui.column().classes("w-full overflow-auto")

    # --- Loading Logic ---
    async def update_expiries(symbol):
        selected_symbol["val"] = symbol
        ui.notify(f"Fetching expiries for {symbol}...", type="info")

        dates = await asyncio.to_thread(
            service.get_expiry_dates, service._get_instrument_key(symbol)
        )
        expiry_options["val"] = dates
        expiry_select.options = dates

        if dates:
            selected_expiry["val"] = dates[0]
            expiry_select.value = dates[0]
            await load_chain()
        else:
            selected_expiry["val"] = None
            expiry_select.value = None
            ui.notify("No active contracts found", type="warning")

    async def load_chain():
        with chain_container:
            chain_container.clear()
            ui.spinner("dots", size="lg").classes("mx-auto my-10 text-indigo-500")

        sym = selected_symbol["val"]
        exp = selected_expiry["val"]

        data = await asyncio.to_thread(service.get_option_chain, sym, exp)

        chain_container.clear()
        with chain_container:
            render_chain_table(data)

    def render_chain_table(data):
        if not data or not data.get("strikes"):
            ui.label("No Data Available").classes("text-red-400 font-bold mx-auto")
            return

        strikes = data["strikes"]
        spot = data.get("underlying_price", 0)

        # Spot Price Banner
        with ui.row().classes("w-full justify-center py-2 bg-slate-800 rounded mb-2"):
            ui.label(f"Spot Price: {spot}").classes("text-xl font-bold text-yellow-400")

        # Table Header
        # Columns: [Calls] OI, Vol, LTP | Strike | [Puts] LTP, Vol, OI
        cols = "1fr 1fr 1fr 100px 1fr 1fr 1fr"

        with ui.grid(columns=cols).classes(
            "w-full gap-1 text-center font-mono text-xs bg-slate-900 p-2 rounded-t sticky top-0 z-10"
        ):
            ui.label("OI (Lakhs)").classes("text-slate-400")
            ui.label("Volume").classes("text-slate-400")
            ui.label("LTP").classes("text-green-400 font-bold")
            ui.label("STRIKE").classes("text-white font-bold bg-slate-700 rounded px-2")
            ui.label("LTP").classes("text-red-400 font-bold")
            ui.label("Volume").classes("text-slate-400")
            ui.label("OI (Lakhs)").classes("text-slate-400")

        # Rows
        with ui.grid(columns=cols).classes(
            "w-full gap-y-1 gap-x-0 items-center text-center font-mono text-sm"
        ):
            for s in strikes:
                strike_price = s["strike"]

                # Check ATM proximity for highlighting
                is_atm = abs(strike_price - spot) < (spot * 0.005)
                bg_class = "bg-yellow-900/20" if is_atm else "hover:bg-slate-800/50"

                # Call Data
                c = s["call"]
                c_ltp = c.get("ltp") or 0
                c_vol = c.get("volume") or 0
                c_oi = (c.get("oi") or 0) / 100000

                # Put Data
                p = s["put"]
                p_ltp = p.get("ltp") or 0
                p_vol = p.get("volume") or 0
                p_oi = (p.get("oi") or 0) / 100000

                # Render Row
                with ui.element("div").classes(f"contents {bg_class}"):
                    # CALLS side
                    ui.label(f"{c_oi:.2f}").classes("text-slate-300")
                    ui.label(f"{c_vol}").classes("text-slate-400 text-xs")
                    ui.label(f"{c_ltp}").classes("text-green-400 font-bold")

                    # STRIKE (Center)
                    ui.label(f"{strike_price}").classes(
                        "font-bold bg-slate-800 py-1 text-white border-x border-slate-700"
                    )

                    # PUTS side
                    ui.label(f"{p_ltp}").classes("text-red-400 font-bold")
                    ui.label(f"{p_vol}").classes("text-slate-400 text-xs")
                    ui.label(f"{p_oi:.2f}").classes("text-slate-300")

    # Initial Load
    # We trigger expiry fetch if symbol is present
    if not selected_expiry["val"]:
        ui.timer(0.1, lambda: update_expiries(selected_symbol["val"]), once=True)
