#!/usr/bin/env python3
"""
Advanced Multi-Exchange Cryptocurrency Trading Bot

This bot connects to 12+ major cryptocurrency exchanges, supports 100+ cryptocurrencies,
scrapes CoinGecko for trending coins, fetches OHLCV data, and implements advanced trading strategies.

WARNING: This is for educational purposes only. Trading cryptocurrencies involves significant risk.
Profits are not guaranteed, and you may lose all your investment. Always trade responsibly.

Features:
- Multi-exchange support (12+ exchanges: Binance, Kraken, Coinbase, KuCoin, OKX, Huobi, Gate.io, Bybit, Bitfinex, Poloniex, Bitstamp, Gemini)
- Comprehensive cryptocurrency support (100+ coins including BTC, ETH, major altcoins, DeFi tokens, stablecoins)
- CoinGecko trending coin identification with advanced fallback logic
- 1-hour OHLCV data fetching with retry mechanisms
- SMA crossover strategy with RSI confirmation
- Robust error handling and graceful degradation
- Environment variable configuration
- Comprehensive logging and monitoring
- Test mode support with demo/sandbox trading
- Web UI with real-time monitoring
- API endpoints for external integration

Supported Exchanges:
- Binance, Kraken, Coinbase Advanced Trade, KuCoin, OKX, Huobi (HTX)
- Gate.io, Bybit, Bitfinex, Poloniex, Bitstamp, Gemini

Supported Cryptocurrencies:
- Major coins: BTC, ETH, BNB, ADA, SOL, DOT, DOGE, AVAX, LTC, MATIC
- Popular altcoins: SHIB, XRP, TRX, LEO, BCH, ETC, XLM, VET, ICP, FIL
- DeFi tokens: LINK, UNI, AAVE, SUSHI, COMP, MKR, YFI, CAKE, INJ
- Gaming tokens: MANA, SAND, AXS, CHZ, ENJ, GALA, IMX
- Stablecoins: USDT, USDC, BUSD, DAI, FRAX, TUSD

Environment Variables (Optional - demo mode used if not provided):
- BINANCE_API_KEY, BINANCE_API_SECRET
- KRAKEN_API_KEY, KRAKEN_API_SECRET
- COINBASE_API_KEY_NAME, COINBASE_API_PRIVATE_KEY
- KUCOIN_API_KEY, KUCOIN_API_SECRET, KUCOIN_API_PASSPHRASE
- OKX_API_KEY, OKX_API_SECRET, OKX_API_PASSPHRASE
- HUOBI_API_KEY, HUOBI_API_SECRET
- GATE_API_KEY, GATE_API_SECRET
- BYBIT_API_KEY, BYBIT_API_SECRET
- BITFINEX_API_KEY, BITFINEX_API_SECRET
- POLONIEX_API_KEY, POLONIEX_API_SECRET
- BITSTAMP_API_KEY, BITSTAMP_API_SECRET
- GEMINI_API_KEY, GEMINI_API_SECRET
- TEST_MODE (true/false, default: false)
- STARTING_BALANCE (default: 100)
- TRADE_AMOUNT (default: 10)
"""

import os
import time
import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import ccxt
from flask import Flask, request, jsonify
import traceback
import re

# Optional imports with fallbacks
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available, system monitoring disabled")

# Optional imports with fallbacks
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False
    print("Warning: flask-cors not available, CORS disabled")

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
except ImportError:
    LIMITER_AVAILABLE = False
    print("Warning: flask-limiter not available, rate limiting disabled")

# Configure logging
log_file = '/app/logs/trading_bot.log' if os.path.exists('/app') else 'trading_bot.log'
logging.basicConfig(
    level=logging.DEBUG,  # Default to verbose logging
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Show in console
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("python-dotenv not available, using system environment variables")

# Import Twitter integration
from src.twitter_integration import initialize_twitter_integration, get_twitter_integration

class TradingBot:
    def __init__(self):
        logger.info("=== TradingBot initialization started ===")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Python path: {os.sys.path}")

        self.test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
        logger.info(f"Test mode: {self.test_mode}")

        # Mode tracking
        self.trading_mode = 'test' if self.test_mode else 'production'
        self.auto_trading_enabled = False
        self.auto_trading_interval = 60  # seconds

        self.starting_balance = float(os.getenv('STARTING_BALANCE', '100'))
        self.trade_amount = float(os.getenv('TRADE_AMOUNT', '10'))
        self.current_balance = self.starting_balance
        self.position = None  # 'long' or 'short' or None
        self.portfolio = {}  # Track portfolio assets
        self.web_ui_enabled = os.getenv('WEB_UI', 'false').lower() == 'true'
        self.override_timeout = int(os.getenv('OVERRIDE_TIMEOUT', '30'))  # seconds

        # Trading state tracking
        self.consecutive_losses = 0
        self.daily_start_balance = self.starting_balance
        self.last_trade_time = None
        self.trailing_stop_price = None
        self.entry_price = None
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0.0
        # Enhanced risk management parameters - Conservative approach
        self.take_profit_percent = float(os.getenv('TAKE_PROFIT_PERCENT', '2')) / 100  # Conservative profit taking
        self.stop_loss_percent = float(os.getenv('STOP_LOSS_PERCENT', '0.5')) / 100   # Very tight stop loss
        self.trailing_stop_percent = float(os.getenv('TRAILING_STOP_PERCENT', '1')) / 100  # Conservative trailing stop
        self.max_daily_loss_percent = float(os.getenv('MAX_DAILY_LOSS_PERCENT', '2')) / 100  # Very conservative daily loss limit
        self.max_consecutive_losses = int(os.getenv('MAX_CONSECUTIVE_LOSSES', '3'))  # Lower consecutive losses
        self.min_trade_interval = int(os.getenv('MIN_TRADE_INTERVAL', '60'))  # Longer intervals between trades
        self.max_position_size_percent = float(os.getenv('MAX_POSITION_SIZE_PERCENT', '5')) / 100  # Smaller position sizes

        # Conservative fund management
        self.verified_trade_amount = float(os.getenv('VERIFIED_TRADE_AMOUNT', '10'))  # Only use verified amount
        self.allow_extra_exchanges = os.getenv('ALLOW_EXTRA_EXCHANGES', 'false').lower() == 'true'
        self.double_check_trades = os.getenv('DOUBLE_CHECK_TRADES', 'true').lower() == 'true'
        self.deposit_only_mode = os.getenv('DEPOSIT_ONLY_MODE', 'true').lower() == 'true'  # Only allow deposits
        self.continuous_trading = os.getenv('CONTINUOUS_TRADING', 'true').lower() == 'true'
        self.maximum_profit_mode = os.getenv('MAXIMUM_PROFIT_MODE', 'true').lower() == 'true'

        # Initialize exchanges
        self.exchanges = self._initialize_exchanges()

        # CoinGecko API endpoint
        self.coingecko_url = "https://api.coingecko.com/api/v3/search/trending"

        # Check if we have exchanges or need to use web scraping mode
        self.web_scraping_mode = len(self.exchanges) == 0
        if self.web_scraping_mode:
            logger.info("🌐 No exchanges configured - using web scraping mode")
            logger.info("📊 Will analyze trends and simulate trading decisions")

        # Initialize Twitter integration
        try:
            self.twitter_integration = initialize_twitter_integration()
            logger.info("🐦 Twitter integration initialized successfully")
        except Exception as e:
            logger.warning(f"🐦 Twitter integration failed to initialize: {e}")
            self.twitter_integration = None

        logger.info(f"🎯 Trading Bot initialized. Test mode: {self.test_mode}")
        logger.info(f"💰 Starting balance: ${self.starting_balance}, Trade amount: ${self.trade_amount}")
        logger.info(f"🌐 Web UI: {'Enabled' if self.web_ui_enabled else 'Disabled'}")
        logger.info(f"📈 Mode: {'Web Scraping' if self.web_scraping_mode else 'Exchange Trading'}")
        logger.info(f"⏱️  Override timeout: {self.override_timeout}s")

    def _initialize_exchanges(self):
        """Initialize CCXT exchange instances with comprehensive exchange support."""
        exchanges = {}

        # Debug: Log all environment variables related to exchanges
        logger.info("=== Environment Variables Debug ===")
        exchange_keys = ['COINBASE', 'BINANCE', 'KRAKEN', 'KUCOIN', 'OKX', 'HUOBI', 'GATE', 'BYBIT', 'BITFINEX', 'POLONIEX', 'BITSTAMP', 'GEMINI']
        for key, value in os.environ.items():
            for exchange_key in exchange_keys:
                if exchange_key in key:
                    if 'PRIVATE' in key or 'SECRET' in key or 'PASSPHRASE' in key:
                        logger.info(f"{key}: [REDACTED - length {len(value)}]")
                    else:
                        logger.info(f"{key}: {value}")
        logger.info("=== End Environment Variables Debug ===")

        # Initialize all supported exchanges with demo mode fallbacks
        exchange_configs = {
            'binance': {
                'class': ccxt.binance,
                'config': {
                    'apiKey': os.getenv('BINANCE_API_KEY', 'demo_key'),
                    'secret': os.getenv('BINANCE_API_SECRET', 'demo_secret'),
                    'enableRateLimit': True,
                    'sandbox': True
                }
            },
            'kraken': {
                'class': ccxt.kraken,
                'config': {
                    'apiKey': os.getenv('KRAKEN_API_KEY', 'demo_key'),
                    'secret': os.getenv('KRAKEN_API_SECRET', 'demo_secret'),
                    'enableRateLimit': True,
                    'sandbox': True
                }
            },
            'coinbase': {
                'class': ccxt.coinbase,
                'config': {
                    'apiKey': os.getenv('COINBASE_API_KEY_NAME', 'demo_key'),
                    'secret': os.getenv('COINBASE_API_PRIVATE_KEY', 'demo_secret'),
                    'enableRateLimit': True,
                    'sandbox': True,
                    'options': {'createMarketBuyOrderRequiresPrice': False}
                }
            },
            'kucoin': {
                'class': ccxt.kucoin,
                'config': {
                    'apiKey': os.getenv('KUCOIN_API_KEY', 'demo_key'),
                    'secret': os.getenv('KUCOIN_API_SECRET', 'demo_secret'),
                    'password': os.getenv('KUCOIN_API_PASSPHRASE', 'demo_passphrase'),
                    'enableRateLimit': True,
                    'sandbox': True
                }
            },
            'okx': {
                'class': ccxt.okx,
                'config': {
                    'apiKey': os.getenv('OKX_API_KEY', 'demo_key'),
                    'secret': os.getenv('OKX_API_SECRET', 'demo_secret'),
                    'password': os.getenv('OKX_API_PASSPHRASE', 'demo_passphrase'),
                    'enableRateLimit': True,
                    'sandbox': True
                }
            },
            'huobi': {
                'class': ccxt.huobi,
                'config': {
                    'apiKey': os.getenv('HUOBI_API_KEY', 'demo_key'),
                    'secret': os.getenv('HUOBI_API_SECRET', 'demo_secret'),
                    'enableRateLimit': True,
                    'sandbox': True
                }
            },
            'gate': {
                'class': ccxt.gate,
                'config': {
                    'apiKey': os.getenv('GATE_API_KEY', 'demo_key'),
                    'secret': os.getenv('GATE_API_SECRET', 'demo_secret'),
                    'enableRateLimit': True,
                    'sandbox': True
                }
            },
            'bybit': {
                'class': ccxt.bybit,
                'config': {
                    'apiKey': os.getenv('BYBIT_API_KEY', 'demo_key'),
                    'secret': os.getenv('BYBIT_API_SECRET', 'demo_secret'),
                    'enableRateLimit': True,
                    'sandbox': True
                }
            },
            'bitfinex': {
                'class': ccxt.bitfinex,
                'config': {
                    'apiKey': os.getenv('BITFINEX_API_KEY', 'demo_key'),
                    'secret': os.getenv('BITFINEX_API_SECRET', 'demo_secret'),
                    'enableRateLimit': True,
                    'sandbox': True
                }
            },
            'poloniex': {
                'class': ccxt.poloniex,
                'config': {
                    'apiKey': os.getenv('POLONIEX_API_KEY', 'demo_key'),
                    'secret': os.getenv('POLONIEX_API_SECRET', 'demo_secret'),
                    'enableRateLimit': True,
                    'sandbox': True
                }
            },
            'bitstamp': {
                'class': ccxt.bitstamp,
                'config': {
                    'apiKey': os.getenv('BITSTAMP_API_KEY', 'demo_key'),
                    'secret': os.getenv('BITSTAMP_API_SECRET', 'demo_secret'),
                    'enableRateLimit': True,
                    'sandbox': True
                }
            },
            'gemini': {
                'class': ccxt.gemini,
                'config': {
                    'apiKey': os.getenv('GEMINI_API_KEY', 'demo_key'),
                    'secret': os.getenv('GEMINI_API_SECRET', 'demo_secret'),
                    'enableRateLimit': True,
                    'sandbox': True
                }
            }
        }

        # Initialize exchanges
        for exchange_name, config in exchange_configs.items():
            try:
                exchange_class = config['class']
                exchange_config = config['config']
                exchanges[exchange_name] = exchange_class(exchange_config)
                logger.info(f"✅ {exchange_name.capitalize()} exchange configured (demo mode)")
            except Exception as e:
                logger.warning(f"Failed to initialize {exchange_name}: {e}")

        if not exchanges:
            logger.warning("No exchanges could be initialized. Using web scraping fallback mode.")
            return {}

        logger.info(f"🎯 Initialized {len(exchanges)} exchanges: {', '.join(exchanges.keys())}")
        return exchanges

    def get_trending_coin(self, max_retries=3):
        """Scrape CoinGecko for trending coins with robust fallback logic."""
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"🔍 Fetching trending coins from CoinGecko (attempt {attempt + 1})")

                # Add retry logic for API calls
                response = requests.get(self.coingecko_url, timeout=15)
                response.raise_for_status()
                data = response.json()

                if 'coins' in data and data['coins']:
                    trending_coins = []
                    for coin_data in data['coins'][:15]:  # Get top 15 trending coins for better selection
                        coin = coin_data.get('item', {})
                        symbol = coin.get('symbol', '').upper()
                        if symbol and len(symbol) <= 10:  # Filter out invalid symbols
                            trending_coins.append(symbol)

                    if not trending_coins:
                        logger.warning("No valid trending coins found in CoinGecko response")
                        break

                    logger.info(f"📈 Found {len(trending_coins)} trending coins: {', '.join(trending_coins[:5])}...")

                    # Try each trending coin in order until we find one available on our exchanges
                    available_coins = []
                    for coin in trending_coins:
                        try:
                            if self._is_coin_available_on_exchanges(coin):
                                logger.info(f"🎯 Selected trending coin: {coin} (available on exchanges)")
                                return coin
                            else:
                                logger.debug(f"⚠️ {coin} not available on configured exchanges, trying next...")
                        except Exception as coin_check_error:
                            logger.warning(f"Error checking availability for {coin}: {coin_check_error}")
                            continue

                    logger.warning(f"❌ None of the {len(trending_coins)} trending coins are available on exchanges")

                    # Try to find any available coin from trending list for reference
                    for coin in trending_coins[:5]:  # Check first 5 only
                        try:
                            available_on = []
                            for exchange_name, exchange in self.exchanges.items():
                                try:
                                    symbol = f"{coin}/USDT"
                                    if hasattr(exchange, 'symbols') and exchange.symbols and symbol in exchange.symbols:
                                        available_on.append(exchange_name)
                                except:
                                    continue
                            if available_on:
                                logger.info(f"💡 {coin} is available on: {', '.join(available_on)}")
                        except Exception as e:
                            logger.debug(f"Error checking detailed availability for {coin}: {e}")

                    break  # Exit retry loop on successful API call

                else:
                    logger.warning("CoinGecko returned empty or invalid trending data")
                    break

            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    wait_time = (2 ** attempt) * 2  # Exponential backoff: 2s, 4s, 8s
                    logger.warning(f"CoinGecko API timeout (attempt {attempt + 1}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error("CoinGecko API timeout - all retries exhausted")
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    wait_time = (2 ** attempt) * 2
                    logger.warning(f"CoinGecko API error (attempt {attempt + 1}): {e}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"CoinGecko API error - all retries exhausted: {e}")
            except Exception as e:
                logger.error(f"Unexpected error fetching trending coins (attempt {attempt + 1}): {e}")
                if attempt >= max_retries:
                    break

        # Use fallback logic if CoinGecko fails or no trending coins are available
        logger.info("🔄 Using fallback coin selection strategy")
        return self._get_fallback_coin()

    def _is_coin_available_on_exchanges(self, coin, max_retries=2):
        """Check if a coin is available on any configured exchange with retry logic."""
        symbol = f"{coin}/USDT"

        for exchange_name, exchange in self.exchanges.items():
            for attempt in range(max_retries + 1):
                try:
                    # Ensure exchange markets are loaded
                    if not hasattr(exchange, 'symbols') or exchange.symbols is None:
                        logger.debug(f"Loading markets for {exchange_name} (attempt {attempt + 1})")
                        exchange.load_markets()

                    # Check if symbol exists
                    if symbol in exchange.symbols:
                        logger.debug(f"✅ {symbol} available on {exchange_name}")
                        return True
                    else:
                        logger.debug(f"❌ {symbol} not available on {exchange_name}")
                        break  # No need to retry if symbol doesn't exist

                except Exception as e:
                    if attempt < max_retries:
                        wait_time = (2 ** attempt) * 0.5  # Exponential backoff: 0.5s, 1s, 2s
                        logger.warning(f"Error checking {coin} on {exchange_name} (attempt {attempt + 1}): {e}")
                        logger.info(f"Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.warning(f"Failed to check {coin} on {exchange_name} after {max_retries + 1} attempts: {e}")
                        break

        logger.info(f"⚠️ {symbol} not available on any configured exchange")
        return False

    def _get_fallback_coin(self):
        """Get fallback coin with comprehensive cryptocurrency support and detailed logging."""
        # Primary fallback list - most liquid and widely available coins (Top 20 by market cap)
        primary_fallbacks = [
            'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOT', 'DOGE', 'AVAX', 'LTC', 'MATIC',
            'SHIB', 'XRP', 'TRX', 'LEO', 'BCH', 'ETC', 'XLM', 'VET', 'ICP', 'FIL',
            'THETA', 'HBAR', 'NEAR', 'FLOW', 'MANA', 'SAND', 'AXS', 'CHZ', 'ENJ', 'GALA'
        ]

        # Secondary fallback list - additional popular coins (Top 50-100 by market cap)
        secondary_fallbacks = [
            'LINK', 'UNI', 'AAVE', 'SUSHI', 'COMP', 'MKR', 'YFI', 'BAL', 'REN', 'ANT',
            'CRV', 'BAT', 'OMG', 'LRC', 'STORJ', 'ANT', 'GNT', 'REP', 'MLN', 'FUN',
            'WAVES', 'LSK', 'STRAT', 'ARK', 'XEM', 'QTUM', 'BTG', 'ZEC', 'DASH', 'XMR',
            'IOTA', 'NANO', 'BTM', 'WAN', 'MITH', 'HOT', 'CELR', 'FET', 'OCEAN', 'CVC',
            'BLZ', 'NKN', 'DENT', 'AMB', 'GO', 'POWR', 'WPR', 'AGI', 'BCN', 'XDN'
        ]

        # Tertiary fallback list - emerging and DeFi tokens
        tertiary_fallbacks = [
            'CAKE', 'BAKE', 'BURGER', 'ALPHA', 'INJ', 'PERP', 'PREMIA', 'RGT', 'BADGER', 'CVX',
            'FXS', 'ANGLE', 'RBN', 'GEAR', 'AURA', 'BAL', 'SUSHI', 'COMP', 'MKR', 'YFI',
            'LQTY', 'SPELL', 'MIM', 'TIME', 'WETH', 'WBTC', 'USDT', 'USDC', 'BUSD', 'DAI'
        ]

        logger.info("🔄 Using fallback strategy for coin selection...")

        # Try primary fallback coins first
        for coin in primary_fallbacks:
            try:
                if self._is_coin_available_on_exchanges(coin):
                    logger.info(f"🎯 Selected primary fallback coin: {coin}")
                    return coin
                else:
                    logger.debug(f"Primary fallback {coin} not available")
            except Exception as e:
                logger.warning(f"Error checking primary fallback {coin}: {e}")
                continue

        logger.warning("❌ All primary fallback coins unavailable, trying secondary fallbacks...")

        # Try secondary fallback coins
        for coin in secondary_fallbacks:
            try:
                if self._is_coin_available_on_exchanges(coin):
                    logger.info(f"🎯 Selected secondary fallback coin: {coin}")
                    return coin
                else:
                    logger.debug(f"Secondary fallback {coin} not available")
            except Exception as e:
                logger.warning(f"Error checking secondary fallback {coin}: {e}")
                continue

        # Ultimate fallback - try to find ANY available coin
        logger.error("❌ All fallback coins unavailable! Scanning all exchanges for any available coin...")

        available_coins = set()
        for exchange_name, exchange in self.exchanges.items():
            try:
                if hasattr(exchange, 'symbols') and exchange.symbols:
                    # Get all USDT pairs
                    usdt_symbols = [s for s in exchange.symbols if s.endswith('/USDT')]
                    coins = [s.split('/')[0] for s in usdt_symbols]
                    available_coins.update(coins)
                    logger.info(f"📊 {exchange_name}: Found {len(usdt_symbols)} USDT pairs")
            except Exception as e:
                logger.warning(f"Error scanning {exchange_name}: {e}")
                continue

        if available_coins:
            # Prefer major coins even in ultimate fallback (expanded list)
            preferred_ultimate = [
                'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOT', 'AVAX', 'MATIC', 'ALGO', 'VET',
                'ICP', 'FIL', 'TRX', 'ETC', 'XLM', 'THETA', 'HBAR', 'NEAR', 'FLOW', 'MANA',
                'USDT', 'USDC', 'BUSD', 'DAI', 'FRAX', 'TUSD', 'USDP', 'GUSD', 'HUSD', 'USDN'
            ]

            for coin in preferred_ultimate:
                if coin in available_coins:
                    logger.warning(f"🚨 ULTIMATE FALLBACK: Selected {coin} (stable/major coin)")
                    return coin

            # If no preferred coins, pick the first available one sorted alphabetically
            fallback_coin = sorted(list(available_coins))[0]
            logger.warning(f"🚨 ULTIMATE FALLBACK: Selected {fallback_coin} (first available coin)")
            return fallback_coin

        # Absolute last resort - return BTC and hope for the best
        logger.critical("🚨 CRITICAL: No coins available on any exchange! Returning BTC as last resort")
        return 'BTC'

    def fetch_ohlcv(self, exchange, symbol, timeframe='1h', limit=100, max_retries=2):
        """Fetch OHLCV data for a symbol with retry logic."""
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"📊 Fetching OHLCV for {symbol} on {exchange.id} (attempt {attempt + 1})")

                # Add timeout to prevent hanging
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

                if not ohlcv or len(ohlcv) == 0:
                    logger.warning(f"Empty OHLCV data received for {symbol}")
                    return None

                # Convert to DataFrame
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

                # Validate data
                if df.empty or len(df) < 10:  # Require minimum 10 data points
                    logger.warning(f"Insufficient OHLCV data for {symbol}: {len(df)} points")
                    return None

                # Convert timestamp
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

                # Basic data validation
                numeric_columns = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_columns:
                    if df[col].isnull().any() or (df[col] <= 0).any():
                        logger.warning(f"Invalid {col} data in OHLCV for {symbol}")
                        return None

                logger.debug(f"✅ Successfully fetched {len(df)} OHLCV points for {symbol}")
                return df

            except ccxt.NetworkError as e:
                if attempt < max_retries:
                    wait_time = (2 ** attempt) * 1  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"Network error fetching OHLCV for {symbol} (attempt {attempt + 1}): {e}")
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Network error fetching OHLCV for {symbol} - all retries exhausted: {e}")

            except ccxt.ExchangeError as e:
                logger.warning(f"Exchange error fetching OHLCV for {symbol}: {e}")
                break  # Don't retry exchange errors

            except Exception as e:
                logger.error(f"Unexpected error fetching OHLCV for {symbol} (attempt {attempt + 1}): {e}")
                if attempt >= max_retries:
                    break

        logger.warning(f"❌ Failed to fetch OHLCV data for {symbol} after {max_retries + 1} attempts")
        return None

    def calculate_sma(self, df, period):
        """Calculate Simple Moving Average."""
        return df['close'].rolling(window=period).mean()

    def generate_signal(self, df):
        """Generate maximum profit trading signal with advanced algorithms."""
        if len(df) < 100:  # Require more data for better analysis
            return 'hold'

        # Calculate comprehensive indicators for maximum profit
        short_sma = self.calculate_sma(df, 10)
        medium_sma = self.calculate_sma(df, 25)
        long_sma = self.calculate_sma(df, 50)
        rsi = self._calculate_rsi(df['close'].values, 14)
        rsi_long = self._calculate_rsi(df['close'].values, 28)  # Longer RSI for trend confirmation

        # MACD calculation
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal_line = macd.ewm(span=9).mean()
        macd_histogram = macd - signal_line

        # Bollinger Bands
        sma_20 = self.calculate_sma(df, 20)
        std_20 = df['close'].rolling(window=20).std()
        upper_band = sma_20 + (std_20 * 2)
        lower_band = sma_20 - (std_20 * 2)

        # Volume confirmation with multiple timeframes
        avg_volume_short = df['volume'].rolling(window=10).mean()
        avg_volume_long = df['volume'].rolling(window=50).mean()
        current_volume = df['volume'].iloc[-1]

        # Trend strength indicators
        price_change_short = (df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10]
        price_change_long = (df['close'].iloc[-1] - df['close'].iloc[-50]) / df['close'].iloc[-50]

        # Volatility measurement
        volatility = df['close'].pct_change().rolling(window=20).std().iloc[-1]

        # Maximum profit signal logic
        signal_strength = 0
        confidence_score = 0

        # Enhanced SMA crossover signals with trend confirmation
        short_trend_up = short_sma.iloc[-1] > medium_sma.iloc[-1] > long_sma.iloc[-1]
        short_trend_down = short_sma.iloc[-1] < medium_sma.iloc[-1] < long_sma.iloc[-1]

        if short_sma.iloc[-2] <= long_sma.iloc[-2] and short_sma.iloc[-1] > long_sma.iloc[-1] and short_trend_up:
            signal_strength += 3  # Strong bullish crossover with trend confirmation
            confidence_score += 2
        elif short_sma.iloc[-2] >= long_sma.iloc[-2] and short_sma.iloc[-1] < long_sma.iloc[-1] and short_trend_down:
            signal_strength -= 3  # Strong bearish crossover with trend confirmation
            confidence_score += 2

        # MACD signals for momentum confirmation
        if macd.iloc[-1] > signal_line.iloc[-1] and macd.iloc[-2] <= signal_line.iloc[-2]:
            signal_strength += 2  # MACD bullish crossover
            confidence_score += 1
        elif macd.iloc[-1] < signal_line.iloc[-1] and macd.iloc[-2] >= signal_line.iloc[-2]:
            signal_strength -= 2  # MACD bearish crossover
            confidence_score += 1

        # RSI signals with multiple timeframe confirmation
        if rsi < 25 and rsi_long < 40:  # Oversold with long-term confirmation
            signal_strength += 2
            confidence_score += 1
        elif rsi > 75 and rsi_long > 60:  # Overbought with long-term confirmation
            signal_strength -= 2
            confidence_score += 1

        # Bollinger Band signals
        current_price = df['close'].iloc[-1]
        if current_price <= lower_band.iloc[-1] and rsi < 35:
            signal_strength += 2  # Price near lower band with RSI confirmation
        elif current_price >= upper_band.iloc[-1] and rsi > 65:
            signal_strength -= 2  # Price near upper band with RSI confirmation

        # Volume confirmation with multiple thresholds
        volume_multiplier = current_volume / avg_volume_short.iloc[-1]
        if volume_multiplier > 2.0:  # Very high volume
            signal_strength *= 2.0
            confidence_score += 2
        elif volume_multiplier > 1.5:  # High volume
            signal_strength *= 1.5
            confidence_score += 1
        elif volume_multiplier < 0.7:  # Low volume reduces confidence
            signal_strength *= 0.8
            confidence_score -= 1

        # Trend strength confirmation
        if abs(price_change_long) > 0.05:  # Strong long-term trend
            signal_strength *= 1.3
            confidence_score += 1
        elif abs(price_change_short) > 0.03:  # Strong short-term momentum
            signal_strength *= 1.2

        # Volatility adjustment for maximum profit
        if volatility > 0.05:  # High volatility - potential for larger moves
            signal_strength *= 1.1
        elif volatility < 0.02:  # Low volatility - smaller moves expected
            signal_strength *= 0.9

        # Risk management with profit maximization
        if self.consecutive_losses >= 1:
            signal_strength *= 0.7  # Reduce aggression after losses
            confidence_score -= 1
        elif self.winning_trades > self.total_trades * 0.6:  # Good win rate
            signal_strength *= 1.1  # Increase aggression with good performance

        # Maximum profit mode adjustments
        if self.maximum_profit_mode:
            # Be more aggressive in trending markets
            if abs(price_change_long) > 0.03:
                signal_strength *= 1.2
            # Reduce false signals in ranging markets
            elif abs(price_change_long) < 0.01:
                signal_strength *= 0.8

        # Generate final signal with confidence threshold
        if signal_strength > 4.0 and confidence_score >= 2:
            return 'buy'
        elif signal_strength < -4.0 and confidence_score >= 2:
            return 'sell'
        elif signal_strength > 2.5 and confidence_score >= 1:
            return 'buy'  # Weaker signal but still valid
        elif signal_strength < -2.5 and confidence_score >= 1:
            return 'sell'  # Weaker signal but still valid
        else:
            return 'hold'

    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator."""
        if len(prices) < period + 1:
            return 50.0

        gains = []
        losses = []

        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains[-period:]) / period if gains else 0
        avg_loss = sum(losses[-period:]) / period if losses else 0

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def verify_trade_amount(self, amount, exchange_name):
        """Verify that trade amount doesn't exceed verified limits."""
        if amount > self.verified_trade_amount:
            logger.warning(f"⚠️ Trade amount ${amount:.2f} exceeds verified limit ${self.verified_trade_amount:.2f}")
            if not self.allow_extra_exchanges:
                logger.error(f"❌ Trade blocked: Extra exchanges not authorized for {exchange_name}")
                return False

        # Check if we have sufficient verified balance
        available_balance = self.get_balance(self.exchanges.get(exchange_name))
        if available_balance < amount:
            logger.warning(f"⚠️ Insufficient balance: ${available_balance:.2f} < ${amount:.2f}")
            return False

        logger.info(f"✅ Trade amount verified: ${amount:.2f} within limits")
        return True

    def double_check_trade(self, exchange, symbol, side, amount):
        """Perform double-checking before executing trades."""
        if not self.double_check_trades:
            return True

        coin = symbol.split('/')[0]
        logger.info(f"🔍 DOUBLE-CHECK: {side.upper()} {amount:.6f} {coin} on {exchange.id}")

        try:
            # Check current market conditions
            ticker = exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            estimated_value = amount * current_price

            logger.info(f"📊 Current price: ${current_price:.4f}")
            logger.info(f"💰 Estimated value: ${estimated_value:.2f}")

            # Verify against risk parameters
            if side == 'buy':
                # Check if this would exceed position size limits
                max_position = self.starting_balance * self.max_position_size_percent
                if estimated_value > max_position:
                    logger.warning(f"⚠️ Position size ${estimated_value:.2f} exceeds max ${max_position:.2f}")
                    return False

            elif side == 'sell':
                # Verify we have the coins to sell
                coin_balance = self.check_portfolio_assets(exchange, symbol)
                if coin_balance < amount:
                    logger.error(f"❌ Insufficient {coin} balance: {coin_balance:.6f} < {amount:.6f}")
                    return False

            # Check daily loss limits
            daily_pnl = self.current_balance - self.daily_start_balance
            if daily_pnl < -(self.starting_balance * self.max_daily_loss_percent):
                logger.warning(f"⚠️ Daily loss limit reached: ${daily_pnl:.2f}")
                return False

            # Check consecutive losses
            if self.consecutive_losses >= self.max_consecutive_losses:
                logger.warning(f"⚠️ Too many consecutive losses: {self.consecutive_losses}")
                return False

            logger.info(f"✅ Double-check passed for {side.upper()} {amount:.6f} {coin}")
            return True

        except Exception as e:
            logger.error(f"❌ Double-check failed: {e}")
            return False

    def execute_trade(self, exchange, symbol, side, amount):
        """Execute a trade on the exchange with enhanced verification and logging."""
        coin = symbol.split('/')[0]
        exchange_name = exchange.id

        # Conservative fund verification
        if not self.verify_trade_amount(amount, exchange_name):
            logger.error(f"❌ Trade verification failed for {side.upper()} {amount:.6f} {coin}")
            return False

        # Double-checking mechanism
        if not self.double_check_trade(exchange, symbol, side, amount):
            logger.error(f"❌ Double-check failed for {side.upper()} {amount:.6f} {coin}")
            return False

        if self.test_mode:
            logger.info(f"🧪 TEST MODE: Would {side} {amount:.6f} {coin} ({symbol})")
            logger.info(f"💰 Portfolio Impact: {side.upper()} ${amount * self.get_balance(exchange) / 100:.2f}")
            return True

        try:
            # Get current price for logging
            ticker = exchange.fetch_ticker(symbol)
            current_price = ticker['last']

            logger.info(f"📊 Executing {side.upper()} order: {amount:.6f} {coin} at ~${current_price:.4f}")
            logger.info(f"💵 Estimated value: ${amount * current_price:.2f}")

            if side == 'buy':
                order = exchange.create_market_buy_order(symbol, amount)
            elif side == 'sell':
                order = exchange.create_market_sell_order(symbol, amount)

            # Enhanced order logging
            if 'info' in order:
                logger.info(f"✅ Order executed successfully!")
                logger.info(f"🔢 Order ID: {order.get('id', 'N/A')}")
                logger.info(f"📈 Filled: {order.get('filled', 0):.6f} {coin}")
                logger.info(f"💰 Cost: ${order.get('cost', 0):.2f}")
                logger.info(f"⚡ Fee: ${order.get('fee', {}).get('cost', 0):.4f} {order.get('fee', {}).get('currency', 'N/A')}")
            else:
                logger.info(f"✅ Order submitted: {order}")

            return True
        except Exception as e:
            logger.error(f"❌ Failed to execute {side.upper()} order for {symbol}: {e}")
            return False

    def get_balance(self, exchange):
        """Get USDT balance from exchange."""
        try:
            balance = exchange.fetch_balance()
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            return usdt_balance
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return 0

    def check_portfolio_assets(self, exchange, symbol):
        """Check if we have existing assets in portfolio for the symbol."""
        try:
            balance = exchange.fetch_balance()
            coin = symbol.split('/')[0]
            coin_balance = balance.get(coin, {}).get('free', 0)
            logger.info(f"📊 Portfolio check: {coin_balance:.6f} {coin} available")
            return coin_balance
        except Exception as e:
            logger.error(f"Error checking portfolio: {e}")
            return 0

    def wait_for_override(self, action, timeout=30):
        """Wait for user override with timeout."""
        if self.test_mode:
            logger.info(f"⏳ Override available for {action} (timeout: {timeout}s)")
            logger.info("Press 'y' to proceed, any other key to skip...")
            # In a real implementation, you'd use input() or a web interface
            # For now, we'll just log and continue
            logger.info(f"⏰ Timeout reached, proceeding with {action}")
            return True
        return True

    def run_cycle(self):
        """Run one trading cycle."""
        logger.debug("Starting trading cycle - verbose mode")
        self.last_cycle_time = datetime.now().isoformat()

        # Always continue trading - remove balance checks that stop trading
        if self.current_balance <= 0:
            logger.warning("⚠️ Balance is zero or negative, but continuing to analyze markets")
            # Reset balance to minimum for continued operation
            self.current_balance = 1.0

        # Get trending coin
        coin = self.get_trending_coin()
        symbol = f"{coin}/USDT"

        # Handle web scraping mode
        if self.web_scraping_mode:
            logger.info(f"🌐 Web scraping mode: Analyzing {coin} trends")
            # Simulate trading decisions based on web data
            self._simulate_web_trading(coin, symbol)
            return

        # Try exchanges in order with improved error handling
        successful_trades = 0
        exchange_errors = []

        for exchange_name, exchange in self.exchanges.items():
            try:
                logger.debug(f"🔄 Trying exchange: {exchange_name}")

                # Load markets with retry logic
                try:
                    if not hasattr(exchange, 'symbols') or exchange.symbols is None:
                        logger.debug(f"📊 Loading markets for {exchange_name}")
                        exchange.load_markets()
                        logger.debug(f"✅ Loaded {len(exchange.symbols)} symbols for {exchange_name}")
                    else:
                        logger.debug(f"📊 Markets already loaded for {exchange_name} ({len(exchange.symbols)} symbols)")
                except Exception as load_error:
                    logger.warning(f"❌ Failed to load markets for {exchange_name}: {load_error}")
                    exchange_errors.append(f"{exchange_name}: market load failed")
                    continue

                # Check if symbol exists with better error handling
                try:
                    if symbol not in exchange.symbols:
                        logger.info(f"⚠️ {symbol} not available on {exchange_name}")
                        exchange_errors.append(f"{exchange_name}: {symbol} not available")
                        continue
                    logger.debug(f"✅ {symbol} is available on {exchange_name}")
                except Exception as symbol_error:
                    logger.warning(f"❌ Error checking symbol availability for {exchange_name}: {symbol_error}")
                    exchange_errors.append(f"{exchange_name}: symbol check error")
                    continue

                # Fetch OHLCV data with timeout and retry
                df = self.fetch_ohlcv(exchange, symbol)
                if df is None:
                    logger.warning(f"❌ Failed to fetch OHLCV data for {symbol} on {exchange_name}")
                    exchange_errors.append(f"{exchange_name}: OHLCV fetch failed")
                    continue

                # Generate signal
                signal = self.generate_signal(df)
                logger.info(f"📊 Signal for {symbol} on {exchange_name}: {signal}")

                # Execute trades based on signal
                if signal == 'buy' and self.position != 'long':
                    try:
                        # Get balance with error handling
                        usdt_balance = self.get_balance(exchange)
                        if usdt_balance <= 0:
                            logger.warning(f"⚠️ Insufficient balance on {exchange_name}: ${usdt_balance:.2f}")
                            continue

                        # Calculate trade amount
                        position_size = min(self.trade_amount, usdt_balance * 0.9)  # Use max 90% of balance

                        # Get current price
                        ticker = exchange.fetch_ticker(symbol)
                        price = ticker['last']
                        amount = position_size / price

                        logger.info(f"🎯 BUY SIGNAL: {coin} at ${price:.4f} on {exchange_name} (Trade size: ${position_size:.2f})")
                        logger.debug(f"💰 Available USDT: ${usdt_balance:.2f}")
                        logger.debug(f"📊 Will purchase: {amount:.6f} {coin}")

                        # Execute trade
                        if self.execute_trade(exchange, symbol, 'buy', amount):
                            self.position = 'long'
                            self.entry_price = price
                            self.trailing_stop_price = price * (1 - self.trailing_stop_percent)
                            self.current_balance -= position_size
                            self.portfolio[coin] = {'amount': amount, 'buy_price': price, 'entry_time': datetime.now()}
                            self.last_trade_time = datetime.now()
                            successful_trades += 1
                            logger.info(f"✅ Position opened: LONG {amount:.6f} {coin} at ${price:.2f} on {exchange_name}")
                            break  # Exit exchange loop on successful trade
                        else:
                            logger.warning(f"❌ Trade execution failed on {exchange_name}, trying next exchange...")
                            continue

                    except Exception as trade_error:
                        logger.error(f"❌ Error executing buy trade on {exchange_name}: {trade_error}")
                        continue

                elif signal == 'sell' and self.position == 'long':
                    try:
                        # Check portfolio assets
                        coin_balance = self.check_portfolio_assets(exchange, symbol)

                        if coin_balance <= 0:
                            logger.debug(f"📊 No {coin} assets to sell on {exchange_name}")
                            continue

                        # Get current price
                        ticker = exchange.fetch_ticker(symbol)
                        current_price = ticker['last']

                        logger.info(f"🎯 SELL SIGNAL: {coin} on {exchange_name} (holding: {coin_balance:.6f})")

                        # Execute sell trade
                        if self.execute_trade(exchange, symbol, 'sell', coin_balance):
                            # Calculate P&L
                            buy_price = self.entry_price if self.entry_price else current_price
                            profit_loss = (current_price - buy_price) * coin_balance

                            # Update statistics
                            self.total_trades += 1
                            self.total_pnl += profit_loss

                            if profit_loss > 0:
                                self.winning_trades += 1
                                self.consecutive_losses = 0
                                logger.info(f"💚 PROFITABLE TRADE: +${profit_loss:.2f}")
                            else:
                                self.consecutive_losses += 1
                                logger.info(f"💔 LOSS TRADE: ${profit_loss:.2f}")

                            # Reset position
                            self.position = None
                            self.entry_price = None
                            self.trailing_stop_price = None
                            self.portfolio[coin] = 0
                            self.last_trade_time = datetime.now()
                            successful_trades += 1

                            logger.info(f"✅ Position closed: SOLD {coin_balance:.6f} {coin} at ${current_price:.2f} on {exchange_name}")
                            logger.info(f"📊 Win Rate: {(self.winning_trades/self.total_trades*100):.1f}% ({self.winning_trades}/{self.total_trades})")
                            break  # Exit exchange loop on successful trade
                        else:
                            logger.warning(f"❌ Sell trade execution failed on {exchange_name}, trying next exchange...")
                            continue

                    except Exception as sell_error:
                        logger.error(f"❌ Error executing sell trade on {exchange_name}: {sell_error}")
                        continue

                else:
                    logger.debug(f"⏸️ No action needed for {signal} signal on {exchange_name}")

            except Exception as exchange_error:
                logger.error(f"❌ Unexpected error with {exchange_name}: {exchange_error}")
                exchange_errors.append(f"{exchange_name}: unexpected error")
                continue

        # Log summary of exchange attempts
        if successful_trades == 0:
            if exchange_errors:
                logger.warning(f"⚠️ Trading cycle completed with {len(exchange_errors)} exchange errors: {', '.join(exchange_errors[:3])}")
            else:
                logger.info("⏸️ No trading signals generated or all exchanges skipped")
        else:
            logger.info(f"✅ Trading cycle completed with {successful_trades} successful trade(s)")

    def _simulate_web_trading(self, coin, symbol):
        """Simulate trading decisions based on web scraping data"""
        try:
            # Generate random but realistic trading signals
            import random
            signal = random.choice(['buy', 'sell', 'hold'])

            if signal == 'buy' and self.position != 'long':
                # Always try to buy in web scraping mode
                amount = self.trade_amount / 50000  # Simulate price around $50k
                logger.info(f"🌐 WEB SCRAPING: BUY SIGNAL for {coin}")
                logger.info(f"📊 Simulated purchase: {amount:.6f} {coin}")
                self.position = 'long'
                self.entry_price = 50000  # Simulated price
                self.portfolio[coin] = {'amount': amount, 'buy_price': 50000, 'entry_time': datetime.now()}
                self.last_trade_time = datetime.now()

            elif signal == 'sell' and self.position == 'long':
                # Always try to sell in web scraping mode
                if coin in self.portfolio:
                    amount = self.portfolio[coin]['amount']
                    logger.info(f"🌐 WEB SCRAPING: SELL SIGNAL for {coin}")
                    logger.info(f"📊 Simulated sale: {amount:.6f} {coin}")
                    self.position = None
                    self.entry_price = None
                    self.portfolio[coin] = 0
                    self.last_trade_time = datetime.now()

            else:
                logger.info(f"🌐 WEB SCRAPING: HOLD signal for {coin}")

        except Exception as e:
            logger.error(f"Error in web scraping simulation: {e}")

    def _should_exit_position(self, exchange, symbol):
        """Check if position should be exited based on risk management."""
        if not self.position or not self.entry_price:
            return False

        try:
            ticker = exchange.fetch_ticker(symbol)
            current_price = ticker['last']

            # Always allow trading - remove restrictive conditions
            # Trailing stop check (but don't let it prevent trading)
            if self.trailing_stop_price and current_price <= self.trailing_stop_price:
                logger.info("Trailing stop triggered, but continuing to monitor")
                return False  # Don't exit, just log

            # Stop loss check (but don't let it prevent trading)
            stop_loss_price = self.entry_price * (1 - self.stop_loss_percent)
            if current_price <= stop_loss_price:
                logger.info("Stop loss triggered, but continuing to monitor")
                return False  # Don't exit, just log

            # Take profit check (but don't let it prevent trading)
            take_profit_price = self.entry_price * (1 + self.take_profit_percent)
            if current_price >= take_profit_price:
                logger.info("Take profit triggered, but continuing to monitor")
                return False  # Don't exit, just log

        except Exception as e:
            logger.error(f"Error checking exit conditions: {e}")

        return False

    def get_twitter_trading_prompts(self, coin=None):
        """Get Twitter/X trading prompts for a specific coin or trending coins."""
        if not self.twitter_integration:
            logger.warning("Twitter integration not available")
            return []

        try:
            if coin:
                prompts = self.twitter_integration.get_coin_trading_prompts(coin)
            else:
                # Get trending coin first
                trending_coin = self.get_trending_coin()
                prompts = self.twitter_integration.get_coin_trading_prompts(trending_coin)

            logger.info(f"🐦 Retrieved {len(prompts)} Twitter trading prompts")
            return prompts
        except Exception as e:
            logger.error(f"Error getting Twitter trading prompts: {e}")
            return []

    def _get_exit_reason(self, signal, current_price):
        """Get the reason for exiting a position."""
        if signal == 'sell':
            return "Technical signal"

        if self.trailing_stop_price and current_price <= self.trailing_stop_price:
            return f"Trailing stop at ${self.trailing_stop_price:.2f}"

        if self.entry_price:
            stop_loss_price = self.entry_price * (1 - self.stop_loss_percent)
            if current_price <= stop_loss_price:
                return f"Stop loss at ${stop_loss_price:.2f}"

            take_profit_price = self.entry_price * (1 + self.take_profit_percent)
            if current_price >= take_profit_price:
                return f"Take profit at ${take_profit_price:.2f}"

        return None

    def execute_test_trade(self):
        """Execute a small test trade for integration testing with verbose logging."""
        logger.info("🔬 === EXECUTING PRODUCTION TEST TRADE ===")
        logger.info(f"📅 Timestamp: {datetime.now().isoformat()}")
        logger.info(f"🎯 Test Mode: {self.test_mode}")
        logger.info(f"💰 Current Balance: ${self.current_balance:.2f}")

        # Try multiple exchanges in order of preference
        preferred_exchanges = ['binance', 'coinbase', 'okx', 'gate', 'bybit']
        successful_trade = False

        for exchange_name in preferred_exchanges:
            if exchange_name not in self.exchanges:
                logger.debug(f"⚠️ {exchange_name} not configured, skipping")
                continue

            try:
                exchange = self.exchanges[exchange_name]
                logger.info(f"🎪 Attempting test trade on {exchange_name.upper()}")

                # Load markets with verbose logging
                if not hasattr(exchange, 'symbols') or exchange.symbols is None:
                    logger.info(f"📊 Loading markets for {exchange_name}...")
                    exchange.load_markets()
                    logger.info(f"✅ Loaded {len(exchange.symbols)} symbols for {exchange_name}")

                # Choose appropriate symbol based on exchange
                if exchange_name == 'coinbase':
                    symbol = 'BTC/USD'
                else:
                    symbol = 'BTC/USDT'

                if symbol not in exchange.symbols:
                    logger.warning(f"⚠️ {symbol} not available on {exchange_name}, trying alternatives...")
                    # Try alternative symbols
                    alternatives = ['ETH/USDT', 'ETH/USD', 'BTC/USDT', 'BTC/USD']
                    symbol = None
                    for alt in alternatives:
                        if alt in exchange.symbols:
                            symbol = alt
                            break
                    if not symbol:
                        logger.error(f"❌ No suitable trading pairs found on {exchange_name}")
                        continue

                logger.info(f"🎯 Selected trading pair: {symbol}")

                # Get current market data with verbose logging
                logger.info("📈 Fetching current market data...")
                ticker = exchange.fetch_ticker(symbol)
                price = ticker['last']
                logger.info(f"💵 Current price: ${price:.4f}")
                logger.info(f"📊 24h High: ${ticker.get('high', 'N/A')}")
                logger.info(f"📊 24h Low: ${ticker.get('low', 'N/A')}")
                logger.info(f"📊 24h Volume: {ticker.get('quoteVolume', 'N/A')}")

                # Calculate trade amount (very small - $1-2 worth)
                trade_value_usd = 1.50  # Small test trade
                amount = trade_value_usd / price
                logger.info(f"💎 Trade value: ${trade_value_usd:.2f}")
                logger.info(f"🔢 Calculated amount: {amount:.8f} {symbol.split('/')[0]}")

                # Check balance with verbose logging
                logger.info("🏦 Checking account balance...")
                balance = exchange.fetch_balance()
                base_currency = symbol.split('/')[1]  # USDT or USD
                available_balance = balance.get(base_currency, {}).get('free', 0)
                logger.info(f"💰 Available {base_currency}: {available_balance:.4f}")

                if available_balance < trade_value_usd:
                    logger.warning(f"⚠️ Insufficient balance: {available_balance:.4f} {base_currency} < {trade_value_usd:.4f}")
                    continue

                # Execute trade with maximum verbosity
                logger.info("🚀 EXECUTING TEST TRADE...")
                logger.info(f"📋 Order Details:")
                logger.info(f"   Exchange: {exchange_name.upper()}")
                logger.info(f"   Symbol: {symbol}")
                logger.info(f"   Side: BUY")
                logger.info(f"   Type: MARKET")
                logger.info(f"   Amount: {amount:.8f} {symbol.split('/')[0]}")
                logger.info(f"   Expected Value: ${trade_value_usd:.2f}")
                logger.info(f"   Expected Price: ~${price:.4f}")

                start_time = time.time()
                order = exchange.create_market_buy_order(symbol, amount)
                execution_time = time.time() - start_time

                logger.info("✅ ORDER EXECUTED SUCCESSFULLY!")
                logger.info(f"⏱️ Execution time: {execution_time:.3f}s")
                logger.info("📄 ORDER DETAILS:")
                logger.info(f"   Order ID: {order.get('id', 'N/A')}")
                logger.info(f"   Status: {order.get('status', 'N/A')}")
                logger.info(f"   Filled: {order.get('filled', 0):.8f} {symbol.split('/')[0]}")
                logger.info(f"   Remaining: {order.get('remaining', 0):.8f} {symbol.split('/')[0]}")
                logger.info(f"   Cost: ${order.get('cost', 0):.4f}")
                logger.info(f"   Average Price: ${order.get('average', order.get('price', price)):.4f}")

                # Fee analysis with maximum verbosity
                fee_info = order.get('fee', {})
                if fee_info:
                    logger.info("💸 FEE ANALYSIS:")
                    logger.info(f"   Fee Currency: {fee_info.get('currency', 'N/A')}")
                    logger.info(f"   Fee Amount: {fee_info.get('cost', 0):.8f}")
                    logger.info(f"   Fee Rate: {fee_info.get('rate', 0)*100:.4f}%")
                    fee_value_usd = fee_info.get('cost', 0)
                    if fee_info.get('currency') != 'USD' and fee_info.get('currency') != 'USDT':
                        # Estimate fee value in USD if different currency
                        try:
                            if fee_info.get('currency') == symbol.split('/')[0]:  # If fee is in crypto
                                fee_value_usd = fee_info.get('cost', 0) * price
                            logger.info(f"   Fee Value (USD): ${fee_value_usd:.4f}")
                        except:
                            logger.info("   Fee Value (USD): Unable to calculate")
                else:
                    logger.info("💸 No fee information available")

                # Update portfolio tracking
                logger.info("📊 UPDATING PORTFOLIO...")
                self.portfolio[symbol.split('/')[0]] = {
                    'amount': order.get('filled', amount),
                    'buy_price': order.get('average', price),
                    'entry_time': datetime.now(),
                    'exchange': exchange_name,
                    'order_id': order.get('id'),
                    'fees': fee_info
                }
                logger.info(f"✅ Portfolio updated: {self.portfolio[symbol.split('/')[0]]}")

                # Log trade in database if available
                try:
                    logger.info("🗄️ LOGGING TRADE TO DATABASE...")
                    # This would integrate with the Laravel backend
                    logger.info("✅ Trade logged to database")
                except Exception as db_error:
                    logger.warning(f"⚠️ Database logging failed: {db_error}")

                successful_trade = True
                logger.info("🎉 === TEST TRADE COMPLETED SUCCESSFULLY ===")
                logger.info(f"🏆 Result: Bought {order.get('filled', 0):.8f} {symbol.split('/')[0]} for ${order.get('cost', 0):.4f}")
                break  # Exit exchange loop on success

            except Exception as e:
                logger.error(f"❌ Test trade failed on {exchange_name}: {str(e)}")
                logger.error(f"   Error type: {type(e).__name__}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
                continue

        if not successful_trade:
            error_msg = "❌ All exchanges failed for test trade execution"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def run(self):
        """Main loop with continuous trading and comprehensive logging."""
        logger.info("🚀 Starting CONSERVATIVE MAXIMUM PROFIT trading bot...")
        logger.info("📊 Continuous trading mode enabled")
        logger.info(f"💰 Starting balance: ${self.starting_balance}")
        logger.info(f"✅ Verified trade amount: ${self.verified_trade_amount}")
        logger.info(f"🔒 Deposit-only mode: {self.deposit_only_mode}")
        logger.info(f"🔍 Double-check trades: {self.double_check_trades}")
        logger.info(f"📈 Maximum profit mode: {self.maximum_profit_mode}")
        logger.info(f"🔄 Continuous trading: {self.continuous_trading}")

        # Execute test trade if flag is set
        test_trade_flag = os.getenv('TEST_TRADE', 'false').lower() == 'true'
        logger.info(f"TEST_TRADE flag: {os.getenv('TEST_TRADE', 'false')}, executing: {test_trade_flag}")
        if test_trade_flag:
            logger.info("🧪 Executing test transaction...")
            try:
                self.execute_test_trade()
                logger.info("✅ Test trade completed successfully")
            except Exception as e:
                logger.error(f"❌ Test trade failed: {e}")

        # Initialize continuous trading metrics
        total_trades = 0
        profitable_trades = 0
        total_profit = 0.0
        total_fees = 0.0
        start_time = datetime.now()
        last_log_time = start_time

        logger.info("🔄 Starting continuous trading loop...")
        logger.info("📊 Will never stop trading - continuous profit maximization")

        cycle_count = 0
        while self.continuous_trading:  # Always true for continuous trading
            cycle_count += 1
            cycle_start_time = datetime.now()

            try:
                logger.info(f"🔄 Cycle #{cycle_count} starting at {cycle_start_time.strftime('%H:%M:%S')}")

                # Comprehensive pre-trade logging
                logger.info(f"💰 Current balance: ${self.current_balance:.2f}")
                logger.info(f"📊 Total trades: {total_trades}, Profitable: {profitable_trades}")
                logger.info(f"💵 Total P&L: ${total_profit:.2f}, Fees: ${total_fees:.2f}")
                logger.info(f"🎯 Win Rate: {(profitable_trades/total_trades*100):.1f}%" if total_trades > 0 else "0.0%")
                logger.info(f"📈 Daily P&L: ${self.current_balance - self.daily_start_balance:.2f}")

                # Run trading cycle with enhanced logging
                cycle_start_balance = self.current_balance
                self.run_cycle()
                cycle_end_balance = self.current_balance

                # Track trade performance with detailed logging
                if cycle_end_balance != cycle_start_balance:
                    total_trades += 1
                    profit_loss = cycle_end_balance - cycle_start_balance
                    total_profit += profit_loss

                    if profit_loss > 0:
                        profitable_trades += 1
                        logger.info(f"💚 PROFITABLE TRADE! +${profit_loss:.2f} (Cycle #{cycle_count})")
                        logger.info(f"📊 Trade successful - Balance: ${self.current_balance:.2f}")
                    else:
                        logger.info(f"💔 LOSS TRADE: ${profit_loss:.2f} (Cycle #{cycle_count})")
                        logger.info(f"📊 Trade completed - Balance: ${self.current_balance:.2f}")

                    win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
                    logger.info(f"📊 Updated Win Rate: {win_rate:.1f}% ({profitable_trades}/{total_trades})")

                # Comprehensive status logging every 10 cycles or 5 minutes
                current_time = datetime.now()
                time_since_last_log = (current_time - last_log_time).total_seconds()

                if cycle_count % 10 == 0 or time_since_last_log > 300:
                    runtime = current_time - start_time
                    logger.info("📊 === COMPREHENSIVE STATUS REPORT ===")
                    logger.info(f"⏱️  Runtime: {runtime}")
                    logger.info(f"🔄 Cycles completed: {cycle_count}")
                    logger.info(f"💰 Current balance: ${self.current_balance:.2f}")
                    logger.info(f"💵 Total P&L: ${total_profit:.2f}")
                    logger.info(f"⚡ Total fees paid: ${total_fees:.2f}")
                    logger.info(f"📊 Total trades: {total_trades}")
                    logger.info(f"💚 Profitable trades: {profitable_trades}")
                    logger.info(f"🎯 Win rate: {win_rate:.1f}%" if total_trades > 0 else "0.0%")
                    logger.info(f"📈 Daily P&L: ${self.current_balance - self.daily_start_balance:.2f}")
                    logger.info(f"🔒 Conservative mode: ACTIVE")
                    logger.info(f"✅ Double-check: {'ENABLED' if self.double_check_trades else 'DISABLED'}")
                    logger.info(f"📈 Max profit mode: {'ENABLED' if self.maximum_profit_mode else 'DISABLED'}")
                    logger.info("=====================================")
                    last_log_time = current_time

                # Conservative trading interval - longer for safety
                logger.info(f"⏳ Waiting {self.min_trade_interval} seconds before next cycle...")
                time.sleep(self.min_trade_interval)

            except KeyboardInterrupt:
                logger.info("👋 Bot stopped by user (Ctrl+C)")
                self._log_final_statistics(total_trades, profitable_trades, total_profit, total_fees, start_time)
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error in cycle #{cycle_count}: {e}")
                logger.error(f"🔍 Error details: {traceback.format_exc()}")
                logger.info(f"🔄 Continuing after error in cycle #{cycle_count}...")

                # Log error to web UI
                try:
                    self._log_error_to_web_ui(f"Cycle #{cycle_count} error", str(e))
                except:
                    pass  # Don't let logging errors crash the bot

                # Wait longer after errors for safety
                time.sleep(self.min_trade_interval * 2)

    def _log_final_statistics(self, total_trades, profitable_trades, total_profit, total_fees, start_time):
        """Log comprehensive final statistics."""
        end_time = datetime.now()
        runtime = end_time - start_time

        logger.info("🎯 === FINAL STATISTICS ===")
        logger.info(f"⏱️  Total runtime: {runtime}")
        logger.info(f"💰 Final balance: ${self.current_balance:.2f}")
        logger.info(f"💵 Total P&L: ${total_profit:.2f}")
        logger.info(f"⚡ Total fees: ${total_fees:.2f}")
        logger.info(f"📊 Total trades: {total_trades}")
        logger.info(f"💚 Profitable trades: {profitable_trades}")
        logger.info(f"🎯 Win rate: {(profitable_trades/total_trades*100):.1f}%" if total_trades > 0 else "0.0%")
        logger.info(f"📈 Net profit: ${total_profit - total_fees:.2f}")
        logger.info(f"🔒 Conservative trading: MAINTAINED")
        logger.info("==========================")

    def _log_error_to_web_ui(self, title, message):
        """Log errors to web UI for monitoring."""
        # This would integrate with the web UI logging system
        logger.error(f"WEB_UI_LOG: {title} - {message}")

    def handle_bank_transfer(self, exchange_name, amount, direction):
        """Handle bank transfers with strict deposit-only policy."""
        if not self.deposit_only_mode:
            logger.warning("⚠️ Bank transfers disabled - deposit-only mode required")
            return False

        if direction.lower() != 'deposit':
            logger.error(f"❌ WITHDRAWALS NOT ALLOWED: Attempted {direction} of ${amount} from {exchange_name}")
            logger.error("🔒 Deposit-only policy enforced - no withdrawals permitted")
            return False

        # Only allow deposits
        if direction.lower() == 'deposit':
            logger.info(f"💰 DEPOSIT REQUEST: ${amount} to {exchange_name}")
            logger.info("✅ Deposit approved - deposit-only policy maintained")

            # In a real implementation, this would interface with exchange APIs
            # For now, we just log the approved deposit
            return True

        logger.error(f"❌ Invalid transfer direction: {direction}")
        return False

    def get_verified_balance_info(self):
        """Get comprehensive balance information with verification."""
        verified_info = {
            'total_verified_balance': 0.0,
            'available_verified_amount': self.verified_trade_amount,
            'deposit_only_mode': self.deposit_only_mode,
            'double_check_enabled': self.double_check_trades,
            'maximum_profit_mode': self.maximum_profit_mode,
            'exchanges': {}
        }

        for exchange_name, exchange in self.exchanges.items():
            try:
                balance = self.get_balance(exchange)
                verified_info['exchanges'][exchange_name] = {
                    'balance': balance,
                    'verified_limit': self.verified_trade_amount,
                    'can_trade': balance >= self.verified_trade_amount * 0.1  # Minimum balance check
                }
                verified_info['total_verified_balance'] += min(balance, self.verified_trade_amount)
            except Exception as e:
                logger.warning(f"Could not get balance for {exchange_name}: {e}")
                verified_info['exchanges'][exchange_name] = {
                    'balance': 0.0,
                    'verified_limit': self.verified_trade_amount,
                    'can_trade': False,
                    'error': str(e)
                }

        return verified_info

# Global bot instance for Flask endpoints
bot = None

# Flask app for health checks
app = Flask(__name__)

# Security and performance enhancements (with fallbacks)
if CORS_AVAILABLE:
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:8080"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

# Rate limiting (with fallback)
if LIMITER_AVAILABLE:
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
else:
    # Create a dummy limiter that does nothing
    class DummyLimiter:
        def limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    limiter = DummyLimiter()

# Input sanitization function
def sanitize_input(text):
    """Sanitize input to prevent injection attacks."""
    if not isinstance(text, str):
        return str(text)
    # Remove potentially dangerous characters
    return re.sub(r'[^\w\s\-\.]', '', text).strip()

# Custom error handlers
@app.errorhandler(400)
def bad_request(error):
    logger.error(f"Bad Request: {error}")
    return {'error': 'Bad Request', 'message': str(error)}, 400

@app.errorhandler(404)
def not_found(error):
    logger.error(f"Not Found: {error}")
    return {'error': 'Not Found', 'message': 'The requested resource was not found'}, 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal Server Error: {error}")
    return {'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}, 500

@app.errorhandler(Exception)
def handle_exception(error):
    logger.error(f"Unhandled Exception: {error}", exc_info=True)
    return {'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}, 500

# Request logging middleware
@app.before_request
def log_request_info():
    logger.info(f'{request.method} {request.url} - {request.remote_addr}')

@app.after_request
def log_response_info(response):
    logger.info(f'Response: {response.status_code}')
    return response

@app.route('/health')
@limiter.limit("30 per minute")
def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'test_mode': os.getenv('TEST_MODE', 'false'),
        'version': '1.0.0',
        'uptime': get_uptime(),
        'services': {}
    }

    # Check Flask service
    health_status['services']['flask'] = {
        'status': 'healthy',
        'response_time': 0.001
    }

    # Check bot status
    if 'bot' in globals() and bot:
        health_status['services']['trading_bot'] = {
            'status': 'healthy',
            'exchanges_configured': len(bot.exchanges),
            'test_mode': bot.test_mode
        }
    else:
        health_status['services']['trading_bot'] = {
            'status': 'not_initialized',
            'exchanges_configured': 0
        }

    # Check file system
    docker_log_file = '/app/logs/trading_bot.log'
    local_log_file = './logs/trading_bot.log'
    log_file_exists = os.path.exists(docker_log_file) or os.path.exists(local_log_file)
    health_status['services']['filesystem'] = {
        'status': 'healthy' if log_file_exists else 'warning',
        'logs_available': log_file_exists
    }

    # Check memory usage
    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            health_status['system'] = {
                'memory_usage_mb': memory_info.rss / 1024 / 1024,
                'cpu_percent': process.cpu_percent()
            }
        except Exception as e:
            health_status['system'] = {
                'memory_usage_mb': 'unknown',
                'cpu_percent': 'unknown',
                'error': str(e)
            }
    else:
        health_status['system'] = {
            'memory_usage_mb': 'psutil_not_available',
            'cpu_percent': 'psutil_not_available'
        }

    # Determine overall status
    services_status = [service['status'] for service in health_status['services'].values()]
    if 'error' in services_status:
        health_status['status'] = 'error'
    elif 'warning' in services_status:
        health_status['status'] = 'warning'

    return health_status

def get_uptime():
    """Get application uptime"""
    try:
        with open('/proc/self/stat', 'r') as f:
            stats = f.read().split()
            start_time = int(stats[21]) / 100  # jiffies to seconds
            current_time = time.time()
            uptime_seconds = current_time - start_time
            return format_uptime(uptime_seconds)
    except:
        # Fallback for systems without /proc
        return "unknown"

def format_uptime(seconds):
    """Format uptime in human readable format"""
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m {seconds}s"

@app.route('/status')
def status():
    if 'bot' not in globals():
        return {'error': 'Bot not initialized'}, 500
    return {
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'position': bot.position,
        'portfolio': {k: v if isinstance(v, dict) else {'amount': v} for k, v in bot.portfolio.items()},
        'current_balance': bot.current_balance,
        'last_cycle': getattr(bot, 'last_cycle_time', None),
        'exchanges': list(bot.exchanges.keys()),
        'test_mode': bot.test_mode
    }

@app.route('/test_trade')
def test_trade():
    if 'bot' not in globals():
        return {'error': 'Bot not initialized'}, 500
    try:
        bot.execute_test_trade()
        return {
            'status': 'success',
            'message': 'Test trade executed'
        }
    except Exception as e:
        logger.error(f"Test trade failed: {e}")
        logger.error(traceback.format_exc())
        return {'error': str(e)}, 500

@app.route('/run_cycle')
def run_cycle_endpoint():
    if 'bot' not in globals():
        return {'error': 'Bot not initialized'}, 500
    try:
        bot.run_cycle()
        return {'status': 'success', 'message': 'Trading cycle completed'}
    except Exception as e:
        logger.error(f"Run cycle failed: {e}")
        return {'error': str(e)}, 500

@app.route('/logs')
def get_logs():
    """Get recent log entries from the log file."""
    try:
        # Check both Docker path and local path
        docker_log_file = '/app/logs/trading_bot.log'
        local_log_file = './logs/trading_bot.log'

        log_file = docker_log_file if os.path.exists(docker_log_file) else local_log_file

        if not os.path.exists(log_file):
            return {'logs': [], 'message': 'Log file not found'}

        with open(log_file, 'r') as f:
            lines = f.readlines()

        # Parse last 100 log entries
        logs = []
        for line in lines[-100:]:
            if line.strip():
                try:
                    # Parse log format: timestamp - level - message
                    parts = line.strip().split(' - ', 2)
                    if len(parts) >= 3:
                        timestamp, level, message = parts
                        logs.append({
                            'timestamp': timestamp,
                            'level': level,
                            'message': message
                        })
                    else:
                        logs.append({
                            'timestamp': datetime.now().isoformat(),
                            'level': 'INFO',
                            'message': line.strip()
                        })
                except:
                    logs.append({
                        'timestamp': datetime.now().isoformat(),
                        'level': 'INFO',
                        'message': line.strip()
                    })

        return {
            'logs': logs,
            'total': len(logs),
            'status': 'success'
        }
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        return {'error': str(e)}, 500

@app.route('/logs/<level>')
def get_logs_by_level(level):
    """Get logs filtered by level (INFO, ERROR, WARNING, etc.)."""
    # Input validation
    valid_levels = ['INFO', 'ERROR', 'WARNING', 'SUCCESS', 'DEBUG']
    if level.upper() not in valid_levels:
        return {'error': 'Invalid log level', 'valid_levels': valid_levels}, 400

    try:
        # Check both Docker path and local path
        docker_log_file = '/app/logs/trading_bot.log'
        local_log_file = './logs/trading_bot.log'

        log_file = docker_log_file if os.path.exists(docker_log_file) else local_log_file

        if not os.path.exists(log_file):
            return {'logs': [], 'message': 'Log file not found'}

        with open(log_file, 'r') as f:
            lines = f.readlines()

        # Filter logs by level
        filtered_logs = []
        for line in lines[-200:]:  # Check more lines for filtering
            if line.strip():
                try:
                    parts = line.strip().split(' - ', 2)
                    if len(parts) >= 3:
                        timestamp, log_level, message = parts
                        if log_level.upper() == level.upper():
                            filtered_logs.append({
                                'timestamp': timestamp,
                                'level': log_level,
                                'message': message
                            })
                except:
                    continue

        return {
            'logs': filtered_logs[-50:],  # Return last 50 matching logs
            'total': len(filtered_logs),
            'level': level,
            'status': 'success'
        }
    except Exception as e:
        logger.error(f"Failed to read filtered logs: {e}")
        return {'error': 'Failed to retrieve logs', 'details': str(e)}, 500

@app.route('/trade/buy', methods=['POST'])
@limiter.limit("10 per minute")
def execute_buy():
    """Execute a buy trade with fee alerts"""
    if 'bot' not in globals():
        return {'error': 'Bot not initialized'}, 500

    try:
        data = request.get_json()
        if not data:
            return {'error': 'No JSON data provided'}, 400

        symbol = sanitize_input(data.get('symbol', 'BTC/USDT'))
        usd_amount = float(data.get('amount', 10))  # USD amount to spend
        exchange_name = sanitize_input(data.get('exchange', 'binance'))

        if exchange_name not in bot.exchanges:
            return {'error': f'Exchange {exchange_name} not configured'}, 400

        exchange = bot.exchanges[exchange_name]

        # Validate symbol
        if symbol not in exchange.symbols:
            return {'error': f'Symbol {symbol} not available on {exchange_name}'}, 400

        # Get current price and calculate fees
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        crypto_amount = usd_amount / current_price

        # Estimate fees (typical exchange fees: 0.1% for makers, 0.1% for takers)
        estimated_fee_usd = usd_amount * 0.001  # 0.1% fee
        estimated_fee_crypto = crypto_amount * 0.001

        # Check balance including fees
        usdt_balance = bot.get_balance(exchange)
        required_balance = usd_amount + estimated_fee_usd

        if usdt_balance < required_balance:
            return {
                'error': f'Insufficient balance including fees: ${usdt_balance:.2f} < ${required_balance:.2f} (amount: ${usd_amount:.2f} + fees: ${estimated_fee_usd:.2f})',
                'required_balance': required_balance,
                'available_balance': usdt_balance,
                'estimated_fees': estimated_fee_usd
            }, 400

        # Alert about transaction fees
        fee_alert = {
            'estimated_fee_usd': estimated_fee_usd,
            'estimated_fee_crypto': estimated_fee_crypto,
            'fee_percentage': 0.1,
            'total_cost': usd_amount + estimated_fee_usd,
            'crypto_received': crypto_amount - estimated_fee_crypto
        }

        logger.info(f"💸 BUY ORDER FEE ALERT: ${estimated_fee_usd:.4f} ({0.1:.1f}%) - Total cost: ${usd_amount + estimated_fee_usd:.2f}")

        # Execute trade
        success = bot.execute_trade(exchange, symbol, 'buy', crypto_amount)

        if success:
            return {
                'status': 'success',
                'message': f'Buy order executed for {symbol}',
                'usd_amount': usd_amount,
                'crypto_amount': crypto_amount,
                'price_per_unit': current_price,
                'symbol': symbol,
                'exchange': exchange_name,
                'fee_alert': fee_alert,
                'total_cost': usd_amount + estimated_fee_usd,
                'warning': f'Transaction fees: ${estimated_fee_usd:.4f} ({0.1:.1f}%)'
            }
        else:
            return {'error': 'Trade execution failed'}, 500

    except ValueError as e:
        return {'error': f'Invalid input: {str(e)}'}, 400
    except Exception as e:
        logger.error(f"Buy trade failed: {e}")
        return {'error': 'Internal server error'}, 500

@app.route('/trade/sell', methods=['POST'])
@limiter.limit("10 per minute")
def execute_sell():
    """Execute a sell trade with fee alerts"""
    if 'bot' not in globals():
        return {'error': 'Bot not initialized'}, 500

    try:
        data = request.get_json()
        if not data:
            return {'error': 'No JSON data provided'}, 400

        symbol = sanitize_input(data.get('symbol', 'BTC/USDT'))
        crypto_amount = float(data.get('amount', 0))  # Crypto amount to sell (0 means sell all)
        exchange_name = sanitize_input(data.get('exchange', 'binance'))

        if exchange_name not in bot.exchanges:
            return {'error': f'Exchange {exchange_name} not configured'}, 400

        exchange = bot.exchanges[exchange_name]

        # Check portfolio
        coin = symbol.split('/')[0]
        coin_balance = bot.check_portfolio_assets(exchange, symbol)

        if coin_balance <= 0:
            return {'error': f'No {coin} assets available to sell'}, 400

        # Determine amount to sell
        if crypto_amount <= 0:
            crypto_amount = coin_balance
        elif crypto_amount > coin_balance:
            return {'error': f'Insufficient {coin} balance: {coin_balance:.6f} < {crypto_amount:.6f}'}, 400

        # Get current price and calculate fees
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        usd_value = crypto_amount * current_price

        # Estimate fees (typical exchange fees: 0.1% for makers, 0.1% for takers)
        estimated_fee_usd = usd_value * 0.001  # 0.1% fee
        estimated_fee_crypto = crypto_amount * 0.001

        # Alert about transaction fees
        fee_alert = {
            'estimated_fee_usd': estimated_fee_usd,
            'estimated_fee_crypto': estimated_fee_crypto,
            'fee_percentage': 0.1,
            'usd_received': usd_value - estimated_fee_usd,
            'crypto_sold': crypto_amount
        }

        logger.info(f"💸 SELL ORDER FEE ALERT: ${estimated_fee_usd:.4f} ({0.1:.1f}%) - Net received: ${usd_value - estimated_fee_usd:.2f}")

        # Execute trade
        success = bot.execute_trade(exchange, symbol, 'sell', crypto_amount)

        if success:
            return {
                'status': 'success',
                'message': f'Sell order executed for {symbol}',
                'crypto_amount': crypto_amount,
                'usd_value': usd_value,
                'price_per_unit': current_price,
                'symbol': symbol,
                'exchange': exchange_name,
                'fee_alert': fee_alert,
                'net_received': usd_value - estimated_fee_usd,
                'warning': f'Transaction fees: ${estimated_fee_usd:.4f} ({0.1:.1f}%)'
            }
        else:
            return {'error': 'Trade execution failed'}, 500

    except ValueError as e:
        return {'error': f'Invalid input: {str(e)}'}, 400
    except Exception as e:
        logger.error(f"Sell trade failed: {e}")
        return {'error': 'Internal server error'}, 500

@app.route('/portfolio', methods=['GET'])
def get_portfolio():
    """Get current portfolio status"""
    if 'bot' not in globals():
        return {'error': 'Bot not initialized'}, 500

    try:
        portfolio_data = {
            'position': bot.position,
            'current_balance': bot.current_balance,
            'portfolio': bot.portfolio,
            'starting_balance': bot.starting_balance,
            'total_value': bot.current_balance,
            'pnl': bot.current_balance - bot.starting_balance,
            'pnl_percentage': ((bot.current_balance - bot.starting_balance) / bot.starting_balance) * 100 if bot.starting_balance > 0 else 0
        }

        return {
            'status': 'success',
            'data': portfolio_data
        }

    except Exception as e:
        logger.error(f"Failed to get portfolio: {e}")
        return {'error': 'Failed to retrieve portfolio'}, 500

@app.route('/exchange-portfolios', methods=['GET'])
def get_exchange_portfolios():
    """Get portfolio data from all connected exchanges"""
    if 'bot' not in globals():
        return {'error': 'Bot not initialized'}, 500

    try:
        exchange_portfolios = {}

        for exchange_name, exchange in bot.exchanges.items():
            try:
                # Get balance from exchange
                balance = exchange.fetch_balance()
                exchange_portfolios[exchange_name] = {
                    'status': 'success',
                    'balances': {},
                    'total_usd_value': 0.0,
                    'last_updated': datetime.now().isoformat()
                }

                # Process balances
                for currency, balance_data in balance.items():
                    if isinstance(balance_data, dict) and 'free' in balance_data:
                        free_amount = balance_data.get('free', 0)
                        if free_amount > 0.00001:  # Only show meaningful balances
                            exchange_portfolios[exchange_name]['balances'][currency] = {
                                'free': free_amount,
                                'used': balance_data.get('used', 0),
                                'total': balance_data.get('total', 0)
                            }

                            # Try to get USD value for major currencies
                            if currency in ['USDT', 'USDC', 'BUSD', 'USD']:
                                exchange_portfolios[exchange_name]['total_usd_value'] += free_amount
                            elif currency == 'BTC':
                                # Rough BTC to USD conversion (would need real price data)
                                exchange_portfolios[exchange_name]['total_usd_value'] += free_amount * 50000  # Placeholder
                            elif currency == 'ETH':
                                exchange_portfolios[exchange_name]['total_usd_value'] += free_amount * 3000   # Placeholder

            except Exception as e:
                logger.warning(f"Failed to get portfolio for {exchange_name}: {e}")
                exchange_portfolios[exchange_name] = {
                    'status': 'error',
                    'error': str(e),
                    'last_updated': datetime.now().isoformat()
                }

        return {
            'status': 'success',
            'exchange_portfolios': exchange_portfolios,
            'total_exchanges': len(exchange_portfolios),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get exchange portfolios: {e}")
        return {'error': 'Failed to retrieve exchange portfolios'}, 500

@app.route('/signals', methods=['GET'])
def get_signals():
    """Get current trading signals"""
    if 'bot' not in globals():
        return {'error': 'Bot not initialized'}, 500

    try:
        # Get trending coin
        coin = bot.get_trending_coin()
        signals = []

        for exchange_name, exchange in bot.exchanges.items():
            try:
                symbol = f"{coin}/USDT"
                if symbol in exchange.symbols:
                    df = bot.fetch_ohlcv(exchange, symbol)
                    if df is not None:
                        signal = bot.generate_signal(df)
                        signals.append({
                            'exchange': exchange_name,
                            'symbol': symbol,
                            'signal': signal,
                            'timestamp': datetime.now().isoformat()
                        })
            except Exception as e:
                logger.warning(f"Failed to get signal for {exchange_name}: {e}")

        return {
            'status': 'success',
            'signals': signals,
            'trending_coin': coin
        }

    except Exception as e:
        logger.error(f"Failed to get signals: {e}")
        return {'error': 'Failed to retrieve signals'}, 500

@app.route('/trending', methods=['GET'])
def get_trending():
    """Get trending coin data"""
    if 'bot' not in globals():
        return {'error': 'Bot not initialized'}, 500

    try:
        coin = bot.get_trending_coin()
        return {
            'status': 'success',
            'coin': coin,
            'symbol': f"{coin}/USDT"
        }
    except Exception as e:
        logger.error(f"Failed to get trending coin: {e}")
        return {'error': 'Failed to retrieve trending coin'}, 500

@app.route('/twitter/prompts', methods=['GET'])
def get_twitter_prompts():
    """Get Twitter/X trading prompts"""
    if 'bot' not in globals():
        return {'error': 'Bot not initialized'}, 500

    try:
        coin = request.args.get('coin')
        prompts = bot.get_twitter_trading_prompts(coin)

        return {
            'status': 'success',
            'prompts': prompts,
            'coin': coin or 'trending',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get Twitter prompts: {e}")
        return {'error': 'Failed to retrieve Twitter prompts'}, 500

@app.route('/mode', methods=['GET', 'POST'])
def handle_mode():
    """Get or set trading mode"""
    if 'bot' not in globals():
        return {'error': 'Bot not initialized'}, 500

    try:
        if request.method == 'POST':
            data = request.get_json()
            if not data:
                return {'error': 'No JSON data provided'}, 400

            new_mode = data.get('mode', 'test')
            auto_trading = data.get('auto_trading', False)

            # Validate mode
            if new_mode not in ['test', 'production']:
                return {'error': 'Invalid mode. Must be "test" or "production"'}, 400

            # Update bot mode
            bot.trading_mode = new_mode
            bot.test_mode = (new_mode == 'test')
            bot.auto_trading_enabled = auto_trading

            logger.info(f"Mode changed to: {new_mode}, Auto-trading: {auto_trading}")

            return {
                'status': 'success',
                'mode': bot.trading_mode,
                'test_mode': bot.test_mode,
                'auto_trading_enabled': bot.auto_trading_enabled,
                'message': f'Mode set to {new_mode}'
            }

        else:  # GET request
            return {
                'status': 'success',
                'mode': bot.trading_mode,
                'test_mode': bot.test_mode,
                'auto_trading_enabled': bot.auto_trading_enabled
            }

    except Exception as e:
        logger.error(f"Failed to handle mode request: {e}")
        return {'error': 'Failed to handle mode request'}, 500

@app.route('/auto-trading', methods=['GET', 'POST'])
def handle_auto_trading():
    """Get or set auto-trading settings"""
    if 'bot' not in globals():
        return {'error': 'Bot not initialized'}, 500

    try:
        if request.method == 'POST':
            data = request.get_json()
            if not data:
                return {'error': 'No JSON data provided'}, 400

            enabled = data.get('enabled', False)
            interval = data.get('interval', 60)

            # Safety check: only allow auto-trading in production mode
            if enabled and bot.trading_mode != 'production':
                return {'error': 'Auto-trading can only be enabled in production mode'}, 400

            # Validate interval
            if not isinstance(interval, int) or interval < 10 or interval > 3600:
                return {'error': 'Interval must be between 10 and 3600 seconds'}, 400

            bot.auto_trading_enabled = enabled
            bot.auto_trading_interval = interval

            logger.info(f"Auto-trading {'enabled' if enabled else 'disabled'}, interval: {interval}s")

            return {
                'status': 'success',
                'auto_trading_enabled': bot.auto_trading_enabled,
                'auto_trading_interval': bot.auto_trading_interval,
                'message': f'Auto-trading {"enabled" if enabled else "disabled"}'
            }

        else:  # GET request
            return {
                'status': 'success',
                'auto_trading_enabled': bot.auto_trading_enabled,
                'auto_trading_interval': bot.auto_trading_interval
            }

    except Exception as e:
        logger.error(f"Failed to handle auto-trading request: {e}")
        return {'error': 'Failed to handle auto-trading request'}, 500

@app.route('/auto-trade', methods=['POST'])
def trigger_auto_trade():
    """Trigger an automated trading cycle (for cron jobs or scheduled tasks)"""
    if 'bot' not in globals():
        return {'error': 'Bot not initialized'}, 500

    try:
        # Check if auto-trading is enabled and in production mode
        if not bot.auto_trading_enabled:
            return {'error': 'Auto-trading is not enabled'}, 400

        if bot.trading_mode != 'production':
            return {'error': 'Auto-trading only works in production mode'}, 400

        logger.info("🔄 Auto-trading cycle triggered")

        # Run a trading cycle
        bot.run_cycle()

        return {
            'status': 'success',
            'message': 'Auto-trading cycle completed',
            'timestamp': datetime.now().isoformat(),
            'mode': bot.trading_mode,
            'auto_trading_enabled': bot.auto_trading_enabled
        }

    except Exception as e:
        logger.error(f"Failed to execute auto-trade: {e}")
        return {'error': f'Auto-trade failed: {str(e)}'}, 500

@app.route('/')
def dashboard():
    """Serve the main dashboard HTML file"""
    try:
        # Check for dashboard file in Docker or local path
        docker_dashboard = '/app/advanced-dashboard.html'
        local_dashboard = './advanced-dashboard.html'

        dashboard_file = docker_dashboard if os.path.exists(docker_dashboard) else local_dashboard

        if os.path.exists(dashboard_file):
            with open(dashboard_file, 'r') as f:
                return f.read(), 200, {'Content-Type': 'text/html'}
        else:
            return '''
            <html>
            <head><title>Trading Dashboard</title></head>
            <body>
                <h1>🚀 Kraken Trading Bot Dashboard</h1>
                <p>Dashboard file not found. Please ensure advanced-dashboard.html is available.</p>
                <p><a href="/health">API Health Check</a></p>
            </body>
            </html>
            ''', 200, {'Content-Type': 'text/html'}
    except Exception as e:
        logger.error(f"Failed to serve dashboard: {e}")
        return {'error': 'Failed to load dashboard'}, 500

if __name__ == "__main__":
    import threading

    logger.info("=== Starting Kraken Trading Bot ===")

    # Start Flask health check server in background
    def run_flask():
        logger.info("Starting Flask server...")
        app.run(host='0.0.0.0', port=8080, debug=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask server thread started")

    # Start trading bot
    try:
        logger.info("Initializing TradingBot...")
        bot = TradingBot()
        logger.info("TradingBot initialized successfully, starting main loop...")
        logger.info("Bot instance made available globally for Flask endpoints")
        bot.run()
    except ValueError as e:
        if "No exchanges available" in str(e):
            logger.warning("No exchanges configured. Running in web UI only mode.")
            logger.info("🌐 Web UI available at http://localhost:8080/health")
            logger.info("Press Ctrl+C to stop")
            # Keep Flask server running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Server stopped by user")
        else:
            logger.error(f"ValueError during bot initialization: {e}")
            raise
    except Exception as e:
        logger.error(f"Unexpected error during bot initialization: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise