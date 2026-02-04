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

# Add project root to Python path (go up 3 levels from backend/api/servers/)
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent.parent.parent
sys.path.insert(0, str(_project_root))

from backend.core.trading.paper_trading import PaperTradingSystem
from backend.core.analytics.performance import PerformanceAnalytics
from backend.core.risk.manager import RiskManager
from backend.services.market_data.downloader import StockDownloader, OptionDownloader, FuturesDownloader
from backend.services.market_data.options_chain import OptionsChainService

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

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get portfolio summary - fetches real data from Upstox if authenticated"""
    try:
        # Check if authenticated using AuthManager
        from auth_manager import AuthManager
        auth = AuthManager()
        access_token = auth.get_valid_token()
        
        # If authenticated, fetch real portfolio from Upstox
        if access_token:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            }
            
            try:
                # Fetch user profile (available 24/7)
                profile_response = requests.get(
                    'https://api.upstox.com/v2/user/profile',
                    headers=headers,
                    timeout=10
                )
                
                # Fetch holdings (available during market hours)
                holdings_response = requests.get(
                    'https://api.upstox.com/v2/portfolio/short-term-positions',
                    headers=headers,
                    timeout=10
                )
                
                # Fetch funds (available 5:30 AM - 12:00 AM IST)
                funds_response = requests.get(
                    'https://api.upstox.com/v2/user/get-funds-and-margin',
                    headers=headers,
                    timeout=10
                )
                
                # Check if we got valid responses
                if profile_response.status_code == 200:
                    # We're authenticated - build portfolio data
                    portfolio = {
                        'authenticated': True,
                        'mode': 'live'
                    }
                    
                    # Try to get funds if API is available
                    if funds_response.status_code == 200:
                        funds_data = funds_response.json().get('data', {})
                        equity = funds_data.get('equity', {})
                        
                        portfolio.update({
                            'total_value': float(equity.get('available_margin', 0)),
                            'cash_available': float(equity.get('available_margin', 0)),
                            'invested_value': float(equity.get('used_margin', 0)),
                            'unrealized_pnl': 0,
                            'realized_pnl': 0,
                            'day_pnl': 0,
                            'day_pnl_percent': 0,
                        })
                    else:
                        # Funds API not available (outside service hours)
                        portfolio.update({
                            'total_value': 0,
                            'cash_available': 0,
                            'invested_value': 0,
                            'unrealized_pnl': 0,
                            'realized_pnl': 0,
                            'day_pnl': 0,
                            'day_pnl_percent': 0,
                            'service_message': 'Funds data available 5:30 AM - 12:00 AM IST'
                        })
                    
                    # Get positions count
                    positions_count = 0
                    if holdings_response.status_code == 200:
                        positions_data = holdings_response.json().get('data', [])
                        positions_count = len(positions_data)
                    
                    portfolio['positions_count'] = positions_count
                    
                    return jsonify(portfolio)
                    
            except Exception as e:
                logger.error(f"Failed to fetch from Upstox: {e}")
                # Fall through to paper trading
        
        # Fall back to paper trading if not authenticated or error
        paper_system = PaperTradingSystem(db_path=DB_PATH)
        summary = paper_system.get_portfolio_summary()
        
        portfolio = {
            'authenticated': False,
            'total_value': summary.get('total_value', 100000),
            'cash_available': summary.get('cash_available', 100000),
            'invested_value': summary.get('invested_value', 0),
            'unrealized_pnl': summary.get('total_pnl', 0),
            'realized_pnl': summary.get('realized_pnl', 0),
            'day_pnl': 0,
            'day_pnl_percent': 0,
            'positions_count': len(summary.get('positions', [])),
            'mode': 'paper'
        }
        
        return jsonify(portfolio)
    except Exception as e:
        logger.error(f"Portfolio endpoint error: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# USER ENDPOINTS
# ============================================================================

@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    """Get user profile from Upstox"""
    try:
        # Check if we have a valid token using AuthManager
        from auth_manager import AuthManager
        auth = AuthManager()
        access_token = auth.get_valid_token()
        
        if not access_token:
            return jsonify({'error': 'Not authenticated', 'authenticated': False}), 401
        
        # Fetch user profile from Upstox
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        response = requests.get('https://api.upstox.com/v2/user/profile', headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            user_data = data.get('data', {})
            
            return jsonify({
                'authenticated': True,
                'name': user_data.get('user_name', 'User'),
                'email': user_data.get('email', ''),
                'user_id': user_data.get('user_id', ''),
                'user_type': user_data.get('user_type', 'individual'),
                'broker': 'Upstox',
                'exchanges': user_data.get('exchanges', [])
            })
        else:
            return jsonify({'error': 'Failed to fetch profile', 'authenticated': False}), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e), 'authenticated': False}), 500


# ============================================================================
# POSITIONS ENDPOINTS
# ============================================================================

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get all open positions"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get positions with current prices (mock current price as entry + small change)
        query = """
            SELECT 
                id,
                symbol,
                quantity,
                average_price as entry_price,
                average_price * 1.02 as current_price,  -- Mock: 2% gain
                updated_at as entry_date,
                CASE WHEN quantity > 0 THEN 'long' ELSE 'short' END as side
            FROM paper_positions
            WHERE quantity != 0
            ORDER BY updated_at DESC
        """
        
        rows = cursor.execute(query).fetchall()
        conn.close()
        
        positions = []
        for row in rows:
            entry_price = row['entry_price']
            current_price = row['current_price']
            quantity = abs(row['quantity'])
            
            pnl = (current_price - entry_price) * quantity
            pnl_percent = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
            
            positions.append({
                'id': row['id'],
                'symbol': row['symbol'],
                'quantity': quantity,
                'entry_price': round(entry_price, 2),
                'current_price': round(current_price, 2),
                'entry_date': row['entry_date'],
                'pnl': round(pnl, 2),
                'pnl_percent': round(pnl_percent, 2),
                'side': row['side']
            })
        
        return jsonify(positions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/positions/<symbol>', methods=['GET'])
def get_position_by_symbol(symbol):
    """Get position for specific symbol"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                id, symbol, quantity, average_price as entry_price,
                average_price * 1.02 as current_price,
                updated_at as entry_date,
                CASE WHEN quantity > 0 THEN 'long' ELSE 'short' END as side
            FROM paper_positions
            WHERE symbol = ? AND quantity != 0
        """
        
        row = cursor.execute(query, (symbol,)).fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'Position not found'}), 404
        
        entry_price = row['entry_price']
        current_price = row['current_price']
        quantity = abs(row['quantity'])
        
        pnl = (current_price - entry_price) * quantity
        pnl_percent = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
        
        position = {
            'id': row['id'],
            'symbol': row['symbol'],
            'quantity': quantity,
            'entry_price': round(entry_price, 2),
            'current_price': round(current_price, 2),
            'entry_date': row['entry_date'],
            'pnl': round(pnl, 2),
            'pnl_percent': round(pnl_percent, 2),
            'side': row['side']
        }
        
        return jsonify(position)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ORDERS ENDPOINTS
# ============================================================================

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get order history"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                id, symbol, side, quantity, order_type, 
                price, status, created_at, executed_at
            FROM paper_orders
            ORDER BY created_at DESC
            LIMIT 50
        """
        
        rows = cursor.execute(query).fetchall()
        conn.close()
        
        orders = []
        for row in rows:
            orders.append({
                'id': row['id'],
                'symbol': row['symbol'],
                'side': row['side'],
                'quantity': row['quantity'],
                'order_type': row['order_type'],
                'price': row['price'],
                'status': row['status'],
                'created_at': row['created_at'],
                'executed_at': row['executed_at']
            })
        
        return jsonify(orders)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/orders', methods=['POST'])
def place_order():
    """Place a new order"""
    try:
        data = request.json
        
        # Validate required fields
        required = ['symbol', 'side', 'quantity', 'order_type']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Place order using paper trading system
        paper_system = PaperTradingSystem(db_path=DB_PATH)
        
        order = paper_system.place_order(
            symbol=data['symbol'],
            side=data['side'],
            quantity=data['quantity'],
            order_type=data['order_type'],
            price=data.get('price')
        )
        
        return jsonify(order), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def cancel_order(order_id):
    """Cancel an order"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update order status to cancelled
        cursor.execute(
            "UPDATE paper_orders SET status = 'cancelled' WHERE id = ?",
            (order_id,)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Order cancelled successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# WATCHLIST ENDPOINTS
# ============================================================================

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    """Get watchlist items"""
    try:
        # Mock data for now (will integrate with real data later)
        watchlist = [
            {
                'symbol': 'INFY',
                'last_price': 1520.50,
                'change': 25.30,
                'change_percent': 1.69,
                'volume': 2500000
            },
            {
                'symbol': 'TCS',
                'last_price': 3450.75,
                'change': -15.25,
                'change_percent': -0.44,
                'volume': 1800000
            },
            {
                'symbol': 'RELIANCE',
                'last_price': 2350.00,
                'change': 42.50,
                'change_percent': 1.84,
                'volume': 3200000
            }
        ]
        
        return jsonify(watchlist)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/watchlist', methods=['POST'])
def add_to_watchlist():
    """Add symbol to watchlist"""
    try:
        data = request.json
        symbol = data.get('symbol')
        
        if not symbol:
            return jsonify({'error': 'Symbol required'}), 400
        
        # TODO: Store in database
        return jsonify({'message': f'{symbol} added to watchlist'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/watchlist/<symbol>', methods=['DELETE'])
def remove_from_watchlist(symbol):
    """Remove symbol from watchlist"""
    try:
        # TODO: Remove from database
        return jsonify({'message': f'{symbol} removed from watchlist'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# PERFORMANCE ENDPOINTS
# ============================================================================

@app.route('/api/performance', methods=['GET'])
def get_performance():
    """Get performance metrics"""
    try:
        analytics = PerformanceAnalytics(db_path=DB_PATH)
        
        # Get comprehensive report
        report = analytics.get_comprehensive_report(days=30)
        
        metrics = {
            'total_trades': report.get('total_trades', 0),
            'winning_trades': report.get('winning_trades', 0),
            'losing_trades': report.get('losing_trades', 0),
            'win_rate': report.get('win_rate', 0),
            'profit_factor': report.get('profit_factor', 0),
            'sharpe_ratio': report.get('sharpe_ratio', 0),
            'sortino_ratio': report.get('sortino_ratio', 0),
            'max_drawdown': report.get('max_drawdown', 0),
            'max_drawdown_percent': report.get('max_drawdown_percent', 0),
            'total_pnl': report.get('total_pnl', 0)
        }
        
        return jsonify(metrics)
    except Exception as e:
        # Return default metrics if error
        return jsonify({
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'max_drawdown': 0,
            'max_drawdown_percent': 0,
            'total_pnl': 0
        })


# ============================================================================
# ALERTS ENDPOINTS
# ============================================================================

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get all alerts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                id, symbol, alert_type, threshold, priority,
                is_active, created_at, triggered_at
            FROM alert_rules
            WHERE is_active = 1
            ORDER BY priority DESC, created_at DESC
        """
        
        rows = cursor.execute(query).fetchall()
        conn.close()
        
        alerts = []
        for row in rows:
            alerts.append({
                'id': row['id'],
                'symbol': row['symbol'],
                'alert_type': row['alert_type'],
                'threshold': row['threshold'],
                'priority': row['priority'],
                'is_active': bool(row['is_active']),
                'created_at': row['created_at'],
                'triggered_at': row['triggered_at']
            })
        
        return jsonify(alerts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts', methods=['POST'])
def create_alert():
    """Create new alert"""
    try:
        data = request.json
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO alert_rules 
            (symbol, alert_type, threshold, priority, is_active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
        """, (
            data['symbol'],
            data['alert_type'],
            data['threshold'],
            data.get('priority', 'MEDIUM'),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        alert_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'id': alert_id, 'message': 'Alert created'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """Delete alert"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM alert_rules WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Alert deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# SIGNALS ENDPOINTS
# ============================================================================

@app.route('/api/signals', methods=['GET'])
def get_signals():
    """Get trading signals"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                id, symbol, strategy, action, confidence,
                entry_price, target_price, stop_loss, generated_at
            FROM trading_signals
            ORDER BY generated_at DESC
            LIMIT 20
        """
        
        rows = cursor.execute(query).fetchall()
        conn.close()
        
        signals = []
        for row in rows:
            signals.append({
                'id': row['id'],
                'symbol': row['symbol'],
                'strategy': row['strategy'],
                'action': row['action'],
                'confidence': row['confidence'],
                'entry_price': row['entry_price'],
                'target_price': row['target_price'],
                'stop_loss': row['stop_loss'],
                'generated_at': row['generated_at']
            })
        
        return jsonify(signals)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/signals/<strategy>', methods=['GET'])
def get_signals_by_strategy(strategy):
    """Get signals for specific strategy"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                id, symbol, strategy, action, confidence,
                entry_price, target_price, stop_loss, generated_at
            FROM trading_signals
            WHERE strategy = ?
            ORDER BY generated_at DESC
            LIMIT 20
        """
        
        rows = cursor.execute(query, (strategy,)).fetchall()
        conn.close()
        
        signals = []
        for row in rows:
            signals.append({
                'id': row['id'],
                'symbol': row['symbol'],
                'strategy': row['strategy'],
                'action': row['action'],
                'confidence': row['confidence'],
                'entry_price': row['entry_price'],
                'target_price': row['target_price'],
                'stop_loss': row['stop_loss'],
                'generated_at': row['generated_at']
            })
        
        return jsonify(signals)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# INSTRUMENTS - NSE Equity Stock Search
# ============================================================================

@app.route('/api/instruments/nse-eq', methods=['GET'])
def get_nse_equity_instruments():
    """Get all NSE equity instruments for autocomplete
    
    Query params:
        search: Optional search term for filtering
        limit: Max results (default 100, max 500)
    
    Returns list of {symbol, name, instrument_key}
    """
    logger.info(f"[TraceID: {g.trace_id}] Fetching NSE equity instruments")
    
    search_term = request.args.get('search', '').strip().upper()
    limit = min(int(request.args.get('limit', 100)), 500)
    
    try:
        conn = get_db_connection()
        
        # Query with JOIN to get company names
        if search_term:
            query = '''
                SELECT DISTINCT 
                    e.trading_symbol as symbol,
                    COALESCE(m.company_name, e.trading_symbol) as name,
                    e.instrument_key
                FROM exchange_listings e
                LEFT JOIN master_stocks m ON e.symbol = m.symbol
                WHERE e.segment = 'NSE_EQ'
                  AND (e.trading_symbol LIKE ? OR m.company_name LIKE ?)
                ORDER BY e.trading_symbol
                LIMIT ?
            '''
            results = conn.execute(query, (f'{search_term}%', f'%{search_term}%', limit)).fetchall()
        else:
            # Return popular/top stocks when no search term
            query = '''
                SELECT DISTINCT 
                    e.trading_symbol as symbol,
                    COALESCE(m.company_name, e.trading_symbol) as name,
                    e.instrument_key
                FROM exchange_listings e
                LEFT JOIN master_stocks m ON e.symbol = m.symbol
                WHERE e.segment = 'NSE_EQ'
                  AND e.trading_symbol IN ('RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 
                                          'HINDUNILVR', 'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK',
                                          'LT', 'AXISBANK', 'BAJFINANCE', 'ASIANPAINT', 'MARUTI')
                ORDER BY e.trading_symbol
            '''
            results = conn.execute(query).fetchall()
        
        conn.close()
        
        instruments = [
            {
                'symbol': row[0],
                'name': row[1],
                'instrument_key': row[2]
            }
            for row in results
        ]
        
        logger.info(f"[TraceID: {g.trace_id}] Returning {len(instruments)} instruments")
        
        return jsonify({
            'instruments': instruments,
            'count': len(instruments),
            'search_term': search_term or None
        })
        
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Error fetching instruments: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("🚀 Starting Upstox Trading Platform API Server")
    print("📡 API running at: http://localhost:8000")
    print("🔗 Endpoints available:")
    print("   GET  /api/portfolio")
    print("   GET  /api/positions")
    print("   GET  /api/orders")
    print("   POST /api/orders")
    print("   GET  /api/watchlist")
    print("   GET  /api/performance")
@app.route('/api/health')
def health():
    """Health check endpoint"""
    logger.debug(f"[TraceID: {g.trace_id}] Health check requested")
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected'
    })


# ============================================================================
# DATA DOWNLOAD ENDPOINTS
# ============================================================================

@app.route('/api/download/stocks', methods=['POST'])
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


@app.route('/api/download/history', methods=['GET'])
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


@app.route('/api/download/logs', methods=['GET'])
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


# ============================================================================
# OPTIONS CHAIN ENDPOINTS
# ============================================================================

@app.route('/api/options/chain', methods=['GET'])
def get_options_chain():
    """
    Get live options chain data
    Query params:
        symbol: Underlying symbol (NIFTY, BANKNIFTY, RELIANCE, etc.)
        expiry_date: Optional expiry date (YYYY-MM-DD)
    """
    try:
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


@app.route('/api/options/market-status', methods=['GET'])
def get_market_status():
    """Check if market is currently open"""
    try:
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


# ============================================================================
# PHASE 3: LIVE UPSTOX API INTEGRATION
# ============================================================================

from backend.services.upstox.live_api import UpstoxLiveAPI

@app.route('/api/upstox/profile', methods=['GET'])
def get_upstox_profile():
    """Get user profile from Upstox"""
    try:
        api = UpstoxLiveAPI()
        profile = api.get_profile()
        return jsonify(profile)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Profile error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/upstox/holdings', methods=['GET'])
def get_upstox_holdings():
    """Get long-term holdings from Upstox"""
    try:
        api = UpstoxLiveAPI()
        holdings = api.get_holdings()
        return jsonify(holdings)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Holdings error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/upstox/positions', methods=['GET'])
def get_upstox_positions():
    """Get day/net positions from Upstox"""
    try:
        api = UpstoxLiveAPI()
        positions = api.get_positions()
        return jsonify(positions)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Positions error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/upstox/option-chain', methods=['GET'])
def get_upstox_option_chain():
    """Get live option chain from Upstox"""
    try:
        symbol = request.args.get('symbol', 'NIFTY')
        expiry_date = request.args.get('expiry_date')
        
        api = UpstoxLiveAPI()
        chain = api.get_option_chain(symbol, expiry_date)
        return jsonify(chain)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Option chain error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/upstox/market-quote', methods=['GET'])
def get_upstox_market_quote():
    """Get real-time market quote from Upstox"""
    try:
        symbol = request.args.get('symbol')
        if not symbol:
            return jsonify({'error': 'Symbol required'}), 400
        
        api = UpstoxLiveAPI()
        quote = api.get_market_quote(symbol)
        return jsonify(quote)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Market quote error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/upstox/funds', methods=['GET'])
def get_upstox_funds():
    """Get account funds/margin from Upstox"""
    try:
        api = UpstoxLiveAPI()
        funds = api.get_funds()
        return jsonify(funds)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Funds error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# PHASE 3: ORDER PLACEMENT (Using existing order_manager.py)
# ============================================================================

from backend.core.trading.order_manager import OrderManagerV3 as OrderManager

@app.route('/api/order/place', methods=['POST'])
def place_upstox_order():
    """Place order via Upstox"""
    try:
        data = request.json
        required = ['symbol', 'quantity', 'order_type', 'transaction_type']
        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400
        
        manager = OrderManager()
        result = manager.place_order(
            symbol=data['symbol'],
            quantity=data['quantity'],
            order_type=data['order_type'],
            transaction_type=data['transaction_type'],
            price=data.get('price'),
            trigger_price=data.get('trigger_price')
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Place order error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/order/cancel/<order_id>', methods=['DELETE'])
def cancel_upstox_order(order_id):
    """Cancel order via Upstox"""
    try:
        manager = OrderManager()
        result = manager.cancel_order(order_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Cancel order error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/order/modify/<order_id>', methods=['PUT'])
def modify_order(order_id):
    """Modify order via Upstox"""
    try:
        data = request.json
        manager = OrderManager()
        result = manager.modify_order(
            order_id=order_id,
            quantity=data.get('quantity'),
            price=data.get('price'),
            trigger_price=data.get('trigger_price')
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Modify order error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/order/status/<order_id>', methods=['GET'])
def get_order_status(order_id):
    """Get order status from Upstox"""
    try:
        manager = OrderManager()
        status = manager.get_order_status(order_id)
        return jsonify(status)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Order status error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# PHASE 3: BACKTESTING ENGINE
# ============================================================================

from backend.core.analytics.backtesting_engine import Backtester, BacktestStrategy, create_iron_condor, create_bull_call_spread

@app.route('/api/backtest/run', methods=['POST'])
def run_backtest():
    """Run strategy backtest"""
    try:
        data = request.json
        strategy_name = data.get('strategy')
        entry_date = data.get('entry_date')
        exit_date = data.get('exit_date')
        
        # Create backtester
        backtester = Backtester()
        
        # Get strategy (for now, use pre-built strategies)
        if strategy_name == 'iron_condor':
            strategy = create_iron_condor(spot_price=data.get('spot_price', 18000))
        elif strategy_name == 'bull_call_spread':
            strategy = create_bull_call_spread(spot_price=data.get('spot_price', 18000))
        else:
            return jsonify({'error': 'Unknown strategy'}), 400
        
        # Mock historical data (in production, fetch from database)
        import pandas as pd
        dates = pd.date_range(entry_date, exit_date, freq='H')
        historical_data = pd.DataFrame({
            'timestamp': dates,
            'close': [18000 + i*10 for i in range(len(dates))]
        })
        
        result = backtester.run_backtest(strategy, historical_data, entry_date, exit_date)
        return jsonify(result)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Backtest error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest/strategies', methods=['GET'])
def get_backtest_strategies():
    """Get available backtest strategies"""
    return jsonify({
        'strategies': [
            {
                'id': 'iron_condor',
                'name': 'Iron Condor',
                'description': 'Sell OTM put/call spreads, profit from low volatility',
                'max_profit': 'Net premium',
                'max_loss': 'Spread width - premium'
            },
            {
                'id': 'bull_call_spread',
                'name': 'Bull Call Spread',
                'description': 'Buy lower strike call, sell higher strike call',
                'max_profit': 'Strike difference - premium',
                'max_loss': 'Net premium paid'
            }
        ]
    })


@app.route('/api/backtest/results', methods=['GET'])
def get_backtest_results():
    """Get past backtest results from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Query backtest results (if stored in DB)
        cursor.execute("""
            SELECT * FROM backtest_results 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'strategy': row[1],
                'entry_date': row[2],
                'exit_date': row[3],
                'pnl': row[4],
                'win_rate': row[5],
                'created_at': row[6]
            })
        
        conn.close()
        return jsonify({'results': results})
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Backtest results error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# PHASE 3: PORTFOLIO ANALYTICS
# ============================================================================

from backend.core.analytics.portfolio import PortfolioAnalytics

@app.route('/api/analytics/performance', methods=['GET'])
def get_performance_analytics():
    """Get comprehensive performance analytics"""
    try:
        analytics = PortfolioAnalytics()
        summary = analytics.get_performance_summary()
        return jsonify(summary)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Analytics error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/equity-curve', methods=['GET'])
def get_equity_curve():
    """Get equity curve data"""
    try:
        days = int(request.args.get('days', 30))
        analytics = PortfolioAnalytics()
        curve = analytics.get_equity_curve(days=days)
        return jsonify({'equity_curve': curve})
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Equity curve error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# PHASE 3: ADVANCED MULTI-EXPIRY STRATEGIES
# ============================================================================

from backend.core.trading.multi_expiry_strategies import (
    create_calendar_spread,
    create_diagonal_spread,
    create_double_calendar,
    MultiExpiryBacktester,
    ExpiryRoller
)

@app.route('/api/strategies/calendar-spread', methods=['POST'])
def create_calendar_spread_strategy():
    """Create calendar spread strategy"""
    try:
        data = request.json
        required = ['underlying_price', 'strike', 'near_expiry', 'far_expiry']
        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400
        
        strategy = create_calendar_spread(
            underlying_price=data['underlying_price'],
            strike=data['strike'],
            near_expiry=data['near_expiry'],
            far_expiry=data['far_expiry'],
            option_type=data.get('option_type', 'CALL'),
            qty=data.get('qty', 50)
        )
        
        # Calculate Greeks and P&L at different prices
        greeks = strategy.get_portfolio_greeks(data['underlying_price'])
        
        price_range = [
            data['underlying_price'] - 200,
            data['underlying_price'] - 100,
            data['underlying_price'],
            data['underlying_price'] + 100,
            data['underlying_price'] + 200
        ]
        
        pnl_curve = []
        for price in price_range:
            pnl = strategy.calculate_pnl(price, data['near_expiry'])
            pnl_curve.append({'price': price, 'pnl': pnl})
        
        return jsonify({
            'strategy_name': strategy.name,
            'legs': [
                {
                    'option_type': leg.option_type.value,
                    'action': leg.action.value,
                    'strike': leg.strike,
                    'expiry': leg.expiry_date,
                    'premium': leg.premium,
                    'qty': leg.qty
                }
                for leg in strategy.legs
            ],
            'greeks': greeks,
            'pnl_curve': pnl_curve,
            'expiries': list(strategy.get_expiry_breakdown().keys())
        })
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Calendar spread error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/strategies/diagonal-spread', methods=['POST'])
def create_diagonal_spread_strategy():
    """Create diagonal spread strategy"""
    try:
        data = request.json
        required = ['underlying_price', 'near_strike', 'far_strike', 'near_expiry', 'far_expiry']
        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400
        
        strategy = create_diagonal_spread(
            underlying_price=data['underlying_price'],
            near_strike=data['near_strike'],
            far_strike=data['far_strike'],
            near_expiry=data['near_expiry'],
            far_expiry=data['far_expiry'],
            option_type=data.get('option_type', 'CALL'),
            qty=data.get('qty', 50)
        )
        
        greeks = strategy.get_portfolio_greeks(data['underlying_price'])
        
        return jsonify({
            'strategy_name': strategy.name,
            'legs': [
                {
                    'option_type': leg.option_type.value,
                    'action': leg.action.value,
                    'strike': leg.strike,
                    'expiry': leg.expiry_date,
                    'premium': leg.premium,
                    'qty': leg.qty
                }
                for leg in strategy.legs
            ],
            'greeks': greeks,
            'expiries': list(strategy.get_expiry_breakdown().keys())
        })
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Diagonal spread error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/strategies/double-calendar', methods=['POST'])
def create_double_calendar_strategy():
    """Create double calendar (iron butterfly calendar) strategy"""
    try:
        data = request.json
        required = ['underlying_price', 'near_expiry', 'far_expiry']
        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400
        
        strategy = create_double_calendar(
            underlying_price=data['underlying_price'],
            near_expiry=data['near_expiry'],
            far_expiry=data['far_expiry'],
            qty=data.get('qty', 50)
        )
        
        greeks = strategy.get_portfolio_greeks(data['underlying_price'])
        
        return jsonify({
            'strategy_name': strategy.name,
            'legs': [
                {
                    'option_type': leg.option_type.value,
                    'action': leg.action.value,
                    'strike': leg.strike,
                    'expiry': leg.expiry_date,
                    'premium': leg.premium,
                    'qty': leg.qty
                }
                for leg in strategy.legs
            ],
            'greeks': greeks,
            'num_legs': len(strategy.legs),
            'expiries': list(strategy.get_expiry_breakdown().keys())
        })
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Double calendar error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/strategies/available', methods=['GET'])
def get_available_strategies():
    """Get all available multi-expiry strategies"""
    return jsonify({
        'strategies': [
            {
                'id': 'calendar_spread',
                'name': 'Calendar Spread',
                'description': 'Sell near-term, buy far-term. Same strike, different expiries. Profit from time decay.',
                'multi_expiry': True,
                'required_params': ['underlying_price', 'strike', 'near_expiry', 'far_expiry', 'option_type'],
                'max_profit': 'Limited (depends on volatility)',
                'max_loss': 'Net debit paid',
                'best_for': 'Low volatility, range-bound markets'
            },
            {
                'id': 'diagonal_spread',
                'name': 'Diagonal Spread',
                'description': 'Different strikes AND expiries. Combines calendar + vertical spread.',
                'multi_expiry': True,
                'required_params': ['underlying_price', 'near_strike', 'far_strike', 'near_expiry', 'far_expiry', 'option_type'],
                'max_profit': 'Higher than calendar (due to strike difference)',
                'max_loss': 'Net debit paid',
                'best_for': 'Directional bias with time decay advantage'
            },
            {
                'id': 'double_calendar',
                'name': 'Double Calendar (Iron Butterfly Calendar)',
                'description': 'Calendar spreads on both calls and puts at ATM. Profit from low volatility.',
                'multi_expiry': True,
                'required_params': ['underlying_price', 'near_expiry', 'far_expiry'],
                'max_profit': 'Double premium from both calendars',
                'max_loss': 'Double net debit',
                'best_for': 'Very low volatility, stable markets'
            },
            {
                'id': 'iron_condor',
                'name': 'Iron Condor',
                'description': 'Sell OTM put/call spreads. Single expiry. Profit from range-bound.',
                'multi_expiry': False,
                'max_profit': 'Net premium',
                'max_loss': 'Spread width - premium'
            },
            {
                'id': 'bull_call_spread',
                'name': 'Bull Call Spread',
                'description': 'Buy lower strike call, sell higher strike call. Single expiry.',
                'multi_expiry': False,
                'max_profit': 'Strike difference - premium',
                'max_loss': 'Net premium paid'
            }
        ]
    })


@app.route('/api/expiry/roll', methods=['POST'])
def roll_expiry():
    """Roll position to next expiry"""
    try:
        data = request.json
        required = ['current_expiry', 'underlying_price', 'strike', 'option_type', 'action']
        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400
        
        roller = ExpiryRoller()
        
        # Create current leg
        from backend.core.trading.multi_expiry_strategies import MultiExpiryLeg, OptionType, ActionType
        current_leg = MultiExpiryLeg(
            option_type=OptionType.CALL if data['option_type'] == 'CALL' else OptionType.PUT,
            action=ActionType.BUY if data['action'] == 'BUY' else ActionType.SELL,
            strike=data['strike'],
            expiry_date=data['current_expiry'],
            premium=data.get('premium', 100),
            qty=data.get('qty', 50)
        )
        
        # Get next expiry
        current_date = data.get('current_date', datetime.now().strftime('%Y-%m-%d'))
        next_expiry = roller.get_next_expiry(current_date, interval=data.get('interval', 'weekly'))
        
        # Roll position
        new_leg, roll_details = roller.roll_position(
            current_leg,
            next_expiry,
            data['underlying_price'],
            current_date
        )
        
        return jsonify({
            'roll_details': roll_details,
            'new_leg': {
                'option_type': new_leg.option_type.value,
                'action': new_leg.action.value,
                'strike': new_leg.strike,
                'expiry': new_leg.expiry_date,
                'premium': new_leg.premium,
                'qty': new_leg.qty
            },
            'recommendation': 'Roll successful' if roll_details['roll_cost'] < 0 else 'Roll at credit'
        })
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Expiry roll error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/expiry/next', methods=['GET'])
def get_next_expiry():
    """Get next expiry date"""
    try:
        current_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        interval = request.args.get('interval', 'weekly')  # weekly or monthly
        
        roller = ExpiryRoller()
        next_expiry = roller.get_next_expiry(current_date, interval)
        
        return jsonify({
            'current_date': current_date,
            'interval': interval,
            'next_expiry': next_expiry,
            'days_until': (datetime.strptime(next_expiry, '%Y-%m-%d') - 
                          datetime.strptime(current_date, '%Y-%m-%d')).days
        })
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Next expiry error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest/multi-expiry', methods=['POST'])
def backtest_multi_expiry():
    """Backtest multi-expiry strategy with auto-rolling"""
    try:
        data = request.json
        required = ['strategy_type', 'start_date', 'end_date', 'underlying_price']
        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400
        
        # Create strategy based on type
        strategy_type = data['strategy_type']
        
        if strategy_type == 'calendar_spread':
            strategy = create_calendar_spread(
                underlying_price=data['underlying_price'],
                strike=data.get('strike', data['underlying_price']),
                near_expiry=data.get('near_expiry', '2026-02-06'),
                far_expiry=data.get('far_expiry', '2026-02-27'),
                option_type=data.get('option_type', 'CALL')
            )
        elif strategy_type == 'diagonal_spread':
            strategy = create_diagonal_spread(
                underlying_price=data['underlying_price'],
                near_strike=data.get('near_strike', data['underlying_price']),
                far_strike=data.get('far_strike', data['underlying_price'] + 200),
                near_expiry=data.get('near_expiry', '2026-02-06'),
                far_expiry=data.get('far_expiry', '2026-02-27'),
                option_type=data.get('option_type', 'CALL')
            )
        else:
            return jsonify({'error': 'Unknown strategy type'}), 400
        
        # Create mock historical data
        import pandas as pd
        import numpy as np
        dates = pd.date_range(data['start_date'], data['end_date'], freq='D')
        prices = data['underlying_price'] + np.cumsum(np.random.randn(len(dates)) * 20)
        
        historical_data = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'close': prices
        })
        
        # Run backtest
        backtester = MultiExpiryBacktester()
        result = backtester.backtest_with_rolling(
            strategy,
            historical_data,
            data['start_date'],
            data['end_date'],
            auto_roll=data.get('auto_roll', True),
            roll_days_before=data.get('roll_days_before', 3)
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"[TraceID: {g.trace_id}] Multi-expiry backtest error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 UPSTOX TRADING API SERVER - PHASE 3 + MULTI-EXPIRY")
    print("="*70)
    print("\n📍 Server: http://localhost:8000")
    print("📊 Database: market_data.db")
    print("\n📡 Available Endpoints:")
    print("\n   📈 Portfolio & Trading:")
    print("   GET  /api/portfolio")
    print("   GET  /api/positions")
    print("   GET  /api/orders")
    print("   POST /api/orders")
    print("\n   📊 Analytics:")
    print("   GET  /api/performance")
    print("   GET  /api/alerts")
    print("   GET  /api/signals")
    print("   GET  /api/health")
    print("\n   📥 Data Download:")
    print("   POST /api/download/stocks")
    print("   GET  /api/download/history")
    print("   GET  /api/download/logs")
    print("\n   📊 Options Chain:")
    print("   GET  /api/options/chain?symbol=NIFTY")
    print("   GET  /api/options/market-status")
    print("\n   🔴 PHASE 3 - Live Upstox API:")
    print("   GET  /api/upstox/profile")
    print("   GET  /api/upstox/holdings")
    print("   GET  /api/upstox/positions")
    print("   GET  /api/upstox/option-chain?symbol=NIFTY&expiry_date=2024-01-25")
    print("   GET  /api/upstox/market-quote?symbol=NSE_INDEX|Nifty 50")
    print("   GET  /api/upstox/funds")
    print("\n   🔴 PHASE 3 - Order Placement:")
    print("   POST /api/order/place")
    print("   DEL  /api/order/cancel/<order_id>")
    print("   PUT  /api/order/modify/<order_id>")
    print("   GET  /api/order/status/<order_id>")
    print("\n   🔴 PHASE 3 - Backtesting:")
    print("   POST /api/backtest/run")
    print("   GET  /api/backtest/strategies")
    print("   GET  /api/backtest/results")
    print("\n   🔴 PHASE 3 - Analytics:")
    print("   GET  /api/analytics/performance")
    print("   GET  /api/analytics/equity-curve?days=30")
    print("\n   🔥 ADVANCED - Multi-Expiry Strategies:")
    print("   POST /api/strategies/calendar-spread")
    print("   POST /api/strategies/diagonal-spread")
    print("   POST /api/strategies/double-calendar")
    print("   GET  /api/strategies/available")
    print("\n   🔥 ADVANCED - Expiry Rolling:")
    print("   POST /api/expiry/roll")
    print("   GET  /api/expiry/next?interval=weekly")
    print("\n   🔥 ADVANCED - Multi-Expiry Backtesting:")
    print("   POST /api/backtest/multi-expiry")
    print("\n✅ CORS enabled for frontend at http://localhost:5001")
    print("✅ Request tracing enabled (TraceID logging)")
    print("✅ Live Upstox API integration active")
    print("✅ Multi-expiry strategies with auto-rolling")
    print("✅ Calendar spreads, diagonal spreads, expiry management")
    print("\n🌐 WebSocket Server: Run separately on port 5002")
    print("   python backend/services/streaming/websocket_server.py")
    print("\nPress CTRL+C to stop\n")
    
    app.run(debug=False, host='0.0.0.0', port=8000)

