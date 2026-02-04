#!/usr/bin/env python3
"""
Database Connection Pool for SQLite
Provides thread-safe connection pooling to prevent 'database is locked' errors
"""

import sqlite3
import logging
from contextlib import contextmanager
from queue import Queue, Empty
from threading import Lock
from typing import Optional
import os

logger = logging.getLogger(__name__)


class DatabasePool:
    """
    SQLite connection pool with thread-safe access.

    Features:
    - Connection pooling to prevent exhaustion
    - Thread-safe connection checkout/checkin
    - Automatic connection reuse
    - Configurable pool size
    - Context manager support

    Usage:
        # Create pool
        db_pool = DatabasePool("market_data.db", pool_size=5)

        # Use connection
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ohlc_data")
            results = cursor.fetchall()
    """

    _instances = {}
    _lock = Lock()

    def __new__(cls, db_path: str, pool_size: int = 5):
        """Singleton pattern - one pool per database file"""
        with cls._lock:
            if db_path not in cls._instances:
                instance = super(DatabasePool, cls).__new__(cls)
                cls._instances[db_path] = instance
            return cls._instances[db_path]

    def __init__(self, db_path: str, pool_size: int = 5):
        """
        Initialize database connection pool.

        Args:
            db_path: Path to SQLite database file
            pool_size: Number of connections in the pool (default: 5)
        """
        # Only initialize once (singleton pattern)
        if hasattr(self, "_initialized"):
            return

        self.db_path = os.path.abspath(db_path)
        self.pool_size = pool_size
        self.pool = Queue(maxsize=pool_size)
        self._initialized = True

        # Create pool of connections
        for _ in range(pool_size):
            conn = self._create_connection()
            self.pool.put(conn)

        logger.info(f"✅ Database pool initialized: {self.db_path} (size: {pool_size})")

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimal settings"""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,  # Allow sharing across threads
            timeout=30.0,  # Wait up to 30s for locks
            isolation_level="DEFERRED",  # Better concurrency
        )

        # Enable WAL mode for better concurrent access
        conn.execute("PRAGMA journal_mode=WAL")

        # Set busy timeout
        conn.execute("PRAGMA busy_timeout=30000")  # 30 seconds

        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys=ON")

        # Row factory for dict-like access
        conn.row_factory = sqlite3.Row

        return conn

    @contextmanager
    def get_connection(self, timeout: Optional[float] = None):
        """
        Get a connection from the pool (context manager).

        Args:
            timeout: Maximum time to wait for a connection (seconds)

        Yields:
            sqlite3.Connection: Database connection

        Example:
            with db_pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
        """
        conn = None
        try:
            # Get connection from pool
            if timeout:
                conn = self.pool.get(timeout=timeout)
            else:
                conn = self.pool.get()

            yield conn

            # Commit on successful completion
            if conn:
                conn.commit()

        except Empty:
            logger.error("⚠️  Connection pool exhausted - all connections in use")
            raise RuntimeError("Database connection pool exhausted")

        except Exception as e:
            # Rollback on error
            if conn:
                conn.rollback()
            logger.error(f"❌ Database error: {e}", exc_info=True)
            raise

        finally:
            # Return connection to pool
            if conn:
                self.pool.put(conn)

    def close_all(self):
        """Close all connections in the pool"""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except Empty:
                break

        logger.info(f"✅ Database pool closed: {self.db_path}")

    def __del__(self):
        """Cleanup on garbage collection"""
        self.close_all()


# Global pool instances for common databases
_default_pool: Optional[DatabasePool] = None


def get_db_pool(db_path: str = "market_data.db", pool_size: int = 5) -> DatabasePool:
    """
    Get or create a database connection pool.

    Args:
        db_path: Path to database file (default: market_data.db)
        pool_size: Number of connections in pool (default: 5)

    Returns:
        DatabasePool instance
    """
    global _default_pool

    # Resolve to absolute path
    if not os.path.isabs(db_path):
        # Check if we're in scripts directory
        current_dir = os.getcwd()
        if current_dir.endswith("scripts"):
            db_path = os.path.join(os.path.dirname(current_dir), db_path)
        else:
            db_path = os.path.join(current_dir, db_path)

    if _default_pool is None or _default_pool.db_path != db_path:
        _default_pool = DatabasePool(db_path, pool_size)

    return _default_pool


if __name__ == "__main__":
    """Test database pool functionality"""
    import time
    import threading

    # Create test database
    test_db = "test_pool.db"

    # Initialize pool
    pool = DatabasePool(test_db, pool_size=3)

    # Test table creation
    with pool.get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS test_data (
                id INTEGER PRIMARY KEY,
                value TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        print("✅ Test table created")

    # Test concurrent access
    def worker(worker_id, iterations=5):
        """Simulate concurrent database access"""
        for i in range(iterations):
            try:
                with pool.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO test_data (value) VALUES (?)",
                        (f"Worker {worker_id} - Iteration {i}",),
                    )
                    print(f"Worker {worker_id}: Inserted record {i}")
                    time.sleep(0.1)
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")

    # Run concurrent workers
    threads = []
    for i in range(5):  # 5 workers, 3 connections (should handle gracefully)
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    # Wait for completion
    for t in threads:
        t.join()

    # Verify results
    with pool.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_data")
        count = cursor.fetchone()[0]
        print(f"\n✅ Test complete: {count} records inserted")

    # Cleanup
    pool.close_all()
    os.remove(test_db)
    print("✅ Test database cleaned up")
