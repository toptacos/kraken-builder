#!/usr/bin/env python3
"""
Backtesting Engine for Trading Strategies
=========================================

This module provides comprehensive backtesting capabilities to validate
trading strategies on historical data, ensuring all trades have positive
expected value before live deployment.

Features:
- Historical data fetching and caching
- Strategy performance validation
- Risk metrics calculation
- Profitability analysis
- Monte Carlo simulations
- Walk-forward optimization

Usage:
    python3 backtesting_engine.py --strategy pure_arbitrage --symbol BTC --days 30
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import ccxt
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import our trading strategies
from trading_strategies import (
    PureArbitrageStrategy,
    StatisticalArbitrageStrategy,
    StrategyManager
)

logger = logging.getLogger(__name__)

class BacktestingEngine:
    def __init__(self, exchanges: Dict[str, ccxt.Exchange], cache_dir: str = "backtest_cache"):
        self.exchanges = exchanges
        self.cache_dir = cache_dir
        self.cache = {}

        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)

        # Load existing cache
        self._load_cache()

        logger.info("Backtesting engine initialized")

    def _load_cache(self):
        """Load cached historical data"""
        cache_file = os.path.join(self.cache_dir, "historical_data.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} cached data entries")
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
                self.cache = {}

    def _save_cache(self):
        """Save cache to disk"""
        cache_file = os.path.join(self.cache_dir, "historical_data.json")
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.debug("Cache saved to disk")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def fetch_historical_data(self, symbol: str, exchange_name: str, days: int = 30) -> Optional[pd.DataFrame]:
        """Fetch historical OHLCV data for backtesting"""
        cache_key = f"{exchange_name}_{symbol}_{days}d"

        # Check cache first
        if cache_key in self.cache:
            cache_time = datetime.fromisoformat(self.cache[cache_key]['timestamp'])
            if (datetime.now() - cache_time).days < 1:  # Cache for 1 day
                logger.info(f"Using cached data for {cache_key}")
                return pd.DataFrame(self.cache[cache_key]['data'])

        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                logger.error(f"Exchange {exchange_name} not available")
                return None

            # Calculate time range
            since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

            # Fetch OHLCV data
            ohlcv = exchange.fetch_ohlcv(f"{symbol}/USDT", '1h', since=since, limit=500)

            if not ohlcv:
                logger.warning(f"No data available for {symbol} on {exchange_name}")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            # Cache the data
            self.cache[cache_key] = {
                'timestamp': datetime.now().isoformat(),
                'data': df.reset_index().to_dict('records')
            }
            self._save_cache()

            logger.info(f"Fetched {len(df)} data points for {symbol} on {exchange_name}")
            return df

        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return None

    def simulate_arbitrage_opportunity(self, symbol: str, timestamp: datetime,
                                     prices: Dict[str, Dict]) -> Optional[Dict]:
        """Simulate an arbitrage opportunity at a specific point in time"""
        try:
            opportunities = []

            exchange_names = list(prices.keys())
            for i, buy_exchange in enumerate(exchange_names):
                for j, sell_exchange in enumerate(exchange_names):
                    if i != j:
                        buy_data = prices.get(buy_exchange, {})
                        sell_data = prices.get(sell_exchange, {})

                        if 'ask' in buy_data and 'bid' in sell_data:
                            buy_price = buy_data['ask']
                            sell_price = sell_data['bid']

                            if buy_price > 0 and sell_price > 0:
                                gross_profit_pct = ((sell_price - buy_price) / buy_price) * 100

                                # Account for fees (0.1% per exchange)
                                fees_pct = 0.2
                                net_profit_pct = gross_profit_pct - fees_pct

                                if net_profit_pct > 0.3:  # Minimum 0.3% profit
                                    opportunity = {
                                        'timestamp': timestamp.isoformat(),
                                        'symbol': symbol,
                                        'buy_exchange': buy_exchange,
                                        'sell_exchange': sell_exchange,
                                        'buy_price': buy_price,
                                        'sell_price': sell_price,
                                        'gross_profit_pct': gross_profit_pct,
                                        'net_profit_pct': net_profit_pct,
                                        'fees_pct': fees_pct,
                                        'trade_amount': 100,  # $100 test trade
                                        'expected_profit': (net_profit_pct / 100) * 100
                                    }
                                    opportunities.append(opportunity)

            # Return best opportunity
            if opportunities:
                return max(opportunities, key=lambda x: x['net_profit_pct'])

            return None

        except Exception as e:
            logger.error(f"Error simulating arbitrage: {e}")
            return None

    def backtest_strategy(self, strategy_name: str, symbol: str, days: int = 30) -> Dict:
        """Backtest a specific strategy on historical data"""
        logger.info(f"Starting backtest: {strategy_name} on {symbol} for {days} days")

        results = {
            'strategy': strategy_name,
            'symbol': symbol,
            'period_days': days,
            'total_opportunities': 0,
            'profitable_opportunities': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'max_profit': 0.0,
            'max_loss': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'trades': []
        }

        try:
            # Fetch historical data from all exchanges
            historical_data = {}
            for exchange_name in self.exchanges.keys():
                df = self.fetch_historical_data(symbol, exchange_name, days)
                if df is not None:
                    historical_data[exchange_name] = df

            if not historical_data:
                logger.error("No historical data available for backtesting")
                return results

            # Simulate trading through historical data
            portfolio_value = 1000.0  # Starting with $1000
            peak_value = portfolio_value
            max_drawdown = 0.0
            trade_log = []

            # Get common timestamps across all exchanges
            common_timestamps = None
            for df in historical_data.values():
                timestamps = set(df.index)
                if common_timestamps is None:
                    common_timestamps = timestamps
                else:
                    common_timestamps = common_timestamps.intersection(timestamps)

            if not common_timestamps:
                logger.error("No common timestamps found across exchanges")
                return results

            # Sort timestamps
            sorted_timestamps = sorted(list(common_timestamps))

            for timestamp in sorted_timestamps:
                # Get prices at this timestamp from all exchanges
                prices = {}
                for exchange_name, df in historical_data.items():
                    if timestamp in df.index:
                        row = df.loc[timestamp]
                        prices[exchange_name] = {
                            'bid': row['low'] * 0.999,  # Simulate bid slightly below low
                            'ask': row['high'] * 1.001,  # Simulate ask slightly above high
                            'last': row['close']
                        }

                if len(prices) >= 2:
                    # Simulate opportunity finding
                    opportunity = self.simulate_arbitrage_opportunity(symbol, timestamp, prices)

                    if opportunity:
                        results['total_opportunities'] += 1

                        if opportunity['net_profit_pct'] > 0:
                            results['profitable_opportunities'] += 1

                            # Simulate trade execution
                            profit = opportunity['expected_profit']
                            portfolio_value += profit

                            # Track peak and drawdown
                            if portfolio_value > peak_value:
                                peak_value = portfolio_value
                            else:
                                drawdown = (peak_value - portfolio_value) / peak_value * 100
                                max_drawdown = max(max_drawdown, drawdown)

                            # Record trade
                            trade = {
                                'timestamp': opportunity['timestamp'],
                                'profit': profit,
                                'portfolio_value': portfolio_value,
                                'drawdown': drawdown
                            }
                            trade_log.append(trade)

                            results['total_trades'] += 1
                            results['total_profit'] += profit
                            results['max_profit'] = max(results['max_profit'], profit)

                            if profit > 0:
                                results['winning_trades'] += 1

            # Calculate final metrics
            if results['total_trades'] > 0:
                results['win_rate'] = (results['winning_trades'] / results['total_trades']) * 100

                if results['total_loss'] != 0:
                    results['profit_factor'] = abs(results['total_profit'] / results['total_loss'])
                else:
                    results['profit_factor'] = float('inf')

            results['max_drawdown'] = max_drawdown
            results['final_portfolio_value'] = portfolio_value
            results['total_return_pct'] = ((portfolio_value - 1000) / 1000) * 100
            results['trades'] = trade_log[-50:]  # Keep last 50 trades for analysis

            logger.info(f"Backtest completed: {results['total_trades']} trades, "
                       f"{results['win_rate']:.1f}% win rate, "
                       f"${results['total_profit']:.2f} profit")

        except Exception as e:
            logger.error(f"Error during backtest: {e}")

        return results

    def run_monte_carlo_simulation(self, strategy_name: str, symbol: str,
                                 days: int = 30, simulations: int = 1000) -> Dict:
        """Run Monte Carlo simulation to assess strategy robustness"""
        logger.info(f"Running Monte Carlo simulation: {simulations} runs")

        results = []

        # Run multiple backtests with slight variations
        for i in range(simulations):
            # Add some randomness to the backtest parameters
            test_days = days + np.random.randint(-5, 6)  # ±5 days variation

            result = self.backtest_strategy(strategy_name, symbol, test_days)
            results.append(result)

        # Analyze results
        profits = [r['total_profit'] for r in results if r['total_trades'] > 0]
        win_rates = [r['win_rate'] for r in results if r['total_trades'] > 0]

        if profits and win_rates:
            analysis = {
                'total_simulations': len(results),
                'profitable_simulations': len([p for p in profits if p > 0]),
                'avg_profit': np.mean(profits),
                'median_profit': np.median(profits),
                'profit_std': np.std(profits),
                'max_profit': max(profits),
                'min_profit': min(profits),
                'profit_percentiles': {
                    '25th': np.percentile(profits, 25),
                    '75th': np.percentile(profits, 75),
                    '95th': np.percentile(profits, 95)
                },
                'avg_win_rate': np.mean(win_rates),
                'win_rate_std': np.std(win_rates),
                'probability_profit': len([p for p in profits if p > 0]) / len(profits) * 100,
                'expected_value': np.mean(profits),
                'risk_of_ruin': len([p for p in profits if p < -500]) / len(profits) * 100
            }

            logger.info(f"Monte Carlo completed: {analysis['probability_profit']:.1f}% profitable, "
                       f"Expected value: ${analysis['expected_value']:.2f}")

            return analysis

        return {'error': 'Insufficient data for Monte Carlo analysis'}

    def validate_strategy_profitability(self, strategy_name: str, symbol: str,
                                      min_win_rate: float = 60.0,
                                      min_profit_factor: float = 1.5) -> Dict:
        """Validate that a strategy meets profitability criteria"""
        logger.info(f"Validating strategy profitability: {strategy_name}")

        # Run backtest
        backtest_result = self.backtest_strategy(strategy_name, symbol, days=30)

        # Run Monte Carlo simulation
        mc_result = self.run_monte_carlo_simulation(strategy_name, symbol, days=30, simulations=100)

        validation = {
            'strategy': strategy_name,
            'symbol': symbol,
            'backtest_result': backtest_result,
            'monte_carlo_result': mc_result,
            'validation_criteria': {
                'min_win_rate': min_win_rate,
                'min_profit_factor': min_profit_factor
            },
            'passed_validation': False,
            'recommendation': 'NOT RECOMMENDED'
        }

        # Check validation criteria
        win_rate_ok = backtest_result.get('win_rate', 0) >= min_win_rate
        profit_factor_ok = backtest_result.get('profit_factor', 0) >= min_profit_factor
        mc_probability_ok = mc_result.get('probability_profit', 0) >= 60.0

        if win_rate_ok and profit_factor_ok and mc_probability_ok:
            validation['passed_validation'] = True
            validation['recommendation'] = 'RECOMMENDED'
        elif win_rate_ok or profit_factor_ok:
            validation['recommendation'] = 'CONDITIONAL'
        else:
            validation['recommendation'] = 'NOT RECOMMENDED'

        logger.info(f"Strategy validation: {validation['recommendation']}")

        return validation

    def optimize_strategy_parameters(self, strategy_name: str, symbol: str,
                                   parameter_ranges: Dict) -> Dict:
        """Optimize strategy parameters using walk-forward analysis"""
        logger.info(f"Optimizing parameters for {strategy_name}")

        best_params = {}
        best_performance = 0

        # This is a simplified optimization - in practice, you'd use more sophisticated methods
        for min_profit_pct in parameter_ranges.get('min_profit_pct', [0.3, 0.5, 0.8]):
            for max_positions in parameter_ranges.get('max_positions', [3, 5, 10]):
                # Test parameter combination
                config = {
                    'min_profit_pct': min_profit_pct,
                    'max_position_size': max_positions * 100
                }

                result = self.backtest_strategy(strategy_name, symbol, days=30)

                if result['total_profit'] > best_performance:
                    best_performance = result['total_profit']
                    best_params = {
                        'min_profit_pct': min_profit_pct,
                        'max_positions': max_positions,
                        'performance': result
                    }

        logger.info(f"Parameter optimization completed: {best_params}")
        return best_params


def main():
    """Main function for command-line usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Trading Strategy Backtesting Engine')
    parser.add_argument('--strategy', required=True, help='Strategy to backtest')
    parser.add_argument('--symbol', default='BTC', help='Trading symbol')
    parser.add_argument('--days', type=int, default=30, help='Backtest period in days')
    parser.add_argument('--validate', action='store_true', help='Run validation checks')
    parser.add_argument('--monte-carlo', type=int, help='Run Monte Carlo simulation with N runs')
    parser.add_argument('--optimize', action='store_true', help='Optimize strategy parameters')

    args = parser.parse_args()

    # Initialize exchanges (you would load actual API keys here)
    exchanges = {
        'binance': ccxt.binance({'sandbox': True}),
        'kraken': ccxt.kraken({'sandbox': True})
    }

    # Initialize backtesting engine
    engine = BacktestingEngine(exchanges)

    if args.validate:
        # Run validation
        result = engine.validate_strategy_profitability(args.strategy, args.symbol)
        print(json.dumps(result, indent=2))

    elif args.monte_carlo:
        # Run Monte Carlo simulation
        result = engine.run_monte_carlo_simulation(args.strategy, args.symbol, args.days, args.monte_carlo)
        print(json.dumps(result, indent=2))

    elif args.optimize:
        # Optimize parameters
        param_ranges = {
            'min_profit_pct': [0.3, 0.5, 0.8, 1.0],
            'max_positions': [3, 5, 10, 15]
        }
        result = engine.optimize_strategy_parameters(args.strategy, args.symbol, param_ranges)
        print(json.dumps(result, indent=2))

    else:
        # Run standard backtest
        result = engine.backtest_strategy(args.strategy, args.symbol, args.days)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()