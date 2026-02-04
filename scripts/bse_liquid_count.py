#!/usr/bin/env python3
"""BSE Liquid Groups inventory."""

import sqlite3

DB = "market_data.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

print("\n" + "=" * 80)
print("BSE LIQUID INVENTORY")
print("=" * 80)

# BSE Liquid Groups (A, B)
q1 = "SELECT COUNT(*) FROM exchange_listings WHERE segment='BSE_EQ' AND instrument_type IN ('A', 'B')"
result1 = cur.execute(q1).fetchone()[0]
print(f"\n✅ BSE Liquid Groups (A/B):                                 {result1:,}")

# Break down by type
q2 = "SELECT instrument_type, COUNT(*) FROM exchange_listings WHERE segment='BSE_EQ' AND instrument_type IN ('A', 'B') GROUP BY instrument_type"
print("\n   Breakdown:")
for itype, cnt in cur.execute(q2):
    print(f"   - Group {itype}: {cnt:,}")

# Compare to NSE
q3 = "SELECT COUNT(*) FROM exchange_listings WHERE segment='NSE_EQ' AND instrument_type IN ('EQ', 'BE')"
result3 = cur.execute(q3).fetchone()[0]
print(f"\n💡 For comparison - NSE Mainboard (EQ/BE):                 {result3:,}")
print(f"   Ratio: BSE liquid / NSE mainboard = {result1/result3:.1%}")

print("\n" + "=" * 80)
conn.close()
