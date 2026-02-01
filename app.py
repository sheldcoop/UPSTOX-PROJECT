"""
Upstox Trading Platform - Flask Web Server
Serves HTML templates with backend API integration
"""

import sys
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import logging
import requests
import sqlite3
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Backend API URL (api_server.py runs on port 8000)
BACKEND_API_URL = 'http://localhost:8000/api'

# Timeout for API calls (seconds)
API_TIMEOUT = 10

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_portfolio_data():
    """Fetch portfolio data from backend API"""
    try:
        response = requests.get(f'{BACKEND_API_URL}/portfolio', timeout=API_TIMEOUT)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch portfolio from backend: {e}")
    
    # Fallback mock data
    return {
        'authenticated': False,
        'total_value': 247891.00,
        'day_pnl': 4231.50,
        'day_pnl_percent': 1.73,
        'positions_count': 12,
        'mode': 'paper'
    }

def get_positions_data():
    """Fetch positions from backend API"""
    try:
        response = requests.get(f'{BACKEND_API_URL}/positions', timeout=API_TIMEOUT)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch positions from backend: {e}")
    
    # Fallback mock data
    return {
        'positions': [
            {'symbol': 'INFY', 'qty': 10, 'ltp': 1800.50, 'avg_price': 1750.00, 'pnl': 5050.00},
            {'symbol': 'TCS', 'qty': 5, 'ltp': 3900.00, 'avg_price': 3800.00, 'pnl': 5000.00},
            {'symbol': 'RELIANCE', 'qty': 2, 'ltp': 2600.00, 'avg_price': 2550.00, 'pnl': 3000.00},
        ]
    }

def get_market_indices():
    """Fetch market indices from backend API"""
    try:
        response = requests.get(f'{BACKEND_API_URL}/indices', timeout=API_TIMEOUT)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch indices from backend: {e}")
    
    # Fallback mock data
    return {
        'indices': [
            {
                'symbol': 'NIFTY 50',
                'ltp': 21800.00,
                'change': 120.50,
                'change_percent': 0.56,
                'high': 21850.00,
                'low': 21650.00
            },
            {
                'symbol': 'NIFTY BANK',
                'ltp': 45600.00,
                'change': -45.20,
                'change_percent': -0.10,
                'high': 45800.00,
                'low': 45400.00
            },
            {
                'symbol': 'INDIA VIX',
                'ltp': 14.25,
                'change': 1.20,
                'change_percent': 9.23,
                'high': 14.50,
                'low': 13.80
            }
        ]
    }

def format_currency(value):
    """Format value as Indian currency"""
    if isinstance(value, (int, float)):
        return f"₹{value:,.2f}"
    return value

def format_data_for_template():
    """Prepare all data for template rendering"""
    portfolio = get_portfolio_data()
    indices = get_market_indices()
    
    # Format portfolio for display
    template_data = {
        'portfolio_value': format_currency(portfolio.get('total_value', 247891)),
        'today_pnl': format_currency(portfolio.get('day_pnl', 4231.50)),
        'pnl_percent': portfolio.get('day_pnl_percent', 1.73),
        'open_positions': portfolio.get('positions_count', 12),
        'mode': portfolio.get('mode', 'paper'),
        'authenticated': portfolio.get('authenticated', False),
    }
    
    # Format indices
    if 'indices' in indices:
        for idx in indices['indices']:
            if 'NIFTY 50' in idx['symbol']:
                template_data['nifty'] = {
                    'value': f"{idx['ltp']:,.2f}",
                    'change': f"{idx['change']:+.2f}",
                    'pct': f"{idx['change_percent']:+.2f}%",
                    'up': idx['change'] >= 0
                }
            elif 'NIFTY BANK' in idx['symbol'] or 'BANKNIFTY' in idx['symbol']:
                template_data['banknifty'] = {
                    'value': f"{idx['ltp']:,.2f}",
                    'change': f"{idx['change']:+.2f}",
                    'pct': f"{idx['change_percent']:+.2f}%",
                    'up': idx['change'] >= 0
                }
            elif 'VIX' in idx['symbol']:
                template_data['vix'] = {
                    'value': f"{idx['ltp']:,.2f}",
                    'change': f"{idx['change']:+.2f}",
                    'pct': f"{idx['change_percent']:+.2f}%",
                    'up': idx['change'] >= 0
                }
    
    return template_data


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def dashboard():
    """Main dashboard page"""
    data = format_data_for_template()
    return render_template('dashboard.html', data=data)

@app.route('/positions')
def positions():
    """Positions page"""
    data = format_data_for_template()
    positions_data = get_positions_data()
    return render_template('positions.html', data=data, positions=positions_data.get('positions', []))

@app.route('/options')
def options():
    """Options chain page"""
    data = format_data_for_template()
    return render_template('options.html', data=data)

@app.route('/downloads')
def downloads():
    """Data download center page"""
    data = format_data_for_template()
    return render_template('downloads.html', data=data)

# ============================================================================
# API ENDPOINTS (Bridge to Backend)
# ============================================================================

@app.route('/api/data')
def api_data():
    """API endpoint - forwards to backend or returns formatted data"""
    return jsonify(format_data_for_template())

@app.route('/api/portfolio')
def api_portfolio():
    """Get portfolio - forwards from backend API"""
    return jsonify(get_portfolio_data())

@app.route('/api/positions')
def api_positions():
    """Get positions - forwards from backend API"""
    return jsonify(get_positions_data())

@app.route('/api/indices')
def api_indices():
    """Get market indices - forwards from backend API"""
    return jsonify(get_market_indices())

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'frontend_port': 5001,
        'backend_url': BACKEND_API_URL
    })

if __name__ == '__main__':
    logger.info("Starting Upstox Trading Platform on http://localhost:5001")
    logger.info(f"Backend API URL: {BACKEND_API_URL}")
    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=True)
