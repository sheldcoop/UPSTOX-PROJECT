#!/usr/bin/env python3
"""
Schema Migration for NSE Index Classification System
Adds index-related columns to instruments_tier1 and creates new tables
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "market_data.db"


def migrate_instruments_tier1(conn: sqlite3.Connection):
    """Add index classification columns to instruments_tier1"""
    cursor = conn.cursor()
    
    logger.info("Adding index classification columns to instruments_tier1...")
    
    # Check which columns already exist
    cursor.execute("PRAGMA table_info(instruments_tier1)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    columns_to_add = [
        ("sector", "TEXT"),
        ("industry", "TEXT"),
        ("index_memberships", "TEXT"),
        ("is_nifty50", "INTEGER DEFAULT 0"),
        ("is_nifty100", "INTEGER DEFAULT 0"),
        ("is_nifty200", "INTEGER DEFAULT 0"),
        ("is_nifty500", "INTEGER DEFAULT 0"),
        ("is_niftynext50", "INTEGER DEFAULT 0"),
        ("is_midcap", "INTEGER DEFAULT 0"),
        ("is_smallcap", "INTEGER DEFAULT 0"),
        ("weight_nifty50", "REAL"),
        ("weight_nifty100", "REAL"),
        ("weight_nifty500", "REAL"),
    ]
    
    added_count = 0
    for col_name, col_type in columns_to_add:
        if col_name not in existing_columns:
            cursor.execute(f"ALTER TABLE instruments_tier1 ADD COLUMN {col_name} {col_type}")
            added_count += 1
            logger.info(f"  ✅ Added column: {col_name}")
        else:
            logger.debug(f"  ⏭️  Column already exists: {col_name}")
    
    # Create indexes for fast filtering
    indexes = [
        ("idx_tier1_sector", "sector"),
        ("idx_tier1_industry", "industry"),
        ("idx_tier1_nifty50", "is_nifty50"),
        ("idx_tier1_nifty100", "is_nifty100"),
        ("idx_tier1_nifty500", "is_nifty500"),
    ]
    
    for idx_name, col_name in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON instruments_tier1({col_name})")
            logger.info(f"  ✅ Created index: {idx_name}")
        except sqlite3.OperationalError:
            logger.debug(f"  ⏭️  Index already exists: {idx_name}")
    
    conn.commit()
    logger.info(f"✅ Added {added_count} new columns to instruments_tier1")


def create_nse_index_metadata_table(conn: sqlite3.Connection):
    """Create table to store NSE index metadata"""
    cursor = conn.cursor()
    
    logger.info("Creating nse_index_metadata table...")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nse_index_metadata (
        index_code TEXT PRIMARY KEY,
        index_name TEXT NOT NULL,
        index_type TEXT,
        constituent_count INTEGER,
        expected_count INTEGER,
        rebalance_frequency TEXT DEFAULT 'quarterly',
        csv_url TEXT,
        html_url TEXT,
        last_scraped TIMESTAMP,
        last_scrape_status TEXT,
        scrape_error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        CHECK (index_type IN ('broad', 'sector', 'thematic', 'strategy')),
        CHECK (last_scrape_status IN ('SUCCESS', 'PARTIAL', 'FAILED', NULL))
    )
    """)
    
    conn.commit()
    logger.info("✅ Created nse_index_metadata table")


def create_index_constituents_v2_table(conn: sqlite3.Connection):
    """Create enhanced index constituents mapping table"""
    cursor = conn.cursor()
    
    logger.info("Creating index_constituents_v2 table...")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS index_constituents_v2 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        index_code TEXT NOT NULL,
        instrument_key TEXT,
        symbol TEXT NOT NULL,
        company_name TEXT,
        isin TEXT,
        
        -- Index-specific data
        weight REAL,
        sector TEXT,
        industry TEXT,
        
        -- Metadata
        effective_date DATE,
        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        removed_date TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        
        -- Source tracking
        data_source TEXT DEFAULT 'NSE_CSV',
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        UNIQUE(index_code, symbol),
        FOREIGN KEY (instrument_key) REFERENCES instruments_tier1(instrument_key)
            ON DELETE SET NULL
    )
    """)
    
    # Create indexes for fast lookups (only if table was just created)
    indexes = [
        ("idx_constituents_index", "index_code"),
        ("idx_constituents_symbol", "symbol"),
        ("idx_constituents_instrument", "instrument_key"),
        ("idx_constituents_active", "is_active"),
        ("idx_constituents_sector", "sector")
    ]
    
    for idx_name, col_name in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON index_constituents_v2({col_name})")
        except Exception as e:
            logger.warning(f"  ⚠️  Could not create index {idx_name}: {e}")
    
    conn.commit()
    logger.info("✅ Created index_constituents_v2 table")


def create_index_scrape_log_table(conn: sqlite3.Connection):
    """Create table to log scraping operations"""
    cursor = conn.cursor()
    
    logger.info("Creating nse_index_scrape_log table...")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nse_index_scrape_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scrape_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        index_code TEXT NOT NULL,
        scrape_type TEXT,
        status TEXT,
        constituents_found INTEGER,
        constituents_matched INTEGER,
        duration_seconds REAL,
        error_message TEXT,
        
        CHECK (scrape_type IN ('CSV', 'HTML', 'MERGED')),
        CHECK (status IN ('SUCCESS', 'PARTIAL', 'FAILED'))
    )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scrape_log_date ON nse_index_scrape_log(scrape_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scrape_log_index ON nse_index_scrape_log(index_code)")
    
    conn.commit()
    logger.info("✅ Created nse_index_scrape_log table")


def seed_index_metadata(conn: sqlite3.Connection):
    """Seed nse_index_metadata with 18 indices configuration"""
    cursor = conn.cursor()
    
    logger.info("Seeding index metadata for 18 NSE indices...")
    
    indices = [
        # Tier 1: Broad Market
        ('NIFTY50', 'Nifty 50 Index', 'broad', 50, 
         'https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv',
         'https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-50'),
        ('NIFTYNEXT50', 'Nifty Next 50 Index', 'broad', 50,
         'https://www.niftyindices.com/IndexConstituent/ind_niftynext50list.csv',
         'https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-next-50'),
        ('NIFTY100', 'Nifty 100 Index', 'broad', 100,
         'https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv',
         'https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-100'),
        ('NIFTY200', 'Nifty 200 Index', 'broad', 200,
         'https://www.niftyindices.com/IndexConstituent/ind_nifty200list.csv',
         'https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-200'),
        ('NIFTY500', 'Nifty 500 Index', 'broad', 500,
         'https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv',
         'https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-500'),
        
        # Tier 2: Market Cap Based
        ('NIFTYTOTALMARKET', 'Nifty Total Market Index', 'broad', 750,
         'https://www.niftyindices.com/IndexConstituent/ind_niftytotalmarketlist.csv',
         'https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-total-market'),
        ('NIFTYMIDCAP150', 'Nifty Midcap150 Index', 'broad', 150,
         'https://www.niftyindices.com/IndexConstituent/ind_niftymidcap150list.csv',
         'https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-midcap-150'),
        ('NIFTYMIDCAP50', 'Nifty Midcap 50 Index', 'broad', 50,
         'https://www.niftyindices.com/IndexConstituent/ind_niftymidcap50list.csv',
         'https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-midcap-50'),
        ('NIFTYMIDCAPSELECT', 'Nifty Midcap Select Index', 'broad', 25,
         'https://www.niftyindices.com/IndexConstituent/ind_niftymidcapselectlist.csv',
         'https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-midcap-select'),
        ('NIFTYMIDCAP100', 'Nifty Midcap 100 Index', 'broad', 100,
         'https://www.niftyindices.com/IndexConstituent/ind_niftymidcap100list.csv',
         'https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-midcap-100'),
        ('NIFTYSMALLCAP500', 'Nifty Smallcap 500', 'broad', 500,
         'https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap500list.csv',
         'https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-smallcap-500'),
        ('NIFTYSMALLCAP250', 'Nifty Smallcap 250 Index', 'broad', 250,
         'https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap250list.csv',
         'https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-smallcap-250'),
        ('NIFTYSMALLCAP100', 'Nifty Smallcap 100 Index', 'broad', 100,
         'https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap100list.csv',
         'https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-smallcap-100'),
        ('NIFTYSMALLCAP50', 'Nifty Smallcap 50 Index', 'broad', 50,
         'https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap50list.csv',
         'https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-smallcap-50'),
        
        # Tier 3: Specialized
        ('NIFTY500MULTICAP', 'Nifty 500 Multicap 50:25:25 Index', 'strategy', 500,
         'https://www.niftyindices.com/IndexConstituent/ind_nifty500multicap502525list.csv',
         'https://www.niftyindices.com/indices/equity/strategy-indices/nifty500-multicap-50-25-25'),
        ('NIFTYMICROCAP250', 'Nifty Microcap 250 Index', 'broad', 250,
         'https://www.niftyindices.com/IndexConstituent/ind_niftymicrocap250list.csv',
         'https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-microcap-250'),
        ('NIFTYLARGEMIDCAP250', 'Nifty LargeMidcap 250 Index', 'broad', 250,
         'https://www.niftyindices.com/IndexConstituent/ind_niftylargemidcap250list.csv',
         'https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-largemidcap-250'),
        ('NIFTYMIDSMALLCAP400', 'Nifty MidSmallcap 400 Index', 'broad', 400,
         'https://www.niftyindices.com/IndexConstituent/ind_niftymidsmallcap400list.csv',
         'https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-midsmallcap-400'),
    ]
    
    for index_code, index_name, index_type, expected_count, csv_url, html_url in indices:
        cursor.execute("""
        INSERT OR REPLACE INTO nse_index_metadata 
        (index_code, index_name, index_type, expected_count, csv_url, html_url, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (index_code, index_name, index_type, expected_count, csv_url, html_url))
    
    conn.commit()
    logger.info(f"✅ Seeded metadata for {len(indices)} NSE indices")


def print_summary(conn: sqlite3.Connection):
    """Print migration summary"""
    cursor = conn.cursor()
    
    logger.info("\n" + "=" * 70)
    logger.info("NSE INDEX SCHEMA MIGRATION SUMMARY")
    logger.info("=" * 70)
    
    # Check instruments_tier1 columns
    cursor.execute("PRAGMA table_info(instruments_tier1)")
    index_columns = [row[1] for row in cursor.fetchall() if 'index' in row[1] or row[1] in ['sector', 'industry']]
    logger.info(f"\n📊 instruments_tier1: {len(index_columns)} index-related columns")
    for col in index_columns:
        logger.info(f"  ✅ {col}")
    
    # Check new tables
    tables = ['nse_index_metadata', 'index_constituents_v2', 'nse_index_scrape_log']
    logger.info(f"\n📁 New tables created:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        logger.info(f"  ✅ {table:30} | {count} rows")
    
    # Index metadata summary
    cursor.execute("SELECT index_type, COUNT(*) FROM nse_index_metadata GROUP BY index_type")
    logger.info(f"\n📈 Indices by type:")
    for index_type, count in cursor.fetchall():
        logger.info(f"  {index_type:10} | {count} indices")
    
    logger.info("=" * 70)


def main():
    """Execute schema migration"""
    logger.info("Starting NSE Index Schema Migration...")
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    
    try:
        # Step 1: Modify instruments_tier1
        migrate_instruments_tier1(conn)
        
        # Step 2: Create new tables
        create_nse_index_metadata_table(conn)
        create_index_constituents_v2_table(conn)
        create_index_scrape_log_table(conn)
        
        # Step 3: Seed index configuration
        seed_index_metadata(conn)
        
        # Step 4: Summary
        print_summary(conn)
        
        logger.info("\n✅ NSE Index Schema Migration completed successfully!")
        logger.info("\nNext steps:")
        logger.info("  1. Run nse_index_scraper.py to download all 18 index CSVs")
        logger.info("  2. Run nse_index_classifier.py to classify instruments")
        logger.info("  3. Schedule monthly auto-refresh in DataSyncManager")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
