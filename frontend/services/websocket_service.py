"""
WebSocket Client Service for Real-time Market Data

Connects to the WebSocket server (port 5002) to receive:
- Live option chain updates
- Real-time quotes
- Position updates
"""

import asyncio
import json
import logging
from typing import Optional, Callable, Dict, Any
from socketio import AsyncClient

logger = logging.getLogger(__name__)


class WebSocketService:
    """WebSocket client for real-time market data streaming"""

    def __init__(self, server_url: str = "http://localhost:5002"):
        """
        Initialize WebSocket service.
        
        Args:
            server_url: WebSocket server URL
        """
        self.server_url = server_url
        self.sio = AsyncClient()
        self.connected = False
        
        # Callback handlers
        self.on_options_update: Optional[Callable] = None
        self.on_quote_update: Optional[Callable] = None
        self.on_positions_update: Optional[Callable] = None
        
        # Setup event handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup Socket.IO event handlers"""
        
        @self.sio.event
        async def connect():
            """Handle connection"""
            self.connected = True
            logger.info("✅ Connected to WebSocket server")
        
        @self.sio.event
        async def disconnect():
            """Handle disconnection"""
            self.connected = False
            logger.warning("⚠️  Disconnected from WebSocket server")
        
        @self.sio.event
        async def connected(data):
            """Handle connected event from server"""
            logger.info(f"Server says: {data.get('message')}")
        
        @self.sio.event
        async def options_update(data):
            """Handle option chain updates"""
            if self.on_options_update:
                await self.on_options_update(data)
        
        @self.sio.event
        async def quote_update(data):
            """Handle quote updates"""
            if self.on_quote_update:
                await self.on_quote_update(data)
        
        @self.sio.event
        async def positions_update(data):
            """Handle positions updates"""
            if self.on_positions_update:
                await self.on_positions_update(data)
        
        @self.sio.event
        async def error(data):
            """Handle errors from server"""
            logger.error(f"WebSocket error: {data.get('message')}")
    
    async def connect(self) -> bool:
        """
        Connect to WebSocket server.
        
        Returns:
            True if connected successfully
        """
        try:
            await self.sio.connect(self.server_url)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.connected:
            await self.sio.disconnect()
    
    async def subscribe_options(self, symbol: str, expiry_date: Optional[str] = None):
        """
        Subscribe to option chain updates.
        
        Args:
            symbol: Underlying symbol (NIFTY, BANKNIFTY, etc.)
            expiry_date: Optional expiry date (YYYY-MM-DD)
        """
        await self.sio.emit("subscribe_options", {
            "symbol": symbol,
            "expiry_date": expiry_date
        })
        logger.info(f"📡 Subscribed to options: {symbol}")
    
    async def unsubscribe_options(self, symbol: str):
        """Unsubscribe from option chain updates"""
        await self.sio.emit("unsubscribe_options", {"symbol": symbol})
        logger.info(f"📡 Unsubscribed from options: {symbol}")
    
    async def subscribe_quote(self, symbol: str):
        """
        Subscribe to real-time quotes.
        
        Args:
            symbol: Symbol to subscribe to
        """
        await self.sio.emit("subscribe_quote", {"symbol": symbol})
        logger.info(f"📡 Subscribed to quotes: {symbol}")
    
    async def subscribe_positions(self):
        """Subscribe to portfolio positions updates"""
        await self.sio.emit("subscribe_positions", {})
        logger.info("📡 Subscribed to positions")


# Global WebSocket service instance
_ws_service: Optional[WebSocketService] = None


def get_websocket_service() -> WebSocketService:
    """Get or create global WebSocket service instance"""
    global _ws_service
    if _ws_service is None:
        _ws_service = WebSocketService()
    return _ws_service
