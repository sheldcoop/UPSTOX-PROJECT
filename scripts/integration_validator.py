#!/usr/bin/env python3
"""
🔗 Zero-Error Architect - Integration Validator
===============================================

Validates integration between frontend and backend.
Ensures all frontend API calls correctly match backend endpoints.

Usage:
    python scripts/integration_validator.py              # Full validation
    python scripts/integration_validator.py --fix        # Auto-fix port mismatches
    python scripts/integration_validator.py --report     # Generate report
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple
import argparse


class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


class IntegrationValidator:
    def __init__(self, fix_mode=False):
        self.fix_mode = fix_mode
        self.issues = []
        self.fixed = []
        self.backend_endpoints = set()
        self.frontend_calls = []
        
    def log(self, message, level="info"):
        """Log with color coding"""
        if level == "success":
            print(f"{Colors.GREEN}✓{Colors.RESET} {message}")
        elif level == "warning":
            print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")
        elif level == "error":
            print(f"{Colors.RED}✗{Colors.RESET} {message}")
        else:
            print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")
    
    def section(self, title):
        """Print section header"""
        print(f"\n{Colors.BOLD}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}{title}{Colors.RESET}")
        print(f"{Colors.BOLD}{'=' * 80}{Colors.RESET}\n")
    
    def scan_backend_endpoints(self):
        """Scan backend files for API endpoints"""
        self.section("📡 Scanning Backend Endpoints")
        
        # Check main API server
        api_server = Path('scripts/api_server.py')
        if api_server.exists():
            content = api_server.read_text()
            
            # Find Flask routes
            route_pattern = r'@(?:app|blueprint)\.route\([\'"]([^\'"]+)'
            routes = re.findall(route_pattern, content)
            
            for route in routes:
                self.backend_endpoints.add(route)
            
            self.log(f"Found {len(routes)} routes in api_server.py", "success")
        
        # Check blueprints
        blueprints_dir = Path('scripts/blueprints')
        if blueprints_dir.exists():
            for bp_file in blueprints_dir.glob('*.py'):
                content = bp_file.read_text()
                routes = re.findall(route_pattern, content)
                
                for route in routes:
                    # Blueprint routes have prefix
                    if not route.startswith('/'):
                        route = '/' + route
                    self.backend_endpoints.add(route)
                
                if routes:
                    self.log(f"Found {len(routes)} routes in {bp_file.name}", "success")
        
        self.log(f"Total backend endpoints: {len(self.backend_endpoints)}", "info")
        
        # Display sample endpoints
        if self.backend_endpoints:
            print("\nSample endpoints:")
            for endpoint in list(self.backend_endpoints)[:10]:
                print(f"  • {endpoint}")
    
    def scan_frontend_api_calls(self):
        """Scan frontend files for API calls"""
        self.section("🎨 Scanning Frontend API Calls")
        
        # Scan dashboard files
        ui_files = []
        
        # Main dashboard
        if Path('nicegui_dashboard.py').exists():
            ui_files.append(Path('nicegui_dashboard.py'))
        
        # UI pages
        pages_dir = Path('dashboard_ui/pages')
        if pages_dir.exists():
            ui_files.extend(pages_dir.glob('*.py'))
        
        for ui_file in ui_files:
            content = ui_file.read_text()
            
            # Find API calls
            # Pattern 1: requests.get/post
            request_patterns = [
                r'requests\.(get|post|put|delete)\([\'"]([^\'"]+)',
                r'safe_api_call\([\'"]([^\'"]+)',
                r'fetch\([\'"]([^\'"]+)',
                r'API_BASE\s*\+\s*[\'"]([^\'"]+)',
            ]
            
            for pattern in request_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, tuple):
                        # Extract URL from tuple
                        url = match[-1] if len(match) > 1 else match[0]
                    else:
                        url = match
                    
                    # Clean up URL
                    if 'localhost' in url:
                        # Extract port and path
                        port_match = re.search(r':(\d+)', url)
                        path_match = re.search(r'localhost:\d+(/[^\s\'"]+)', url)
                        
                        port = port_match.group(1) if port_match else None
                        path = path_match.group(1) if path_match else None
                        
                        if port and path:
                            self.frontend_calls.append({
                                'file': ui_file.name,
                                'port': port,
                                'path': path,
                                'full_url': url
                            })
        
        self.log(f"Found {len(self.frontend_calls)} API calls in frontend", "success")
        
        # Display sample calls
        if self.frontend_calls:
            print("\nSample API calls:")
            for call in self.frontend_calls[:5]:
                print(f"  • {call['file']}: {call['path']} (port {call['port']})")
    
    def validate_integration(self):
        """Validate that frontend calls match backend endpoints"""
        self.section("🔍 Validating Integration")
        
        standard_backend_port = '8000'
        standard_frontend_port = '5001'
        
        port_issues = []
        endpoint_issues = []
        
        for call in self.frontend_calls:
            # Check port
            if call['port'] != standard_backend_port:
                port_issues.append(call)
            
            # Check if endpoint exists in backend
            path = call['path']
            # Remove /api prefix if present for matching
            clean_path = path.replace('/api', '', 1) if path.startswith('/api') else path
            
            # Check if any backend endpoint matches
            matched = False
            for endpoint in self.backend_endpoints:
                if clean_path in endpoint or endpoint in path:
                    matched = True
                    break
            
            if not matched:
                endpoint_issues.append(call)
        
        # Report port issues
        if port_issues:
            self.log(f"Found {len(port_issues)} port mismatches", "error")
            for issue in port_issues[:5]:
                print(f"  • {issue['file']}: Using port {issue['port']} instead of {standard_backend_port}")
            self.issues.extend(port_issues)
        else:
            self.log("All API calls use correct port (8000)", "success")
        
        # Report endpoint issues
        if endpoint_issues:
            self.log(f"Found {len(endpoint_issues)} potential missing endpoints", "warning")
            for issue in endpoint_issues[:5]:
                print(f"  • {issue['file']}: {issue['path']} (not found in backend)")
            self.issues.extend(endpoint_issues)
        else:
            self.log("All API calls match backend endpoints", "success")
    
    def fix_port_mismatches(self):
        """Auto-fix port mismatches in frontend files"""
        if not self.fix_mode:
            return
        
        self.section("🔧 Auto-Fixing Port Mismatches")
        
        standard_port = '8000'
        
        # Get unique files with issues
        files_to_fix = set()
        for issue in self.issues:
            if issue['port'] != standard_port:
                files_to_fix.add(issue['file'])
        
        for filename in files_to_fix:
            # Find full path
            file_path = None
            if Path(filename).exists():
                file_path = Path(filename)
            elif Path(f'dashboard_ui/pages/{filename}').exists():
                file_path = Path(f'dashboard_ui/pages/{filename}')
            
            if not file_path:
                continue
            
            content = file_path.read_text()
            original_content = content
            
            # Replace wrong ports with correct port
            wrong_ports = ['3000', '5000', '5001', '9000']
            for wrong_port in wrong_ports:
                pattern = f'localhost:{wrong_port}'
                replacement = f'localhost:{standard_port}'
                content = content.replace(pattern, replacement)
            
            if content != original_content:
                file_path.write_text(content)
                self.log(f"Fixed port in {filename}", "success")
                self.fixed.append(filename)
    
    def generate_report(self):
        """Generate validation report"""
        self.section("📊 Integration Validation Report")
        
        print(f"\n{Colors.BOLD}Summary:{Colors.RESET}")
        print(f"  Backend endpoints: {len(self.backend_endpoints)}")
        print(f"  Frontend API calls: {len(self.frontend_calls)}")
        print(f"  Issues found: {len(self.issues)}")
        
        if self.fix_mode and self.fixed:
            print(f"  Files fixed: {len(self.fixed)}")
        
        if len(self.issues) == 0:
            print(f"\n{Colors.GREEN}✅ INTEGRATION VALIDATED{Colors.RESET}")
            print(f"{Colors.GREEN}Frontend and backend are properly connected!{Colors.RESET}")
            return 0
        else:
            print(f"\n{Colors.YELLOW}⚠️  INTEGRATION ISSUES DETECTED{Colors.RESET}")
            print(f"{Colors.YELLOW}Fix the issues above or run with --fix{Colors.RESET}")
            return 1
    
    def save_report_json(self, filename='integration_report.json'):
        """Save report as JSON"""
        report = {
            'backend_endpoints': list(self.backend_endpoints),
            'frontend_calls': self.frontend_calls,
            'issues': self.issues,
            'fixed': self.fixed if self.fix_mode else [],
            'summary': {
                'backend_endpoints_count': len(self.backend_endpoints),
                'frontend_calls_count': len(self.frontend_calls),
                'issues_count': len(self.issues),
                'status': 'pass' if len(self.issues) == 0 else 'fail'
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log(f"Report saved to {filename}", "success")
    
    def run(self):
        """Run full validation"""
        print(f"\n{Colors.BOLD}{'*' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}🔗 ZERO-ERROR ARCHITECT - Integration Validator{Colors.RESET}")
        print(f"{Colors.BOLD}{'*' * 80}{Colors.RESET}\n")
        
        self.scan_backend_endpoints()
        self.scan_frontend_api_calls()
        self.validate_integration()
        
        if self.fix_mode:
            self.fix_port_mismatches()
        
        return self.generate_report()


def main():
    parser = argparse.ArgumentParser(description='Integration Validator')
    parser.add_argument('--fix', action='store_true', 
                       help='Auto-fix port mismatches')
    parser.add_argument('--report', action='store_true',
                       help='Save JSON report')
    parser.add_argument('--report-file', default='integration_report.json',
                       help='Report filename')
    
    args = parser.parse_args()
    
    validator = IntegrationValidator(fix_mode=args.fix)
    exit_code = validator.run()
    
    if args.report:
        validator.save_report_json(args.report_file)
    
    return exit_code


if __name__ == '__main__':
    import sys
    sys.exit(main())
