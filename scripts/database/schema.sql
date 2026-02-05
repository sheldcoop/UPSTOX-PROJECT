-- ============================================================================
-- UPSTOX Trading Platform - Market Data Database Schema
-- ============================================================================
-- Complete schema for instruments, indices, sectors, and derivatives
-- Supports complex filtering and querying across all market data
-- ============================================================================

-- ============================================================================
-- 1. INSTRUMENTS MASTER (from Upstox API)
-- ============================================================================

CREATE TABLE IF NOT EXISTS instruments (
    instrument_key TEXT PRIMARY KEY,      -- NSE_EQ|INE002A01018
    symbol TEXT NOT NULL,                  -- RELIANCE
    trading_symbol TEXT,                   -- RELIANCE-EQ
    company_name TEXT,                     -- Reliance Industries Ltd
    exchange TEXT NOT NULL,                -- NSE, BSE
    segment TEXT NOT NULL,                 -- NSE_EQ, BSE_EQ, NSE_FO
    instrument_type TEXT,                  -- EQ, BE, SM, FUT, CE, PE
    isin TEXT,                             -- INE002A01018
    lot_size INTEGER DEFAULT 1,
    tick_size REAL DEFAULT 0.05,
    is_active BOOLEAN DEFAULT 1,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_instruments_symbol ON instruments(symbol);
CREATE INDEX IF NOT EXISTS idx_instruments_exchange ON instruments(exchange);
CREATE INDEX IF NOT EXISTS idx_instruments_segment ON instruments(segment);
CREATE INDEX IF NOT EXISTS idx_instruments_isin ON instruments(isin);
CREATE INDEX IF NOT EXISTS idx_instruments_active ON instruments(is_active);

-- ============================================================================
-- 2. INDEX MASTER (All NSE Indices Metadata)
-- ============================================================================

CREATE TABLE IF NOT EXISTS index_master (
    index_code TEXT PRIMARY KEY,           -- NIFTY50, NIFTYBANK, etc.
    index_name TEXT NOT NULL,              -- Nifty 50, Nifty Bank
    index_category TEXT NOT NULL,          -- broad, sectoral, thematic
    index_subcategory TEXT,                -- largecap, midcap, auto, pharma, esg
    description TEXT,
    base_date DATE,
    base_value REAL,
    constituent_count INTEGER,
    is_derivative_available BOOLEAN DEFAULT 0,
    csv_url TEXT,                          -- Source URL for updates
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_index_category ON index_master(index_category);
CREATE INDEX IF NOT EXISTS idx_index_subcategory ON index_master(index_subcategory);

-- ============================================================================
-- 3. INDEX CONSTITUENTS (Stock-Index Mapping)
-- ============================================================================

CREATE TABLE IF NOT EXISTS index_constituents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    index_code TEXT NOT NULL,
    symbol TEXT NOT NULL,
    company_name TEXT,
    isin TEXT,
    series TEXT,                           -- EQ, BE
    weightage REAL,                        -- % weight in index
    date_added DATE,
    is_active BOOLEAN DEFAULT 1,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (index_code) REFERENCES index_master(index_code),
    UNIQUE(index_code, symbol)
);

CREATE INDEX IF NOT EXISTS idx_constituents_index ON index_constituents(index_code);
CREATE INDEX IF NOT EXISTS idx_constituents_symbol ON index_constituents(symbol);
CREATE INDEX IF NOT EXISTS idx_constituents_active ON index_constituents(is_active);
CREATE INDEX IF NOT EXISTS idx_constituents_isin ON index_constituents(isin);

-- ============================================================================
-- 4. SECTORS (Industry Classification)
-- ============================================================================

CREATE TABLE IF NOT EXISTS sectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sector_name TEXT UNIQUE NOT NULL,      -- Financial Services, IT, Auto
    sector_code TEXT UNIQUE,               -- FIN, IT, AUTO
    parent_sector TEXT,                    -- For hierarchical classification
    description TEXT,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sector_name ON sectors(sector_name);
CREATE INDEX IF NOT EXISTS idx_sector_code ON sectors(sector_code);

-- ============================================================================
-- 5. STOCK SECTORS (Stock-Sector Mapping)
-- ============================================================================

CREATE TABLE IF NOT EXISTS stock_sectors (
    symbol TEXT PRIMARY KEY,
    company_name TEXT,
    sector_id INTEGER,
    industry TEXT,                         -- More specific than sector
    sub_industry TEXT,                     -- Even more specific
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sector_id) REFERENCES sectors(id)
);

CREATE INDEX IF NOT EXISTS idx_stock_sector ON stock_sectors(sector_id);
CREATE INDEX IF NOT EXISTS idx_stock_industry ON stock_sectors(industry);

-- ============================================================================
-- 6. DERIVATIVES METADATA (F&O Contracts)
-- ============================================================================

CREATE TABLE IF NOT EXISTS derivatives_metadata (
    instrument_key TEXT PRIMARY KEY,
    underlying_symbol TEXT NOT NULL,
    underlying_index_code TEXT,            -- For index derivatives (NIFTY50, etc.)
    derivative_type TEXT NOT NULL,         -- FUT, CE, PE
    expiry_date DATE NOT NULL,
    strike_price REAL,                     -- NULL for futures
    option_type TEXT,                      -- CE, PE, NULL for futures
    lot_size INTEGER,
    tick_size REAL,
    is_active BOOLEAN DEFAULT 1,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_deriv_underlying ON derivatives_metadata(underlying_symbol);
CREATE INDEX IF NOT EXISTS idx_deriv_index ON derivatives_metadata(underlying_index_code);
CREATE INDEX IF NOT EXISTS idx_deriv_expiry ON derivatives_metadata(expiry_date);
CREATE INDEX IF NOT EXISTS idx_deriv_type ON derivatives_metadata(derivative_type);
CREATE INDEX IF NOT EXISTS idx_deriv_active ON derivatives_metadata(is_active);

-- ============================================================================
-- 7. DATA FRESHNESS TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS data_refresh_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_source TEXT NOT NULL,             -- upstox_instruments, nse_indices, etc.
    refresh_type TEXT NOT NULL,            -- full, incremental
    records_processed INTEGER,
    records_inserted INTEGER,
    records_updated INTEGER,
    records_failed INTEGER,
    status TEXT NOT NULL,                  -- success, partial, failed
    error_message TEXT,
    started_at DATETIME,
    completed_at DATETIME,
    duration_seconds REAL
);

CREATE INDEX IF NOT EXISTS idx_refresh_source ON data_refresh_log(data_source);
CREATE INDEX IF NOT EXISTS idx_refresh_status ON data_refresh_log(status);
CREATE INDEX IF NOT EXISTS idx_refresh_completed ON data_refresh_log(completed_at);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Stocks with their complete classification
CREATE VIEW IF NOT EXISTS v_stock_classification AS
SELECT 
    i.symbol,
    i.company_name,
    i.exchange,
    i.segment,
    i.isin,
    s.sector_name,
    ss.industry,
    ss.sub_industry,
    GROUP_CONCAT(DISTINCT ic.index_code) as indices,
    CASE 
        WHEN ic50.symbol IS NOT NULL THEN 'large'
        WHEN ic_mid.symbol IS NOT NULL THEN 'mid'
        WHEN ic_small.symbol IS NOT NULL THEN 'small'
        ELSE 'other'
    END as market_cap_category,
    CASE WHEN dm.underlying_symbol IS NOT NULL THEN 1 ELSE 0 END as has_fno
FROM instruments i
LEFT JOIN stock_sectors ss ON i.symbol = ss.symbol
LEFT JOIN sectors s ON ss.sector_id = s.id
LEFT JOIN index_constituents ic ON i.symbol = ic.symbol AND ic.is_active = 1
LEFT JOIN index_constituents ic50 ON i.symbol = ic50.symbol AND ic50.index_code LIKE 'NIFTY50' AND ic50.is_active = 1
LEFT JOIN index_constituents ic_mid ON i.symbol = ic_mid.symbol AND ic_mid.index_code LIKE 'NIFTY%MIDCAP%' AND ic_mid.is_active = 1
LEFT JOIN index_constituents ic_small ON i.symbol = ic_small.symbol AND ic_small.index_code LIKE 'NIFTY%SMALLCAP%' AND ic_small.is_active = 1
LEFT JOIN (SELECT DISTINCT underlying_symbol FROM derivatives_metadata WHERE is_active = 1) dm ON i.symbol = dm.underlying_symbol
WHERE i.exchange = 'NSE' AND i.segment = 'NSE_EQ'
GROUP BY i.symbol;

-- View: Index statistics
CREATE VIEW IF NOT EXISTS v_index_stats AS
SELECT 
    im.index_code,
    im.index_name,
    im.index_category,
    im.index_subcategory,
    COUNT(ic.symbol) as actual_constituent_count,
    im.constituent_count as expected_count,
    im.is_derivative_available,
    im.last_updated
FROM index_master im
LEFT JOIN index_constituents ic ON im.index_code = ic.index_code AND ic.is_active = 1
GROUP BY im.index_code;

-- ============================================================================
-- INITIAL DATA: Index Master Metadata
-- ============================================================================

-- Broad Market Indices
INSERT OR IGNORE INTO index_master (index_code, index_name, index_category, index_subcategory, constituent_count, csv_url) VALUES
('NIFTY50', 'Nifty 50', 'broad', 'largecap', 50, 'https://archives.nseindia.com/content/indices/ind_nifty50list.csv'),
('NIFTYNEXT50', 'Nifty Next 50', 'broad', 'largecap', 50, 'https://archives.nseindia.com/content/indices/ind_niftynext50list.csv'),
('NIFTY100', 'Nifty 100', 'broad', 'largecap', 100, 'https://archives.nseindia.com/content/indices/ind_nifty100list.csv'),
('NIFTY200', 'Nifty 200', 'broad', 'largecap', 200, 'https://archives.nseindia.com/content/indices/ind_nifty200list.csv'),
('NIFTY500', 'Nifty 500', 'broad', 'diversified', 500, 'https://archives.nseindia.com/content/indices/ind_nifty500list.csv'),
('NIFTYMIDCAP50', 'Nifty Midcap 50', 'broad', 'midcap', 50, 'https://archives.nseindia.com/content/indices/ind_niftymidcap50list.csv'),
('NIFTYMIDCAP100', 'Nifty Midcap 100', 'broad', 'midcap', 100, 'https://archives.nseindia.com/content/indices/ind_niftymidcap100list.csv'),
('NIFTYMIDCAP150', 'Nifty Midcap 150', 'broad', 'midcap', 150, 'https://archives.nseindia.com/content/indices/ind_niftymidcap150list.csv'),
('NIFTYSMALLCAP50', 'Nifty Smallcap 50', 'broad', 'smallcap', 50, 'https://archives.nseindia.com/content/indices/ind_niftysmallcap50list.csv'),
('NIFTYSMALLCAP100', 'Nifty Smallcap 100', 'broad', 'smallcap', 100, 'https://archives.nseindia.com/content/indices/ind_niftysmallcap100list.csv'),
('NIFTYSMALLCAP250', 'Nifty Smallcap 250', 'broad', 'smallcap', 250, 'https://archives.nseindia.com/content/indices/ind_niftysmallcap250list.csv');

-- Sectoral Indices
INSERT OR IGNORE INTO index_master (index_code, index_name, index_category, index_subcategory, is_derivative_available, csv_url) VALUES
('NIFTYAUTO', 'Nifty Auto', 'sectoral', 'auto', 0, 'https://archives.nseindia.com/content/indices/ind_niftyautolist.csv'),
('NIFTYBANK', 'Nifty Bank', 'sectoral', 'bank', 1, 'https://archives.nseindia.com/content/indices/ind_niftybanklist.csv'),
('NIFTYFINSERVICE', 'Nifty Financial Services', 'sectoral', 'financial', 1, 'https://archives.nseindia.com/content/indices/ind_niftyfinancelist.csv'),
('NIFTYFMCG', 'Nifty FMCG', 'sectoral', 'fmcg', 0, 'https://archives.nseindia.com/content/indices/ind_niftyfmcglist.csv'),
('NIFTYIT', 'Nifty IT', 'sectoral', 'it', 0, 'https://archives.nseindia.com/content/indices/ind_niftyitlist.csv'),
('NIFTYMEDIA', 'Nifty Media', 'sectoral', 'media', 0, 'https://archives.nseindia.com/content/indices/ind_niftymedialist.csv'),
('NIFTYMETAL', 'Nifty Metal', 'sectoral', 'metal', 0, 'https://archives.nseindia.com/content/indices/ind_niftymetallist.csv'),
('NIFTYPHARMA', 'Nifty Pharma', 'sectoral', 'pharma', 0, 'https://archives.nseindia.com/content/indices/ind_niftypharmalist.csv'),
('NIFTYREALTY', 'Nifty Realty', 'sectoral', 'realty', 0, 'https://archives.nseindia.com/content/indices/ind_niftyrealtylist.csv');

-- ============================================================================
-- UTILITY FUNCTIONS (for application code)
-- ============================================================================

-- These are SQL queries that can be used in Python code

-- Get stocks by multiple filters:
-- SELECT * FROM v_stock_classification 
-- WHERE indices LIKE '%NIFTY50%' 
-- AND sector_name = 'Information Technology'
-- AND has_fno = 1;

-- Get index overlap:
-- SELECT ic1.symbol 
-- FROM index_constituents ic1
-- JOIN index_constituents ic2 ON ic1.symbol = ic2.symbol
-- WHERE ic1.index_code = 'NIFTY50' 
-- AND ic2.index_code = 'NIFTYBANK'
-- AND ic1.is_active = 1 AND ic2.is_active = 1;

-- Get all indices a stock belongs to:
-- SELECT index_code, index_name, weightage
-- FROM index_constituents ic
-- JOIN index_master im ON ic.index_code = im.index_code
-- WHERE ic.symbol = 'RELIANCE' AND ic.is_active = 1;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
