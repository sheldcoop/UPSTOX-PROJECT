#!/usr/bin/env python3
"""
UPSTOX Trading Platform - One-Click Launcher
Master script to start all services with health checks and dependency verification.

Usage:
    python run_platform.py                  # Start all services with real-time monitoring
    python run_platform.py --check          # Health check only
    python run_platform.py --stop           # Stop all services
    python run_platform.py --dashboard      # Show real-time monitoring dashboard
    python run_platform.py --setup          # First-time setup only
    python run_platform.py --reinstall      # Clean and reinstall environment
    python run_platform.py --clean          # Same as --reinstall

Features:
    - Real-time monitoring dashboard with auto-refresh
    - Automatic log rotation (10MB max, 5 backups)
    - Auto-restart crashed services
    - Service health checks and uptime tracking
"""

import sys
import os
import subprocess
import time
import signal
import argparse
import json
import webbrowser
import urllib.request
import urllib.error
import shutil
import platform
import threading
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Dict, Optional

# ANSI color codes
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color
    BOLD = '\033[1m'

class PlatformLauncher:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.logs_dir = self.project_root / "logs"
        self.venv_path = self.project_root / ".venv"
        self.processes: Dict[str, subprocess.Popen] = {}
        self.pid_files = {
            "api": self.logs_dir / "api.pid",
            "oauth": self.logs_dir / "oauth.pid",
            "frontend": self.logs_dir / "frontend.pid"
        }
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread = None
        self.service_stats = {
            "api": {"status": "stopped", "uptime": 0, "restarts": 0, "last_check": None},
            "oauth": {"status": "stopped", "uptime": 0, "restarts": 0, "last_check": None},
            "frontend": {"status": "stopped", "uptime": 0, "restarts": 0, "last_check": None}
        }
        self.start_times = {}
        
        # Log rotation configuration (10MB max per file, keep 5 backups)
        self.max_log_size = 10 * 1024 * 1024  # 10MB
        self.log_backup_count = 5
        
        # Service configuration
        self.services = {
            "api": {
                "name": "API Server",
                "command": ["python", "scripts/api_server.py"],
                "port": 8000,
                "health_endpoint": "http://localhost:8000/api/health",
                "log_file": self.logs_dir / "api_server.log"
            },
            "oauth": {
                "name": "OAuth Server",
                "command": ["python", "scripts/oauth_server.py"],
                "port": 5050,
                "health_endpoint": "http://localhost:5050/debug/config",
                "log_file": self.logs_dir / "oauth_server.log"
            },
            "frontend": {
                "name": "Frontend Dashboard",
                "command": ["python", "nicegui_dashboard.py"],
                "port": 5001,
                "health_endpoint": None,  # NiceGUI doesn't have built-in health endpoint
                "log_file": self.logs_dir / "nicegui_server.log"
            }
        }

    def print_header(self):
        """Print application header"""
        print(f"\n{Colors.CYAN}{'='*60}{Colors.NC}")
        print(f"{Colors.BOLD}  🚀 UPSTOX Trading Platform - One-Click Launcher{Colors.NC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.NC}\n")

    def print_step(self, step: str, message: str, status: str = "info"):
        """Print a formatted step message"""
        symbols = {
            "info": "📋",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "running": "⏳"
        }
        colors = {
            "info": Colors.BLUE,
            "success": Colors.GREEN,
            "warning": Colors.YELLOW,
            "error": Colors.RED,
            "running": Colors.CYAN
        }
        
        symbol = symbols.get(status, "•")
        color = colors.get(status, Colors.NC)
        print(f"{color}{symbol} {step}: {message}{Colors.NC}")

    def check_python_version(self) -> bool:
        """Check if Python version is 3.11 or higher"""
        version = sys.version_info
        self.print_step("Python Version", f"{version.major}.{version.minor}.{version.micro}", "info")
        
        if version.major == 3 and version.minor >= 11:
            self.print_step("Python Version", f"✓ Python {version.major}.{version.minor}+ is installed", "success")
            return True
        else:
            self.print_step("Python Version", f"Python 3.11+ required (found {version.major}.{version.minor})", "error")
            print()
            
            # Provide platform-specific instructions
            system = platform.system()
            if system == "Darwin":  # macOS
                print(f"{Colors.YELLOW}{'─'*60}{Colors.NC}")
                print(f"{Colors.BOLD}  💡 How to install Python 3.11+ on macOS:{Colors.NC}")
                print(f"{Colors.YELLOW}{'─'*60}{Colors.NC}")
                print(f"  1. Install using Homebrew:")
                print(f"     {Colors.CYAN}brew install python@3.11{Colors.NC}")
                print()
                print(f"  2. Then run this script with:")
                print(f"     {Colors.CYAN}python3.11 run_platform.py{Colors.NC}")
                print(f"{Colors.YELLOW}{'─'*60}{Colors.NC}\n")
            elif system == "Linux":
                print(f"{Colors.YELLOW}{'─'*60}{Colors.NC}")
                print(f"{Colors.BOLD}  💡 How to install Python 3.11+ on Linux:{Colors.NC}")
                print(f"{Colors.YELLOW}{'─'*60}{Colors.NC}")
                print(f"  Ubuntu/Debian:")
                print(f"     {Colors.CYAN}sudo apt update && sudo apt install python3.11{Colors.NC}")
                print()
                print(f"  Fedora/RHEL:")
                print(f"     {Colors.CYAN}sudo dnf install python3.11{Colors.NC}")
                print(f"{Colors.YELLOW}{'─'*60}{Colors.NC}\n")
            elif system == "Windows":
                print(f"{Colors.YELLOW}{'─'*60}{Colors.NC}")
                print(f"{Colors.BOLD}  💡 How to install Python 3.11+ on Windows:{Colors.NC}")
                print(f"{Colors.YELLOW}{'─'*60}{Colors.NC}")
                print(f"  Download from: {Colors.CYAN}https://www.python.org/downloads/{Colors.NC}")
                print(f"{Colors.YELLOW}{'─'*60}{Colors.NC}\n")
            
            return False

    def check_virtual_environment(self) -> bool:
        """Check if virtual environment exists"""
        if self.venv_path.exists():
            self.print_step("Virtual Environment", "Found at .venv/", "success")
            return True
        else:
            self.print_step("Virtual Environment", "Not found - creating...", "warning")
            return self.create_virtual_environment()

    def create_virtual_environment(self) -> bool:
        """Create virtual environment"""
        try:
            subprocess.run([sys.executable, "-m", "venv", str(self.venv_path)], check=True)
            self.print_step("Virtual Environment", "Created successfully", "success")
            return True
        except subprocess.CalledProcessError as e:
            self.print_step("Virtual Environment", f"Failed to create: {e}", "error")
            return False

    def get_python_executable(self) -> str:
        """Get the path to Python executable in virtual environment"""
        if sys.platform == "win32":
            return str(self.venv_path / "Scripts" / "python.exe")
        else:
            return str(self.venv_path / "bin" / "python")

    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        self.print_step("Dependencies", "Checking installation...", "running")
        
        python_exe = self.get_python_executable()
        requirements_file = self.project_root / "requirements.txt"
        
        if not requirements_file.exists():
            self.print_step("Dependencies", "requirements.txt not found", "error")
            return False
        
        try:
            # Check if dependencies are installed
            result = subprocess.run(
                [python_exe, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                check=True
            )
            installed_packages = {pkg["name"].lower() for pkg in json.loads(result.stdout)}
            
            # Read requirements
            with open(requirements_file) as f:
                required = {line.split("==")[0].split(">=")[0].lower().strip() 
                           for line in f if line.strip() and not line.startswith("#")}
            
            missing = required - installed_packages
            
            if missing:
                self.print_step("Dependencies", f"Installing {len(missing)} missing packages...", "warning")
                return self.install_dependencies()
            else:
                self.print_step("Dependencies", "All packages installed", "success")
                return True
                
        except Exception as e:
            self.print_step("Dependencies", f"Check failed: {e}", "warning")
            return self.install_dependencies()

    def install_dependencies(self) -> bool:
        """Install dependencies from requirements.txt using venv pip"""
        python_exe = self.get_python_executable()
        requirements_file = self.project_root / "requirements.txt"
        
        # Get pip from venv explicitly
        if sys.platform == "win32":
            pip_exe = str(self.venv_path / "Scripts" / "pip")
        else:
            pip_exe = str(self.venv_path / "bin" / "pip")
        
        try:
            self.print_step("Dependencies", "Installing from requirements.txt...", "running")
            # Use venv pip directly to ensure we don't use system pip
            subprocess.run(
                [pip_exe, "install", "-r", str(requirements_file)],
                check=True,
                cwd=str(self.project_root)
            )
            self.print_step("Dependencies", "Installed successfully", "success")
            return True
        except subprocess.CalledProcessError as e:
            self.print_step("Dependencies", f"Installation failed: {e}", "error")
            return False

    def check_environment_file(self) -> bool:
        """Check if .env file exists"""
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"
        
        if env_file.exists():
            self.print_step("Environment", ".env file found", "success")
            return True
        elif env_example.exists():
            self.print_step("Environment", "Creating .env from .env.example...", "warning")
            try:
                import shutil
                shutil.copy(env_example, env_file)
                self.print_step("Environment", ".env file created - PLEASE EDIT WITH YOUR CREDENTIALS", "warning")
                return True
            except Exception as e:
                self.print_step("Environment", f"Failed to create .env: {e}", "error")
                return False
        else:
            self.print_step("Environment", ".env and .env.example not found", "error")
            return False

    def setup_directories(self) -> bool:
        """Create required directories"""
        dirs = ["logs", "cache", "downloads"]
        
        for dir_name in dirs:
            dir_path = self.project_root / dir_name
            dir_path.mkdir(exist_ok=True)
        
        self.print_step("Directories", f"Created {', '.join(dirs)}/", "success")
        return True

    def setup_log_rotation(self, log_file: Path) -> RotatingFileHandler:
        """Setup rotating file handler for a log file"""
        handler = RotatingFileHandler(
            log_file,
            maxBytes=self.max_log_size,
            backupCount=self.log_backup_count,
            encoding='utf-8'
        )
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        return handler

    def rotate_logs_if_needed(self):
        """Check and rotate logs if they exceed size limit"""
        for service_key, service in self.services.items():
            log_file = service["log_file"]
            if log_file.exists():
                size = log_file.stat().st_size
                if size > self.max_log_size:
                    # Rotate the log
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_file = log_file.with_suffix(f".{timestamp}.log")
                    
                    # Keep only last N backups
                    backups = sorted(log_file.parent.glob(f"{log_file.stem}.*.log"))
                    if len(backups) >= self.log_backup_count:
                        for old_backup in backups[:-self.log_backup_count + 1]:
                            old_backup.unlink()
                    
                    # Rotate current log
                    shutil.move(str(log_file), str(backup_file))
                    self.print_step("Log Rotation", f"{service['name']}: {size / 1024 / 1024:.1f}MB → rotated", "info")

    def get_process_info(self, pid: int) -> Optional[Dict]:
        """Get process information (CPU, memory, uptime) - fallback without psutil"""
        try:
            # Check if process exists
            os.kill(pid, 0)
            
            # Try to get basic info using ps command (Unix-like systems)
            if sys.platform != "win32":
                result = subprocess.run(
                    ["ps", "-p", str(pid), "-o", "pid,pcpu,pmem,etime"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        parts = lines[1].split()
                        if len(parts) >= 4:
                            return {
                                "cpu_percent": float(parts[1]) if parts[1] != '-' else 0.0,
                                "memory_percent": float(parts[2]) if parts[2] != '-' else 0.0,
                                "uptime": parts[3]
                            }
            
            # Fallback: just confirm process exists
            return {
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "uptime": "unknown"
            }
        except (OSError, ProcessLookupError):
            return None

    def monitor_services(self):
        """Background thread to monitor service health"""
        while self.monitoring_active:
            try:
                for service_key in self.services.keys():
                    if service_key in self.processes:
                        process = self.processes[service_key]
                        
                        # Check if process is still running
                        if process.poll() is not None:
                            # Process died
                            self.service_stats[service_key]["status"] = "crashed"
                            self.print_step(
                                self.services[service_key]["name"],
                                "Process crashed - attempting restart...",
                                "error"
                            )
                            # Auto-restart
                            self.start_service(service_key)
                            self.service_stats[service_key]["restarts"] += 1
                        else:
                            # Process is running
                            self.service_stats[service_key]["status"] = "running"
                            
                            # Calculate uptime
                            if service_key in self.start_times:
                                uptime = time.time() - self.start_times[service_key]
                                self.service_stats[service_key]["uptime"] = uptime
                        
                        self.service_stats[service_key]["last_check"] = datetime.now()
                
                # Rotate logs if needed
                self.rotate_logs_if_needed()
                
                # Sleep for 5 seconds between checks
                time.sleep(5)
                
            except Exception as e:
                # Silently continue on errors
                time.sleep(5)

    def start_monitoring(self):
        """Start the monitoring thread"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self.monitor_services, daemon=True)
            self.monitoring_thread.start()
            self.print_step("Monitoring", "Real-time monitoring started", "success")

    def stop_monitoring(self):
        """Stop the monitoring thread"""
        if self.monitoring_active:
            self.monitoring_active = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=2)
            self.print_step("Monitoring", "Monitoring stopped", "info")

    def format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m {int(seconds % 60)}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"

    def print_status_dashboard(self):
        """Print real-time status dashboard"""
        # Clear screen (cross-platform)
        os.system('cls' if os.name == 'nt' else 'clear')
        
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
        
        for service_key, service in self.services.items():
            stats = self.service_stats[service_key]
            status = stats["status"]
            uptime = self.format_uptime(stats["uptime"]) if stats["uptime"] > 0 else "-"
            restarts = stats["restarts"]
            port = service["port"]
            
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
            
            print(f"{service['name']:<20} {status_colored:<22} {uptime:<15} {restarts_colored:<20} {port:<8}")
        
        print(f"{Colors.CYAN}{'─'*80}{Colors.NC}\n")
        
        # Log file sizes
        print(f"{Colors.CYAN}📝 Log Files:{Colors.NC}")
        for service_key, service in self.services.items():
            log_file = service["log_file"]
            if log_file.exists():
                size_mb = log_file.stat().st_size / 1024 / 1024
                size_percent = (log_file.stat().st_size / self.max_log_size) * 100
                
                # Color code based on size
                if size_percent > 80:
                    size_colored = f"{Colors.RED}{size_mb:.2f}MB ({size_percent:.0f}%){Colors.NC}"
                elif size_percent > 50:
                    size_colored = f"{Colors.YELLOW}{size_mb:.2f}MB ({size_percent:.0f}%){Colors.NC}"
                else:
                    size_colored = f"{Colors.GREEN}{size_mb:.2f}MB ({size_percent:.0f}%){Colors.NC}"
                
                print(f"   • {service['name']:<20} {size_colored}")
            else:
                print(f"   • {service['name']:<20} {Colors.YELLOW}No log file{Colors.NC}")
        
        print(f"\n{Colors.CYAN}{'─'*80}{Colors.NC}")
        print(f"{Colors.BLUE}💡 Press 's' for status, 'q' to quit, or Ctrl+C to stop all services{Colors.NC}")
        print(f"{Colors.CYAN}{'='*80}{Colors.NC}\n")

    def interactive_dashboard(self):
        """Run interactive dashboard with keyboard controls"""
        import select
        import tty
        import termios
        
        # Save terminal settings
        old_settings = termios.tcgetattr(sys.stdin)
        
        try:
            # Set terminal to raw mode for immediate key detection
            tty.setcbreak(sys.stdin.fileno())
            
            while True:
                # Print dashboard
                self.print_status_dashboard()
                
                # Check for keyboard input (non-blocking)
                if select.select([sys.stdin], [], [], 5)[0]:
                    key = sys.stdin.read(1)
                    
                    if key.lower() == 'q':
                        break
                    elif key.lower() == 's':
                        # Refresh immediately
                        continue
                else:
                    # Auto-refresh every 5 seconds
                    continue
                    
        except KeyboardInterrupt:
            pass
        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    def clean_environment(self) -> bool:
        """Clean virtual environment and cached files for fresh reinstall"""
        self.print_header()
        self.print_step("Cleanup", "Starting environment cleanup...", "running")
        print()
        
        cleaned_items = []
        
        # Remove .venv directory
        if self.venv_path.exists():
            try:
                self.print_step("Virtual Environment", "Removing .venv/", "running")
                shutil.rmtree(self.venv_path)
                cleaned_items.append(".venv/")
                self.print_step("Virtual Environment", "Removed successfully", "success")
            except Exception as e:
                self.print_step("Virtual Environment", f"Failed to remove: {e}", "error")
                return False
        else:
            self.print_step("Virtual Environment", "Not found (already clean)", "info")
        
        # Remove __pycache__ directories
        pycache_count = 0
        for pycache_dir in self.project_root.rglob("__pycache__"):
            try:
                shutil.rmtree(pycache_dir)
                pycache_count += 1
            except Exception:
                pass
        
        if pycache_count > 0:
            cleaned_items.append(f"{pycache_count} __pycache__ directories")
            self.print_step("Cache", f"Removed {pycache_count} __pycache__ directories", "success")
        else:
            self.print_step("Cache", "No __pycache__ directories found", "info")
        
        # Remove .pyc files
        pyc_count = 0
        for pyc_file in self.project_root.rglob("*.pyc"):
            try:
                pyc_file.unlink()
                pyc_count += 1
            except Exception:
                pass
        
        if pyc_count > 0:
            cleaned_items.append(f"{pyc_count} .pyc files")
            self.print_step("Cache", f"Removed {pyc_count} .pyc files", "success")
        else:
            self.print_step("Cache", "No .pyc files found", "info")
        
        print()
        self.print_step("Cleanup", f"Environment cleaned successfully!", "success")
        print()
        
        if cleaned_items:
            print(f"{Colors.CYAN}📦 Cleaned:{Colors.NC}")
            for item in cleaned_items:
                print(f"   • {item}")
            print()
        
        return True

    def kill_port(self, port: int) -> None:
        """Kill process using specified port"""
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["powershell", "-Command", f"Get-Process -Id (Get-NetTCPConnection -LocalPort {port}).OwningProcess | Stop-Process -Force"],
                    check=False,
                    stderr=subprocess.DEVNULL
                )
            else:
                result = subprocess.run(
                    ["lsof", "-ti", f":{port}"],
                    capture_output=True,
                    text=True
                )
                if result.stdout:
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        subprocess.run(["kill", "-9", pid], check=False)
        except Exception:
            pass  # Ignore errors

    def start_service(self, service_key: str) -> bool:
        """Start a single service"""
        service = self.services[service_key]
        
        # Kill existing process on port
        self.kill_port(service["port"])
        time.sleep(0.5)
        
        # Get Python executable from venv
        python_exe = self.get_python_executable()
        command = [python_exe] + service["command"][1:]  # Replace 'python' with venv python
        
        try:
            # Open log file
            log_file = open(service["log_file"], "w")
            
            # Start process
            process = subprocess.Popen(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=str(self.project_root)
            )
            
            self.processes[service_key] = process
            
            # Track start time for uptime calculation
            self.start_times[service_key] = time.time()
            self.service_stats[service_key]["status"] = "starting"
            
            # Save PID
            with open(self.pid_files[service_key], "w") as f:
                f.write(str(process.pid))
            
            self.print_step(
                service["name"],
                f"Started on port {service['port']} (PID: {process.pid})",
                "success"
            )
            return True
            
        except Exception as e:
            self.print_step(service["name"], f"Failed to start: {e}", "error")
            return False

    def wait_for_service(self, service_key: str, timeout: int = 30) -> bool:
        """Wait for service to become healthy using stdlib urllib"""
        service = self.services[service_key]
        
        if service["health_endpoint"] is None:
            time.sleep(2)  # Just wait a bit for services without health checks
            return True
        
        self.print_step(service["name"], "Waiting for service to be ready...", "running")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Use urllib.request instead of requests (stdlib only)
                req = urllib.request.Request(service["health_endpoint"])
                with urllib.request.urlopen(req, timeout=1) as response:
                    if response.status == 200:
                        self.print_step(service["name"], "Service is healthy ✓", "success")
                        return True
            except (urllib.error.URLError, urllib.error.HTTPError, OSError):
                pass
            time.sleep(1)
        
        self.print_step(service["name"], "Service health check timed out", "warning")
        return False

    def stop_all_services(self) -> None:
        """Stop all running services"""
        self.print_step("Shutdown", "Stopping all services...", "running")
        
        # Stop monitoring first
        self.stop_monitoring()
        
        # Stop processes
        for service_key, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                self.print_step(self.services[service_key]["name"], "Stopped", "success")
            except:
                try:
                    process.kill()
                except:
                    pass
        
        # Clean up PID files
        for pid_file in self.pid_files.values():
            if pid_file.exists():
                pid_file.unlink()
        
        # Also try to kill by port
        for service in self.services.values():
            self.kill_port(service["port"])

    def run_health_check(self) -> bool:
        """Run health checks on all services using stdlib urllib"""
        self.print_header()
        self.print_step("Health Check", "Checking platform health...", "running")
        print()
        
        all_healthy = True
        for service_key, service in self.services.items():
            if service["health_endpoint"]:
                try:
                    # Use urllib.request instead of requests (stdlib only)
                    req = urllib.request.Request(service["health_endpoint"])
                    with urllib.request.urlopen(req, timeout=2) as response:
                        if response.status == 200:
                            self.print_step(service["name"], f"Healthy on port {service['port']}", "success")
                        else:
                            self.print_step(service["name"], f"Unhealthy (status {response.status})", "error")
                            all_healthy = False
                except (urllib.error.URLError, urllib.error.HTTPError, OSError):
                    self.print_step(service["name"], "Not responding", "error")
                    all_healthy = False
            else:
                # Check if process is running
                if self.pid_files[service_key].exists():
                    with open(self.pid_files[service_key]) as f:
                        pid = int(f.read().strip())
                    try:
                        os.kill(pid, 0)  # Check if process exists
                        self.print_step(service["name"], f"Running (PID {pid})", "success")
                    except:
                        self.print_step(service["name"], "Not running", "error")
                        all_healthy = False
                else:
                    self.print_step(service["name"], "Not running", "error")
                    all_healthy = False
        
        print()
        return all_healthy

    def setup_only(self) -> bool:
        """Run first-time setup without starting services"""
        self.print_header()
        self.print_step("Setup", "Running first-time setup...", "running")
        print()
        
        if not self.check_python_version():
            return False
        
        if not self.check_virtual_environment():
            return False
        
        if not self.check_dependencies():
            return False
        
        if not self.check_environment_file():
            return False
        
        if not self.setup_directories():
            return False
        
        print()
        self.print_step("Setup", "Setup completed successfully!", "success")
        print()
        return True

    def run_zero_error_checks(self) -> bool:
        """Run Zero-Error Architect health and preflight checks"""
        self.print_step("Zero-Error Checks", "Running comprehensive validation...", "running")
        print()
        
        # Run health check
        health_check_script = self.project_root / "scripts" / "check_health.py"
        if health_check_script.exists():
            python_exe = self.get_python_executable()
            try:
                self.print_step("Health Check", "Validating system health...", "running")
                result = subprocess.run(
                    [python_exe, str(health_check_script), "--quick"],
                    capture_output=True,
                    text=True,
                    cwd=str(self.project_root)
                )
                if result.returncode == 0:
                    self.print_step("Health Check", "System health validated ✓", "success")
                elif result.returncode == 1:
                    self.print_step("Health Check", "Passed with warnings", "warning")
                else:
                    self.print_step("Health Check", "Failed - check issues above", "error")
                    return False
            except Exception as e:
                self.print_step("Health Check", f"Failed to run: {e}", "error")
                return False
        
        # Run preflight check
        preflight_script = self.project_root / "scripts" / "preflight_check.py"
        if preflight_script.exists():
            try:
                self.print_step("Preflight Check", "Running pre-flight safety checks...", "running")
                result = subprocess.run(
                    [python_exe, str(preflight_script)],
                    capture_output=True,
                    text=True,
                    cwd=str(self.project_root)
                )
                if result.returncode == 0:
                    self.print_step("Preflight Check", "Pre-flight checks passed ✓", "success")
                elif result.returncode == 1:
                    self.print_step("Preflight Check", "Passed with warnings", "warning")
                else:
                    self.print_step("Preflight Check", "Failed - check issues above", "error")
                    return False
            except Exception as e:
                self.print_step("Preflight Check", f"Failed to run: {e}", "error")
                return False
        
        print()
        return True

    def run(self) -> bool:
        """Main execution flow"""
        self.print_header()
        
        # Step 1: Environment checks
        self.print_step("Step 1/5", "Environment Verification", "running")
        print()
        
        if not self.check_python_version():
            return False
        
        if not self.check_virtual_environment():
            return False
        
        if not self.check_dependencies():
            return False
        
        if not self.check_environment_file():
            return False
        
        if not self.setup_directories():
            return False
        
        print()
        
        # Step 2: Zero-Error Architect validation
        self.print_step("Step 2/5", "Zero-Error Validation", "running")
        print()
        
        if not self.run_zero_error_checks():
            self.print_step("Validation", "Zero-Error checks failed - fix issues before proceeding", "error")
            return False
        
        print()
        
        # Step 3: Start services
        self.print_step("Step 3/5", "Starting Services", "running")
        print()
        
        for service_key in ["api", "oauth", "frontend"]:
            if not self.start_service(service_key):
                self.stop_all_services()
                return False
            time.sleep(1)
        
        print()
        
        # Step 4: Health checks
        self.print_step("Step 4/5", "Health Checks", "running")
        print()
        
        time.sleep(3)  # Give services time to start
        
        for service_key in ["api", "oauth"]:  # Skip frontend health check
            self.wait_for_service(service_key)
        
        print()
        
        # Step 5: Start monitoring
        self.print_step("Step 5/5", "Starting Monitoring & Dashboard", "running")
        print()
        
        # Start background monitoring
        self.start_monitoring()
        
        print()
        
        print(f"{Colors.GREEN}{'='*60}{Colors.NC}")
        print(f"{Colors.BOLD}  🎉 All services started successfully!{Colors.NC}")
        print(f"{Colors.GREEN}{'='*60}{Colors.NC}\n")
        
        print(f"{Colors.CYAN}📍 Access Points:{Colors.NC}")
        print(f"   🌐 Frontend Dashboard: {Colors.BOLD}http://localhost:5001{Colors.NC}")
        print(f"   📡 API Server:         {Colors.BOLD}http://localhost:8000{Colors.NC}")
        print(f"   🔐 OAuth Service:      {Colors.BOLD}http://localhost:5050{Colors.NC}\n")
        
        print(f"{Colors.CYAN}📝 Logs:{Colors.NC}")
        for service_key, service in self.services.items():
            print(f"   • {service['name']}: tail -f {service['log_file']}")
        print()
        
        print(f"{Colors.CYAN}🛑 To stop:{Colors.NC}")
        print(f"   python run_platform.py --stop")
        print(f"   Or press Ctrl+C\n")
        
        print(f"{Colors.GREEN}{'='*60}{Colors.NC}\n")
        
        # Open browser
        try:
            time.sleep(2)
            webbrowser.open("http://localhost:5001")
            self.print_step("Browser", "Opening http://localhost:5001", "success")
        except:
            pass
        
        print()
        print(f"{Colors.CYAN}{'='*60}{Colors.NC}")
        print(f"{Colors.BOLD}  📊 Launching Real-Time Status Dashboard...{Colors.NC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.NC}\n")
        print(f"{Colors.YELLOW}⏳ Starting dashboard in 3 seconds...{Colors.NC}\n")
        time.sleep(3)
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            print("\n")
            self.stop_all_services()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run interactive dashboard
        try:
            self.interactive_dashboard()
        except KeyboardInterrupt:
            print("\n")
        finally:
            self.stop_all_services()
        
        return True


def main():
    parser = argparse.ArgumentParser(description="UPSTOX Trading Platform - One-Click Launcher")
    parser.add_argument("--check", action="store_true", help="Run health check only")
    parser.add_argument("--stop", action="store_true", help="Stop all services")
    parser.add_argument("--setup", action="store_true", help="Run first-time setup only")
    parser.add_argument("--dashboard", action="store_true", help="Show real-time monitoring dashboard for running services")
    parser.add_argument("--reinstall", "--clean", dest="reinstall", action="store_true",
                        help="Clean environment and reinstall (removes .venv, __pycache__, and .pyc files)")
    
    args = parser.parse_args()
    
    launcher = PlatformLauncher()
    
    if args.check:
        success = launcher.run_health_check()
        sys.exit(0 if success else 1)
    elif args.stop:
        launcher.print_header()
        launcher.stop_all_services()
        print()
    elif args.dashboard:
        # Show dashboard for running services
        launcher.print_header()
        
        # Load running processes from PID files
        for service_key in launcher.services.keys():
            pid_file = launcher.pid_files[service_key]
            if pid_file.exists():
                try:
                    with open(pid_file) as f:
                        pid = int(f.read().strip())
                    # Check if process is still running
                    os.kill(pid, 0)
                    # Create a mock process object
                    launcher.processes[service_key] = type('obj', (object,), {'pid': pid, 'poll': lambda: None})()
                    launcher.start_times[service_key] = time.time() - 60  # Assume started 60s ago
                    launcher.service_stats[service_key]["status"] = "running"
                except (OSError, ProcessLookupError, ValueError):
                    launcher.service_stats[service_key]["status"] = "stopped"
        
        # Start monitoring
        launcher.start_monitoring()
        
        # Run dashboard
        try:
            launcher.interactive_dashboard()
        except KeyboardInterrupt:
            pass
        finally:
            launcher.stop_monitoring()
        
        print()
    elif args.reinstall:
        # Clean environment first
        if not launcher.clean_environment():
            sys.exit(1)
        # Then run setup
        success = launcher.setup_only()
        sys.exit(0 if success else 1)
    elif args.setup:
        success = launcher.setup_only()
        sys.exit(0 if success else 1)
    else:
        success = launcher.run()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
