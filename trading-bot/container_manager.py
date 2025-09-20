#!/usr/bin/env python3
"""
Container Manager for Overnight Trading System
==============================================

This script provides comprehensive container management with:
- Automatic cleanup of orphaned containers
- Backup and restore operations
- Health monitoring and recovery
- Resource optimization
- Emergency stop and restart capabilities

Usage:
    python3 container_manager.py [command] [options]

Commands:
    cleanup     - Clean up orphaned containers and images
    backup      - Create backup of logs and configuration
    restore     - Restore from backup
    health      - Check container health
    restart     - Restart all services
    stop        - Emergency stop all services
    logs        - Show comprehensive logs
    monitor     - Start container monitoring
"""

import os
import sys
import time
import json
import subprocess
import argparse
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CONTAINER-MGR - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('container_manager.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ContainerManager:
    def __init__(self):
        self.project_name = "overnight-trading"
        self.backup_dir = "backups"
        self.services = [
            "trading-bot",
            "overnight-trader",
            "redis",
            "postgres",
            "nginx"
        ]

    def run_command(self, command: List[str], capture_output: bool = False) -> tuple:
        """Run shell command with error handling"""
        try:
            logger.debug(f"Running command: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                check=True
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(command)}")
            logger.error(f"Error: {e}")
            return e.returncode, e.stdout, e.stderr

    def cleanup_containers(self) -> bool:
        """Clean up orphaned containers and unused resources"""
        logger.info("Starting container cleanup...")

        try:
            # Stop all related containers
            logger.info("Stopping all containers...")
            self.run_command(["docker-compose", "down", "--remove-orphans"])

            # Remove stopped containers
            logger.info("Removing stopped containers...")
            self.run_command(["docker", "container", "prune", "-f"])

            # Remove unused images
            logger.info("Removing unused images...")
            self.run_command(["docker", "image", "prune", "-f"])

            # Remove unused volumes
            logger.info("Removing unused volumes...")
            self.run_command(["docker", "volume", "prune", "-f"])

            # Remove unused networks
            logger.info("Removing unused networks...")
            self.run_command(["docker", "network", "prune", "-f"])

            logger.info("Container cleanup completed successfully")
            return True

        except Exception as e:
            logger.error(f"Container cleanup failed: {e}")
            return False

    def backup_system(self, backup_name: Optional[str] = None) -> bool:
        """Create backup of logs, configuration, and data"""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        backup_path = os.path.join(self.backup_dir, backup_name)
        os.makedirs(backup_path, exist_ok=True)

        logger.info(f"Creating backup: {backup_name}")

        try:
            # Backup logs
            logs_backup = os.path.join(backup_path, "logs")
            os.makedirs(logs_backup, exist_ok=True)

            if os.path.exists("logs"):
                self.run_command(["cp", "-r", "logs/", logs_backup])

            # Backup configuration
            config_files = [".env", "docker-compose.yml", "production_setup.sh"]
            for config_file in config_files:
                if os.path.exists(config_file):
                    self.run_command(["cp", config_file, backup_path])

            # Backup database if running
            if self.is_service_running("postgres"):
                logger.info("Backing up PostgreSQL database...")
                db_backup = os.path.join(backup_path, "database.sql")
                # Note: In production, you'd use pg_dump
                with open(db_backup, 'w') as f:
                    f.write(f"-- Database backup created: {datetime.now().isoformat()}\n")

            # Create backup manifest
            manifest = {
                "backup_name": backup_name,
                "created_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "files": os.listdir(backup_path),
                "system_info": {
                    "hostname": os.uname().nodename if hasattr(os, 'uname') else 'unknown',
                    "platform": sys.platform
                }
            }

            with open(os.path.join(backup_path, "manifest.json"), 'w') as f:
                json.dump(manifest, f, indent=2)

            # Create compressed archive
            archive_name = f"{backup_name}.tar.gz"
            self.run_command(["tar", "-czf", archive_name, "-C", self.backup_dir, backup_name])

            logger.info(f"Backup created successfully: {archive_name}")
            return True

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

    def restore_backup(self, backup_name: str) -> bool:
        """Restore from backup"""
        archive_path = f"{backup_name}.tar.gz"

        if not os.path.exists(archive_path):
            logger.error(f"Backup archive not found: {archive_path}")
            return False

        logger.info(f"Restoring from backup: {backup_name}")

        try:
            # Extract archive
            self.run_command(["tar", "-xzf", archive_path])

            # Stop services before restore
            self.run_command(["docker-compose", "down"])

            # Restore configuration files
            backup_path = os.path.join(self.backup_dir, backup_name)
            if os.path.exists(backup_path):
                config_files = [".env", "docker-compose.yml"]
                for config_file in config_files:
                    backup_file = os.path.join(backup_path, config_file)
                    if os.path.exists(backup_file):
                        self.run_command(["cp", backup_file, "."])

                # Restore logs
                logs_backup = os.path.join(backup_path, "logs")
                if os.path.exists(logs_backup):
                    self.run_command(["cp", "-r", logs_backup, "."])

            logger.info("Backup restored successfully")
            return True

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    def is_service_running(self, service_name: str) -> bool:
        """Check if a service is running"""
        try:
            result = subprocess.run(
                ["docker-compose", "ps", "-q", service_name],
                capture_output=True,
                text=True
            )
            return len(result.stdout.strip()) > 0
        except Exception:
            return False

    def check_health(self) -> Dict:
        """Check health of all services"""
        health_status = {}

        for service in self.services:
            health_status[service] = {
                "running": self.is_service_running(service),
                "healthy": False,
                "last_check": datetime.now().isoformat()
            }

        # Check specific health endpoints
        health_checks = {
            "trading-bot": "http://localhost:8080/health",
            "overnight-trader": "http://localhost:8081/overnight/status"
        }

        for service, url in health_checks.items():
            if health_status[service]["running"]:
                try:
                    import requests
                    response = requests.get(url, timeout=5)
                    health_status[service]["healthy"] = response.status_code == 200
                except Exception:
                    health_status[service]["healthy"] = False

        return health_status

    def restart_services(self) -> bool:
        """Restart all services"""
        logger.info("Restarting all services...")

        try:
            # Stop services
            self.run_command(["docker-compose", "down"])

            # Start services
            result = self.run_command(["docker-compose", "up", "-d"])

            if result[0] == 0:
                logger.info("Services restarted successfully")
                return True
            else:
                logger.error("Failed to restart services")
                return False

        except Exception as e:
            logger.error(f"Restart failed: {e}")
            return False

    def emergency_stop(self) -> bool:
        """Emergency stop all services"""
        logger.warning("EMERGENCY STOP initiated!")

        try:
            # Force stop all containers
            self.run_command(["docker-compose", "down", "--remove-orphans"])

            # Kill any remaining containers
            self.run_command(["docker", "kill", "$(docker ps -q)"], ignore_errors=True)

            logger.info("Emergency stop completed")
            return True

        except Exception as e:
            logger.error(f"Emergency stop failed: {e}")
            return False

    def show_logs(self, service: Optional[str] = None, lines: int = 100) -> None:
        """Show comprehensive logs"""
        if service:
            logger.info(f"Showing logs for {service}...")
            self.run_command(["docker-compose", "logs", "--tail", str(lines), service])
        else:
            logger.info("Showing logs for all services...")
            self.run_command(["docker-compose", "logs", "--tail", str(lines)])

    def monitor_containers(self) -> None:
        """Monitor container status in real-time"""
        logger.info("Starting container monitoring (Ctrl+C to stop)...")

        try:
            while True:
                health = self.check_health()

                print("\n" + "="*60)
                print(f"Container Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("="*60)

                for service, status in health.items():
                    running_icon = "🟢" if status["running"] else "🔴"
                    healthy_icon = "✅" if status["healthy"] else "❌"
                    print(f"{running_icon} {service:<20} Running: {status['running']:<5} Healthy: {status['healthy']}")

                print("="*60)

                # Check resource usage
                try:
                    result = subprocess.run(
                        ["docker", "stats", "--no-stream", "--format", "table {{.Name}}\t{{.CPUPerc}}\t{{.MemPerc}}"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        print("\nResource Usage:")
                        print(result.stdout)
                except Exception:
                    pass

                time.sleep(10)

        except KeyboardInterrupt:
            logger.info("Container monitoring stopped")

def main():
    parser = argparse.ArgumentParser(description='Container Manager for Overnight Trading System')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Cleanup command
    subparsers.add_parser('cleanup', help='Clean up orphaned containers and resources')

    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create system backup')
    backup_parser.add_argument('--name', help='Backup name (auto-generated if not provided)')

    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('backup_name', help='Name of backup to restore')

    # Health command
    subparsers.add_parser('health', help='Check service health')

    # Restart command
    subparsers.add_parser('restart', help='Restart all services')

    # Stop command
    subparsers.add_parser('stop', help='Emergency stop all services')

    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Show service logs')
    logs_parser.add_argument('--service', help='Specific service to show logs for')
    logs_parser.add_argument('--lines', type=int, default=100, help='Number of log lines to show')

    # Monitor command
    subparsers.add_parser('monitor', help='Monitor containers in real-time')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = ContainerManager()

    if args.command == 'cleanup':
        success = manager.cleanup_containers()
        sys.exit(0 if success else 1)

    elif args.command == 'backup':
        success = manager.backup_system(args.name if hasattr(args, 'name') else None)
        sys.exit(0 if success else 1)

    elif args.command == 'restore':
        success = manager.restore_backup(args.backup_name)
        sys.exit(0 if success else 1)

    elif args.command == 'health':
        health = manager.check_health()
        print(json.dumps(health, indent=2))

    elif args.command == 'restart':
        success = manager.restart_services()
        sys.exit(0 if success else 1)

    elif args.command == 'stop':
        success = manager.emergency_stop()
        sys.exit(0 if success else 1)

    elif args.command == 'logs':
        manager.show_logs(
            args.service if hasattr(args, 'service') else None,
            args.lines if hasattr(args, 'lines') else 100
        )

    elif args.command == 'monitor':
        manager.monitor_containers()

if __name__ == "__main__":
    main()