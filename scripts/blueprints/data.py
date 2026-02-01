#!/usr/bin/env python3
"""
Data Management Blueprint
Handles data downloads and related endpoints
"""

from flask import Blueprint, jsonify, g, request
from datetime import datetime
from pathlib import Path
import logging

data_bp = Blueprint('data', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

DB_PATH = 'market_data.db'


@data_bp.route('/download/stocks', methods=['POST'])
def download_stocks():
    """
    Download stock OHLC data from Yahoo Finance
    Request body:
    {
        "symbols": ["INFY", "TCS"],
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "interval": "1d",
        "save_db": true,
        "export_format": "parquet"
    }
    """
    try:
        from data_downloader import StockDownloader
        
        data = request.get_json()
        logger.info(f"[TraceID: {g.trace_id}] Stock download requested: {data.get('symbols')}")
        
        # Validate input
        required = ['symbols', 'start_date', 'end_date']
        for field in required:
            if field not in data:
                logger.warning(f"[TraceID: {g.trace_id}] Missing required field: {field}")
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        symbols = data['symbols']
        start_date = data['start_date']
        end_date = data['end_date']
        interval = data.get('interval', '1d')
        save_db = data.get('save_db', True)
        export_format = data.get('export_format', 'parquet')
        
        logger.debug(f"[TraceID: {g.trace_id}] Params: symbols={symbols}, interval={interval}, save_db={save_db}")
        
        # Download data
        downloader = StockDownloader(db_path=DB_PATH)
        result = downloader.download_and_process(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            save_db=save_db,
            export_format=export_format
        )
        
        logger.info(f"[TraceID: {g.trace_id}] Download complete: {result['rows']} rows, {len(result['gaps'])} gaps")
        
        return jsonify({
            'success': True,
            'trace_id': g.trace_id,
            'rows': result['rows'],
            'filepath': result['filepath'],
            'gaps': result['gaps'],
            'validation_errors': result['validation_errors'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Stock download failed: {e}", exc_info=True)
        return jsonify({
            'error': str(e),
            'trace_id': g.trace_id
        }), 500


@data_bp.route('/download/history', methods=['GET'])
def download_history():
    """Get list of downloaded files"""
    try:
        logger.debug(f"[TraceID: {g.trace_id}] Fetching download history")
        
        downloads_dir = Path('downloads')
        if not downloads_dir.exists():
            return jsonify({'files': []})
        
        files = []
        for file in downloads_dir.iterdir():
            if file.is_file():
                stat = file.stat()
                files.append({
                    'filename': file.name,
                    'size': stat.st_size,
                    'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'format': file.suffix.lstrip('.')
                })
        
        # Sort by creation date (newest first)
        files.sort(key=lambda x: x['created_at'], reverse=True)
        
        logger.info(f"[TraceID: {g.trace_id}] Found {len(files)} downloaded files")
        
        return jsonify({
            'files': files,
            'total': len(files)
        })
        
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Failed to fetch download history: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@data_bp.route('/download/logs', methods=['GET'])
def download_logs():
    """Get recent download logs"""
    try:
        logger.debug(f"[TraceID: {g.trace_id}] Fetching download logs")
        
        log_file = Path('logs/data_downloader.log')
        if not log_file.exists():
            return jsonify({'logs': []})
        
        # Read last 100 lines
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent_logs = lines[-100:] if len(lines) > 100 else lines
        
        logger.info(f"[TraceID: {g.trace_id}] Returning {len(recent_logs)} log lines")
        
        return jsonify({
            'logs': recent_logs,
            'total_lines': len(recent_logs)
        })
        
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Failed to fetch logs: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@data_bp.route('/options/chain', methods=['GET'])
def get_options_chain():
    """
    Get live options chain data
    Query params:
        symbol: Underlying symbol (NIFTY, BANKNIFTY, RELIANCE, etc.)
        expiry_date: Optional expiry date (YYYY-MM-DD)
    """
    try:
        from options_chain_service import OptionsChainService
        
        symbol = request.args.get('symbol')
        expiry_date = request.args.get('expiry_date')
        
        if not symbol:
            logger.warning(f"[TraceID: {g.trace_id}] Missing symbol parameter")
            return jsonify({'error': 'Symbol parameter required'}), 400
        
        logger.info(f"[TraceID: {g.trace_id}] Options chain requested: symbol={symbol}, expiry={expiry_date}")
        
        # Fetch option chain
        service = OptionsChainService(db_path=DB_PATH)
        chain_data = service.get_option_chain(symbol=symbol, expiry_date=expiry_date)
        
        logger.info(f"[TraceID: {g.trace_id}] Returning {len(chain_data['strikes'])} strikes")
        
        return jsonify(chain_data)
        
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Options chain fetch failed: {e}", exc_info=True)
        return jsonify({
            'error': str(e),
            'trace_id': g.trace_id
        }), 500


@data_bp.route('/options/market-status', methods=['GET'])
def get_market_status():
    """Check if market is currently open"""
    try:
        from options_chain_service import OptionsChainService
        
        logger.debug(f"[TraceID: {g.trace_id}] Market status check")
        
        service = OptionsChainService(db_path=DB_PATH)
        is_open, message = service.is_market_open()
        
        return jsonify({
            'market_open': is_open,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Market status check failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@data_bp.route('/page/downloads', methods=['GET'])
def downloads_page():
    """Render the data downloads page"""
    from flask import render_template
    try:
        logger.debug(f"[TraceID: {g.trace_id}] Rendering downloads page")
        return render_template('downloads_new.html')
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Downloads page error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to load downloads page'}), 500