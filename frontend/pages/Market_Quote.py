"""
Market Quote / Super Screener
Allows filtering by Segment, Sector, Industry, and Index.
"""
from nicegui import ui, run
from ..common import Components
import sqlite3
from pathlib import Path
import pandas as pd
import asyncio

DB_PATH = Path("market_data.db").absolute()

def get_filter_options(column):
    """Get unique values for a column (sector, industry)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f"SELECT DISTINCT {column} FROM instrument_master WHERE {column} IS NOT NULL ORDER BY {column}")
        options = [row[0] for row in cursor.fetchall()]
        conn.close()
        return options
    except Exception as e:
        print(f"Error fetching {column}: {e}")
        return []

def get_indices():
    """Get list of available indices"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT index_name FROM index_mapping ORDER BY index_name")
        indices = [row[0] for row in cursor.fetchall()]
        conn.close()
        return indices
    except Exception as e:
        print(f"Error fetching indices: {e}")
        return []

def get_screener_data(segment=None, sector=None, industry=None, index=None, search=None, limit=1000):
    """Fetch filtered data joined with latest quotes if available"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Base Query
        query = """
            SELECT 
                im.trading_symbol,
                im.name,
                im.sector,
                im.industry,
                im.segment,
                im.instrument_key,
                q.close as last_price,
                q.volume,
                (q.close - q.open) as net_change,
                q.open, q.high, q.low,
                q.bid_price_1, q.bid_qty_1, q.ask_price_1, q.ask_qty_1,
                q.bid_price_2, q.bid_qty_2, q.ask_price_2, q.ask_qty_2,
                q.bid_price_3, q.bid_qty_3, q.ask_price_3, q.ask_qty_3,
                q.bid_price_4, q.bid_qty_4, q.ask_price_4, q.ask_qty_4,
                q.bid_price_5, q.bid_qty_5, q.ask_price_5, q.ask_qty_5
            FROM instrument_master im
            LEFT JOIN market_quota_nse500_data q ON im.instrument_key = q.instrument_key
        """
        
        # Dynamic Join for Index
        if index and index != "All":
            query += " JOIN index_mapping idx ON im.instrument_key = idx.instrument_key"
            
        query += " WHERE im.is_active = 1"
        params = []
        
        if segment:
            query += " AND im.segment = ?"
            params.append(segment)
            
        # Index Filter
        if index and index != "All":
            query += " AND idx.index_name = ?"
            params.append(index)

        if sector and sector != "All":
            query += " AND im.sector = ?"
            params.append(sector)
            
        if industry and industry != "All":
            query += " AND im.industry = ?"
            params.append(industry)
            
        if search:
            query += " AND (im.trading_symbol LIKE ? OR im.name LIKE ?)"
            match = f"%{search}%"
            params.extend([match, match])
            
        query += " ORDER BY im.trading_symbol LIMIT ?"
        params.append(limit)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        # DEBUG: Print to terminal
        print(f"DEBUG: Fetched {len(df)} rows.")
        if not df.empty:
            print(f"DEBUG: Sample Row: {df.iloc[0].to_dict()}")
            
        return df.to_dict('records')
        
    except Exception as e:
        print(f"Error fetching screener data: {e}")
        import traceback
        traceback.print_exc()
        return []

def render_page(state):
    Components.section_header(
        "Market Quote", "Advanced Screener & Multi-Factor Filter", "filter_alt"
    )
    
    # --- State ---
    filters = {
        'segment': 'NSE_EQ',
        'index': 'All',
        'sector': 'All',
        'industry': 'All',
        'search': ''
    }
    
    sectors = ["All"] + get_filter_options("sector")
    # Initial industries (will update dynamically)
    industries = ["All"] + get_filter_options("industry") 
    indices = ["All"] + get_indices()
    
    # --- UI ---
    with Components.card():
        with ui.row().classes("w-full items-end gap-4"):
            
            # Segment
            ui.select(
                options=["NSE_EQ", "NSE_INDEX", "NSE_FO"],
                value=filters['segment'],
                label="Segment",
                on_change=lambda e: update_table()
            ).classes("w-32").bind_value(filters, 'segment')
            
            # Index (New)
            ui.select(
                options=indices,
                value=filters['index'],
                label="Index / Theme",
                on_change=lambda e: update_table()
            ).classes("w-48").bind_value(filters, 'index')
            
            # Sector
            sector_select = ui.select(
                options=sectors,
                value=filters['sector'],
                label="Sector",
                on_change=lambda e: update_table()
            ).classes("w-48").bind_value(filters, 'sector')
            
            # Industry
            industry_select = ui.select(
                options=industries,
                value=filters['industry'],
                label="Industry",
                on_change=lambda e: update_table()
            ).classes("w-48").bind_value(filters, 'industry')
            
            # Search
            search_input = ui.input(
                label="Search Symbol",
                placeholder="e.g. TATA",
                on_change=lambda e: update_table()
            ).classes("flex-grow").bind_value(filters, 'search')
            
            ui.button(icon="refresh", on_click=lambda: update_table()).props("flat round")

    # --- Detail Dialog ---
    with ui.dialog() as dialog, ui.card():
        ui.label().bind_text_from(dialog, 'title').classes("text-xl font-bold mb-4")
        
        # Depth Table Container
        depth_container = ui.column().classes("w-full")
        
    def show_details(row):
        dialog.title = f"Market Depth: {row['trading_symbol']}"
        depth_container.clear()
        
        with depth_container:
            # Stats
            with ui.row().classes("w-full justify-between mb-4"):
                ui.label(f"Price: ₹{row.get('last_price', 0)}").classes("text-lg font-mono")
                ui.label(f"Vol: {row.get('volume', 0):,}").classes("text-lg font-mono text-slate-400")

            # Bid/Ask Table
            with ui.grid(columns=2).classes("w-full gap-4"):
                # Bids (Buy)
                with ui.column():
                    ui.label("BID (Buy)").classes("font-bold text-green-400")
                    with ui.row().classes("w-full justify-between text-xs text-slate-500 border-b"):
                        ui.label("Qty")
                        ui.label("Price")
                    
                    for i in range(1, 6):
                        price = row.get(f'bid_price_{i}', 0)
                        qty = row.get(f'bid_qty_{i}', 0)
                        if price:
                            with ui.row().classes("w-full justify-between font-mono text-sm"):
                                ui.label(f"{qty:,}")
                                ui.label(f"{price:.2f}").classes("text-green-300")

                # Asks (Sell)
                with ui.column():
                    ui.label("ASK (Sell)").classes("font-bold text-red-400")
                    with ui.row().classes("w-full justify-between text-xs text-slate-500 border-b"):
                        ui.label("Price")
                        ui.label("Qty")
                        
                    for i in range(1, 6):
                        price = row.get(f'ask_price_{i}', 0)
                        qty = row.get(f'ask_qty_{i}', 0)
                        if price:
                            with ui.row().classes("w-full justify-between font-mono text-sm"):
                                ui.label(f"{price:.2f}").classes("text-red-300")
                                ui.label(f"{qty:,}")

        dialog.open()

    # --- Data Grid ---
    grid_container = ui.column().classes("w-full mt-4")
    
    def update_table():
        grid_container.clear()
        with grid_container:
            ui.spinner("dots").classes("mx-auto")
            
        # Fetch Data
        rows = get_screener_data(
            segment=filters['segment'],
            index=filters['index'],
            sector=filters['sector'],
            industry=filters['industry'],
            search=filters['search']
        )
        
        grid_container.clear()
        with grid_container:
            if not rows:
                ui.label("No unique records found.").classes("text-slate-400 italic")
                return
 
            ui.label(f"Found {len(rows)} instruments").classes("text-xs text-slate-500 mb-2")
            
            columns = [
                {'name': 'symbol', 'label': 'Symbol', 'field': 'trading_symbol', 'sortable': True, 'align': 'left'},
                {'name': 'ltp', 'label': 'Price', 'field': 'last_price', 'sortable': True, 'align': 'right'},
                {'name': 'change', 'label': 'Change', 'field': 'net_change', 'sortable': True, 'align': 'right'},
                {'name': 'volume', 'label': 'Volume', 'field': 'volume', 'sortable': True, 'align': 'right'},
                {'name': 'open', 'label': 'Open', 'field': 'open', 'sortable': True, 'align': 'right'},
                {'name': 'high', 'label': 'High', 'field': 'high', 'sortable': True, 'align': 'right'},
                {'name': 'low', 'label': 'Low', 'field': 'low', 'sortable': True, 'align': 'right'},
                {'name': 'action', 'label': 'Depth', 'field': 'action', 'align': 'center'},
            ]
            
            table = ui.table(
                columns=columns, 
                rows=rows, 
                pagination=15
            ).classes("w-full bg-slate-900 border border-slate-800")
            
            # Styling & Interactions
            table.add_slot('body-cell-symbol', '''
                <q-td :props="props">
                    <div class="font-bold text-blue-400 cursor-pointer">
                        {{ props.value }}
                    </div>
                </q-td>
            ''')
            
            table.add_slot('body-cell-ltp', '''
                <q-td :props="props">
                    <div v-if="props.value" class="font-mono text-white">
                        ₹{{ props.value.toFixed(2) }}
                    </div>
                    <div v-else class="text-slate-600">-</div>
                </q-td>
            ''')
            
            table.add_slot('body-cell-change', '''
                <q-td :props="props">
                    <div v-if="props.value !== null" :class="props.value >= 0 ? 'text-green-400' : 'text-red-400'">
                        {{ props.value > 0 ? '+' : '' }}{{ props.value.toFixed(2) }}
                    </div>
                </q-td>
            ''')

            # Depth Button
            table.add_slot('body-cell-action', '''
                <q-td :props="props">
                    <q-btn flat dense size="sm" icon="format_list_bulleted" color="primary" 
                        @click="$parent.$emit('row-click', props.row)" />
                </q-td>
            ''')

            # Listen for row click from button or symbol
            table.on('row-click', lambda e: show_details(e.args))

    # Initial Load
    update_table()
