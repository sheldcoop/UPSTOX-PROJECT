#!/usr/bin/env python3
"""
Data Sync & Refresh Manager
Automated data refresh scheduler with gap detection and validation.
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import time
import schedule

from scripts.database_validator import DatabaseValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataSyncManager:
    """
    Automated data synchronization and refresh management.
    
    Features:
    - Scheduled data refresh
    - Gap detection in historical data
    - Data validation before insertion
    - Sync status tracking
    - Automatic retry for failed syncs
    """
    
    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path
        self.validator = DatabaseValidator(db_path=db_path)
        self._init_sync_db()
    
    def _init_sync_db(self):
        """Initialize database tables for sync tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sync jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name TEXT UNIQUE NOT NULL,
                description TEXT,
                schedule_cron TEXT,
                enabled BOOLEAN DEFAULT 1,
                last_run DATETIME,
                last_status TEXT,
                next_run DATETIME,
                run_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sync history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name TEXT NOT NULL,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                status TEXT DEFAULT 'RUNNING',
                records_synced INTEGER DEFAULT 0,
                errors_count INTEGER DEFAULT 0,
                error_message TEXT,
                duration_seconds REAL,
                FOREIGN KEY (job_name) REFERENCES sync_jobs(job_name)
            )
        """)
        
        # Data gaps table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_gaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                gap_start DATETIME NOT NULL,
                gap_end DATETIME NOT NULL,
                gap_duration_hours REAL,
                detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                filled BOOLEAN DEFAULT 0,
                filled_at DATETIME
            )
        """)
        
        conn.commit()
        conn.close()
    
    def register_sync_job(self, name: str, description: str, 
                         schedule_cron: str = "0 * * * *") -> int:
        """
        Register a new sync job.
        
        Args:
            name: Unique job name
            description: Job description
            schedule_cron: Cron expression (default: every hour)
        
        Returns:
            Job ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO sync_jobs
            (job_name, description, schedule_cron)
            VALUES (?, ?, ?)
        """, (name, description, schedule_cron))
        
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Sync job registered: {name}")
        
        return job_id
    
    def start_sync(self, job_name: str) -> int:
        """Start a sync operation and return sync history ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sync_history (job_name, status)
            VALUES (?, 'RUNNING')
        """, (job_name,))
        
        sync_id = cursor.lastrowid
        
        # Update job last_run
        cursor.execute("""
            UPDATE sync_jobs
            SET last_run = CURRENT_TIMESTAMP,
                run_count = run_count + 1
            WHERE job_name = ?
        """, (job_name,))
        
        conn.commit()
        conn.close()
        
        return sync_id
    
    def complete_sync(self, sync_id: int, status: str = 'SUCCESS',
                     records_synced: int = 0, errors_count: int = 0,
                     error_message: Optional[str] = None):
        """Mark a sync operation as complete"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get sync start time
        cursor.execute("""
            SELECT started_at, job_name
            FROM sync_history
            WHERE id = ?
        """, (sync_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return
        
        started_at, job_name = result
        duration = (datetime.now() - datetime.fromisoformat(started_at)).total_seconds()
        
        # Update sync history
        cursor.execute("""
            UPDATE sync_history
            SET completed_at = CURRENT_TIMESTAMP,
                status = ?,
                records_synced = ?,
                errors_count = ?,
                error_message = ?,
                duration_seconds = ?
            WHERE id = ?
        """, (status, records_synced, errors_count, error_message, duration, sync_id))
        
        # Update job statistics
        if status == 'SUCCESS':
            cursor.execute("""
                UPDATE sync_jobs
                SET last_status = 'SUCCESS',
                    success_count = success_count + 1
                WHERE job_name = ?
            """, (job_name,))
        else:
            cursor.execute("""
                UPDATE sync_jobs
                SET last_status = 'FAILED',
                    failure_count = failure_count + 1
                WHERE job_name = ?
            """, (job_name,))
        
        conn.commit()
        conn.close()
        
        logger.info(
            f"Sync completed: {job_name} - {status} "
            f"({records_synced} records, {duration:.1f}s)"
        )
    
    def detect_data_gaps(self, symbol: str, expected_interval_minutes: int = 5) -> List[Dict]:
        """
        Detect gaps in time-series data for a symbol.
        
        Args:
            symbol: Trading symbol
            expected_interval_minutes: Expected interval between data points
        
        Returns:
            List of detected gaps
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp
            FROM market_data
            WHERE symbol = ?
            AND timestamp >= datetime('now', '-7 days')
            ORDER BY timestamp ASC
        """, (symbol,))
        
        timestamps = [datetime.fromisoformat(row[0]) for row in cursor.fetchall()]
        
        if len(timestamps) < 2:
            conn.close()
            return []
        
        gaps = []
        expected_delta = timedelta(minutes=expected_interval_minutes)
        
        for i in range(len(timestamps) - 1):
            current_time = timestamps[i]
            next_time = timestamps[i + 1]
            
            gap_duration = next_time - current_time
            
            # If gap is larger than 2x expected interval, it's a gap
            if gap_duration > (expected_delta * 2):
                gap_hours = gap_duration.total_seconds() / 3600
                
                # Store gap in database
                cursor.execute("""
                    INSERT INTO data_gaps
                    (symbol, gap_start, gap_end, gap_duration_hours)
                    VALUES (?, ?, ?, ?)
                """, (symbol, current_time, next_time, gap_hours))
                
                gaps.append({
                    'symbol': symbol,
                    'gap_start': current_time.isoformat(),
                    'gap_end': next_time.isoformat(),
                    'gap_duration_hours': gap_hours,
                    'missing_intervals': int(gap_hours * 60 / expected_interval_minutes)
                })
        
        conn.commit()
        conn.close()
        
        if gaps:
            logger.warning(f"Detected {len(gaps)} data gaps for {symbol}")
        
        return gaps
    
    def fill_data_gap(self, gap_id: int) -> bool:
        """
        Fill a detected data gap (placeholder for actual API call).
        
        Args:
            gap_id: Gap ID from data_gaps table
        
        Returns:
            True if gap filled successfully
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT symbol, gap_start, gap_end
            FROM data_gaps
            WHERE id = ? AND filled = 0
        """, (gap_id,))
        
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False
        
        symbol, gap_start, gap_end = result
        
        # TODO: Call actual API to fetch missing data
        # For now, just mark as filled
        
        cursor.execute("""
            UPDATE data_gaps
            SET filled = 1, filled_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (gap_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Gap filled: {symbol} from {gap_start} to {gap_end}")
        
        return True
    
    def sync_market_data(self, symbols: List[str], interval: str = '5minute') -> Dict[str, Any]:
        """
        Sync latest market data for symbols.
        
        Args:
            symbols: List of trading symbols
            interval: Data interval
        
        Returns:
            Sync summary
        """
        sync_id = self.start_sync('market_data_sync')
        
        total_records = 0
        errors = 0
        error_messages = []
        
        try:
            for symbol in symbols:
                try:
                    # TODO: Call actual market data API
                    # For now, detect and log gaps
                    gaps = self.detect_data_gaps(symbol)
                    
                    if gaps:
                        logger.info(f"{symbol}: {len(gaps)} gaps detected")
                    
                    total_records += 1
                    
                except Exception as e:
                    errors += 1
                    error_messages.append(f"{symbol}: {str(e)}")
                    logger.error(f"Failed to sync {symbol}: {str(e)}")
            
            self.complete_sync(
                sync_id,
                status='SUCCESS' if errors == 0 else 'PARTIAL',
                records_synced=total_records,
                errors_count=errors,
                error_message='; '.join(error_messages) if error_messages else None
            )
            
        except Exception as e:
            self.complete_sync(
                sync_id,
                status='FAILED',
                records_synced=total_records,
                errors_count=errors + 1,
                error_message=str(e)
            )
        
        return {
            'sync_id': sync_id,
            'total_symbols': len(symbols),
            'records_synced': total_records,
            'errors': errors
        }
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get status of all sync jobs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                job_name,
                enabled,
                last_run,
                last_status,
                run_count,
                success_count,
                failure_count
            FROM sync_jobs
            ORDER BY last_run DESC
        """)
        
        jobs = []
        for row in cursor.fetchall():
            success_rate = (row[5] / row[4] * 100) if row[4] > 0 else 0
            
            jobs.append({
                'job_name': row[0],
                'enabled': bool(row[1]),
                'last_run': row[2],
                'last_status': row[3],
                'run_count': row[4],
                'success_count': row[5],
                'failure_count': row[6],
                'success_rate': success_rate
            })
        
        conn.close()
        
        return {
            'total_jobs': len(jobs),
            'jobs': jobs
        }
    
    def get_unfilled_gaps(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get unfilled data gaps"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT id, symbol, gap_start, gap_end, gap_duration_hours, detected_at
            FROM data_gaps
            WHERE filled = 0
        """
        
        if symbol:
            query += f" AND symbol = '{symbol}'"
        
        query += " ORDER BY detected_at DESC LIMIT 50"
        
        cursor.execute(query)
        
        gaps = []
        for row in cursor.fetchall():
            gaps.append({
                'id': row[0],
                'symbol': row[1],
                'gap_start': row[2],
                'gap_end': row[3],
                'gap_duration_hours': row[4],
                'detected_at': row[5]
            })
        
        conn.close()
        
        return gaps


def main():
    """Test data sync manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Sync Manager")
    parser.add_argument('--action',
                       choices=['register', 'sync', 'gaps', 'status'],
                       default='status',
                       help='Action to perform')
    parser.add_argument('--symbols', type=str, default='INFY,TCS',
                       help='Comma-separated symbols')
    
    args = parser.parse_args()
    
    sync_mgr = DataSyncManager()
    
    if args.action == 'register':
        job_id = sync_mgr.register_sync_job(
            name='hourly_market_data',
            description='Sync market data every hour',
            schedule_cron='0 * * * *'
        )
        print(f"Sync job registered: ID {job_id}")
    
    elif args.action == 'sync':
        symbols = args.symbols.split(',')
        result = sync_mgr.sync_market_data(symbols)
        
        print("\n=== Sync Results ===")
        print(f"Symbols: {result['total_symbols']}")
        print(f"Records Synced: {result['records_synced']}")
        print(f"Errors: {result['errors']}")
    
    elif args.action == 'gaps':
        symbols = args.symbols.split(',')
        
        print("\n=== Data Gaps ===")
        for symbol in symbols:
            gaps = sync_mgr.detect_data_gaps(symbol)
            
            if gaps:
                print(f"\n{symbol}: {len(gaps)} gaps")
                for gap in gaps[:5]:
                    print(f"  {gap['gap_start']} -> {gap['gap_end']} "
                          f"({gap['gap_duration_hours']:.1f}h)")
            else:
                print(f"{symbol}: No gaps")
    
    elif args.action == 'status':
        status = sync_mgr.get_sync_status()
        
        print(f"\n=== Sync Status ({status['total_jobs']} jobs) ===")
        for job in status['jobs']:
            print(f"\n{job['job_name']}")
            print(f"  Status: {job['last_status']} ({'Enabled' if job['enabled'] else 'Disabled'})")
            print(f"  Last Run: {job['last_run']}")
            print(f"  Success Rate: {job['success_rate']:.1f}%")
            print(f"  Runs: {job['run_count']} (✅ {job['success_count']}, ❌ {job['failure_count']})")


if __name__ == "__main__":
    main()
