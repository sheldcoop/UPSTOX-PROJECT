import os
import sys
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Use OpenAI client for Groq and OpenRouter
from openai import OpenAI
from dotenv import load_dotenv

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.upstox.live_api import get_upstox_api
from frontend.services.movers import MarketMoversService
from backend.services.upstox.portfolio import PortfolioServicesV3 as PortfolioService
from backend.utils.auth.manager import AuthManager

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Environment
load_dotenv()

# --- Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


class AIService:
    """
    Universal AI Assistant Service.
    Strategy: Groq (Llama-3) -> OpenRouter (Backup)
    Integrates with Upstox data sources via Function Calling.
    """

    def __init__(self):
        self.upstox_api = get_upstox_api()
        self.movers_service = MarketMoversService()
        self.auth_manager = AuthManager()

        # Initialize Portfolio Service
        self.portfolio_service = PortfolioService()

        # -- AI Clients --
        self.clients = []

        # 1. Groq (Fastest, Preferred)
        if GROQ_API_KEY:
            self.clients.append(
                {
                    "provider": "Groq",
                    "client": OpenAI(
                        base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY
                    ),
                    "model": "llama-3.3-70b-versatile",
                }
            )

        # 2. OpenRouter (Backup)
        if OPENROUTER_API_KEY:
            self.clients.append(
                {
                    "provider": "OpenRouter",
                    "client": OpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=OPENROUTER_API_KEY,
                    ),
                    "model": "deepseek/deepseek-r1:free",  # Often reliable free model
                }
            )

        if not self.clients:
            logger.warning(
                "No AI providers configured (Groq/OpenRouter). AI features will fail."
            )

        # -- Tools Definition (OpenAI Format) --
        self.tools_schema = [
            {
                "type": "function",
                "function": {
                    "name": "lookup_instrument_key",
                    "description": "Search for an instrument Key (ID), Token, or details by name. Use this for 'What is the key for X' or 'Check token for Y'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_query": {
                                "type": "string",
                                "description": "The name or symbol to search (e.g. 'IRCTC', 'RELIANCE', 'NIFTY 27 FEB').",
                            }
                        },
                        "required": ["search_query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_market_movers",
                    "description": "Get top gaining and losing stocks for the current trading day.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Market category: 'NSE_MAIN', 'BSE_MAIN', 'NIFTY_50'. Default is NSE_MAIN.",
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_portfolio_holdings",
                    "description": "Get the current list of long-term holdings/investments in the user's portfolio with P&L.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_account_balance",
                    "description": "Get the user's available funds and account balance.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_stock_quote",
                    "description": "Get real-time market price (LTP) and OHLC data for a specific stock.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "The stock symbol to check (e.g. 'TCS', 'INFY').",
                            }
                        },
                        "required": ["symbol"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_recent_news",
                    "description": "Get recent news articles and sentiment for a specific stock or general market.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Stock symbol or keyword (e.g. 'TATA', 'Earnings'). Leave empty for general news.",
                            }
                        },
                    },
                },
            },
        ]

    # =========================================================================
    # CORE AI LOGIC (Multi-Provider)
    # =========================================================================

    def send_message(self, user_message: str) -> str:
        """
        Process user message using the best available AI provider.
        Handles Tool Calling (Function Calling) loop.
        """
        messages = [
            {
                "role": "system",
                "content": """You are an expert trading assistant for the Upstox Platform.
                You have access to real-time market data, portfolio tools, and news.

                WHEN ASKED "WHAT CAN YOU DO?" OR "HELP", RESPOND WITH:
                "Here is how I can assist you:
                
                📊 **Market Data**
                • **Live Quotes**: "Get price for Reliance" or "Quote for Nifty 27 Feb"
                • **Movers**: "Show top Gainers" or "Top Losers today"
                • **Search**: "What is the token/key for IRCTC?"
                
                💼 **Portfolio & Account**
                • **Holdings**: "Show my portfolio" or "Check P&L"
                • **Funds**: "What is my account balance?"
                
                📰 **Intelligence**
                • **News**: "Latest news for Tata Steel" or "Market sentiment"
                "

                GUIDELINES:
                1. ALWAYS invoke tools to fetch data. Do not hallucinate prices or keys.
                2. If the user asks general questions, guide them to these features.
                3. Format all currency in INR (₹).
                4. Be concise and professional.
                """,
            },
            {"role": "user", "content": user_message},
        ]

        # Try each client in order
        for client_cfg in self.clients:
            provider = client_cfg["provider"]
            client = client_cfg["client"]
            model = client_cfg["model"]

            try:
                logger.info(f"Attempting generation with {provider} ({model})...")

                # 1. First Call
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=self.tools_schema,
                    tool_choice="auto",
                )

                response_msg = response.choices[0].message
                tool_calls = response_msg.tool_calls

                # 2. Handle Tool Calls (if any)
                if tool_calls:
                    logger.info(f"{provider} requested {len(tool_calls)} tool calls.")

                    # Add the assistant's request to history
                    messages.append(response_msg)

                    for tool_call in tool_calls:
                        func_name = tool_call.function.name
                        args_json = tool_call.function.arguments
                        call_id = tool_call.id

                        # Execute Tool
                        tool_result_str = self._execute_tool(func_name, args_json)

                        # Append result
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call_id,
                                "content": tool_result_str,
                            }
                        )

                    # 3. Final Answer Generation (with tool outputs)
                    final_response = client.chat.completions.create(
                        model=model, messages=messages
                    )
                    return final_response.choices[0].message.content

                else:
                    # No tools needed, just return text
                    return response_msg.content

            except Exception as e:
                logger.error(f"{provider} Failed: {e}")
                continue  # Try next provider

        return "Sorry, I am unable to process your request at the moment (All AI providers failed)."

    def _execute_tool(self, func_name: str, args_json: str) -> str:
        """Execute the mapped Python method and return JSON string"""
        try:
            args = json.loads(args_json)
            logger.info(f"EXEC TOOL: {func_name} | Args: {args}")

            if func_name == "lookup_instrument_key":
                result = self.lookup_instrument_key(args.get("search_query"))
            elif func_name == "get_market_movers":
                result = self.get_market_movers(args.get("category", "NSE_MAIN"))
            elif func_name == "get_portfolio_holdings":
                result = self.get_portfolio_holdings()
            elif func_name == "get_account_balance":
                result = self.get_account_balance()
            elif func_name == "get_stock_quote":
                result = self.get_stock_quote(args.get("symbol"))
            elif func_name == "get_recent_news":
                result = self.get_recent_news(args.get("query"))
            else:
                result = {"error": "Unknown function"}

            return json.dumps(result, default=str)
        except Exception as e:
            logger.error(f"Tool Execution Failed: {e}")
            return json.dumps({"error": str(e)})

    # =========================================================================
    # TOOL IMPLEMENTATIONS (Backend Logic)
    # =========================================================================

    def lookup_instrument_key(self, search_query: str) -> List[Dict[str, Any]]:
        """DB Search for Instrument Keys"""
        try:
            import sqlite3

            conn = sqlite3.connect("market_data.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Use strict-then-fuzzy logic
            query_upper = search_query.upper()
            wild_pat = f"%{query_upper}%"
            start_pat = f"{query_upper}%"

            sql = """
                SELECT instrument_key, symbol, trading_symbol, segment, instrument_type, exchange_token 
                FROM exchange_listings 
                WHERE symbol LIKE ? OR trading_symbol LIKE ?
                ORDER BY 
                    CASE WHEN symbol = ? THEN 0 
                         WHEN symbol LIKE ? THEN 1 
                         ELSE 2 
                    END,
                    CASE WHEN segment = 'NSE_EQ' THEN 0 ELSE 1 END, 
                    symbol ASC
                LIMIT 10
            """

            cursor.execute(sql, (wild_pat, wild_pat, query_upper, start_pat))
            rows = cursor.fetchall()
            conn.close()

            results = [dict(row) for row in rows]
            if not results:
                return [{"status": "No instruments found", "query": search_query}]
            return results
        except Exception as e:
            return [{"error": str(e)}]

    def get_market_movers(self, category: str = "NSE_MAIN") -> Dict[str, Any]:
        """Fetch gainers/losers"""
        category_map = {
            "NSE": "NSE_MAIN",
            "BSE": "BSE_MAIN",
            "NIFTY": "NIFTY_50",
            "BANKNIFTY": "NIFTY_BANK",
        }
        mapped = category_map.get(category.upper(), category)
        return self.movers_service.get_movers(mapped)

    def get_portfolio_holdings(self) -> Any:
        """Fetch holdings"""
        try:
            with self.portfolio_service as portfolio:
                return portfolio.get_holdings()
        except Exception as e:
            return {"error": str(e)}

    def get_account_balance(self) -> Dict[str, Any]:
        """Fetch funds"""
        try:
            url = "https://api.upstox.com/v2/user/get-funds-and-margin"
            headers = self.upstox_api._get_headers()
            response = self.upstox_api.session.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            return {"error": f"Failed: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """Fetch LTP/Quote"""
        try:
            # 1. Search first to get key
            search_res = self.lookup_instrument_key(symbol)
            if (
                isinstance(search_res, list)
                and len(search_res) > 0
                and "instrument_key" in search_res[0]
            ):
                target = search_res[0]
                key = target["instrument_key"]
                name = target.get("trading_symbol", symbol)

                # 2. Get Quote
                url = f"https://api.upstox.com/v2/market/quote/ltp?instrument_key={key}"
                headers = self.upstox_api._get_headers()
                resp = self.upstox_api.session.get(url, headers=headers)
                if resp.status_code == 200:
                    return {
                        "symbol": name,
                        "key": key,
                        "data": resp.json().get("data", {}),
                    }

            return {"error": f"Could not find quote for {symbol}"}
        except Exception as e:
            return {"error": str(e)}

    def get_recent_news(self, query: str = "") -> List[Dict[str, Any]]:
        """Fetch recent news from DB"""
        try:
            import sqlite3

            conn = sqlite3.connect("market_data.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if query:
                sql = """SELECT headline, summary, sentiment, published_at FROM news_articles 
                         WHERE symbols LIKE ? OR headline LIKE ? 
                         ORDER BY published_at DESC LIMIT 5"""
                pat = f"%{query}%"
                cursor.execute(sql, (pat, pat))
            else:
                sql = """SELECT headline, summary, sentiment, published_at FROM news_articles 
                          ORDER BY published_at DESC LIMIT 5"""
                cursor.execute(sql)

            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            return [{"error": str(e)}]


if __name__ == "__main__":
    # Self-test
    service = AIService()
    print("Testing Groq/OpenRouter connection...")
    print(service.send_message("What is the instrument key for IRCTC?"))
