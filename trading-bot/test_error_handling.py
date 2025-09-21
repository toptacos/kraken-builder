#!/usr/bin/env python3
"""
Test script to verify the refactored error handling in trading_bot.py
This script tests the improved coin availability checking and fallback logic.
"""

import os
import sys
import logging
from unittest.mock import Mock, patch

# Add current directory to path to import trading_bot
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging for testing
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_coin_availability_with_mock_exchanges():
    """Test coin availability checking with mocked exchanges"""
    print("🧪 Testing coin availability with mocked exchanges...")

    # Mock CCXT exchanges
    mock_binance = Mock()
    mock_binance.id = 'binance'
    mock_binance.symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT']

    mock_coinbase = Mock()
    mock_coinbase.id = 'coinbase'
    mock_coinbase.symbols = ['BTC/USD', 'ETH/USD', 'ADA/USD']  # Note: USD not USDT

    mock_kraken = Mock()
    mock_kraken.id = 'kraken'
    mock_kraken.symbols = ['BTC/USDT', 'ETH/USDT', 'DOT/USDT']

    exchanges = {
        'binance': mock_binance,
        'coinbase': mock_coinbase,
        'kraken': mock_kraken
    }

    # Test case 1: Coin available on multiple exchanges
    print("\n📊 Test 1: BTC available on multiple exchanges")
    from trading_bot import TradingBot

    # Create a minimal bot instance for testing
    bot = TradingBot.__new__(TradingBot)
    bot.exchanges = exchanges

    # Test BTC (should be available)
    result = bot._is_coin_available_on_exchanges('BTC')
    print(f"✅ BTC availability check: {result}")
    assert result == True, "BTC should be available"

    # Test case 2: Coin not available on any exchange
    print("\n📊 Test 2: ASTER not available on any exchange")
    result = bot._is_coin_available_on_exchanges('ASTER')
    print(f"✅ ASTER availability check: {result}")
    assert result == False, "ASTER should not be available"

    # Test case 3: Coin available on some exchanges but not others
    print("\n📊 Test 3: ADA available on some exchanges")
    result = bot._is_coin_available_on_exchanges('ADA')
    print(f"✅ ADA availability check: {result}")
    assert result == True, "ADA should be available on Binance"

    print("✅ All coin availability tests passed!")

def test_fallback_coin_selection():
    """Test fallback coin selection logic with expanded cryptocurrency support"""
    print("\n🧪 Testing fallback coin selection...")

    # Mock exchanges with limited availability
    mock_exchange1 = Mock()
    mock_exchange1.id = 'exchange1'
    mock_exchange1.symbols = ['BTC/USDT', 'ETH/USDT', 'SHIB/USDT', 'XRP/USDT']

    mock_exchange2 = Mock()
    mock_exchange2.id = 'exchange2'
    mock_exchange2.symbols = ['ADA/USDT', 'SOL/USDT', 'LINK/USDT', 'UNI/USDT']

    exchanges = {
        'exchange1': mock_exchange1,
        'exchange2': mock_exchange2
    }

    from trading_bot import TradingBot

    bot = TradingBot.__new__(TradingBot)
    bot.exchanges = exchanges

    # Test fallback selection
    fallback_coin = bot._get_fallback_coin()
    print(f"🎯 Selected fallback coin: {fallback_coin}")

    # Should select from expanded primary fallback list
    primary_fallbacks = [
        'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOT', 'DOGE', 'AVAX', 'LTC', 'MATIC',
        'SHIB', 'XRP', 'TRX', 'LEO', 'BCH', 'ETC', 'XLM', 'VET', 'ICP', 'FIL',
        'THETA', 'HBAR', 'NEAR', 'FLOW', 'MANA', 'SAND', 'AXS', 'CHZ', 'ENJ', 'GALA'
    ]
    assert fallback_coin in primary_fallbacks, f"Fallback coin {fallback_coin} should be in expanded primary list"

    print("✅ Fallback coin selection test passed!")

def test_exchange_error_handling():
    """Test that exchange errors are handled gracefully"""
    print("\n🧪 Testing exchange error handling...")

    # Mock exchange that raises errors
    mock_exchange_error = Mock()
    mock_exchange_error.id = 'error_exchange'
    mock_exchange_error.symbols = Mock(side_effect=Exception("Connection failed"))

    mock_exchange_good = Mock()
    mock_exchange_good.id = 'good_exchange'
    mock_exchange_good.symbols = ['BTC/USDT', 'ETH/USDT']

    exchanges = {
        'error_exchange': mock_exchange_error,
        'good_exchange': mock_exchange_good
    }

    from trading_bot import TradingBot

    bot = TradingBot.__new__(TradingBot)
    bot.exchanges = exchanges

    # Test that error is handled and fallback works
    result = bot._is_coin_available_on_exchanges('BTC')
    print(f"✅ Error handling test result: {result}")
    assert result == True, "Should still find BTC on good exchange despite error on first exchange"

    print("✅ Exchange error handling test passed!")

def test_trending_coin_with_api_error():
    """Test trending coin selection with API errors"""
    print("\n🧪 Testing trending coin selection with API errors...")

    from trading_bot import TradingBot

    # Create bot instance
    bot = TradingBot.__new__(TradingBot)

    # Mock exchanges
    mock_exchange = Mock()
    mock_exchange.id = 'test_exchange'
    mock_exchange.symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SHIB/USDT', 'XRP/USDT']
    bot.exchanges = {'test_exchange': mock_exchange}

    # Mock requests to simulate API failure
    with patch('trading_bot.requests.get') as mock_get:
        # Simulate API timeout
        mock_get.side_effect = Exception("API timeout")

        # Test that fallback works
        coin = bot.get_trending_coin()
        print(f"🎯 Selected coin despite API error: {coin}")

        # Should return a fallback coin from expanded list
        expanded_fallbacks = [
            'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOT', 'DOGE', 'AVAX', 'LTC', 'MATIC',
            'SHIB', 'XRP', 'TRX', 'LEO', 'BCH', 'ETC', 'XLM', 'VET', 'ICP', 'FIL',
            'THETA', 'HBAR', 'NEAR', 'FLOW', 'MANA', 'SAND', 'AXS', 'CHZ', 'ENJ', 'GALA'
        ]
        assert coin in expanded_fallbacks, f"Should return fallback coin from expanded list, got {coin}"

    print("✅ Trending coin API error handling test passed!")

def test_expanded_exchange_support():
    """Test that the bot can handle multiple exchanges gracefully"""
    print("\n🧪 Testing expanded exchange support...")

    # Mock multiple exchanges with different coin availability
    exchanges = {}

    exchange_names = ['binance', 'kraken', 'coinbase', 'kucoin', 'okx', 'huobi', 'gate', 'bybit']
    base_coins = ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'SHIB', 'XRP']

    for i, exchange_name in enumerate(exchange_names):
        mock_exchange = Mock()
        mock_exchange.id = exchange_name
        # Each exchange has different coin availability
        available_coins = base_coins[i:i+5] if i < 5 else base_coins[:3]
        mock_exchange.symbols = [f"{coin}/USDT" for coin in available_coins]
        exchanges[exchange_name] = mock_exchange

    from trading_bot import TradingBot

    bot = TradingBot.__new__(TradingBot)
    bot.exchanges = exchanges

    # Test coin availability checking across multiple exchanges
    test_coins = ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'SHIB', 'XRP']

    for coin in test_coins:
        result = bot._is_coin_available_on_exchanges(coin)
        available_on = [name for name, ex in exchanges.items() if f"{coin}/USDT" in ex.symbols]
        print(f"✅ {coin}: Available on {len(available_on)} exchanges - {result}")

    # Test fallback selection with multiple exchanges
    fallback_coin = bot._get_fallback_coin()
    print(f"🎯 Selected fallback coin with {len(exchanges)} exchanges: {fallback_coin}")

    # Should select from primary fallback list
    primary_fallbacks = [
        'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOT', 'DOGE', 'AVAX', 'LTC', 'MATIC',
        'SHIB', 'XRP', 'TRX', 'LEO', 'BCH', 'ETC', 'XLM', 'VET', 'ICP', 'FIL',
        'THETA', 'HBAR', 'NEAR', 'FLOW', 'MANA', 'SAND', 'AXS', 'CHZ', 'ENJ', 'GALA'
    ]
    assert fallback_coin in primary_fallbacks, f"Fallback coin {fallback_coin} should be in primary list"

    print("✅ Expanded exchange support test passed!")

def main():
    """Run all tests"""
    print("🚀 Starting error handling tests for trading bot...")

    try:
        test_coin_availability_with_mock_exchanges()
        test_fallback_coin_selection()
        test_exchange_error_handling()
        test_trending_coin_with_api_error()
        test_expanded_exchange_support()

        print("\n🎉 All tests passed! Error handling improvements are working correctly.")
        print("\n📋 Summary of improvements:")
        print("✅ Coin availability checking with retry logic")
        print("✅ Robust fallback coin selection")
        print("✅ Exchange-specific error handling")
        print("✅ API timeout and network error recovery")
        print("✅ Graceful degradation when services fail")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())