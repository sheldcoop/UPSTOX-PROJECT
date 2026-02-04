#!/usr/bin/env python3
"""
Schema Migration V3 - Tiered Instruments Architecture
Creates multi-tier instrument tables with future-proof columns for sector, industry, F&O, and index membership
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "market_data.db"


def create_tiered_schema(conn: sqlite3.Connection):
    """Create enhanced tiered instruments schema"""
    cursor = conn.cursor()
    
    logger.info("Creating tiered instruments schema...")
    
    # ========================================================================
    # TIER 1: LIQUID EQUITY (NSE EQ + BSE A/B/XT) - ~5,664 instruments
    # ========================================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS instruments_tier1 (
        instrument_key TEXT PRIMARY KEY,
        exchange TEXT NOT NULL,              -- NSE, BSE
        segment TEXT NOT NULL,                -- NSE_EQ, BSE_EQ
        instrument_type TEXT,                 -- EQ, A, B, XT
        symbol TEXT NOT NULL,                 -- RELIANCE, TCS, INFY
        trading_symbol TEXT,                  -- RELIANCE-EQ, TCS
        company_name TEXT,                    -- Full company name
        isin TEXT,                            -- INE002A01018
        
        -- Trading specs
        lot_size INTEGER DEFAULT 1,
        tick_size REAL DEFAULT 0.05,
        freeze_quantity INTEGER,              -- Max order quantity
        
        -- FUTURE-PROOF: Sector & Industry classification
        sector TEXT,                          -- Technology, Banking, Pharma, etc.
        industry TEXT,                        -- IT Services, Private Banks, etc.
        
        -- FUTURE-PROOF: F&O availability
        has_fno BOOLEAN DEFAULT 0,            -- 1 if F&O available for this stock
        fno_segment TEXT,                     -- NSE_FO, BSE_FO (if has_fno=1)
        
        -- FUTURE-PROOF: Index membership (comma-separated)
        index_memberships TEXT,               -- 'NIFTY50,NIFTY100,NIFTYBANK' or NULL
        is_nifty50 BOOLEAN DEFAULT 0,         -- Quick filter for Nifty 50
        is_nifty100 BOOLEAN DEFAULT 0,        -- Quick filter for Nifty 100
        is_nifty200 BOOLEAN DEFAULT 0,        -- Quick filter for Nifty 200
        is_nifty500 BOOLEAN DEFAULT 0,        -- Quick filter for Nifty 500
        
        -- Market cap & liquidity (to be populated later)
        market_cap_category TEXT,             -- LARGE, MID, SMALL
        avg_daily_volume INTEGER,             -- Average daily volume (for liquidity screening)
        
        -- Status tracking
        is_active BOOLEAN DEFAULT 1,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_price_update TIMESTAMP,          -- For tracking stale data
        
        -- Indexes for performance
        CHECK (exchange IN ('NSE', 'BSE')),
        CHECK (lot_size > 0)
    )
    """)
    
    # Indexes for tier1 (fast queries)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tier1_symbol ON instruments_tier1(symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tier1_exchange ON instruments_tier1(exchange)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tier1_has_fno ON instruments_tier1(has_fno)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tier1_sector ON instruments_tier1(sector)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tier1_nifty50 ON instruments_tier1(is_nifty50)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tier1_nifty100 ON instruments_tier1(is_nifty100)")
    
    logger.info("✅ Created instruments_tier1 with future-proof columns")
    
    # ========================================================================
    # TIER 2: SME STOCKS (NSE SM + BSE M) - ~814 instruments
    # ========================================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS instruments_sme (
        instrument_key TEXT PRIMARY KEY,
        exchange TEXT NOT NULL,
        segment TEXT NOT NULL,                -- NSE_EQ, BSE_EQ
        instrument_type TEXT,                 -- SM, M
        symbol TEXT NOT NULL,
        trading_symbol TEXT,
        company_name TEXT,
        isin TEXT,
        
        -- Trading specs (SME-specific)
        lot_size INTEGER DEFAULT 1,           -- Often 5000+ for SME
        tick_size REAL DEFAULT 0.05,
        freeze_quantity INTEGER,
        
        -- RISK FLAGS (Auto-populated)
        risk_level TEXT DEFAULT 'HIGH',       -- HIGH, VERY_HIGH
        min_lot_warning BOOLEAN DEFAULT 1,    -- Alert if lot_size > 1000
        liquidity_tier TEXT DEFAULT 'LOW',    -- LOW, VERY_LOW
        
        -- FUTURE-PROOF: Sector & Industry
        sector TEXT,
        industry TEXT,
        
        -- SME-specific metadata
        listing_date DATE,                    -- Track how new the SME is
        is_graded BOOLEAN DEFAULT 0,          -- NSE SME grading available
        sme_grade TEXT,                       -- A+, A, B (if graded)
        
        -- Status tracking
        is_active BOOLEAN DEFAULT 1,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        CHECK (risk_level IN ('HIGH', 'VERY_HIGH'))
    )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sme_symbol ON instruments_sme(symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sme_risk ON instruments_sme(risk_level)")
    
    logger.info("✅ Created instruments_sme with risk flags")
    
    # ========================================================================
    # TIER 3: DERIVATIVES (F&O) - ~186,201 instruments
    # ========================================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS instruments_derivatives (
        instrument_key TEXT PRIMARY KEY,
        exchange TEXT NOT NULL,
        segment TEXT NOT NULL,                -- NSE_FO, BSE_FO, MCX_FO, etc.
        instrument_type TEXT NOT NULL,        -- OPTIDX, OPTSTK, FUTIDX, FUTSTK, FUTCOM, FUTCUR
        symbol TEXT NOT NULL,
        trading_symbol TEXT,
        
        -- Underlying instrument linking
        underlying_key TEXT,                  -- Links to tier1/tier2 instrument_key
        underlying_symbol TEXT,               -- NIFTY, BANKNIFTY, RELIANCE
        underlying_type TEXT,                 -- EQUITY, INDEX, COMMODITY, CURRENCY
        
        -- Contract specifications
        expiry DATE NOT NULL,                 -- Contract expiry date (for auto-cleanup)
        strike_price REAL,                    -- Strike price for options (0 for futures)
        option_type TEXT,                     -- CE, PE, FUT
        
        -- Trading specs
        lot_size INTEGER DEFAULT 1,
        tick_size REAL DEFAULT 0.05,
        freeze_quantity INTEGER,
        minimum_lot INTEGER,                  -- Minimum lot size
        
        -- Contract metadata
        weekly BOOLEAN DEFAULT 0,             -- Weekly vs Monthly expiry
        is_atm BOOLEAN DEFAULT 0,             -- At-the-money flag (for filtering)
        moneyness TEXT,                       -- ITM, ATM, OTM (calculated)
        
        -- FUTURE-PROOF: Greeks & analytics (to be populated later)
        implied_volatility REAL,              -- IV% (calculated from market data)
        delta REAL,                            -- Option delta
        gamma REAL,                            -- Option gamma
        theta REAL,                            -- Option theta
        vega REAL,                             -- Option vega
        
        -- Status tracking
        is_active BOOLEAN DEFAULT 1,
        is_expired BOOLEAN DEFAULT 0,         -- Auto-set on expiry date
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        CHECK (instrument_type IN ('OPTIDX', 'OPTSTK', 'FUTIDX', 'FUTSTK', 'FUTCOM', 'FUTCUR', 'OPTCUR', 'OPTIRD')),
        CHECK (option_type IN ('CE', 'PE', 'FUT', NULL))
    )
    """)
    
    # Critical indexes for derivatives (expiry cleanup + option chain queries)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deriv_expiry ON instruments_derivatives(expiry)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deriv_underlying ON instruments_derivatives(underlying_key)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deriv_symbol ON instruments_derivatives(underlying_symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deriv_type ON instruments_derivatives(instrument_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deriv_active ON instruments_derivatives(is_active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deriv_strike ON instruments_derivatives(strike_price)")
    
    logger.info("✅ Created instruments_derivatives with expiry tracking")
    
    # ========================================================================
    # TIER 4: INDICES & ETFs - ~312 instruments
    # ========================================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS instruments_indices_etfs (
        instrument_key TEXT PRIMARY KEY,
        exchange TEXT NOT NULL,
        segment TEXT NOT NULL,                -- NSE_INDEX, BSE_INDEX, NSE_EQ (for ETFs)
        instrument_type TEXT NOT NULL,        -- INDEX, N1 (ETF)
        symbol TEXT NOT NULL,                 -- NIFTY, BANKNIFTY, NIFTYBEES
        trading_symbol TEXT,
        name TEXT,                            -- Full index/ETF name
        
        -- Index-specific metadata
        index_code TEXT,                      -- NIFTY50, BANKNIFTY, NIFTYIT
        constituent_count INTEGER,            -- Number of stocks in index
        base_value REAL,                      -- Index base value
        base_date DATE,                       -- Index inception date
        
        -- ETF-specific metadata
        is_etf BOOLEAN DEFAULT 0,
        underlying_index TEXT,                -- For ETFs: NIFTY50, GOLDBEES
        aum REAL,                             -- Assets under management (for ETFs)
        expense_ratio REAL,                   -- ETF expense ratio %
        
        -- Status tracking
        is_active BOOLEAN DEFAULT 1,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        CHECK (instrument_type IN ('INDEX', 'N1', 'IDX'))
    )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_indices_symbol ON instruments_indices_etfs(symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_indices_type ON instruments_indices_etfs(instrument_type)")
    
    logger.info("✅ Created instruments_indices_etfs")
    
    # ========================================================================
    # SUSPENDED INSTRUMENTS TRACKING (Reactive - on order failures)
    # ========================================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS instruments_suspended (
        instrument_key TEXT PRIMARY KEY,
        exchange TEXT,
        symbol TEXT,
        trading_symbol TEXT,
        
        -- Suspension details
        suspended_date DATE,
        reason TEXT,                          -- Trading halt, delisting, corporate action
        detected_via TEXT DEFAULT 'ORDER_REJECTION',  -- ORDER_REJECTION, API_SYNC
        
        -- Status tracking
        is_resumed BOOLEAN DEFAULT 0,         -- 1 if resumed trading
        resumed_date DATE,
        last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (instrument_key) REFERENCES instruments_tier1(instrument_key)
            ON DELETE CASCADE
    )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_suspended_date ON instruments_suspended(suspended_date)")
    
    logger.info("✅ Created instruments_suspended (reactive tracking)")
    
    # ========================================================================
    # INDEX CONSTITUENTS LINKING (For labeling NIFTY50/100/200)
    # ========================================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS index_constituents_v2 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        index_code TEXT NOT NULL,             -- NIFTY50, NIFTY100, BANKNIFTY
        instrument_key TEXT NOT NULL,         -- Link to tier1 instrument
        symbol TEXT NOT NULL,
        
        -- Weightage & metadata
        weightage REAL,                       -- Index weightage %
        effective_date DATE,                  -- Constituent added date
        exit_date DATE,                       -- NULL if still active
        
        is_active BOOLEAN DEFAULT 1,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (instrument_key) REFERENCES instruments_tier1(instrument_key)
    )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_constituents_index ON index_constituents_v2(index_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_constituents_instrument ON index_constituents_v2(instrument_key)")
    
    logger.info("✅ Created index_constituents_v2 for labeling")
    
    # ========================================================================
    # SYNC TRACKING (For DataSyncManager integration)
    # ========================================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS instruments_sync_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sync_type TEXT NOT NULL,              -- tier1, sme, derivatives, indices
        sync_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        -- Statistics
        instruments_fetched INTEGER,
        instruments_inserted INTEGER,
        instruments_updated INTEGER,
        instruments_deactivated INTEGER,      -- Expired/delisted
        
        -- Performance metrics
        duration_seconds REAL,
        status TEXT,                          -- SUCCESS, PARTIAL, FAILED
        error_message TEXT,
        
        CHECK (sync_type IN ('tier1', 'sme', 'derivatives', 'indices', 'full')),
        CHECK (status IN ('SUCCESS', 'PARTIAL', 'FAILED'))
    )
    """)
    
    logger.info("✅ Created instruments_sync_log")
    
    conn.commit()
    logger.info("✅ Tiered schema migration complete!")


def migrate_existing_data(conn: sqlite3.Connection):
    """Migrate data from old instruments table to tiered structure (if exists)"""
    cursor = conn.cursor()
    
    # Check if old table exists
    cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='instruments'
    """)
    
    if cursor.fetchone():
        logger.info("Found existing instruments table, migrating data...")
        
        # Migrate to tier1 (assumes most are NSE_EQ/BSE_EQ)
        cursor.execute("""
        INSERT OR IGNORE INTO instruments_tier1 
        (instrument_key, exchange, segment, symbol, trading_symbol, company_name, 
         isin, lot_size, tick_size, is_active, last_updated)
        SELECT 
            instrument_key, exchange, segment, symbol, trading_symbol, company_name,
            isin, lot_size, tick_size, is_active, last_updated
        FROM instruments
        WHERE instrument_type IN ('EQ', 'A', 'B', 'XT', 'BE', 'BZ')
        """)
        
        migrated = cursor.rowcount
        logger.info(f"✅ Migrated {migrated} instruments from old table")
        
        conn.commit()
    else:
        logger.info("No existing instruments table found, starting fresh")


def print_schema_summary(conn: sqlite3.Connection):
    """Print summary of created tables"""
    cursor = conn.cursor()
    
    tables = [
        'instruments_tier1',
        'instruments_sme',
        'instruments_derivatives',
        'instruments_indices_etfs',
        'instruments_suspended',
        'index_constituents_v2',
        'instruments_sync_log'
    ]
    
    logger.info("\n" + "=" * 70)
    logger.info("TIERED SCHEMA SUMMARY")
    logger.info("=" * 70)
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        logger.info(f"{table:35} | {count:,} rows")
    
    logger.info("=" * 70)


def main():
    """Execute schema migration"""
    logger.info("Starting Schema Migration V3...")
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    
    try:
        create_tiered_schema(conn)
        migrate_existing_data(conn)
        print_schema_summary(conn)
        
        logger.info("\n✅ Schema migration V3 completed successfully!")
        logger.info("\nNext steps:")
        logger.info("  1. Run upstox_instruments_fetcher_v2.py to populate tables")
        logger.info("  2. Run index_labeling_script.py to mark NIFTY50/100/200")
        logger.info("  3. Configure DataSyncManager for daily 6:30 AM sync")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
