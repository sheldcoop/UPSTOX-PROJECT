from nicegui import ui
from ..common import Components
from pathlib import Path


def render_page(state):
    Components.section_header(
        "Market Guide",
        "Instrument Categories & Codes from Documentation",
        "library_books",
    )

    try:
        # Use correct path to the guide file
        guide_path = Path(__file__).parent.parent.parent / "docs" / "guides" / "MARKET_INSTRUMENTS_GUIDE.md"
        
        with open(guide_path, "r") as f:
            content = f.read()

        with Components.card():
            # render markdown with some custom styling for tables to ensure they look good in dark mode
            ui.markdown(content).classes(
                "prose prose-invert prose-slate max-w-none w-full"
            )
    except FileNotFoundError:
        with Components.card():
            ui.label(f"Error loading documentation: [Errno 2] No such file or directory: 'MARKET_INSTRUMENTS_GUIDE.md'").classes("text-red-400")
            ui.label(f"Expected location: docs/guides/MARKET_INSTRUMENTS_GUIDE.md").classes("text-yellow-400 mt-2")
    except Exception as e:
        with Components.card():
            ui.label(f"Error loading documentation: {str(e)}").classes("text-red-400")
