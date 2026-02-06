"""
Oracle Market Data MCP Server
-----------------------------
Exposes the Market Data Database as an MCP Server.
Allows external AI agents (like Claude Desktop) to query:
- Sector/Industry constituents
- Real-time Market Quotes
- Instrument Metadata

Usage:
    mcp run backend/api/mcp_server.py
    OR via Claude Desktop Config
"""

import sqlite3
import os
import sys
from typing import List, Dict, Optional
from mcp.server.fastmcp import FastMCP

# Configuration
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../market_data.db"))

# Initialize MCP Server
mcp = FastMCP("Oracle Market Data")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

@mcp.tool()
def get_stocks_by_sector(sector_name: str) -> List[Dict]:
    """
    Get all stocks in a specific Sector (e.g., 'Energy', 'Technology').
    Returns Trading Symbol and Company Name.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT trading_symbol, name, industry 
        FROM instrument_master 
        WHERE sector LIKE ? AND segment = 'NSE_EQ' AND is_active = 1
        ORDER BY name
    """, (f"%{sector_name}%",))
    rows = cursor.fetchall()
    conn.close()
    return [{"symbol": r[0], "name": r[1], "industry": r[2]} for r in rows]

@mcp.tool()
def get_stocks_by_industry(industry_name: str) -> List[Dict]:
    """
    Get all stocks in a specific Industry (e.g., 'Software Infrastructure', 'Banks').
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT trading_symbol, name, sector 
        FROM instrument_master 
        WHERE industry LIKE ? AND segment = 'NSE_EQ' AND is_active = 1
        ORDER BY name
    """, (f"%{industry_name}%",))
    rows = cursor.fetchall()
    conn.close()
    return [{"symbol": r[0], "name": r[1], "sector": r[2]} for r in rows]

@mcp.tool()
def get_quote(symbol: str) -> Dict:
    """
    Get the latest Market Quote (Price, Volume, Depth) for a Symbol (e.g., 'RELIANCE').
    """
    symbol = symbol.upper().strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Resolve Instrument Key
    cursor.execute("SELECT instrument_key FROM instrument_master WHERE trading_symbol = ?", (symbol,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"error": f"Symbol {symbol} not found."}
    
    key = row[0]
    
    # 2. Check all tables (Mainboard > SME > F&O)
    tables = ['market_quota_nse500_data', 'market_quota_sme_data', 'market_quota_fo_data']
    quote_data = None
    
    for table_name in tables:
        cursor.execute(f"SELECT * FROM {table_name} WHERE instrument_key = ? ORDER BY timestamp DESC LIMIT 1", (key,))
        q_row = cursor.fetchone()
        if q_row:
            # Convert row to dict
            col_names = [description[0] for description in cursor.description]
            quote_data = dict(zip(col_names, q_row))
            quote_data['source'] = table_name
            break
            
    conn.close()
    
    if quote_data:
        return quote_data
    else:
        return {"status": "No Recent Data", "symbol": symbol}

@mcp.tool()
def get_option_chain(symbol: str, min_strike: Optional[float] = None, max_strike: Optional[float] = None) -> List[Dict]:
    """
    Get the Option Chain (Call/Put Price, OI, Greeks) for a symbol (e.g., 'NIFTY 50', 'RELIANCE').
    Optionally filter by strike price range.
    """
    symbol = symbol.upper().strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Resolve Instrument Key (Need Underlying Key)
    # Try direct match first, then LIKE for indices
    cursor.execute("SELECT instrument_key FROM instrument_master WHERE trading_symbol = ? OR name = ?", (symbol, symbol))
    row = cursor.fetchone()
    
    underlying_key = None
    if row:
        underlying_key = row[0]
    else:
        # Try generic search for Indices (e.g. "NIFTY") -> "NSE_INDEX|Nifty 50"
        cursor.execute("SELECT instrument_key FROM instrument_master WHERE name LIKE ? AND segment='NSE_INDEX' LIMIT 1", (f"%{symbol}%",))
        row = cursor.fetchone()
        if row: underlying_key = row[0]
        
    if not underlying_key:
        conn.close()
        return [{"error": f"Underlying symbol {symbol} not found."}]

    # 2. Query Option Chain Table
    query = """
        SELECT strike_price, expiry_date, 
               ce_ltp, ce_oi, ce_iv, 
               pe_ltp, pe_oi, pe_iv 
        FROM optionchain_intrday_schema 
        WHERE underlying_key = ? 
    """
    params = [underlying_key]
    
    if min_strike:
        query += " AND strike_price >= ?"
        params.append(min_strike)
    if max_strike:
        query += " AND strike_price <= ?"
        params.append(max_strike)
        
    query += " ORDER BY strike_price ASC"
    
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return [{"status": "No Option Chain data found (Market might be closed or Poller inactive).", "symbol": symbol}]

    # Format result
    results = []
    for r in rows:
        results.append({
            "strike": r[0],
            "expiry": r[1],
            "CE": {"LTP": r[2], "OI": r[3], "IV": r[4]},
            "PE": {"LTP": r[5], "OI": r[6], "IV": r[7]}
        })
    return results

@mcp.tool()
def search_market(query: str) -> List[Dict]:
    """
    Fuzzy search for companies by Name or Symbol.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    like_query = f"%{query}%"
    cursor.execute("""
        SELECT trading_symbol, name, sector, industry
        FROM instrument_master 
        WHERE (trading_symbol LIKE ? OR name LIKE ?) 
        AND segment = 'NSE_EQ' AND is_active = 1
        LIMIT 20
    """, (like_query, like_query))
    rows = cursor.fetchall()
    conn.close()
    return [{"symbol": r[0], "name": r[1], "sector": r[2], "industry": r[3]} for r in rows]

@mcp.tool()
def get_market_summary() -> Dict:
    """
    Get high-level market stats (Counts by Sector).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sector, count(*) as count 
        FROM instrument_master 
        WHERE segment='NSE_EQ' AND is_active=1 AND sector IS NOT NULL 
        GROUP BY sector 
        ORDER BY count DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

if __name__ == "__main__":
    mcp.run()
