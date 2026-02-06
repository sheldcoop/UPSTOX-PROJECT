#!/usr/bin/env python3
"""
Quick Security and Code Quality Validation
Tests critical security fixes without requiring full dependency installation
"""

import sys
import os
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_header(msg):
    print(f"\n{BOLD}{'=' * 70}{RESET}")
    print(f"{BOLD}{msg}{RESET}")
    print(f"{BOLD}{'=' * 70}{RESET}\n")


def test_env_example_security():
    """Test that .env.example doesn't contain real credentials"""
    print_header("TEST 1: Check .env.example Security")
    
    env_path = Path('.env.example')
    if not env_path.exists():
        print_warning(".env.example not found")
        return False
    
    content = env_path.read_text()
    
    # Check for exposed credentials
    issues = []
    if '33b9a757-1a99-47dc-b6fa-c3cf3dcaf6b4' in content:
        issues.append("Real UPSTOX_CLIENT_ID found")
    if 't6hxe1b1ky' in content:
        issues.append("Real UPSTOX_CLIENT_SECRET found")
    if 'BcaH04F93jlI8F37K9NWJKr2kIuonRzdJ6bsmXsWY8I=' in content:
        issues.append("Real ENCRYPTION_KEY found")
    
    if issues:
        for issue in issues:
            print_error(issue)
        return False
    
    # Check for placeholders
    if 'your-upstox-client-id-here' in content:
        print_success(".env.example contains placeholders (no real credentials)")
        return True
    else:
        print_warning("Placeholders not found, but no real credentials either")
        return True


def test_api_server_security():
    """Test that api_server.py doesn't contain hardcoded credentials"""
    print_header("TEST 2: Check api_server.py Security")
    
    api_path = Path('backend/api/servers/api_server.py')
    if not api_path.exists():
        print_warning("api_server.py not found")
        return False
    
    content = api_path.read_text()
    
    # Check for hardcoded CLIENT_ID
    if "CLIENT_ID = '33b9a757-1a99-47dc-b6fa-c3cf3dcaf6b4'" in content:
        print_error("Hardcoded CLIENT_ID found in api_server.py")
        return False
    
    # Check for environment variable loading
    if "os.getenv('UPSTOX_CLIENT_ID'" in content:
        print_success("api_server.py loads credentials from environment")
    else:
        print_warning("Environment variable loading not found")
    
    # Check for CSRF protection
    if "from flask_wtf.csrf import CSRFProtect" in content:
        print_success("CSRF protection imported")
    else:
        print_warning("CSRF protection import not found")
    
    if "csrf = CSRFProtect(app)" in content:
        print_success("CSRF protection enabled")
        return True
    else:
        print_warning("CSRF protection not enabled")
        return False


def test_sql_injection_fixes():
    """Test that SQL injection vulnerabilities are fixed"""
    print_header("TEST 3: Check SQL Injection Fixes")
    
    # Check symbol_resolver.py
    symbol_path = Path('backend/utils/helpers/symbol_resolver.py')
    if symbol_path.exists():
        content = symbol_path.read_text()
        
        # Check for parameterized queries
        if 'cur.execute(query, params)' in content or 'cursor.execute(query, params)' in content:
            print_success("symbol_resolver.py uses parameterized queries")
        else:
            print_error("symbol_resolver.py doesn't use parameterized queries")
            return False
        
        # Check for parameter list usage
        if 'params = []' in content and 'params.append' in content:
            print_success("symbol_resolver.py builds parameter lists safely")
        else:
            print_warning("Parameter list building not found (may use different method)")
    
    # Check database_validator.py
    validator_path = Path('backend/data/database/database_validator.py')
    if validator_path.exists():
        content = validator_path.read_text()
        
        # Check for table whitelist
        if 'valid_tables = {' in content:
            print_success("database_validator.py uses table whitelist")
        else:
            print_error("database_validator.py missing table whitelist")
            return False
    
    # Check schema_indices.py
    schema_path = Path('backend/data/database/schema_indices.py')
    if schema_path.exists():
        content = schema_path.read_text()
        
        # Check for validation
        if 'valid_tables' in content:
            print_success("schema_indices.py validates table names")
        else:
            print_warning("schema_indices.py table validation not found")
    
    return True


def test_centralized_logging():
    """Test that centralized logging is used"""
    print_header("TEST 4: Check Centralized Logging")
    
    api_path = Path('backend/api/servers/api_server.py')
    if not api_path.exists():
        print_warning("api_server.py not found")
        return False
    
    content = api_path.read_text()
    
    # Check that logging.basicConfig is NOT used
    if 'logging.basicConfig(' in content:
        print_error("api_server.py still uses logging.basicConfig()")
        return False
    
    # Check for centralized logger import
    if 'from backend.utils.logging.config import get_logger' in content:
        print_success("api_server.py uses centralized logging")
        return True
    else:
        print_warning("Centralized logging import not found")
        return False


def test_file_structure():
    """Test that critical files exist and are properly structured"""
    print_header("TEST 5: Check File Structure")
    
    critical_files = [
        'backend/api/servers/api_server.py',
        'backend/utils/logging/config.py',
        'backend/utils/helpers/symbol_resolver.py',
        'backend/data/database/database_validator.py',
        '.env.example',
        'requirements.txt',
    ]
    
    all_exist = True
    for filepath in critical_files:
        path = Path(filepath)
        if path.exists():
            print_success(f"{filepath} exists")
        else:
            print_error(f"{filepath} missing")
            all_exist = False
    
    return all_exist


def run_all_tests():
    """Run all validation tests"""
    print("\n" + "=" * 70)
    print(f"{BOLD}🔍 SECURITY & CODE QUALITY VALIDATION{RESET}")
    print("=" * 70)
    
    results = {
        "Environment File Security": test_env_example_security(),
        "API Server Security": test_api_server_security(),
        "SQL Injection Fixes": test_sql_injection_fixes(),
        "Centralized Logging": test_centralized_logging(),
        "File Structure": test_file_structure(),
    }
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {test_name:30} {status}")
    
    print(f"\n{BOLD}Results: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"\n{GREEN}{BOLD}✅ ALL VALIDATIONS PASSED!{RESET}")
        print(f"{GREEN}   - No exposed credentials")
        print(f"   - SQL injection vulnerabilities fixed")
        print(f"   - CSRF protection enabled")
        print(f"   - Centralized logging configured{RESET}")
        return 0
    else:
        print(f"\n{RED}{BOLD}❌ SOME VALIDATIONS FAILED{RESET}")
        print(f"{RED}   Please review the issues above{RESET}")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
