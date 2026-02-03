from nicegui import ui


def create_sidebar(show_page):
    drawer = ui.left_drawer(value=True).classes(
        "bg-slate-900 border-r border-slate-700 w-64 shadow-xl"
    )
    with drawer:
        with ui.column().classes("gap-0 h-full"):
            # Header
            ui.label("NAVIGATION").classes(
                "text-xs font-bold px-4 py-4 border-b border-slate-700 text-indigo-400 uppercase tracking-wider"
            )

            nav_items = [
                ("dashboard", "🏠 Dashboard"),
                ("positions", "📊 Positions"),
                ("options", "💱 Options Chain"),
                ("greeks", "📐 Greeks Dashboard"),
                ("strategy", "🛠️ Strategy Builder"),
                ("orderbook", "📚 Order Book Heatmap"),
                ("pnl", "💰 P&L Calculator"),
                ("maxpain", "🔥 Max Pain"),
                ("ivscanner", "📈 IV Scanner"),
                ("expiry", "🗓️ Expiry Calendar"),
                ("screener", "🔎 Stock Screener"),
                ("orders", "📝 Orders"),
                ("downloads", "⬇️ Data Downloads"),
                ("debug", "🛠️ Debug Panel"),
            ]

            for page_id, label in nav_items:

                def on_nav_click(p=page_id):
                    show_page(p)

                btn = ui.button(label, on_click=on_nav_click)
                btn.classes(
                    "w-full text-left px-4 py-3 hover:bg-blue-600 hover:text-white text-slate-300 font-medium rounded-lg mx-2 transition-colors"
                )

            ui.space()

            # Footer
            with ui.column().classes(
                "text-xs text-slate-500 px-4 py-4 border-t border-slate-800"
            ):
                ui.label("v1.0 Production")
                ui.label("Trading Platform")
