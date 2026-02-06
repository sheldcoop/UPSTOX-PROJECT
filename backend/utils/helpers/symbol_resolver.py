#!/usr/bin/env python3
"""
Symbol Resolver — Find stocks by SQL filters or direct listing.

Usage:
  # Find by direct symbol list
  symbols = resolve_symbols(symbols=['RELIANCE', 'INFY', 'TCS'])

  # Find by segment
  symbols = resolve_symbols(segment='NSE_EQ', instrument_type=['EQ', 'BE'])

  # Find by SQL filter
  symbols = resolve_symbols(sql_filter="WHERE has_fno=1 AND instrument_type='EQ' LIMIT 10")

  # Find by criteria (keyword search)
  symbols = resolve_symbols(criteria={'segment': 'NSE_EQ', 'instrument_type': 'EQ', 'has_fno': 1})
"""

import sqlite3
from typing import List, Dict, Optional

DB = "market_data.db"


def resolve_symbols(
    symbols: Optional[List[str]] = None,
    segment: Optional[str] = None,
    instrument_type: Optional[List[str]] = None,
    has_fno: Optional[int] = None,
    criteria: Optional[Dict] = None,
    sql_filter: Optional[str] = None,
) -> List[str]:
    """
    Resolve stock symbols based on filters.

    Args:
        symbols: Direct list of symbols (e.g., ['RELIANCE', 'INFY'])
        segment: Segment filter (e.g., 'NSE_EQ', 'BSE_EQ', 'NSE_FO')
        instrument_type: List of instrument types (e.g., ['EQ', 'BE'])
        has_fno: 1 = only stocks with F&O, 0 = exclude F&O, None = any
        criteria: Dict of filters (segment, instrument_type, has_fno, etc.)
        sql_filter: Raw SQL WHERE clause (advanced) - DEPRECATED for security

    Returns:
        List of trading_symbol strings
    """
    # Direct symbol list
    if symbols:
        return symbols

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Build SQL filter with parameterized queries
    where_parts = []
    params = []

    if criteria:
        if "segment" in criteria:
            where_parts.append("segment=?")
            params.append(criteria['segment'])
        if "instrument_type" in criteria:
            itype = criteria["instrument_type"]
            if isinstance(itype, list):
                placeholders = ','.join('?' * len(itype))
                where_parts.append(f"instrument_type IN ({placeholders})")
                params.extend(itype)
            else:
                where_parts.append("instrument_type=?")
                params.append(itype)
        if "has_fno" in criteria:
            where_parts.append("has_fno=?")
            params.append(criteria['has_fno'])
    else:
        if segment:
            where_parts.append("segment=?")
            params.append(segment)
        if instrument_type:
            placeholders = ','.join('?' * len(instrument_type))
            where_parts.append(f"instrument_type IN ({placeholders})")
            params.extend(instrument_type)
        if has_fno is not None:
            where_parts.append("has_fno=?")
            params.append(has_fno)

    # Build query - NOTE: sql_filter parameter deprecated for security
    if sql_filter:
        print("⚠️  WARNING: sql_filter parameter is deprecated for security reasons")
        print("    Please use segment, instrument_type, and has_fno parameters instead")
        # Fallback to safer criteria-based approach
        where_clause = " AND ".join(where_parts) if where_parts else "1=1"
        query = f"SELECT DISTINCT trading_symbol FROM exchange_listings WHERE {where_clause}"
    else:
        where_clause = " AND ".join(where_parts) if where_parts else "1=1"
        query = f"SELECT DISTINCT trading_symbol FROM exchange_listings WHERE {where_clause}"

    try:
        results = cur.execute(query, params).fetchall()
        symbols = [row[0] for row in results]
        print(f"✅ Resolved {len(symbols)} symbols")
        if len(symbols) <= 20:
            print(f"   {', '.join(symbols)}")
        else:
            print(f"   {', '.join(symbols[:10])} ... and {len(symbols)-10} more")
        return symbols
    except Exception as e:
        print(f"❌ Error resolving symbols: {e}")
        return []
    finally:
        conn.close()


def show_available_filters():
    """Print available filter options."""
    print("\n" + "=" * 80)
    print("AVAILABLE FILTERS")
    print("=" * 80)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    print("\n📊 SEGMENTS:")
    for (seg,) in cur.execute(
        "SELECT DISTINCT segment FROM exchange_listings ORDER BY segment"
    ):
        cnt = cur.execute(
            "SELECT COUNT(*) FROM exchange_listings WHERE segment=?", (seg,)
        ).fetchone()[0]
        print(f"   {seg:20} ({cnt:7,} listings)")

    print("\n🏷️  INSTRUMENT TYPES (NSE_EQ):")
    for (itype,) in cur.execute(
        "SELECT DISTINCT instrument_type FROM exchange_listings WHERE segment='NSE_EQ' ORDER BY instrument_type"
    ):
        cnt = cur.execute(
            "SELECT COUNT(*) FROM exchange_listings WHERE segment='NSE_EQ' AND instrument_type=?", (itype,)
        ).fetchone()[0]
        print(f"   {itype:20} ({cnt:7,} listings)")

    print("\n💎 F&O AVAILABILITY:")
    fno_yes = cur.execute(
        "SELECT COUNT(*) FROM exchange_listings WHERE has_fno=1"
    ).fetchone()[0]
    fno_no = cur.execute(
        "SELECT COUNT(*) FROM exchange_listings WHERE has_fno=0 OR has_fno IS NULL"
    ).fetchone()[0]
    print(f"   With F&O (has_fno=1): {fno_yes:,}")
    print(f"   Without F&O:           {fno_no:,}")

    print("\n" + "=" * 80)
    conn.close()


if __name__ == "__main__":
    # Example usage
    print("\n" + "=" * 80)
    print("SYMBOL RESOLVER - TEST")
    print("=" * 80)

    print("\n1️⃣  Direct symbol list:")
    syms = resolve_symbols(symbols=["RELIANCE", "INFY", "TCS"])

    print("\n2️⃣  NSE_EQ mainboard with F&O:")
    syms = resolve_symbols(segment="NSE_EQ", instrument_type=["EQ", "BE"], has_fno=1)

    print("\n3️⃣  All F&O stocks:")
    syms = resolve_symbols(has_fno=1)

    show_available_filters()
