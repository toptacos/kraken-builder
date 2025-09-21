#!/usr/bin/env python3
"""
Comprehensive Test Suite for Kraken Trading Bot
==============================================

This test suite covers all major functionality of the trading bot including:
- Exchange initialization and configuration
- Trend analysis and coin selection
- Technical analysis and signal generation
- Trade execution (mocked)
- Risk management
- API endpoints
- Error handling and fallbacks

Run with: python -m pytest tests/test_trading_bot.py -v
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot import TradingBot
from crypto_trend_analyzer import CryptoTrendAnalyzer
from src.twitter_integration import TwitterIntegration


class TestTradingBot(unittest.TestCase):
    """Test cases for the main TradingBot class"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'TEST_MODE': 'true',
            'STARTING_BALANCE': '1000',
            'TRADE_AMOUNT': '50',
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret'
        })
        self.env_patcher.start()

        # Mock CCXT exchanges
        with patch('ccxt.binance') as mock_binance:
            mock_exchange = Mock()
            mock_exchange.symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT']
            mock_exchange.load_markets = Mock()
            mock_exchange.fetch_balance = Mock(return_value={'USDT': {'free': 1000}})
            mock_exchange.fetch_ticker = Mock(return_value={'last': 50000})
            mock_exchange.fetch_ohlcv = Mock(return_value=[
                [1640995200000, 50000, 51000, 49000, 50500, 100],
                [1641081600000, 50500, 52000, 50000, 51500, 120],
                [1641168000000, 51500, 53000, 51000, 52500, 110]
            ])
            mock_binance.return_value = mock_exchange

            # Initialize bot with mocked dependencies
            with patch('src.twitter_integration.initialize_twitter_integration', return_value=Mock()):
                self.bot = TradingBot()

    def tearDown(self):
        """Clean up test fixtures"""
        self.env_patcher.stop()

    def test_initialization(self):
        """Test bot initialization with correct parameters"""
        self.assertEqual(self.bot.test_mode, True)
        self.assertEqual(self.bot.starting_balance, 1000)
        self.assertEqual(self.bot.trade_amount, 50)
        self.assertEqual(self.bot.current_balance, 1000)
        self.assertIsNotNone(self.bot.exchanges)
        self.assertIn('binance', self.bot.exchanges)

    def test_exchange_initialization(self):
        """Test exchange initialization and configuration"""
        self.assertIn('binance', self.bot.exchanges)
        self.assertIsInstance(self.bot.exchanges['binance'], Mock)

    @patch('requests.get')
    def test_get_trending_coin_success(self, mock_get):
        """Test successful trending coin retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'coins': [
                {'item': {'symbol': 'BTC', 'name': 'Bitcoin'}},
                {'item': {'symbol': 'ETH', 'name': 'Ethereum'}}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch.object(self.bot, '_is_coin_available_on_exchanges', return_value=True):
            coin = self.bot.get_trending_coin()
            self.assertEqual(coin, 'BTC')

    @patch('requests.get')
    def test_get_trending_coin_api_failure(self, mock_get):
        """Test trending coin fallback on API failure"""
        mock_get.side_effect = Exception("API Error")

        coin = self.bot.get_trending_coin()
        self.assertIn(coin, ['BTC', 'ETH', 'BNB', 'ADA', 'SOL'])

    def test_fallback_coin_selection(self):
        """Test fallback coin selection logic"""
        with patch.object(self.bot, '_is_coin_available_on_exchanges', return_value=True):
            coin = self.bot._get_fallback_coin()
            self.assertIsInstance(coin, str)
            self.assertGreater(len(coin), 0)

    def test_ohlcv_fetching(self):
        """Test OHLCV data fetching and processing"""
        df = self.bot.fetch_ohlcv(self.bot.exchanges['binance'], 'BTC/USDT')
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn('timestamp', df.columns)
        self.assertIn('close', df.columns)
        self.assertEqual(len(df), 3)

    def test_signal_generation(self):
        """Test trading signal generation"""
        # Create test data
        dates = pd.date_range(start='2023-01-01', periods=60, freq='H')
        data = {
            'timestamp': dates,
            'open': np.random.uniform(50000, 55000, 60),
            'high': np.random.uniform(51000, 56000, 60),
            'low': np.random.uniform(49000, 54000, 60),
            'close': np.random.uniform(50000, 55000, 60),
            'volume': np.random.uniform(100, 1000, 60)
        }
        df = pd.DataFrame(data)

        signal = self.bot.generate_signal(df)
        self.assertIn(signal, ['buy', 'sell', 'hold'])

    def test_rsi_calculation(self):
        """Test RSI indicator calculation"""
        prices = np.array([50, 51, 52, 51, 50, 49, 48, 49, 50, 51, 52, 53, 54, 55, 54])
        rsi = self.bot._calculate_rsi(prices, 14)
        self.assertIsInstance(rsi, float)
        self.assertGreaterEqual(rsi, 0)
        self.assertLessEqual(rsi, 100)

    @patch('ccxt.binance')
    def test_trade_execution_test_mode(self, mock_binance):
        """Test trade execution in test mode"""
        mock_exchange = Mock()
        mock_exchange.fetch_ticker.return_value = {'last': 50000}
        mock_binance.return_value = mock_exchange

        success = self.bot.execute_trade(mock_exchange, 'BTC/USDT', 'buy', 0.001)
        self.assertTrue(success)

    def test_portfolio_tracking(self):
        """Test portfolio asset tracking"""
        # Simulate a buy trade
        self.bot.position = 'long'
        self.bot.entry_price = 50000
        self.bot.portfolio['BTC'] = {'amount': 0.01, 'buy_price': 50000}

        # Check portfolio balance
        balance = self.bot.check_portfolio_assets(self.bot.exchanges['binance'], 'BTC/USDT')
        self.assertIsInstance(balance, float)

    def test_risk_management(self):
        """Test risk management parameters"""
        self.assertEqual(self.bot.take_profit_percent, 0.03)
        self.assertEqual(self.bot.stop_loss_percent, 0.01)
        self.assertEqual(self.bot.max_daily_loss_percent, 0.05)
        self.assertEqual(self.bot.max_consecutive_losses, 5)


class TestCryptoTrendAnalyzer(unittest.TestCase):
    """Test cases for the CryptoTrendAnalyzer class"""

    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = CryptoTrendAnalyzer(cache_dir="test_cache", update_interval=1)

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up test cache
        import shutil
        if os.path.exists("test_cache"):
            shutil.rmtree("test_cache")

    @patch('requests.get')
    def test_coingecko_scraping(self, mock_get):
        """Test CoinGecko data scraping"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'coins': [
                {'item': {'symbol': 'BTC', 'name': 'Bitcoin', 'market_cap_rank': 1}},
                {'item': {'symbol': 'ETH', 'name': 'Ethereum', 'market_cap_rank': 2}}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        data = self.analyzer._scrape_coingecko()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertIn('symbol', data[0])
        self.assertIn('score', data[0])

    def test_technical_indicators(self):
        """Test technical analysis calculations"""
        # Create mock exchange
        mock_exchange = Mock()
        mock_exchange.symbols = ['BTC/USDT', 'ETH/USDT']

        # Mock OHLCV data
        ohlcv_data = [
            [1640995200000, 50000, 51000, 49000, 50500, 100],
            [1641081600000, 50500, 52000, 50000, 51500, 120],
            [1641168000000, 51500, 53000, 51000, 52500, 110],
            [1641254400000, 52500, 54000, 52000, 53500, 130],
            [1641340800000, 53500, 55000, 53000, 54500, 140],
            [1641427200000, 54500, 56000, 54000, 55500, 150],
            [1641513600000, 55500, 57000, 55000, 56500, 160],
            [1641600000000, 56500, 58000, 56000, 57500, 170],
            [1641686400000, 57500, 59000, 57000, 58500, 180],
            [1641772800000, 58500, 60000, 58000, 59500, 190],
            [1641859200000, 59500, 61000, 59000, 60500, 200],
            [1641945600000, 60500, 62000, 60000, 61500, 210],
            [1642032000000, 61500, 63000, 61000, 62500, 220],
            [1642118400000, 62500, 64000, 62000, 63500, 230],
            [1642204800000, 63500, 65000, 63000, 64500, 240],
            [1642291200000, 64500, 66000, 64000, 65500, 250],
            [1642377600000, 65500, 67000, 65000, 66500, 260],
            [1642464000000, 66500, 68000, 66000, 67500, 270],
            [1642550400000, 67500, 69000, 67000, 68500, 280],
            [1642636800000, 68500, 70000, 68000, 69500, 290],
            [1642723200000, 69500, 71000, 69000, 70500, 300],
            [1642809600000, 70500, 72000, 70000, 71500, 310],
            [1642896000000, 71500, 73000, 71000, 72500, 320],
            [1642982400000, 72500, 74000, 72000, 73500, 330],
            [1643068800000, 73500, 75000, 73000, 74500, 340],
            [1643155200000, 74500, 76000, 74000, 75500, 350],
            [1643241600000, 75500, 77000, 75000, 76500, 360],
            [1643328000000, 76500, 78000, 76000, 77500, 370],
            [1643414400000, 77500, 79000, 77000, 78500, 380],
            [1643500800000, 78500, 80000, 78000, 79500, 390],
            [1643587200000, 79500, 81000, 79000, 80500, 400],
            [1643673600000, 80500, 82000, 80000, 81500, 410],
            [1643760000000, 81500, 83000, 81000, 82500, 420],
            [1643846400000, 82500, 84000, 82000, 83500, 430],
            [1643932800000, 83500, 85000, 83000, 84500, 440],
            [1644019200000, 84500, 86000, 84000, 85500, 450],
            [1644105600000, 85500, 87000, 85000, 86500, 460],
            [1644192000000, 86500, 88000, 86000, 87500, 470],
            [1644278400000, 87500, 89000, 87000, 88500, 480],
            [1644364800000, 88500, 90000, 88000, 89500, 490],
            [1644451200000, 89500, 91000, 89000, 90500, 500],
            [1644537600000, 90500, 92000, 90000, 91500, 510],
            [1644624000000, 91500, 93000, 91000, 92500, 520],
            [1644710400000, 92500, 94000, 92000, 93500, 530],
            [1644796800000, 93500, 95000, 93000, 94500, 540],
            [1644883200000, 94500, 96000, 94000, 95500, 550],
            [1644969600000, 95500, 97000, 95000, 96500, 560],
            [1645056000000, 96500, 98000, 96000, 97500, 570],
            [1645142400000, 97500, 99000, 97000, 98500, 580],
            [1645228800000, 98500, 100000, 98000, 99500, 590],
            [1645315200000, 99500, 101000, 99000, 100500, 600]
        ]
        mock_exchange.fetch_ohlcv.return_value = ohlcv_data

        exchanges = {'binance': mock_exchange}
        technical_data = self.analyzer._analyze_technical_indicators(exchanges)

        self.assertIsInstance(technical_data, list)
        if technical_data:
            self.assertIn('symbol', technical_data[0])
            self.assertIn('rsi', technical_data[0])
            self.assertIn('score', technical_data[0])


class TestTwitterIntegration(unittest.TestCase):
    """Test cases for Twitter integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.twitter = TwitterIntegration()

    @patch('requests.get')
    def test_get_coin_trading_prompts(self, mock_get):
        """Test Twitter trading prompts retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'text': 'BTC looking bullish! #BTC #trading',
                'created_at': '2023-01-01T12:00:00Z',
                'author': 'trader123',
                'sentiment': 'positive'
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        prompts = self.twitter.get_coin_trading_prompts('BTC')
        self.assertIsInstance(prompts, list)


class TestAPIEndpoints(unittest.TestCase):
    """Test cases for Flask API endpoints"""

    def setUp(self):
        """Set up test fixtures"""
        from trading_bot import app
        self.app = app.test_client()
        self.app.testing = True

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('status', data)
        self.assertIn('services', data)

    def test_status_endpoint(self):
        """Test status endpoint"""
        response = self.app.get('/status')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('status', data)

    def test_logs_endpoint(self):
        """Test logs endpoint"""
        response = self.app.get('/logs')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('logs', data)


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple components"""

    def setUp(self):
        """Set up integration test fixtures"""
        # Mock environment
        self.env_patcher = patch.dict(os.environ, {
            'TEST_MODE': 'true',
            'STARTING_BALANCE': '1000',
            'TRADE_AMOUNT': '50'
        })
        self.env_patcher.start()

    def tearDown(self):
        """Clean up integration test fixtures"""
        self.env_patcher.stop()

    @patch('ccxt.binance')
    @patch('requests.get')
    def test_full_trading_cycle(self, mock_requests, mock_binance):
        """Test a complete trading cycle"""
        # Mock exchange
        mock_exchange = Mock()
        mock_exchange.symbols = ['BTC/USDT', 'ETH/USDT']
        mock_exchange.load_markets = Mock()
        mock_exchange.fetch_balance = Mock(return_value={'USDT': {'free': 1000}})
        mock_exchange.fetch_ticker = Mock(return_value={'last': 50000})
        mock_exchange.fetch_ohlcv = Mock(return_value=[
            [1640995200000, 50000, 51000, 49000, 50500, 100],
            [1641081600000, 50500, 52000, 50000, 51500, 120],
            [1641168000000, 51500, 53000, 51000, 52500, 110]
        ])
        mock_binance.return_value = mock_exchange

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'coins': [{'item': {'symbol': 'BTC', 'name': 'Bitcoin'}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_requests.return_value = mock_response

        # Initialize bot
        with patch('src.twitter_integration.initialize_twitter_integration', return_value=Mock()):
            bot = TradingBot()

        # Test trading cycle
        result = bot.run_cycle()
        self.assertIsNone(result)  # Should complete without error


if __name__ == '__main__':
    # Create test suite
    unittest.main(verbosity=2)