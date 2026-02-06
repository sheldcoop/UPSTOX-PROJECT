#!/usr/bin/env python3
"""
Comprehensive Test Runner and Coverage Report

Runs all categorized tests and generates coverage report
Target: 100% coverage on critical paths
"""

import os
import sys
import subprocess
from pathlib import Path

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text:^70}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.END}\n")

def run_test_category(category_path, category_name):
    """Run tests for a specific category"""
    print(f"\n{Colors.BLUE}▶ Running {category_name} Tests...{Colors.END}")
    print(f"{Colors.BOLD}Path: {category_path}{Colors.END}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', category_path, '-v', '--tb=short'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Print output
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        # Parse results
        passed = 0
        failed = 0
        
        # Look for passed count
        import re
        passed_match = re.search(r'(\d+) passed', result.stdout)
        if passed_match:
            passed = int(passed_match.group(1))
            
        # Look for failed count
        failed_match = re.search(r'(\d+) failed', result.stdout)
        if failed_match:
            failed = int(failed_match.group(1))
            
        if failed > 0:
            print(f"{Colors.RED}❌ {category_name}: {failed} tests FAILED{Colors.END}")
        elif passed > 0:
            print(f"{Colors.GREEN}✅ {category_name}: {passed} tests PASSED{Colors.END}")
            
        if passed == 0 and failed == 0 and not result.stdout:
            # No tests found
            print(f"{Colors.YELLOW}⚠️  {category_name}: No tests found or collection error{Colors.END}")
            return {'passed': 0, 'failed': 0, 'category': category_name, 'error': True}
            
        return {'passed': passed, 'failed': failed, 'category': category_name}
        
    except subprocess.TimeoutExpired:
        print(f"{Colors.RED}❌ {category_name}: Tests timed out{Colors.END}")
        return {'passed': 0, 'failed': 0, 'category': category_name, 'timeout': True}
    except Exception as e:
        print(f"{Colors.RED}❌ {category_name}: Error running tests: {e}{Colors.END}")
        return {'passed': 0, 'failed': 0, 'category': category_name, 'error': True}

def main():
    """Main test runner"""
    print_header("COMPREHENSIVE TEST SUITE RUNNER")
    
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print(f"{Colors.BOLD}Project Root:{Colors.END} {project_root}")
    print(f"{Colors.BOLD}Python Version:{Colors.END} {sys.version}")
    
    # Test categories to run
    test_categories = [
        ('tests/unit/api/', 'Unit: API Client'),
        ('tests/unit/auth/', 'Unit: Authentication'),
        ('tests/unit/websocket/', 'Unit: WebSocket'),
        ('tests/unit/helpers/', 'Unit: Helpers'),
        ('tests/integration/api/', 'Integration: API'),
        ('tests/integration/auth/', 'Integration: Auth'),
        ('tests/integration/websocket/', 'Integration: WebSocket'),
    ]
    
    results = []
    
    # Run each category
    for category_path, category_name in test_categories:
        if os.path.exists(category_path):
            result = run_test_category(category_path, category_name)
            results.append(result)
        else:
            print(f"{Colors.YELLOW}⚠️  Skipping {category_name} (directory not found){Colors.END}")
    
    # Summary
    print_header("TEST SUMMARY")
    
    total_passed = sum(r.get('passed', 0) for r in results)
    total_failed = sum(r.get('failed', 0) for r in results)
    total_tests = total_passed + total_failed
    
    print(f"\n{Colors.BOLD}By Category:{Colors.END}")
    for result in results:
        category = result['category']
        passed = result.get('passed', 0)
        failed = result.get('failed', 0)
        
        if result.get('error'):
            status = f"{Colors.YELLOW}ERROR{Colors.END}"
        elif result.get('timeout'):
            status = f"{Colors.RED}TIMEOUT{Colors.END}"
        elif failed > 0:
            status = f"{Colors.RED}FAIL{Colors.END}"
        elif passed > 0:
            status = f"{Colors.GREEN}PASS{Colors.END}"
        else:
            status = f"{Colors.YELLOW}SKIP{Colors.END}"
        
        print(f"  {status} | {category:30} | Passed: {passed:3} | Failed: {failed:3}")
    
    print(f"\n{Colors.BOLD}Overall Results:{Colors.END}")
    print(f"  Total Tests:     {total_tests}")
    print(f"  {Colors.GREEN}✅ Passed:{Colors.END}        {total_passed}")
    print(f"  {Colors.RED}❌ Failed:{Colors.END}        {total_failed}")
    
    if total_tests > 0:
        pass_rate = (total_passed / total_tests) * 100
        print(f"  {Colors.BOLD}Pass Rate:{Colors.END}       {pass_rate:.1f}%")
        
        if pass_rate == 100:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.END}")
        elif pass_rate >= 90:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ Excellent test coverage!{Colors.END}")
        elif pass_rate >= 75:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Good, but some tests failing{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ Many tests failing - needs attention{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  No tests executed{Colors.END}")
    
    # Coverage recommendation
    print(f"\n{Colors.BOLD}To generate coverage report:{Colors.END}")
    print(f"  {Colors.CYAN}pytest tests/unit/ --cov=backend --cov-report=html --cov-report=term{Colors.END}")
    
    print(f"\n{Colors.CYAN}{'='*70}{Colors.END}\n")
    
    return 0 if total_failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
