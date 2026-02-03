#!/usr/bin/env python3
"""
Centralized Logging and Monitoring System
Production-grade logging with rotation, system metrics, and monitoring.
"""

import logging
import logging.handlers
import os
import sys
import sqlite3
import psutil
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path


class SystemMetrics:
    """System resource metrics"""

    @staticmethod
    def get_cpu_usage() -> float:
        """Get current CPU usage percentage"""
        return psutil.cpu_percent(interval=1)

    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """Get memory usage statistics"""
        mem = psutil.virtual_memory()
        return {
            "total_mb": mem.total / (1024 * 1024),
            "available_mb": mem.available / (1024 * 1024),
            "used_mb": mem.used / (1024 * 1024),
            "percent": mem.percent,
        }

    @staticmethod
    def get_disk_usage() -> Dict[str, Any]:
        """Get disk usage statistics"""
        disk = psutil.disk_usage("/")
        return {
            "total_gb": disk.total / (1024 * 1024 * 1024),
            "used_gb": disk.used / (1024 * 1024 * 1024),
            "free_gb": disk.free / (1024 * 1024 * 1024),
            "percent": disk.percent,
        }

    @staticmethod
    def get_process_info() -> Dict[str, Any]:
        """Get current process information"""
        process = psutil.Process()

        return {
            "pid": process.pid,
            "cpu_percent": process.cpu_percent(interval=0.1),
            "memory_mb": process.memory_info().rss / (1024 * 1024),
            "threads": process.num_threads(),
            "status": process.status(),
        }


class DatabaseLogHandler(logging.Handler):
    """Custom log handler that writes to database"""

    def __init__(self, db_path: str = "market_data.db"):
        super().__init__()
        self.db_path = db_path
        self._init_log_table()

    def _init_log_table(self):
        """Initialize log table in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS application_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                level TEXT NOT NULL,
                logger_name TEXT,
                message TEXT,
                module TEXT,
                function TEXT,
                line_number INTEGER,
                exception TEXT,
                extra_data TEXT
            )
        """
        )

        # Create index for faster queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_logs_timestamp
            ON application_logs(timestamp)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_logs_level
            ON application_logs(level)
        """
        )

        conn.commit()
        conn.close()

    def emit(self, record: logging.LogRecord):
        """Emit a log record to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Extract exception info if present
            exception_text = None
            if record.exc_info:
                exception_text = self.format(record)

            cursor.execute(
                """
                INSERT INTO application_logs
                (level, logger_name, message, module, function, line_number, exception)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    record.levelname,
                    record.name,
                    record.getMessage(),
                    record.module,
                    record.funcName,
                    record.lineno,
                    exception_text,
                ),
            )

            conn.commit()
            conn.close()

        except Exception:
            self.handleError(record)


class LoggerConfig:
    """
    Centralized logging configuration and monitoring.

    Features:
    - Multiple log handlers (console, file, database)
    - Automatic log rotation
    - System metrics tracking
    - Log level filtering
    - Performance monitoring
    """

    def __init__(
        self,
        app_name: str = "upstox_trading",
        log_dir: str = "logs",
        db_path: str = "market_data.db",
        console_level: str = "INFO",
        file_level: str = "DEBUG",
        db_level: str = "WARNING",
    ):
        self.app_name = app_name
        self.log_dir = Path(log_dir)
        self.db_path = db_path
        self.console_level = getattr(logging, console_level)
        self.file_level = getattr(logging, file_level)
        self.db_level = getattr(logging, db_level)

        # Create log directory
        self.log_dir.mkdir(exist_ok=True)

        # Initialize loggers
        self.logger = self._setup_logger()
        self._init_metrics_db()

    def _setup_logger(self) -> logging.Logger:
        """Setup and configure logger with multiple handlers"""
        logger = logging.getLogger(self.app_name)
        logger.setLevel(logging.DEBUG)  # Capture all levels

        # Remove existing handlers
        logger.handlers = []

        # Console handler (colored output)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.console_level)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler with rotation (10MB max, keep 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.app_name}.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        file_handler.setLevel(self.file_level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Error file handler (only errors and critical)
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.app_name}_errors.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=3,
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)

        # Database handler for warnings and above
        db_handler = DatabaseLogHandler(self.db_path)
        db_handler.setLevel(self.db_level)
        db_handler.setFormatter(file_formatter)
        logger.addHandler(db_handler)

        return logger

    def _init_metrics_db(self):
        """Initialize metrics tracking table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_percent REAL,
                memory_used_mb REAL,
                memory_percent REAL,
                disk_used_gb REAL,
                disk_percent REAL,
                process_cpu_percent REAL,
                process_memory_mb REAL,
                process_threads INTEGER
            )
        """
        )

        conn.commit()
        conn.close()

    def get_logger(self) -> logging.Logger:
        """Get configured logger instance"""
        return self.logger

    def log_metrics(self):
        """Log current system metrics to database"""
        metrics = SystemMetrics()
        cpu = metrics.get_cpu_usage()
        memory = metrics.get_memory_usage()
        disk = metrics.get_disk_usage()
        process = metrics.get_process_info()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO system_metrics
            (cpu_percent, memory_used_mb, memory_percent, disk_used_gb, 
             disk_percent, process_cpu_percent, process_memory_mb, process_threads)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                cpu,
                memory["used_mb"],
                memory["percent"],
                disk["used_gb"],
                disk["percent"],
                process["cpu_percent"],
                process["memory_mb"],
                process["threads"],
            ),
        )

        conn.commit()
        conn.close()

        self.logger.debug(
            f"Metrics logged: CPU={cpu:.1f}%, Memory={memory['percent']:.1f}%, "
            f"Process Memory={process['memory_mb']:.1f}MB"
        )

    def get_recent_logs(self, level: Optional[str] = None, limit: int = 100) -> list:
        """Get recent logs from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT timestamp, level, logger_name, message FROM application_logs"

        if level:
            query += f" WHERE level = '{level}'"

        query += " ORDER BY timestamp DESC LIMIT ?"

        cursor.execute(query, (limit,))

        logs = []
        for row in cursor.fetchall():
            logs.append(
                {
                    "timestamp": row[0],
                    "level": row[1],
                    "logger": row[2],
                    "message": row[3],
                }
            )

        conn.close()

        return logs

    def get_log_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get log statistics for the specified time period"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total logs by level
        cursor.execute(
            """
            SELECT level, COUNT(*) as count
            FROM application_logs
            WHERE timestamp >= datetime('now', '-{} hours')
            GROUP BY level
        """.format(
                hours
            )
        )

        logs_by_level = dict(cursor.fetchall())

        # Total logs
        total_logs = sum(logs_by_level.values())

        # Error rate
        errors = logs_by_level.get("ERROR", 0) + logs_by_level.get("CRITICAL", 0)
        error_rate = (errors / total_logs * 100) if total_logs > 0 else 0

        # Top logging modules
        cursor.execute(
            """
            SELECT module, COUNT(*) as count
            FROM application_logs
            WHERE timestamp >= datetime('now', '-{} hours')
            GROUP BY module
            ORDER BY count DESC
            LIMIT 10
        """.format(
                hours
            )
        )

        top_modules = dict(cursor.fetchall())

        conn.close()

        return {
            "total_logs": total_logs,
            "logs_by_level": logs_by_level,
            "error_rate": error_rate,
            "top_modules": top_modules,
            "period_hours": hours,
        }

    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get system metrics summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                AVG(cpu_percent) as avg_cpu,
                MAX(cpu_percent) as max_cpu,
                AVG(memory_percent) as avg_memory,
                MAX(memory_percent) as max_memory,
                AVG(process_memory_mb) as avg_process_mem,
                MAX(process_memory_mb) as max_process_mem
            FROM system_metrics
            WHERE timestamp >= datetime('now', '-{} hours')
        """.format(
                hours
            )
        )

        result = cursor.fetchone()
        conn.close()

        if not result or result[0] is None:
            return {"message": "No metrics data available", "period_hours": hours}

        return {
            "period_hours": hours,
            "cpu": {"average": result[0], "max": result[1]},
            "memory": {"average_percent": result[2], "max_percent": result[3]},
            "process_memory": {"average_mb": result[4], "max_mb": result[5]},
        }

    def cleanup_old_logs(self, days: int = 30):
        """Delete logs older than specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Delete old application logs
        cursor.execute(
            """
            DELETE FROM application_logs
            WHERE timestamp < datetime('now', '-{} days')
        """.format(
                days
            )
        )

        app_logs_deleted = cursor.rowcount

        # Delete old metrics
        cursor.execute(
            """
            DELETE FROM system_metrics
            WHERE timestamp < datetime('now', '-{} days')
        """.format(
                days
            )
        )

        metrics_deleted = cursor.rowcount

        conn.commit()
        conn.close()

        self.logger.info(
            f"Cleanup complete: {app_logs_deleted} logs, {metrics_deleted} metrics deleted"
        )

        return {"logs_deleted": app_logs_deleted, "metrics_deleted": metrics_deleted}


# Global logger instance
_global_logger_config: Optional[LoggerConfig] = None


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.

    Usage:
        from scripts.logger_config import get_logger
        logger = get_logger(__name__)
        logger.info("Application started")
    """
    global _global_logger_config

    if _global_logger_config is None:
        _global_logger_config = LoggerConfig()

    if name:
        return logging.getLogger(name)
    else:
        return _global_logger_config.get_logger()


def main():
    """Test logging system"""
    import argparse
    import time

    parser = argparse.ArgumentParser(description="Logging & Monitoring")
    parser.add_argument(
        "--action",
        choices=["test", "stats", "metrics", "cleanup", "monitor"],
        default="stats",
        help="Action to perform",
    )
    parser.add_argument("--hours", type=int, default=24, help="Hours to look back")

    args = parser.parse_args()

    logger_config = LoggerConfig()
    logger = logger_config.get_logger()

    if args.action == "test":
        print("\n=== Testing Logging System ===")

        logger.debug("This is a DEBUG message")
        logger.info("This is an INFO message")
        logger.warning("This is a WARNING message")
        logger.error("This is an ERROR message")

        try:
            raise ValueError("Test exception")
        except Exception as e:
            logger.exception("Exception occurred during test")

        print("Test logs created. Check logs/ directory and database.")

    elif args.action == "stats":
        stats = logger_config.get_log_statistics(hours=args.hours)

        print(f"\n=== Log Statistics ({stats['period_hours']}h) ===")
        print(f"Total Logs: {stats['total_logs']}")
        print(f"Error Rate: {stats['error_rate']:.2f}%")

        print("\nLogs by Level:")
        for level, count in stats["logs_by_level"].items():
            print(f"  {level}: {count}")

        print("\nTop Modules:")
        for module, count in stats["top_modules"].items():
            print(f"  {module}: {count}")

    elif args.action == "metrics":
        # Log current metrics
        logger_config.log_metrics()

        # Get summary
        summary = logger_config.get_metrics_summary(hours=args.hours)

        print(f"\n=== System Metrics ({summary['period_hours']}h) ===")

        if "message" in summary:
            print(summary["message"])
        else:
            print(f"\nCPU:")
            print(f"  Average: {summary['cpu']['average']:.1f}%")
            print(f"  Max: {summary['cpu']['max']:.1f}%")

            print(f"\nMemory:")
            print(f"  Average: {summary['memory']['average_percent']:.1f}%")
            print(f"  Max: {summary['memory']['max_percent']:.1f}%")

            print(f"\nProcess Memory:")
            print(f"  Average: {summary['process_memory']['average_mb']:.1f} MB")
            print(f"  Max: {summary['process_memory']['max_mb']:.1f} MB")

    elif args.action == "cleanup":
        result = logger_config.cleanup_old_logs(days=30)

        print("\n=== Cleanup Results ===")
        print(f"Logs Deleted: {result['logs_deleted']}")
        print(f"Metrics Deleted: {result['metrics_deleted']}")

    elif args.action == "monitor":
        print("\n=== Real-time Monitoring (Ctrl+C to stop) ===")

        try:
            while True:
                logger_config.log_metrics()

                metrics = SystemMetrics()
                cpu = metrics.get_cpu_usage()
                memory = metrics.get_memory_usage()
                process = metrics.get_process_info()

                print(
                    f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                    f"CPU: {cpu:.1f}% | "
                    f"Memory: {memory['percent']:.1f}% | "
                    f"Process: {process['memory_mb']:.1f}MB",
                    end="",
                    flush=True,
                )

                time.sleep(5)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")


if __name__ == "__main__":
    main()
