import sqlite3

db_path = "market_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get 5 F&O records
print("--- F&O Sample ---")
rows = cursor.execute(
    "SELECT symbol, trading_symbol, instrument_type FROM exchange_listings WHERE segment='NSE_FO' LIMIT 5"
).fetchall()
for r in rows:
    print(r)

# Logic to extract underlying from Futures
print("\n--- Futures Extraction ---")
fut_rows = cursor.execute(
    "SELECT symbol, trading_symbol, instrument_key FROM exchange_listings WHERE segment='NSE_FO' AND instrument_type='FUT' LIMIT 5"
).fetchall()
for r in fut_rows:
    print(r)

print("\n--- Matching Attempt ---")
# Get all active NSE_EQ symbols
eq_symbols = set(
    [
        r[0]
        for r in cursor.execute(
            "SELECT symbol FROM exchange_listings WHERE segment='NSE_EQ'"
        ).fetchall()
    ]
)

# Get all NSE_FO symbols (underlyings)
fo_symbols = [
    r[0]
    for r in cursor.execute(
        "SELECT DISTINCT underlying_symbol FROM exchange_listings WHERE segment='NSE_FO'"
    ).fetchall()
]

matched_set = set()
for fsym in fo_symbols:
    if fsym in eq_symbols:
        matched_set.add(fsym)

print(f"Matched {len(matched_set)} unique underlying stocks.")
print(f"Sample: {list(matched_set)[:10]}")

conn.close()
