"""
Database Connection Pooling with SQLAlchemy
Improves database performance with connection reuse
"""

import os
import logging
from typing import Optional
from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import sqlite3

logger = logging.getLogger(__name__)

# Base class for ORM models
Base = declarative_base()


class DatabasePool:
    """
    Database connection pool manager
    Supports both SQLite and PostgreSQL
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database pool

        Args:
            database_url: Database connection URL
                         SQLite: sqlite:///market_data.db
                         PostgreSQL: postgresql://user:pass@host:port/db
        """
        if database_url is None:
            # Default to SQLite
            database_url = os.getenv("DATABASE_URL", "sqlite:///market_data.db")

        self.database_url = database_url
        self.engine = None
        self.Session = None
        self._setup_engine()

    def _setup_engine(self):
        """Setup SQLAlchemy engine with connection pooling"""

        if self.database_url.startswith("sqlite"):
            # SQLite configuration
            self.engine = create_engine(
                self.database_url,
                poolclass=pool.StaticPool,  # Better for SQLite
                connect_args={"check_same_thread": False},
                echo=False,
            )

            # Enable WAL mode for better concurrency
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.close()

            logger.info(f"✓ SQLite connection pool initialized: {self.database_url}")

        else:
            # PostgreSQL configuration
            self.engine = create_engine(
                self.database_url,
                poolclass=pool.QueuePool,
                pool_size=10,  # Number of connections to maintain
                max_overflow=20,  # Max extra connections
                pool_timeout=30,  # Timeout for getting connection
                pool_recycle=3600,  # Recycle connections after 1 hour
                pool_pre_ping=True,  # Test connections before using
                echo=False,
            )

            logger.info(f"✓ PostgreSQL connection pool initialized")
            logger.info(f"  Pool size: 10, Max overflow: 20")

        # Create session factory
        self.Session = scoped_session(
            sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        )

    def get_session(self):
        """
        Get a database session from the pool

        Returns:
            SQLAlchemy Session object
        """
        return self.Session()

    def close_session(self, session):
        """
        Return session to pool

        Args:
            session: SQLAlchemy Session to close
        """
        try:
            session.close()
        except Exception as e:
            logger.error(f"Error closing session: {e}")

    def execute_query(self, query: str, params: Optional[tuple] = None):
        """
        Execute a raw SQL query

        Args:
            query: SQL query string
            params: Optional query parameters

        Returns:
            Query results
        """
        session = self.get_session()
        try:
            if params:
                result = session.execute(query, params)
            else:
                result = session.execute(query)
            session.commit()
            return result.fetchall()
        except Exception as e:
            session.rollback()
            logger.error(f"Query error: {e}")
            raise
        finally:
            self.close_session(session)

    def get_pool_stats(self) -> dict:
        """
        Get connection pool statistics

        Returns:
            Dict with pool statistics
        """
        pool = self.engine.pool

        stats = {
            "pool_size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "checked_in": pool.checkedin(),
        }

        return stats

    def dispose(self):
        """Dispose of the connection pool"""
        if self.engine:
            self.engine.dispose()
            logger.info("Connection pool disposed")


# Global pool instance
_db_pool: Optional[DatabasePool] = None


def get_database_pool(database_url: Optional[str] = None) -> DatabasePool:
    """
    Get global database pool instance (singleton)

    Args:
        database_url: Optional database URL

    Returns:
        DatabasePool instance
    """
    global _db_pool

    if _db_pool is None:
        _db_pool = DatabasePool(database_url)

    return _db_pool


def get_db_session():
    """
    Convenience function to get a database session

    Returns:
        SQLAlchemy Session
    """
    pool = get_database_pool()
    return pool.get_session()


def close_db_session(session):
    """
    Convenience function to close a database session

    Args:
        session: SQLAlchemy Session to close
    """
    pool = get_database_pool()
    pool.close_session(session)


# Context manager for sessions
class DatabaseSession:
    """Context manager for database sessions"""

    def __init__(self):
        self.pool = get_database_pool()
        self.session = None

    def __enter__(self):
        self.session = self.pool.get_session()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        else:
            self.session.commit()
        self.pool.close_session(self.session)
        return False


def example_usage():
    """Example usage of database pool"""

    # Initialize pool
    pool = get_database_pool("sqlite:///market_data.db")

    # Get session and use it
    session = pool.get_session()
    try:
        result = session.execute("SELECT COUNT(*) FROM ohlc_data")
        count = result.fetchone()[0]
        print(f"Total OHLC records: {count}")
    finally:
        pool.close_session(session)

    # Using context manager
    with DatabaseSession() as session:
        result = session.execute("SELECT COUNT(*) FROM trading_signals")
        count = result.fetchone()[0]
        print(f"Total signals: {count}")

    # Get pool stats
    stats = pool.get_pool_stats()
    print(f"Pool stats: {stats}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    example_usage()
