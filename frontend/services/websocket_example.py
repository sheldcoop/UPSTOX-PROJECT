"""
Example: Using WebSocket Service in NiceGUI Pages

This shows how to integrate real-time WebSocket updates
into your NiceGUI dashboard pages.
"""

from nicegui import ui
from frontend.services.websocket_service import get_websocket_service
import asyncio


async def option_chain_page_with_websocket():
    """Example: Option chain page with live updates"""
    
    # Get WebSocket service
    ws = get_websocket_service()
    
    # Create UI container for live data
    live_data_container = ui.column()
    
    # Define callback for option updates
    async def handle_options_update(data):
        """Handle incoming option chain updates"""
        symbol = data.get('symbol')
        option_data = data.get('data')
        timestamp = data.get('timestamp')
        
        # Update UI with new data
        with live_data_container:
            live_data_container.clear()
            ui.label(f"Live Data for {symbol}").classes("text-xl font-bold")
            ui.label(f"Updated: {timestamp}").classes("text-sm text-gray-500")
            
            # Display option data (customize as needed)
            if option_data:
                ui.json_editor({'content': {'json': option_data}})
    
    # Set the callback
    ws.on_options_update = handle_options_update
    
    # Connect and subscribe
    if not ws.connected:
        await ws.connect()
    
    await ws.subscribe_options("NIFTY")
    
    # Create UI
    with ui.card():
        ui.label("Real-time Option Chain").classes("text-2xl font-bold")
        
        # Symbol selector
        with ui.row():
            symbol_select = ui.select(
                ["NIFTY", "BANKNIFTY", "FINNIFTY"],
                value="NIFTY",
                label="Symbol"
            )
            
            async def change_symbol():
                # Unsubscribe from old, subscribe to new
                await ws.unsubscribe_options("NIFTY")
                await ws.subscribe_options(symbol_select.value)
            
            symbol_select.on_value_change(lambda: asyncio.create_task(change_symbol()))
        
        # Live data display
        live_data_container
    
    # Cleanup on page unload
    async def cleanup():
        await ws.disconnect()
    
    # Note: In real usage, you'd want to handle cleanup properly
    # when the user navigates away from the page


async def live_quotes_widget():
    """Example: Live quotes widget"""
    
    ws = get_websocket_service()
    
    # Create quote display
    quote_label = ui.label("Waiting for data...")
    
    # Handle quote updates
    async def handle_quote_update(data):
        symbol = data.get('symbol')
        quote = data.get('data', {})
        ltp = quote.get('ltp', 'N/A')
        change = quote.get('change', 'N/A')
        
        quote_label.text = f"{symbol}: ₹{ltp} ({change}%)"
    
    ws.on_quote_update = handle_quote_update
    
    # Connect and subscribe
    if not ws.connected:
        await ws.connect()
    
    await ws.subscribe_quote("NIFTY")
    
    return quote_label


# ============================================================================
# USAGE IN YOUR PAGES
# ============================================================================

"""
To use WebSocket in your existing pages:

1. Import the service:
   from frontend.services.websocket_service import get_websocket_service

2. In your page function, get the service:
   ws = get_websocket_service()

3. Set up callbacks:
   async def handle_update(data):
       # Update your UI with data
       pass
   
   ws.on_options_update = handle_update

4. Connect and subscribe:
   if not ws.connected:
       await ws.connect()
   
   await ws.subscribe_options("NIFTY")

5. Update your UI in the callback function using NiceGUI components

Example integration in option_chain.py:
--------------------------------------------
from frontend.services.websocket_service import get_websocket_service

def option_chain_page():
    ws = get_websocket_service()
    
    # Your existing UI code...
    data_container = ui.column()
    
    async def update_display(data):
        with data_container:
            data_container.clear()
            # Render updated option chain
            render_option_chain(data.get('data'))
    
    ws.on_options_update = update_display
    
    # Connect on page load
    asyncio.create_task(ws.connect())
    asyncio.create_task(ws.subscribe_options("NIFTY"))
"""
