-- Table A: Option Equity Intraday (Underlying Spot)
-- Optimized for high-frequency writes and duplicate prevention

CREATE TABLE IF NOT EXISTS option_equity_intraday_ohlcv (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_key TEXT NOT NULL,       -- NSE_EQ|INE...
    timestamp DATETIME NOT NULL,        -- Candle Open Time (UTC or IST as per source)
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraint to prevent duplicate candles for the same time
    UNIQUE(instrument_key, timestamp) ON CONFLICT IGNORE
);

-- Index for fast retrieval of latest candles
CREATE INDEX IF NOT EXISTS idx_opt_equity_key_time 
ON option_equity_intraday_ohlcv(instrument_key, timestamp DESC);
