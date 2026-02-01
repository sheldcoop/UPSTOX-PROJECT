#!/usr/bin/env python3
"""
Schema Migration V2 - The "World-Class" Upgrade
Normalizes the database schema into relational tables for Equities and Derivatives.
"""

import sqlite3
import re
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = 'market_data.db'

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def create_new_tables(conn):
    cursor = conn.cursor()
    
    logger.info("creating normalized tables...")
    
    # 1. Exchanges
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exchanges (
        id TEXT PRIMARY KEY,
        name TEXT
    )
    """)
    
    # 2. Segments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS segments (
        id TEXT PRIMARY KEY,
        exchange_id TEXT,
        type TEXT,
        FOREIGN KEY(exchange_id) REFERENCES exchanges(id)
    )
    """)
    
    # 3. Instrument Types (The Decoder Ring)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS instrument_types (
        code TEXT PRIMARY KEY,
        category TEXT, -- 'Equity', 'Bond', 'Index', 'Option', 'Future'
        description TEXT
    )
    """)
    
    # 4. Master Instruments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS instruments (
        instrument_key TEXT PRIMARY KEY,
        exchange_token TEXT,
        symbol TEXT,
        trading_symbol TEXT,
        segment_id TEXT,
        type_code TEXT,
        lot_size INTEGER,
        tick_size REAL,
        is_active BOOLEAN,
        last_updated DATETIME,
        FOREIGN KEY(segment_id) REFERENCES segments(id),
        FOREIGN KEY(type_code) REFERENCES instrument_types(code)
    )
    """)
    
    # 5. Equities Metadata
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equities_metadata (
        instrument_key TEXT PRIMARY KEY,
        isin TEXT, 
        sector TEXT,
        market_cap_category TEXT,
        FOREIGN KEY(instrument_key) REFERENCES instruments(instrument_key)
    )
    """)
    
    # 6. Derivatives Metadata
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS derivatives_metadata (
        instrument_key TEXT PRIMARY KEY,
        underlying_symbol TEXT,
        expiry_date DATE,
        strike_price REAL,
        option_type TEXT, -- CE, PE, FUT
        FOREIGN KEY(instrument_key) REFERENCES instruments(instrument_key)
    )
    """)
    
    # Initialize Static Data
    logger.info("Populating static reference data...")
    
    # Exchanges
    exchanges = [('NSE', 'National Stock Exchange'), ('BSE', 'Bombay Stock Exchange'), ('MCX', 'Multi Commodity Exchange')]
    cursor.executemany("INSERT OR IGNORE INTO exchanges (id, name) VALUES (?, ?)", exchanges)
    
    # Segments
    segments = [
        ('NSE_EQ', 'NSE', 'CASH'), 
        ('NSE_FO', 'NSE', 'DERIVATIVE'),
        ('BSE_EQ', 'BSE', 'CASH'),
        ('BSE_FO', 'BSE', 'DERIVATIVE')
    ]
    cursor.executemany("INSERT OR IGNORE INTO segments (id, exchange_id, type) VALUES (?, ?, ?)", segments)
    
    # Instrument Types Map (Based on Upstox codes)
    # EQ=Equity, BE=TradeForTrade, GB=GovtBond, etc.
    # We will also populate this dynamically, but this seeds the important ones.
    types = [
        ('EQ', 'Equity', 'Common Stock'),
        ('BE', 'Equity', 'Restricted Equity'),
        ('A', 'Equity', 'BSE Class A Equity'),
        ('B', 'Equity', 'BSE Class B Equity'),
        ('GB', 'Bond', 'Government Bond'),
        ('ME', 'Equity', 'BSE SME'),
        ('SM', 'Equity', 'NSE SME'), 
        ('IDX', 'Index', 'Market Index'),
        ('CE', 'Option', 'Call Option'),
        ('PE', 'Option', 'Put Option'),
        ('FUT', 'Future', 'Futures Contract'),
        # Fallbacks for the noise
        ('F', 'Bond', 'BSE Fixed Income'), 
        ('N1', 'ETF', 'NSE ETF'),
        ('Y0', 'Bond', 'Bond') 
    ]
    cursor.executemany("INSERT OR IGNORE INTO instrument_types (code, category, description) VALUES (?, ?, ?)", types)

    conn.commit()

def migrate_data(conn):
    cursor = conn.cursor()
    logger.info("Migrating data from exchange_listings to new schema...")
    
    # --- Step 1: Populate Instrument Types dynamically ---
    # Find any types we missed
    cursor.execute("SELECT DISTINCT instrument_type FROM exchange_listings")
    existing_types = cursor.fetchall()
    
    for (itype,) in existing_types:
        if not itype: continue
        # Default category logic if not in our seed list
        category = 'Other'
        if itype in ['EQ', 'BE', 'A', 'B', 'M', 'T', 'X', 'XT', 'Z', 'P']:
            category = 'Equity'
        elif itype in ['CE', 'PE']:
            category = 'Option'
        elif 'FUT' in itype or itype == 'FUT':
             category = 'Future'
        elif itype in ['GB', 'GS', 'F']:
            category = 'Bond'
        
        cursor.execute("INSERT OR IGNORE INTO instrument_types (code, category, description) VALUES (?, ?, ?)", 
                       (itype, category, f"Auto-imported {itype}"))
    
    conn.commit()
    
    # --- Step 2: Migrate Instruments ---
    logger.info("Copying base instruments...")
    cursor.execute("""
    INSERT OR IGNORE INTO instruments 
    (instrument_key, exchange_token, symbol, trading_symbol, segment_id, type_code, lot_size, tick_size, is_active, last_updated)
    SELECT 
        instrument_key, exchange_token, symbol, trading_symbol, segment, instrument_type, lot_size, tick_size, is_active, last_updated
    FROM exchange_listings
    """)
    conn.commit()
    
    # --- Step 3: Populate Equities Metadata ---
    logger.info("Building Equities Metadata...")
    cursor.execute("""
    INSERT OR IGNORE INTO equities_metadata (instrument_key)
    SELECT instrument_key 
    FROM instruments 
    JOIN instrument_types ON instruments.type_code = instrument_types.code
    WHERE instrument_types.category = 'Equity'
    """)
    conn.commit()
    
    # --- Step 4: Populate Derivatives Metadata (The Hard Part) ---
    logger.info("Parsing Derivatives (this might take a moment)...")
    
    # Select derivatives that need metadata
    cursor.execute("""
    SELECT i.instrument_key, i.trading_symbol, i.type_code, el.underlying_symbol
    FROM instruments i
    JOIN exchange_listings el ON i.instrument_key = el.instrument_key
    JOIN instrument_types it ON i.type_code = it.code
    WHERE it.category IN ('Option', 'Future')
    """)
    
    derivatives = cursor.fetchall()
    
    parsed_count = 0
    futures_count = 0
    options_count = 0
    
    # Regex for standard format: SYMBOL STRIKE OPTION_TYPE DD MMM YY
    # Example: NATIONALUM 355 PE 24 FEB 26
    # Or: NIFTY 22000 CE 29 FEB 24
    regex_opt = re.compile(r'([A-Z0-9]+)\s+(\d+(?:\.\d+)?)\s+(CE|PE)\s+(\d+\s+[A-Z]{3}\s+\d{2})')
    
    # Future Example: BANKNIFTY FUT 29 FEB 24 (Hypothetical, usually just BANKNIFTY 29FEB24FUT?)
    # Upstox usually has "BANKNIFTY 24FEB FUT" or similar.
    # Let's check a FUT symbol if we can find one later. For now, assume simple parsing or skip.
    
    rows_to_insert = []
    
    for key, trading_symbol, type_code, underlying in derivatives:
        if not trading_symbol: continue
        
        # Initialize
        strike = 0.0
        opt_type = 'FUT'
        expiry = None
        
        # Try Options Parsing
        match = regex_opt.search(trading_symbol)
        if match:
             # sym = match.group(1) # Unused, we use underlying from column
             strike = float(match.group(2))
             opt_type = match.group(3)
             expiry_str = match.group(4)
             
             try:
                 # Parse '24 FEB 26' -> Date object
                 expiry = datetime.strptime(expiry_str, '%d %b %y').date()
             except ValueError:
                 pass
             options_count += 1
        else:
            # Maybe Future?
            # Assign type
            if 'FUT' in type_code or 'FUT' in trading_symbol:
                opt_type = 'FUT'
                futures_count += 1
                # Try to extract date from end of string... this varies.
            else:
                continue

        rows_to_insert.append((key, underlying, expiry, strike, opt_type))
        
        if len(rows_to_insert) > 1000:
            cursor.executemany("INSERT OR IGNORE INTO derivatives_metadata (instrument_key, underlying_symbol, expiry_date, strike_price, option_type) VALUES (?, ?, ?, ?, ?)", rows_to_insert)
            conn.commit()
            parsed_count += len(rows_to_insert)
            rows_to_insert = []

    # Final batch
    if rows_to_insert:
        cursor.executemany("INSERT OR IGNORE INTO derivatives_metadata (instrument_key, underlying_symbol, expiry_date, strike_price, option_type) VALUES (?, ?, ?, ?, ?)", rows_to_insert)
        conn.commit()
        parsed_count += len(rows_to_insert)

    logger.info(f"Derivatives processed: {parsed_count} (Options: {options_count}, Futures: {futures_count})")

def main():
    try:
        conn = get_db_connection()
        create_new_tables(conn)
        migrate_data(conn)
        
        # Verify
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM instruments")
        count_inst = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM equities_metadata")
        count_eq = cursor.fetchone()[0]
        
        logger.info(f"✅ Migration Complete.")
        logger.info(f"   Total Instruments: {count_inst}")
        logger.info(f"   Clean Equities: {count_eq}")
        
        conn.close()
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)

if __name__ == "__main__":
    main()