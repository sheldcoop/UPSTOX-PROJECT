"""
WSGI Entry Point for Production Deployment
Supports both API server and main application
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Determine which application to run based on environment variable
APP_MODE = os.getenv('APP_MODE', 'api').lower()

if APP_MODE == 'api':
    # Import API Server
    from scripts.api_server import app as application
    print("🚀 Starting API Server in production mode")
    
elif APP_MODE == 'frontend':
    # Import Frontend Application
    from app import app as application
    print("🚀 Starting Frontend Server in production mode")
    
elif APP_MODE == 'nicegui':
    # NiceGUI dashboard
    print("⚠️  NiceGUI should be run directly with 'python nicegui_dashboard.py'")
    print("   Falling back to API server...")
    from scripts.api_server import app as application
    
else:
    raise ValueError(f"Unknown APP_MODE: {APP_MODE}. Use 'api', 'frontend', or 'nicegui'")

# Ensure logs directory exists
Path('logs').mkdir(exist_ok=True)

# Application is now available as 'application' for WSGI servers
if __name__ == '__main__':
    # This won't be called when running under gunicorn
    # But useful for testing: python wsgi.py
    application.run(host='0.0.0.0', port=8080)
