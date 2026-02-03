from nicegui import ui, run
from ..common import Components
import sys
from pathlib import Path
import asyncio

# Import Upstox API (Add to path if needed)
sys.path.append(str(Path(__file__).parent.parent.parent))
from scripts.upstox_live_api import get_upstox_api

# Initialize API
api = get_upstox_api()


def render_page(state):
    Components.section_header(
        "Live Data", "Real-time market quotes & analytics", "ssid_chart"
    )

    # --- State for this page ---
    selected_symbol = {"val": None}

    # --- UI Container ---
    content_container = ui.column().classes("w-full mt-6 gap-6")

    async def fetch_quote(symbol):
        if not symbol:
            return

        # UI Feedback
        ui.notify(f"Fetching live data for {symbol}...", type="info")
        content_container.clear()

        with content_container:
            ui.spinner("dots", size="lg").classes("mx-auto text-indigo-500")

        # Background Fetch
        try:
            quote = await run.io_bound(api.get_market_quote, symbol)

            content_container.clear()
            with content_container:
                if not quote:
                    ui.label(f"No data found for {symbol}").classes(
                        "text-red-400 font-bold"
                    )
                    return

                # --- DEBUG: Raw Data Toggle ---
                # with ui.expansion('Raw JSON Response'):
                #     ui.json_editor({'content': {'json': quote}}).classes('h-64')

                # --- 1. Header Card (Price & Change) ---
                with Components.card():
                    with ui.row().classes("w-full items-center justify-between"):
                        # Symbol Name
                        with ui.column().classes("gap-0"):
                            ui.label(symbol).classes(
                                "text-2xl font-black text-white tracking-tighter"
                            )
                            ui.label(quote.get("timestamp", "N/A")).classes(
                                "text-xs text-slate-500 font-mono"
                            )

                        # Price & Change
                        ltp = quote.get("last_price", 0)
                        change = quote.get("net_change", 0)
                        p_change = (
                            (change / (ltp - change)) * 100 if ltp and change else 0.0
                        )

                        color = "text-green-400" if change >= 0 else "text-red-400"
                        arrow = "▲" if change >= 0 else "▼"

                        with ui.column().classes("items-end gap-0"):
                            ui.label(f"₹{ltp:,.2f}").classes(
                                f"text-4xl font-mono font-bold {color}"
                            )
                            ui.label(
                                f"{arrow} {change:+.2f} ({p_change:+.2f}%)"
                            ).classes(f"text-sm font-bold {color}")

                # --- 2. Analytics Grid (The User's "Important" Fields) ---
                with ui.grid(columns=4).classes("w-full gap-4"):
                    # Open Interest
                    with Components.card():
                        ui.label("Open Interest (OI)").classes(
                            "text-slate-400 text-xs uppercase font-bold"
                        )
                        oi = quote.get("oi", 0)
                        ui.label(f"{int(oi):,}").classes(
                            "text-xl text-indigo-400 font-mono font-bold mt-1"
                        )
                        ui.label("Contracts").classes("text-xs text-slate-600")

                    # Volume
                    with Components.card():
                        ui.label("Volume").classes(
                            "text-slate-400 text-xs uppercase font-bold"
                        )
                        vol = quote.get("volume", 0)
                        ui.label(f"{int(vol):,}").classes(
                            "text-xl text-blue-400 font-mono font-bold mt-1"
                        )

                    # Avg Price (VWAPish)
                    with Components.card():
                        ui.label("Avg. Price").classes(
                            "text-slate-400 text-xs uppercase font-bold"
                        )
                        avg = quote.get("average_price", 0)
                        ui.label(f"₹{avg:,.2f}").classes(
                            "text-xl text-orange-400 font-mono font-bold mt-1"
                        )

                    # Total Buy/Sell Pressure (Ratio)
                    with Components.card():
                        buy_q = quote.get("total_buy_quantity", 0)
                        sell_q = quote.get("total_sell_quantity", 0)
                        total = buy_q + sell_q if (buy_q + sell_q) > 0 else 1
                        ratio = buy_q / total

                        ui.label("Buy/Sell Pressure").classes(
                            "text-slate-400 text-xs uppercase font-bold"
                        )
                        with ui.row().classes("w-full items-center gap-2 mt-2"):
                            ui.linear_progress(
                                value=ratio,
                                size="10px",
                                color="green",
                                track_color="red",
                            ).classes("rounded-full")
                        with ui.row().classes(
                            "w-full justify-between text-xs font-mono mt-1"
                        ):
                            ui.label(f"{buy_q/1000:.1f}k").classes("text-green-500")
                            ui.label(f"{sell_q/1000:.1f}k").classes("text-red-500")

                # --- 3. OHLC & Range ---
                with Components.card():
                    ohlc = quote.get("ohlc", {})
                    op, hi, lo, cl = (
                        ohlc.get("open", 0),
                        ohlc.get("high", 0),
                        ohlc.get("low", 0),
                        ohlc.get("close", 0),
                    )

                    ui.label("Today's Session").classes(
                        "text-md font-bold text-white mb-4"
                    )
                    with ui.row().classes(
                        "w-full justify-between text-center divide-x divide-slate-800"
                    ):
                        for lbl, val in [
                            ("Open", op),
                            ("High", hi),
                            ("Low", lo),
                            ("Prev. Close", cl),
                        ]:
                            with ui.column().classes("px-4 flex-1"):
                                ui.label(lbl).classes(
                                    "text-xs text-slate-500 uppercase"
                                )
                                ui.label(f"{val:,.2f}").classes(
                                    "text-lg font-mono text-slate-200"
                                )

                # --- 4. Market Depth (Order Book) ---
                depth = quote.get("depth", {})
                bids = depth.get("buy", [])
                asks = depth.get("sell", [])

                with ui.grid(columns=2).classes("w-full gap-4"):
                    # Bids Table
                    with Components.card():
                        ui.label("Bid Orders (Buy)").classes(
                            "text-green-400 font-bold mb-2"
                        )
                        with ui.element("table").classes("w-full text-right text-sm"):
                            with ui.element("thead").classes(
                                "text-slate-500 text-xs border-b border-slate-700"
                            ):
                                with ui.element("tr"):
                                    ui.element("th").text("Qty").classes("pb-2 pr-4")
                                    ui.element("th").text("Price").classes(
                                        "pb-2 text-green-500"
                                    )
                            with ui.element("tbody"):
                                for b in bids:
                                    if b.get("quantity", 0) == 0:
                                        continue
                                    with ui.element("tr").classes(
                                        "border-b border-slate-800/50"
                                    ):
                                        ui.element("td").text(
                                            f"{b['quantity']:,}"
                                        ).classes("py-1 pr-4 font-mono text-slate-300")
                                        ui.element("td").text(
                                            f"{b['price']:.2f}"
                                        ).classes("py-1 text-green-400 font-bold")

                    # Asks Table
                    with Components.card():
                        ui.label("Ask Orders (Sell)").classes(
                            "text-red-400 font-bold mb-2"
                        )
                        with ui.element("table").classes("w-full text-right text-sm"):
                            with ui.element("thead").classes(
                                "text-slate-500 text-xs border-b border-slate-700"
                            ):
                                with ui.element("tr"):
                                    ui.element("th").text("Price").classes(
                                        "pb-2 text-red-500"
                                    )
                                    ui.element("th").text("Qty").classes("pb-2")
                            with ui.element("tbody"):
                                for a in asks:
                                    if a.get("quantity", 0) == 0:
                                        continue
                                    with ui.element("tr").classes(
                                        "border-b border-slate-800/50"
                                    ):
                                        ui.element("td").text(
                                            f"{a['price']:.2f}"
                                        ).classes("py-1 text-red-400 font-bold")
                                        ui.element("td").text(
                                            f"{a['quantity']:,}"
                                        ).classes("py-1 font-mono text-slate-300")

        except Exception as e:
            ui.notify(f"Error: {str(e)}", type="negative")
            print(f"Fetch Error: {e}")

    # --- Search Bar (Server Side) ---
    async def on_search_input(e):
        val = e.args
        if len(val) < 2:
            return
        opts = await state.search_instruments(
            "NSE_EQ", val
        )  # Default to NSE_EQ for now
        # Mix in Indices if searching NIFTY
        if "NIFTY" in val.upper():
            opts = ["NIFTY", "BANKNIFTY"] + opts

        search_box.options = opts
        search_box.update()

    async def on_select(e):
        sym = e.value
        if sym:
            await fetch_quote(sym)

    with ui.row().classes("w-full max-w-xl"):
        search_box = (
            ui.select(
                options=[], label="Search Symbol", with_input=True, on_change=on_select
            )
            .props(
                'outlined dark dense use-input hide-selected fill-input input-debounce="300" placeholder="e.g. RELIANCE, NIFTY..."'
            )
            .classes("w-full")
        )

        search_box.on("input-value", on_search_input)
