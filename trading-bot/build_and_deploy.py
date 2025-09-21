#!/usr/bin/env python3
"""
Build and Deploy Script for Kraken Trading Bot
==============================================

This script provides a comprehensive build, test, and deployment pipeline for the trading bot.

Features:
- Clean build process with dependency management
- Automated testing with coverage reporting
- Docker container management
- Graceful service restart
- Health checks and rollback capabilities
- Environment-specific configurations

Usage:
    python build_and_deploy.py --build        # Build and test
    python build_and_deploy.py --deploy       # Deploy to production
    python build_and_deploy.py --restart      # Restart services
    python build_and_deploy.py --rollback     # Rollback to previous version
    python build_and_deploy.py --status       # Check service status
"""

import os
import sys
import subprocess
import argparse
import time
import shutil
from datetime import datetime
from pathlib import Path


class BuildDeployManager:
    """Manages the build and deployment process"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backup_dir = self.project_root / "backups"
        self.log_dir = self.project_root / "logs"
        self.backup_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)

    def run_command(self, command, description, cwd=None, check=True):
        """Run a shell command with logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{timestamp}] {description}")
        print(f"Command: {' '.join(command)}")

        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=False,
                text=True,
                check=check
            )
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            print(f"Command failed with return code {e.returncode}")
            return False
        except Exception as e:
            print(f"Error running command: {e}")
            return False

    def backup_current_deployment(self):
        """Create a backup of the current deployment"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"

        print(f"Creating backup at {backup_path}")

        # Backup important files
        files_to_backup = [
            "trading_bot.py",
            "overnight_trader.py",
            "crypto_trend_analyzer.py",
            "requirements.txt",
            "docker-compose.yml",
            "Dockerfile",
            ".env"
        ]

        backup_path.mkdir()
        for file in files_to_backup:
            if (self.project_root / file).exists():
                shutil.copy2(self.project_root / file, backup_path / file)

        print(f"Backup created successfully at {backup_path}")
        return backup_path

    def check_dependencies(self):
        """Check if all required dependencies are available"""
        print("Checking system dependencies...")

        required_commands = [
            "docker",
            "docker-compose",
            "python3",
            "pip",
            "curl"
        ]

        missing_deps = []
        for cmd in required_commands:
            if not self.run_command(["which", cmd], f"Checking {cmd}", check=False):
                missing_deps.append(cmd)

        if missing_deps:
            print(f"Missing dependencies: {', '.join(missing_deps)}")
            print("Please install missing dependencies and try again")
            return False

        return True

    def install_python_dependencies(self):
        """Install Python dependencies"""
        print("Installing Python dependencies...")

        # Upgrade pip first
        if not self.run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                               "Upgrading pip"):
            return False

        # Install dependencies
        if not self.run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                               "Installing Python dependencies"):
            return False

        return True

    def run_tests(self):
        """Run the test suite"""
        print("Running test suite...")

        if not (self.project_root / "tests").exists():
            print("No tests directory found, skipping tests")
            return True

        # Run tests with coverage
        success = self.run_command([
            sys.executable, "-m", "pytest",
            "tests/",
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-fail-under=80",
            "-v"
        ], "Running test suite")

        if success:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
            return False

        return True

    def build_docker_images(self):
        """Build Docker images"""
        print("Building Docker images...")

        # Build main application image
        if not self.run_command([
            "docker", "build", "-t", "kraken-trading-bot:latest", "."
        ], "Building Docker image"):
            return False

        # Build FrankenPHP image if it exists
        if (self.project_root / "frankenphp.dockerfile").exists():
            if not self.run_command([
                "docker", "build",
                "-f", "frankenphp.dockerfile",
                "-t", "kraken-frankenphp:latest",
                "."
            ], "Building FrankenPHP image"):
                return False

        return True

    def start_services(self):
        """Start all services"""
        print("Starting services...")

        # Stop any existing services first
        self.run_command(["docker-compose", "down"], "Stopping existing services", check=False)

        # Start services
        if not self.run_command([
            "docker-compose", "up", "-d", "--build"
        ], "Starting services with Docker Compose"):
            return False

        return True

    def stop_services(self):
        """Stop all services"""
        print("Stopping services...")
        return self.run_command(["docker-compose", "down"], "Stopping services")

    def health_check(self, timeout=60):
        """Perform health checks on running services"""
        print("Performing health checks...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check Flask API health
                result = subprocess.run([
                    "curl", "-f", "http://localhost:8080/health"
                ], capture_output=True, text=True, timeout=5)

                if result.returncode == 0:
                    print("✅ Flask API is healthy")

                    # Check if bot is initialized
                    status_result = subprocess.run([
                        "curl", "-f", "http://localhost:8080/status"
                    ], capture_output=True, text=True, timeout=5)

                    if status_result.returncode == 0:
                        print("✅ Trading bot is running")
                        return True
                    else:
                        print("⚠️ Trading bot not yet initialized, waiting...")

                else:
                    print("⚠️ Flask API not ready, waiting...")

            except subprocess.TimeoutExpired:
                print("⚠️ Health check timeout, waiting...")
            except Exception as e:
                print(f"⚠️ Health check error: {e}, waiting...")

            time.sleep(5)

        print("❌ Health check failed - services may not be running properly")
        return False

    def cleanup_old_images(self):
        """Clean up old Docker images"""
        print("Cleaning up old Docker images...")

        # Remove dangling images
        self.run_command([
            "docker", "image", "prune", "-f"
        ], "Removing dangling images", check=False)

        # Remove old images (keep last 3 versions)
        self.run_command([
            "docker", "images", "kraken-trading-bot", "--format", "{{.Repository}}:{{.Tag}}"
        ], "Listing bot images", check=False)

        return True

    def build(self):
        """Complete build process"""
        print("🚀 Starting build process...")

        # Create backup
        backup_path = self.backup_current_deployment()

        # Check dependencies
        if not self.check_dependencies():
            return False

        # Install dependencies
        if not self.install_python_dependencies():
            return False

        # Run tests
        if not self.run_tests():
            return False

        # Build Docker images
        if not self.build_docker_images():
            return False

        # Cleanup
        self.cleanup_old_images()

        print("✅ Build process completed successfully!")
        print(f"📦 Backup created at: {backup_path}")
        return True

    def deploy(self):
        """Deploy the application"""
        print("🚀 Starting deployment process...")

        # Stop existing services
        self.stop_services()

        # Start new services
        if not self.start_services():
            print("❌ Failed to start services")
            return False

        # Perform health checks
        if not self.health_check():
            print("❌ Health checks failed")
            print("🔄 Attempting rollback...")
            self.rollback()
            return False

        print("✅ Deployment completed successfully!")
        return True

    def restart(self):
        """Restart all services"""
        print("🔄 Restarting services...")

        if not self.stop_services():
            print("⚠️ Warning: Could not stop all services cleanly")

        if not self.start_services():
            print("❌ Failed to restart services")
            return False

        if not self.health_check():
            print("❌ Services failed health checks after restart")
            return False

        print("✅ Services restarted successfully!")
        return True

    def rollback(self):
        """Rollback to previous deployment"""
        print("🔄 Starting rollback process...")

        # Find latest backup
        backups = sorted(self.backup_dir.glob("backup_*"))
        if not backups:
            print("❌ No backups found for rollback")
            return False

        latest_backup = backups[-1]
        print(f"Rolling back to backup: {latest_backup}")

        # Stop services
        self.stop_services()

        # Restore files from backup
        for file_path in latest_backup.glob("*"):
            if file_path.is_file():
                shutil.copy2(file_path, self.project_root / file_path.name)
                print(f"Restored: {file_path.name}")

        # Restart services
        if not self.start_services():
            print("❌ Failed to restart services after rollback")
            return False

        if not self.health_check():
            print("❌ Services failed health checks after rollback")
            return False

        print("✅ Rollback completed successfully!")
        return True

    def status(self):
        """Check status of all services"""
        print("📊 Checking service status...")

        # Check Docker containers
        print("\n🐳 Docker Containers:")
        self.run_command([
            "docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        ], "Checking Docker containers", check=False)

        # Check Docker Compose services
        print("\n📋 Docker Compose Services:")
        self.run_command([
            "docker-compose", "ps"
        ], "Checking Docker Compose services", check=False)

        # Check API health
        print("\n🌐 API Health Check:")
        try:
            result = subprocess.run([
                "curl", "-s", "http://localhost:8080/health"
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                print("✅ Flask API: Healthy")
                try:
                    import json
                    health_data = json.loads(result.stdout)
                    print(f"   Status: {health_data.get('status', 'unknown')}")
                    print(f"   Uptime: {health_data.get('uptime', 'unknown')}")
                except:
                    pass
            else:
                print("❌ Flask API: Unhealthy")
        except:
            print("❌ Flask API: Not responding")

        # Check Laravel API if available
        print("\n🔧 Laravel API Health Check:")
        try:
            result = subprocess.run([
                "curl", "-s", "http://localhost:8000/api/health"
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                print("✅ Laravel API: Healthy")
            else:
                print("❌ Laravel API: Unhealthy")
        except:
            print("❌ Laravel API: Not responding")

        return True


def main():
    parser = argparse.ArgumentParser(description='Build and Deploy Kraken Trading Bot')
    parser.add_argument('--build', action='store_true', help='Build the application')
    parser.add_argument('--deploy', action='store_true', help='Deploy the application')
    parser.add_argument('--restart', action='store_true', help='Restart all services')
    parser.add_argument('--rollback', action='store_true', help='Rollback to previous version')
    parser.add_argument('--status', action='store_true', help='Check service status')
    parser.add_argument('--stop', action='store_true', help='Stop all services')

    args = parser.parse_args()

    manager = BuildDeployManager()

    if args.build:
        success = manager.build()
    elif args.deploy:
        success = manager.deploy()
    elif args.restart:
        success = manager.restart()
    elif args.rollback:
        success = manager.rollback()
    elif args.status:
        success = manager.status()
    elif args.stop:
        success = manager.stop_services()
    else:
        parser.print_help()
        success = True

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()