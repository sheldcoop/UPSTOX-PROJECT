from nicegui import ui
from ..common import Components


def render_page(state):
    Components.section_header(
        "F&O Analysis", "Derivatives Data & Option Chain", "timeline"
    )

    with ui.row().classes("w-full gap-6 items-start"):
        # Selection Panel
        with ui.column().classes("w-1/4 gap-4"):
            with Components.card():
                ui.label("Select Underlying").classes("text-lg font-bold mb-4")

                # Async Search for underlying
                async def on_underlying_input(e):
                    val = e.args
                    if not val:
                        return
                    # For FNO, even 1 char is fine since list is small, but 2 is safer
                    opts = await state.search_instruments("FNO_UNDERLYING", val)
                    selected_script.options = opts
                    selected_script.update()

                selected_script = (
                    ui.select(options=[], label="Script", with_input=True)
                    .props(
                        'outlined dense dark use-input behavior="menu" placeholder="Type script..."'
                    )
                    .classes("w-full")
                )

                selected_script.on("input-value", on_underlying_input)

                ui.label("Contracts").classes("text-sm font-bold text-slate-400 mt-4")
                contract_list = ui.column().classes(
                    "w-full gap-1 max-h-[400px] overflow-y-auto"
                )

                async def load_contracts(e):
                    script = e.value
                    if not script:
                        return

                    contract_list.clear()  # Clear immediately

                    with contract_list:
                        ui.label(f"Loading contracts for {script}...").classes(
                            "text-xs animate-pulse"
                        )
                        # Async loading
                        stats = await state.get_fno_contracts(script)

                        contract_list.clear()  # Clear loading msg
                        if stats:
                            for type_, count, next_exp in stats:
                                with ui.row().classes(
                                    "w-full justify-between bg-slate-800 p-2 rounded"
                                ):
                                    ui.label(
                                        f"Option {type_}"
                                        if type_ in ["CE", "PE"]
                                        else "Futures"
                                    ).classes("text-sm font-bold")
                                    ui.label(f"{count} contracts").classes(
                                        "text-xs text-slate-400"
                                    )
                        else:
                            ui.label("No active contracts").classes(
                                "text-xs text-slate-500"
                            )

                selected_script.on("update:model-value", load_contracts)

        # Main Content Area (Option Chain Placeholder)
        with ui.column().classes("w-3/4"):
            with Components.card("h-full min-h-[500px] items-center justify-center"):
                ui.icon("analytics", size="5xl").classes("text-slate-700 mb-4")
                ui.label("Select a script to view Chain").classes(
                    "text-xl text-slate-500 font-medium"
                )
                ui.label("Real-time Option Chain & Greeks coming soon").classes(
                    "text-sm text-slate-600"
                )
