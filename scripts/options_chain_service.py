"""
Options Chain Service - Fetch and process live options data from Upstox
Handles market hours, Greeks calculation, and real-time updates
"""

import logging
import requests
import sys
import os
from datetime import datetime, timedelta, time as dt_time
from typing import Dict, List, Optional, Tuple
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.auth_manager import AuthManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/options_chain.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory
Path('logs').mkdir(exist_ok=True)


class OptionsChainService:
    """Service for fetching and processing options chain data from Upstox"""
    
    def __init__(self, db_path: str = 'market_data.db'):
        self.db_path = db_path
        self.base_url = "https://api.upstox.com/v2"
        self.auth_manager = AuthManager(db_path=db_path)
        logger.info(f"Initialized OptionsChainService with db={db_path}")
    
    def is_market_open(self) -> Tuple[bool, str]:
        """
        Check if Indian stock market is currently open
        NSE: Mon-Fri 9:15 AM - 3:30 PM IST
        Returns: (is_open, message)
        """
        now = datetime.now()
        current_time = now.time()
        weekday = now.weekday()  # 0 = Monday, 6 = Sunday
        
        # Market closed on weekends
        if weekday >= 5:  # Saturday or Sunday
            logger.debug("Market closed: Weekend")
            return False, "Market is closed on weekends"
        
        # Market hours: 9:15 AM - 3:30 PM IST
        market_open = dt_time(9, 15)
        market_close = dt_time(15, 30)
        
        if current_time < market_open:
            logger.debug(f"Market closed: Before opening (current: {current_time})")
            return False, f"Market opens at 9:15 AM (current time: {current_time.strftime('%H:%M')})"
        
        if current_time > market_close:
            logger.debug(f"Market closed: After closing (current: {current_time})")
            return False, f"Market closed at 3:30 PM (current time: {current_time.strftime('%H:%M')})"
        
        logger.debug("Market is open")
        return True, "Market is open"
    
    def get_option_chain(
        self,
        symbol: str,
        expiry_date: Optional[str] = None
    ) -> Dict:
        """
        Fetch options chain from Upstox API
        
        Args:
            symbol: Underlying symbol (e.g., 'NIFTY', 'BANKNIFTY', 'RELIANCE')
            expiry_date: Expiry date in YYYY-MM-DD format (optional, uses nearest expiry if not provided)
        
        Returns:
            {
                'symbol': str,
                'expiry_date': str,
                'underlying_price': float,
                'timestamp': str,
                'market_open': bool,
                'strikes': [
                    {
                        'strike': float,
                        'call': {...},
                        'put': {...}
                    }
                ]
            }
        """
        logger.info(f"[OPTIONS] Fetching chain for {symbol}, expiry={expiry_date}")
        
        # Check market status
        market_open, market_msg = self.is_market_open()
        logger.info(f"[OPTIONS] Market status: {market_msg}")
        
        # For now, return mock data quickly since Upstox API might not have option chain endpoint
        # or might require different authentication
        logger.info("[OPTIONS] Using mock data (Upstox option chain API not yet configured)")
        return self._mock_option_chain(symbol, expiry_date, market_open)
        
        # TODO: Uncomment below when Upstox option chain API is properly configured
        """
        try:
            # Get valid token
            token = self.auth_manager.get_valid_token()
            if not token:
                logger.error("[OPTIONS] No valid Upstox token available")
                return self._mock_option_chain(symbol, expiry_date, market_open)
            
            # Construct API request
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }
            
            # Build URL
            # Upstox API endpoint: https://api.upstox.com/v2/option/chain?instrument_key=NSE_INDEX|Nifty%2050&expiry_date=2025-02-06
            params = {
                'instrument_key': self._get_instrument_key(symbol)
            }
            
            if expiry_date:
                params['expiry_date'] = expiry_date
            
            logger.debug(f"[OPTIONS] API request: {self.base_url}/option/chain, params={params}")
            
            response = requests.get(
                f"{self.base_url}/option/chain",
                headers=headers,
                params=params,
                timeout=5  # Reduced timeout
            )
            
            logger.debug(f"[OPTIONS] API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"[OPTIONS] Successfully fetched chain data")
                return self._process_upstox_response(data, symbol, market_open)
            
            elif response.status_code == 401:
                logger.warning("[OPTIONS] Token expired, attempting refresh")
                # Token expired, try refresh
                token = self.auth_manager.get_valid_token(force_refresh=True)
                if token:
                    # Retry with new token
                    headers['Authorization'] = f'Bearer {token}'
                    response = requests.get(
                        f"{self.base_url}/option/chain",
                        headers=headers,
                        params=params,
                        timeout=5
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return self._process_upstox_response(data, symbol, market_open)
            
            # If API fails, return mock data
            logger.warning(f"[OPTIONS] API failed with status {response.status_code}, using mock data")
            return self._mock_option_chain(symbol, expiry_date, market_open)
            
        except Exception as e:
            logger.error(f"[OPTIONS] Error fetching chain: {e}", exc_info=True)
            # Return mock data on error
            return self._mock_option_chain(symbol, expiry_date, market_open)
        """
    
    def _get_instrument_key(self, symbol: str) -> str:
        """Convert symbol to Upstox instrument key"""
        # Index symbols
        if symbol.upper() == 'NIFTY':
            return 'NSE_INDEX|Nifty%2050'
        elif symbol.upper() == 'BANKNIFTY':
            return 'NSE_INDEX|Nifty%20Bank'
        elif symbol.upper() == 'FINNIFTY':
            return 'NSE_INDEX|Nifty%20Fin%20Services'
        else:
            # Stock options
            return f'NSE_EQ|{symbol.upper()}'
    
    def _process_upstox_response(self, data: Dict, symbol: str, market_open: bool) -> Dict:
        """Process Upstox API response into standardized format"""
        logger.debug("[OPTIONS] Processing Upstox response")
        
        # Extract data from Upstox response
        # Actual structure will depend on Upstox API format
        # This is a template - adjust based on real API response
        
        strikes_data = []
        
        # Parse Upstox response
        # TODO: Update this based on actual Upstox API response structure
        option_data = data.get('data', {})
        
        for strike_data in option_data.get('strikes', []):
            strike = {
                'strike': strike_data.get('strike_price'),
                'call': {
                    'ltp': strike_data.get('call', {}).get('last_price'),
                    'volume': strike_data.get('call', {}).get('volume'),
                    'oi': strike_data.get('call', {}).get('open_interest'),
                    'iv': strike_data.get('call', {}).get('iv'),
                    'delta': strike_data.get('call', {}).get('delta'),
                    'gamma': strike_data.get('call', {}).get('gamma'),
                    'theta': strike_data.get('call', {}).get('theta'),
                    'vega': strike_data.get('call', {}).get('vega'),
                    'bid': strike_data.get('call', {}).get('bid'),
                    'ask': strike_data.get('call', {}).get('ask'),
                },
                'put': {
                    'ltp': strike_data.get('put', {}).get('last_price'),
                    'volume': strike_data.get('put', {}).get('volume'),
                    'oi': strike_data.get('put', {}).get('open_interest'),
                    'iv': strike_data.get('put', {}).get('iv'),
                    'delta': strike_data.get('put', {}).get('delta'),
                    'gamma': strike_data.get('put', {}).get('gamma'),
                    'theta': strike_data.get('put', {}).get('theta'),
                    'vega': strike_data.get('put', {}).get('vega'),
                    'bid': strike_data.get('put', {}).get('bid'),
                    'ask': strike_data.get('put', {}).get('ask'),
                }
            }
            strikes_data.append(strike)
        
        result = {
            'symbol': symbol,
            'expiry_date': option_data.get('expiry_date'),
            'underlying_price': option_data.get('underlying_value'),
            'timestamp': datetime.now().isoformat(),
            'market_open': market_open,
            'strikes': strikes_data
        }
        
        logger.info(f"[OPTIONS] Processed {len(strikes_data)} strikes")
        return result
    
    def _mock_option_chain(self, symbol: str, expiry_date: Optional[str], market_open: bool) -> Dict:
        """
        Generate realistic mock option chain data
        Used when market is closed or API is unavailable
        """
        logger.warning("[OPTIONS] Generating mock option chain data")
        
        # Mock underlying price based on symbol
        underlying_prices = {
            'NIFTY': 21800.00,
            'BANKNIFTY': 46500.00,
            'FINNIFTY': 19800.00,
            'RELIANCE': 2850.00,
            'INFY': 1450.00,
            'TCS': 3650.00,
        }
        
        underlying_price = underlying_prices.get(symbol.upper(), 1000.00)
        
        # Generate strikes around current price
        if symbol.upper() in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
            strike_interval = 100 if symbol.upper() == 'NIFTY' else 100
            num_strikes = 15
        else:
            strike_interval = 50
            num_strikes = 11
        
        atm_strike = round(underlying_price / strike_interval) * strike_interval
        strikes = [atm_strike + (i - num_strikes // 2) * strike_interval for i in range(num_strikes)]
        
        strikes_data = []
        for strike in strikes:
            # Calculate moneyness
            moneyness = (underlying_price - strike) / strike
            
            # Mock option prices based on moneyness
            call_ltp = max(0, (underlying_price - strike) + abs(moneyness) * 50) if strike < underlying_price else abs(moneyness) * 30
            put_ltp = max(0, (strike - underlying_price) + abs(moneyness) * 50) if strike > underlying_price else abs(moneyness) * 30
            
            # Mock Greeks (simplified Black-Scholes approximation)
            call_delta = 0.5 + moneyness if moneyness > 0 else 0.5 * (1 + moneyness)
            put_delta = call_delta - 1
            
            gamma = 0.05 if abs(moneyness) < 0.02 else 0.02  # High gamma near ATM
            theta = -20 if abs(moneyness) < 0.02 else -10  # High theta near ATM
            vega = 15 if abs(moneyness) < 0.02 else 8
            iv = 18 + abs(moneyness) * 10  # IV smile
            
            strikes_data.append({
                'strike': strike,
                'call': {
                    'ltp': round(call_ltp, 2),
                    'volume': int(10000 * (1 - abs(moneyness))) if abs(moneyness) < 0.1 else 1000,
                    'oi': int(50000 * (1 - abs(moneyness))) if abs(moneyness) < 0.1 else 5000,
                    'iv': round(iv, 2),
                    'delta': round(call_delta, 3),
                    'gamma': round(gamma, 3),
                    'theta': round(theta, 2),
                    'vega': round(vega, 2),
                    'bid': round(call_ltp * 0.98, 2),
                    'ask': round(call_ltp * 1.02, 2),
                },
                'put': {
                    'ltp': round(put_ltp, 2),
                    'volume': int(10000 * (1 - abs(moneyness))) if abs(moneyness) < 0.1 else 1000,
                    'oi': int(50000 * (1 - abs(moneyness))) if abs(moneyness) < 0.1 else 5000,
                    'iv': round(iv, 2),
                    'delta': round(put_delta, 3),
                    'gamma': round(gamma, 3),
                    'theta': round(theta, 2),
                    'vega': round(vega, 2),
                    'bid': round(put_ltp * 0.98, 2),
                    'ask': round(put_ltp * 1.02, 2),
                }
            })
        
        # Use next weekly expiry if not provided
        if not expiry_date:
            # Find next Friday
            today = datetime.now()
            days_ahead = 4 - today.weekday()  # 4 = Friday
            if days_ahead <= 0:
                days_ahead += 7
            next_friday = today + timedelta(days=days_ahead)
            expiry_date = next_friday.strftime('%Y-%m-%d')
        
        result = {
            'symbol': symbol,
            'expiry_date': expiry_date,
            'underlying_price': underlying_price,
            'timestamp': datetime.now().isoformat(),
            'market_open': market_open,
            'data_source': 'mock',
            'strikes': strikes_data
        }
        
        logger.info(f"[OPTIONS] Generated mock chain: {len(strikes_data)} strikes, underlying={underlying_price}")
        return result


# Testing
if __name__ == '__main__':
    service = OptionsChainService()
    
    # Test market status
    is_open, msg = service.is_market_open()
    print(f"Market Status: {msg}")
    
    # Test option chain fetch
    chain = service.get_option_chain('NIFTY')
    print(f"\nOption Chain for {chain['symbol']}:")
    print(f"Underlying: ₹{chain['underlying_price']}")
    print(f"Expiry: {chain['expiry_date']}")
    print(f"Strikes: {len(chain['strikes'])}")
    print(f"Data source: {chain.get('data_source', 'live')}")
