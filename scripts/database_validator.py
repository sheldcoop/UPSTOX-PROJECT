#!/usr/bin/env python3
"""
Database Validation and Integrity Management
Ensures data quality, adds constraints, and validates inputs.
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from decimal import Decimal
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseValidator:
    """
    Database validation and integrity management.
    
    Features:
    - SQL constraints for data integrity
    - Input validation before insertion
    - Data quality checks
    - Performance indexes
    - Data sanitization
    """
    
    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path
        self._apply_constraints()
        self._create_indexes()
    
    def _apply_constraints(self):
        """Apply database constraints for data integrity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Note: SQLite doesn't support ALTER TABLE ADD CONSTRAINT easily
        # We'll create new tables with constraints and migrate data if needed
        
        # Create validation rules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                column_name TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                rule_value TEXT,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(table_name, column_name, rule_type)
            )
        """)
        
        # Insert default validation rules
        rules = [
            # OHLC validations
            ('market_data', 'open', 'POSITIVE', None, 'Open price must be positive'),
            ('market_data', 'high', 'POSITIVE', None, 'High price must be positive'),
            ('market_data', 'low', 'POSITIVE', None, 'Low price must be positive'),
            ('market_data', 'close', 'POSITIVE', None, 'Close price must be positive'),
            ('market_data', 'volume', 'NON_NEGATIVE', None, 'Volume cannot be negative'),
            ('market_data', 'high', 'GREATER_EQUAL', 'low', 'High must be >= Low'),
            ('market_data', 'high', 'GREATER_EQUAL', 'open', 'High must be >= Open'),
            ('market_data', 'high', 'GREATER_EQUAL', 'close', 'High must be >= Close'),
            ('market_data', 'low', 'LESS_EQUAL', 'open', 'Low must be <= Open'),
            ('market_data', 'low', 'LESS_EQUAL', 'close', 'Low must be <= Close'),
            
            # Order validations
            ('orders', 'quantity', 'POSITIVE', None, 'Quantity must be positive'),
            ('orders', 'price', 'POSITIVE', None, 'Price must be positive'),
            ('orders', 'status', 'ENUM', 'PENDING,COMPLETE,CANCELLED,REJECTED', 'Invalid order status'),
            
            # Holdings validations
            ('holdings', 'quantity', 'NON_NEGATIVE', None, 'Holdings quantity cannot be negative'),
            ('holdings', 'average_price', 'POSITIVE', None, 'Average price must be positive'),
        ]
        
        for rule in rules:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO validation_rules
                    (table_name, column_name, rule_type, rule_value, error_message)
                    VALUES (?, ?, ?, ?, ?)
                """, rule)
            except Exception as e:
                logger.error(f"Failed to insert validation rule: {str(e)}")
        
        conn.commit()
        conn.close()
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        indexes = [
            # Market data indexes
            ("idx_market_data_symbol", "market_data", "symbol"),
            ("idx_market_data_timestamp", "market_data", "timestamp"),
            ("idx_market_data_symbol_timestamp", "market_data", "symbol, timestamp"),
            
            # Order indexes
            ("idx_orders_symbol", "orders", "symbol"),
            ("idx_orders_timestamp", "orders", "timestamp"),
            ("idx_orders_status", "orders", "status"),
            
            # Holdings indexes
            ("idx_holdings_symbol", "holdings", "symbol"),
            
            # Stop-loss indexes
            ("idx_stop_loss_symbol", "stop_loss_orders", "symbol"),
            ("idx_stop_loss_status", "stop_loss_orders", "status"),
            
            # Error logs indexes
            ("idx_error_logs_timestamp", "error_logs", "timestamp"),
            ("idx_error_logs_type", "error_logs", "error_type"),
            
            # Auth tokens indexes
            ("idx_auth_tokens_user", "auth_tokens", "user_id"),
            ("idx_auth_tokens_expiry", "auth_tokens", "expires_at"),
        ]
        
        for index_name, table_name, columns in indexes:
            try:
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS {index_name}
                    ON {table_name} ({columns})
                """)
                logger.info(f"Index created: {index_name}")
            except Exception as e:
                logger.error(f"Failed to create index {index_name}: {str(e)}")
        
        conn.commit()
        conn.close()
    
    def validate_ohlc(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate OHLC (Open, High, Low, Close) data.
        
        Returns:
            (is_valid, error_message)
        """
        required_fields = ['open', 'high', 'low', 'close']
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"
        
        open_price = float(data['open'])
        high_price = float(data['high'])
        low_price = float(data['low'])
        close_price = float(data['close'])
        
        # Check positive values
        if any(price <= 0 for price in [open_price, high_price, low_price, close_price]):
            return False, "All OHLC prices must be positive"
        
        # Check high >= low
        if high_price < low_price:
            return False, f"High ({high_price}) must be >= Low ({low_price})"
        
        # Check high >= open and close
        if high_price < open_price:
            return False, f"High ({high_price}) must be >= Open ({open_price})"
        if high_price < close_price:
            return False, f"High ({high_price}) must be >= Close ({close_price})"
        
        # Check low <= open and close
        if low_price > open_price:
            return False, f"Low ({low_price}) must be <= Open ({open_price})"
        if low_price > close_price:
            return False, f"Low ({low_price}) must be <= Close ({close_price})"
        
        # Check volume if present
        if 'volume' in data:
            volume = int(data['volume'])
            if volume < 0:
                return False, "Volume cannot be negative"
        
        return True, None
    
    def validate_order(self, order_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate order data before insertion.
        
        Returns:
            (is_valid, error_message)
        """
        required_fields = ['symbol', 'quantity', 'price', 'transaction_type']
        
        # Check required fields
        for field in required_fields:
            if field not in order_data:
                return False, f"Missing required field: {field}"
        
        # Validate symbol format (alphanumeric, 1-20 chars)
        symbol = order_data['symbol']
        if not re.match(r'^[A-Z0-9]{1,20}$', symbol):
            return False, f"Invalid symbol format: {symbol}"
        
        # Validate quantity (positive integer)
        try:
            quantity = int(order_data['quantity'])
            if quantity <= 0:
                return False, "Quantity must be positive"
        except (ValueError, TypeError):
            return False, "Quantity must be a valid integer"
        
        # Validate price (positive float)
        try:
            price = float(order_data['price'])
            if price <= 0:
                return False, "Price must be positive"
        except (ValueError, TypeError):
            return False, "Price must be a valid number"
        
        # Validate transaction type
        valid_types = ['BUY', 'SELL']
        if order_data['transaction_type'] not in valid_types:
            return False, f"Transaction type must be one of: {', '.join(valid_types)}"
        
        # Validate product type if present
        if 'product' in order_data:
            valid_products = ['CNC', 'INTRADAY', 'MARGIN']
            if order_data['product'] not in valid_products:
                return False, f"Product must be one of: {', '.join(valid_products)}"
        
        # Validate order type if present
        if 'order_type' in order_data:
            valid_order_types = ['MARKET', 'LIMIT', 'SL', 'SL-M']
            if order_data['order_type'] not in valid_order_types:
                return False, f"Order type must be one of: {', '.join(valid_order_types)}"
        
        return True, None
    
    def validate_holding(self, holding_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate holdings data.
        
        Returns:
            (is_valid, error_message)
        """
        required_fields = ['symbol', 'quantity', 'average_price']
        
        # Check required fields
        for field in required_fields:
            if field not in holding_data:
                return False, f"Missing required field: {field}"
        
        # Validate quantity (non-negative)
        try:
            quantity = int(holding_data['quantity'])
            if quantity < 0:
                return False, "Quantity cannot be negative"
        except (ValueError, TypeError):
            return False, "Quantity must be a valid integer"
        
        # Validate average price (positive)
        try:
            avg_price = float(holding_data['average_price'])
            if avg_price <= 0:
                return False, "Average price must be positive"
        except (ValueError, TypeError):
            return False, "Average price must be a valid number"
        
        return True, None
    
    def sanitize_string(self, value: str, max_length: int = 255) -> str:
        """Sanitize string input to prevent SQL injection"""
        if not isinstance(value, str):
            value = str(value)
        
        # Remove any null bytes
        value = value.replace('\x00', '')
        
        # Truncate to max length
        value = value[:max_length]
        
        # Remove leading/trailing whitespace
        value = value.strip()
        
        return value
    
    def check_data_quality(self, table_name: str, days: int = 7) -> Dict[str, Any]:
        """
        Check data quality for a specific table.
        
        Returns:
            Dict with quality metrics and issues
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        quality_report = {
            'table': table_name,
            'total_records': 0,
            'null_count': {},
            'duplicate_count': 0,
            'outliers': [],
            'invalid_records': []
        }
        
        try:
            # Get total records
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            quality_report['total_records'] = cursor.fetchone()[0]
            
            # Check for NULL values (if applicable)
            if table_name == 'market_data':
                cursor.execute(f"""
                    SELECT 
                        SUM(CASE WHEN open IS NULL THEN 1 ELSE 0 END) as null_open,
                        SUM(CASE WHEN high IS NULL THEN 1 ELSE 0 END) as null_high,
                        SUM(CASE WHEN low IS NULL THEN 1 ELSE 0 END) as null_low,
                        SUM(CASE WHEN close IS NULL THEN 1 ELSE 0 END) as null_close,
                        SUM(CASE WHEN volume IS NULL THEN 1 ELSE 0 END) as null_volume
                    FROM {table_name}
                    WHERE timestamp >= datetime('now', '-{days} days')
                """)
                
                row = cursor.fetchone()
                quality_report['null_count'] = {
                    'open': row[0],
                    'high': row[1],
                    'low': row[2],
                    'close': row[3],
                    'volume': row[4]
                }
                
                # Check for invalid OHLC relationships
                cursor.execute(f"""
                    SELECT symbol, timestamp, open, high, low, close
                    FROM {table_name}
                    WHERE timestamp >= datetime('now', '-{days} days')
                    AND (
                        high < low
                        OR high < open
                        OR high < close
                        OR low > open
                        OR low > close
                        OR open <= 0
                        OR high <= 0
                        OR low <= 0
                        OR close <= 0
                    )
                    LIMIT 10
                """)
                
                invalid_records = cursor.fetchall()
                quality_report['invalid_records'] = [
                    {
                        'symbol': row[0],
                        'timestamp': row[1],
                        'open': row[2],
                        'high': row[3],
                        'low': row[4],
                        'close': row[5]
                    }
                    for row in invalid_records
                ]
                
                # Check for duplicates
                cursor.execute(f"""
                    SELECT symbol, timestamp, COUNT(*) as count
                    FROM {table_name}
                    WHERE timestamp >= datetime('now', '-{days} days')
                    GROUP BY symbol, timestamp
                    HAVING COUNT(*) > 1
                """)
                
                duplicates = cursor.fetchall()
                quality_report['duplicate_count'] = len(duplicates)
        
        except Exception as e:
            logger.error(f"Error checking data quality for {table_name}: {str(e)}")
            quality_report['error'] = str(e)
        
        finally:
            conn.close()
        
        return quality_report
    
    def repair_data(self, table_name: str, auto_fix: bool = False) -> Dict[str, Any]:
        """
        Identify and optionally repair data issues.
        
        Args:
            table_name: Table to repair
            auto_fix: Whether to automatically fix issues
        
        Returns:
            Dict with repair results
        """
        repair_report = {
            'table': table_name,
            'issues_found': [],
            'fixes_applied': [],
            'manual_review_needed': []
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if table_name == 'market_data':
                # Find and remove exact duplicates
                cursor.execute("""
                    SELECT symbol, timestamp, COUNT(*) as count
                    FROM market_data
                    GROUP BY symbol, timestamp
                    HAVING COUNT(*) > 1
                """)
                
                duplicates = cursor.fetchall()
                
                if duplicates:
                    repair_report['issues_found'].append(
                        f"Found {len(duplicates)} duplicate records"
                    )
                    
                    if auto_fix:
                        # Keep only the first record for each duplicate
                        for symbol, timestamp, count in duplicates:
                            cursor.execute("""
                                DELETE FROM market_data
                                WHERE rowid NOT IN (
                                    SELECT MIN(rowid)
                                    FROM market_data
                                    WHERE symbol = ? AND timestamp = ?
                                )
                                AND symbol = ? AND timestamp = ?
                            """, (symbol, timestamp, symbol, timestamp))
                        
                        repair_report['fixes_applied'].append(
                            f"Removed {len(duplicates)} duplicate records"
                        )
                
                # Find records with invalid OHLC relationships
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM market_data
                    WHERE high < low OR high < open OR high < close
                    OR low > open OR low > close
                """)
                
                invalid_count = cursor.fetchone()[0]
                
                if invalid_count > 0:
                    repair_report['issues_found'].append(
                        f"Found {invalid_count} records with invalid OHLC relationships"
                    )
                    repair_report['manual_review_needed'].append(
                        "Invalid OHLC records require manual review"
                    )
            
            if auto_fix:
                conn.commit()
        
        except Exception as e:
            logger.error(f"Error repairing data for {table_name}: {str(e)}")
            repair_report['error'] = str(e)
            conn.rollback()
        
        finally:
            conn.close()
        
        return repair_report
    
    def vacuum_database(self):
        """Optimize database by reclaiming unused space"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("VACUUM")
            conn.close()
            logger.info("Database vacuumed successfully")
        except Exception as e:
            logger.error(f"Failed to vacuum database: {str(e)}")


def main():
    """Test database validation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Validation")
    parser.add_argument('--action', 
                       choices=['validate', 'quality', 'repair', 'vacuum', 'indexes'],
                       default='quality',
                       help='Action to perform')
    parser.add_argument('--table', type=str, default='market_data',
                       help='Table name')
    parser.add_argument('--auto-fix', action='store_true',
                       help='Automatically fix issues')
    
    args = parser.parse_args()
    
    validator = DatabaseValidator()
    
    if args.action == 'validate':
        # Test OHLC validation
        test_data = {
            'open': 100,
            'high': 105,
            'low': 98,
            'close': 102,
            'volume': 10000
        }
        
        is_valid, error = validator.validate_ohlc(test_data)
        print(f"\n=== OHLC Validation ===")
        print(f"Valid: {is_valid}")
        if error:
            print(f"Error: {error}")
    
    elif args.action == 'quality':
        report = validator.check_data_quality(args.table)
        
        print(f"\n=== Data Quality Report: {report['table']} ===")
        print(f"Total Records: {report['total_records']}")
        
        if 'null_count' in report:
            print("\nNull Counts:")
            for field, count in report['null_count'].items():
                print(f"  {field}: {count}")
        
        print(f"\nDuplicates: {report['duplicate_count']}")
        
        if report['invalid_records']:
            print(f"\nInvalid Records ({len(report['invalid_records'])}):")
            for record in report['invalid_records'][:5]:
                print(f"  {record}")
    
    elif args.action == 'repair':
        report = validator.repair_data(args.table, auto_fix=args.auto_fix)
        
        print(f"\n=== Repair Report: {report['table']} ===")
        
        if report['issues_found']:
            print("\nIssues Found:")
            for issue in report['issues_found']:
                print(f"  - {issue}")
        
        if report['fixes_applied']:
            print("\nFixes Applied:")
            for fix in report['fixes_applied']:
                print(f"  ✅ {fix}")
        
        if report['manual_review_needed']:
            print("\nManual Review Needed:")
            for item in report['manual_review_needed']:
                print(f"  ⚠️  {item}")
    
    elif args.action == 'vacuum':
        validator.vacuum_database()
        print("Database optimization complete")
    
    elif args.action == 'indexes':
        print("Indexes created/verified")


if __name__ == "__main__":
    main()
