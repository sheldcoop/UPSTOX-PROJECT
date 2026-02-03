"""
📝 Zero-Error Architect - Example Implementation
================================================

This file demonstrates how to use the Zero-Error Architect system
to build a new feature from scratch.

Feature: Live Portfolio Monitor
- Displays live portfolio data
- Updates every 5 seconds
- Shows real-time P&L
- Follows all Zero-Error principles
"""

from nicegui import ui
from scripts.utilities.async_helpers import (
    safe_api_call,
    safe_notification,
    safe_sleep,
    AsyncTimer,
    safe_io_bound
)
import logging
from datetime import datetime

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration (following Zero-Error principles)
API_BASE = 'http://localhost:8000'  # Backend API port
FRONTEND_PORT = 5001  # This page runs on port 5001


class LivePortfolioMonitor:
    """
    Live Portfolio Monitor following Zero-Error Architect principles
    
    Demonstrates:
    - Safe async API calls
    - Non-blocking UI updates
    - Proper error handling
    - Live data streaming
    - Refreshable components
    """
    
    def __init__(self):
        self.portfolio_data = {
            'total_value': 0.0,
            'pnl': 0.0,
            'pnl_percent': 0.0,
            'positions': []
        }
        self.timer = None
        self.is_streaming = False
        self.last_update = None
    
    @ui.refreshable
    def portfolio_summary(self):
        """Refreshable portfolio summary card"""
        with ui.card().classes('w-full'):
            ui.label('Portfolio Summary').classes('text-h6 mb-2')
            
            if not self.last_update:
                ui.label('No data yet - click "Start Live Updates"')
                return
            
            # Display summary
            with ui.row().classes('w-full justify-between'):
                with ui.column():
                    ui.label('Total Value')
                    ui.label(f'₹{self.portfolio_data["total_value"]:,.2f}').classes('text-h5')
                
                with ui.column():
                    pnl = self.portfolio_data['pnl']
                    color = 'text-green' if pnl >= 0 else 'text-red'
                    ui.label('P&L')
                    ui.label(f'₹{pnl:,.2f}').classes(f'text-h5 {color}')
                
                with ui.column():
                    pnl_pct = self.portfolio_data['pnl_percent']
                    color = 'text-green' if pnl_pct >= 0 else 'text-red'
                    ui.label('P&L %')
                    ui.label(f'{pnl_pct:.2f}%').classes(f'text-h5 {color}')
            
            ui.label(f'Last updated: {self.last_update}').classes('text-caption mt-2')
    
    @ui.refreshable
    def positions_table(self):
        """Refreshable positions table"""
        with ui.card().classes('w-full'):
            ui.label('Positions').classes('text-h6 mb-2')
            
            positions = self.portfolio_data.get('positions', [])
            
            if not positions:
                ui.label('No positions')
                return
            
            # Table headers
            with ui.row().classes('w-full gap-2 font-bold'):
                ui.label('Symbol').classes('w-32')
                ui.label('Quantity').classes('w-24')
                ui.label('Avg Price').classes('w-32')
                ui.label('Current Price').classes('w-32')
                ui.label('P&L').classes('w-32')
            
            # Table rows
            for position in positions:
                pnl = position.get('pnl', 0)
                pnl_color = 'text-green' if pnl >= 0 else 'text-red'
                
                with ui.row().classes('w-full gap-2'):
                    ui.label(position['symbol']).classes('w-32')
                    ui.label(str(position['quantity'])).classes('w-24')
                    ui.label(f"₹{position['avg_price']:.2f}").classes('w-32')
                    ui.label(f"₹{position['current_price']:.2f}").classes('w-32')
                    ui.label(f"₹{pnl:.2f}").classes(f'w-32 {pnl_color}')
    
    async def fetch_portfolio_data(self):
        """
        Fetch portfolio data from backend API
        
        Demonstrates:
        - Safe API call (non-blocking)
        - Proper error handling
        - User-friendly error messages
        """
        try:
            logger.info("Fetching portfolio data...")
            
            # Safe, non-blocking API call
            response = await safe_api_call(
                f'{API_BASE}/api/portfolio',
                method='GET',
                timeout=10.0
            )
            
            # Check for errors
            if 'error' in response:
                error_msg = response.get('message', 'Unknown error')
                logger.error(f"API error: {error_msg}")
                
                # User-friendly error message
                if 'Connection refused' in error_msg:
                    await safe_notification(
                        "Backend server is not running. Start with: python scripts/api_server.py",
                        type='error',
                        timeout=5
                    )
                else:
                    await safe_notification(
                        f"Error: {error_msg}",
                        type='error'
                    )
                return False
            
            # Update portfolio data
            self.portfolio_data = response
            self.last_update = datetime.now().strftime('%H:%M:%S')
            
            logger.info("Portfolio data updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fetch portfolio data: {e}", exc_info=True)
            await safe_notification(
                "Failed to load portfolio data",
                type='error'
            )
            return False
    
    async def update_display(self):
        """
        Update the display with latest data
        
        Demonstrates:
        - Refreshing UI components
        - Non-blocking updates
        """
        success = await self.fetch_portfolio_data()
        
        if success:
            # Refresh both components
            self.portfolio_summary.refresh()
            self.positions_table.refresh()
    
    async def start_live_updates(self):
        """
        Start live updates timer
        
        Demonstrates:
        - AsyncTimer for periodic updates
        - Non-blocking periodic tasks
        """
        if self.is_streaming:
            await safe_notification("Live updates already running", type='warning')
            return
        
        # Initial fetch
        await self.update_display()
        
        # Start timer for periodic updates
        self.timer = AsyncTimer(
            callback=self.update_display,
            interval=5.0  # Update every 5 seconds
        )
        await self.timer.start()
        
        self.is_streaming = True
        await safe_notification(
            "Live updates started (5s interval)",
            type='success'
        )
        logger.info("Live updates started")
    
    async def stop_live_updates(self):
        """Stop live updates timer"""
        if not self.is_streaming:
            await safe_notification("Live updates not running", type='warning')
            return
        
        if self.timer:
            await self.timer.stop()
            self.timer = None
        
        self.is_streaming = False
        await safe_notification("Live updates stopped", type='info')
        logger.info("Live updates stopped")
    
    async def manual_refresh(self):
        """Manual refresh button handler"""
        await safe_notification("Refreshing...", type='info', timeout=1)
        await self.update_display()
        await safe_notification("Refreshed!", type='success', timeout=1)
    
    def render(self):
        """
        Render the complete UI
        
        Demonstrates:
        - Proper UI structure
        - Button event handlers (async)
        - Responsive layout
        """
        with ui.column().classes('w-full gap-4 p-4'):
            # Header
            ui.label('Live Portfolio Monitor').classes('text-h4')
            ui.label('Zero-Error Architect Example').classes('text-subtitle2 text-grey')
            
            # Control buttons
            with ui.row().classes('gap-2'):
                ui.button(
                    'Start Live Updates',
                    on_click=self.start_live_updates,
                    icon='play_arrow'
                ).props('color=positive')
                
                ui.button(
                    'Stop Live Updates',
                    on_click=self.stop_live_updates,
                    icon='stop'
                ).props('color=negative')
                
                ui.button(
                    'Manual Refresh',
                    on_click=self.manual_refresh,
                    icon='refresh'
                ).props('color=primary')
            
            # Display components
            self.portfolio_summary()
            self.positions_table()
            
            # Footer with tips
            with ui.card().classes('w-full bg-blue-1'):
                ui.label('💡 Tips:').classes('font-bold')
                ui.label('• This example follows all Zero-Error Architect principles')
                ui.label('• UI never freezes - all operations are async')
                ui.label('• Errors are handled gracefully with user-friendly messages')
                ui.label('• Ports are correctly configured (frontend: 5001, backend: 8000)')


# ============================================================================
# Main Application
# ============================================================================

async def main():
    """Main application entry point"""
    
    # Set page title
    ui.page_title = 'Live Portfolio Monitor - Zero-Error Example'
    
    # Create and render the monitor
    monitor = LivePortfolioMonitor()
    monitor.render()
    
    # Run the UI
    ui.run(
        port=FRONTEND_PORT,
        title='Live Portfolio Monitor',
        reload=False  # Disable reload in production
    )


# ============================================================================
# How to Run This Example
# ============================================================================
"""
1. Ensure backend is running:
   python scripts/api_server.py

2. Run this example:
   python examples/zero_error_example.py

3. Open browser:
   http://localhost:5001

4. Click "Start Live Updates" to see it in action!

Expected Behavior:
- ✅ UI stays responsive
- ✅ Data updates every 5 seconds
- ✅ Errors are handled gracefully
- ✅ Can stop/start updates anytime
- ✅ Manual refresh works instantly

Common Issues & Solutions:
- Backend not running? Start it with: python scripts/api_server.py
- Port already in use? Check with: lsof -i :5001
- Dependencies missing? Run: pip install nicegui aiohttp
"""

if __name__ == '__main__':
    # Before running, do a quick check
    print("\n" + "=" * 80)
    print("🛡️  Zero-Error Architect - Example Implementation")
    print("=" * 80)
    print("\n📋 Pre-Flight Checklist:")
    print("  ✓ Backend API should be running on port 8000")
    print("  ✓ This will start on port 5001")
    print("  ✓ Press Ctrl+C to stop")
    print("\n" + "=" * 80 + "\n")
    
    # Note: In actual implementation, uncomment the line below
    # import asyncio
    # asyncio.run(main())
    
    print("💡 To run this example:")
    print("   1. Uncomment the asyncio.run(main()) line above")
    print("   2. Save the file")
    print("   3. Run: python examples/zero_error_example.py")
    print("\n" + "=" * 80)
