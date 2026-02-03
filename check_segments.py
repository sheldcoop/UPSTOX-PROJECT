import sqlite3

db_path = "market_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Segments & Counts ---")
cursor.execute("SELECT segment, count(*) FROM exchange_listings GROUP BY segment")
for row in cursor.fetchall():
    print(row)

print("\n--- NSE_FO Type Codes ---")
cursor.execute(
    "SELECT instrument_type, count(*) FROM exchange_listings WHERE segment='NSE_FO' GROUP BY instrument_type"
)
for row in cursor.fetchall():
    print(row)

conn.close()
