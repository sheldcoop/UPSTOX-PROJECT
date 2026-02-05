"""
Instruments API Blueprint
Provides endpoints for searching and browsing instruments
"""

from flask import Blueprint, jsonify, request
from scripts.upstox_live_api import get_upstox_api
import logging

logger = logging.getLogger(__name__)

instruments_bp = Blueprint('instruments', __name__, url_prefix='/api/instruments')

# Cache for instruments data
_instruments_cache = {}


@instruments_bp.route('/nse-eq', methods=['GET'])
def search_nse_eq():
    """
    Search NSE Equity instruments
    Query params:
        - query: Search term (optional)
        - limit: Max results (default: 100)
    """
    try:
        query = request.args.get('query', '').upper()
        limit = int(request.args.get('limit', 100))
        
        api = get_upstox_api()
        
        # Get all NSE_EQ instruments
        if 'NSE_EQ' not in _instruments_cache:
            # Fetch from Upstox API
            # Note: This is a placeholder - you'll need to implement actual fetching
            _instruments_cache['NSE_EQ'] = []
        
        instruments = _instruments_cache.get('NSE_EQ', [])
        
        # Filter by query if provided
        if query:
            instruments = [
                inst for inst in instruments 
                if query in inst.get('symbol', '').upper() or 
                   query in inst.get('name', '').upper()
            ]
        
        # Limit results
        instruments = instruments[:limit]
        
        return jsonify({
            'success': True,
            'data': instruments,
            'count': len(instruments)
        })
        
    except Exception as e:
        logger.error(f"Error searching NSE EQ instruments: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': []
        }), 500


@instruments_bp.route('/<instrument_key>', methods=['GET'])
def get_instrument_details(instrument_key):
    """
    Get details for a specific instrument
    """
    try:
        api = get_upstox_api()
        
        # Get quote for the instrument
        quote = api.get_market_quote(instrument_key)
        
        if quote:
            return jsonify({
                'success': True,
                'data': quote
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Instrument not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error fetching instrument {instrument_key}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@instruments_bp.route('/search', methods=['GET'])
def search_instruments():
    """
    Global search across all instruments
    Query params:
        - q: Search query
        - exchange: Filter by exchange (NSE_EQ, BSE_EQ, etc.)
        - limit: Max results (default: 50)
    """
    try:
        query = request.args.get('q', '').upper()
        exchange = request.args.get('exchange', '')
        limit = int(request.args.get('limit', 50))
        
        if not query or len(query) < 2:
            return jsonify({
                'success': True,
                'data': [],
                'message': 'Query too short'
            })
        
        # For now, return empty results with proper structure
        # This should be implemented with actual instrument data
        return jsonify({
            'success': True,
            'data': [],
            'count': 0,
            'message': 'Instrument search requires database setup'
        })
        
    except Exception as e:
        logger.error(f"Error in instrument search: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
