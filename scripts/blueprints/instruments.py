"""
Instruments API Blueprint
Provides endpoints for searching and browsing instruments
"""

from flask import Blueprint, jsonify, request
from scripts.services.instrument_service import InstrumentService
from scripts.services.market_data_service import MarketDataService
import logging

logger = logging.getLogger(__name__)

instruments_bp = Blueprint('instruments', __name__, url_prefix='/api/instruments')

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
        
        service = InstrumentService()

        instruments = service.search_instruments(
            query=query,
            limit=limit,
            segment="NSE_EQ",
        )
        
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
        service = MarketDataService()
        quotes = service.get_quotes([instrument_key])

        if instrument_key in quotes:
            return jsonify({
                'success': True,
                'data': quotes[instrument_key]
            })

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

        service = InstrumentService()
        results = service.search_instruments(
            query=query,
            limit=limit,
            exchange=exchange or None,
        )

        return jsonify({
            'success': True,
            'data': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error in instrument search: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
