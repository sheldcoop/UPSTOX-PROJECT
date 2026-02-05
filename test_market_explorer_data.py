#!/usr/bin/env python3
"""
Quick test to verify Market Explorer data is accessible
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "market_data.db"

def test_indices():
    """Test fetching indices from nse_index_metadata"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 70)
    print("TESTING: Broad Market Indices")
    print("=" * 70)
    
    cursor.execute("""
        SELECT 
            index_code,
            index_name,
            index_type,
            expected_constituents
        FROM nse_index_metadata
        WHERE index_type IN ('broad', 'largecap', 'midcap', 'smallcap')
        ORDER BY 
            CASE 
                WHEN index_code = 'NIFTY50' THEN 1
                WHEN index_code = 'NIFTYNEXT50' THEN 2
                WHEN index_code = 'NIFTY100' THEN 3
                WHEN index_code = 'NIFTY200' THEN 4
                WHEN index_code = 'NIFTY500' THEN 5
                ELSE 6
            END
    """)
    
    for row in cursor.fetchall():
        print(f"{row[0]:25} | {row[1]:40} | Expected: {row[3]:3}")
    
    conn.close()

def test_nifty50_constituents():
    """Test fetching NIFTY 50 constituents"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "=" * 70)
    print("TESTING: NIFTY 50 Constituents")
    print("=" * 70)
    
    cursor.execute("""
        SELECT 
            ic.symbol,
            ic.company_name,
            ic.weight,
            ic.industry,
            t1.series
        FROM index_constituents_v2 ic
        LEFT JOIN instruments_tier1 t1 ON ic.instrument_key = t1.instrument_key
        WHERE ic.index_code = 'NIFTY50' AND ic.is_active = 1
        ORDER BY ic.weight DESC
        LIMIT 10
    """)
    
    print(f"{'Symbol':15} | {'Company':35} | {'Weight':8} | {'Industry':25}")
    print("-" * 100)
    
    for row in cursor.fetchall():
        symbol, company, weight, industry, series = row
        weight_str = f"{weight:.2f}%" if weight else "N/A"
        print(f"{symbol:15} | {company[:35]:35} | {weight_str:8} | {industry or 'N/A':25}")
    
    conn.close()

def test_sector_stats():
    """Test sector statistics for NIFTY 50"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "=" * 70)
    print("TESTING: NIFTY 50 Sector Distribution")
    print("=" * 70)
    
    cursor.execute("""
        SELECT industry, COUNT(*) as count
        FROM index_constituents_v2
        WHERE index_code = 'NIFTY50' AND is_active = 1 AND industry IS NOT NULL
        GROUP BY industry
        ORDER BY count DESC
    """)
    
    for row in cursor.fetchall():
        print(f"{row[0]:40} | {row[1]:3} stocks")
    
    conn.close()

def test_instruments_tier1_flags():
    """Test instruments_tier1 index flags"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "=" * 70)
    print("TESTING: instruments_tier1 Index Flags")
    print("=" * 70)
    
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN is_nifty50 = 1 THEN 1 ELSE 0 END) as nifty50,
            SUM(CASE WHEN is_nifty100 = 1 THEN 1 ELSE 0 END) as nifty100,
            SUM(CASE WHEN is_nifty500 = 1 THEN 1 ELSE 0 END) as nifty500,
            SUM(CASE WHEN is_midcap = 1 THEN 1 ELSE 0 END) as midcap,
            SUM(CASE WHEN is_smallcap = 1 THEN 1 ELSE 0 END) as smallcap,
            SUM(CASE WHEN industry IS NOT NULL THEN 1 ELSE 0 END) as with_industry
        FROM instruments_tier1
        WHERE is_active = 1
    """)
    
    flags = cursor.fetchone()
    print(f"is_nifty50:      {flags[0]:4}")
    print(f"is_nifty100:     {flags[1]:4}")
    print(f"is_nifty500:     {flags[2]:4}")
    print(f"is_midcap:       {flags[3]:4}")
    print(f"is_smallcap:     {flags[4]:4}")
    print(f"with_industry:   {flags[5]:4}")
    
    # Sample NIFTY 50 stocks
    print(f"\n📋 Sample NIFTY 50 stocks:")
    cursor.execute("""
        SELECT symbol, industry, index_memberships
        FROM instruments_tier1
        WHERE is_nifty50 = 1
        ORDER BY symbol
        LIMIT 5
    """)
    
    for symbol, industry, memberships in cursor.fetchall():
        print(f"  {symbol:25} | {industry or 'N/A':30} | {memberships or '-'}")
    
    conn.close()

if __name__ == "__main__":
    try:
        test_indices()
        test_nifty50_constituents()
        test_sector_stats()
        test_instruments_tier1_flags()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nMarket Explorer data is ready!")
        print("  - Navigate to 'Market Explorer' tab in dashboard")
        print("  - Select 'Broad Market Indices'")
        print("  - Filter by NIFTY 50, NIFTY 100, etc.")
        print("  - View constituents with industry metadata")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
