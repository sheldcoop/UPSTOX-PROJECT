"""
Enrich Instrument Master with Industry Data
-------------------------------------------
Reads enriched CSVs from data/nse_indices/ and updates `industry` column in instrument_master.

Usage:
    python backend/data/etl/enrich_industry.py
"""

import sqlite3
import pandas as pd
import glob
import os
import logging
import sys

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

DB_PATH = "market_data.db"
INDICES_DIR = "data/nse_indices"
LOG_FILE = "logs/industry_enrichment.log"

# Logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("IndustryEnricher")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def enrich_from_files():
    csv_files = glob.glob(os.path.join(INDICES_DIR, "*_enriched.csv"))
    if not csv_files:
        logger.error("No CSV files found.")
        return

    industry_map = {} # Symbol -> Industry

    logger.info(f"Scanning {len(csv_files)} files for Industry data...")
    
    for filepath in csv_files:
        try:
            df = pd.read_csv(filepath)
            if 'symbol' in df.columns and 'industry' in df.columns:
                # Iterate and populate map (Late writes overwrite early ones, usually fine)
                for _, row in df.iterrows():
                    sym = str(row['symbol']).strip()
                    ind = str(row['industry']).strip()
                    if sym and ind and ind.lower() != 'nan':
                        industry_map[sym] = ind
        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")

    logger.info(f"Found {len(industry_map)} unique symbols with industry data.")
    
    if not industry_map:
        return

    # Update Database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    updated_count = 0
    
    # Chunk updates for sanity
    batch_size = 500
    items = list(industry_map.items())
    
    try:
        conn.execute("BEGIN TRANSACTION")
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            # Batch: [(Symbol, Industry), ...]
            # SQL: UPDATE instrument_master SET industry = ? WHERE trading_symbol = ? AND segment = 'NSE_EQ'
            # Swap for executemany: (Industry, Symbol)
            params = [(ind, sym) for sym, ind in batch]
            
            cursor.executemany("""
                UPDATE instrument_master 
                SET industry = ? 
                WHERE trading_symbol = ? 
                AND segment = 'NSE_EQ'
            """, params)
            updated_count += cursor.rowcount
            
        conn.commit()
        logger.info(f"Successfully enriched {updated_count} instruments with Industry data.")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Database update failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    enrich_from_files()
