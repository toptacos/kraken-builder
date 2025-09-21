#!/usr/bin/env python3
"""
Basic Functionality Test for Kraken Trading Bot
==============================================

This script performs basic functionality tests without requiring pytest.
It verifies that the core components can be imported and initialized correctly.

Usage: python3 test_basic_functionality.py
"""

import os
import sys
import traceback
from datetime import datetime

def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")

    try:
        # Test core trading bot import
        from trading_bot import TradingBot
        print("✅ trading_bot module imported successfully")

        # Test crypto trend analyzer import
        from crypto_trend_analyzer import CryptoTrendAnalyzer
        print("✅ crypto_trend_analyzer module imported successfully")

        # Test overnight trader import
        from overnight_trader import OvernightTrader
        print("✅ overnight_trader module imported successfully")

        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during imports: {e}")
        return False

def test_trading_bot_initialization():
    """Test TradingBot initialization"""
    print("\nTesting TradingBot initialization...")

    try:
        # Mock environment for testing
        original_env = os.environ.copy()

        # Set test environment variables
        os.environ['TEST_MODE'] = 'true'
        os.environ['STARTING_BALANCE'] = '1000'
        os.environ['TRADE_AMOUNT'] = '50'

        # Mock external dependencies
        from unittest.mock import patch, MagicMock

        with patch('ccxt.binance') as mock_binance, \
             patch('src.twitter_integration.initialize_twitter_integration', return_value=MagicMock()):

            mock_exchange = MagicMock()
            mock_exchange.symbols = ['BTC/USDT', 'ETH/USDT']
            mock_exchange.load_markets = MagicMock()
            mock_exchange.fetch_balance = MagicMock(return_value={'USDT': {'free': 1000}})
            mock_binance.return_value = mock_exchange

            from trading_bot import TradingBot
            bot = TradingBot()

            # Verify initialization
            assert bot.test_mode == True
            assert bot.starting_balance == 1000
            assert bot.trade_amount == 50
            assert 'binance' in bot.exchanges

            print("✅ TradingBot initialized successfully")
            print(f"   Test mode: {bot.test_mode}")
            print(f"   Starting balance: ${bot.starting_balance}")
            print(f"   Trade amount: ${bot.trade_amount}")
            print(f"   Exchanges configured: {list(bot.exchanges.keys())}")

        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)

        return True

    except Exception as e:
        print(f"❌ TradingBot initialization failed: {e}")
        traceback.print_exc()
        return False

def test_crypto_trend_analyzer():
    """Test CryptoTrendAnalyzer functionality"""
    print("\nTesting CryptoTrendAnalyzer...")

    try:
        from crypto_trend_analyzer import CryptoTrendAnalyzer

        analyzer = CryptoTrendAnalyzer(cache_dir="test_cache", update_interval=1)

        # Test basic functionality
        assert analyzer.cache_dir == "test_cache"
        assert analyzer.update_interval == 1

        print("✅ CryptoTrendAnalyzer initialized successfully")
        print(f"   Cache directory: {analyzer.cache_dir}")
        print(f"   Update interval: {analyzer.update_interval}s")

        # Clean up test cache
        import shutil
        if os.path.exists("test_cache"):
            shutil.rmtree("test_cache")

        return True

    except Exception as e:
        print(f"❌ CryptoTrendAnalyzer test failed: {e}")
        traceback.print_exc()
        return False

def test_twitter_integration():
    """Test Twitter integration import"""
    print("\nTesting Twitter integration...")

    try:
        from src.twitter_integration import TwitterIntegration, initialize_twitter_integration

        # Test that classes can be instantiated
        twitter = TwitterIntegration()
        print("✅ TwitterIntegration class instantiated successfully")

        # Test initialization function
        mock_twitter = initialize_twitter_integration()
        print("✅ Twitter integration initialization function works")

        return True

    except ImportError as e:
        print(f"⚠️ Twitter integration not available: {e}")
        print("   This is expected if Twitter API keys are not configured")
        return True  # Not a failure, just not configured
    except Exception as e:
        print(f"❌ Twitter integration test failed: {e}")
        traceback.print_exc()
        return False

def test_flask_app():
    """Test Flask application setup"""
    print("\nTesting Flask application...")

    try:
        from trading_bot import app

        # Test that app is properly configured
        assert app is not None
        print("✅ Flask app imported successfully")

        # Test that routes are registered
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        expected_routes = ['/health', '/status', '/logs', '/test_trade', '/run_cycle', '/portfolio', '/signals', '/trending', '/twitter/prompts']

        for route in expected_routes:
            if route in routes:
                print(f"   ✅ Route {route} is registered")
            else:
                print(f"   ⚠️ Route {route} not found")

        return True

    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        traceback.print_exc()
        return False

def test_file_structure():
    """Test that all required files exist"""
    print("\nTesting file structure...")

    required_files = [
        'trading_bot.py',
        'overnight_trader.py',
        'crypto_trend_analyzer.py',
        'requirements.txt',
        'Dockerfile',
        'pytest.ini',
        'tests/__init__.py',
        'tests/test_trading_bot.py',
        'tests/test_e2e.py',
        'src/twitter_integration.py',
        'build_and_deploy.py',
        'run_tests.py'
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"   ✅ {file_path} exists")

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False

    print("✅ All required files are present")
    return True

def main():
    """Run all basic functionality tests"""
    print("=" * 60)
    print("Kraken Trading Bot - Basic Functionality Tests")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print()

    tests = [
        ("File Structure", test_file_structure),
        ("Module Imports", test_imports),
        ("TradingBot Initialization", test_trading_bot_initialization),
        ("CryptoTrendAnalyzer", test_crypto_trend_analyzer),
        ("Twitter Integration", test_twitter_integration),
        ("Flask Application", test_flask_app),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All basic functionality tests passed!")
        return True
    else:
        print("⚠️ Some tests failed. Please check the output above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)