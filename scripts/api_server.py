#!/usr/bin/env python3
"""
Flask API Server - Wraps existing Python backend scripts
Provides REST endpoints for the React frontend
"""

from flask import Flask, jsonify, request, g, Response, stream_with_context, render_template
from flask_cors import CORS
import sqlite3
import sys
import os
import uuid
import logging
import json
import requests
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.legacy.paper_trading import PaperTradingSystem
from scripts.metrics.performance_analytics import PerformanceAnalytics
from scripts.metrics.risk_manager import RiskManager
from scripts.data_downloader import StockDownloader, OptionDownloader, FuturesDownloader
from scripts.legacy.options_chain_service import OptionsChainService

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Database path
DB_PATH = 'market_data.db'

# Upstox credentials (from oauth_server.py)
CLIENT_ID = '33b9a757-1a99-47dc-b6fa-c3cf3dcaf6b4'

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory
Path('logs').mkdir(exist_ok=True)


# ============================================================================
# REQUEST TRACING MIDDLEWARE (God-Mode Debugging)
# ============================================================================

@app.before_request
def inject_trace_id():
    """Inject unique trace ID for request tracking"""
    g.trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4())[:8])
    logger.info(f"[TraceID: {g.trace_id}] {request.method} {request.path} - Client: {request.remote_addr}")
    if request.method in ['POST', 'PUT', 'PATCH']:
        logger.debug(f"[TraceID: {g.trace_id}] Request body: {request.get_json()}")

@app.after_request
def log_response(response):
    """Log response and attach trace ID header"""
    logger.info(f"[TraceID: {g.trace_id}] Response: {response.status_code}")
    response.headers['X-Trace-ID'] = g.trace_id
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler with state dump"""
    logger.error(f"[TraceID: {g.trace_id}] Unhandled exception: {str(e)}", exc_info=True)
    
    # Dump state for debugging
    error_dump = {
        'trace_id': g.trace_id,
        'error': str(e),
        'type': type(e).__name__,
        'path': request.path,
        'method': request.method,
        'timestamp': datetime.now().isoformat()
    }
    
    dump_dir = Path('debug_dumps')
    dump_dir.mkdir(exist_ok=True)
    dump_file = dump_dir / f"error_{g.trace_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(dump_file, 'w') as f:
        json.dump(error_dump, f, indent=2, default=str)
    
    logger.error(f"[TraceID: {g.trace_id}] Error state dumped to {dump_file}")
    
    return jsonify({
        'error': str(e),
        'trace_id': g.trace_id,
        'timestamp': datetime.now().isoformat()
    }), 500

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================================
# HOME & FRONTEND ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve dashboard"""
    return render_template('dashboard.html')


# ============================================================================
# PORTFOLIO ENDPOINTS
# ============================================================================
# ...existing code...
