#!/usr/bin/env python3
"""
WebSocket Server for Real-time Market Data
Provides live updates for option chains, market quotes, and positions
"""

import os
import sys
from pathlib import Path
from typing import Dict, Set
from datetime import datetime
import re

# Add project root to Python path (go up 3 levels from backend/services/streaming/)
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent.parent.parent
sys.path.insert(0, str(_project_root))

import asyncio
from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import logging

from backend.services.upstox.live_api import get_upstox_api
from backend.services.market_data.options_chain import OptionsChainService

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

# Upstox API instance (for quotes/positions)
upstox_api = get_upstox_api()
# Options Service (for Option Chain)
options_service = OptionsChainService()


# Input validation functions
def validate_symbol(symbol: str) -> bool:
    """Validate symbol format (alphanumeric, max 20 chars)"""
    if not symbol or not isinstance(symbol, str):
        return False
    return bool(re.match(r"^[A-Z0-9]{1,20}$", symbol))


def validate_expiry_date(expiry_date: str) -> bool:
    """Validate expiry date format (YYYY-MM-DD)"""
    if not expiry_date:
        return True  # Optional field
    if not isinstance(expiry_date, str):
        return False
    try:
        datetime.strptime(expiry_date, "%Y-%m-%d")
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
        emit(
            "error",
            {
                "message": "Invalid symbol format. Must be alphanumeric, max 20 characters"
            },
        )
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
    option_chain = options_service.get_option_chain(symbol, expiry_date)
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
        # No data available
        emit("error", {"message": f"No data available for {symbol}"})


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


    def _validate_mock_removed(self):
        pass


def start_background_updates():
    """Background task to push updates to subscribed clients"""
    while True:
        try:
            # Get rooms safely
            rooms = socketio.server.manager.rooms.get("/") if socketio.server.manager.rooms else None
            
            if not rooms:
                socketio.sleep(5)
                continue
            
            # Update options for subscribed symbols
            for room in rooms:
                if room and room.startswith("options_"):
                    symbol = room.replace("options_", "")
                    # Fetch using OptionsChainService
                    option_chain = options_service.get_option_chain(symbol)

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
            for room in rooms:
                if room and room.startswith("quote_"):
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
            if "positions" in rooms:
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
