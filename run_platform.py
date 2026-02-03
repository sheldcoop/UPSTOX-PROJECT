#!/usr/bin/env python3
"""
UPSTOX Trading Platform - One-Click Launcher
Master script to start all services with health checks and dependency verification.

Usage:
    python run_platform.py              # Start all services
    python run_platform.py --check      # Health check only
    python run_platform.py --stop       # Stop all services
    python run_platform.py --setup      # First-time setup only
"""

import sys
import os
import subprocess
import time
import signal
import argparse
import json
import webbrowser
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
        """Install dependencies from requirements.txt"""
        python_exe = self.get_python_executable()
        requirements_file = self.project_root / "requirements.txt"
        
        try:
            self.print_step("Dependencies", "Installing from requirements.txt...", "running")
            subprocess.run(
                [python_exe, "-m", "pip", "install", "-r", str(requirements_file)],
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
        """Wait for service to become healthy"""
        service = self.services[service_key]
        
        if service["health_endpoint"] is None:
            time.sleep(2)  # Just wait a bit for services without health checks
            return True
        
        import requests
        
        self.print_step(service["name"], "Waiting for service to be ready...", "running")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(service["health_endpoint"], timeout=1)
                if response.status_code == 200:
                    self.print_step(service["name"], "Service is healthy ✓", "success")
                    return True
            except:
                pass
            time.sleep(1)
        
        self.print_step(service["name"], "Service health check timed out", "warning")
        return False

    def stop_all_services(self) -> None:
        """Stop all running services"""
        self.print_step("Shutdown", "Stopping all services...", "running")
        
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
        """Run health checks on all services"""
        self.print_header()
        self.print_step("Health Check", "Checking platform health...", "running")
        print()
        
        all_healthy = True
        for service_key, service in self.services.items():
            if service["health_endpoint"]:
                try:
                    import requests
                    response = requests.get(service["health_endpoint"], timeout=2)
                    if response.status_code == 200:
                        self.print_step(service["name"], f"Healthy on port {service['port']}", "success")
                    else:
                        self.print_step(service["name"], f"Unhealthy (status {response.status_code})", "error")
                        all_healthy = False
                except:
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
        
        # Step 5: Success message
        self.print_step("Step 5/5", "Platform Ready!", "success")
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
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            print("\n")
            self.stop_all_services()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n")
            self.stop_all_services()
        
        return True


def main():
    parser = argparse.ArgumentParser(description="UPSTOX Trading Platform - One-Click Launcher")
    parser.add_argument("--check", action="store_true", help="Run health check only")
    parser.add_argument("--stop", action="store_true", help="Stop all services")
    parser.add_argument("--setup", action="store_true", help="Run first-time setup only")
    
    args = parser.parse_args()
    
    launcher = PlatformLauncher()
    
    if args.check:
        success = launcher.run_health_check()
        sys.exit(0 if success else 1)
    elif args.stop:
        launcher.print_header()
        launcher.stop_all_services()
        print()
    elif args.setup:
        success = launcher.setup_only()
        sys.exit(0 if success else 1)
    else:
        success = launcher.run()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
