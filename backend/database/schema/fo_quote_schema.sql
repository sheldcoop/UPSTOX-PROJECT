-- Table E: F&O Market Quote Data (212 Stocks Liquidity)
-- Stores 5-minute snapshots of the 212 F&O Underlying Stocks
-- Structure: Clone of market_quota_nse500_data

CREATE TABLE IF NOT EXISTS market_quota_fo_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_key TEXT NOT NULL,       -- NSE_EQ|...
    timestamp DATETIME NOT NULL,        -- Snapshot Time
    
    -- OHLCV
    open REAL,
    high REAL,
    low REAL,
    close REAL,            -- last_price
    volume INTEGER,
    average_price REAL,
    
    -- Overall Liquidity / Pressure
    total_buy_quantity INTEGER,
    total_sell_quantity INTEGER,
    oi REAL,               -- Open Interest
    
    -- Flattened Market Depth (Top 5 Bids)
    bid_price_1 REAL, bid_qty_1 INTEGER, bid_orders_1 INTEGER,
    bid_price_2 REAL, bid_qty_2 INTEGER, bid_orders_2 INTEGER,
    bid_price_3 REAL, bid_qty_3 INTEGER, bid_orders_3 INTEGER,
    bid_price_4 REAL, bid_qty_4 INTEGER, bid_orders_4 INTEGER,
    bid_price_5 REAL, bid_qty_5 INTEGER, bid_orders_5 INTEGER,

    -- Flattened Market Depth (Top 5 Asks/Sells)
    ask_price_1 REAL, ask_qty_1 INTEGER, ask_orders_1 INTEGER,
    ask_price_2 REAL, ask_qty_2 INTEGER, ask_orders_2 INTEGER,
    ask_price_3 REAL, ask_qty_3 INTEGER, ask_orders_3 INTEGER,
    ask_price_4 REAL, ask_qty_4 INTEGER, ask_orders_4 INTEGER,
    ask_price_5 REAL, ask_qty_5 INTEGER, ask_orders_5 INTEGER,

    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Constraints: One snapshot per instrument per time
    UNIQUE(instrument_key, timestamp) ON CONFLICT IGNORE
);

CREATE INDEX IF NOT EXISTS idx_fo_lookup 
ON market_quota_fo_data(instrument_key, timestamp DESC);
