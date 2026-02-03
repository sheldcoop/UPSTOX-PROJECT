#!/usr/bin/env python3
"""
Database Indexing Script
Adds indexes to improve query performance
Works with both SQLite and PostgreSQL
"""

import sqlite3
import os
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_sqlite_indexes(db_path="market_data.db"):
    """Create indexes for SQLite database"""

    indexes = [
        # OHLC data - most queried table
        "CREATE INDEX IF NOT EXISTS idx_ohlc_symbol_timestamp ON ohlc_data(symbol, timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_ohlc_timestamp ON ohlc_data(timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_ohlc_symbol ON ohlc_data(symbol)",
        # Trading signals
        "CREATE INDEX IF NOT EXISTS idx_signals_symbol ON trading_signals(symbol)",
        "CREATE INDEX IF NOT EXISTS idx_signals_created ON trading_signals(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_signals_status ON trading_signals(status)",
        # Paper trading orders
        "CREATE INDEX IF NOT EXISTS idx_paper_orders_symbol ON paper_orders(symbol)",
        "CREATE INDEX IF NOT EXISTS idx_paper_orders_status ON paper_orders(status)",
        "CREATE INDEX IF NOT EXISTS idx_paper_orders_created ON paper_orders(created_at DESC)",
        # Risk metrics
        "CREATE INDEX IF NOT EXISTS idx_risk_metrics_date ON risk_metrics(date DESC)",
        # Alert rules
        "CREATE INDEX IF NOT EXISTS idx_alert_rules_symbol ON alert_rules(symbol)",
        "CREATE INDEX IF NOT EXISTS idx_alert_rules_active ON alert_rules(is_active)",
        # Performance metrics
        "CREATE INDEX IF NOT EXISTS idx_performance_date ON performance_metrics(date DESC)",
        # Market data tables
        "CREATE INDEX IF NOT EXISTS idx_options_expiry ON options_chain(expiry_date)",
        "CREATE INDEX IF NOT EXISTS idx_options_symbol ON options_chain(underlying_symbol)",
        # News and announcements
        "CREATE INDEX IF NOT EXISTS idx_news_timestamp ON news_data(published_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_announcements_date ON corporate_announcements(announcement_date DESC)",
    ]

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        logger.info(f"Creating indexes for {db_path}")

        for idx_sql in indexes:
            try:
                cursor.execute(idx_sql)
                index_name = idx_sql.split("IF NOT EXISTS ")[1].split(" ON ")[0]
                logger.info(f"✓ Created index: {index_name}")
            except sqlite3.OperationalError as e:
                if "no such table" in str(e).lower():
                    logger.warning(
                        f"⚠ Skipped (table doesn't exist): {idx_sql.split('ON ')[1].split('(')[0]}"
                    )
                else:
                    logger.error(f"✗ Error creating index: {e}")

        conn.commit()
        conn.close()
        logger.info("\n✅ SQLite indexing completed!")

    except Exception as e:
        logger.error(f"❌ Error creating indexes: {e}")
        raise


def create_postgresql_indexes(db_url):
    """Create indexes for PostgreSQL database"""
    try:
        import psycopg2

        indexes = [
            # OHLC data
            "CREATE INDEX IF NOT EXISTS idx_ohlc_symbol_timestamp ON ohlc_data(symbol, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_ohlc_timestamp ON ohlc_data(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_ohlc_symbol ON ohlc_data(symbol)",
            # Trading signals
            "CREATE INDEX IF NOT EXISTS idx_signals_symbol ON trading_signals(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_signals_created ON trading_signals(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_signals_status ON trading_signals(status)",
            # Paper trading
            "CREATE INDEX IF NOT EXISTS idx_paper_orders_symbol ON paper_orders(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_paper_orders_status ON paper_orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_paper_orders_created ON paper_orders(created_at DESC)",
            # Risk metrics
            "CREATE INDEX IF NOT EXISTS idx_risk_metrics_date ON risk_metrics(date DESC)",
            # Alert rules
            "CREATE INDEX IF NOT EXISTS idx_alert_rules_symbol ON alert_rules(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_alert_rules_active ON alert_rules(is_active)",
            # Performance
            "CREATE INDEX IF NOT EXISTS idx_performance_date ON performance_metrics(date DESC)",
            # Options
            "CREATE INDEX IF NOT EXISTS idx_options_expiry ON options_chain(expiry_date)",
            "CREATE INDEX IF NOT EXISTS idx_options_symbol ON options_chain(underlying_symbol)",
            # News
            "CREATE INDEX IF NOT EXISTS idx_news_timestamp ON news_data(published_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_announcements_date ON corporate_announcements(announcement_date DESC)",
        ]

        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        logger.info("Creating indexes for PostgreSQL")

        for idx_sql in indexes:
            try:
                cursor.execute(idx_sql)
                index_name = idx_sql.split("IF NOT EXISTS ")[1].split(" ON ")[0]
                logger.info(f"✓ Created index: {index_name}")
            except Exception as e:
                logger.warning(f"⚠ Skipped: {str(e)}")

        conn.commit()
        conn.close()
        logger.info("\n✅ PostgreSQL indexing completed!")

    except ImportError:
        logger.error(
            "psycopg2 not installed. Install with: pip install psycopg2-binary"
        )
        raise
    except Exception as e:
        logger.error(f"❌ Error creating PostgreSQL indexes: {e}")
        raise


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Create database indexes")
    parser.add_argument(
        "--db-type",
        choices=["sqlite", "postgresql"],
        default="sqlite",
        help="Database type (default: sqlite)",
    )
    parser.add_argument(
        "--db-path",
        default="market_data.db",
        help="SQLite database path (default: market_data.db)",
    )
    parser.add_argument(
        "--db-url",
        default="postgresql://upstox:upstox_password@localhost:5432/upstox_trading",
        help="PostgreSQL connection URL",
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Database Indexing Tool")
    logger.info("=" * 60)

    if args.db_type == "sqlite":
        create_sqlite_indexes(args.db_path)
    else:
        create_postgresql_indexes(args.db_url)


if __name__ == "__main__":
    main()
