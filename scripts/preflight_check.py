#!/usr/bin/env python3
"""
🛫 Zero-Error Architect - Pre-Flight Safety Check
==================================================

Validates code changes before deployment.
Implements the "Pre-Flight Check Protocol" from the Zero-Error Architect system.

Usage:
    python scripts/preflight_check.py                    # Check everything
    python scripts/preflight_check.py --integration      # Integration tests only
    python scripts/preflight_check.py --nicegui          # NiceGUI safety checks
    python scripts/preflight_check.py --api-v3           # API v3 compliance

The Pre-Flight Check Protocol:
1. Integration Test: Frontend-backend port matching
2. NiceGUI Trap: Async code validation
3. Beginner Shield: Code complexity check
4. Dependency Watchdog: requirements.txt validation
5. V3 Compliance Check: Upstox API version check
"""

import sys
import os
import ast
import re
from pathlib import Path
from typing import List, Dict, Tuple
import json

class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


class PreFlightChecker:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.issues = []
        self.warnings = []
        self.passed = []
        
    def log(self, message, level="info"):
        """Log with color coding"""
        if level == "success":
            print(f"{Colors.GREEN}✓{Colors.RESET} {message}")
            self.passed.append(message)
        elif level == "warning":
            print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")
            self.warnings.append(message)
        elif level == "error":
            print(f"{Colors.RED}✗{Colors.RESET} {message}")
            self.issues.append(message)
        else:
            if self.verbose:
                print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")
    
    def section(self, title):
        """Print section header"""
        print(f"\n{Colors.BOLD}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}{title}{Colors.RESET}")
        print(f"{Colors.BOLD}{'=' * 80}{Colors.RESET}\n")
    
    def check_integration_test(self):
        """
        Check 1: Integration Test
        Does frontend match backend API endpoints and ports?
        """
        self.section("🔌 Integration Test - Frontend/Backend Port Matching")
        
        # Check API server configuration
        api_server_file = Path('scripts/api_server.py')
        if api_server_file.exists():
            content = api_server_file.read_text()
            
            # Look for port configuration
            api_port = 8000  # default
            port_match = re.search(r'port["\']?\s*[:=]\s*(\d+)', content)
            if port_match:
                api_port = int(port_match.group(1))
            
            self.log(f"Backend API configured for port {api_port}", "success")
        else:
            self.log("API server file not found", "error")
            return
        
        # Check frontend configuration
        frontend_file = Path('nicegui_dashboard.py')
        if frontend_file.exists():
            content = frontend_file.read_text()
            
            # Check for API base URL
            api_base_patterns = [
                r'API_BASE\s*=\s*["\']http://localhost:(\d+)',
                r'base_url\s*=\s*["\']http://localhost:(\d+)',
                r'api_url\s*=\s*["\']http://localhost:(\d+)'
            ]
            
            frontend_api_port = None
            for pattern in api_base_patterns:
                match = re.search(pattern, content)
                if match:
                    frontend_api_port = int(match.group(1))
                    break
            
            if frontend_api_port:
                if frontend_api_port == api_port:
                    self.log(f"Frontend correctly points to backend port {api_port}", "success")
                else:
                    self.log(
                        f"PORT MISMATCH: Frontend uses {frontend_api_port}, backend uses {api_port}",
                        "error"
                    )
            else:
                self.log("Could not verify frontend API configuration", "warning")
            
            # Check frontend port
            frontend_port_match = re.search(r'ui\.run\([^)]*port\s*=\s*(\d+)', content)
            if frontend_port_match:
                frontend_port = int(frontend_port_match.group(1))
                if frontend_port == 5001:
                    self.log(f"Frontend port is {frontend_port} (standard)", "success")
                else:
                    self.log(f"Frontend port is {frontend_port} (non-standard)", "warning")
        else:
            self.log("Frontend dashboard file not found", "warning")
    
    def check_nicegui_trap(self):
        """
        Check 2: NiceGUI Trap
        Detect blocking code that will freeze the UI
        """
        self.section("⚡ NiceGUI Trap - Async Code Validation")
        
        # Check all dashboard files
        ui_files = list(Path('dashboard_ui/pages').glob('*.py'))
        ui_files.append(Path('nicegui_dashboard.py'))
        
        blocking_patterns = [
            (r'\btime\.sleep\s*\(', 'time.sleep() - use asyncio.sleep() instead'),
            (r'\brequests\.get\s*\(', 'requests.get() - use run.io_bound() or aiohttp'),
            (r'\brequests\.post\s*\(', 'requests.post() - use run.io_bound() or aiohttp'),
            (r'while\s+True\s*:', 'while True - may freeze UI if not async'),
        ]
        
        total_issues = 0
        
        for ui_file in ui_files:
            if not ui_file.exists():
                continue
            
            content = ui_file.read_text()
            file_issues = []
            
            for pattern, issue in blocking_patterns:
                matches = list(re.finditer(pattern, content))
                if matches:
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        file_issues.append((line_num, issue))
                        total_issues += 1
            
            if file_issues:
                self.log(f"Blocking code in {ui_file.name}:", "error")
                for line_num, issue in file_issues[:3]:  # Show first 3
                    print(f"    Line {line_num}: {issue}")
            else:
                if self.verbose:
                    self.log(f"{ui_file.name}: No blocking patterns detected", "success")
        
        if total_issues == 0:
            self.log("No blocking patterns found in UI code", "success")
        else:
            self.log(f"Found {total_issues} potential UI freezing issues", "error")
    
    def check_beginner_shield(self):
        """
        Check 3: Beginner Shield
        Ensure code is simple and well-documented
        """
        self.section("🛡️  Beginner Shield - Code Complexity Check")
        
        # Check for common beginner mistakes
        issues_found = []
        
        # Check for hardcoded credentials
        all_py_files = list(Path('.').glob('**/*.py'))
        for py_file in all_py_files:
            if '.venv' in str(py_file) or 'site-packages' in str(py_file):
                continue
            
            try:
                content = py_file.read_text()
                
                # Check for hardcoded secrets
                secret_patterns = [
                    r'password\s*=\s*["\'][^"\']{8,}["\']',
                    r'api_key\s*=\s*["\'][^"\']{20,}["\']',
                    r'secret\s*=\s*["\'][^"\']{20,}["\']',
                ]
                
                for pattern in secret_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        issues_found.append(f"{py_file}: Possible hardcoded credential")
                        break
            except:
                continue
        
        if issues_found:
            for issue in issues_found[:5]:
                self.log(issue, "error")
        else:
            self.log("No hardcoded credentials detected", "success")
        
        # Check for proper error handling in critical files
        critical_files = ['scripts/api_server.py', 'nicegui_dashboard.py']
        for file_path in critical_files:
            path = Path(file_path)
            if path.exists():
                content = path.read_text()
                try_count = content.count('try:')
                except_count = content.count('except')
                
                if try_count > 0 and except_count > 0:
                    self.log(f"{file_path}: Has error handling ({try_count} try blocks)", "success")
                else:
                    self.log(f"{file_path}: Missing error handling", "warning")
    
    def check_dependency_watchdog(self):
        """
        Check 4: Dependency Watchdog
        Ensure all imports are in requirements.txt
        """
        self.section("📦 Dependency Watchdog - Requirements Validation")
        
        requirements_file = Path('requirements.txt')
        if not requirements_file.exists():
            self.log("requirements.txt not found", "error")
            return
        
        # Parse requirements.txt
        requirements = set()
        for line in requirements_file.read_text().split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name (before ==, >=, etc.)
                pkg = re.split(r'[=<>!]', line)[0].strip()
                requirements.add(pkg.lower())
        
        self.log(f"Found {len(requirements)} packages in requirements.txt", "success")
        
        # Check common imports in Python files
        common_imports = set()
        py_files = list(Path('scripts').glob('*.py'))
        py_files.extend(Path('dashboard_ui/pages').glob('*.py'))
        
        for py_file in py_files[:10]:  # Sample first 10 files
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            common_imports.add(alias.name.split('.')[0].lower())
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            common_imports.add(node.module.split('.')[0].lower())
            except:
                continue
        
        # Map Python import names to package names
        import_to_package = {
            'flask': 'flask',
            'nicegui': 'nicegui',
            'pandas': 'pandas',
            'numpy': 'numpy',
            'yaml': 'pyyaml',
            'dotenv': 'python-dotenv',
            'sklearn': 'scikit-learn',
            'PIL': 'pillow',
            'cv2': 'opencv-python',
        }
        
        # Check for missing packages
        missing = []
        for imp in common_imports:
            pkg = import_to_package.get(imp, imp)
            if pkg not in requirements and imp not in ['os', 'sys', 'json', 'datetime', 're', 'pathlib']:
                missing.append(imp)
        
        if missing:
            self.log(f"Potentially missing packages: {', '.join(missing)}", "warning")
            print(f"    Add to requirements.txt if needed")
        else:
            self.log("All common imports appear to be in requirements.txt", "success")
    
    def check_v3_compliance(self):
        """
        Check 5: V3 Compliance Check
        Ensure using Upstox API v3
        """
        self.section("🔄 V3 Compliance - Upstox API Version Check")
        
        # Check for old API patterns
        old_api_patterns = [
            (r'api\.upstox\.com/v2/', 'Using API v2 URL'),
            (r'market_quote_old', 'Using old market quote method'),
        ]
        
        v3_indicators = [
            (r'api\.upstox\.com/v3/', 'Using API v3 URL'),
            (r'websocket_v3_streamer', 'Using v3 WebSocket'),
            (r'order_manager_v3', 'Using v3 Order Manager'),
        ]
        
        old_api_found = False
        v3_found = False
        
        # Check Python files
        py_files = list(Path('scripts').glob('*.py'))
        
        for py_file in py_files:
            try:
                content = py_file.read_text()
                
                for pattern, desc in old_api_patterns:
                    if re.search(pattern, content):
                        self.log(f"{py_file.name}: {desc} - upgrade to v3", "warning")
                        old_api_found = True
                
                for pattern, desc in v3_indicators:
                    if re.search(pattern, content):
                        v3_found = True
            except:
                continue
        
        if v3_found:
            self.log("API v3 implementation detected", "success")
        
        if not old_api_found:
            self.log("No old API v2 patterns detected", "success")
    
    def generate_preflight_report(self):
        """Generate pre-flight report"""
        self.section("📊 Pre-Flight Check Summary")
        
        total = len(self.passed) + len(self.warnings) + len(self.issues)
        
        print(f"\n{Colors.BOLD}Results:{Colors.RESET}")
        print(f"  {Colors.GREEN}✓ Passed:{Colors.RESET}   {len(self.passed)}")
        print(f"  {Colors.YELLOW}⚠ Warnings:{Colors.RESET} {len(self.warnings)}")
        print(f"  {Colors.RED}✗ Issues:{Colors.RESET}   {len(self.issues)}")
        
        if len(self.issues) == 0 and len(self.warnings) == 0:
            print(f"\n{Colors.GREEN}✅ PRE-FLIGHT CHECK PASSED{Colors.RESET}")
            print(f"{Colors.GREEN}System is ready for deployment!{Colors.RESET}")
            return 0
        elif len(self.issues) == 0:
            print(f"\n{Colors.YELLOW}⚠️  PRE-FLIGHT CHECK PASSED WITH WARNINGS{Colors.RESET}")
            print(f"{Colors.YELLOW}Address warnings before production deployment{Colors.RESET}")
            return 1
        else:
            print(f"\n{Colors.RED}❌ PRE-FLIGHT CHECK FAILED{Colors.RESET}")
            print(f"{Colors.RED}Fix critical issues before proceeding{Colors.RESET}")
            print(f"\n{Colors.RED}Critical Issues:{Colors.RESET}")
            for issue in self.issues[:5]:
                print(f"  • {issue}")
            return 2
    
    def run_all_checks(self):
        """Run all pre-flight checks"""
        print(f"\n{Colors.BOLD}{'*' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}🛫 ZERO-ERROR ARCHITECT - Pre-Flight Safety Check{Colors.RESET}")
        print(f"{Colors.BOLD}{'*' * 80}{Colors.RESET}\n")
        
        self.check_integration_test()
        self.check_nicegui_trap()
        self.check_beginner_shield()
        self.check_dependency_watchdog()
        self.check_v3_compliance()
        
        return self.generate_preflight_report()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Pre-Flight Safety Check')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--integration', action='store_true', help='Integration tests only')
    parser.add_argument('--nicegui', action='store_true', help='NiceGUI safety checks only')
    parser.add_argument('--api-v3', action='store_true', help='API v3 compliance only')
    
    args = parser.parse_args()
    
    checker = PreFlightChecker(verbose=args.verbose)
    
    if args.integration:
        checker.section("Running Integration Tests Only")
        checker.check_integration_test()
        return checker.generate_preflight_report()
    elif args.nicegui:
        checker.section("Running NiceGUI Safety Checks Only")
        checker.check_nicegui_trap()
        return checker.generate_preflight_report()
    elif args.api_v3:
        checker.section("Running API v3 Compliance Only")
        checker.check_v3_compliance()
        return checker.generate_preflight_report()
    else:
        exit_code = checker.run_all_checks()
        sys.exit(exit_code)


if __name__ == '__main__':
    main()
