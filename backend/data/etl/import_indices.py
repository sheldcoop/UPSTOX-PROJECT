"""
Import NSE Indices to Index Mapping Table
-----------------------------------------
Reads enriched CSVs from data/nse_indices/ and populates the `index_mapping` table.
Maps Trading Symbols -> Instrument Keys (NSE_EQ).

Usage:
    python backend/data/etl/import_indices.py
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
LOG_FILE = "logs/index_import.log"

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
logger = logging.getLogger("IndexImporter")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def resolve_instrument_keys(cursor, symbols):
    """
    Resolve list of symbols to instrument keys.
    Returns: Dict[symbol, instrument_key]
    """
    if not symbols: return {}
    
    placeholders = ",".join("?" for _ in symbols)
    query = f"""
        SELECT trading_symbol, instrument_key 
        FROM instrument_master 
        WHERE segment = 'NSE_EQ' 
        AND is_active = 1
        AND trading_symbol IN ({placeholders})
    """
    
    try:
        cursor.execute(query, symbols)
        return {row[0]: row[1] for row in cursor.fetchall()}
    except Exception as e:
        logger.error(f"Resolution error: {e}")
        return {}

def import_index_file(filepath):
    filename = os.path.basename(filepath)
    # Filename format: NIFTY50_enriched.csv -> Index Name: NIFTY 50 (or raw code)
    # The CSV has an 'index_code' column: NIFTY50
    
    try:
        df = pd.read_csv(filepath)
        if df.empty:
            logger.warning(f"Skipping empty file: {filename}")
            return

        # Normalize symbols (strip spaces)
        if 'symbol' not in df.columns:
            logger.error(f"Missing 'symbol' column in {filename}")
            return
            
        symbols = df['symbol'].str.strip().unique().tolist()
        index_name = df['index_code'].iloc[0] if 'index_code' in df.columns else filename.replace("_enriched.csv", "")
        
        # Clean index name for display (optional)
        # NIFTY50 -> NIFTY 50 (Manual mapping or regex)
        # For now, keeping the code as is for consistency with filename
        
        logger.info(f"Processing {index_name} ({len(symbols)} symbols) from {filename}...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Resolve Keys
        # Chunking resolution if too many symbols (though indices are usually < 500)
        key_map = resolve_instrument_keys(cursor, symbols)
        
        # Identify missing
        found = len(key_map)
        missing = len(symbols) - found
        if missing > 0:
            missing_syms = set(symbols) - set(key_map.keys())
            logger.warning(f"  - Missing {missing} symbols in Master: {list(missing_syms)[:5]}...")
            
        # Clear existing mapping for this index
        cursor.execute("DELETE FROM index_mapping WHERE index_name = ?", (index_name,))
        
        # Insert New
        to_insert = [(index_name, key) for key in key_map.values()]
        cursor.executemany("INSERT INTO index_mapping (index_name, instrument_key) VALUES (?, ?)", to_insert)
        
        conn.commit()
        conn.close()
        
        logger.info(f"  - Imported {len(to_insert)} instruments to {index_name}.")
        
    except Exception as e:
        logger.error(f"Failed to import {filename}: {e}")

def main():
    csv_files = glob.glob(os.path.join(INDICES_DIR, "*_enriched.csv"))
    if not csv_files:
        logger.error(f"No CSV files found in {INDICES_DIR}")
        return

    logger.info(f"Found {len(csv_files)} index files.")
    
    for csv_file in csv_files:
        import_index_file(csv_file)
        
    logger.info("Index import complete.")

if __name__ == "__main__":
    main()
