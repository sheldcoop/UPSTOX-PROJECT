# 🎯 Zero-Error Architect - Code Templates

Ready-to-use code templates that follow the Zero-Error Architect principles.

---

## Template 1: NiceGUI Page with API Integration

```python
"""
New Dashboard Page Template
Following Zero-Error Architect principles
"""

from nicegui import ui
from scripts.utilities.async_helpers import (
    safe_api_call,
    safe_notification,
    safe_sleep,
    AsyncTimer
)
import logging

logger = logging.getLogger(__name__)

# Configuration
API_BASE = 'http://localhost:8000'  # Backend port
FRONTEND_PORT = 5001  # This page runs on port 5001


class MyPage:
    """
    Template for a new dashboard page
    """
    
    def __init__(self):
        self.data = []
        self.timer = None
    
    @ui.refreshable
    async def data_display(self):
        """Refreshable data display section"""
        if not self.data:
            ui.label('No data available')
            return
        
        with ui.card().classes('w-full'):
            ui.label('Data').classes('text-h6')
            for item in self.data:
                ui.label(f"• {item}")
    
    async def fetch_data(self):
        """
        Fetch data from backend API (non-blocking)
        """
        try:
            # Safe, non-blocking API call
            response = await safe_api_call(
                f'{API_BASE}/api/my-endpoint',
                method='GET'
            )
            
            if 'error' in response:
                await safe_notification(
                    f"Error: {response.get('message', 'Unknown error')}",
                    type='error'
                )
                return None
            
            return response.get('data', [])
            
        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
            await safe_notification("Failed to load data", type='error')
            return None
    
    async def refresh_data(self):
        """Refresh data and update UI"""
        # Show loading notification
        await safe_notification("Loading...", type='info', timeout=1)
        
        # Fetch data (non-blocking)
        new_data = await self.fetch_data()
        
        if new_data:
            self.data = new_data
            self.data_display.refresh()  # Refresh the UI
            await safe_notification("Data loaded!", type='success')
    
    async def start_auto_refresh(self, interval=5.0):
        """Start auto-refresh timer"""
        if self.timer:
            await self.timer.stop()
        
        self.timer = AsyncTimer(self.refresh_data, interval=interval)
        await self.timer.start()
        await safe_notification(f"Auto-refresh enabled ({interval}s)", type='info')
    
    async def stop_auto_refresh(self):
        """Stop auto-refresh timer"""
        if self.timer:
            await self.timer.stop()
            self.timer = None
            await safe_notification("Auto-refresh disabled", type='info')
    
    def render(self):
        """Render the page"""
        with ui.column().classes('w-full gap-4'):
            # Header
            ui.label('My Dashboard Page').classes('text-h4')
            
            # Controls
            with ui.row().classes('gap-2'):
                ui.button(
                    'Refresh',
                    on_click=self.refresh_data,
                    icon='refresh'
                ).props('color=primary')
                
                ui.button(
                    'Auto-Refresh ON',
                    on_click=lambda: self.start_auto_refresh(5.0),
                    icon='play_arrow'
                ).props('color=positive')
                
                ui.button(
                    'Auto-Refresh OFF',
                    on_click=self.stop_auto_refresh,
                    icon='stop'
                ).props('color=negative')
            
            # Data display
            self.data_display()


# Usage in main dashboard
def create_page():
    """Create and return the page"""
    page = MyPage()
    page.render()
    return page
```

---

## Template 2: Backend API Endpoint

```python
"""
Backend API Endpoint Template
Following Zero-Error Architect principles
"""

from flask import Blueprint, jsonify, request, g
import logging
from functools import wraps

logger = logging.getLogger(__name__)

# Create blueprint
my_api = Blueprint('my_api', __name__, url_prefix='/api')


def error_handler(f):
    """Decorator for consistent error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return jsonify({
                'error': 'validation_error',
                'message': str(e)
            }), 400
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            return jsonify({
                'error': 'server_error',
                'message': 'An unexpected error occurred'
            }), 500
    return decorated_function


@my_api.route('/my-endpoint', methods=['GET'])
@error_handler
def get_data():
    """
    Get data from database
    
    Returns:
        200: Success with data
        400: Bad request
        500: Server error
    """
    # Validate query parameters
    limit = request.args.get('limit', 10, type=int)
    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100")
    
    # Fetch data (with error handling)
    try:
        import sqlite3
        conn = sqlite3.connect('market_data.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM my_table LIMIT ?', (limit,))
        rows = cursor.fetchall()
        
        conn.close()
        
        # Format response
        data = [
            {'id': row[0], 'value': row[1]}
            for row in rows
        ]
        
        return jsonify({
            'status': 'success',
            'data': data,
            'count': len(data)
        }), 200
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise ValueError("Database query failed")


@my_api.route('/my-endpoint', methods=['POST'])
@error_handler
def create_data():
    """
    Create new data entry
    
    Request Body:
        {
            "name": "string",
            "value": number
        }
    
    Returns:
        201: Created
        400: Bad request
        500: Server error
    """
    # Validate request
    if not request.is_json:
        raise ValueError("Content-Type must be application/json")
    
    data = request.get_json()
    
    # Validate fields
    if 'name' not in data or 'value' not in data:
        raise ValueError("Missing required fields: name, value")
    
    # Insert data
    try:
        import sqlite3
        conn = sqlite3.connect('market_data.db')
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO my_table (name, value) VALUES (?, ?)',
            (data['name'], data['value'])
        )
        
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Data created',
            'id': new_id
        }), 201
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise ValueError("Failed to create data")


# Register blueprint in main app
# In scripts/api_server.py:
# from my_module import my_api
# app.register_blueprint(my_api)
```

---

## Template 3: Async Database Query

```python
"""
Async Database Query Template
Prevents UI freezing in NiceGUI
"""

import sqlite3
from scripts.utilities.async_helpers import safe_db_query
import logging

logger = logging.getLogger(__name__)


async def get_recent_orders(limit=10):
    """
    Fetch recent orders from database (non-blocking)
    
    Args:
        limit: Maximum number of orders to return
        
    Returns:
        List of order dictionaries
    """
    def query():
        """Inner function that does the actual query"""
        try:
            conn = sqlite3.connect('market_data.db')
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    id,
                    symbol,
                    quantity,
                    price,
                    created_at
                FROM orders
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to list of dicts
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []
    
    # Run query in thread pool (non-blocking)
    orders = await safe_db_query(query)
    return orders


async def insert_order(symbol, quantity, price):
    """
    Insert new order into database (non-blocking)
    
    Args:
        symbol: Stock symbol
        quantity: Order quantity
        price: Order price
        
    Returns:
        Order ID if successful, None otherwise
    """
    def query():
        """Inner function that does the actual insert"""
        try:
            conn = sqlite3.connect('market_data.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO orders (symbol, quantity, price, created_at)
                VALUES (?, ?, ?, datetime('now'))
            ''', (symbol, quantity, price))
            
            conn.commit()
            order_id = cursor.lastrowid
            conn.close()
            
            return order_id
            
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return None
    
    # Run insert in thread pool (non-blocking)
    order_id = await safe_db_query(query)
    return order_id
```

---

## Template 4: Error Handler with Auto-Fix

```python
"""
Error Handler Template with Auto-Fix Suggestions
"""

from scripts.utilities.async_helpers import safe_notification
import logging

logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Centralized error handler with user-friendly messages
    """
    
    @staticmethod
    async def handle_api_error(error, context=""):
        """
        Handle API errors with user-friendly messages
        
        Args:
            error: The error object
            context: Context about where error occurred
        """
        error_msg = str(error)
        
        # Map common errors to user-friendly messages
        if 'Connection refused' in error_msg:
            await safe_notification(
                "Backend server is not running. Start it with: python scripts/api_server.py",
                type='error',
                timeout=5
            )
            logger.error(f"Connection refused - backend not running ({context})")
            
        elif 'timeout' in error_msg.lower():
            await safe_notification(
                "Request timed out. Check your network connection.",
                type='error'
            )
            logger.error(f"Request timeout ({context})")
            
        elif '404' in error_msg:
            await safe_notification(
                "Endpoint not found. Check API URL.",
                type='error'
            )
            logger.error(f"404 Not Found ({context})")
            
        elif '500' in error_msg:
            await safe_notification(
                "Server error. Check backend logs.",
                type='error'
            )
            logger.error(f"500 Server Error ({context})")
            
        else:
            await safe_notification(
                f"Error: {error_msg}",
                type='error'
            )
            logger.error(f"Unexpected error ({context}): {error}")
    
    @staticmethod
    async def handle_db_error(error, context=""):
        """Handle database errors"""
        error_msg = str(error)
        
        if 'no such table' in error_msg.lower():
            await safe_notification(
                "Database table not found. Run database initialization.",
                type='error',
                timeout=5
            )
            logger.error(f"Table not found ({context})")
            
        elif 'locked' in error_msg.lower():
            await safe_notification(
                "Database is locked. Close other connections and retry.",
                type='warning'
            )
            logger.warning(f"Database locked ({context})")
            
        else:
            await safe_notification(
                f"Database error: {error_msg}",
                type='error'
            )
            logger.error(f"Database error ({context}): {error}")


# Usage example
async def fetch_data_with_error_handling():
    """Fetch data with comprehensive error handling"""
    try:
        from scripts.utilities.async_helpers import safe_api_call
        
        data = await safe_api_call('http://localhost:8000/api/data')
        
        if 'error' in data:
            await ErrorHandler.handle_api_error(
                Exception(data['message']),
                context='fetch_data'
            )
            return None
        
        return data
        
    except Exception as e:
        await ErrorHandler.handle_api_error(e, context='fetch_data')
        return None
```

---

## Template 5: Live Data Streaming

```python
"""
Live Data Streaming Template
Updates UI in real-time without blocking
"""

from nicegui import ui
from scripts.utilities.async_helpers import (
    safe_api_call,
    safe_notification,
    AsyncTimer
)
import logging

logger = logging.getLogger(__name__)


class LiveDataStream:
    """
    Stream live data and update UI in real-time
    """
    
    def __init__(self, endpoint, interval=5.0):
        self.endpoint = endpoint
        self.interval = interval
        self.timer = None
        self.data = {}
        self.is_running = False
    
    @ui.refreshable
    def data_display(self):
        """Refreshable data display"""
        if not self.data:
            ui.label('Waiting for data...')
            return
        
        with ui.card().classes('w-full'):
            for key, value in self.data.items():
                ui.label(f"{key}: {value}")
    
    async def fetch_and_update(self):
        """Fetch data and update UI"""
        try:
            # Fetch latest data
            response = await safe_api_call(self.endpoint)
            
            if 'error' not in response:
                self.data = response
                self.data_display.refresh()  # Update UI
            else:
                logger.error(f"API error: {response['message']}")
                
        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
    
    async def start(self):
        """Start live streaming"""
        if self.is_running:
            return
        
        self.is_running = True
        self.timer = AsyncTimer(
            self.fetch_and_update,
            interval=self.interval
        )
        await self.timer.start()
        await safe_notification("Live stream started", type='success')
    
    async def stop(self):
        """Stop live streaming"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.timer:
            await self.timer.stop()
            self.timer = None
        
        await safe_notification("Live stream stopped", type='info')
    
    def render(self):
        """Render the streaming widget"""
        with ui.column().classes('w-full gap-4'):
            ui.label('Live Data Stream').classes('text-h5')
            
            with ui.row().classes('gap-2'):
                ui.button(
                    'Start Stream',
                    on_click=self.start,
                    icon='play_arrow'
                ).props('color=positive')
                
                ui.button(
                    'Stop Stream',
                    on_click=self.stop,
                    icon='stop'
                ).props('color=negative')
            
            self.data_display()


# Usage
def create_live_stream():
    stream = LiveDataStream(
        endpoint='http://localhost:8000/api/live-prices',
        interval=5.0
    )
    stream.render()
    return stream
```

---

## Quick Reference

### ✅ DO's
- Use `safe_api_call()` for all API requests
- Use `safe_sleep()` instead of `time.sleep()`
- Use `safe_db_query()` for database operations
- Use `@ui.refreshable` for dynamic content
- Use `AsyncTimer` for periodic updates
- Always handle errors gracefully
- Test with health check before committing

### ❌ DON'Ts
- Don't use `time.sleep()` in UI code
- Don't use `requests.get()` in event handlers
- Don't hardcode ports (use constants)
- Don't skip error handling
- Don't forget to call `.refresh()` after data updates

---

**For more templates and examples, see:**
- [ZERO_ERROR_ARCHITECT.md](ZERO_ERROR_ARCHITECT.md)
- [ZERO_ERROR_QUICK_START.md](ZERO_ERROR_QUICK_START.md)
