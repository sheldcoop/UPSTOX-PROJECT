#!/usr/bin/env python3
"""
Demo script to show what the monitoring dashboard looks like
This is a standalone demo - doesn't require services to be running
"""

import time
import os
from datetime import datetime

# ANSI color codes
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color
    BOLD = '\033[1m'

def format_uptime(seconds: float) -> str:
    """Format uptime in human-readable format"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds / 60)}m {int(seconds % 60)}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"

def print_demo_dashboard():
    """Print a demo of the monitoring dashboard"""
    # Clear screen
    os.system('clear')
    
    # Header
    print(f"\n{Colors.CYAN}{'='*80}{Colors.NC}")
    print(f"{Colors.BOLD}  📊 UPSTOX Trading Platform - Real-Time Status Dashboard{Colors.NC}")
    print(f"{Colors.CYAN}{'='*80}{Colors.NC}\n")
    
    # Current time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Colors.BLUE}⏰ Current Time: {Colors.BOLD}{current_time}{Colors.NC}\n")
    
    # Service status table
    print(f"{Colors.CYAN}{'─'*80}{Colors.NC}")
    print(f"{Colors.BOLD}{'SERVICE':<20} {'STATUS':<12} {'UPTIME':<15} {'RESTARTS':<10} {'PORT':<8}{Colors.NC}")
    print(f"{Colors.CYAN}{'─'*80}{Colors.NC}")
    
    # Demo data
    services = [
        ("API Server", "running", 323, 0, 8000),
        ("OAuth Server", "running", 322, 0, 5050),
        ("Frontend Dashboard", "running", 321, 1, 5001),
    ]
    
    for name, status, uptime_sec, restarts, port in services:
        uptime = format_uptime(uptime_sec)
        
        # Color code status
        if status == "running":
            status_colored = f"{Colors.GREEN}● {status.upper()}{Colors.NC}"
        elif status == "crashed":
            status_colored = f"{Colors.RED}● {status.upper()}{Colors.NC}"
        else:
            status_colored = f"{Colors.YELLOW}● {status.upper()}{Colors.NC}"
        
        # Color code restarts
        if restarts > 0:
            restarts_colored = f"{Colors.YELLOW}{restarts}{Colors.NC}"
        else:
            restarts_colored = f"{Colors.GREEN}{restarts}{Colors.NC}"
        
        print(f"{name:<20} {status_colored:<22} {uptime:<15} {restarts_colored:<20} {port:<8}")
    
    print(f"{Colors.CYAN}{'─'*80}{Colors.NC}\n")
    
    # Log file sizes
    print(f"{Colors.CYAN}📝 Log Files:{Colors.NC}")
    
    log_data = [
        ("API Server", 0.15, 1),
        ("OAuth Server", 0.08, 1),
        ("Frontend Dashboard", 0.02, 0),
    ]
    
    for name, size_mb, size_percent in log_data:
        # Color code based on size
        if size_percent > 80:
            size_colored = f"{Colors.RED}{size_mb:.2f}MB ({size_percent:.0f}%){Colors.NC}"
        elif size_percent > 50:
            size_colored = f"{Colors.YELLOW}{size_mb:.2f}MB ({size_percent:.0f}%){Colors.NC}"
        else:
            size_colored = f"{Colors.GREEN}{size_mb:.2f}MB ({size_percent:.0f}%){Colors.NC}"
        
        print(f"   • {name:<20} {size_colored}")
    
    print(f"\n{Colors.CYAN}{'─'*80}{Colors.NC}")
    print(f"{Colors.BLUE}💡 Press 's' for status, 'q' to quit, or Ctrl+C to stop all services{Colors.NC}")
    print(f"{Colors.CYAN}{'='*80}{Colors.NC}\n")

if __name__ == "__main__":
    print(f"\n{Colors.BOLD}{Colors.CYAN}Dashboard Demo - This is what the real-time monitoring looks like{Colors.NC}\n")
    print(f"{Colors.YELLOW}Note: This is a static demo. The real dashboard auto-refreshes every 5 seconds.{Colors.NC}\n")
    time.sleep(2)
    
    print_demo_dashboard()
    
    print(f"\n{Colors.GREEN}✅ This is what you'll see when you run:{Colors.NC}")
    print(f"   {Colors.BOLD}python3.11 run_platform.py{Colors.NC}")
    print(f"   {Colors.BOLD}python3.11 run_platform.py --dashboard{Colors.NC}\n")
