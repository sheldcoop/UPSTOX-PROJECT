"""
Deep Web Enrichment using YFinance
----------------------------------
Fetches Sector/Industry data for stocks missing this info in instrument_master.
Uses Yahoo Finance as the data source.

Usage:
    python backend/data/etl/enrich_industry_yfinance.py [--limit 100]
"""

import sqlite3
import yfinance as yf
import logging
import sys
import os
import argparse
import time

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

DB_PATH = "market_data.db"
LOG_FILE = "logs/yfinance_enrichment.log"

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
logger = logging.getLogger("YFEnricher")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def fetch_missing_industry_symbols(limit=100):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT trading_symbol 
        FROM instrument_master 
        WHERE segment = 'NSE_EQ' 
        AND is_active = 1 
        AND (industry IS NULL OR industry = '')
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def update_industry(symbol, industry):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE instrument_master 
        SET industry = ? 
        WHERE trading_symbol = ? AND segment = 'NSE_EQ'
    """, (industry, symbol))
    conn.commit()
    conn.close()

def enrich_batch(limit):
    symbols = fetch_missing_industry_symbols(limit)
    if not symbols:
        logger.info("No instruments found missing Industry data.")
        return

    logger.info(f"Targeting {len(symbols)} instruments for YFinance enrichment...")
    
    success_count = 0
    
    for i, symbol in enumerate(symbols):
        try:
            yf_ticker = f"{symbol}.NS"
            ticker = yf.Ticker(yf_ticker)
            
            # Fast info fetch
            info = ticker.info
            
            # Extract Sector/Industry
            # 'sector' or 'industry' keys
            industry = info.get('industry') or info.get('sector')
            
            if industry:
                update_industry(symbol, industry)
                logger.info(f"[{i+1}/{len(symbols)}] {symbol} -> {industry}")
                success_count += 1
            else:
                logger.warning(f"[{i+1}/{len(symbols)}] {symbol}: No industry data found.")
                
            # Respect rate limits
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Failed {symbol}: {e}")
            
    logger.info(f"Enrichment Complete. Enriched {success_count}/{len(symbols)} stocks.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50, help="Max stocks to process")
    args = parser.parse_args()
    
    enrich_batch(args.limit)
