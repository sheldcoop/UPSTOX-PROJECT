#!/usr/bin/env python3
"""
Error Handler and Retry Logic for Upstox API
Provides robust error handling with exponential backoff, rate limiting, and graceful degradation.
"""

import time
import logging
import functools
from typing import Callable, Any, Optional, Dict, List
from datetime import datetime, timedelta
import sqlite3
import json

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)
import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError, RequestException

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UpstoxAPIError(Exception):
    """Base exception for Upstox API errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class RateLimitError(UpstoxAPIError):
    """Raised when API rate limit is exceeded"""

    pass


class AuthenticationError(UpstoxAPIError):
    """Raised when authentication fails"""

    pass


class NetworkError(UpstoxAPIError):
    """Raised when network connectivity issues occur"""

    pass


class ValidationError(UpstoxAPIError):
    """Raised when input validation fails"""

    pass


class ErrorHandler:
    """
    Centralized error handling and retry logic for Upstox API calls.

    Features:
    - Exponential backoff with jitter
    - Rate limit detection and handling
    - Network error recovery
    - Error logging and tracking
    - Graceful degradation with cached data
    """

    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path
        self.error_cache: Dict[str, List[Dict]] = {}
        self.rate_limit_reset_time: Optional[datetime] = None
        self._init_error_tracking_db()

    def _init_error_tracking_db(self):
        """Initialize database table for error tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                error_type TEXT NOT NULL,
                error_message TEXT,
                status_code INTEGER,
                endpoint TEXT,
                retry_count INTEGER DEFAULT 0,
                resolved BOOLEAN DEFAULT 0,
                resolution_time DATETIME,
                context TEXT
            )
        """
        )

        conn.commit()
        conn.close()

    def log_error(
        self,
        error_type: str,
        error_message: str,
        status_code: Optional[int] = None,
        endpoint: Optional[str] = None,
        retry_count: int = 0,
        context: Optional[Dict] = None,
    ):
        """Log error to database for tracking and analysis"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO error_logs 
                (error_type, error_message, status_code, endpoint, retry_count, context)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    error_type,
                    error_message,
                    status_code,
                    endpoint,
                    retry_count,
                    json.dumps(context) if context else None,
                ),
            )

            conn.commit()
            conn.close()

            logger.error(
                f"{error_type}: {error_message} (Status: {status_code}, Endpoint: {endpoint})"
            )

        except Exception as e:
            logger.error(f"Failed to log error to database: {str(e)}")

    def mark_error_resolved(self, error_id: int):
        """Mark an error as resolved in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE error_logs 
                SET resolved = 1, resolution_time = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (error_id,),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to mark error as resolved: {str(e)}")

    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for the specified time period"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Total errors in time period
            cursor.execute(
                """
                SELECT COUNT(*) FROM error_logs
                WHERE timestamp >= datetime('now', '-{} hours')
            """.format(
                    hours
                )
            )
            total_errors = cursor.fetchone()[0]

            # Errors by type
            cursor.execute(
                """
                SELECT error_type, COUNT(*) as count
                FROM error_logs
                WHERE timestamp >= datetime('now', '-{} hours')
                GROUP BY error_type
                ORDER BY count DESC
            """.format(
                    hours
                )
            )
            errors_by_type = dict(cursor.fetchall())

            # Errors by endpoint
            cursor.execute(
                """
                SELECT endpoint, COUNT(*) as count
                FROM error_logs
                WHERE timestamp >= datetime('now', '-{} hours')
                AND endpoint IS NOT NULL
                GROUP BY endpoint
                ORDER BY count DESC
                LIMIT 10
            """.format(
                    hours
                )
            )
            errors_by_endpoint = dict(cursor.fetchall())

            # Resolution rate
            cursor.execute(
                """
                SELECT 
                    COUNT(CASE WHEN resolved = 1 THEN 1 END) as resolved,
                    COUNT(*) as total
                FROM error_logs
                WHERE timestamp >= datetime('now', '-{} hours')
            """.format(
                    hours
                )
            )
            resolved, total = cursor.fetchone()
            resolution_rate = (resolved / total * 100) if total > 0 else 0

            conn.close()

            return {
                "total_errors": total_errors,
                "errors_by_type": errors_by_type,
                "errors_by_endpoint": errors_by_endpoint,
                "resolution_rate": resolution_rate,
                "time_period_hours": hours,
            }

        except Exception as e:
            logger.error(f"Failed to get error statistics: {str(e)}")
            return {}

    def handle_http_error(self, response: requests.Response, endpoint: str) -> None:
        """Handle HTTP errors from API responses"""
        status_code = response.status_code

        try:
            error_data = response.json()
        except ValueError:
            error_data = {"message": response.text}

        error_message = error_data.get("message", "Unknown error")

        # Log the error
        self.log_error(
            error_type=f"HTTP_{status_code}",
            error_message=error_message,
            status_code=status_code,
            endpoint=endpoint,
            context=error_data,
        )

        # Handle specific status codes
        if status_code == 401:
            raise AuthenticationError(
                "Authentication failed. Token may be expired.",
                status_code=status_code,
                response_data=error_data,
            )

        elif status_code == 429:
            # Rate limit exceeded
            retry_after = response.headers.get("Retry-After", 60)
            try:
                retry_after = int(retry_after)
            except ValueError:
                retry_after = 60

            self.rate_limit_reset_time = datetime.now() + timedelta(seconds=retry_after)

            raise RateLimitError(
                f"Rate limit exceeded. Retry after {retry_after} seconds.",
                status_code=status_code,
                response_data=error_data,
            )

        elif status_code >= 500:
            # Server error - likely temporary
            raise UpstoxAPIError(
                f"Server error: {error_message}",
                status_code=status_code,
                response_data=error_data,
            )

        elif status_code >= 400:
            # Client error
            raise ValidationError(
                f"Request validation error: {error_message}",
                status_code=status_code,
                response_data=error_data,
            )

        else:
            raise UpstoxAPIError(
                f"Unexpected error: {error_message}",
                status_code=status_code,
                response_data=error_data,
            )

    def should_retry(self, exception: Exception) -> bool:
        """Determine if a request should be retried based on the exception"""
        # Always retry network errors
        if isinstance(exception, (Timeout, ConnectionError)):
            return True

        # Retry rate limit errors (after waiting)
        if isinstance(exception, RateLimitError):
            return True

        # Retry server errors (5xx)
        if isinstance(exception, UpstoxAPIError) and exception.status_code >= 500:
            return True

        # Don't retry authentication or validation errors
        if isinstance(exception, (AuthenticationError, ValidationError)):
            return False

        return False

    def get_cached_data(self, cache_key: str) -> Optional[Any]:
        """
        Retrieve cached data for graceful degradation.
        Returns None if no cached data is available.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Try to get recent cached data (within last hour)
            cursor.execute(
                """
                SELECT data FROM api_cache
                WHERE cache_key = ?
                AND timestamp >= datetime('now', '-1 hour')
                ORDER BY timestamp DESC
                LIMIT 1
            """,
                (cache_key,),
            )

            result = cursor.fetchone()
            conn.close()

            if result:
                logger.info(f"Using cached data for: {cache_key}")
                return json.loads(result[0])

        except Exception as e:
            logger.error(f"Failed to retrieve cached data: {str(e)}")

        return None

    def cache_data(self, cache_key: str, data: Any):
        """Cache successful API responses for graceful degradation"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create cache table if it doesn't exist
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS api_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT NOT NULL,
                    data TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Insert cached data
            cursor.execute(
                """
                INSERT INTO api_cache (cache_key, data)
                VALUES (?, ?)
            """,
                (cache_key, json.dumps(data)),
            )

            # Clean old cache entries (older than 24 hours)
            cursor.execute(
                """
                DELETE FROM api_cache
                WHERE timestamp < datetime('now', '-24 hours')
            """
            )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to cache data: {str(e)}")

    def get_error_rate(self, minutes: int = 5) -> float:
        """
        Calculate error rate per minute for the specified time period.

        Args:
            minutes: Time window to calculate error rate (default: 5)

        Returns:
            float: Errors per minute
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT COUNT(*) FROM error_logs
                WHERE timestamp >= datetime('now', '-{} minutes')
            """.format(
                    minutes
                )
            )

            error_count = cursor.fetchone()[0]
            conn.close()

            return error_count / minutes if minutes > 0 else 0

        except Exception as e:
            logger.error(f"Failed to calculate error rate: {str(e)}")
            return 0.0

    def check_error_threshold(
        self, threshold: float = 10.0, window_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        Check if error rate exceeds threshold and return alert info.

        Args:
            threshold: Error rate threshold (errors per minute)
            window_minutes: Time window to check (default: 5 minutes)

        Returns:
            dict: Alert information with 'alert', 'rate', 'threshold', 'message'
        """
        error_rate = self.get_error_rate(window_minutes)

        alert_info = {
            "alert": error_rate > threshold,
            "rate": error_rate,
            "threshold": threshold,
            "window_minutes": window_minutes,
            "timestamp": datetime.now().isoformat(),
        }

        if alert_info["alert"]:
            alert_info["message"] = (
                f"⚠️  HIGH ERROR RATE ALERT: {error_rate:.2f} errors/min "
                f"(threshold: {threshold}/min over {window_minutes}m window)"
            )
            logger.warning(alert_info["message"])

            # Get recent error breakdown
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT error_type, COUNT(*) as count
                    FROM error_logs
                    WHERE timestamp >= datetime('now', '-{} minutes')
                    GROUP BY error_type
                    ORDER BY count DESC
                    LIMIT 5
                """.format(
                        window_minutes
                    )
                )

                error_breakdown = dict(cursor.fetchall())
                alert_info["error_breakdown"] = error_breakdown
                conn.close()

            except Exception as e:
                logger.error(f"Failed to get error breakdown: {str(e)}")

        return alert_info

    def send_alert(self, alert_info: Dict[str, Any]):
        """
        Send alert notification (can be extended to email, Slack, etc.).

        Args:
            alert_info: Alert information dictionary
        """
        # Log to console/file (can be extended to other channels)
        if alert_info.get("alert"):
            logger.critical(
                f"\n{'='*60}\n"
                f"CRITICAL ALERT: High Error Rate Detected\n"
                f"Rate: {alert_info['rate']:.2f} errors/min\n"
                f"Threshold: {alert_info['threshold']} errors/min\n"
                f"Window: {alert_info['window_minutes']} minutes\n"
                f"Time: {alert_info['timestamp']}\n"
                f"Error Breakdown: {alert_info.get('error_breakdown', {})}\n"
                f"{'='*60}\n"
            )

            # TODO: Extend to send email, Slack, Telegram notifications
            # Example:
            # self._send_email_alert(alert_info)
            # self._send_slack_alert(alert_info)


# Global error handler instance
error_handler = ErrorHandler()


def with_retry(
    max_attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 10,
    use_cache: bool = False,
):
    """
    Decorator for API calls with automatic retry logic and error handling.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        use_cache: Whether to use cached data on failure

    Example:
        @with_retry(max_attempts=3, use_cache=True)
        def fetch_market_data(symbol):
            response = requests.get(f"/market-quote/{symbol}")
            return response.json()
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = None

            # Generate cache key if caching is enabled
            if use_cache:
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            attempt = 0
            last_exception = None

            while attempt < max_attempts:
                try:
                    # Check rate limit
                    if error_handler.rate_limit_reset_time:
                        if datetime.now() < error_handler.rate_limit_reset_time:
                            wait_time = (
                                error_handler.rate_limit_reset_time - datetime.now()
                            ).total_seconds()
                            logger.warning(
                                f"Rate limited. Waiting {wait_time:.1f} seconds..."
                            )
                            time.sleep(wait_time)
                            error_handler.rate_limit_reset_time = None

                    # Execute function
                    result = func(*args, **kwargs)

                    # Cache successful result
                    if use_cache and cache_key:
                        error_handler.cache_data(cache_key, result)

                    return result

                except Exception as e:
                    attempt += 1
                    last_exception = e

                    # Log the error
                    error_handler.log_error(
                        error_type=type(e).__name__,
                        error_message=str(e),
                        status_code=getattr(e, "status_code", None),
                        endpoint=func.__name__,
                        retry_count=attempt,
                    )

                    # Check if we should retry
                    if not error_handler.should_retry(e):
                        logger.error(
                            f"Non-retryable error in {func.__name__}: {str(e)}"
                        )
                        break

                    # Calculate wait time with exponential backoff
                    if attempt < max_attempts:
                        wait_time = min(min_wait * (2 ** (attempt - 1)), max_wait)
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}. "
                            f"Retrying in {wait_time}s... Error: {str(e)}"
                        )
                        time.sleep(wait_time)

            # All attempts failed - try cached data if available
            if use_cache and cache_key:
                cached_result = error_handler.get_cached_data(cache_key)
                if cached_result is not None:
                    logger.warning(
                        f"All retry attempts failed for {func.__name__}. "
                        "Using cached data (may be stale)."
                    )
                    return cached_result

            # No cached data available - raise the last exception
            logger.error(
                f"All {max_attempts} attempts failed for {func.__name__}. "
                f"Last error: {str(last_exception)}"
            )
            raise last_exception

        return wrapper

    return decorator


def safe_api_call(func: Callable) -> Callable:
    """
    Simplified decorator for basic error handling without retry.
    Use for operations that should fail fast.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler.log_error(
                error_type=type(e).__name__,
                error_message=str(e),
                endpoint=func.__name__,
            )
            raise

    return wrapper


def main():
    """Test error handling and retry logic"""
    import argparse

    parser = argparse.ArgumentParser(description="Error Handler Testing")
    parser.add_argument(
        "--action",
        choices=["stats", "test", "clear"],
        default="stats",
        help="Action to perform",
    )
    parser.add_argument(
        "--hours", type=int, default=24, help="Hours to look back for statistics"
    )

    args = parser.parse_args()

    if args.action == "stats":
        # Show error statistics
        stats = error_handler.get_error_statistics(hours=args.hours)

        print("\n=== Error Statistics ===")
        print(f"Time Period: Last {stats['time_period_hours']} hours")
        print(f"Total Errors: {stats['total_errors']}")
        print(f"Resolution Rate: {stats['resolution_rate']:.1f}%")

        print("\n--- Errors by Type ---")
        for error_type, count in stats["errors_by_type"].items():
            print(f"  {error_type}: {count}")

        print("\n--- Top Failing Endpoints ---")
        for endpoint, count in stats["errors_by_endpoint"].items():
            print(f"  {endpoint}: {count}")

    elif args.action == "test":
        # Test retry logic
        print("\n=== Testing Retry Logic ===")

        @with_retry(max_attempts=3, use_cache=True)
        def test_function():
            import random

            if random.random() < 0.7:  # 70% failure rate
                raise ConnectionError("Simulated network error")
            return {"status": "success", "data": [1, 2, 3]}

        try:
            result = test_function()
            print(f"Success: {result}")
        except Exception as e:
            print(f"Failed: {str(e)}")

    elif args.action == "clear":
        # Clear error logs
        conn = sqlite3.connect(error_handler.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM error_logs")
        cursor.execute("DELETE FROM api_cache")
        conn.commit()
        conn.close()
        print("Error logs and cache cleared.")


if __name__ == "__main__":
    main()
