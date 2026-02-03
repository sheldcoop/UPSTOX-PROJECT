#!/usr/bin/env python3
"""
Test Runner - Execute all tests in the test suite

Provides comprehensive test reporting and coverage analysis.
"""

import os
import sys
import unittest
import argparse
from io import StringIO

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_all_tests(verbosity=2):
    """Run all tests in the test suite."""

    # Discover and run all tests
    loader = unittest.TestLoader()
    test_dir = os.path.dirname(os.path.abspath(__file__))

    suite = loader.discover(test_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    return result


def run_specific_test(test_name, verbosity=2):
    """Run a specific test module."""

    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_file = f"test_{test_name}.py"
    test_path = os.path.join(test_dir, test_file)

    if not os.path.exists(test_path):
        print(f"✗ Test file not found: {test_file}")
        return None

    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern=test_file)

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    return result


def print_test_summary(result):
    """Print summary of test results."""

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = total_tests - failures - errors - skipped

    print(f"\n{'Total Tests':<20}: {total_tests}")
    print(f"{'Passed':<20}: {passed} ✓" if passed > 0 else f"{'Passed':<20}: {passed}")
    print(
        f"{'Failed':<20}: {failures} ✗"
        if failures > 0
        else f"{'Failed':<20}: {failures}"
    )
    print(f"{'Errors':<20}: {errors} ⚠" if errors > 0 else f"{'Errors':<20}: {errors}")
    print(f"{'Skipped':<20}: {skipped}")

    if failures > 0:
        print(f"\n{'FAILURES':-^70}")
        for test, traceback in result.failures:
            print(f"\n{test}:")
            print(traceback)

    if errors > 0:
        print(f"\n{'ERRORS':-^70}")
        for test, traceback in result.errors:
            print(f"\n{test}:")
            print(traceback)

    if skipped > 0:
        print(f"\n{'SKIPPED TESTS':-^70}")
        for test, reason in result.skipped:
            print(f"{test}: {reason}")

    print("\n" + "=" * 70)

    # Return exit code
    if failures > 0 or errors > 0:
        return 1
    return 0


def main():
    """Main function."""

    parser = argparse.ArgumentParser(description="Run tests for Upstox project")
    parser.add_argument(
        "--all", action="store_true", default=True, help="Run all tests (default)"
    )
    parser.add_argument(
        "--candle", action="store_true", help="Run candle fetcher tests only"
    )
    parser.add_argument(
        "--option-chain",
        action="store_true",
        help="Run option chain fetcher tests only",
    )
    parser.add_argument(
        "--option-history",
        action="store_true",
        help="Run option history fetcher tests only",
    )
    parser.add_argument(
        "--backtest", action="store_true", help="Run backtest engine tests only"
    )
    parser.add_argument(
        "--expired-options",
        action="store_true",
        help="Run expired options fetcher tests only",
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=2, help="Increase verbosity level"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Quiet mode (minimal output)"
    )

    args = parser.parse_args()

    verbosity = 0 if args.quiet else args.verbose

    print("=" * 70)
    print("UPSTOX PROJECT - TEST SUITE")
    print("=" * 70)
    print()

    # Run tests
    if args.candle:
        print("Running Candle Fetcher Tests...")
        result = run_specific_test("candle_fetcher", verbosity)
    elif args.option_chain:
        print("Running Option Chain Fetcher Tests...")
        result = run_specific_test("option_chain_fetcher", verbosity)
    elif args.option_history:
        print("Running Option History Fetcher Tests...")
        result = run_specific_test("option_history_fetcher", verbosity)
    elif args.backtest:
        print("Running Backtest Engine Tests...")
        result = run_specific_test("backtest_engine", verbosity)
    elif args.expired_options:
        print("Running Expired Options Fetcher Tests...")
        result = run_specific_test("expired_options_fetcher", verbosity)
    else:
        print("Running All Tests...")
        result = run_all_tests(verbosity)

    if result:
        exit_code = print_test_summary(result)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
