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
from backend.utils.auth.manager import AuthManager
from backend.utils.auth.headers import build_bearer_headers

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/options_chain.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Create logs directory
Path("logs").mkdir(exist_ok=True)


class OptionsChainService:
    """Service for fetching and processing options chain data from Upstox"""

    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path
        self.base_url = "https://api.upstox.com/v2"
        self.auth_manager = AuthManager(db_path=db_path)
        logger.info(f"Initialized OptionsChainService with db={db_path}")

    def get_expiry_dates(self, instrument_key: str) -> List[str]:
        """
        Fetch available expiry dates for an instrument.
        Uses active contracts api or option chain API to find valid dates.
        """
        try:
            # Strategy: Use v2/option/contract to get all contracts, then extract unique expiries
            token = self.auth_manager.get_valid_token()
            if not token:
                return []

            headers = build_bearer_headers(token, include_json=True)
            url = f"{self.base_url}/option/contract"
            params = {"instrument_key": instrument_key}

            response = requests.get(url, headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json().get("data", [])
                # Extract unique expiry dates
                dates = sorted(list(set([c["expiry"] for c in data])))
                return dates
            return []
        except Exception as e:
            logger.error(f"Error fetching expiries: {e}")
            return []

    def get_option_greeks(self, instrument_keys: List[str]) -> Dict:
        """
        Fetch detailed option greeks using v3 API.
        Response includes: theta, delta, gamma, vega, iv, etc.
        """
        try:
            token = self.auth_manager.get_valid_token()
            if not token:
                logger.error("No token for greeks")
                return {}

            # v3 endpoint
            url = "https://api.upstox.com/v3/market-quote/option-greek"
            headers = build_bearer_headers(token, include_json=True)

            # API supports comma separated keys
            keys_str = ",".join(instrument_keys)
            params = {"instrument_key": keys_str}

            response = requests.get(url, headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json().get("data", {})
                return data
            else:
                logger.error(
                    f"Greeks API failed: {response.status_code} {response.text}"
                )
                return {}
        except Exception as e:
            logger.error(f"Error fetching greeks: {e}")
            return {}

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
            return (
                False,
                f"Market opens at 9:15 AM (current time: {current_time.strftime('%H:%M')})",
            )

        if current_time > market_close:
            logger.debug(f"Market closed: After closing (current: {current_time})")
            return (
                False,
                f"Market closed at 3:30 PM (current time: {current_time.strftime('%H:%M')})",
            )

        logger.debug("Market is open")
        return True, "Market is open"

    def get_option_chain(self, symbol: str, expiry_date: Optional[str] = None) -> Dict:
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

        # For now, try to fetch real data
        logger.info(f"[OPTIONS] Fetching live data for {symbol} Expiry: {expiry_date}")

        try:
            # Get valid token
            token = self.auth_manager.get_valid_token()
            if not token:
                logger.error("[OPTIONS] No valid Upstox token available")
                return self._mock_option_chain(symbol, expiry_date, market_open)

            # Construct API request
            headers = build_bearer_headers(token, include_json=True)

            # Map symbol to key
            inst_key = self._get_instrument_key(symbol)
            params = {"instrument_key": inst_key}

            if expiry_date:
                params["expiry_date"] = expiry_date

            # If no expiry provided for Live API, we MUST provide one or the API might fail or return default?
            # Documentation says expiry_date is REQUIRED query param.
            if not expiry_date:
                # auto-fetch expiries
                dates = self.get_expiry_dates(inst_key)
                if dates:
                    params["expiry_date"] = dates[0]
                    # Also update result to show we picked this date
                    expiry_date = dates[0]
                else:
                    logger.warning("Could not find expiry dates, defaulting to mock")
                    return self._mock_option_chain(symbol, expiry_date, market_open)

            logger.debug(
                f"[OPTIONS] API request: {self.base_url}/option/chain, params={params}"
            )

            response = requests.get(
                f"{self.base_url}/option/chain",
                headers=headers,
                params=params,
                timeout=5,
            )

            if response.status_code == 200:
                data = response.json()
                # Parse
                return self._process_upstox_response(data, symbol, market_open)

            logger.warning(f"API Failed {response.status_code}: {response.text}")
            return self._mock_option_chain(symbol, expiry_date, market_open)

        except Exception as e:
            logger.error(f"[OPTIONS] Error fetching chain: {e}", exc_info=True)
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
        if symbol.upper() == "NIFTY":
            return "NSE_INDEX|Nifty%2050"
        elif symbol.upper() == "BANKNIFTY":
            return "NSE_INDEX|Nifty%20Bank"
        elif symbol.upper() == "FINNIFTY":
            return "NSE_INDEX|Nifty%20Fin%20Services"
        else:
            # Stock options
            return f"NSE_EQ|{symbol.upper()}"

    def _process_upstox_response(
        self, data: Dict, symbol: str, market_open: bool
    ) -> Dict:
        """Process Upstox API response into standardized format"""
        # data structure based on v2 API documentation
        resp_data = data.get("data", [])
        if not resp_data:
            return self._mock_option_chain(symbol, None, market_open)

        # The v2 API returns a LIST of objects (one per strike/expiry combo? or one object with strikes?)
        # Doc says Response Body: { status: success, data: [ { expiry, strike_price, call_options, put_options ... } ] }
        # So it is a list of strikes.

        strikes_data = []
        underlying_price = 0
        expiry_date = ""

        # Sort by strike price
        try:
            sorted_data = sorted(resp_data, key=lambda x: x.get("strike_price", 0))

            for item in sorted_data:
                # Capture metadata from first item
                if not underlying_price:
                    underlying_price = item.get("underlying_spot_price", 0)
                if not expiry_date:
                    expiry_date = item.get("expiry", "")

                # Call Data
                call = item.get("call_options", {})
                call_md = call.get("market_data", {})
                call_greeks = call.get("option_greeks", {})

                # Put Data
                put = item.get("put_options", {})
                put_md = put.get("market_data", {})
                put_greeks = put.get("option_greeks", {})

                strike = {
                    "strike": item.get("strike_price"),
                    "call": {
                        "instrument_key": call.get("instrument_key"),
                        "ltp": call_md.get("ltp"),
                        "volume": call_md.get("volume"),
                        "oi": call_md.get("oi"),
                        "iv": call_greeks.get("iv"),
                        "delta": call_greeks.get("delta"),
                        "gamma": call_greeks.get("gamma"),
                        "theta": call_greeks.get("theta"),
                        "vega": call_greeks.get("vega"),
                        "bid": call_md.get("bid_price"),
                        "ask": call_md.get("ask_price"),
                    },
                    "put": {
                        "instrument_key": put.get("instrument_key"),
                        "ltp": put_md.get("ltp"),
                        "volume": put_md.get("volume"),
                        "oi": put_md.get("oi"),
                        "iv": put_greeks.get("iv"),
                        "delta": put_greeks.get("delta"),
                        "gamma": put_greeks.get("gamma"),
                        "theta": put_greeks.get("theta"),
                        "vega": put_greeks.get("vega"),
                        "bid": put_md.get("bid_price"),
                        "ask": put_md.get("ask_price"),
                    },
                }
                strikes_data.append(strike)

        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return self._mock_option_chain(symbol, None, market_open)

        result = {
            "symbol": symbol,
            "expiry_date": expiry_date,
            "underlying_price": underlying_price,
            "timestamp": datetime.now().isoformat(),
            "market_open": market_open,
            "strikes": strikes_data,
        }

        logger.info(f"[OPTIONS] Processed {len(strikes_data)} strikes")
        return result

    def _mock_option_chain(
        self, symbol: str, expiry_date: Optional[str], market_open: bool
    ) -> Dict:
        """
        Generate realistic mock option chain data
        Used when market is closed or API is unavailable
        """
        logger.warning("[OPTIONS] Generating mock option chain data")

        # Mock underlying price based on symbol
        underlying_prices = {
            "NIFTY": 21800.00,
            "BANKNIFTY": 46500.00,
            "FINNIFTY": 19800.00,
            "RELIANCE": 2850.00,
            "INFY": 1450.00,
            "TCS": 3650.00,
        }

        underlying_price = underlying_prices.get(symbol.upper(), 1000.00)

        # Generate strikes around current price
        if symbol.upper() in ["NIFTY", "BANKNIFTY", "FINNIFTY"]:
            strike_interval = 100 if symbol.upper() == "NIFTY" else 100
            num_strikes = 15
        else:
            strike_interval = 50
            num_strikes = 11

        atm_strike = round(underlying_price / strike_interval) * strike_interval
        strikes = [
            atm_strike + (i - num_strikes // 2) * strike_interval
            for i in range(num_strikes)
        ]

        strikes_data = []
        for strike in strikes:
            # Calculate moneyness
            moneyness = (underlying_price - strike) / strike

            # Mock option prices based on moneyness
            call_ltp = (
                max(0, (underlying_price - strike) + abs(moneyness) * 50)
                if strike < underlying_price
                else abs(moneyness) * 30
            )
            put_ltp = (
                max(0, (strike - underlying_price) + abs(moneyness) * 50)
                if strike > underlying_price
                else abs(moneyness) * 30
            )

            # Mock Greeks (simplified Black-Scholes approximation)
            call_delta = 0.5 + moneyness if moneyness > 0 else 0.5 * (1 + moneyness)
            put_delta = call_delta - 1

            gamma = 0.05 if abs(moneyness) < 0.02 else 0.02  # High gamma near ATM
            theta = -20 if abs(moneyness) < 0.02 else -10  # High theta near ATM
            vega = 15 if abs(moneyness) < 0.02 else 8
            iv = 18 + abs(moneyness) * 10  # IV smile

            strikes_data.append(
                {
                    "strike": strike,
                    "call": {
                        "ltp": round(call_ltp, 2),
                        "volume": (
                            int(10000 * (1 - abs(moneyness)))
                            if abs(moneyness) < 0.1
                            else 1000
                        ),
                        "oi": (
                            int(50000 * (1 - abs(moneyness)))
                            if abs(moneyness) < 0.1
                            else 5000
                        ),
                        "iv": round(iv, 2),
                        "delta": round(call_delta, 3),
                        "gamma": round(gamma, 3),
                        "theta": round(theta, 2),
                        "vega": round(vega, 2),
                        "bid": round(call_ltp * 0.98, 2),
                        "ask": round(call_ltp * 1.02, 2),
                    },
                    "put": {
                        "ltp": round(put_ltp, 2),
                        "volume": (
                            int(10000 * (1 - abs(moneyness)))
                            if abs(moneyness) < 0.1
                            else 1000
                        ),
                        "oi": (
                            int(50000 * (1 - abs(moneyness)))
                            if abs(moneyness) < 0.1
                            else 5000
                        ),
                        "iv": round(iv, 2),
                        "delta": round(put_delta, 3),
                        "gamma": round(gamma, 3),
                        "theta": round(theta, 2),
                        "vega": round(vega, 2),
                        "bid": round(put_ltp * 0.98, 2),
                        "ask": round(put_ltp * 1.02, 2),
                    },
                }
            )

        # Use next weekly expiry if not provided
        if not expiry_date:
            # Find next Friday
            today = datetime.now()
            days_ahead = 4 - today.weekday()  # 4 = Friday
            if days_ahead <= 0:
                days_ahead += 7
            next_friday = today + timedelta(days=days_ahead)
            expiry_date = next_friday.strftime("%Y-%m-%d")

        result = {
            "symbol": symbol,
            "expiry_date": expiry_date,
            "underlying_price": underlying_price,
            "timestamp": datetime.now().isoformat(),
            "market_open": market_open,
            "data_source": "mock",
            "strikes": strikes_data,
        }

        logger.info(
            f"[OPTIONS] Generated mock chain: {len(strikes_data)} strikes, underlying={underlying_price}"
        )
        return result


# Testing
if __name__ == "__main__":
    service = OptionsChainService()

    # Test market status
    is_open, msg = service.is_market_open()
    print(f"Market Status: {msg}")

    # Test option chain fetch
    chain = service.get_option_chain("NIFTY")
    print(f"\nOption Chain for {chain['symbol']}:")
    print(f"Underlying: ₹{chain['underlying_price']}")
    print(f"Expiry: {chain['expiry_date']}")
    print(f"Strikes: {len(chain['strikes'])}")
    print(f"Data source: {chain.get('data_source', 'live')}")
