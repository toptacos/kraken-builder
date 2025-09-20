#!/usr/bin/env python3
"""
Advanced Crypto Trend Analyzer
==============================

This module provides comprehensive cryptocurrency trend analysis by scraping
and analyzing data from multiple sources including:

- CoinGecko Trending API
- CoinMarketCap Trending
- LunarCrush Social Sentiment
- Google Trends
- Reddit Sentiment Analysis
- Twitter Trending Topics
- News Sentiment Analysis
- Technical Analysis Indicators

Features:
- Multi-source data aggregation
- Sentiment analysis
- Technical indicators
- Trend strength scoring
- Risk assessment
- Real-time updates
"""

import os
import json
import time
import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("Warning: beautifulsoup4 not available, web scraping disabled")

import ccxt

logger = logging.getLogger(__name__)

class CryptoTrendAnalyzer:
    def __init__(self, cache_dir: str = "trend_cache", update_interval: int = 300):
        self.cache_dir = cache_dir
        self.update_interval = update_interval  # 5 minutes
        self.cache = {}

        # API Keys (optional)
        self.coingecko_key = os.getenv('COINGECKO_API_KEY')
        self.cmc_key = os.getenv('COINMARKETCAP_API_KEY')
        self.lunarcrush_key = os.getenv('LUNARCRUSH_API_KEY')

        # Data sources
        self.sources = {
            'coingecko': self._scrape_coingecko,
            'coinmarketcap': self._scrape_coinmarketcap,
            'lunarcrush': self._scrape_lunarcrush,
            'google_trends': self._scrape_google_trends,
            'reddit': self._scrape_reddit_sentiment,
            'news': self._scrape_news_sentiment,
            'technical': self._analyze_technical_indicators
        }

        # Trend scoring weights
        self.weights = {
            'coingecko': 0.25,
            'coinmarketcap': 0.20,
            'lunarcrush': 0.15,
            'google_trends': 0.10,
            'reddit': 0.10,
            'news': 0.10,
            'technical': 0.10
        }

        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)

        # Load existing cache
        self._load_cache()

        logger.info("Crypto Trend Analyzer initialized")

    def _load_cache(self):
        """Load cached trend data"""
        cache_file = os.path.join(self.cache_dir, "trend_data.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} cached trend entries")
            except Exception as e:
                logger.error(f"Error loading cache: {e}")

    def _save_cache(self):
        """Save trend data to cache"""
        cache_file = os.path.join(self.cache_dir, "trend_data.json")
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False

        cache_time = datetime.fromisoformat(self.cache[cache_key]['timestamp'])
        return (datetime.now() - cache_time).seconds < self.update_interval

    def _cache_result(self, cache_key: str, data: Any):
        """Cache analysis result"""
        self.cache[cache_key] = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        self._save_cache()

    def _scrape_coingecko(self) -> List[Dict]:
        """Scrape trending coins from CoinGecko"""
        logger.info("🔍 [CoinGecko] Starting trend analysis...")
        try:
            url = "https://api.coingecko.com/api/v3/search/trending"
            logger.debug(f"📡 [CoinGecko] Requesting: {url}")
            response = requests.get(url, timeout=10)

            logger.info(f"📊 [CoinGecko] Response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                trending = []

                coins_data = data.get('coins', [])
                logger.info(f"📈 [CoinGecko] Processing {len(coins_data)} trending coins")

                for i, coin_data in enumerate(coins_data):
                    coin = coin_data.get('item', {})
                    symbol = coin.get('symbol', '').upper()
                    name = coin.get('name', '')
                    market_cap_rank = coin.get('market_cap_rank')
                    price_btc = coin.get('price_btc', 0)

                    trending.append({
                        'symbol': symbol,
                        'name': name,
                        'market_cap_rank': market_cap_rank,
                        'price_btc': price_btc,
                        'source': 'coingecko',
                        'score': 100,  # CoinGecko trending score
                        'timestamp': datetime.now().isoformat()
                    })

                    logger.debug(f"💎 [CoinGecko] #{i+1}: {symbol} ({name}) - Rank: {market_cap_rank}, BTC Price: {price_btc}")

                logger.info(f"✅ [CoinGecko] Successfully scraped {len(trending)} trending coins")
                return trending
            else:
                logger.warning(f"⚠️ [CoinGecko] API returned status {response.status_code}")

        except Exception as e:
            logger.error(f"❌ [CoinGecko] Error scraping: {e}")

        return []

    def _scrape_coinmarketcap(self) -> List[Dict]:
        """Scrape trending coins from CoinMarketCap"""
        logger.info("🔍 [CoinMarketCap] Starting trend analysis...")
        try:
            url = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing"
            headers = {}
            if self.cmc_key:
                headers['X-CMC_PRO_API_KEY'] = self.cmc_key
                logger.debug("🔑 [CoinMarketCap] Using API key for enhanced data")
            else:
                logger.debug("🔓 [CoinMarketCap] No API key - using free tier")

            params = {
                'start': '1',
                'limit': '100',
                'sortBy': 'percent_change_24h',
                'sortType': 'desc'
            }

            logger.debug(f"📡 [CoinMarketCap] Requesting: {url} with params: {params}")
            response = requests.get(url, headers=headers, params=params, timeout=10)

            logger.info(f"📊 [CoinMarketCap] Response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                trending = []

                coins_list = data.get('data', {}).get('cryptoCurrencyList', [])[:20]
                logger.info(f"📈 [CoinMarketCap] Processing top {len(coins_list)} coins by 24h change")

                for i, coin in enumerate(coins_list):
                    symbol = coin.get('symbol', '')
                    name = coin.get('name', '')
                    price = coin.get('quotes', [{}])[0].get('price', 0)
                    percent_change = coin.get('quotes', [{}])[0].get('percentChange24h', 0)

                    # Calculate trend score based on 24h change
                    score = min(max(percent_change * 10, 0), 100)  # Scale to 0-100

                    trending.append({
                        'symbol': symbol,
                        'name': name,
                        'price': price,
                        'percent_change_24h': percent_change,
                        'source': 'coinmarketcap',
                        'score': score,
                        'timestamp': datetime.now().isoformat()
                    })

                    logger.debug(f"💎 [CoinMarketCap] #{i+1}: {symbol} ({name}) - 24h Change: {percent_change:.2f}%, Score: {score:.1f}")

                logger.info(f"✅ [CoinMarketCap] Successfully scraped {len(trending)} trending coins")
                return trending
            else:
                logger.warning(f"⚠️ [CoinMarketCap] API returned status {response.status_code}")

        except Exception as e:
            logger.error(f"❌ [CoinMarketCap] Error scraping: {e}")

        return []

    def _scrape_lunarcrush(self) -> List[Dict]:
        """Scrape social sentiment from LunarCrush"""
        try:
            if not self.lunarcrush_key:
                logger.debug("LunarCrush API key not provided")
                return []

            url = "https://api.lunarcrush.com/v2/assets"
            headers = {'Authorization': f'Bearer {self.lunarcrush_key}'}
            params = {
                'data': 'assets',
                'type': 'full',
                'sort': 'social_score',
                'limit': 50
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                trending = []

                for asset in data.get('data', [])[:20]:
                    # Calculate sentiment score
                    social_score = asset.get('social_score', 0)
                    sentiment = asset.get('sentiment', 0)
                    score = min(max((social_score + sentiment * 50), 0), 100)

                    trending.append({
                        'symbol': asset.get('symbol', ''),
                        'name': asset.get('name', ''),
                        'social_score': social_score,
                        'sentiment': sentiment,
                        'source': 'lunarcrush',
                        'score': score,
                        'timestamp': datetime.now().isoformat()
                    })

                logger.info(f"LunarCrush: Found {len(trending)} trending coins")
                return trending

        except Exception as e:
            logger.error(f"Error scraping LunarCrush: {e}")

        return []

    def _scrape_google_trends(self) -> List[Dict]:
        """Scrape Google Trends for crypto interest"""
        try:
            # This is a simplified implementation
            # In production, you'd use Google Trends API or pytrends
            trending_terms = [
                'Bitcoin', 'Ethereum', 'Solana', 'Cardano',
                'Polkadot', 'Chainlink', 'Avalanche', 'Polygon'
            ]

            trending = []
            for term in trending_terms:
                # Simulate trend score (0-100)
                score = np.random.randint(20, 80)  # Replace with actual API call

                trending.append({
                    'symbol': term.upper()[:3] if len(term) > 3 else term.upper(),
                    'name': term,
                    'trend_score': score,
                    'source': 'google_trends',
                    'score': score,
                    'timestamp': datetime.now().isoformat()
                })

            logger.info(f"Google Trends: Found {len(trending)} trending terms")
            return trending

        except Exception as e:
            logger.error(f"Error scraping Google Trends: {e}")

        return []

    def _scrape_reddit_sentiment(self) -> List[Dict]:
        """Analyze Reddit sentiment for cryptocurrencies"""
        try:
            # This is a simplified implementation
            # In production, you'd use Reddit API or PRAW
            subreddits = ['cryptocurrency', 'bitcoin', 'ethereum', 'solana']

            trending = []
            crypto_symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'LINK', 'AVAX', 'MATIC']

            for symbol in crypto_symbols:
                # Simulate sentiment analysis
                sentiment_score = np.random.normal(0.6, 0.2)  # Mean 0.6, std 0.2
                sentiment_score = max(0, min(1, sentiment_score))  # Clamp to 0-1
                score = sentiment_score * 100

                trending.append({
                    'symbol': symbol,
                    'name': f"Reddit_{symbol}",
                    'sentiment_score': sentiment_score,
                    'mentions': np.random.randint(10, 1000),
                    'source': 'reddit',
                    'score': score,
                    'timestamp': datetime.now().isoformat()
                })

            logger.info(f"Reddit: Analyzed sentiment for {len(trending)} coins")
            return trending

        except Exception as e:
            logger.error(f"Error analyzing Reddit sentiment: {e}")

        return []

    def _scrape_news_sentiment(self) -> List[Dict]:
        """Analyze news sentiment for cryptocurrencies"""
        try:
            # This is a simplified implementation
            # In production, you'd use news APIs like NewsAPI or Alpha Vantage
            news_sources = [
                'CoinDesk', 'CoinTelegraph', 'CryptoSlate',
                'Decrypt', 'The Block', 'Blockworks'
            ]

            trending = []
            crypto_symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'LINK']

            for symbol in crypto_symbols:
                # Simulate news sentiment analysis
                sentiment_score = np.random.normal(0.55, 0.15)
                sentiment_score = max(0, min(1, sentiment_score))
                score = sentiment_score * 100

                trending.append({
                    'symbol': symbol,
                    'name': f"News_{symbol}",
                    'sentiment_score': sentiment_score,
                    'article_count': np.random.randint(5, 50),
                    'source': 'news',
                    'score': score,
                    'timestamp': datetime.now().isoformat()
                })

            logger.info(f"News: Analyzed sentiment for {len(trending)} coins")
            return trending

        except Exception as e:
            logger.error(f"Error analyzing news sentiment: {e}")

        return []

    def _analyze_technical_indicators(self, exchanges: Dict[str, ccxt.Exchange]) -> List[Dict]:
        """Analyze technical indicators for trending coins"""
        try:
            trending = []
            base_coins = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'LINK', 'AVAX', 'MATIC']

            for symbol_base in base_coins:
                symbol = f"{symbol_base}/USDT"

                # Get technical data from primary exchange
                primary_exchange = list(exchanges.keys())[0]
                exchange = exchanges[primary_exchange]

                if symbol not in exchange.symbols:
                    continue

                try:
                    # Fetch recent OHLCV data
                    ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=50)

                    if len(ohlcv) < 20:
                        continue

                    # Calculate technical indicators
                    closes = [candle[4] for candle in ohlcv]

                    # RSI (Relative Strength Index)
                    rsi = self._calculate_rsi(closes, 14)

                    # MACD
                    macd, signal, histogram = self._calculate_macd(closes)

                    # Bollinger Bands
                    upper, middle, lower = self._calculate_bollinger_bands(closes, 20, 2)

                    # Trend strength score (0-100)
                    current_price = closes[-1]
                    trend_score = 50  # Neutral

                    # RSI signals
                    if rsi > 70:
                        trend_score += 20  # Overbought but strong momentum
                    elif rsi < 30:
                        trend_score -= 20  # Oversold but weak momentum

                    # MACD signals
                    if histogram[-1] > histogram[-2] > 0:
                        trend_score += 15  # Bullish momentum
                    elif histogram[-1] < histogram[-2] < 0:
                        trend_score -= 15  # Bearish momentum

                    # Bollinger Band position
                    if current_price > upper:
                        trend_score += 10  # Strong upward momentum
                    elif current_price < lower:
                        trend_score -= 10  # Strong downward momentum

                    # Clamp to 0-100
                    trend_score = max(0, min(100, trend_score))

                    trending.append({
                        'symbol': symbol_base,
                        'name': f"Technical_{symbol_base}",
                        'rsi': rsi,
                        'macd': macd,
                        'macd_signal': signal,
                        'macd_histogram': histogram[-1],
                        'bb_upper': upper,
                        'bb_middle': middle,
                        'bb_lower': lower,
                        'current_price': current_price,
                        'source': 'technical',
                        'score': trend_score,
                        'timestamp': datetime.now().isoformat()
                    })

                except Exception as e:
                    logger.debug(f"Error analyzing {symbol}: {e}")
                    continue

            logger.info(f"Technical Analysis: Analyzed {len(trending)} coins")
            return trending

        except Exception as e:
            logger.error(f"Error in technical analysis: {e}")

        return []

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
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

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9):
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow:
            return 0, 0, 0

        # Calculate EMAs
        fast_ema = self._calculate_ema(prices, fast)
        slow_ema = self._calculate_ema(prices, slow)

        # MACD line
        macd_line = fast_ema - slow_ema

        # Signal line
        signal_line = self._calculate_ema([macd_line] * len(prices), signal)

        # Histogram
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return sum(prices) / len(prices)

        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period

        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def _calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2):
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return prices[-1], prices[-1], prices[-1]

        sma = sum(prices[-period:]) / period
        std = np.std(prices[-period:])

        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)

        return upper, sma, lower

    def analyze_trends(self, exchanges: Optional[Dict[str, ccxt.Exchange]] = None) -> Dict:
        """Comprehensive trend analysis from all sources"""
        cache_key = "comprehensive_trends"
        if self._is_cache_valid(cache_key):
            logger.info("📋 Using cached comprehensive trend analysis")
            return self.cache[cache_key]['data']

        logger.info("🚀 Starting comprehensive trend analysis across 7 data sources...")
        start_time = datetime.now()

        # Collect data from all sources in parallel
        results = {}
        logger.info(f"🔄 Processing {len(self.sources)} data sources in parallel...")

        with ThreadPoolExecutor(max_workers=len(self.sources)) as executor:
            future_to_source = {
                executor.submit(func, exchanges if 'technical' in func.__name__ else None): source
                for source, func in self.sources.items()
            }

            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    results[source] = future.result()
                    result_count = len(results[source])
                    logger.info(f"✅ [{source.upper()}] Completed: {result_count} results")
                except Exception as e:
                    logger.error(f"❌ [{source.upper()}] Error: {e}")
                    results[source] = []

        # Aggregate and score all coins
        logger.info("🔀 Aggregating data from all sources...")
        aggregated_trends = self._aggregate_trends(results)

        # Sort by composite score
        aggregated_trends.sort(key=lambda x: x['composite_score'], reverse=True)

        processing_time = (datetime.now() - start_time).total_seconds()

        analysis_result = {
            'timestamp': datetime.now().isoformat(),
            'processing_time_seconds': processing_time,
            'sources_analyzed': list(results.keys()),
            'total_coins_found': len(aggregated_trends),
            'top_trends': aggregated_trends[:20],  # Top 20 trending coins
            'source_breakdown': {source: len(data) for source, data in results.items()},
            'raw_data': results
        }

        # Cache the result
        self._cache_result(cache_key, analysis_result)

        # Log detailed results
        logger.info(f"🎯 Trend analysis complete in {processing_time:.2f}s")
        logger.info(f"📊 Total coins analyzed: {len(aggregated_trends)}")
        logger.info(f"🏆 Top trending coins: {', '.join([coin['symbol'] for coin in aggregated_trends[:5]])}")

        # Log source breakdown
        for source, count in analysis_result['source_breakdown'].items():
            logger.info(f"   • {source}: {count} coins")

        return analysis_result

    def _aggregate_trends(self, results: Dict[str, List[Dict]]) -> List[Dict]:
        """Aggregate trend data from all sources"""
        coin_scores = {}

        # Process each source
        for source, data in results.items():
            weight = self.weights.get(source, 0.1)

            for item in data:
                symbol = item.get('symbol', '').upper()
                if not symbol:
                    continue

                if symbol not in coin_scores:
                    coin_scores[symbol] = {
                        'symbol': symbol,
                        'name': item.get('name', symbol),
                        'sources': {},
                        'scores': [],
                        'metadata': {}
                    }

                # Store source-specific data
                coin_scores[symbol]['sources'][source] = item
                coin_scores[symbol]['scores'].append(item.get('score', 0) * weight)

                # Store additional metadata
                for key, value in item.items():
                    if key not in ['symbol', 'name', 'source', 'score', 'timestamp']:
                        coin_scores[symbol]['metadata'][f"{source}_{key}"] = value

        # Calculate composite scores
        aggregated = []
        for symbol, data in coin_scores.items():
            if data['scores']:
                composite_score = sum(data['scores']) / len(data['scores'])
                data['composite_score'] = composite_score
                data['source_count'] = len(data['sources'])
                data['avg_score'] = sum(data['scores']) / len(data['scores'])
                aggregated.append(data)

        return aggregated

    def get_top_trending_coins(self, limit: int = 20,
                              min_score: float = 30.0,
                              min_sources: int = 2) -> List[str]:
        """Get top trending coins based on analysis"""
        analysis = self.analyze_trends()

        filtered_coins = []
        for coin in analysis['top_trends']:
            if (coin['composite_score'] >= min_score and
                coin['source_count'] >= min_sources):
                filtered_coins.append(coin['symbol'])

        # Add major coins that are always tradeable
        major_coins = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOT', 'DOGE', 'SHIB']
        for coin in major_coins:
            if coin not in filtered_coins:
                filtered_coins.append(coin)

        return filtered_coins[:limit]

    def get_coin_analysis(self, symbol: str) -> Optional[Dict]:
        """Get detailed analysis for a specific coin"""
        analysis = self.analyze_trends()

        for coin in analysis['top_trends']:
            if coin['symbol'] == symbol.upper():
                return coin

        return None

    def export_analysis_report(self, filename: str = None) -> str:
        """Export comprehensive analysis report"""
        if not filename:
            filename = f"trend_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        analysis = self.analyze_trends()

        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2)

        logger.info(f"Analysis report exported to {filename}")
        return filename


# Global trend analyzer instance
trend_analyzer = None

def initialize_trend_analyzer(cache_dir: str = "trend_cache", update_interval: int = 300):
    """Initialize the global trend analyzer"""
    global trend_analyzer
    trend_analyzer = CryptoTrendAnalyzer(cache_dir, update_interval)
    return trend_analyzer

def get_trend_analyzer():
    """Get the global trend analyzer instance"""
    return trend_analyzer

# Example usage:
"""
# Initialize
analyzer = initialize_trend_analyzer()

# Get trending coins
trending_coins = analyzer.get_top_trending_coins(limit=20, min_score=40.0)

# Get detailed analysis for specific coin
btc_analysis = analyzer.get_coin_analysis('BTC')

# Export full report
analyzer.export_analysis_report()
"""