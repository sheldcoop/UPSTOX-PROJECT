#!/usr/bin/env python3
"""
PostgreSQL Migration Script
Migrates data from SQLite to PostgreSQL
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
import sys
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Migrate SQLite database to PostgreSQL"""

    def __init__(self, sqlite_path, postgres_url):
        self.sqlite_path = sqlite_path
        self.postgres_url = postgres_url
        self.sqlite_conn = None
        self.postgres_conn = None

    def connect(self):
        """Connect to both databases"""
        logger.info(f"Connecting to SQLite: {self.sqlite_path}")
        self.sqlite_conn = sqlite3.connect(self.sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row

        logger.info("Connecting to PostgreSQL")
        self.postgres_conn = psycopg2.connect(self.postgres_url)
        self.postgres_conn.autocommit = False

    def get_tables(self):
        """Get list of tables from SQLite"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row[0] for row in cursor.fetchall()]

    def get_table_schema(self, table_name):
        """Get table schema from SQLite"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return cursor.fetchall()

    def convert_type(self, sqlite_type):
        """Convert SQLite type to PostgreSQL type"""
        type_map = {
            "INTEGER": "INTEGER",
            "REAL": "REAL",
            "TEXT": "TEXT",
            "BLOB": "BYTEA",
            "NUMERIC": "NUMERIC",
            "DATETIME": "TIMESTAMP",
            "DATE": "DATE",
            "BOOLEAN": "BOOLEAN",
        }

        sqlite_type = sqlite_type.upper()
        for key in type_map:
            if key in sqlite_type:
                return type_map[key]
        return "TEXT"  # Default fallback

    def create_table(self, table_name):
        """Create table in PostgreSQL with same schema as SQLite"""
        schema = self.get_table_schema(table_name)

        columns = []
        for col in schema:
            col_name = col[1]
            col_type = self.convert_type(col[2])
            not_null = " NOT NULL" if col[3] else ""
            pk = " PRIMARY KEY" if col[5] else ""

            columns.append(f"{col_name} {col_type}{not_null}{pk}")

        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"

        cursor = self.postgres_conn.cursor()
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            cursor.execute(create_sql)
            logger.info(f"Created table: {table_name}")
        except Exception as e:
            logger.error(f"Error creating table {table_name}: {e}")
            raise

    def migrate_table_data(self, table_name):
        """Migrate data from SQLite table to PostgreSQL"""
        logger.info(f"Migrating data for table: {table_name}")

        # Get data from SQLite
        sqlite_cursor = self.sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()

        if not rows:
            logger.info(f"No data to migrate for table: {table_name}")
            return

        # Get column names
        columns = [description[0] for description in sqlite_cursor.description]

        # Convert rows to tuples
        data = [tuple(dict(row).values()) for row in rows]

        # Insert into PostgreSQL
        postgres_cursor = self.postgres_conn.cursor()
        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES %s"

        try:
            execute_values(postgres_cursor, insert_sql, data)
            logger.info(f"Migrated {len(data)} rows for table: {table_name}")
        except Exception as e:
            logger.error(f"Error migrating data for {table_name}: {e}")
            raise

    def migrate(self):
        """Perform full migration"""
        try:
            self.connect()

            # Get all tables
            tables = self.get_tables()
            logger.info(f"Found {len(tables)} tables to migrate")

            for table in tables:
                logger.info(f"\nProcessing table: {table}")
                self.create_table(table)
                self.migrate_table_data(table)

            # Commit transaction
            self.postgres_conn.commit()
            logger.info("\n✅ Migration completed successfully!")

        except Exception as e:
            logger.error(f"\n❌ Migration failed: {e}")
            if self.postgres_conn:
                self.postgres_conn.rollback()
            raise

        finally:
            if self.sqlite_conn:
                self.sqlite_conn.close()
            if self.postgres_conn:
                self.postgres_conn.close()


def main():
    """Main entry point"""
    # Get database URLs from environment or defaults
    sqlite_path = os.getenv("SQLITE_PATH", "market_data.db")
    postgres_url = os.getenv(
        "DATABASE_URL",
        "postgresql://upstox:upstox_password@localhost:5432/upstox_trading",
    )

    if not os.path.exists(sqlite_path):
        logger.error(f"SQLite database not found: {sqlite_path}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("PostgreSQL Migration Tool")
    logger.info("=" * 60)
    logger.info(f"Source: {sqlite_path}")
    logger.info(f"Target: {postgres_url}")
    logger.info("=" * 60)

    response = input(
        "\nThis will overwrite existing PostgreSQL tables. Continue? (yes/no): "
    )
    if response.lower() != "yes":
        logger.info("Migration cancelled")
        sys.exit(0)

    migrator = DatabaseMigrator(sqlite_path, postgres_url)
    migrator.migrate()


if __name__ == "__main__":
    main()
