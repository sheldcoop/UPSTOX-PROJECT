"""
Async Operations Helper
Provides async/await support for fetching multiple API endpoints concurrently
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


async def fetch_url(
    session: aiohttp.ClientSession, url: str, timeout: int = 10
) -> Dict[str, Any]:
    """
    Fetch a single URL asynchronously

    Args:
        session: aiohttp ClientSession
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Dict with response data
    """
    try:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            data = await response.json()
            return {"url": url, "status": response.status, "data": data, "error": None}
    except asyncio.TimeoutError:
        logger.error(f"Timeout fetching {url}")
        return {"url": url, "status": 408, "data": None, "error": "Timeout"}
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return {"url": url, "status": 500, "data": None, "error": str(e)}


async def fetch_multiple_urls(
    urls: List[str], timeout: int = 10
) -> List[Dict[str, Any]]:
    """
    Fetch multiple URLs concurrently

    Args:
        urls: List of URLs to fetch
        timeout: Request timeout in seconds

    Returns:
        List of response dicts
    """
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url, timeout) for url in urls]
        return await asyncio.gather(*tasks)


def fetch_multiple_symbols_sync(symbols: List[str], base_url: str) -> Dict[str, Any]:
    """
    Synchronous wrapper to fetch multiple symbols

    Args:
        symbols: List of stock symbols
        base_url: Base API URL (e.g., 'http://localhost:8000/api/quote')

    Returns:
        Dict mapping symbol to response data
    """
    urls = [f"{base_url}/{symbol}" for symbol in symbols]

    try:
        results = asyncio.run(fetch_multiple_urls(urls))

        # Map results back to symbols
        symbol_data = {}
        for symbol, result in zip(symbols, results):
            if result["status"] == 200 and result["data"]:
                symbol_data[symbol] = result["data"]
            else:
                symbol_data[symbol] = {"error": result.get("error", "Unknown error")}

        return symbol_data

    except Exception as e:
        logger.error(f"Error in fetch_multiple_symbols_sync: {e}")
        return {symbol: {"error": str(e)} for symbol in symbols}


async def fetch_market_data_async(symbols: List[str], api_base: str) -> Dict[str, Any]:
    """
    Fetch market data for multiple symbols asynchronously

    Args:
        symbols: List of symbols to fetch
        api_base: Base API URL

    Returns:
        Dict with aggregated market data
    """
    start_time = datetime.now()

    # Build URLs for different endpoints
    quote_urls = [f"{api_base}/quote/{symbol}" for symbol in symbols]

    # Fetch all data concurrently
    results = await fetch_multiple_urls(quote_urls)

    # Process results
    market_data = {
        "symbols": {},
        "fetch_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
        "total_symbols": len(symbols),
        "successful": 0,
        "failed": 0,
    }

    for symbol, result in zip(symbols, results):
        if result["status"] == 200 and result["data"]:
            market_data["symbols"][symbol] = result["data"]
            market_data["successful"] += 1
        else:
            market_data["symbols"][symbol] = {"error": result.get("error")}
            market_data["failed"] += 1

    logger.info(
        f"Fetched {market_data['successful']}/{len(symbols)} symbols in {market_data['fetch_time_ms']:.2f}ms"
    )

    return market_data


class AsyncAPIClient:
    """
    Async API client for concurrent requests
    """

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def get(self, endpoint: str) -> Dict[str, Any]:
        """GET request to endpoint"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        async with aiohttp.ClientSession() as session:
            return await fetch_url(session, url, self.timeout)

    async def get_multiple(self, endpoints: List[str]) -> List[Dict[str, Any]]:
        """GET requests to multiple endpoints"""
        urls = [f"{self.base_url}/{ep.lstrip('/')}" for ep in endpoints]
        return await fetch_multiple_urls(urls, self.timeout)

    async def fetch_portfolio_data(self) -> Dict[str, Any]:
        """
        Fetch all portfolio-related data concurrently
        """
        endpoints = ["/api/portfolio", "/api/positions", "/api/holdings", "/api/orders"]

        results = await self.get_multiple(endpoints)

        return {
            "portfolio": results[0].get("data"),
            "positions": results[1].get("data"),
            "holdings": results[2].get("data"),
            "orders": results[3].get("data"),
            "fetch_time": datetime.now().isoformat(),
        }


def example_usage():
    """Example usage of async operations"""

    # Example 1: Fetch multiple symbols
    symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]
    data = fetch_multiple_symbols_sync(symbols, "http://localhost:8000/api/quote")
    print(f"Fetched {len(data)} symbols")

    # Example 2: Using AsyncAPIClient
    async def fetch_all_data():
        client = AsyncAPIClient("http://localhost:8000")
        portfolio_data = await client.fetch_portfolio_data()
        return portfolio_data

    # Run async function
    # result = asyncio.run(fetch_all_data())


if __name__ == "__main__":
    example_usage()
