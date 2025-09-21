#!/usr/bin/env python3
"""
Automated Trading Script for Kraken Trading Bot
===============================================

This script runs automated trading cycles every minute when enabled.
It scrapes trending data, analyzes charts, and executes trades automatically.

Usage:
    python3 auto_trader.py

Environment Variables:
    - AUTO_TRADING_ENABLED: true/false (default: false)
    - TRADING_MODE: test/production (default: test)
    - AUTO_TRADING_INTERVAL: seconds between cycles (default: 60)

Safety Features:
    - Only runs in production mode
    - Requires explicit enablement
    - Comprehensive logging
    - Error handling and recovery
"""

import os
import sys
import time
import logging
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/auto_trader.log') if os.path.exists('/app') else logging.FileHandler('auto_trader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoTrader:
    """Automated trading controller"""

    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.enabled = os.getenv('AUTO_TRADING_ENABLED', 'false').lower() == 'true'
        self.trading_mode = os.getenv('TRADING_MODE', 'test')
        self.interval = int(os.getenv('AUTO_TRADING_INTERVAL', '60'))

        logger.info("=== Auto Trader Initialized ===")
        logger.info(f"Enabled: {self.enabled}")
        logger.info(f"Trading Mode: {self.trading_mode}")
        logger.info(f"Interval: {self.interval} seconds")

    def check_health(self):
        """Check if the trading bot is healthy and ready"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('status') == 'healthy'
            return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def check_mode_settings(self):
        """Verify that auto-trading is properly configured"""
        try:
            response = requests.get(f"{self.base_url}/mode", timeout=10)
            if response.status_code == 200:
                data = response.json()
                mode_ok = data.get('mode') == 'production'
                auto_trading_ok = data.get('auto_trading_enabled', False)
                return mode_ok and auto_trading_ok
            return False
        except Exception as e:
            logger.error(f"Mode check failed: {e}")
            return False

    def execute_trade_cycle(self):
        """Execute one automated trading cycle"""
        try:
            logger.info("🚀 Executing automated trading cycle...")

            # Trigger auto-trade via API
            response = requests.post(f"{self.base_url}/auto-trade", timeout=30)

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    logger.info("✅ Auto-trading cycle completed successfully")
                    return True
                else:
                    logger.error(f"❌ Auto-trading cycle failed: {data.get('message', 'Unknown error')}")
                    return False
            else:
                logger.error(f"❌ Auto-trading API call failed with status {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False

        except requests.exceptions.Timeout:
            logger.error("❌ Auto-trading cycle timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Auto-trading cycle failed with exception: {e}")
            return False

    def run_continuous(self):
        """Run continuous automated trading"""
        logger.info("🔄 Starting continuous automated trading...")

        cycle_count = 0
        consecutive_failures = 0
        max_consecutive_failures = 5

        while True:
            cycle_count += 1
            cycle_start = datetime.now()

            logger.info(f"🔄 Cycle #{cycle_count} starting at {cycle_start.strftime('%H:%M:%S')}")

            # Safety checks
            if not self.check_health():
                logger.warning("⚠️ Trading bot health check failed, skipping cycle")
                consecutive_failures += 1
            elif not self.check_mode_settings():
                logger.warning("⚠️ Auto-trading not properly configured, skipping cycle")
                consecutive_failures += 1
            else:
                # Execute trading cycle
                if self.execute_trade_cycle():
                    consecutive_failures = 0
                    logger.info("✅ Cycle completed successfully")
                else:
                    consecutive_failures += 1
                    logger.error(f"❌ Cycle failed (failure #{consecutive_failures})")

            # Check for too many consecutive failures
            if consecutive_failures >= max_consecutive_failures:
                logger.critical(f"🚨 {max_consecutive_failures} consecutive failures, stopping auto-trader")
                break

            # Calculate sleep time
            cycle_end = datetime.now()
            cycle_duration = (cycle_end - cycle_start).total_seconds()
            sleep_time = max(0, self.interval - cycle_duration)

            if sleep_time > 0:
                logger.info(f"⏳ Sleeping for {sleep_time:.1f} seconds until next cycle...")
                time.sleep(sleep_time)
            else:
                logger.warning(f"⚠️ Cycle took {cycle_duration:.1f}s, longer than interval {self.interval}s")

    def run_single_cycle(self):
        """Run a single automated trading cycle"""
        logger.info("🔄 Running single automated trading cycle...")

        if not self.check_health():
            logger.error("❌ Trading bot is not healthy")
            return False

        if not self.check_mode_settings():
            logger.error("❌ Auto-trading is not properly configured")
            return False

        return self.execute_trade_cycle()

def main():
    """Main entry point"""
    trader = AutoTrader()

    if not trader.enabled:
        logger.warning("⚠️ Auto-trading is not enabled. Set AUTO_TRADING_ENABLED=true to enable.")
        sys.exit(1)

    if trader.trading_mode != 'production':
        logger.error("❌ Auto-trading can only run in production mode")
        sys.exit(1)

    # Check if we should run continuously or single cycle
    run_mode = os.getenv('AUTO_TRADER_MODE', 'continuous')

    if run_mode == 'single':
        success = trader.run_single_cycle()
        sys.exit(0 if success else 1)
    else:
        # Run continuous mode
        try:
            trader.run_continuous()
        except KeyboardInterrupt:
            logger.info("👋 Auto-trader stopped by user")
        except Exception as e:
            logger.critical(f"💥 Auto-trader crashed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()