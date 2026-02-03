"""
WebSocket Server for Real-time Market Data
Provides live updates for option chains, market quotes, and positions
"""

import sys
import logging
import asyncio
import re
from typing import Dict, Set
from datetime import datetime
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import logging

from scripts.upstox_live_api import get_upstox_api

# Setup logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = "upstox-trading-platform-secret"
CORS(app, resources={r"/*": {"origins": "*"}})

# Socket.IO server
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Track active subscriptions
active_subscriptions: Dict[str, Set[str]] = {
    "options": set(),
    "quotes": set(),
    "positions": set(),
}

# Upstox API instance
upstox_api = get_upstox_api()


# Input validation functions
def validate_symbol(symbol: str) -> bool:
    """Validate symbol format (alphanumeric, max 20 chars)"""
    if not symbol or not isinstance(symbol, str):
        return False
    return bool(re.match(r'^[A-Z0-9]{1,20}$', symbol))


def validate_expiry_date(expiry_date: str) -> bool:
    """Validate expiry date format (YYYY-MM-DD)"""
    if not expiry_date:
        return True  # Optional field
    if not isinstance(expiry_date, str):
        return False
    try:
        datetime.strptime(expiry_date, '%Y-%m-%d')
        return True
    except (ValueError, TypeError):
        return False


@socketio.on("connect")
def handle_connect():
    """Client connected"""
    logger.info(f"Client connected: {request.sid}")
    emit("connected", {"message": "Connected to Upstox WebSocket server"})


@socketio.on("disconnect")
def handle_disconnect():
    """Client disconnected"""
    logger.info(f"Client disconnected: {request.sid}")

    # Remove from all subscriptions
    for subscription_type in active_subscriptions:
        active_subscriptions[subscription_type].discard(request.sid)


@socketio.on("subscribe_options")
def handle_subscribe_options(data):
    """Subscribe to option chain updates"""
    if not data or not isinstance(data, dict):
        emit("error", {"message": "Invalid request data"})
        return
    
    symbol = data.get("symbol", "NIFTY")
    expiry_date = data.get("expiry_date")

    # Validate symbol
    if not validate_symbol(symbol):
        emit("error", {"message": "Invalid symbol format. Must be alphanumeric, max 20 characters"})
        return
    
    # Validate expiry date
    if not validate_expiry_date(expiry_date):
        emit("error", {"message": "Invalid expiry date format. Must be YYYY-MM-DD"})
        return

    logger.info(f"Client {request.sid} subscribed to options: {symbol}")

    # Add to options room
    room = f"options_{symbol}"
    join_room(room)
    active_subscriptions["options"].add(request.sid)

    # Send initial data
    option_chain = upstox_api.get_option_chain(symbol, expiry_date)
    if option_chain:
        emit(
            "options_update",
            {
                "symbol": symbol,
                "data": option_chain,
                "timestamp": datetime.now().isoformat(),
            },
        )
    else:
        # Send mock data if API fails
        emit(
            "options_update",
            {
                "symbol": symbol,
                "data": _get_mock_option_chain(symbol),
                "timestamp": datetime.now().isoformat(),
                "is_mock": True,
            },
        )


@socketio.on("unsubscribe_options")
def handle_unsubscribe_options(data):
    """Unsubscribe from option chain updates"""
    if not data or not isinstance(data, dict):
        emit("error", {"message": "Invalid request data"})
        return
    
    symbol = data.get("symbol", "NIFTY")
    
    # Validate symbol
    if not validate_symbol(symbol):
        emit("error", {"message": "Invalid symbol format"})
        return
    
    room = f"options_{symbol}"
    leave_room(room)
    active_subscriptions["options"].discard(request.sid)
    logger.info(f"Client {request.sid} unsubscribed from options: {symbol}")


@socketio.on("subscribe_quote")
def handle_subscribe_quote(data):
    """Subscribe to market quote updates"""
    if not data or not isinstance(data, dict):
        emit("error", {"message": "Invalid request data"})
        return
    
    symbol = data.get("symbol", "NIFTY")
    
    # Validate symbol
    if not validate_symbol(symbol):
        emit("error", {"message": "Invalid symbol format"})
        return

    logger.info(f"Client {request.sid} subscribed to quotes: {symbol}")

    room = f"quote_{symbol}"
    join_room(room)
    active_subscriptions["quotes"].add(request.sid)

    # Send initial quote
    quote = upstox_api.get_market_quote(symbol)
    if quote:
        emit(
            "quote_update",
            {"symbol": symbol, "data": quote, "timestamp": datetime.now().isoformat()},
        )


@socketio.on("subscribe_positions")
def handle_subscribe_positions():
    """Subscribe to positions updates"""
    logger.info(f"Client {request.sid} subscribed to positions")

    join_room("positions")
    active_subscriptions["positions"].add(request.sid)

    # Send initial positions
    positions = upstox_api.get_positions()
    emit(
        "positions_update", {"data": positions, "timestamp": datetime.now().isoformat()}
    )


def _get_mock_option_chain(symbol: str):
    """Generate mock option chain for testing"""
    base_price = (
        21800 if symbol == "NIFTY" else 46500 if symbol == "BANKNIFTY" else 19500
    )

    strikes = []
    for i in range(-7, 8):
        strike = base_price + (i * 100)
        strikes.append(
            {
                "strike": strike,
                "call_ltp": max(0, (base_price - strike) + 50),
                "put_ltp": max(0, (strike - base_price) + 50),
                "call_oi": 1000000 + (i * 50000),
                "put_oi": 1000000 - (i * 50000),
                "call_volume": 50000 + abs(i) * 10000,
                "put_volume": 50000 + abs(i) * 10000,
                "call_iv": 15 + abs(i),
                "put_iv": 15 + abs(i),
                "call_delta": 0.50 + (i * 0.05),
                "put_delta": -0.50 - (i * 0.05),
            }
        )

    return {
        "symbol": symbol,
        "underlying_price": base_price,
        "strikes": strikes,
        "expiry": "2026-02-27",
    }


def start_background_updates():
    """Background task to push updates to subscribed clients"""
    while True:
        try:
            # Update options for subscribed symbols
            for room in socketio.server.manager.rooms.get("/"):
                if room.startswith("options_"):
                    symbol = room.replace("options_", "")
                    option_chain = upstox_api.get_option_chain(symbol)

                    if option_chain:
                        socketio.emit(
                            "options_update",
                            {
                                "symbol": symbol,
                                "data": option_chain,
                                "timestamp": datetime.now().isoformat(),
                            },
                            room=room,
                        )

            # Update quotes
            for room in socketio.server.manager.rooms.get("/"):
                if room.startswith("quote_"):
                    symbol = room.replace("quote_", "")
                    quote = upstox_api.get_market_quote(symbol)

                    if quote:
                        socketio.emit(
                            "quote_update",
                            {
                                "symbol": symbol,
                                "data": quote,
                                "timestamp": datetime.now().isoformat(),
                            },
                            room=room,
                        )

            # Update positions
            if "positions" in socketio.server.manager.rooms.get("/"):
                positions = upstox_api.get_positions()
                socketio.emit(
                    "positions_update",
                    {"data": positions, "timestamp": datetime.now().isoformat()},
                    room="positions",
                )

            # Wait 5 seconds before next update
            socketio.sleep(5)

        except Exception as e:
            logger.error(f"Error in background updates: {e}", exc_info=True)
            socketio.sleep(5)


if __name__ == "__main__":
    logger.info("Starting WebSocket server on http://localhost:5002")

    # Start background update task
    socketio.start_background_task(start_background_updates)

    # Run server
    socketio.run(app, host="0.0.0.0", port=5002, debug=False)
