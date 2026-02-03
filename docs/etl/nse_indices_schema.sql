-- NSE Indices ETL Schema for SQLite
-- Version: 1.0
-- Date: 2026-02-03
-- Purpose: Create all required tables, views, and indexes for NSE indices ETL

-- Enable foreign key support
PRAGMA foreign_keys = ON;

-- Set journal mode to WAL for better concurrency during ETL
PRAGMA journal_mode = WAL;

-- ============================================================================
-- MASTER TABLES
-- ============================================================================

-- Indices master table
CREATE TABLE IF NOT EXISTS indices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  index_code TEXT UNIQUE NOT NULL,
  index_name TEXT NOT NULL,
  index_type TEXT,
  source_url TEXT,
  last_updated TEXT,
  metadata_json TEXT
);

-- Companies master table
CREATE TABLE IF NOT EXISTS companies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  isin TEXT UNIQUE NOT NULL,
  symbol TEXT NOT NULL,
  company_name TEXT NOT NULL,
  listed_exchange TEXT DEFAULT 'NSE',
  metadata_json TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

-- ============================================================================
-- RELATIONSHIP TABLES
-- ============================================================================

-- Index constituents mapping
CREATE TABLE IF NOT EXISTS index_constituents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  index_id INTEGER NOT NULL,
  company_id INTEGER NOT NULL,
  weight REAL,
  effective_date TEXT NOT NULL,
  source_csv_url TEXT,
  raw_row_json TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(index_id) REFERENCES indices(id) ON DELETE CASCADE,
  FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
  UNIQUE(index_id, company_id, effective_date)
);

-- ============================================================================
-- CLASSIFICATION TABLES
-- ============================================================================

-- Sector/Industry classification
CREATE TABLE IF NOT EXISTS sectors (
  code TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  parent_code TEXT,
  classification_level TEXT,
  source_page INTEGER,
  FOREIGN KEY(parent_code) REFERENCES sectors(code)
);

-- Company to sector mapping
CREATE TABLE IF NOT EXISTS company_sector_map (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_id INTEGER NOT NULL,
  sector_code TEXT,
  industry_code TEXT,
  assigned_date TEXT DEFAULT (datetime('now')),
  is_current BOOLEAN DEFAULT 1,
  FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
  FOREIGN KEY(sector_code) REFERENCES sectors(code),
  UNIQUE(company_id, sector_code, industry_code, assigned_date)
);

-- ============================================================================
-- DERIVATIVES TABLES
-- ============================================================================

-- Derivatives metadata
CREATE TABLE IF NOT EXISTS derivatives_metadata (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  market_type TEXT,
  instrument_type TEXT,
  underlying TEXT,
  underlying_isin TEXT,
  security_descriptor TEXT,
  contract_size INTEGER,
  tick_size REAL,
  lot_size INTEGER,
  source_url TEXT,
  last_scraped TEXT,
  metadata_json TEXT,
  UNIQUE(symbol, instrument_type, underlying)
);

-- ============================================================================
-- ETL MANAGEMENT TABLES
-- ============================================================================

-- Import manifest for tracking ETL runs
CREATE TABLE IF NOT EXISTS import_manifest (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_url TEXT NOT NULL,
  source_file_name TEXT NOT NULL,
  file_hash TEXT,
  download_timestamp TEXT NOT NULL,
  rows_expected INTEGER,
  rows_imported INTEGER,
  rows_flagged INTEGER,
  errors_json TEXT,
  pdf_version TEXT,
  import_status TEXT DEFAULT 'success',
  created_at TEXT DEFAULT (datetime('now'))
);

-- ============================================================================
-- COMPATIBILITY VIEWS
-- ============================================================================

-- View: Companies with their index memberships
CREATE VIEW IF NOT EXISTS view_companies_with_index AS
SELECT 
  c.id as company_id,
  c.isin,
  c.symbol,
  c.company_name,
  c.listed_exchange,
  i.id as index_id,
  i.index_code,
  i.index_name,
  i.index_type,
  ic.weight,
  ic.effective_date,
  ic.source_csv_url
FROM companies c
JOIN index_constituents ic ON ic.company_id = c.id
JOIN indices i ON i.id = ic.index_id;

-- View: Index constituents with full details
CREATE VIEW IF NOT EXISTS view_index_constituents AS
SELECT 
  i.index_code,
  i.index_name,
  i.index_type,
  c.isin,
  c.symbol,
  c.company_name,
  ic.weight,
  ic.effective_date,
  ic.source_csv_url
FROM index_constituents ic
JOIN indices i ON i.id = ic.index_id
JOIN companies c ON c.id = ic.company_id
ORDER BY i.index_code, ic.weight DESC;

-- View: Company sector assignments
CREATE VIEW IF NOT EXISTS view_company_sectors AS
SELECT 
  c.isin,
  c.symbol,
  c.company_name,
  s.code as sector_code,
  s.name as sector_name,
  s.classification_level,
  csm.assigned_date
FROM companies c
JOIN company_sector_map csm ON csm.company_id = c.id
JOIN sectors s ON s.code = csm.sector_code
WHERE csm.is_current = 1;

-- View: Derivatives with underlying details
CREATE VIEW IF NOT EXISTS view_derivatives_with_underlying AS
SELECT 
  d.symbol,
  d.market_type,
  d.instrument_type,
  d.underlying,
  d.underlying_isin,
  d.security_descriptor,
  CASE 
    WHEN i.index_code IS NOT NULL THEN 'INDEX'
    WHEN c.isin IS NOT NULL THEN 'EQUITY'
    ELSE 'UNKNOWN'
  END as underlying_type,
  COALESCE(i.index_name, c.company_name) as underlying_name,
  d.last_scraped
FROM derivatives_metadata d
LEFT JOIN indices i ON i.index_code = d.underlying
LEFT JOIN companies c ON c.isin = d.underlying_isin;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Companies indexes
CREATE INDEX IF NOT EXISTS idx_companies_isin ON companies(isin);
CREATE INDEX IF NOT EXISTS idx_companies_symbol ON companies(symbol);
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(company_name);

-- Indices indexes
CREATE INDEX IF NOT EXISTS idx_indices_code ON indices(index_code);
CREATE INDEX IF NOT EXISTS idx_indices_type ON indices(index_type);

-- Index constituents indexes
CREATE INDEX IF NOT EXISTS idx_const_index_id ON index_constituents(index_id);
CREATE INDEX IF NOT EXISTS idx_const_company_id ON index_constituents(company_id);
CREATE INDEX IF NOT EXISTS idx_const_idx_comp ON index_constituents(index_id, company_id);
CREATE INDEX IF NOT EXISTS idx_const_effective_date ON index_constituents(effective_date);

-- Sector indexes
CREATE INDEX IF NOT EXISTS idx_sectors_level ON sectors(classification_level);
CREATE INDEX IF NOT EXISTS idx_sectors_parent ON sectors(parent_code);

-- Company sector map indexes
CREATE INDEX IF NOT EXISTS idx_csm_company_id ON company_sector_map(company_id);
CREATE INDEX IF NOT EXISTS idx_csm_sector_code ON company_sector_map(sector_code);
CREATE INDEX IF NOT EXISTS idx_csm_current ON company_sector_map(is_current);

-- Derivatives indexes
CREATE INDEX IF NOT EXISTS idx_derivatives_underlying ON derivatives_metadata(underlying);
CREATE INDEX IF NOT EXISTS idx_derivatives_underlying_isin ON derivatives_metadata(underlying_isin);
CREATE INDEX IF NOT EXISTS idx_derivatives_instrument_type ON derivatives_metadata(instrument_type);
CREATE INDEX IF NOT EXISTS idx_derivatives_market_type ON derivatives_metadata(market_type);

-- Import manifest indexes
CREATE INDEX IF NOT EXISTS idx_manifest_timestamp ON import_manifest(download_timestamp);
CREATE INDEX IF NOT EXISTS idx_manifest_source ON import_manifest(source_file_name);
CREATE INDEX IF NOT EXISTS idx_manifest_hash ON import_manifest(file_hash);

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ============================================================================

-- Update timestamp on companies update
CREATE TRIGGER IF NOT EXISTS update_companies_timestamp 
AFTER UPDATE ON companies
BEGIN
  UPDATE companies SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- ============================================================================
-- STATISTICS AND OPTIMIZATION
-- ============================================================================

-- Run ANALYZE to gather statistics for query optimizer
ANALYZE;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Uncomment to run verification after schema creation:
-- SELECT 'Tables created:' as info;
-- SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
-- 
-- SELECT 'Views created:' as info;
-- SELECT name FROM sqlite_master WHERE type='view' ORDER BY name;
-- 
-- SELECT 'Indexes created:' as info;
-- SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY name;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

-- Print completion message
SELECT 'NSE Indices ETL schema created successfully!' as status;
SELECT 'Tables: indices, companies, index_constituents, sectors, company_sector_map, derivatives_metadata, import_manifest' as created_tables;
SELECT 'Views: view_companies_with_index, view_index_constituents, view_company_sectors, view_derivatives_with_underlying' as created_views;
SELECT 'Ready for ETL import!' as next_step;
