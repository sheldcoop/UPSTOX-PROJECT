from nicegui import ui
from ..common import Components

def render_page(state):
    Components.section_header('Live Positions', 'Manage open trades', 'pie_chart')
    
    pos_data = state.portfolio.get('positions', [])
    
    if not pos_data:
        with Components.card('items-center justify-center py-12'):
            ui.icon('inbox', size='4xl').classes('text-slate-700 mb-4')
            ui.label('No active positions').classes('text-xl text-slate-500')
    else:
        Components.data_table(
            columns=[
                {'name': 'symbol', 'label': 'Symbol', 'field': 'symbol', 'align': 'left'},
                {'name': 'qty', 'label': 'Quantity', 'field': 'qty'},
                {'name': 'ltp', 'label': 'LTP', 'field': 'ltp'},
                {'name': 'pnl', 'label': 'P&L', 'field': 'pnl', 'format': lambda val: f'₹{val}'}
            ],
            rows=pos_data
        )
