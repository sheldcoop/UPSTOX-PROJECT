import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("market_data.db")
CSV_PATH = Path("data/nse_indices/NIFTY100_enriched.csv")

def ingest_nifty100():
    if not CSV_PATH.exists():
        print(f"Error: CSV not found at {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"Ingesting {len(df)} records from NIFTY 100 CSV...")

    for _, row in df.iterrows():
        symbol = row['symbol']
        industry = row['industry']
        company_name = row['company_name']
        
        # Check if symbol exists
        cursor.execute("SELECT symbol FROM stock_metadata WHERE symbol = ?", (symbol,))
        exists = cursor.fetchone()
        
        if exists:
            # Update existing
            cursor.execute("""
                UPDATE stock_metadata 
                SET is_nifty100 = 1, sector = ?, company_name = ?
                WHERE symbol = ?
            """, (industry, company_name, symbol))
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO stock_metadata (symbol, company_name, sector, is_nifty100)
                VALUES (?, ?, ?, 1)
            """, (symbol, company_name, industry))

    conn.commit()
    conn.close()
    print("Ingestion complete.")

if __name__ == "__main__":
    ingest_nifty100()
