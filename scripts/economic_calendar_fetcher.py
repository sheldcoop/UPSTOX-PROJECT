#!/usr/bin/env python3
"""
Economic Calendar Fetcher - Macro Events for Indian Markets

Tracks major economic events that impact market movements:
- RBI Monetary Policy Committee (MPC) decisions
- GDP announcements (quarterly growth rates)
- Inflation data (CPI, WPI)
- PMI manufacturing and services
- IIP (Index of Industrial Production)
- Federal Reserve decisions (global impact)
- Trade balance data
- Employment statistics
- Currency movements

Features:
- Multi-country economic calendar (India primary, US/global secondary)
- Event impact classification (HIGH/MEDIUM/LOW)
- Historical vs forecast vs actual tracking
- Market correlation analysis
- Pre-event alerts
- Time zone handling (IST)
- Blackout period identification

Usage:
    # Get upcoming RBI policy dates
    python economic_calendar_fetcher.py --action rbi-policy --days 180

    # Get all high-impact events
    python economic_calendar_fetcher.py --action high-impact --days 60

    # Get inflation data calendar
    python economic_calendar_fetcher.py --action inflation --days 90

    # Get complete economic calendar
    python economic_calendar_fetcher.py --action calendar --days 30

    # Monitor events in real-time
    python economic_calendar_fetcher.py --action monitor --interval 3600

    # Get Fed policy dates (US impact on Indian markets)
    python economic_calendar_fetcher.py --action fed-policy --days 180

Author: Upstox Backend Team
Date: 2026-01-31
"""

import os
import sys
import json
import sqlite3
import requests
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EconomicCalendarFetcher:
    """Fetches and manages economic calendar events."""
    
    def __init__(self, db_path: str = "market_data.db"):
        """
        Initialize the Economic Calendar Fetcher.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._init_database()
        self._load_static_events()
    
    def _init_database(self):
        """Initialize database tables for economic events."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Economic events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS economic_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country TEXT NOT NULL,
                event_name TEXT NOT NULL,
                event_category TEXT,
                event_date DATETIME,
                event_time TEXT,
                previous_value REAL,
                forecast_value REAL,
                actual_value REAL,
                impact_level TEXT,
                currency TEXT,
                data_source TEXT,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(country, event_name, event_date)
            )
        """)
        
        # RBI policy decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rbi_policy_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_date DATETIME NOT NULL,
                decision_date DATETIME,
                policy_type TEXT,
                repo_rate REAL,
                reverse_repo_rate REAL,
                crr REAL,
                slr REAL,
                policy_stance TEXT,
                gdp_forecast REAL,
                inflation_forecast REAL,
                announcement TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(meeting_date)
            )
        """)
        
        # Economic alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS economic_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                event_name TEXT,
                alert_date DATETIME,
                days_before INTEGER,
                status TEXT DEFAULT 'PENDING',
                sent_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(event_id) REFERENCES economic_events(id)
            )
        """)
        
        # Market impact history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_impact_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                event_date DATETIME,
                event_name TEXT,
                nifty_change_pct REAL,
                banknifty_change_pct REAL,
                vix_change REAL,
                volume_change_pct REAL,
                recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(event_id) REFERENCES economic_events(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_economic_events_date ON economic_events(event_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_economic_events_country ON economic_events(country)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rbi_policy_date ON rbi_policy_decisions(meeting_date)")
        
        conn.commit()
        conn.close()
        logger.info("Economic calendar database initialized")
    
    def _load_static_events(self):
        """Load known recurring economic events for 2026."""
        # RBI MPC meetings (typically bi-monthly: Feb, Apr, Jun, Aug, Oct, Dec)
        rbi_meetings_2026 = [
            {'date': '2026-02-07', 'type': 'MONETARY_POLICY'},
            {'date': '2026-04-10', 'type': 'MONETARY_POLICY'},
            {'date': '2026-06-08', 'type': 'MONETARY_POLICY'},
            {'date': '2026-08-09', 'type': 'MONETARY_POLICY'},
            {'date': '2026-10-09', 'type': 'MONETARY_POLICY'},
            {'date': '2026-12-06', 'type': 'MONETARY_POLICY'}
        ]
        
        # Fed FOMC meetings 2026
        fed_meetings_2026 = [
            {'date': '2026-01-29', 'type': 'FOMC'},
            {'date': '2026-03-18', 'type': 'FOMC'},
            {'date': '2026-05-07', 'type': 'FOMC'},
            {'date': '2026-06-17', 'type': 'FOMC'},
            {'date': '2026-07-29', 'type': 'FOMC'},
            {'date': '2026-09-17', 'type': 'FOMC'},
            {'date': '2026-11-05', 'type': 'FOMC'},
            {'date': '2026-12-16', 'type': 'FOMC'}
        ]
        
        # GDP release dates (quarterly: Q3 FY26, Q4 FY26, Q1 FY27, Q2 FY27)
        gdp_releases_2026 = [
            {'date': '2026-02-28', 'quarter': 'Q3 FY26', 'type': 'GDP'},
            {'date': '2026-05-31', 'quarter': 'Q4 FY26', 'type': 'GDP'},
            {'date': '2026-08-31', 'quarter': 'Q1 FY27', 'type': 'GDP'},
            {'date': '2026-11-30', 'quarter': 'Q2 FY27', 'type': 'GDP'}
        ]
        
        # Inflation data (monthly CPI releases)
        # Typically released ~12th of following month
        inflation_dates_2026 = [
            datetime(2026, month, 12).strftime('%Y-%m-%d') 
            for month in range(2, 13)  # Feb to Dec
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert RBI policy events
        for meeting in rbi_meetings_2026:
            cursor.execute("""
                INSERT OR IGNORE INTO economic_events
                (country, event_name, event_category, event_date, impact_level, description, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                'INDIA',
                'RBI Monetary Policy Decision',
                'CENTRAL_BANK',
                meeting['date'],
                'HIGH',
                f"RBI MPC meeting to decide on repo rate and monetary policy stance",
                'STATIC'
            ))
            
            # Also insert in RBI-specific table
            cursor.execute("""
                INSERT OR IGNORE INTO rbi_policy_decisions
                (meeting_date, policy_type)
                VALUES (?, ?)
            """, (meeting['date'], meeting['type']))
        
        # Insert Fed policy events
        for meeting in fed_meetings_2026:
            cursor.execute("""
                INSERT OR IGNORE INTO economic_events
                (country, event_name, event_category, event_date, impact_level, description, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                'USA',
                'Federal Reserve FOMC Decision',
                'CENTRAL_BANK',
                meeting['date'],
                'HIGH',
                f"Fed FOMC meeting - impacts global markets including India",
                'STATIC'
            ))
        
        # Insert GDP events
        for gdp in gdp_releases_2026:
            cursor.execute("""
                INSERT OR IGNORE INTO economic_events
                (country, event_name, event_category, event_date, impact_level, description, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                'INDIA',
                f'GDP Growth Rate {gdp["quarter"]}',
                'GDP',
                gdp['date'],
                'HIGH',
                f'Quarterly GDP growth rate announcement for {gdp["quarter"]}',
                'STATIC'
            ))
        
        # Insert inflation events
        for inflation_date in inflation_dates_2026:
            month_name = datetime.strptime(inflation_date, '%Y-%m-%d').strftime('%B')
            cursor.execute("""
                INSERT OR IGNORE INTO economic_events
                (country, event_name, event_category, event_date, impact_level, description, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                'INDIA',
                f'CPI Inflation {month_name}',
                'INFLATION',
                inflation_date,
                'MEDIUM',
                f'Consumer Price Index (CPI) inflation data for {month_name}',
                'STATIC'
            ))
        
        # Insert PMI events (monthly, released ~1st business day of month)
        for month in range(2, 13):
            pmi_date = datetime(2026, month, 3).strftime('%Y-%m-%d')  # Approx 3rd of month
            month_name = datetime(2026, month, 1).strftime('%B')
            
            # Manufacturing PMI
            cursor.execute("""
                INSERT OR IGNORE INTO economic_events
                (country, event_name, event_category, event_date, impact_level, description, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                'INDIA',
                f'Manufacturing PMI {month_name}',
                'PMI',
                pmi_date,
                'MEDIUM',
                f'Purchasing Managers Index - Manufacturing for {month_name}',
                'STATIC'
            ))
            
            # Services PMI
            cursor.execute("""
                INSERT OR IGNORE INTO economic_events
                (country, event_name, event_category, event_date, impact_level, description, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                'INDIA',
                f'Services PMI {month_name}',
                'PMI',
                pmi_date,
                'MEDIUM',
                f'Purchasing Managers Index - Services for {month_name}',
                'STATIC'
            ))
        
        conn.commit()
        conn.close()
        logger.info("Static economic events loaded")
    
    def get_rbi_policy_dates(self, days_ahead: int = 180) -> List[Dict[str, Any]]:
        """
        Get upcoming RBI policy decision dates.
        
        Args:
            days_ahead: Number of days to look ahead
        
        Returns:
            List of RBI policy events
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT * FROM economic_events
            WHERE country = 'INDIA'
            AND event_name LIKE '%RBI%Policy%'
            AND event_date >= date('now')
            AND event_date <= ?
            ORDER BY event_date ASC
        """, (end_date,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return results
    
    def get_fed_policy_dates(self, days_ahead: int = 180) -> List[Dict[str, Any]]:
        """Get upcoming Fed FOMC decision dates."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT * FROM economic_events
            WHERE country = 'USA'
            AND event_name LIKE '%Federal Reserve%'
            AND event_date >= date('now')
            AND event_date <= ?
            ORDER BY event_date ASC
        """, (end_date,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return results
    
    def get_gdp_dates(self, days_ahead: int = 180) -> List[Dict[str, Any]]:
        """Get upcoming GDP announcement dates."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT * FROM economic_events
            WHERE event_category = 'GDP'
            AND event_date >= date('now')
            AND event_date <= ?
            ORDER BY event_date ASC
        """, (end_date,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return results
    
    def get_inflation_dates(self, days_ahead: int = 90) -> List[Dict[str, Any]]:
        """Get upcoming inflation data release dates."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT * FROM economic_events
            WHERE event_category = 'INFLATION'
            AND event_date >= date('now')
            AND event_date <= ?
            ORDER BY event_date ASC
        """, (end_date,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return results
    
    def get_pmi_dates(self, days_ahead: int = 90) -> List[Dict[str, Any]]:
        """Get upcoming PMI release dates."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT * FROM economic_events
            WHERE event_category = 'PMI'
            AND event_date >= date('now')
            AND event_date <= ?
            ORDER BY event_date ASC
        """, (end_date,))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return results
    
    def get_calendar(self, days_ahead: int = 30, impact_level: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get complete economic calendar.
        
        Args:
            days_ahead: Number of days to look ahead
            impact_level: Filter by impact (HIGH, MEDIUM, LOW)
        
        Returns:
            List of economic events
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        query = """
            SELECT * FROM economic_events
            WHERE event_date >= date('now')
            AND event_date <= ?
        """
        
        params = [end_date]
        
        if impact_level:
            query += " AND impact_level = ?"
            params.append(impact_level)
        
        query += " ORDER BY event_date ASC"
        
        cursor.execute(query, params)
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return results
    
    def get_high_impact_events(self, days_ahead: int = 60) -> List[Dict[str, Any]]:
        """Get only high-impact economic events."""
        return self.get_calendar(days_ahead=days_ahead, impact_level='HIGH')
    
    def set_alert(self, event_name: str, days_before: int = 3) -> bool:
        """
        Set alert for upcoming economic event.
        
        Args:
            event_name: Name of economic event
            days_before: Days before event to alert
        
        Returns:
            True if alert set successfully
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find matching event
        cursor.execute("""
            SELECT id, event_date FROM economic_events
            WHERE event_name LIKE ?
            AND event_date >= date('now')
            ORDER BY event_date ASC
            LIMIT 1
        """, (f'%{event_name}%',))
        
        result = cursor.fetchone()
        
        if not result:
            logger.warning(f"No upcoming event found matching: {event_name}")
            conn.close()
            return False
        
        event_id, event_date = result
        alert_date = (datetime.strptime(event_date, '%Y-%m-%d') - timedelta(days=days_before)).strftime('%Y-%m-%d')
        
        cursor.execute("""
            INSERT OR IGNORE INTO economic_alerts
            (event_id, event_name, alert_date, days_before)
            VALUES (?, ?, ?, ?)
        """, (event_id, event_name, alert_date, days_before))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Alert set for {event_name} on {alert_date}")
        return True
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for pending economic event alerts."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT a.*, e.event_date, e.description, e.impact_level
            FROM economic_alerts a
            JOIN economic_events e ON a.event_id = e.id
            WHERE a.status = 'PENDING'
            AND date(a.alert_date) <= date('now')
            ORDER BY a.alert_date ASC
        """)
        
        columns = [desc[0] for desc in cursor.description]
        alerts = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Mark alerts as sent
        for alert in alerts:
            cursor.execute("""
                UPDATE economic_alerts
                SET status = 'SENT', sent_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (alert['id'],))
        
        conn.commit()
        conn.close()
        
        return alerts
    
    def record_market_impact(self, event_id: int, nifty_change: float, 
                            banknifty_change: float, vix_change: float):
        """
        Record market impact after economic event.
        
        Args:
            event_id: Economic event ID
            nifty_change: NIFTY percentage change
            banknifty_change: BANKNIFTY percentage change
            vix_change: VIX absolute change
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get event details
        cursor.execute("""
            SELECT event_name, event_date FROM economic_events
            WHERE id = ?
        """, (event_id,))
        
        result = cursor.fetchone()
        
        if result:
            event_name, event_date = result
            
            cursor.execute("""
                INSERT INTO market_impact_history
                (event_id, event_date, event_name, nifty_change_pct, 
                 banknifty_change_pct, vix_change)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (event_id, event_date, event_name, nifty_change, banknifty_change, vix_change))
            
            conn.commit()
            logger.info(f"Market impact recorded for {event_name}")
        
        conn.close()
    
    def display_calendar(self, events: List[Dict[str, Any]], title: str = "ECONOMIC CALENDAR"):
        """Display economic calendar in formatted table."""
        if not events:
            print("\n❌ No events found")
            return
        
        print("\n" + "=" * 120)
        print(title)
        print("=" * 120)
        print(f"{'Date':<12} | {'Country':<8} | {'Event':<35} | {'Impact':<8} | {'Days Away':<10} | {'Category':<15}")
        print("-" * 120)
        
        current_date = datetime.now()
        
        for event in events:
            event_date = event.get('event_date', '')
            country = event.get('country', '')[:8]
            event_name = event.get('event_name', '')[:35]
            impact = event.get('impact_level', 'MEDIUM')
            category = event.get('event_category', '')[:15]
            
            # Calculate days away
            try:
                event_dt = datetime.strptime(event_date, '%Y-%m-%d')
                days_away = (event_dt - current_date).days
                days_str = f"{days_away} days"
            except:
                days_str = "N/A"
            
            # Impact emoji
            impact_emoji = "🔴" if impact == "HIGH" else "🟡" if impact == "MEDIUM" else "🟢"
            
            print(f"{event_date:<12} | {country:<8} | {event_name:<35} | {impact_emoji} {impact:<6} | {days_str:<10} | {category:<15}")
        
        print("=" * 120)
        print(f"Total events: {len(events)}\n")
    
    def monitor_events(self, interval: int = 3600, duration: Optional[int] = None):
        """
        Monitor economic events and check for alerts.
        
        Args:
            interval: Check interval in seconds
            duration: Total monitoring duration in seconds
        """
        import time
        
        start_time = time.time()
        print(f"\n🔍 Monitoring economic events (checking every {interval}s)")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Check for alerts
                alerts = self.check_alerts()
                
                if alerts:
                    print(f"\n🚨 ECONOMIC EVENT ALERTS ({len(alerts)})")
                    print("-" * 80)
                    for alert in alerts:
                        print(f"  📅 {alert['event_name']}")
                        print(f"     Date: {alert['event_date']}")
                        print(f"     Impact: {alert['impact_level']}")
                        print(f"     Description: {alert['description']}")
                        print()
                
                # Display timestamp
                print(f"✓ Checked at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Next check in {interval}s")
                
                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    print("\n✅ Monitoring duration completed")
                    break
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n✅ Monitoring stopped by user")


def main():
    parser = argparse.ArgumentParser(
        description="Economic Calendar Fetcher - Track macro events",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--action', type=str, required=True,
                       choices=['calendar', 'high-impact', 'rbi-policy', 'fed-policy',
                               'gdp', 'inflation', 'pmi', 'set-alert', 'check-alerts', 'monitor'],
                       help='Action to perform')
    
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days to look ahead (default: 30)')
    
    parser.add_argument('--event-name', type=str,
                       help='Event name for alert')
    
    parser.add_argument('--days-before', type=int, default=3,
                       help='Days before event to alert (default: 3)')
    
    parser.add_argument('--interval', type=int, default=3600,
                       help='Monitoring interval in seconds (default: 3600)')
    
    parser.add_argument('--duration', type=int,
                       help='Monitoring duration in seconds')
    
    parser.add_argument('--db-path', type=str, default='market_data.db',
                       help='Database path (default: market_data.db)')
    
    args = parser.parse_args()
    
    # Initialize fetcher
    fetcher = EconomicCalendarFetcher(db_path=args.db_path)
    
    # Execute action
    if args.action == 'calendar':
        events = fetcher.get_calendar(days_ahead=args.days)
        fetcher.display_calendar(events, title="COMPLETE ECONOMIC CALENDAR")
    
    elif args.action == 'high-impact':
        events = fetcher.get_high_impact_events(days_ahead=args.days)
        fetcher.display_calendar(events, title="HIGH-IMPACT ECONOMIC EVENTS")
    
    elif args.action == 'rbi-policy':
        events = fetcher.get_rbi_policy_dates(days_ahead=args.days)
        fetcher.display_calendar(events, title="RBI MONETARY POLICY CALENDAR")
    
    elif args.action == 'fed-policy':
        events = fetcher.get_fed_policy_dates(days_ahead=args.days)
        fetcher.display_calendar(events, title="FEDERAL RESERVE FOMC CALENDAR")
    
    elif args.action == 'gdp':
        events = fetcher.get_gdp_dates(days_ahead=args.days)
        fetcher.display_calendar(events, title="GDP ANNOUNCEMENT CALENDAR")
    
    elif args.action == 'inflation':
        events = fetcher.get_inflation_dates(days_ahead=args.days)
        fetcher.display_calendar(events, title="INFLATION DATA CALENDAR")
    
    elif args.action == 'pmi':
        events = fetcher.get_pmi_dates(days_ahead=args.days)
        fetcher.display_calendar(events, title="PMI RELEASE CALENDAR")
    
    elif args.action == 'set-alert':
        if not args.event_name:
            print("❌ Error: --event-name required for set-alert")
            sys.exit(1)
        
        success = fetcher.set_alert(
            event_name=args.event_name,
            days_before=args.days_before
        )
        
        if success:
            print(f"✅ Alert set for {args.event_name} ({args.days_before} days before)")
        else:
            print(f"❌ Failed to set alert")
    
    elif args.action == 'check-alerts':
        alerts = fetcher.check_alerts()
        
        if alerts:
            print(f"\n🚨 PENDING ECONOMIC EVENT ALERTS ({len(alerts)})")
            print("=" * 80)
            for alert in alerts:
                print(f"Event: {alert['event_name']}")
                print(f"Date: {alert['event_date']}")
                print(f"Impact: {alert['impact_level']}")
                print(f"Description: {alert['description']}")
                print("-" * 80)
        else:
            print("\n✅ No pending alerts")
    
    elif args.action == 'monitor':
        fetcher.monitor_events(
            interval=args.interval,
            duration=args.duration
        )


if __name__ == "__main__":
    main()
