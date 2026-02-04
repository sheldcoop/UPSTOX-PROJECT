"""Database Service - Centralized database operations with context manager"""

import sqlite3
from typing import Any, List, Dict, Optional, Tuple
from contextlib import contextmanager
import os


class DatabaseService:
    """
    Centralized database service with connection pooling and context managers.
    Prevents connection leaks and provides consistent DB access.
    """
    
    def __init__(self, db_path: str = "market_data.db"):
        """Initialize with database path"""
        # Force absolute path
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(db_path)
        self.db_path = db_path
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        Auto-commits on success, rolls back on error.
        
        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
        """
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def execute(self, query: str, params: Tuple = ()) -> List[Tuple]:
        """
        Execute query and return all results.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            List of result tuples
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_one(self, query: str, params: Tuple = ()) -> Optional[Tuple]:
        """Execute query and return first result"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """
        Execute query with multiple parameter sets.
        
        Returns:
            Number of rows affected
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        Insert data into table.
        
        Args:
            table: Table name
            data: Dict of column: value
            
        Returns:
            Last inserted row ID
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(data.values()))
            return cursor.lastrowid
    
    def update(self, table: str, data: Dict[str, Any], where: str, where_params: Tuple = ()) -> int:
        """
        Update table rows.
        
        Args:
            table: Table name
            data: Dict of column: value to update
            where: WHERE clause (without WHERE keyword)
            where_params: Parameters for WHERE clause
            
        Returns:
            Number of rows updated
        """
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        params = tuple(data.values()) + where_params
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount
    
    def delete(self, table: str, where: str, where_params: Tuple = ()) -> int:
        """Delete rows from table"""
        query = f"DELETE FROM {table} WHERE {where}"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, where_params)
            return cursor.rowcount
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.execute_one(query, (table_name,))
        return result is not None
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information"""
        query = f"PRAGMA table_info({table_name})"
        rows = self.execute(query)
        return [
            {
                "cid": row[0],
                "name": row[1],
                "type": row[2],
                "notnull": bool(row[3]),
                "default": row[4],
                "pk": bool(row[5])
            }
            for row in rows
        ]


# Singleton instance
db = DatabaseService()
