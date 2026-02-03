from nicegui import ui
from ..common import Components
import sys
from pathlib import Path
import asyncio

# Import Service
sys.path.append(str(Path(__file__).parent.parent.parent))
from scripts.options_chain_service import OptionsChainService

service = OptionsChainService()


def render_page(state):
    Components.section_header(
        "Option Greeks",
        "Deep Dive Analysis (Delta, Theta, Gamma, Vega)",
        "data_exploration",
    )

    # State
    current_symbol = {"val": "NIFTY"}
    current_strikes = {"val": []}  # List of instrument keys
    greeks_data = {"val": {}}

    with ui.row().classes("w-full gap-4"):
        # Input for manual lookup for now, simpler than full expiry flow again
        ui.input(
            label="Symbol", on_change=lambda e: current_symbol.update({"val": e.value})
        ).props("outlined dense dark").classes("w-40").bind_value(current_symbol, "val")

        async def fetch_greeks():
            sym = current_symbol["val"]
            # We need instrument keys.
            # Strategy: Get Option Chain for nearest expiry, pick top 10 ATM strikes, and fetch greeks for them.
            ui.notify(f"Analyzing Greeks for {sym}...", type="info")

            # 1. Get Chain (Standard V2 to get keys)
            # Default to nearest
            chain = await asyncio.to_thread(service.get_option_chain, sym)
            strikes = chain.get("strikes", [])
            spot = chain.get("underlying_price", 0)

            if not strikes:
                ui.notify("No strike data found", type="warning")
                return

            # 2. Filter ATM +/- 5
            # Sort by proximity to spot
            strikes.sort(key=lambda x: abs(x["strike"] - spot))
            selected = strikes[:10]  # Top 10 closest
            selected.sort(key=lambda x: x["strike"])  # Sort back by strike for display

            # Check if V2 already has greeks (it usually does).
            # The user requested V3 specifically.
            # Let's collect V3 keys.
            keys_to_fetch = []
            key_map = {}  # key -> description

            for s in selected:
                ck = s["call"]["instrument_key"]
                pk = s["put"]["instrument_key"]
                if ck:
                    keys_to_fetch.append(ck)
                    key_map[ck] = f"{s['strike']} CE"
                if pk:
                    keys_to_fetch.append(pk)
                    key_map[pk] = f"{s['strike']} PE"

            # 3. Call V3 API
            v3_data = await asyncio.to_thread(service.get_option_greeks, keys_to_fetch)

            # Render
            greeks_container.clear()
            with greeks_container:
                if not v3_data:
                    ui.label(
                        "V3 API returned no data. Using V2 Fallback if available."
                    ).classes("text-orange-400")
                    # Fallback to display V2 logic?? No, user wants V3.

                # Create Cards for each strike
                for s in selected:
                    with ui.card().classes("w-full bg-slate-800 p-2"):
                        ui.label(f"Strike: {s['strike']}").classes(
                            "text-lg font-bold text-center w-full mb-2 bg-slate-900 rounded"
                        )

                        cols = "1fr 1fr 1fr 1fr 1fr"
                        with ui.grid(columns=cols).classes(
                            "w-full text-center text-xs gap-2"
                        ):
                            ui.label("Type").classes("font-bold text-slate-400")
                            ui.label("Delta").classes("text-blue-400")
                            ui.label("Theta").classes("text-yellow-400")
                            ui.label("Gamma").classes("text-purple-400")
                            ui.label("Vega").classes("text-pink-400")

                            # CE Row
                            ck = s["call"]["instrument_key"]
                            cd = v3_data.get(
                                ck
                            )  # Keys might be formatted differently in response?
                            # Response format in doc: "NSE_FO:NIFTY..." : { ... }
                            # But we passed instrument_key. Let's see how it returns.
                            # Usually response dict keys match the requested instrument keys OR the trading symbol.
                            # We will try exact match or finding it.

                            # Heuristic match
                            c_greek = cd or {}

                            ui.label("CE").classes("font-bold text-green-400")
                            ui.label(f"{c_greek.get('delta', '-')}")
                            ui.label(f"{c_greek.get('theta', '-')}")
                            ui.label(f"{c_greek.get('gamma', '-')}")
                            ui.label(f"{c_greek.get('vega', '-')}")

                            # PE Row
                            pk = s["put"]["instrument_key"]
                            pd = v3_data.get(pk) or {}

                            ui.label("PE").classes("font-bold text-red-400")
                            ui.label(f"{pd.get('delta', '-')}")
                            ui.label(f"{pd.get('theta', '-')}")
                            ui.label(f"{pd.get('gamma', '-')}")
                            ui.label(f"{pd.get('vega', '-')}")

        ui.button("Analyze Greeks (ATM)", on_click=fetch_greeks).classes(
            "bg-purple-600"
        )

    greeks_container = ui.column().classes("w-full mt-4 gap-2")
