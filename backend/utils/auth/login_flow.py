"""
Interactive Login Flow
----------------------
Helper script to manually generate an Upstox Auth Token.
Usage:
    python3 backend/utils/auth/login_flow.py
"""

import sys
import os
import urllib.parse

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.utils.auth.manager import AuthManager

def main():
    print("\n🔐 Oracle Authentication Helper")
    print("=================================")
    
    auth = AuthManager()
    
    # 1. Get URL
    url = auth.get_authorization_url()
    
    print("\nStep 1: Open this URL in your browser:")
    print(f"\n{url}\n")
    
    print("Step 2: Login with your Upstox credentials.")
    print("Step 3: You will be redirected to a page (likely 404 or white screen).")
    print("Step 4: Copy the FULL URL from the address bar and paste it below.")
    
    full_url = input("\n🔗 Paste Redirected URL here: ").strip()
    
    # 2. Extract Code
    try:
        parsed = urllib.parse.urlparse(full_url)
        params = urllib.parse.parse_qs(parsed.query)
        code = params.get('code', [None])[0]
        
        if not code:
            print("❌ Error: Could not find 'code' in the URL.")
            return
            
        print(f"\n✅ Auth Code extracted: {code[:10]}...")
        
        # 3. Exchange for Token
        token_data = auth.exchange_code_for_token(code)
        
        # 4. Save
        auth.save_token("default", token_data)
        
        print("\n🎉 Success! Auth Token saved to database.")
        print("You can now run the Option Chain Poller.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
