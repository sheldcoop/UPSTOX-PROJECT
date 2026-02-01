#!/usr/bin/env python3
"""
Test All Features - Comprehensive Test Suite

Tests all 11 backend features for:
- Syntax errors
- Import errors
- Database initialization
- Basic functionality
- CLI argument parsing

Run this to verify everything works before live trading!

Usage:
    python scripts/test_all_features.py

Author: Upstox Backend Team
Date: 2026-01-31
"""

import sys
import os
import importlib
import subprocess
from pathlib import Path

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(title):
    """Print test section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_test(test_name, passed, message=""):
    """Print test result."""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {test_name}")
    if message:
        print(f"       {message}")


def test_imports():
    """Test if all required modules can be imported."""
    print_header("TESTING IMPORTS")
    
    required_modules = [
        'sqlite3',
        'requests',
        'argparse',
        'json',
        'datetime',
        'logging'
    ]
    
    all_passed = True
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print_test(f"Import {module}", True)
        except ImportError as e:
            print_test(f"Import {module}", False, str(e))
            all_passed = False
    
    return all_passed


def test_syntax(script_path):
    """Test Python syntax by compiling."""
    try:
        with open(script_path, 'r') as f:
            compile(f.read(), script_path, 'exec')
        return True, ""
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"


def test_all_scripts():
    """Test syntax for all scripts."""
    print_header("TESTING SCRIPT SYNTAX")
    
    scripts_dir = Path("scripts")
    
    scripts = [
        "candle_fetcher.py",
        "option_chain_fetcher.py",
        "option_history_fetcher.py",
        "expired_options_fetcher.py",
        "websocket_quote_streamer.py",
        "order_manager.py",
        "gtt_orders_manager.py",
        "account_fetcher.py",
        "market_depth_fetcher.py",
        "corporate_announcements_fetcher.py",
        "economic_calendar_fetcher.py",
        "news_alerts_manager.py",
        "telegram_bot.py"
    ]
    
    all_passed = True
    
    for script in scripts:
        script_path = scripts_dir / script
        
        if not script_path.exists():
            print_test(script, False, "File not found")
            all_passed = False
            continue
        
        passed, error = test_syntax(script_path)
        print_test(script, passed, error if not passed else "")
        
        if not passed:
            all_passed = False
    
    return all_passed


def test_help_commands():
    """Test --help on all scripts."""
    print_header("TESTING CLI --help")
    
    scripts = [
        "candle_fetcher.py",
        "websocket_quote_streamer.py",
        "order_manager.py",
        "gtt_orders_manager.py",
        "account_fetcher.py",
        "market_depth_fetcher.py",
        "corporate_announcements_fetcher.py",
        "economic_calendar_fetcher.py",
        "news_alerts_manager.py",
        "telegram_bot.py"
    ]
    
    all_passed = True
    
    for script in scripts:
        try:
            result = subprocess.run(
                ["python3", f"scripts/{script}", "--help"],
                capture_output=True,
                timeout=5
            )
            
            # --help should exit with 0
            passed = result.returncode == 0
            print_test(f"{script} --help", passed)
            
            if not passed:
                all_passed = False
                
        except subprocess.TimeoutExpired:
            print_test(f"{script} --help", False, "Timeout")
            all_passed = False
        except Exception as e:
            print_test(f"{script} --help", False, str(e))
            all_passed = False
    
    return all_passed


def test_database_creation():
    """Test database initialization."""
    print_header("TESTING DATABASE INITIALIZATION")
    
    import sqlite3
    
    # Remove test DB if exists
    test_db = "test_market_data.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    tests = []
    
    # Test 1: Candle fetcher DB
    try:
        sys.path.insert(0, 'scripts')
        from candle_fetcher import CandleFetcher
        
        fetcher = CandleFetcher(access_token="test_token", db_path=test_db)
        
        # Check if tables exist
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        has_candles = 'candles_new' in tables
        print_test("Candle Fetcher DB Init", has_candles, 
                  f"Tables: {', '.join(tables)}" if has_candles else "")
        tests.append(has_candles)
        
    except Exception as e:
        print_test("Candle Fetcher DB Init", False, str(e))
        tests.append(False)
    
    # Test 2: Corporate announcements DB
    try:
        from corporate_announcements_fetcher import CorporateAnnouncementsFetcher
        
        fetcher = CorporateAnnouncementsFetcher(db_path=test_db)
        
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        has_announcements = 'corporate_announcements' in tables
        print_test("Corporate Announcements DB Init", has_announcements)
        tests.append(has_announcements)
        
    except Exception as e:
        print_test("Corporate Announcements DB Init", False, str(e))
        tests.append(False)
    
    # Test 3: Economic calendar DB
    try:
        from economic_calendar_fetcher import EconomicCalendarFetcher
        
        fetcher = EconomicCalendarFetcher(db_path=test_db)
        
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        has_economic = 'economic_events' in tables
        print_test("Economic Calendar DB Init", has_economic)
        tests.append(has_economic)
        
    except Exception as e:
        print_test("Economic Calendar DB Init", False, str(e))
        tests.append(False)
    
    # Test 4: News DB
    try:
        from news_alerts_manager import NewsAlertsManager
        
        manager = NewsAlertsManager(db_path=test_db)
        
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        has_news = 'news_articles' in tables
        print_test("News Alerts DB Init", has_news)
        tests.append(has_news)
        
    except Exception as e:
        print_test("News Alerts DB Init", False, str(e))
        tests.append(False)
    
    # Cleanup
    if os.path.exists(test_db):
        os.remove(test_db)
    
    return all(tests)


def test_mock_data_generation():
    """Test mock data generation."""
    print_header("TESTING MOCK DATA GENERATION")
    
    import sqlite3
    
    test_db = "test_market_data.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    tests = []
    
    # Test economic calendar with pre-loaded events
    try:
        sys.path.insert(0, 'scripts')
        from economic_calendar_fetcher import EconomicCalendarFetcher
        
        fetcher = EconomicCalendarFetcher(db_path=test_db)
        
        # Check if events were loaded
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM economic_events")
        count = cursor.fetchone()[0]
        conn.close()
        
        has_events = count > 0
        print_test("Economic Events Pre-loaded", has_events, 
                  f"{count} events" if has_events else "")
        tests.append(has_events)
        
    except Exception as e:
        print_test("Economic Events Pre-loaded", False, str(e))
        tests.append(False)
    
    # Test news mock generation
    try:
        from news_alerts_manager import NewsAlertsManager
        
        manager = NewsAlertsManager(db_path=test_db)
        news = manager.fetch_latest_news(symbol="INFY", limit=5)
        
        has_news = len(news) > 0
        print_test("News Mock Generation", has_news,
                  f"{len(news)} articles generated" if has_news else "")
        tests.append(has_news)
        
    except Exception as e:
        print_test("News Mock Generation", False, str(e))
        tests.append(False)
    
    # Cleanup
    if os.path.exists(test_db):
        os.remove(test_db)
    
    return all(tests)


def main():
    """Run all tests."""
    print(f"\n{BLUE}╔═══════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║                  UPSTOX BACKEND - FEATURE TEST SUITE                  ║{RESET}")
    print(f"{BLUE}╚═══════════════════════════════════════════════════════════════════════╝{RESET}")
    
    results = []
    
    # Run all test suites
    results.append(("Imports", test_imports()))
    results.append(("Script Syntax", test_all_scripts()))
    results.append(("CLI Help", test_help_commands()))
    results.append(("Database Init", test_database_creation()))
    results.append(("Mock Data", test_mock_data_generation()))
    
    # Summary
    print_header("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)
    failed_tests = total_tests - passed_tests
    
    for test_name, passed in results:
        status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 80)
    print(f"Total: {total_tests} | Passed: {GREEN}{passed_tests}{RESET} | Failed: {RED}{failed_tests}{RESET}")
    print("=" * 80)
    
    if failed_tests == 0:
        print(f"\n{GREEN}✓ ALL TESTS PASSED!{RESET}")
        print(f"{GREEN}✓ System is ready for use!{RESET}\n")
        return 0
    else:
        print(f"\n{RED}✗ SOME TESTS FAILED{RESET}")
        print(f"{YELLOW}⚠ Review errors above before using in production{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
