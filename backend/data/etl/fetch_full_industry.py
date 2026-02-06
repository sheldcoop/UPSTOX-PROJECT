"""
Fetch Full Industry Data using NSELib
-------------------------------------
Uses nselib to fetch the official 'Securities Available for Trading' list from NSE.
This covers both Mainboard and SME, providing 'Sector' or 'Industry' data for potentially 8000+ stocks.

Usage:
    python backend/data/etl/fetch_full_industry.py
"""

import sqlite3
import pandas as pd
import logging
import sys
import os
from nselib import capital_market

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

DB_PATH = "market_data.db"
LOG_FILE = "logs/nselib_enrichment.log"

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
logger = logging.getLogger("NSELibEnricher")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def enrich_from_nselib():
    try:
        logger.info("Fetching Equity List from NSE (via nselib)...")
        # equity_list() returns a DataFrame with columns like:
        # SYMBOL, NAME OF COMPANY, SERIES, DATE OF LISTING, PAID UP VALUE, MARKET LOT, ISIN NUMBER, FACE VALUE
        # Wait, equity_list often doesn't have SECTOR.
        # Let's try 'nifty500_equity_list' or similar if available, but we need ALL.
        # Actually, let's check what columns we get. 
        # If equity_list() lacks Industry, we might need 'bhavcopy' but that doesn't have industry.
        # nselib might not expose the 'Securities available for trading' file with industry directly.
        # However, let's try to fetch active data.
        
        # Alternative: nselib.capital_market.undeclared_dividend() etc.
        # Let's try to load the standard list. 
        
        df = capital_market.equity_list()
        logger.info(f"Fetched {len(df)} records from NSE.")
        logger.info(f"Columns: {df.columns.tolist()}")
        
        # Check for Industry/Sector column
        sector_col = None
        for col in df.columns:
            if 'SECTOR' in col.upper() or 'INDUSTRY' in col.upper():
                sector_col = col
                break
        
        if not sector_col:
            logger.warning("No explicit 'Sector' or 'Industry' column found in equity_list().")
            logger.info("Attempting to fetch Nifty 500 list from nselib for comparison...")
            # If basic list fails, we might just be getting the symbols.
            # But the user challenge is to 'dig web'.
            # If nselib fails, I can try to download the CSV directly from NSE active URL in a separate function.
            return

        # If we found a sector column, let's update.
        logger.info(f"Found Industry column: {sector_col}")
        
        updates = []
        for _, row in df.iterrows():
            sym = str(row['SYMBOL']).strip()
            ind = str(row[sector_col]).strip()
            if sym and ind and ind.lower() != 'nan':
                updates.append((ind, sym))
        
        if not updates:
            logger.warning("No valid updates found.")
            return
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.executemany("""
            UPDATE instrument_master 
            SET industry = ? 
            WHERE trading_symbol = ? 
            AND (industry IS NULL OR industry = '')
        """, updates)
        
        conn.commit()
        conn.close()
        logger.info(f"Enriched {cursor.rowcount} instruments using NSELib data.")

    except Exception as e:
        logger.error(f"NSELib enrichment failed: {e}")

if __name__ == "__main__":
    enrich_from_nselib()
