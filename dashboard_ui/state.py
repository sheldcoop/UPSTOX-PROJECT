from nicegui import run
import requests
import sqlite3
from typing import Dict, Any, List

# Configuration
API_BASE = "http://localhost:9000"

# ============================================================================
# 📡 Async API Wrappers
# ============================================================================


async def async_get(endpoint: str, timeout: int = 5) -> Dict[str, Any]:
    try:
        response = await run.io_bound(
            requests.get, f"{API_BASE}{endpoint}", timeout=timeout
        )
        if response.status_code == 200:
            return response.json()
        return {"error": f"Status {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


async def async_post(endpoint: str, data: Dict, timeout: int = 30) -> Dict[str, Any]:
    try:
        response = await run.io_bound(
            requests.post, f"{API_BASE}{endpoint}", json=data, timeout=timeout
        )
        if response.status_code in [200, 201]:
            return response.json()
        return {"error": f"Status {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# 🧠 Application State
# ============================================================================


class DashboardState:
    def __init__(self):
        self.current_page: str = "dashboard"
        self.portfolio: Dict[str, Any] = {}
        self.download_history: Dict[str, Any] = {}
        self.selected_symbols: List[str] = []
        self.is_sidebar_collapsed: bool = False

    async def fetch_portfolio(self):
        self.portfolio = await async_get("/api/portfolio")
        return self.portfolio

    async def fetch_download_history(self):
        self.download_history = await async_get("/api/download/history")
        return self.download_history

    async def search_instruments(
        self, category: str, query_text: str = ""
    ) -> List[str]:
        """Async search for instruments with limit for performance"""
        return await run.io_bound(self._search_instruments_sync, category, query_text)

    def _search_instruments_sync(self, category: str, query_text: str) -> List[str]:
        try:
            conn = sqlite3.connect("market_data.db")
            cursor = conn.cursor()

            # Base Queries
            base_query = ""
            where_clause = ""

            if category == "NSE_EQ":
                base_query = "SELECT i.symbol FROM instruments i JOIN instrument_types it ON i.type_code = it.code"
                where_clause = "WHERE i.segment_id='NSE_EQ' AND it.category='Equity'"
            elif category == "BSE_EQ":
                base_query = "SELECT i.symbol FROM instruments i JOIN instrument_types it ON i.type_code = it.code"
                where_clause = "WHERE i.segment_id='BSE_EQ' AND it.category='Equity'"
            elif category == "DEBT":
                base_query = "SELECT i.symbol FROM instruments i JOIN instrument_types it ON i.type_code = it.code"
                where_clause = "WHERE it.category = 'Bond'"
            elif category == "GOLD":
                base_query = "SELECT i.symbol FROM instruments i"
                where_clause = "WHERE i.type_code = 'SG'"
            elif category == "INDICES":
                base_query = "SELECT i.symbol FROM instruments i JOIN instrument_types it ON i.type_code = it.code"
                where_clause = "WHERE it.category = 'Index'"
            elif category == "ETFs":
                base_query = "SELECT i.symbol FROM instruments i JOIN instrument_types it ON i.type_code = it.code"
                where_clause = "WHERE it.category = 'ETF'"
            elif category == "SME_EQ":
                base_query = "SELECT i.symbol FROM instruments i"
                where_clause = "WHERE i.type_code IN ('SM', 'M')"
            elif category == "FNO_UNDERLYING":
                base_query = (
                    "SELECT DISTINCT underlying_symbol FROM derivatives_metadata"
                )
                where_clause = "WHERE 1=1"

            if not base_query:
                return []

            # Add Search Filter
            params = []
            if query_text:
                if category == "FNO_UNDERLYING":
                    where_clause += " AND underlying_symbol LIKE ?"
                else:
                    where_clause += " AND i.symbol LIKE ?"
                params.append(
                    f"{query_text.upper()}%"
                )  # Prefix search is faster and more useful

            final_sql = f"{base_query} {where_clause} ORDER BY 1 ASC LIMIT 100"

            cursor.execute(final_sql, params)
            stocks = [row[0] for row in cursor.fetchall()]
            conn.close()
            return stocks
        except Exception as e:
            print(f"Error searching {category}: {e}")
            return []

    def get_instruments_sync(self, category: str) -> List[str]:
        # Deprecated: Use search_instruments for better performance
        return self._search_instruments_sync(category, "")

    async def get_fno_contracts(self, underlying: str) -> List[tuple]:
        return await run.io_bound(self.get_fno_contracts_sync, underlying)

    def get_fno_contracts_sync(self, underlying: str) -> List[tuple]:
        """Fetch F&O contracts for underlying"""
        try:
            conn = sqlite3.connect("market_data.db")
            c = conn.cursor()
            c.execute(
                """
                SELECT option_type, COUNT(*), MIN(expiry_date) 
                FROM derivatives_metadata 
                WHERE underlying_symbol = ? 
                GROUP BY option_type
            """,
                (underlying,),
            )
            stats = c.fetchall()
            conn.close()
            return stats
        except Exception as e:
            print(f"Error loading contracts for {underlying}: {e}")
            return []

    async def search_instrument_details(self, query_text: str) -> List[Dict[str, Any]]:
        """Search across all instruments and return details (Key, Symbol, Exchange)"""
        return await run.io_bound(self._search_instrument_details_sync, query_text)

    def _search_instrument_details_sync(self, query_text: str) -> List[Dict[str, Any]]:
        try:
            if not query_text or len(query_text) < 2:
                return []

            conn = sqlite3.connect("market_data.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Global search across all segments
            # Updated: Use CONTAINS (%) instead of STARTSWITH to be more flexible
            # Prioritize: 1. Exact Match, 2. Starts With, 3. NSE_EQ Segment
            sql = """
                SELECT instrument_key, symbol, trading_symbol, segment_id, type_code 
                FROM instruments 
                WHERE symbol LIKE ? OR trading_symbol LIKE ?
                ORDER BY 
                    CASE WHEN symbol = ? THEN 0 
                         WHEN symbol LIKE ? THEN 1 
                         ELSE 2 
                    END,
                    CASE WHEN segment_id = 'NSE_EQ' THEN 0 ELSE 1 END, 
                    symbol ASC
                LIMIT 100
            """

            wild_pat = f"%{query_text.upper()}%"
            start_pat = f"{query_text.upper()}%"
            exact_pat = query_text.upper()

            cursor.execute(sql, (wild_pat, wild_pat, exact_pat, start_pat))
            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error searching details: {e}")
            return []
