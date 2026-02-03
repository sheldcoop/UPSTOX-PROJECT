#!/usr/bin/env python3
"""Run 20 sample queries to inspect the database."""
import sqlite3

DB = "market_data.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

queries = [
    (
        "Q1. NSE Mainboard (EQ/BE)",
        "SELECT COUNT(*) FROM exchange_listings WHERE exchange='NSE' AND instrument_type IN ('EQ', 'BE')",
    ),
    (
        "Q2. BSE Liquid (A/B)",
        "SELECT COUNT(*) FROM exchange_listings WHERE exchange='BSE' AND instrument_type IN ('A', 'B')",
    ),
    (
        "Q3. Cross-listed (NSE & BSE)",
        "SELECT COUNT(*) FROM (SELECT symbol FROM exchange_listings WHERE exchange='NSE' INTERSECT SELECT symbol FROM exchange_listings WHERE exchange='BSE')",
    ),
    (
        "Q4. Penny Stocks (BSE Z/T/XT)",
        "SELECT COUNT(*) FROM exchange_listings WHERE exchange='BSE' AND instrument_type IN ('Z','T','XT')",
    ),
    (
        "Q5. Unique NSE companies (EQ/BE)",
        "SELECT COUNT(DISTINCT symbol) FROM exchange_listings WHERE exchange='NSE' AND instrument_type IN ('EQ', 'BE')",
    ),
    (
        "Q6. Unique BSE companies (A/B)",
        "SELECT COUNT(DISTINCT symbol) FROM exchange_listings WHERE exchange='BSE' AND instrument_type IN ('A', 'B')",
    ),
    (
        "Q7. Sectors in master_stocks",
        "SELECT COUNT(*) FROM master_stocks WHERE sector_id IS NOT NULL",
    ),
    (
        "Q8. Lot Size Trap (NSE_EQ, lot > 1)",
        "SELECT COUNT(*) FROM exchange_listings WHERE segment='NSE_EQ' AND lot_size > 1",
    ),
    (
        "Q9. Max Lot Size in SME",
        "SELECT COALESCE(MAX(lot_size), 0) FROM exchange_listings WHERE instrument_type IN ('SM', 'ST')",
    ),
    (
        "Q10. F&O Universe (Unique underlying stocks)",
        "SELECT COUNT(DISTINCT underlying_symbol) FROM exchange_listings WHERE segment='NSE_FO' AND underlying_type='EQUITY'",
    ),
    (
        "Q11. Option Sample (Mainboard first 5)",
        "SELECT COUNT(*) FROM exchange_listings WHERE segment='NSE_FO' AND instrument_type IN ('CE', 'PE') LIMIT 1",
    ),
    (
        "Q12. Indices in F&O",
        "SELECT COUNT(DISTINCT underlying_symbol) FROM exchange_listings WHERE segment='NSE_FO' AND underlying_type='INDEX'",
    ),
    (
        "Q13. TCS in F&O",
        "SELECT COUNT(*) FROM exchange_listings WHERE underlying_symbol='TCS' AND segment='NSE_FO'",
    ),
    (
        "Q14. NIFTY vs BankNifty contracts",
        "SELECT underlying_symbol, COUNT(*) FROM exchange_listings WHERE underlying_symbol IN ('NIFTY', 'BANKNIFTY') AND segment='NSE_FO' GROUP BY underlying_symbol",
    ),
    (
        "Q15. Commodity segment (NSE_COM)",
        "SELECT COUNT(*) FROM exchange_listings WHERE segment='NSE_COM'",
    ),
    (
        "Q16. MCX commodities",
        "SELECT COUNT(DISTINCT underlying_symbol) FROM exchange_listings WHERE segment='MCX_FO'",
    ),
    (
        "Q17. BSE F&O",
        "SELECT COUNT(DISTINCT underlying_symbol) FROM exchange_listings WHERE segment='BSE_FO'",
    ),
    (
        "Q18. Sovereign Gold Bonds (SG)",
        "SELECT COUNT(*) FROM exchange_listings WHERE instrument_type='SG'",
    ),
    (
        "Q19. Indices in master_stocks",
        "SELECT COUNT(*) FROM master_stocks WHERE symbol LIKE '%NIFTY%' OR symbol LIKE '%SENSEX%'",
    ),
    (
        "Q20. Govt Securities (GS) on NSE",
        "SELECT COUNT(*) FROM exchange_listings WHERE exchange='NSE' AND instrument_type='GS'",
    ),
]

print("\n" + "=" * 80)
print("UPSTOX DATABASE - INVENTORY QUERIES")
print("=" * 80)

for i, (label, query) in enumerate(queries, 1):
    try:
        result = cur.execute(query).fetchone()
        if isinstance(result, tuple) and len(result) > 1:
            # Multi-row result
            print(f"\n✅ {label}")
            for row in result:
                print(f"   {row}")
        else:
            # Single value
            value = result[0] if result else "N/A"
            print(f"✅ {label:55} → {value}")
    except Exception as e:
        print(f"❌ {label:55} → Error: {str(e)[:50]}")

# Show more details for multi-row queries
print("\n" + "=" * 80)
print("DETAILED RESULTS (Multi-row Queries)")
print("=" * 80)

print("\nQ14. Nifty Contracts Breakdown:")
for row in cur.execute(
    "SELECT underlying_symbol, COUNT(*) FROM exchange_listings WHERE underlying_symbol IN ('NIFTY', 'BANKNIFTY') AND segment='NSE_FO' GROUP BY underlying_symbol"
):
    print(f"  {row[0]}: {row[1]}")

print("\nQ16. Top 10 MCX Commodities:")
for row in cur.execute(
    "SELECT underlying_symbol, COUNT(*) FROM exchange_listings WHERE segment='MCX_FO' GROUP BY underlying_symbol ORDER BY COUNT(*) DESC LIMIT 10"
):
    print(f"  {row[0]}: {row[1]} contracts")

print("\nQ17. BSE F&O Underlyings:")
for row in cur.execute(
    "SELECT underlying_symbol, COUNT(*) FROM exchange_listings WHERE segment='BSE_FO' GROUP BY underlying_symbol"
):
    print(f"  {row[0]}: {row[1]}")

conn.close()
print("\n" + "=" * 80)
