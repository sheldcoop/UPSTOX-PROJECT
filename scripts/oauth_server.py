"""
Flask OAuth Server for Upstox Authentication
Handles OAuth flow with browser-based authorization
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, redirect, jsonify
from auth_manager import AuthManager
import logging
import webbrowser

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
auth_manager = AuthManager()

# --- DEBUGGING MIDDLEWARE ---
@app.before_request
def log_request_info():
    logger.debug('=' * 40)
    logger.debug(f'Incoming Request: {request.method} {request.path}')
    logger.debug(f'Headers: {dict(request.headers)}')
    logger.debug(f'Args: {dict(request.args)}')
    logger.debug('=' * 40)

@app.route('/debug/config')
def debug_config():
    """Endpoint to verify what the server THINKS its config is"""
    return jsonify({
        "configured_redirect_uri": auth_manager.redirect_uri,
        "env_redirect_uri": os.getenv("UPSTOX_REDIRECT_URI"),
        "flask_host_port": "0.0.0.0:5050"
    })

@app.route('/auth/start')
def auth_start():
    """Start OAuth flow by redirecting to Upstox"""
    try:
        # Force reload redirect_uri from env to ensure it matches
        auth_manager.redirect_uri = os.getenv("UPSTOX_REDIRECT_URI", "http://localhost:5050/auth/callback")
        
        auth_url = auth_manager.get_authorization_url()
        logger.info(f"✅ Generating Auth URL with redirect_uri: {auth_manager.redirect_uri}")
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"❌ Error starting auth: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback with authorization code"""
    try:
        # Get authorization code from query params
        code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            logger.error(f"❌ Authorization failed: {error}")
            return f"""
            <html>
            <body style="font-family: Arial; padding: 50px; text-align: center;">
                <h1 style="color: red;">❌ Authorization Failed</h1>
                <p>Error: {error}</p>
                <p>Please try again.</p>
            </body>
            </html>
            """, 400
        
        if not code:
            logger.error("❌ No authorization code received")
            return jsonify({"error": "No authorization code"}), 400
        
        logger.info(f"🔄 Received authorization code, exchanging for token...")
        
        # Exchange code for tokens
        token_data = auth_manager.exchange_code_for_token(code)
        
        # Save tokens to database
        auth_manager.save_token("default", token_data)
        
        logger.info("✅ Authentication successful!")
        
        # Success page
        return f"""
        <html>
        <body style="font-family: Arial; padding: 50px; text-align: center;">
            <h1 style="color: green;">✅ Authentication Successful!</h1>
            <p>Your Upstox account is now connected.</p>
            <p>Access token: <code>{token_data['access_token'][:30]}...</code></p>
            <p style="margin-top: 30px;">You can close this window and return to your terminal.</p>
            <script>
                setTimeout(function() {{
                    window.close();
                }}, 3000);
            </script>
        </body>
        </html>
        """
    
    except Exception as e:
        logger.error(f"❌ Request failed: {e}", exc_info=True)
        return f"""
        <html>
        <body style="font-family: Arial; padding: 50px; text-align: center;">
            <h1 style="color: red;">❌ Error</h1>
            <p>{str(e)}</p>
        </body>
        </html>
        """, 500


@app.route('/auth/status')
def auth_status():
    """Check authentication status"""
    try:
        token = auth_manager.get_valid_token()
        
        if token:
            return jsonify({
                "authenticated": True,
                "token_preview": token[:30] + "...",
                "message": "Valid token found"
            })
        else:
            return jsonify({
                "authenticated": False,
                "message": "No valid token - please authenticate"
            }), 401
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 UPSTOX OAUTH SERVER RUNNING")
    print("   Open: http://localhost:5050/auth/start")
    print("=" * 60)
    
    # Auto-open browser if requested
    if "--open-browser" in sys.argv or "-o" in sys.argv:
        webbrowser.open("http://localhost:5050/auth/start")
    
    # Use port 5050 to avoid macOS AirPlay (5000) and common dev ports (8000/8080)
    app.run(host="0.0.0.0", port=5050, debug=True)
