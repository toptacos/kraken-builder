#!/usr/bin/env python3
"""
End-to-End Tests for Kraken Trading Bot
======================================

This module contains end-to-end tests that verify the complete functionality
of the trading bot system, including all integrations and workflows.

Tests include:
- Full bot initialization and startup
- API endpoint functionality
- Trading cycle execution
- Data flow between components
- Error handling and recovery
- Performance validation

Run with: python -m pytest tests/test_e2e.py -v -s
"""

import os
import sys
import time
import unittest
import requests
import subprocess
import signal
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot import TradingBot, app
import threading


class TestEndToEnd(unittest.TestCase):
    """End-to-end test cases"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Mock environment variables for testing
        cls.env_patcher = patch.dict(os.environ, {
            'TEST_MODE': 'true',
            'STARTING_BALANCE': '1000',
            'TRADE_AMOUNT': '50',
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret'
        })
        cls.env_patcher.start()

        # Start Flask test server
        cls.flask_thread = threading.Thread(target=cls._run_flask_test_server, daemon=True)
        cls.flask_thread.start()
        time.sleep(2)  # Wait for server to start

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        cls.env_patcher.stop()
        # Flask server will be stopped by daemon thread

    @classmethod
    def _run_flask_test_server(cls):
        """Run Flask test server"""
        try:
            app.run(host='127.0.0.1', port=8081, debug=False, use_reloader=False)
        except Exception as e:
            print(f"Flask test server error: {e}")

    def setUp(self):
        """Set up each test"""
        self.base_url = 'http://127.0.0.1:8081'
        self.bot = None

    def test_01_bot_initialization(self):
        """Test complete bot initialization"""
        print("Testing bot initialization...")

        with patch('ccxt.binance') as mock_binance, \
             patch('src.twitter_integration.initialize_twitter_integration', return_value=MagicMock()):

            mock_exchange = MagicMock()
            mock_exchange.symbols = ['BTC/USDT', 'ETH/USDT']
            mock_exchange.load_markets = MagicMock()
            mock_exchange.fetch_balance = MagicMock(return_value={'USDT': {'free': 1000}})
            mock_binance.return_value = mock_exchange

            # Initialize bot
            self.bot = TradingBot()

            # Verify initialization
            self.assertIsNotNone(self.bot)
            self.assertEqual(self.bot.test_mode, True)
            self.assertEqual(self.bot.starting_balance, 1000)
            self.assertIn('binance', self.bot.exchanges)

        print("✅ Bot initialization test passed")

    def test_02_api_health_check(self):
        """Test API health check endpoint"""
        print("Testing API health check...")

        try:
            response = requests.get(f'{self.base_url}/health', timeout=10)
            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertIn('status', data)
            self.assertIn('services', data)
            self.assertIn('timestamp', data)

        except requests.exceptions.ConnectionError:
            self.skipTest("Flask server not running - skipping API tests")

        print("✅ API health check test passed")

    def test_03_api_status_endpoint(self):
        """Test API status endpoint"""
        print("Testing API status endpoint...")

        try:
            response = requests.get(f'{self.base_url}/status', timeout=10)
            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertIn('status', data)
            self.assertIn('timestamp', data)

        except requests.exceptions.ConnectionError:
            self.skipTest("Flask server not running - skipping API tests")

        print("✅ API status endpoint test passed")

    def test_04_trending_coin_api(self):
        """Test trending coin API endpoint"""
        print("Testing trending coin API...")

        try:
            response = requests.get(f'{self.base_url}/trending', timeout=10)
            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertIn('status', data)
            self.assertIn('coin', data)
            self.assertIn('symbol', data)

        except requests.exceptions.ConnectionError:
            self.skipTest("Flask server not running - skipping API tests")

        print("✅ Trending coin API test passed")

    def test_05_signals_api(self):
        """Test trading signals API endpoint"""
        print("Testing trading signals API...")

        try:
            response = requests.get(f'{self.base_url}/signals', timeout=10)
            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertIn('status', data)
            self.assertIn('signals', data)

        except requests.exceptions.ConnectionError:
            self.skipTest("Flask server not running - skipping API tests")

        print("✅ Trading signals API test passed")

    def test_06_portfolio_api(self):
        """Test portfolio API endpoint"""
        print("Testing portfolio API...")

        try:
            response = requests.get(f'{self.base_url}/portfolio', timeout=10)
            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertIn('status', data)
            self.assertIn('data', data)

        except requests.exceptions.ConnectionError:
            self.skipTest("Flask server not running - skipping API tests")

        print("✅ Portfolio API test passed")

    def test_07_logs_api(self):
        """Test logs API endpoint"""
        print("Testing logs API...")

        try:
            response = requests.get(f'{self.base_url}/logs', timeout=10)
            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertIn('logs', data)
            self.assertIn('total', data)

        except requests.exceptions.ConnectionError:
            self.skipTest("Flask server not running - skipping API tests")

        print("✅ Logs API test passed")

    def test_08_trading_cycle_execution(self):
        """Test trading cycle execution"""
        print("Testing trading cycle execution...")

        with patch('ccxt.binance') as mock_binance, \
             patch('src.twitter_integration.initialize_twitter_integration', return_value=MagicMock()), \
             patch('requests.get') as mock_get:

            # Mock exchange
            mock_exchange = MagicMock()
            mock_exchange.symbols = ['BTC/USDT', 'ETH/USDT']
            mock_exchange.load_markets = MagicMock()
            mock_exchange.fetch_balance = MagicMock(return_value={'USDT': {'free': 1000}})
            mock_exchange.fetch_ticker = MagicMock(return_value={'last': 50000})
            mock_exchange.fetch_ohlcv = MagicMock(return_value=[
                [1640995200000, 50000, 51000, 49000, 50500, 100],
                [1641081600000, 50500, 52000, 50000, 51500, 120],
                [1641168000000, 51500, 53000, 51000, 52500, 110]
            ])
            mock_binance.return_value = mock_exchange

            # Mock CoinGecko API
            mock_response = MagicMock()
            mock_response.json.return_value = {
                'coins': [{'item': {'symbol': 'BTC', 'name': 'Bitcoin'}}]
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Initialize bot
            bot = TradingBot()

            # Execute trading cycle
            result = bot.run_cycle()

            # Verify cycle completed (should not raise exception)
            self.assertIsNone(result)

        print("✅ Trading cycle execution test passed")

    def test_09_error_handling(self):
        """Test error handling and recovery"""
        print("Testing error handling...")

        with patch('ccxt.binance') as mock_binance, \
             patch('src.twitter_integration.initialize_twitter_integration', return_value=MagicMock()):

            # Mock exchange that raises errors
            mock_exchange = MagicMock()
            mock_exchange.symbols = ['BTC/USDT']
            mock_exchange.load_markets = MagicMock(side_effect=Exception("Network error"))
            mock_binance.return_value = mock_exchange

            # Initialize bot
            bot = TradingBot()

            # Test that bot handles errors gracefully
            try:
                bot.run_cycle()
                # Should not raise unhandled exception
            except Exception as e:
                self.fail(f"Bot raised unhandled exception: {e}")

        print("✅ Error handling test passed")

    def test_10_twitter_integration(self):
        """Test Twitter integration functionality"""
        print("Testing Twitter integration...")

        try:
            response = requests.get(f'{self.base_url}/twitter/prompts', timeout=10)
            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertIn('status', data)
            self.assertIn('prompts', data)

        except requests.exceptions.ConnectionError:
            self.skipTest("Flask server not running - skipping Twitter API tests")

        print("✅ Twitter integration test passed")

    def test_11_performance_validation(self):
        """Test performance and response times"""
        print("Testing performance...")

        try:
            import time

            # Test health endpoint response time
            start_time = time.time()
            response = requests.get(f'{self.base_url}/health', timeout=5)
            response_time = time.time() - start_time

            self.assertEqual(response.status_code, 200)
            self.assertLess(response_time, 2.0, "Health check took too long")

            # Test status endpoint response time
            start_time = time.time()
            response = requests.get(f'{self.base_url}/status', timeout=5)
            response_time = time.time() - start_time

            self.assertEqual(response.status_code, 200)
            self.assertLess(response_time, 1.0, "Status check took too long")

        except requests.exceptions.ConnectionError:
            self.skipTest("Flask server not running - skipping performance tests")

        print("✅ Performance validation test passed")

    def test_12_memory_and_resource_usage(self):
        """Test memory and resource usage"""
        print("Testing resource usage...")

        try:
            import psutil
            import os

            # Get current process
            process = psutil.Process(os.getpid())

            # Check memory usage
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            # Should not exceed reasonable limits (500MB for tests)
            self.assertLess(memory_mb, 500, f"Memory usage too high: {memory_mb:.2f}MB")

            # Check CPU usage (should not be excessively high)
            cpu_percent = process.cpu_percent(interval=1.0)
            self.assertLess(cpu_percent, 50, f"CPU usage too high: {cpu_percent:.1f}%")

        except ImportError:
            self.skipTest("psutil not available - skipping resource tests")

        print("✅ Resource usage test passed")


class TestIntegrationWorkflow(unittest.TestCase):
    """Integration workflow tests"""

    def test_workflow_initialization_to_trading(self):
        """Test complete workflow from initialization to trading"""
        print("Testing complete workflow...")

        with patch('ccxt.binance') as mock_binance, \
             patch('src.twitter_integration.initialize_twitter_integration', return_value=MagicMock()), \
             patch('requests.get') as mock_get:

            # Mock all external dependencies
            mock_exchange = MagicMock()
            mock_exchange.symbols = ['BTC/USDT', 'ETH/USDT']
            mock_exchange.load_markets = MagicMock()
            mock_exchange.fetch_balance = MagicMock(return_value={'USDT': {'free': 1000}})
            mock_exchange.fetch_ticker = MagicMock(return_value={'last': 50000})
            mock_exchange.fetch_ohlcv = MagicMock(return_value=[
                [1640995200000, 50000, 51000, 49000, 50500, 100],
                [1641081600000, 50500, 52000, 50000, 51500, 120],
                [1641168000000, 51500, 53000, 51000, 52500, 110]
            ])
            mock_binance.return_value = mock_exchange

            # Mock CoinGecko API
            mock_response = MagicMock()
            mock_response.json.return_value = {
                'coins': [{'item': {'symbol': 'BTC', 'name': 'Bitcoin'}}]
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Execute complete workflow
            bot = TradingBot()

            # Verify bot is ready
            self.assertIsNotNone(bot.exchanges)
            self.assertTrue(len(bot.exchanges) > 0)

            # Test trending coin retrieval
            coin = bot.get_trending_coin()
            self.assertIsNotNone(coin)

            # Test signal generation
            df = bot.fetch_ohlcv(mock_exchange, 'BTC/USDT')
            signal = bot.generate_signal(df)
            self.assertIn(signal, ['buy', 'sell', 'hold'])

            # Test trade execution (mocked)
            success = bot.execute_trade(mock_exchange, 'BTC/USDT', 'buy', 0.001)
            self.assertTrue(success)

        print("✅ Complete workflow test passed")


if __name__ == '__main__':
    # Add verbose output for E2E tests
    if '--verbose' in sys.argv or '-v' in sys.argv:
        unittest.main(verbosity=2)
    else:
        unittest.main(verbosity=1)