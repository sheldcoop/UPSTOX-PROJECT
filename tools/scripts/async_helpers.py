"""
⚡ Zero-Error Architect - Async Helper Utilities
================================================

Prevents UI freezing in NiceGUI by providing safe async wrappers.
Use these helpers instead of blocking operations.

Usage:
    from scripts.utilities.async_helpers import safe_sleep, safe_api_call, safe_notification
    
    # Instead of time.sleep(2)
    await safe_sleep(2)
    
    # Instead of requests.get(url)
    data = await safe_api_call(url, method='GET')
    
    # Instead of ui.notify() in event handlers
    await safe_notification("Message", type="success")
"""

import asyncio
import functools
from typing import Any, Callable, Optional, Dict
import logging

try:
    from nicegui import ui, run
    NICEGUI_AVAILABLE = True
except ImportError:
    NICEGUI_AVAILABLE = False
    print("⚠️  NiceGUI not installed - some features unavailable")

logger = logging.getLogger(__name__)


async def safe_sleep(seconds: float):
    """
    Safe async sleep that doesn't block the UI.
    
    Args:
        seconds: Time to sleep in seconds
        
    Example:
        await safe_sleep(2)  # Sleep for 2 seconds without freezing UI
    """
    await asyncio.sleep(seconds)


async def safe_api_call(
    url: str,
    method: str = 'GET',
    headers: Optional[Dict] = None,
    data: Optional[Dict] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    Safe async API call using aiohttp (non-blocking).
    
    Args:
        url: API endpoint URL
        method: HTTP method (GET, POST, PUT, DELETE)
        headers: Optional headers dict
        data: Optional request data
        timeout: Request timeout in seconds
        
    Returns:
        Response data as dict
        
    Example:
        data = await safe_api_call('http://localhost:8000/api/health')
    """
    try:
        import aiohttp
    except ImportError:
        logger.error("aiohttp not installed - run: pip install aiohttp")
        raise
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API call failed: {response.status}")
                    return {
                        'error': f'HTTP {response.status}',
                        'message': await response.text()
                    }
    except asyncio.TimeoutError:
        logger.error(f"API call timeout: {url}")
        return {'error': 'timeout', 'message': 'Request timed out'}
    except Exception as e:
        logger.error(f"API call error: {e}")
        return {'error': 'exception', 'message': str(e)}


async def safe_io_bound(func: Callable, *args, **kwargs) -> Any:
    """
    Run a blocking I/O operation in a thread pool (non-blocking).
    
    Use this for any operation that might block:
    - Database queries
    - File I/O
    - Network requests with requests library
    
    Args:
        func: The blocking function to run
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Result of the function
        
    Example:
        import requests
        response = await safe_io_bound(requests.get, 'http://api.example.com')
    """
    if not NICEGUI_AVAILABLE:
        # Fallback to asyncio if NiceGUI not available
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))
    
    return await run.io_bound(func, *args, **kwargs)


async def safe_cpu_bound(func: Callable, *args, **kwargs) -> Any:
    """
    Run a CPU-intensive operation in a process pool (non-blocking).
    
    Use this for:
    - Heavy calculations
    - Data processing
    - ML model inference
    
    Args:
        func: The CPU-intensive function to run
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Result of the function
        
    Example:
        result = await safe_cpu_bound(calculate_metrics, data)
    """
    if not NICEGUI_AVAILABLE:
        # Fallback to asyncio if NiceGUI not available
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))
    
    return await run.cpu_bound(func, *args, **kwargs)


async def safe_notification(
    message: str,
    type: str = 'info',
    position: str = 'top',
    close_button: bool = True,
    timeout: float = 3.0
):
    """
    Show a notification safely in NiceGUI.
    
    Args:
        message: Notification message
        type: Type of notification ('info', 'success', 'warning', 'error')
        position: Position ('top', 'bottom', 'left', 'right')
        close_button: Show close button
        timeout: Auto-dismiss after seconds (0 = no auto-dismiss)
        
    Example:
        await safe_notification("Data saved!", type="success")
    """
    if not NICEGUI_AVAILABLE:
        print(f"[{type.upper()}] {message}")
        return
    
    ui.notify(
        message,
        type=type,
        position=position,
        close_button=close_button,
        timeout=timeout * 1000 if timeout > 0 else None  # Convert to ms
    )


def async_event_handler(func: Callable) -> Callable:
    """
    Decorator to make event handlers async-safe.
    
    Automatically wraps synchronous event handlers to be async.
    
    Example:
        @async_event_handler
        async def on_button_click():
            await safe_sleep(1)
            await safe_notification("Done!")
        
        ui.button('Click me', on_click=on_button_click)
    """
    if asyncio.iscoroutinefunction(func):
        return func
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await safe_io_bound(func, *args, **kwargs)
    
    return wrapper


class AsyncTimer:
    """
    Async timer for periodic tasks without blocking.
    
    Example:
        async def update_data():
            data = await fetch_latest_data()
            update_ui(data)
        
        timer = AsyncTimer(update_data, interval=5.0)
        await timer.start()
    """
    
    def __init__(self, callback: Callable, interval: float):
        self.callback = callback
        self.interval = interval
        self.running = False
        self.task = None
    
    async def start(self):
        """Start the timer"""
        self.running = True
        self.task = asyncio.create_task(self._run())
    
    async def stop(self):
        """Stop the timer"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
    
    async def _run(self):
        """Internal run loop"""
        while self.running:
            try:
                if asyncio.iscoroutinefunction(self.callback):
                    await self.callback()
                else:
                    await safe_io_bound(self.callback)
                await safe_sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Timer callback error: {e}")
                await safe_sleep(self.interval)


async def safe_db_query(query_func: Callable, *args, **kwargs) -> Any:
    """
    Execute database query safely without blocking UI.
    
    Args:
        query_func: Function that performs the DB query
        *args: Query function arguments
        **kwargs: Query function keyword arguments
        
    Returns:
        Query results
        
    Example:
        import sqlite3
        
        def get_data():
            conn = sqlite3.connect('market_data.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM candles LIMIT 10')
            return cursor.fetchall()
        
        data = await safe_db_query(get_data)
    """
    return await safe_io_bound(query_func, *args, **kwargs)


def blocking_operation_warning():
    """
    Decorator to warn about blocking operations in async context.
    
    Example:
        @blocking_operation_warning()
        def slow_function():
            time.sleep(5)  # Will log a warning
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.warning(
                f"⚠️  Blocking operation detected: {func.__name__}\n"
                f"   Consider using async alternative or wrap with safe_io_bound()"
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Example usage patterns for documentation
USAGE_EXAMPLES = """
# ============================================================================
# SAFE ASYNC PATTERNS FOR NICEGUI
# ============================================================================

# ❌ WRONG: Blocks the UI
def on_click():
    time.sleep(2)
    data = requests.get('http://api.example.com').json()
    ui.notify("Done!")

# ✅ CORRECT: Non-blocking async
async def on_click():
    await safe_sleep(2)
    data = await safe_api_call('http://api.example.com')
    await safe_notification("Done!", type="success")


# ❌ WRONG: Blocking database query
def load_data():
    conn = sqlite3.connect('db.sqlite')
    return conn.execute('SELECT * FROM data').fetchall()
    
ui.button('Load', on_click=load_data)

# ✅ CORRECT: Non-blocking database query
async def load_data():
    def query():
        conn = sqlite3.connect('db.sqlite')
        return conn.execute('SELECT * FROM data').fetchall()
    
    data = await safe_db_query(query)
    return data

ui.button('Load', on_click=load_data)


# ❌ WRONG: Blocking API call
def fetch_portfolio():
    response = requests.get('http://localhost:8000/api/portfolio')
    return response.json()

# ✅ CORRECT: Non-blocking API call
async def fetch_portfolio():
    return await safe_api_call('http://localhost:8000/api/portfolio')


# ============================================================================
# PERIODIC UPDATES WITHOUT BLOCKING
# ============================================================================

# Create timer for live data updates
async def update_prices():
    data = await safe_api_call('http://localhost:8000/api/live-prices')
    price_label.set_text(f"Price: {data['price']}")

timer = AsyncTimer(update_prices, interval=5.0)
await timer.start()  # Updates every 5 seconds
"""

if __name__ == '__main__':
    print("⚡ Async Helper Utilities for NiceGUI")
    print("=" * 80)
    print("\nThis module provides safe async wrappers to prevent UI freezing.")
    print("\nUsage examples:")
    print(USAGE_EXAMPLES)
