-- Table B: Option Chain Intraday (Wide Schema)
-- Stores 5-minute snapshot of Option Chain for 212 stocks
-- One row per Strike per Expiry (Contains both CE and PE data)

CREATE TABLE IF NOT EXISTS optionchain_intrday_schema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    underlying_key TEXT NOT NULL,         -- FK to instrument_master (e.g. NSE_INDEX|Nifty 50)
    expiry_date DATE NOT NULL,            -- e.g. 2024-03-28
    timestamp DATETIME NOT NULL,          -- Snapshot Time
    strike_price REAL NOT NULL,
    pcr REAL,                             -- Put Call Ratio (Vol/OI based)

    -- Call Option Data (CE)
    ce_instrument_key TEXT,
    ce_ltp REAL,
    ce_volume INTEGER,
    ce_oi INTEGER,
    ce_bid_price REAL,
    ce_ask_price REAL,
    ce_iv REAL,
    ce_delta REAL,
    ce_gamma REAL,
    ce_theta REAL,
    ce_vega REAL,
    ce_rho REAL,
    
    -- Put Option Data (PE)
    pe_instrument_key TEXT,
    pe_ltp REAL,
    pe_volume INTEGER,
    pe_oi INTEGER,
    pe_bid_price REAL,
    pe_ask_price REAL,
    pe_iv REAL,
    pe_delta REAL,
    pe_gamma REAL,
    pe_theta REAL,
    pe_vega REAL,
    pe_rho REAL,

    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Unique Constraint: One snapshot per strike per time per expiry
    UNIQUE(underlying_key, expiry_date, strike_price, timestamp) ON CONFLICT IGNORE
);

CREATE INDEX IF NOT EXISTS idx_opt_chain_lookup 
ON optionchain_intrday_schema(underlying_key, expiry_date, timestamp);
