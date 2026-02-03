"""
Market Explorer Page - Real-time Market Data with Database Integration
Displays Broad Market Indices, Derivatives, and Sectoral Indices with filtering
"""

from nicegui import ui, run
from ..common import Components
from datetime import datetime
import sqlite3
import asyncio
import requests
from typing import Dict, List, Any, Optional
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "market_data.db"
API_BASE = "http://localhost:8000"


# ============================================================================
# 📊 DATABASE QUERIES
# ============================================================================

def get_broad_market_indices() -> List[Dict]:
    """Get all broad market indices from new schema (nse_index_metadata)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                index_code,
                index_name,
                index_type,
                expected_count
            FROM nse_index_metadata
            WHERE index_type = 'broad'
            ORDER BY 
                CASE 
                    WHEN index_code = 'NIFTY50' THEN 1
                    WHEN index_code = 'NIFTYNEXT50' THEN 2
                    WHEN index_code = 'NIFTY100' THEN 3
                    WHEN index_code = 'NIFTY200' THEN 4
                    WHEN index_code = 'NIFTY500' THEN 5
                    ELSE 6
                END,
                index_name
        """)
        
        indices = []
        for row in cursor.fetchall():
            indices.append({
                'code': row[0],
                'name': row[1],
                'category': row[2] or 'broad',
                'expected_count': row[3] or 0
            })
        
        conn.close()
        return indices
        
    except Exception as e:
        print(f"Error fetching broad indices: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_sectoral_indices() -> List[Dict]:
    """Get all sectoral/thematic indices from new schema"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                index_code,
                index_name,
                index_type,
                expected_count
            FROM nse_index_metadata
            WHERE index_type IN ('sectoral', 'thematic', 'strategy')
            ORDER BY index_name
        """)
        
        indices = []
        for row in cursor.fetchall():
            indices.append({
                'code': row[0],
                'name': row[1],
                'sector': row[2] or 'sectoral',
                'expected_count': row[3] or 0
            })
        
        conn.close()
        return indices
        
    except Exception as e:
        print(f"Error fetching sectoral indices: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_index_constituents(index_code: str) -> List[Dict]:
    """Get constituents of a specific index from new schema (index_constituents_v2)"""
    
    # Write to debug file
    debug_file = Path(__file__).parent.parent.parent / "market_explorer_debug.txt"
    with open(debug_file, 'a') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"CALLED: get_index_constituents('{index_code}')\n")
        f.write(f"DB_PATH: {DB_PATH}\n")
        f.write(f"DB EXISTS: {DB_PATH.exists()}\n")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                ic.symbol,
                ic.company_name,
                ic.isin,
                ic.weight,
                ic.sector,
                ic.industry
            FROM index_constituents_v2 ic
            WHERE ic.index_code = ? AND ic.is_active = 1
            ORDER BY 
                CASE WHEN ic.weight IS NOT NULL THEN 0 ELSE 1 END,
                ic.weight DESC,
                ic.symbol
        """, (index_code,))
        
        rows = cursor.fetchall()
        
        with open(debug_file, 'a') as f:
            f.write(f"Query returned {len(rows)} rows\n")
            if rows:
                f.write(f"First row sample: {rows[0]}\n")
        
        constituents = []
        for row in rows:
            constituents.append({
                'symbol': row[0],
                'company_name': row[1] or row[0],
                'isin': row[2],
                'weight': round(row[3], 2) if row[3] else None,
                'sector': row[4] or 'N/A',
                'industry': row[5] or 'N/A'
            })
        
        conn.close()
        
        with open(debug_file, 'a') as f:
            f.write(f"Returning {len(constituents)} constituents\n")
        
        return constituents
        
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        
        with open(debug_file, 'a') as f:
            f.write(f"ERROR: {str(e)}\n")
            f.write(f"Traceback:\n{error_msg}\n")
        
        print(f"Error fetching constituents for {index_code}: {e}")
        traceback.print_exc()
        return []


def get_index_stats(index_code: str) -> Dict:
    """Get statistics for an index from new schema"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get actual constituent count
        cursor.execute("""
            SELECT COUNT(*) 
            FROM index_constituents_v2 
            WHERE index_code = ? AND is_active = 1
        """, (index_code,))
        actual_count = cursor.fetchone()[0]
        
        # Get sector distribution
        cursor.execute("""
            SELECT sector, COUNT(*) as count
            FROM index_constituents_v2
            WHERE index_code = ? AND is_active = 1 AND sector IS NOT NULL
            GROUP BY sector
            ORDER BY count DESC
            LIMIT 5
        """, (index_code,))
        
        top_sectors = []
        for row in cursor.fetchall():
            top_sectors.append({'sector': row[0], 'count': row[1]})
        
        conn.close()
        
        return {
            'actual_count': actual_count,
            'top_sectors': top_sectors
        }
        
    except Exception as e:
        print(f"Error fetching stats for {index_code}: {e}")
        import traceback
        traceback.print_exc()
        return {'actual_count': 0, 'top_sectors': []}


# ============================================================================
# 📊 UI RENDERING
# ============================================================================

def render_page(state):
    """Main page render function"""
    Components.section_header(
        "Market Explorer",
        "Explore NSE Indices and Constituents",
        "insights",
    )
    
    # Check if database is populated
    broad_indices = get_broad_market_indices()
    sectoral_indices = get_sectoral_indices()
    
    if not broad_indices:
        with Components.card():
            ui.label("⚠️ Market data not loaded").classes("text-xl text-yellow-500 mb-2")
            ui.label("Please run the database setup script:").classes("text-slate-400")
            ui.code("python scripts/setup_market_database.py").classes("mt-2")
        return
    
    # Tab navigation
    with ui.tabs().classes("w-full") as tabs:
        broad_tab = ui.tab("Broad Market Indices", icon="insights")
        sectoral_tab = ui.tab("Sectoral Indices", icon="business")
        derivatives_tab = ui.tab("Derivatives", icon="trending_up")
    
    # Tab panels
    with ui.tab_panels(tabs, value=broad_tab).classes("w-full mt-4"):
        # Broad Market Indices Tab
        with ui.tab_panel(broad_tab):
            render_broad_market_tab(broad_indices)
        
        # Sectoral Indices Tab
        with ui.tab_panel(sectoral_tab):
            render_sectoral_tab(sectoral_indices)
        
        # Derivatives Tab
        with ui.tab_panel(derivatives_tab):
            with Components.card():
                ui.label("🚧 Derivatives Explorer Coming Soon").classes("text-xl text-yellow-500")
                ui.label("This section will display F&O contracts and derivatives data.").classes("text-slate-400 mt-2")


def render_broad_market_tab(indices: List[Dict]):
    """Render Broad Market Indices tab with filters"""
    
    with ui.row().classes("w-full gap-4"):
        # Left panel: Index selector
        with ui.column().classes("w-80 flex-shrink-0"):
            with Components.card():
                ui.label("Select Index").classes("text-lg font-bold mb-4")
                
                # Filter buttons
                with ui.row().classes("w-full gap-2 mb-4 flex-wrap"):
                    filter_all = ui.button("ALL", icon="list").props("outline dense").classes("flex-1 min-w-[60px]")
                    filter_large = ui.button("LARGE CAP", icon="trending_up").props("outline dense").classes("flex-1 min-w-[60px]")
                    filter_mid = ui.button("MID CAP", icon="show_chart").props("outline dense").classes("flex-1 min-w-[60px]")
                    filter_small = ui.button("SMALL CAP", icon="insights").props("outline dense").classes("flex-1 min-w-[60px]")
                
                # Index list container
                index_list_container = ui.column().classes("w-full gap-2 max-h-[600px] overflow-y-auto")
        
        # Right panel: Index details
        details_container = ui.column().classes("flex-1 gap-4")
        
        with details_container:
            # Placeholder
            with Components.card():
                ui.label("👈 Select an index to view details").classes("text-lg text-slate-400 text-center py-12")
        
        def load_index_details(idx: Dict):
            """Load and display index details"""
            print(f"[DEBUG] load_index_details called with idx: {idx}")
            print(f"[DEBUG] Index code: {idx.get('code')}, Index name: {idx.get('name')}")
            
            details_container.clear()
            
            with details_container:
                # Header card
                with Components.card():
                    with ui.row().classes("w-full justify-between items-start"):
                        with ui.column().classes("gap-2"):
                            ui.label(idx['name']).classes("text-2xl font-bold text-white")
                            ui.label(f"Index Code: {idx['code']}").classes("text-sm text-slate-400")
                        
                        ui.button("Refresh", icon="refresh", on_click=lambda: load_index_details(idx)).props("outline dense")
                
                # Stats card
                print(f"[DEBUG] Calling get_index_stats for {idx['code']}")
                stats = get_index_stats(idx['code'])
                print(f"[DEBUG] Stats returned: {stats}")
                
                with Components.card():
                    ui.label("Index Statistics").classes("text-lg font-bold mb-4")
                    
                    with ui.row().classes("w-full gap-4"):
                        with ui.column().classes("flex-1 bg-blue-500/10 p-4 rounded-lg"):
                            ui.label("Total Constituents").classes("text-xs text-slate-400 uppercase")
                            ui.label(str(stats['actual_count'])).classes("text-3xl font-bold text-blue-400")
                        
                        with ui.column().classes("flex-1 bg-purple-500/10 p-4 rounded-lg"):
                            ui.label("Expected").classes("text-xs text-slate-400 uppercase")
                            ui.label(str(idx['expected_count'])).classes("text-3xl font-bold text-purple-400")
                        
                        with ui.column().classes("flex-1 bg-green-500/10 p-4 rounded-lg"):
                            ui.label("Data Status").classes("text-xs text-slate-400 uppercase")
                            status = "✅ Complete" if stats['actual_count'] >= idx['expected_count'] * 0.9 else "⚠️ Partial"
                            ui.label(status).classes("text-xl font-bold text-green-400")
                    
                    # Top sectors
                    if stats['top_sectors']:
                        ui.label("Top 5 Sectors").classes("text-sm font-bold mt-4 mb-2")
                        for sector_data in stats['top_sectors']:
                            with ui.row().classes("w-full justify-between items-center py-1"):
                                ui.label(sector_data['sector']).classes("text-slate-300")
                                ui.label(f"{sector_data['count']} stocks").classes("text-slate-500 text-sm")
                
                # Constituents table
                print(f"[DEBUG] Calling get_index_constituents for {idx['code']}")
                constituents = get_index_constituents(idx['code'])
                print(f"[DEBUG] get_index_constituents returned {len(constituents)} items")
                
                with Components.card():
                    ui.label(f"Constituents ({len(constituents)})").classes("text-lg font-bold mb-4")
                    
                    if constituents:
                        # Search box
                        search_input = ui.input(
                            label="Search stocks",
                            placeholder="Type symbol or company name..."
                        ).props("outlined dense clearable").classes("w-full mb-4")
                        
                        # Table columns (showing industry as main category since sector is often null)
                        columns = [
                            {'name': 'symbol', 'label': 'Symbol', 'field': 'symbol', 'align': 'left', 'sortable': True},
                            {'name': 'company_name', 'label': 'Company Name', 'field': 'company_name', 'align': 'left', 'sortable': True},
                            {'name': 'weight', 'label': 'Weight %', 'field': 'weight', 'align': 'center', 'sortable': True},
                            {'name': 'industry', 'label': 'Category', 'field': 'industry', 'align': 'left', 'sortable': True}
                        ]
                        
                        table = ui.table(
                            columns=columns,
                            rows=constituents,
                            row_key='symbol',
                            pagination={'rowsPerPage': 20, 'sortBy': 'symbol', 'descending': False}
                        ).classes("w-full")
                        
                        # Search filter
                        def filter_table():
                            query = search_input.value.lower() if search_input.value else ""
                            if query:
                                filtered = [
                                    c for c in constituents 
                                    if query in c['symbol'].lower() or query in c['company_name'].lower()
                                ]
                                table.rows = filtered
                            else:
                                table.rows = constituents
                            table.update()
                        
                        search_input.on('input', lambda: filter_table())
                    else:
                        ui.label("No constituents data available").classes("text-slate-400 italic")
        
        def render_index_list(filter_category: Optional[str] = None):
            """Render filtered index list"""
            index_list_container.clear()
            
            filtered_indices = indices
            if filter_category:
                filtered_indices = [idx for idx in indices if filter_category.lower() in idx['category'].lower()]
            
            with index_list_container:
                for idx in filtered_indices:
                    with ui.card().classes("w-full p-3 cursor-pointer hover:bg-slate-700/50 transition-colors") as card:
                        with ui.row().classes("w-full justify-between items-center"):
                            with ui.column().classes("gap-1"):
                                ui.label(idx['name']).classes("font-semibold text-white")
                                ui.label(f"{idx['expected_count']} stocks • {idx['category']}").classes("text-xs text-slate-400")
                            ui.icon("chevron_right").classes("text-slate-400")
                        
                        # Click handler
                        card.on('click', lambda i=idx: load_index_details(i))
        
        # Filter button handlers
        filter_all.on('click', lambda: render_index_list(None))
        filter_large.on('click', lambda: render_index_list('large'))
        filter_mid.on('click', lambda: render_index_list('mid'))
        filter_small.on('click', lambda: render_index_list('small'))
        
        # Initial render
        render_index_list()

def render_sectoral_tab(indices: List[Dict]):
    """Render Sectoral Indices tab"""
    with Components.card():
        ui.label("Sectoral Indices").classes("text-xl font-bold mb-4")
        
        if not indices:
            ui.label("No sectoral indices data available").classes("text-slate-400 italic")
            return
        
        # Grid of sectoral indices
        with ui.grid(columns=3).classes("w-full gap-4"):
            for idx in indices:
                with ui.card().classes("p-4 cursor-pointer hover:bg-slate-700/50 transition-colors"):
                    ui.label(idx['name']).classes("font-semibold text-white mb-2")
                    ui.label(f"Sector: {idx['sector']}").classes("text-xs text-slate-400")
                    stats = get_index_stats(idx['code'])
                    ui.label(f"{stats['actual_count']} constituents").classes("text-sm text-blue-400 mt-2")
