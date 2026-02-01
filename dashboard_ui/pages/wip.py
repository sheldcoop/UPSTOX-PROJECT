from nicegui import ui
from ..common import Components

def render_page(name: str):
    Components.section_header(name.replace('_', ' ').title(), 'Under Construction', 'construction')
    with Components.card('border-dashed border-2 border-slate-700 bg-transparent items-center justify-center py-20'):
        ui.spinner('dots', size='lg', color='indigo')
        ui.label('Module Loading...').classes('mt-4 text-slate-500')
