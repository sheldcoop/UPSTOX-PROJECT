-- Expert Schema: Master Instrument Synchronization
-- Designed for high-performance lookups and referential integrity

-- Enable Foreign Keys (Critical for this schema)
PRAGMA foreign_keys = ON;

-- 1. Master Instrument Table (The Golden Record)
CREATE TABLE IF NOT EXISTS instrument_master (
    instrument_key TEXT PRIMARY KEY,          -- NSE_FO|43919
    trading_symbol TEXT NOT NULL,             -- RELIANCE
    name TEXT,                                -- RELIANCE INDUSTRIES
    instrument_type TEXT NOT NULL,            -- EQ, FUT, CE, PE
    security_type TEXT,                       -- STK, IND, COM, CUR
    segment TEXT NOT NULL,                    -- NSE_EQ, NSE_FO
    exchange TEXT,                            -- NSE, BSE, MCX
    lot_size INTEGER DEFAULT 1,
    tick_size REAL DEFAULT 0.05,
    freeze_quantity INTEGER DEFAULT 0,
    underlying_key TEXT,                      -- FK to instrument_master(instrument_key)
    expiry DATE,                              -- YYYY-MM-DD
    strike_price REAL,
    is_active INTEGER DEFAULT 1,              -- 1 = Active, 0 = Expired/Suspended
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (underlying_key) REFERENCES instrument_master(instrument_key)
);

-- Indexes for Sub-millisecond Lookups
CREATE INDEX IF NOT EXISTS idx_trading_symbol ON instrument_master(trading_symbol);
CREATE INDEX IF NOT EXISTS idx_underlying_key ON instrument_master(underlying_key);
CREATE INDEX IF NOT EXISTS idx_expiry ON instrument_master(expiry);
CREATE INDEX IF NOT EXISTS idx_segment_active ON instrument_master(segment, is_active);

-- 2. Index Mapping (Normalization)
-- Links instruments to Indices (e.g., RELIANCE -> Nifty 50)
CREATE TABLE IF NOT EXISTS index_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    index_name TEXT NOT NULL,                -- Nifty 50, Bank Nifty
    instrument_key TEXT NOT NULL,
    weightage REAL,                          -- Optional: Stock weight in index
    
    FOREIGN KEY (instrument_key) REFERENCES instrument_master(instrument_key)
);
CREATE INDEX IF NOT EXISTS idx_index_map_inst ON index_mapping(instrument_key);
CREATE INDEX IF NOT EXISTS idx_index_map_name ON index_mapping(index_name);

-- 3. Thematic Mapping (Normalization)
-- Links to Sectors/Themes (e.g., RELIANCE -> Energy, Oil & Gas)
CREATE TABLE IF NOT EXISTS thematic_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    theme_name TEXT NOT NULL,                -- Energy, PSU Bank, IT
    theme_type TEXT NOT NULL,                -- SECTOR, THEME
    instrument_key TEXT NOT NULL,
    
    FOREIGN KEY (instrument_key) REFERENCES instrument_master(instrument_key)
);
CREATE INDEX IF NOT EXISTS idx_theme_map_inst ON thematic_mapping(instrument_key);

-- 4. Expired Instruments Archive
-- (Can be used to move fully dead contracts out of master if needed, 
-- but user prompt said "Flag or move". We flag in master, but this is for archiving if we DELETE from master)
CREATE TABLE IF NOT EXISTS expired_instruments_archive (
    instrument_key TEXT PRIMARY KEY,
    details_json TEXT,                       -- Full blob of the instrument data
    archived_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 5. Historical Data: Equity (Partitioned Logic - Separate Table)
CREATE TABLE IF NOT EXISTS historical_equity (
    instrument_key TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    
    PRIMARY KEY (instrument_key, timestamp),
    FOREIGN KEY (instrument_key) REFERENCES instrument_master(instrument_key)
) WITHOUT ROWID; -- Optimization for composite PK

-- 6. Historical Data: Options (Separate Table for Performance)
CREATE TABLE IF NOT EXISTS historical_options (
    instrument_key TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    oi INTEGER,                              -- Open Interest
    
    PRIMARY KEY (instrument_key, timestamp),
    FOREIGN KEY (instrument_key) REFERENCES instrument_master(instrument_key)
) WITHOUT ROWID;

-- 7. Sync Log (Audit Trail)
CREATE TABLE IF NOT EXISTS master_sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_date DATE DEFAULT CURRENT_DATE,
    total_processed INTEGER,
    inserted INTEGER,
    updated INTEGER,
    expired_flagged INTEGER,
    duration_seconds REAL,
    status TEXT
);
