-- Migration: 001_init_schema.sql
-- Normalized SQLite schema for Upstox research project
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- 1) Sectors (optional taxonomy)
CREATE TABLE IF NOT EXISTS sectors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL
);

-- 2) Master stocks / underlyings
CREATE TABLE IF NOT EXISTS master_stocks (
  symbol TEXT PRIMARY KEY,            -- e.g. RELIANCE
  company_name TEXT,
  isin TEXT,
  sector_id INTEGER,
  is_fno_enabled INTEGER DEFAULT 0,  -- 0/1
  created_at INTEGER DEFAULT (strftime('%s','now')),
  last_updated INTEGER,
  FOREIGN KEY(sector_id) REFERENCES sectors(id)
);

-- 3) Exchange-specific listings (instrument keys used by APIs)
CREATE TABLE IF NOT EXISTS exchange_listings (
  instrument_key TEXT PRIMARY KEY,    -- NSE_EQ|INE... or NSE_FO|12345
  symbol TEXT NOT NULL,               -- links to master_stocks.symbol
  trading_symbol TEXT,
  exchange TEXT,
  segment TEXT,
  exchange_token TEXT,
  lot_size INTEGER,
  tick_size REAL,
  price_precision INTEGER,
  is_active INTEGER DEFAULT 1,
  last_price REAL,
  last_updated INTEGER,
  FOREIGN KEY(symbol) REFERENCES master_stocks(symbol)
);

-- 4) Derivatives metadata (expiring contracts)
CREATE TABLE IF NOT EXISTS derivatives (
  instrument_key TEXT PRIMARY KEY,    -- e.g. NSE_FO|73507|24-04-2025
  underlying_instrument_key TEXT,     -- exchange_listings.instrument_key
  underlying_symbol TEXT,             -- master_stocks.symbol
  expiry_date TEXT,                   -- ISO date
  strike_price REAL,
  option_type TEXT,                   -- CE, PE, FUT
  lot_size INTEGER,
  is_expired INTEGER DEFAULT 0,
  created_at INTEGER,
  last_updated INTEGER,
  FOREIGN KEY(underlying_instrument_key) REFERENCES exchange_listings(instrument_key),
  FOREIGN KEY(underlying_symbol) REFERENCES master_stocks(symbol)
);

-- 5) Time-series candles (normalized). Narrow table optimized for queries.
CREATE TABLE IF NOT EXISTS candles (
  instrument_key TEXT NOT NULL,
  timeframe_unit TEXT NOT NULL,   -- 'minutes','hours','days','weeks','months'
  interval INTEGER NOT NULL,      -- 1,5,15,30 etc.
  ts INTEGER NOT NULL,            -- epoch seconds (candle start)
  open REAL, high REAL, low REAL, close REAL,
  volume REAL,
  oi REAL,
  PRIMARY KEY (instrument_key, timeframe_unit, interval, ts),
  FOREIGN KEY(instrument_key) REFERENCES exchange_listings(instrument_key)
);

-- 6) Option market data / greeks time-series
CREATE TABLE IF NOT EXISTS option_market_data (
  instrument_key TEXT NOT NULL,
  ts INTEGER NOT NULL,
  ltp REAL,
  bid_price REAL, bid_qty INTEGER,
  ask_price REAL, ask_qty INTEGER,
  oi REAL, iv REAL,
  delta REAL, gamma REAL, theta REAL, vega REAL,
  pop REAL,                         -- probability of profit
  PRIMARY KEY(instrument_key, ts),
  FOREIGN KEY(instrument_key) REFERENCES exchange_listings(instrument_key)
);

-- 7) Option chain snapshots (store raw JSON + metadata for reproducibility)
CREATE TABLE IF NOT EXISTS option_chain_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  underlying_instrument_key TEXT,
  expiry_date TEXT,
  snapshot_ts INTEGER,               -- epoch when snapshot taken
  raw_json TEXT,                     -- compressed/trimmed JSON
  created_at INTEGER DEFAULT (strftime('%s','now')),
  FOREIGN KEY(underlying_instrument_key) REFERENCES exchange_listings(instrument_key)
);

-- 8) Trades / fills (for reconciliation & simulation)
CREATE TABLE IF NOT EXISTS trades (
  trade_id TEXT PRIMARY KEY,
  order_id TEXT,
  instrument_key TEXT,
  ts INTEGER,
  price REAL,
  qty REAL,
  side TEXT,
  FOREIGN KEY(instrument_key) REFERENCES exchange_listings(instrument_key)
);

-- 9) OAuth tokens (secure storage only on local machine)
CREATE TABLE IF NOT EXISTS oauth_tokens (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE,
  access_token TEXT,
  refresh_token TEXT,
  expires_at INTEGER,
  created_at INTEGER DEFAULT (strftime('%s','now'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_master_sector ON master_stocks(sector_id);
CREATE INDEX IF NOT EXISTS idx_deriv_underlying_expiry ON derivatives(underlying_symbol, expiry_date);
CREATE INDEX IF NOT EXISTS idx_candles_instrument_ts ON candles(instrument_key, ts);
CREATE INDEX IF NOT EXISTS idx_option_md_instrument_ts ON option_market_data(instrument_key, ts);
CREATE INDEX IF NOT EXISTS idx_snapshots_underlying ON option_chain_snapshots(underlying_instrument_key, expiry_date);

-- Vacuum and analyze recommended after large imports
-- VACUUM;
-- ANALYZE;
