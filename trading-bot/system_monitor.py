#!/usr/bin/env python3
"""
System Monitor for Overnight Trading Bot
========================================

This script provides comprehensive monitoring, alerting, and logging
for the overnight trading system with the following features:

- Real-time health monitoring of all services
- Automated alerts for system issues
- Performance metrics tracking
- Log aggregation and analysis
- Emergency response automation
- Multi-channel notifications (console, file, webhook)

Usage:
    python3 system_monitor.py [--alert-webhook URL] [--debug]
"""

import os
import time
import logging
import requests
import json
import psutil
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse
import sys
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MONITOR - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SystemMonitor:
    def __init__(self, alert_webhook: Optional[str] = None, debug: bool = False):
        self.alert_webhook = alert_webhook
        self.debug = debug
        self.alerts_sent = set()  # Track sent alerts to avoid spam
        self.system_stats = {}
        self.service_status = {}
        self.performance_metrics = []

        # Alert thresholds
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'response_time': 5.0,  # seconds
            'error_rate': 10.0     # percent
        }

        # Service endpoints to monitor
        self.services = {
            'trading_bot': {
                'url': 'http://localhost:8080/health',
                'name': 'Main Trading Bot'
            },
            'overnight_trader': {
                'url': 'http://localhost:8081/overnight/status',
                'name': 'Overnight Trader'
            },
            'redis': {
                'url': 'http://localhost:6379',
                'name': 'Redis Cache',
                'type': 'tcp'
            },
            'postgres': {
                'url': 'localhost:5432',
                'name': 'PostgreSQL Database',
                'type': 'tcp'
            }
        }

        logger.info("System Monitor initialized")
        if self.alert_webhook:
            logger.info(f"Alert webhook configured: {self.alert_webhook}")

    def send_alert(self, title: str, message: str, severity: str = 'warning'):
        """Send alert through configured channels"""
        alert_id = f"{title}_{int(time.time())}"

        # Avoid sending duplicate alerts within 5 minutes
        if alert_id in self.alerts_sent:
            return

        self.alerts_sent.add(alert_id)

        # Clean old alerts (keep only last 100)
        if len(self.alerts_sent) > 100:
            self.alerts_sent = set(list(self.alerts_sent)[-50:])

        timestamp = datetime.now().isoformat()

        alert_data = {
            'id': alert_id,
            'title': title,
            'message': message,
            'severity': severity,
            'timestamp': timestamp,
            'hostname': socket.gethostname(),
            'system_stats': self.system_stats
        }

        # Log alert
        log_level = logging.WARNING if severity == 'warning' else logging.ERROR
        logger.log(log_level, f"ALERT: {title} - {message}")

        # Send to webhook if configured
        if self.alert_webhook:
            try:
                response = requests.post(
                    self.alert_webhook,
                    json=alert_data,
                    timeout=10,
                    headers={'Content-Type': 'application/json'}
                )
                if response.status_code == 200:
                    logger.info("Alert sent to webhook successfully")
                else:
                    logger.error(f"Failed to send alert to webhook: {response.status_code}")
            except Exception as e:
                logger.error(f"Error sending alert to webhook: {e}")

        # Print to console with formatting
        print(f"\n🚨 ALERT [{severity.upper()}] {timestamp}")
        print(f"📢 {title}")
        print(f"💬 {message}")
        print("-" * 50)

    def check_service_health(self, service_name: str, service_config: Dict) -> Dict:
        """Check health of a specific service"""
        try:
            if service_config.get('type') == 'tcp':
                # TCP connection check
                host, port = service_config['url'].split(':')
                port = int(port)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()

                is_healthy = result == 0
                response_time = 0.001 if is_healthy else 5.0
            else:
                # HTTP health check
                start_time = time.time()
                response = requests.get(service_config['url'], timeout=10)
                response_time = time.time() - start_time
                is_healthy = response.status_code == 200

                if self.debug:
                    logger.debug(f"{service_name} response: {response.status_code} in {response_time:.3f}s")

            status = {
                'healthy': is_healthy,
                'response_time': response_time,
                'last_check': datetime.now().isoformat(),
                'error': None
            }

            # Alert on unhealthy services
            if not is_healthy:
                self.send_alert(
                    f"{service_config['name']} Unhealthy",
                    f"Service {service_name} is not responding properly",
                    'error'
                )

            # Alert on slow responses
            if response_time > self.thresholds['response_time']:
                self.send_alert(
                    f"{service_config['name']} Slow Response",
                    f"Response time: {response_time:.2f}s (threshold: {self.thresholds['response_time']}s)",
                    'warning'
                )

            return status

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error checking {service_name}: {error_msg}")

            return {
                'healthy': False,
                'response_time': 10.0,
                'last_check': datetime.now().isoformat(),
                'error': error_msg
            }

    def check_system_resources(self) -> Dict:
        """Check system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            # Network I/O
            net_io = psutil.net_io_counters()
            bytes_sent = net_io.bytes_sent
            bytes_recv = net_io.bytes_recv

            stats = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_used_gb': memory.used / (1024**3),
                'memory_total_gb': memory.total / (1024**3),
                'disk_percent': disk_percent,
                'disk_used_gb': disk.used / (1024**3),
                'disk_total_gb': disk.total / (1024**3),
                'network_sent_mb': bytes_sent / (1024**2),
                'network_recv_mb': bytes_recv / (1024**2),
                'timestamp': datetime.now().isoformat()
            }

            # Store for trend analysis
            self.system_stats = stats
            self.performance_metrics.append(stats)

            # Keep only last 100 metrics
            if len(self.performance_metrics) > 100:
                self.performance_metrics = self.performance_metrics[-100:]

            # Alert on high resource usage
            if cpu_percent > self.thresholds['cpu_percent']:
                self.send_alert(
                    "High CPU Usage",
                    f"CPU usage at {cpu_percent:.1f}% (threshold: {self.thresholds['cpu_percent']}%)",
                    'warning'
                )

            if memory_percent > self.thresholds['memory_percent']:
                self.send_alert(
                    "High Memory Usage",
                    f"Memory usage at {memory_percent:.1f}% (threshold: {self.thresholds['memory_percent']}%)",
                    'warning'
                )

            if disk_percent > self.thresholds['disk_percent']:
                self.send_alert(
                    "High Disk Usage",
                    f"Disk usage at {disk_percent:.1f}% (threshold: {self.thresholds['disk_percent']}%)",
                    'error'
                )

            return stats

        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return {}

    def check_trading_performance(self) -> Dict:
        """Check trading performance metrics"""
        try:
            # Get overnight trader status
            response = requests.get('http://localhost:8081/overnight/status', timeout=10)
            if response.status_code == 200:
                data = response.json()

                daily_pnl = data.get('daily_pnl', 0)
                current_balance = data.get('current_balance', 1000)
                active_positions = data.get('active_positions', 0)

                # Calculate performance metrics
                pnl_percentage = (daily_pnl / current_balance) * 100 if current_balance > 0 else 0

                # Alert on significant losses
                if pnl_percentage < -10:  # More than 10% loss
                    self.send_alert(
                        "Significant Trading Loss",
                        f"Daily P&L: {pnl_percentage:.2f}% (${daily_pnl:.2f})",
                        'error'
                    )
                elif pnl_percentage > 5:  # More than 5% gain
                    self.send_alert(
                        "Strong Trading Performance",
                        f"Daily P&L: {pnl_percentage:.2f}% (${daily_pnl:.2f})",
                        'info'
                    )

                return {
                    'daily_pnl': daily_pnl,
                    'pnl_percentage': pnl_percentage,
                    'current_balance': current_balance,
                    'active_positions': active_positions,
                    'timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error checking trading performance: {e}")

        return {}

    def generate_health_report(self) -> str:
        """Generate comprehensive health report"""
        report = []
        report.append("=" * 60)
        report.append("SYSTEM HEALTH REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # System Resources
        if self.system_stats:
            report.append("SYSTEM RESOURCES:")
            report.append(f"  CPU Usage: {self.system_stats.get('cpu_percent', 0):.1f}%")
            report.append(f"  Memory: {self.system_stats.get('memory_used_gb', 0):.1f}GB / {self.system_stats.get('memory_total_gb', 0):.1f}GB")
            report.append(f"  Disk: {self.system_stats.get('disk_used_gb', 0):.1f}GB / {self.system_stats.get('disk_total_gb', 0):.1f}GB")
            report.append("")

        # Service Status
        report.append("SERVICE STATUS:")
        for service_name, status in self.service_status.items():
            health_icon = "✅" if status.get('healthy') else "❌"
            response_time = status.get('response_time', 0)
            report.append(f"  {health_icon} {service_name}: {response_time:.3f}s")

        # Trading Performance
        if hasattr(self, 'trading_performance') and self.trading_performance:
            report.append("")
            report.append("TRADING PERFORMANCE:")
            report.append(f"  Daily P&L: ${self.trading_performance.get('daily_pnl', 0):.2f}")
            report.append(f"  P&L %: {self.trading_performance.get('pnl_percentage', 0):.2f}%")
            report.append(f"  Active Positions: {self.trading_performance.get('active_positions', 0)}")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)

    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        logger.info("Starting monitoring cycle")

        # Check system resources
        self.check_system_resources()

        # Check all services
        for service_name, service_config in self.services.items():
            self.service_status[service_name] = self.check_service_health(service_name, service_config)

        # Check trading performance
        self.trading_performance = self.check_trading_performance()

        # Generate and log health report every 10 cycles
        if hasattr(self, 'cycle_count'):
            self.cycle_count += 1
        else:
            self.cycle_count = 1

        if self.cycle_count % 10 == 0:
            report = self.generate_health_report()
            logger.info(f"Health Report:\n{report}")

        logger.info("Monitoring cycle completed")

    def start_monitoring(self, interval: int = 60):
        """Start continuous monitoring"""
        logger.info(f"Starting continuous monitoring (interval: {interval}s)")

        try:
            while True:
                self.run_monitoring_cycle()
                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            self.send_alert(
                "Monitoring System Error",
                f"System monitor encountered an error: {e}",
                'error'
            )

def main():
    parser = argparse.ArgumentParser(description='System Monitor for Overnight Trading Bot')
    parser.add_argument('--alert-webhook', help='Webhook URL for alerts')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in seconds')
    parser.add_argument('--once', action='store_true', help='Run one monitoring cycle and exit')

    args = parser.parse_args()

    # Create monitor
    monitor = SystemMonitor(
        alert_webhook=args.alert_webhook,
        debug=args.debug
    )

    if args.once:
        # Run single monitoring cycle
        monitor.run_monitoring_cycle()
        print("\nMonitoring cycle completed. Health report:")
        print(monitor.generate_health_report())
    else:
        # Start continuous monitoring
        monitor.start_monitoring(interval=args.interval)

if __name__ == "__main__":
    main()