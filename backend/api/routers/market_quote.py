from flask import Blueprint, jsonify, request, g
import sqlite3
import logging
from typing import Dict, List, Optional

market_quote_bp = Blueprint('market_quote', __name__)
logger = logging.getLogger(__name__)

@market_quote_bp.route('/indices', methods=['GET'])
def get_indices_list():
    """Get list of available indices."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT index_name FROM index_mapping ORDER BY index_name")
        indices = [row[0] for row in cursor.fetchall()]
        conn.close()
        return jsonify(indices)
    except Exception as e:
        logger.error(f"Indices list error: {e}")
        return jsonify([])

@market_quote_bp.route('/index/<index_name>', methods=['GET'])
def get_index_constituents(index_name):
    """
    Get market quotes for all constituents of an index.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Get Keys for Index
        # 2. Join with NSE500 table for latest quotes (assuming all index stocks are in NSE500 table)
        # Note: If NSE500 table (2500 stocks) covers everything, this join is efficient.
        # We target the LATEST snapshot for each instrument.
        
        # Get max timestamp first to filter for latest snapshot
        cursor.execute("SELECT MAX(timestamp) FROM market_quota_nse500_data")
        max_ts = cursor.fetchone()[0]
        
        if not max_ts:
            return jsonify({'error': 'No market data available'}), 404

        sql = """
            SELECT m.* 
            FROM market_quota_nse500_data m
            JOIN index_mapping i ON m.instrument_key = i.instrument_key
            WHERE i.index_name = ?
            AND m.timestamp = ?
            ORDER BY m.total_buy_quantity DESC
        """
        
        cursor.execute(sql, (index_name, max_ts))
        rows = cursor.fetchall()
        conn.close()
        
        results = [dict(row) for row in rows]
        return jsonify({
            'index': index_name,
            'timestamp': max_ts,
            'count': len(results),
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Index data error: {e}")
        return jsonify({'error': str(e)}), 500

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@market_quote_bp.route('/search', methods=['GET'])
def search_instruments():
    """
    Search instruments in instrument_master.
    Query Params: q (query string), limit (default 20), exchange (optional)
    """
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    limit = request.args.get('limit', 20)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Search by symbol or name
        sql = """
            SELECT instrument_key, trading_symbol, name, exchange, segment, instrument_type
            FROM instrument_master
            WHERE is_active = 1
            AND (trading_symbol LIKE ? OR name LIKE ?)
            LIMIT ?
        """
        like_query = f"%{query}%"
        cursor.execute(sql, (like_query, like_query, limit))
        rows = cursor.fetchall()
        conn.close()
        
        results = [dict(row) for row in rows]
        return jsonify(results)
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500

@market_quote_bp.route('/universe/<universe_type>', methods=['GET'])
def get_universe_data(universe_type):
    """
    Get latest market quotes for a specific universe.
    universe_type: 'sme', 'nse500', 'fno'
    """
    table_map = {
        'sme': 'market_quota_sme_data',
        'nse500': 'market_quota_nse500_data',
        'fno': 'market_quota_fo_data'
    }
    
    table_name = table_map.get(universe_type.lower())
    if not table_name:
        return jsonify({'error': 'Invalid universe type'}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get latest snapshot for each instrument
        # Optimizing: Get distinct instrument_keys from the latest batch?
        # Assuming we just want the LATEST rows.
        # Efficient query: Select * from table where timestamp = (select max(timestamp) from table)
        # OR just getting top N rows ordered by timestamp desc if we want a feed.
        
        # Best approach: Get the most recent timestamp first
        cursor.execute(f"SELECT MAX(timestamp) FROM {table_name}")
        max_ts = cursor.fetchone()[0]
        
        if not max_ts:
            conn.close()
            return jsonify([])
            
        sql = f"""
            SELECT * FROM {table_name}
            WHERE timestamp = ?
        """
        cursor.execute(sql, (max_ts,))
        rows = cursor.fetchall()
        conn.close()
        
        results = [dict(row) for row in rows]
        return jsonify({
            'timestamp': max_ts,
            'count': len(results),
            'data': results
        })
    except Exception as e:
        logger.error(f"Universe data error: {e}")
        return jsonify({'error': str(e)}), 500

@market_quote_bp.route('/snapshot/<instrument_key>', methods=['GET'])
def get_instrument_snapshot(instrument_key):
    """
    Get latest snapshot for a single instrument across all tables (or specific check).
    Since we don't know which table it is in easily, we might verify universe or check all.
    Optimization: Client should specify universe if possible, but let's check all tables or join.
    Actually, simpler to search mostly used tables.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        tables = ['market_quota_nse500_data', 'market_quota_fo_data', 'market_quota_sme_data']
        result = None
        
        for table in tables:
            cursor.execute(f"SELECT * FROM {table} WHERE instrument_key = ? ORDER BY timestamp DESC LIMIT 1", (instrument_key,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result['source_table'] = table
                break
        
        conn.close()
        
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Instrument not found in market quote tables'}), 404
            
    except Exception as e:
        logger.error(f"Snapshot error: {e}")
        return jsonify({'error': str(e)}), 500
