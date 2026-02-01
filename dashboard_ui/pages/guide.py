from nicegui import ui
from ..common import Components

def render_page(state):
    Components.section_header('Market Guide', 'Instrument Categories & Codes from Documentation', 'library_books')
    
    try:
        with open('MARKET_INSTRUMENTS_GUIDE.md', 'r') as f:
            content = f.read()
        
        with Components.card():
            # render markdown with some custom styling for tables to ensure they look good in dark mode
            ui.markdown(content).classes('prose prose-invert prose-slate max-w-none w-full')
    except Exception as e:
            with Components.card():
                ui.label(f'Error loading documentation: {str(e)}').classes('text-red-400')
