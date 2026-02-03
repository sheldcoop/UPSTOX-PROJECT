"""
Test Utilities for Upstox Project
"""

import os
import sqlite3
import logging


def initialize_database(db_path=":memory:"):
    """
    Initialize database with the new schema for testing.
    Reads from migrations/001_init_schema.sql
    """
    if db_path != ":memory:" and os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Locate schema file
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(project_root, "migrations", "001_init_schema.sql")

    if not os.path.exists(schema_path):
        # Fallback to local schema string if file not found (e.g. CI/CD)
        # But we prefer reading the file.
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    with open(schema_path, "r") as f:
        schema_sql = f.read()

    cursor.executescript(schema_sql)

    # Also create the 'candles_new' table if it's not in the main schema yet
    # (Based on candle_fetcher.py logic)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS candles_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            instrument_key TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER NOT NULL,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(instrument_key, timeframe, timestamp)
        )
    """
    )

    conn.commit()
    conn.close()
    logging.info(f"Initialized test database at {db_path}")
