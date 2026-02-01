from nicegui import ui
from datetime import datetime, timedelta
from ..common import Components
from ..state import async_post

def render_page(state):
    Components.section_header('Data Center', 'Historical market data downloader', 'cloud_download')
    
    with ui.row().classes('w-full gap-6 items-start'):
        # Left Column: Controls
        with ui.column().classes('flex-[2] gap-6'):
            with Components.card():
                with ui.row().classes('w-full justify-between items-center mb-4'):
                    ui.label('Instrument Selection').classes('text-lg font-bold')
                    ui.icon('search', size='sm').classes('text-slate-500')
                
                # Chip container (Moved to top for visibility)
                chip_container = ui.row().classes('gap-2 mb-4 min-h-[40px] w-full p-2 bg-slate-950/30 rounded border border-slate-800')
                
                def clear_all_symbols():
                    state.selected_symbols.clear()
                    render_chips()

                def render_chips():
                    chip_container.clear()
                    with chip_container:
                        if not state.selected_symbols:
                            ui.label('No symbols selected').classes('text-xs text-slate-500 italic')
                        else:
                            # Add Clear All button if strict selection exists
                            ui.button(icon='delete_sweep', on_click=clear_all_symbols).props('flat dense round color=red').tooltip('Clear all selections')
                            
                        for s in state.selected_symbols:
                            ui.chip(s, removable=True, on_remove=lambda sym=s: remove_symbol(sym)) \
                                .classes('bg-indigo-900/50 border border-indigo-500/30 text-xs')

                def add_symbol(val):
                    if not val: return
                    val = val.upper().strip()
                    if val and val not in state.selected_symbols:
                        state.selected_symbols.append(val)
                        render_chips()

                def remove_symbol(sym):
                    if sym in state.selected_symbols:
                        state.selected_symbols.remove(sym)
                        render_chips()
                
                # Tabs for Universe Selection
                with ui.tabs().classes('w-full text-slate-400 border-b border-slate-800') as tabs:
                    t_nse = ui.tab('NSE EQ').classes('text-xs')
                    t_bse = ui.tab('BSE EQ').classes('text-xs')
                    t_sme = ui.tab('SME').classes('text-xs')
                    t_debt = ui.tab('Debt').classes('text-xs')
                    t_gold = ui.tab('Gold').classes('text-xs')
                    t_indices = ui.tab('Indices').classes('text-xs')
                    t_etf = ui.tab('ETFs').classes('text-xs')

                # State for tracking user input (Robustness Fix)
                pending_inputs = {} 
                last_focused_category = {'val': 'NSE_EQ'} # Default to first tab

                with ui.tab_panels(tabs, value=t_nse).classes('w-full bg-transparent mt-2'):
                    
                    # Helper for search boxes
                    def instrument_search_box(category, label):
                        # PERFORMANCE OPTIMIZATION & ROBUSTNESS: 
                        # Use server-side filtering and track pending inputs.
                        
                        async def on_input(e):
                            val = e.args
                            # ROBUSTNESS: Capture typed text even if not selected
                            pending_inputs[category] = val
                            
                            if not val: return
                            if len(val) < 2: return 
                            
                            opts = await state.search_instruments(category, val)
                            sel.options = opts
                            sel.update()

                        sel = ui.select(
                            options=[], 
                            label=label,
                            with_input=True,
                            clearable=True,
                            new_value_mode='add-unique' 
                        ).props('outlined dense dark use-input hide-selected fill-input input-debounce="300" behavior="menu" placeholder="Type to search (e.g. REL)..."').classes('w-full')
                        
                        # Handle input typing
                        sel.on('input-value', on_input)
                        
                        # Track Focus for "Smart Selection"
                        # We use on('focus') via HTML props since nicegui select doesn't expose it directly conveniently in python events sometimes, 
                        # but actually we can just update last_focused on input or click.
                        # Simplest is updating on input.
                        
                        def on_select(e):
                            if e.args:
                                add_symbol(e.args)
                                sel.set_value(None)
                                pending_inputs[category] = '' # Clear pending on success
                                
                        sel.on('update:model-value', on_select)
                        
                        # Set active category on interaction
                        def set_active():
                            last_focused_category['val'] = category
                        
                        sel.on('click', set_active)
                        sel.on('focus', set_active)

                        # Fallback "Add" button
                        with sel.add_slot('append'):
                            ui.button(icon='add', on_click=lambda: (add_symbol(sel.value), sel.set_value(None))).props('flat dense round color=indigo')
                            
                        return sel

                    with ui.tab_panel(t_nse).classes('p-0'):
                        instrument_search_box('NSE_EQ', 'Search NSE Stocks')

                    with ui.tab_panel(t_bse).classes('p-0'):
                        instrument_search_box('BSE_EQ', 'Search BSE Stocks')

                    with ui.tab_panel(t_sme).classes('p-0'):
                        instrument_search_box('SME_EQ', 'Search SME Stocks (NSE/BSE)')
                        
                    with ui.tab_panel(t_debt).classes('p-0'):
                        instrument_search_box('DEBT', 'Search Bonds & Fixed Income')
                        
                    with ui.tab_panel(t_gold).classes('p-0'):
                        instrument_search_box('GOLD', 'Search Gold Bonds (SGB)')
                        
                    with ui.tab_panel(t_indices).classes('p-0'):
                        instrument_search_box('INDICES', 'Search Market Indices')
                        
                    with ui.tab_panel(t_etf).classes('p-0'):
                        instrument_search_box('ETFs', 'Search Exchange Traded Funds')

                render_chips()
                
                # Date Selection
                ui.label('Time Period').classes('text-sm font-bold text-slate-400 mt-4 mb-2')
                with ui.row().classes('w-full gap-4'):
                    d_from = Components.date_input('Start From', value=(datetime.now() - timedelta(30)).strftime('%Y-%m-%d'))
                    d_to = Components.date_input('End To', value=datetime.now().strftime('%Y-%m-%d'))
                
                # Quick Ranges
                with ui.row().classes('gap-2 mt-2'):
                    def set_range(days: int):
                        d_to.value = datetime.now().strftime('%Y-%m-%d')
                        d_from.value = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                    
                    for label, days in [('1W', 7), ('1M', 30), ('3M', 90), ('YTD', (datetime.now() - datetime(datetime.now().year, 1, 1)).days)]:
                        ui.chip(label, on_click=lambda d=days: set_range(d)).props('clickable dense square outline icon=calendar_today').classes('hover:bg-indigo-500 hover:text-white text-xs')

                # Data Granularity
                ui.label('Data Granularity').classes('text-sm font-bold text-slate-400 mt-4 mb-2')
                interval_select = ui.select(
                    options={
                        '1m': '1 Minute',
                        '5m': '5 Minutes',
                        '15m': '15 Minutes',
                        '30m': '30 Minutes',
                        '1h': '1 Hour',
                        '1d': 'Daily (EOD)',
                        'week': 'Weekly',
                        'month': 'Monthly'
                    },
                    value='1d',
                    label='Candle Interval'
                ).props('outlined dense dark options-dense').classes('w-full')

                # Options
                ui.label('Output Options').classes('text-sm font-bold text-slate-400 mt-4 mb-2')
                with ui.column().classes('gap-2'):
                        save_db_switch = ui.switch('Save to Database', value=True).props('color=green dense dark')
                        with ui.row().classes('items-center gap-4'):
                            download_local_switch = ui.switch('Download Local File', value=False).props('color=blue dense dark')
                            file_format = ui.select(['parquet', 'csv'], value='parquet', label='Format').props('dense outlined dark options-dense').classes('w-32').bind_visibility_from(download_local_switch, 'value')

                status_label = ui.label('').classes('text-sm mt-2')

                async def run_download():
                    # ROBUSTNESS: Check for pending input if no selection
                    if not state.selected_symbols:
                        # Check if user typed something but didn't hit enter
                        cat = last_focused_category['val']
                        pending_text = pending_inputs.get(cat, '').strip()
                        
                        if pending_text and len(pending_text) > 1:
                            # Auto-add the pending text
                            add_symbol(pending_text)
                            ui.notify(f"Auto-selected '{pending_text}'", type='info')
                            # Continue to download...
                        else:
                            ui.notify('Select at least one symbol', type='warning')
                            return
                    
                    if not save_db_switch.value and not download_local_switch.value:
                        ui.notify('Select at least one output option', type='warning')
                        return
                    
                    status_label.text = '⏳ Requesting data...'
                    
                    # Determine export format
                    fmt = file_format.value if download_local_switch.value else None

                    res = await async_post('/api/download/stocks', {
                        "symbols": state.selected_symbols,
                        "start_date": d_from.value,
                        "end_date": d_to.value,
                        "interval": interval_select.value,
                        "save_db": save_db_switch.value,
                        "export_format": fmt
                    })
                    
                    if 'error' in res:
                        status_label.text = '❌ Failed'
                        status_label.classes('text-red-400')
                    else:
                        status_label.text = '✅ Complete'
                        status_label.classes('text-green-400')
                        
                        # Trigger Download if requested
                        if download_local_switch.value and res.get('filepath'):
                            ui.download(res['filepath'])
                            ui.notify('File download started', type='positive')
                            
                        # Clear symbols after successful request (Enhancement for User State)
                        clear_all_symbols()
                            
                        await refresh_dl_list()

                ui.button('Download Data', icon='download', on_click=run_download).classes('w-full mt-4 bg-indigo-600 hover:bg-indigo-500')

        # Right Column: History
        with ui.column().classes('flex-[3]'):
            with Components.card():
                ui.label('Recent Files').classes('text-lg font-bold mb-4')
                history_list = ui.column().classes('w-full gap-2')
                
                async def refresh_dl_list():
                    hist = await state.fetch_download_history()
                    history_list.clear()
                    with history_list:
                        if not hist.get('files'):
                            ui.label('No files found').classes('text-slate-500 italic')
                        for f in hist['files'][:8]:
                            with ui.row().classes('w-full justify-between items-center bg-slate-800/30 p-3 rounded hover:bg-slate-800/50 transition'):
                                with ui.row().classes('gap-3 items-center'):
                                    ui.icon('description', size='sm').classes('text-indigo-400')
                                    ui.label(f['filename']).classes('font-mono text-sm')
                                ui.label(f"{f['size']/1024:.0f} KB").classes('text-xs text-slate-500')

                # Init Load
                ui.timer(0.1, refresh_dl_list, once=True)
