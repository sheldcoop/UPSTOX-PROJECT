#!/usr/bin/env python3
"""Test queries: NSE EQ stocks and F&O coverage."""
import sqlite3

DB = 'market_data.db'
conn = sqlite3.connect(DB)
cur = conn.cursor()

print("\n" + "=" * 80)
print("NSE STOCK INVENTORY TEST")
print("=" * 80)

# Q1: NSE EQ stocks (strict: only 'EQ' type)
q1 = "SELECT COUNT(*) FROM exchange_listings WHERE segment='NSE_EQ' AND instrument_type='EQ'"
result1 = cur.execute(q1).fetchone()[0]
print(f"\n✅ NSE_EQ stocks (instrument_type='EQ' only):              {result1:,}")

# Q2: NSE EQ stocks (mainboard: EQ + BE)
q2 = "SELECT COUNT(*) FROM exchange_listings WHERE segment='NSE_EQ' AND instrument_type IN ('EQ', 'BE')"
result2 = cur.execute(q2).fetchone()[0]
print(f"✅ NSE_EQ mainboard stocks (EQ + BE):                     {result2:,}")

# Q3: NSE stocks with F&O (options/futures available)
q3 = "SELECT COUNT(DISTINCT underlying_symbol) FROM exchange_listings WHERE segment='NSE_FO' AND underlying_type='EQUITY'"
result3 = cur.execute(q3).fetchone()[0]
print(f"✅ NSE stocks with F&O (options/futures):                 {result3:,}")

# Q4: Coverage - what % of NSE_EQ have F&O?
coverage = (result3 / result2 * 100) if result2 > 0 else 0
print(f"\n💡 Coverage: {result3}/{result2} = {coverage:.1f}% of mainboard stocks have derivatives")

# Q5: NSE_EQ stocks WITHOUT F&O
q5 = """
SELECT COUNT(DISTINCT el.symbol) 
FROM exchange_listings el
WHERE el.segment='NSE_EQ' AND el.instrument_type IN ('EQ', 'BE')
AND el.symbol NOT IN (
    SELECT DISTINCT underlying_symbol FROM exchange_listings 
    WHERE segment='NSE_FO' AND underlying_type='EQUITY'
)
"""
result5 = cur.execute(q5).fetchone()[0]
print(f"✅ NSE_EQ stocks WITHOUT F&O (illiquid for derivatives): {result5:,}")

print("\n" + "=" * 80)
conn.close()
