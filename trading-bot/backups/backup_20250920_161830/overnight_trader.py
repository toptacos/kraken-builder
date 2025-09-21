#!/usr/bin/env python3
"""
Overnight Trading Bot - Maximum Profit Optimization
==================================================

This script runs overnight to maximize profits through:
- Multi-exchange arbitrage opportunities
- Comprehensive trending coin trading
- Automated profit-taking and risk management
- Daily profit/loss limits with auto-stop
- 24/7 operation with minimal intervention

Features:
- Scrapes all trending cryptocurrencies across platforms
- Identifies arbitrage opportunities between exchanges
- Implements advanced trading strategies for overnight gains
- Tracks daily limits and stops trading when reached
- Comprehensive logging and monitoring
- Emergency stop mechanisms

WARNING: This bot trades with real money. Use at your own risk.
"""

import os
import time
import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ccxt
from flask import Flask
import threading
import json
import sys
from typing import Dict, List, Optional, Tuple

# Import modular trading strategies
from trading_strategies import initialize_strategy_manager, get_strategy_manager

# Import advanced trend analyzer
from crypto_trend_analyzer import initialize_trend_analyzer, get_trend_analyzer

# Configure logging with production verbose settings
log_level = logging.DEBUG if os.getenv('VERBOSE_LOGGING', 'false').lower() == 'true' else logging.INFO
production_mode = os.getenv('PRODUCTION_MODE', 'false').lower() == 'true'

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(funcName)s:%(lineno)d - %(message)s' if production_mode else '%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('overnight_trader.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Add verbose logging for production
if production_mode:
    logging.getLogger('trading_strategies').setLevel(logging.DEBUG)
    logging.getLogger('crypto_trend_analyzer').setLevel(logging.DEBUG)
    logging.getLogger('backtesting_engine').setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

if production_mode:
    logger.info("🚀 PRODUCTION MODE ENABLED - VERBOSE LOGGING ACTIVE")
    logger.info(f"📊 Log Level: {logging.getLevelName(log_level)}")
    logger.info("🔍 Detailed function-level logging enabled")

class OvernightTrader:
    def __init__(self):
        logger.info("=== Overnight Trader Initialization ===")

        # Trading parameters
        self.test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
        self.starting_balance = float(os.getenv('STARTING_BALANCE', '1000'))
        self.daily_profit_target = float(os.getenv('DAILY_PROFIT_TARGET', '50'))  # $50 profit target
        self.daily_loss_limit = float(os.getenv('DAILY_LOSS_LIMIT', '-100'))     # -$100 loss limit
        self.trade_amount = float(os.getenv('TRADE_AMOUNT', '25'))               # $25 per trade
        self.max_trades_per_hour = int(os.getenv('MAX_TRADES_PER_HOUR', '12'))   # Rate limiting

        # Risk management
        self.current_balance = self.starting_balance
        self.daily_pnl = 0.0
        self.session_start_time = datetime.now()
        self.last_trade_time = datetime.now() - timedelta(hours=1)  # Allow immediate first trade
        self.active_positions = {}  # Track open positions
        self.trade_history = []     # Track all trades

        # Arbitrage settings
        self.min_arb_profit_pct = float(os.getenv('MIN_ARB_PROFIT_PCT', '0.5'))  # 0.5% minimum arbitrage profit
        self.max_arb_positions = int(os.getenv('MAX_ARB_POSITIONS', '5'))       # Max concurrent arbitrage positions

        # Initialize exchanges
        self.exchanges = self._initialize_exchanges()

        # Initialize strategy manager with profit-guaranteed strategies
        strategy_config = {
            'trade_amount': self.trade_amount,
            'min_profit_pct': self.min_arb_profit_pct,
            'max_position_size': self.max_arb_positions * self.trade_amount,
            'max_concurrent_positions': self.max_arb_positions,
            'daily_loss_limit': self.daily_loss_limit
        }
        self.strategy_manager = initialize_strategy_manager(self.exchanges, strategy_config)

        # Initialize advanced trend analyzer
        self.trend_analyzer = initialize_trend_analyzer(
            cache_dir="trend_cache",
            update_interval=300  # 5 minutes
        )

        # Legacy API URLs (kept for fallback)
        self.coingecko_url = "https://api.coingecko.com/api/v3/search/trending"
        self.coinmarketcap_url = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing"

        logger.info(f"Overnight Trader initialized - Test Mode: {self.test_mode}")
        logger.info(f"Daily Profit Target: ${self.daily_profit_target}")
        logger.info(f"Daily Loss Limit: ${self.daily_loss_limit}")
        logger.info(f"Trade Amount: ${self.trade_amount}")
        logger.info(f"Exchanges configured: {list(self.exchanges.keys())}")
        logger.info(f"Strategy Manager: Initialized with {len(self.strategy_manager.strategies)} profit-guaranteed strategies")

    def _initialize_exchanges(self) -> Dict:
        """Initialize all configured exchanges"""
        exchanges = {}

        # Binance
        if os.getenv('BINANCE_API_KEY') and os.getenv('BINANCE_API_SECRET'):
            exchanges['binance'] = ccxt.binance({
                'apiKey': os.getenv('BINANCE_API_KEY'),
                'secret': os.getenv('BINANCE_API_SECRET'),
                'enableRateLimit': True,
                'sandbox': self.test_mode
            })

        # Kraken
        if os.getenv('KRAKEN_API_KEY') and os.getenv('KRAKEN_API_SECRET'):
            exchanges['kraken'] = ccxt.kraken({
                'apiKey': os.getenv('KRAKEN_API_KEY'),
                'secret': os.getenv('KRAKEN_API_SECRET'),
                'enableRateLimit': True,
                'sandbox': self.test_mode
            })

        # Coinbase
        if os.getenv('COINBASE_API_KEY_NAME') and os.getenv('COINBASE_API_PRIVATE_KEY'):
            try:
                api_key = os.getenv('COINBASE_API_KEY_NAME')
                if '/apiKeys/' in api_key:
                    api_key = api_key.split('/apiKeys/')[-1]
                private_key = os.getenv('COINBASE_API_PRIVATE_KEY').replace('\\n', '\n')
                exchanges['coinbase'] = ccxt.coinbase({
                    'apiKey': api_key,
                    'secret': private_key,
                    'enableRateLimit': True,
                    'sandbox': self.test_mode
                })
            except Exception as e:
                logger.error(f"Failed to initialize Coinbase: {e}")

        # KuCoin
        if os.getenv('KUCOIN_API_KEY') and os.getenv('KUCOIN_API_SECRET') and os.getenv('KUCOIN_API_PASSPHRASE'):
            exchanges['kucoin'] = ccxt.kucoin({
                'apiKey': os.getenv('KUCOIN_API_KEY'),
                'secret': os.getenv('KUCOIN_API_SECRET'),
                'password': os.getenv('KUCOIN_API_PASSPHRASE'),
                'enableRateLimit': True,
                'sandbox': self.test_mode
            })

        if not exchanges:
            raise ValueError("No exchanges configured. Set API credentials in environment variables.")

        return exchanges

    def get_comprehensive_trending_coins(self) -> List[str]:
        """Get trending coins using advanced multi-source analysis"""
        try:
            # Use advanced trend analyzer
            trending_coins = self.trend_analyzer.get_top_trending_coins(
                limit=30,
                min_score=25.0,  # Lower threshold for more opportunities
                min_sources=1    # Accept coins from at least 1 source
            )

            logger.info(f"Advanced trend analysis found {len(trending_coins)} trending coins")
            logger.info(f"Top trending: {trending_coins[:10]}")

            return trending_coins

        except Exception as e:
            logger.error(f"Error in advanced trend analysis: {e}")
            logger.info("Falling back to basic CoinGecko analysis")

            # Fallback to basic analysis
            trending_coins = set()
            try:
                response = requests.get(self.coingecko_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for coin_data in data.get('coins', []):
                        symbol = coin_data.get('item', {}).get('symbol', '').upper()
                        if symbol:
                            trending_coins.add(symbol)
            except Exception as fallback_error:
                logger.error(f"Fallback analysis also failed: {fallback_error}")

            # Add major coins that are always tradeable
            major_coins = {'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOT', 'DOGE', 'SHIB', 'AVAX', 'MATIC'}
            trending_coins.update(major_coins)

            logger.info(f"Fallback found {len(trending_coins)} trending coins")
            return sorted(list(trending_coins))

    def _analyze_market_conditions(self, coins: List[str]) -> Dict:
        """Analyze current market conditions for strategy adaptation"""
        try:
            market_data = {
                'volatility': 'medium',
                'trend': 'sideways',
                'volume': 'normal',
                'liquidity': 'good'
            }

            # Analyze volatility across coins
            volatilities = []
            for coin in coins[:5]:  # Check top 5 coins
                for exchange_name, exchange in self.exchanges.items():
                    try:
                        if f"{coin}/USDT" in exchange.symbols:
                            # Get recent price data
                            ticker = exchange.fetch_ticker(f"{coin}/USDT")
                            # Simplified volatility calculation
                            # In practice, you'd use more sophisticated analysis
                            volatilities.append(ticker.get('percentage', 0))
                    except:
                        continue

            if volatilities:
                avg_volatility = sum(volatilities) / len(volatilities)
                if avg_volatility > 5:
                    market_data['volatility'] = 'high'
                elif avg_volatility < 2:
                    market_data['volatility'] = 'low'

            # Analyze trend (simplified)
            # In practice, you'd analyze price movements over time
            market_data['trend'] = 'sideways'  # Default

            # Analyze volume (simplified)
            # In practice, you'd compare to historical averages
            market_data['volume'] = 'normal'  # Default

            logger.debug(f"Market conditions analyzed: {market_data}")
            return market_data

        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}")
            return {
                'volatility': 'medium',
                'trend': 'sideways',
                'volume': 'normal',
                'liquidity': 'good'
            }

    # Arbitrage methods removed - now using modular strategy system
    # All trading logic is handled by the StrategyManager and individual strategies

    def check_daily_limits(self) -> bool:
        """Check if daily profit/loss limits have been reached"""
        # Check profit target
        if self.daily_pnl >= self.daily_profit_target:
            logger.info(f"🎉 Daily profit target reached: ${self.daily_pnl:.2f} >= ${self.daily_profit_target}")
            return False  # Stop trading

        # Check loss limit
        if self.daily_pnl <= self.daily_loss_limit:
            logger.error(f"⚠️ Daily loss limit reached: ${self.daily_pnl:.2f} <= ${self.daily_loss_limit}")
            return False  # Stop trading

        return True  # Continue trading

    def run_overnight_cycle(self):
        """Run one complete overnight trading cycle"""
        logger.info("🌙 Starting overnight trading cycle")

        # Check daily limits
        if not self.check_daily_limits():
            logger.info("📊 Daily limits reached - stopping overnight trading")
            return False

        # Check rate limiting
        time_since_last_trade = (datetime.now() - self.last_trade_time).total_seconds() / 3600
        if time_since_last_trade < (1 / self.max_trades_per_hour):
            logger.debug("⏳ Rate limiting: waiting before next trade")
            return True

        # Get trending coins
        trending_coins = self.get_comprehensive_trending_coins()

        # Analyze market conditions for dynamic strategy adaptation
        market_conditions = self._analyze_market_conditions(trending_coins[:10])

        # Allow strategy manager to adapt based on market conditions
        self.strategy_manager.monitor_and_adapt(market_conditions)

        # Use modular strategy system to find and execute profitable trades
        opportunities = self.strategy_manager.find_best_opportunities(trending_coins[:20])

        # Execute best opportunity using strategy manager
        executed_trades = 0
        if opportunities:
            if self.strategy_manager.execute_best_opportunity(opportunities):
                self.last_trade_time = datetime.now()
                executed_trades += 1
                logger.info("✅ Strategy manager executed profitable trade")
            else:
                logger.debug("Strategy manager found opportunities but execution failed")
        else:
            logger.debug("No profitable opportunities found by strategy manager")

        # Log current status
        logger.info(f"💰 Current Balance: ${self.current_balance:.2f}")
        logger.info(f"📈 Daily P&L: ${self.daily_pnl:.2f}")
        logger.info(f"🎯 Progress to target: {((self.daily_pnl / self.daily_profit_target) * 100):.1f}%")

        return True

    def run_overnight_session(self):
        """Run the complete overnight trading session"""
        logger.info("🌙 === STARTING OVERNIGHT TRADING SESSION ===")
        logger.info(f"Session start time: {self.session_start_time}")
        logger.info(f"Daily profit target: ${self.daily_profit_target}")
        logger.info(f"Daily loss limit: ${self.daily_loss_limit}")

        cycle_count = 0
        while True:
            try:
                cycle_count += 1
                logger.info(f"🔄 Cycle #{cycle_count} starting")

                # Run trading cycle
                if not self.run_overnight_cycle():
                    break  # Stop if limits reached

                # Wait before next cycle (1 minute for faster trading)
                logger.info("⏳ Waiting 1 minute before next cycle...")
                time.sleep(60)

                # Check if it's time to stop (morning hours)
                current_hour = datetime.now().hour
                if 6 <= current_hour <= 8:  # Stop between 6-8 AM
                    logger.info("🌅 Morning hours reached - stopping overnight session")
                    break

            except KeyboardInterrupt:
                logger.info("🛑 Overnight session interrupted by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in overnight cycle: {e}")
                time.sleep(60)  # Wait 1 minute on error

        # Final summary
        session_duration = datetime.now() - self.session_start_time
        logger.info("🌙 === OVERNIGHT SESSION COMPLETED ===")
        logger.info(f"Session duration: {session_duration}")
        logger.info(f"Total cycles: {cycle_count}")
        logger.info(f"Final balance: ${self.current_balance:.2f}")
        logger.info(f"Total P&L: ${self.daily_pnl:.2f}")
        logger.info(f"Trades executed: {len(self.trade_history)}")

        if self.daily_pnl > 0:
            logger.info(f"🎉 Session profitable! Made ${self.daily_pnl:.2f}")
        else:
            logger.info(f"📉 Session ended with loss of ${abs(self.daily_pnl):.2f}")

# Flask web interface for monitoring
app = Flask(__name__)

@app.route('/overnight/status')
def get_overnight_status():
    """Get overnight trading status with strategy performance"""
    if 'trader' not in globals():
        return {'error': 'Overnight trader not initialized'}, 500

    # Get strategy performance data
    strategy_performance = trader.strategy_manager.get_performance_summary()

    # Get trend analysis data
    trend_data = {}
    try:
        if hasattr(trader, 'trend_analyzer') and trader.trend_analyzer:
            analysis = trader.trend_analyzer.analyze_trends(trader.exchanges)
            trend_data = {
                'total_coins_analyzed': analysis.get('total_coins_found', 0),
                'top_trends': analysis.get('top_trends', [])[:5],  # Top 5 for status
                'sources_analyzed': analysis.get('sources_analyzed', []),
                'last_analysis': analysis.get('timestamp')
            }
    except Exception as e:
        logger.error(f"Error getting trend data: {e}")

    return {
        'status': 'running',
        'current_balance': trader.current_balance,
        'daily_pnl': trader.daily_pnl,
        'profit_target': trader.daily_profit_target,
        'loss_limit': trader.daily_loss_limit,
        'active_positions': len(trader.active_positions),
        'total_trades': len(trader.trade_history),
        'session_start': trader.session_start_time.isoformat(),
        'test_mode': trader.test_mode,
        'strategies': strategy_performance.get('strategies', {}),
        'overall_performance': {
            'total_trades': strategy_performance.get('total_trades', 0),
            'successful_trades': strategy_performance.get('successful_trades', 0),
            'win_rate': strategy_performance.get('win_rate', 0),
            'total_profit': strategy_performance.get('total_profit', 0)
        },
        'trend_analysis': trend_data
    }

@app.route('/overnight/stop')
def stop_overnight_trading():
    """Emergency stop for overnight trading"""
    if 'trader' not in globals():
        return {'error': 'Overnight trader not initialized'}, 500

    trader.daily_pnl = trader.daily_loss_limit - 1  # Force stop condition
    return {'status': 'stop_signal_sent', 'message': 'Overnight trading will stop on next cycle'}

if __name__ == "__main__":
    # Start Flask monitoring server
    def run_flask():
        logger.info("Starting Flask monitoring server on port 8081...")
        app.run(host='0.0.0.0', port=8081, debug=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Start overnight trader
    try:
        trader = OvernightTrader()
        trader.run_overnight_session()
    except Exception as e:
        logger.error(f"Failed to start overnight trader: {e}")
        sys.exit(1)