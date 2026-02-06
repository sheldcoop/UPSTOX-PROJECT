import sqlite3
import pandas as pd
from pathlib import Path
import os
import re

DB_PATH = Path("market_data.db")
INDICES_DIR = Path("data/nse_indices")

def get_db_column(csv_name):
    index_code = csv_name.replace("_enriched.csv", "").upper()
    
    # Mapping for special cases
    mapping = {
        "NIFTY50": "is_nifty50",
        "NIFTY100": "is_nifty100",
        "NIFTY200": "is_nifty200",
        "NIFTY500": "is_nifty500",
        "NIFTYBANK": "is_nifty_bank",
        "NIFTYNEXT50": "is_nifty_next50",
        "NIFTYMIDCAP50": "is_nifty_midcap50",
        "NIFTYMIDCAP100": "is_nifty_midcap100",
        "NIFTYMIDCAP150": "is_nifty_midcap150",
        "NIFTYSMALLCAP50": "is_nifty_smallcap50",
        "NIFTYSMALLCAP100": "is_nifty_smallcap100",
        "NIFTYSMALLCAP250": "is_nifty_smallcap250",
        "NIFTYLARGEMIDCAP250": "is_nifty_largemidcap250",
        "NIFTYMIDSMALLCAP400": "is_nifty_midsmallcap400"
    }
    
    return mapping.get(index_code)

def ingest_all_indices():
    if not INDICES_DIR.exists():
        print(f"Error: Directory not found at {INDICES_DIR}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    csv_files = list(INDICES_DIR.glob("*_enriched.csv"))
    print(f"Found {len(csv_files)} index files.")

    for csv_path in csv_files:
        db_column = get_db_column(csv_path.name)
        if not db_column:
            print(f"Skipping {csv_path.name} - no column mapping.")
            continue
            
        print(f"Ingesting {csv_path.name} into {db_column}...")
        df = pd.read_csv(csv_path)

        for _, row in df.iterrows():
            symbol = row['symbol']
            industry = row['industry']
            company_name = row['company_name']
            
            # Check if symbol exists
            cursor.execute("SELECT symbol FROM stock_metadata WHERE symbol = ?", (symbol,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing
                cursor.execute(f"""
                    UPDATE stock_metadata 
                    SET {db_column} = 1, sector = ?, company_name = ?
                    WHERE symbol = ?
                """, (industry, company_name, symbol))
            else:
                # Insert new
                cursor.execute(f"""
                    INSERT INTO stock_metadata (symbol, company_name, sector, {db_column})
                    VALUES (?, ?, ?, 1)
                """, (symbol, company_name, industry))

    conn.commit()
    conn.close()
    print("All ingestions complete.")

if __name__ == "__main__":
    ingest_all_indices()
