#!/usr/bin/env python3
"""
Flask API Server - Refactored with Blueprints
Provides REST endpoints for the trading platform frontend

Architecture:
- Main app file handles middleware, logging, error handling
- Blueprints handle feature-specific endpoints (portfolio, orders, etc.)
- Shared utilities in individual modules
"""

from flask import Flask, jsonify, request, g, render_template
from flask_cors import CORS
import sys
import os
import uuid
import logging
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.append(project_root)

# Configure Flask app with correct template/static folders
app = Flask(
    __name__,
    template_folder=os.path.join(project_root, "templates"),
    static_folder=os.path.join(project_root, "static"),
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/api_server.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Create logs directory
Path("logs").mkdir(exist_ok=True)

# Enable CORS for frontend
CORS(app)

# Optional production monitoring & performance enhancements
try:
    from config.enhancements import (
        setup_redis_cache,
        setup_rate_limiting,
        setup_compression,
        setup_prometheus_metrics,
        setup_sentry,
    )

    setup_redis_cache(app)
    setup_rate_limiting(app)
    setup_compression(app)
    setup_prometheus_metrics(app)
    setup_sentry(app)
except Exception as e:
    logger.warning(f"Monitoring enhancements skipped: {e}")

# Database path
DB_PATH = "market_data.db"


# ============================================================================
# REQUEST TRACING MIDDLEWARE (God-Mode Debugging)
# ============================================================================


@app.before_request
def inject_trace_id():
    """Inject unique trace ID for request tracking"""
    g.trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4())[:8])
    logger.info(
        f"[TraceID: {g.trace_id}] {request.method} {request.path} - Client: {request.remote_addr}"
    )
    if request.method in ["POST", "PUT", "PATCH"]:
        logger.debug(f"[TraceID: {g.trace_id}] Request body: {request.get_json()}")


@app.after_request
def log_response(response):
    """Log response and attach trace ID header"""
    logger.info(f"[TraceID: {g.trace_id}] Response: {response.status_code}")
    response.headers["X-Trace-ID"] = g.trace_id
    return response


@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler with state dump"""
    logger.error(
        f"[TraceID: {g.trace_id}] Unhandled exception: {str(e)}", exc_info=True
    )

    # Dump state for debugging
    error_dump = {
        "trace_id": g.trace_id,
        "error": str(e),
        "type": type(e).__name__,
        "path": request.path,
        "method": request.method,
        "timestamp": datetime.now().isoformat(),
    }

    dump_dir = Path("debug_dumps")
    dump_dir.mkdir(exist_ok=True)
    dump_file = (
        dump_dir / f"error_{g.trace_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )

    with open(dump_file, "w") as f:
        json.dump(error_dump, f, indent=2, default=str)

    logger.error(f"[TraceID: {g.trace_id}] Error state dumped to {dump_file}")

    return (
        jsonify(
            {
                "error": str(e),
                "trace_id": g.trace_id,
                "timestamp": datetime.now().isoformat(),
            }
        ),
        500,
    )


# ============================================================================
# FRONTEND ROUTES
# ============================================================================


@app.route("/")
def index():
    """Serve dashboard"""
    return render_template("dashboard_modern.html")


# ============================================================================
# REGISTER BLUEPRINTS
# ============================================================================

# Import blueprints
from scripts.blueprints.portfolio import portfolio_bp
from scripts.blueprints.orders import orders_bp
from scripts.blueprints.signals import signals_bp
from scripts.blueprints.analytics import analytics_bp
from scripts.blueprints.data import data_bp
from scripts.blueprints.upstox import upstox_bp
from scripts.blueprints.order import order_bp
from scripts.blueprints.backtest import backtest_bp
from scripts.blueprints.strategies import strategies_bp
from scripts.blueprints.expiry import expiry_bp
from scripts.blueprints.health import health_bp
from scripts.blueprints.auth import auth_bp
from scripts.blueprints.market_info import market_info_bp
from scripts.blueprints.charges import charges_bp
from scripts.blueprints.quote_v3 import quote_v3_bp
from scripts.blueprints.historical_v3 import historical_v3_bp
from scripts.blueprints.websocket import websocket_bp
from scripts.blueprints.instruments import instruments_bp
from scripts.blueprints.gtt import gtt_bp
from scripts.blueprints.webhook import webhook_bp

# Register blueprints
app.register_blueprint(portfolio_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(signals_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(data_bp)
app.register_blueprint(upstox_bp)
app.register_blueprint(order_bp)
app.register_blueprint(backtest_bp)
app.register_blueprint(strategies_bp)
app.register_blueprint(expiry_bp)
app.register_blueprint(health_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(market_info_bp)
app.register_blueprint(charges_bp)
app.register_blueprint(quote_v3_bp)
app.register_blueprint(historical_v3_bp)
app.register_blueprint(websocket_bp)
app.register_blueprint(instruments_bp)
app.register_blueprint(gtt_bp)
app.register_blueprint(webhook_bp)

logger.info("✅ All blueprints registered successfully")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 UPSTOX TRADING API SERVER - REFACTORED WITH BLUEPRINTS")
    print("=" * 70)
    print("\n📍 Server: http://localhost:8000")
    print("📊 Database: market_data.db")
    print("\n📡 Registered Blueprints:")
    print(
        "   📈 Portfolio Blueprint (/api/portfolio, /api/positions, /api/user/profile)"
    )
    print("   📊 Orders Blueprint (/api/orders, /api/alerts)")
    print("   🎯 Signals Blueprint (/api/signals, /api/instruments/nse-eq)")
    print("   📉 Analytics Blueprint (/api/performance, /api/analytics/*)")
    print("   📥 Data Blueprint (/api/download/*, /api/options/*)")
    print("   🔴 Upstox Blueprint (/api/upstox/*)")
    print("   🛒 Order Blueprint (/api/order/place, /cancel, /modify, /status)")
    print("   🧪 Backtest Blueprint (/api/backtest/*)")
    print("   🎲 Strategies Blueprint (/api/strategies/*)")
    print("   ⏰ Expiry Blueprint (/api/expiry/*)")
    print("   ❤️  Health Blueprint (/api/health)")
    print("\n✅ CORS enabled for frontend")
    print("✅ Request tracing enabled (TraceID logging)")
    print("✅ Global error handling with state dumps")
    print("✅ Modular architecture with blueprints")
    print("\nPress CTRL+C to stop\n")

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Upstox Trading API Server")
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to run server on (default: 8000)"
    )
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    args = parser.parse_args()

    print(f"🚀 Starting on {args.host}:{args.port}\n")
    app.run(debug=True, host=args.host, port=args.port)
