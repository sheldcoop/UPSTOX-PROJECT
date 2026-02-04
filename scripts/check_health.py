#!/usr/bin/env python3
"""
🏥 Zero-Error Architect - Comprehensive System Health Checker
==============================================================

Validates the entire trading platform before deployment or after changes.
Provides color-coded output with confidence scores.

Usage:
    python scripts/check_health.py              # Full check
    python scripts/check_health.py --quick      # Quick check (no API calls)
    python scripts/check_health.py --verbose    # Detailed output

Exit Codes:
    0 - All checks passed (Green)
    1 - Warnings detected (Yellow)
    2 - Critical failures (Red)
"""

import sys
import os
import sqlite3
import importlib
import subprocess
import argparse
import json
from pathlib import Path
from datetime import datetime
import socket

# Colors for terminal output
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

class HealthChecker:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.errors = []
        self.warnings = []
        self.passed = []
        self.confidence_score = 100
        
    def log(self, message, level="info"):
        """Log a message with appropriate color"""
        if level == "success":
            print(f"{Colors.GREEN}✓{Colors.RESET} {message}")
            self.passed.append(message)
        elif level == "warning":
            print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")
            self.warnings.append(message)
            self.confidence_score -= 5
        elif level == "error":
            print(f"{Colors.RED}✗{Colors.RESET} {message}")
            self.errors.append(message)
            self.confidence_score -= 15
        else:
            if self.verbose:
                print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")
    
    def section(self, title):
        """Print a section header"""
        print(f"\n{Colors.BOLD}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}{title}{Colors.RESET}")
        print(f"{Colors.BOLD}{'=' * 80}{Colors.RESET}\n")
    
    def check_python_version(self):
        """Check Python version is 3.11+"""
        self.section("🐍 Python Version Check")
        version = sys.version_info
        if version >= (3, 11):
            self.log(f"Python {version.major}.{version.minor}.{version.micro}", "success")
        elif version >= (3, 9):
            self.log(f"Python {version.major}.{version.minor}.{version.micro} (Recommended: 3.11+)", "warning")
        else:
            self.log(f"Python {version.major}.{version.minor}.{version.micro} (Required: 3.11+)", "error")
    
    def check_dependencies(self):
        """Check all required dependencies are installed"""
        self.section("📦 Dependencies Check")
        
        required = {
            'flask': 'Flask',
            'nicegui': 'NiceGUI',
            'pandas': 'Pandas',
            'requests': 'Requests',
            'yaml': 'PyYAML',
            'dotenv': 'python-dotenv',
            'cryptography': 'Cryptography',
            'gunicorn': 'Gunicorn'
        }
        
        for module, name in required.items():
            try:
                importlib.import_module(module)
                self.log(f"{name} installed", "success")
            except ImportError:
                self.log(f"{name} NOT installed - run: pip install {name.lower()}", "error")
    
    def check_environment(self):
        """Check environment variables"""
        self.section("🔐 Environment Configuration")
        
        env_file = Path('.env')
        if not env_file.exists():
            self.log(".env file NOT found - copy from .env.example", "error")
            return
        
        self.log(".env file exists", "success")
        
        # Check critical env vars
        critical_vars = [
            'UPSTOX_CLIENT_ID',
            'UPSTOX_CLIENT_SECRET',
            'UPSTOX_REDIRECT_URI'
        ]
        
        from dotenv import load_dotenv
        load_dotenv()
        
        for var in critical_vars:
            value = os.getenv(var)
            if value and value != 'your_client_id_here':
                self.log(f"{var} configured", "success")
            else:
                self.log(f"{var} NOT configured in .env", "warning")
    
    def check_database(self):
        """Check database exists and has data"""
        self.section("🗄️  Database Check")
        
        db_path = 'market_data.db'
        if not Path(db_path).exists():
            self.log(f"{db_path} NOT found - will be created on first run", "warning")
            return
        
        self.log(f"{db_path} exists", "success")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check key tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            if len(tables) > 0:
                self.log(f"Found {len(tables)} tables", "success")
                
                # Check for critical tables
                critical_tables = ['oauth_tokens', 'candles_new', 'option_chain_snapshots']
                for table in critical_tables:
                    if table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        if count > 0:
                            self.log(f"{table}: {count} records", "success")
                        else:
                            self.log(f"{table}: empty", "warning")
                    else:
                        self.log(f"{table}: NOT created yet", "warning")
            else:
                self.log("Database is empty", "warning")
            
            conn.close()
        except Exception as e:
            self.log(f"Database error: {e}", "error")
    
    def check_ports(self):
        """Check if required ports are available"""
        self.section("🌐 Port Availability Check")
        
        ports = {
            8000: 'API Server',
            5001: 'Frontend (NiceGUI)'
        }
        
        for port, name in ports.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                self.log(f"Port {port} ({name}) is IN USE (service running)", "success")
            else:
                self.log(f"Port {port} ({name}) is AVAILABLE", "success")
    
    def check_file_structure(self):
        """Check all critical files and directories exist"""
        self.section("📁 File Structure Check")
        
        critical_paths = {
            'scripts/api_server.py': 'API Server',
            'nicegui_dashboard.py': 'Frontend Dashboard',
            'config/trading.yaml': 'Trading Config',
            'requirements.txt': 'Dependencies File',
            '.gitignore': 'Git Ignore',
            'scripts/blueprints': 'API Blueprints (directory)',
            'dashboard_ui/pages': 'UI Pages (directory)'
        }
        
        for path, desc in critical_paths.items():
            full_path = Path(path)
            if full_path.exists():
                self.log(f"{desc} exists", "success")
            else:
                self.log(f"{desc} NOT found at {path}", "error")
    
    def check_api_v3_compliance(self):
        """Check for Upstox API v3 compliance"""
        self.section("🔄 Upstox API v3 Compliance")
        
        # Check for websocket implementation
        ws_file = Path('scripts/websocket_v3_streamer.py')
        if ws_file.exists():
            self.log("WebSocket v3 implementation found", "success")
        else:
            self.log("WebSocket v3 NOT implemented - upgrade needed", "warning")
        
        # Check for order manager v3
        order_file = Path('scripts/order_manager_v3.py')
        if order_file.exists():
            self.log("Order Manager v3 found", "success")
        else:
            self.log("Order Manager v3 NOT found - upgrade needed", "warning")
    
    def check_async_patterns(self):
        """Check for async/await patterns in NiceGUI code"""
        self.section("⚡ Async Pattern Check")
        
        dashboard_file = Path('nicegui_dashboard.py')
        if dashboard_file.exists():
            content = dashboard_file.read_text()
            
            # Check for blocking patterns
            if 'time.sleep' in content:
                self.log("WARNING: time.sleep() found - use asyncio.sleep() instead", "warning")
            else:
                self.log("No blocking time.sleep() calls found", "success")
            
            # Check for async usage
            if 'async def' in content or 'await ' in content:
                self.log("Async patterns detected", "success")
            else:
                self.log("Consider using async patterns for better UI responsiveness", "warning")
    
    def check_git_status(self):
        """Check git repository status"""
        self.section("📝 Git Status Check")
        
        try:
            # Check if git repo
            result = subprocess.run(['git', 'status'], 
                                  capture_output=True, 
                                  text=True, 
                                  check=False)
            
            if result.returncode == 0:
                self.log("Git repository initialized", "success")
                
                # Check for uncommitted changes
                if 'nothing to commit' in result.stdout:
                    self.log("No uncommitted changes", "success")
                else:
                    self.log("Uncommitted changes present", "warning")
            else:
                self.log("Not a git repository", "warning")
        except FileNotFoundError:
            self.log("Git not installed", "warning")
    
    def generate_report(self):
        """Generate final report with confidence score"""
        self.section("📊 Health Check Summary")
        
        total_checks = len(self.passed) + len(self.warnings) + len(self.errors)
        
        print(f"\n{Colors.BOLD}Results:{Colors.RESET}")
        print(f"  {Colors.GREEN}✓ Passed:{Colors.RESET}   {len(self.passed)}")
        print(f"  {Colors.YELLOW}⚠ Warnings:{Colors.RESET} {len(self.warnings)}")
        print(f"  {Colors.RED}✗ Errors:{Colors.RESET}   {len(self.errors)}")
        print(f"\n{Colors.BOLD}Total Checks: {total_checks}{Colors.RESET}")
        
        # Ensure confidence score doesn't go negative
        self.confidence_score = max(0, self.confidence_score)
        
        print(f"\n{Colors.BOLD}Confidence Score: {self.confidence_score}%{Colors.RESET}")
        
        if self.confidence_score >= 90:
            print(f"{Colors.GREEN}🎉 System is PRODUCTION READY!{Colors.RESET}")
            print(f"\n{Colors.GREEN}I am {self.confidence_score}% sure this will work because:{Colors.RESET}")
            print(f"  • All critical checks passed")
            print(f"  • Dependencies are installed")
            print(f"  • Configuration files exist")
            return 0
        elif self.confidence_score >= 70:
            print(f"{Colors.YELLOW}⚠️  System has minor issues{Colors.RESET}")
            print(f"\n{Colors.YELLOW}I am {self.confidence_score}% sure this will work because:{Colors.RESET}")
            print(f"  • Most checks passed")
            print(f"  • Some non-critical warnings exist")
            print(f"\n{Colors.YELLOW}Recommended actions:{Colors.RESET}")
            for warning in self.warnings[:5]:
                print(f"  • {warning}")
            return 1
        else:
            print(f"{Colors.RED}❌ System has CRITICAL issues{Colors.RESET}")
            print(f"\n{Colors.RED}I am only {self.confidence_score}% confident because:{Colors.RESET}")
            print(f"  • Critical errors detected")
            print(f"  • System may not function correctly")
            print(f"\n{Colors.RED}Required fixes:{Colors.RESET}")
            for error in self.errors[:5]:
                print(f"  • {error}")
            return 2
    
    def run_all_checks(self, quick=False):
        """Run all health checks"""
        print(f"\n{Colors.BOLD}{'*' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}🛡️  ZERO-ERROR ARCHITECT - System Health Check{Colors.RESET}")
        print(f"{Colors.BOLD}{'*' * 80}{Colors.RESET}")
        print(f"\n{Colors.BLUE}Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}\n")
        
        # Core checks (always run)
        self.check_python_version()
        self.check_dependencies()
        self.check_environment()
        self.check_file_structure()
        
        if not quick:
            # Extended checks
            self.check_database()
            self.check_ports()
            self.check_api_v3_compliance()
            self.check_async_patterns()
            self.check_git_status()
        
        return self.generate_report()


def main():
    parser = argparse.ArgumentParser(description='Zero-Error Architect - System Health Checker')
    parser.add_argument('--quick', action='store_true', 
                       help='Quick check (skip API and database checks)')
    parser.add_argument('--verbose', action='store_true', 
                       help='Verbose output')
    parser.add_argument('--json', action='store_true',
                       help='Output results as JSON')
    
    args = parser.parse_args()
    
    checker = HealthChecker(verbose=args.verbose)
    exit_code = checker.run_all_checks(quick=args.quick)
    
    if args.json:
        # Output JSON for CI/CD integration
        results = {
            'timestamp': datetime.now().isoformat(),
            'confidence_score': checker.confidence_score,
            'passed': len(checker.passed),
            'warnings': len(checker.warnings),
            'errors': len(checker.errors),
            'status': 'pass' if exit_code == 0 else 'warning' if exit_code == 1 else 'fail'
        }
        print(f"\n{json.dumps(results, indent=2)}")
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
