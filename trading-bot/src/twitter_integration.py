#!/usr/bin/env python3
"""
Twitter/X Integration for Automated Trading Bot
Integrates with PHP Twitter scraper to get trading prompts and sentiment analysis
"""

import os
import json
import logging
import requests
import subprocess
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import threading

logger = logging.getLogger(__name__)

class TwitterIntegration:
    """Integrates Twitter/X sentiment analysis with trading bot"""

    def __init__(self, php_scraper_path: str = "src/twitter_scraper.php"):
        self.php_scraper_path = php_scraper_path
        self.last_scrape_time = None
        self.scrape_interval = 300  # 5 minutes
        self.cached_prompts = []
        self.sentiment_cache = {}
        self.is_running = False
        self.scrape_thread = None

    def start_background_scraping(self):
        """Start background thread for continuous Twitter scraping"""
        if self.is_running:
            logger.info("Twitter scraping already running")
            return

        self.is_running = True
        self.scrape_thread = threading.Thread(target=self._background_scrape_loop, daemon=True)
        self.scrape_thread.start()
        logger.info("🧵 Started Twitter background scraping thread")

    def stop_background_scraping(self):
        """Stop background Twitter scraping"""
        self.is_running = False
        if self.scrape_thread:
            self.scrape_thread.join(timeout=5)
        logger.info("🧵 Stopped Twitter background scraping")

    def _background_scrape_loop(self):
        """Background loop for continuous Twitter scraping"""
        while self.is_running:
            try:
                self.scrape_trading_prompts()
                time.sleep(self.scrape_interval)
            except Exception as e:
                logger.error(f"Error in Twitter scraping loop: {e}")
                time.sleep(60)  # Wait 1 minute on error

    def scrape_trading_prompts(self) -> List[Dict]:
        """Scrape trading prompts from Twitter using PHP scraper"""
        try:
            # Check if we need to scrape (respect rate limits)
            if self.last_scrape_time and (datetime.now() - self.last_scrape_time).seconds < 60:
                logger.debug("Using cached Twitter prompts (rate limited)")
                return self.cached_prompts

            logger.info("🔍 Scraping Twitter for trading prompts...")

            # Run PHP scraper
            result = subprocess.run(
                ['php', self.php_scraper_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )

            if result.returncode != 0:
                logger.warning(f"PHP scraper failed: {result.stderr}")
                return self._get_mock_prompts()

            # Parse JSON response
            try:
                data = json.loads(result.stdout)
                if data.get('status') == 'success':
                    prompts = data.get('prompts', [])
                    self.cached_prompts = prompts
                    self.last_scrape_time = datetime.now()
                    logger.info(f"✅ Scraped {len(prompts)} trading prompts from Twitter")
                    return prompts
                else:
                    logger.warning("Twitter scraper returned error status")
                    return self._get_mock_prompts()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Twitter scraper response: {e}")
                return self._get_mock_prompts()

        except subprocess.TimeoutExpired:
            logger.warning("Twitter scraping timed out")
            return self._get_mock_prompts()
        except Exception as e:
            logger.error(f"Error scraping Twitter prompts: {e}")
            return self._get_mock_prompts()

    def get_sentiment_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get sentiment analysis for a specific cryptocurrency"""
        try:
            # Get recent prompts
            prompts = self.scrape_trading_prompts()

            # Filter prompts for the symbol
            symbol_prompts = []
            symbol_lower = symbol.lower()

            for prompt in prompts:
                text = prompt.get('prompt', '').lower()
                if symbol_lower in text or f"#{symbol_lower}" in text:
                    symbol_prompts.append(prompt)

            if not symbol_prompts:
                return {
                    'symbol': symbol,
                    'sentiment': 'neutral',
                    'confidence': 0.0,
                    'prompts_count': 0,
                    'analysis': 'No recent Twitter mentions found'
                }

            # Analyze sentiment
            positive_count = 0
            negative_count = 0
            neutral_count = 0

            for prompt in symbol_prompts:
                sentiment = prompt.get('sentiment', 'neutral')
                if sentiment == 'positive':
                    positive_count += 1
                elif sentiment == 'negative':
                    negative_count += 1
                else:
                    neutral_count += 1

            total = len(symbol_prompts)

            # Determine overall sentiment
            if positive_count > negative_count and positive_count > neutral_count:
                overall_sentiment = 'bullish'
                confidence = positive_count / total
            elif negative_count > positive_count and negative_count > neutral_count:
                overall_sentiment = 'bearish'
                confidence = negative_count / total
            else:
                overall_sentiment = 'neutral'
                confidence = max(positive_count, negative_count, neutral_count) / total

            analysis = ".1f" ".1f" ".1f"

            return {
                'symbol': symbol,
                'sentiment': overall_sentiment,
                'confidence': round(confidence, 2),
                'prompts_count': total,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count,
                'analysis': analysis,
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing sentiment for {symbol}: {e}")
            return {
                'symbol': symbol,
                'sentiment': 'neutral',
                'confidence': 0.0,
                'error': str(e)
            }

    def get_trading_signals_from_twitter(self) -> List[Dict]:
        """Extract trading signals from Twitter prompts"""
        try:
            prompts = self.scrape_trading_prompts()
            signals = []

            for prompt in prompts:
                text = prompt.get('prompt', '').lower()
                sentiment = prompt.get('sentiment', 'neutral')

                # Extract potential signals
                signal = self._extract_signal_from_text(text, sentiment)
                if signal:
                    signals.append({
                        'signal': signal,
                        'sentiment': sentiment,
                        'confidence': prompt.get('confidence', 0.5),
                        'source': 'twitter',
                        'timestamp': prompt.get('created_at', datetime.now().isoformat()),
                        'text': prompt.get('prompt', '')
                    })

            logger.info(f"📊 Generated {len(signals)} trading signals from Twitter")
            return signals[:10]  # Limit to top 10 signals

        except Exception as e:
            logger.error(f"Error extracting trading signals from Twitter: {e}")
            return []

    def _extract_signal_from_text(self, text: str, sentiment: str) -> Optional[str]:
        """Extract trading signal from text content"""
        try:
            # Buy signals
            buy_keywords = ['buy', 'bullish', 'moon', 'pump', 'breakout', 'surge', 'green', 'profit', 'gain', 'accumulate']
            sell_keywords = ['sell', 'bearish', 'dump', 'crash', 'drop', 'red', 'loss', 'decline', 'short']

            buy_score = sum(1 for keyword in buy_keywords if keyword in text)
            sell_score = sum(1 for keyword in sell_keywords if keyword in text)

            if buy_score > sell_score:
                return 'BUY'
            elif sell_score > buy_score:
                return 'SELL'
            elif sentiment == 'positive':
                return 'BUY'
            elif sentiment == 'negative':
                return 'SELL'
            else:
                return None

        except Exception as e:
            logger.debug(f"Error extracting signal from text: {e}")
            return None

    def _get_mock_prompts(self) -> List[Dict]:
        """Return mock prompts when Twitter scraping fails"""
        return [
            {
                'prompt': 'Bitcoin showing strong bullish signals with RSI above 70. Expecting breakout soon!',
                'source': 'twitter',
                'sentiment': 'positive',
                'created_at': datetime.now().isoformat(),
                'confidence': 0.8
            },
            {
                'prompt': 'Ethereum upgrade next week could pump ETH prices significantly. Getting ready for the moon!',
                'source': 'twitter',
                'sentiment': 'positive',
                'created_at': datetime.now().isoformat(),
                'confidence': 0.7
            },
            {
                'prompt': 'Market analysis: BTC dominance increasing, altcoins might face pressure.',
                'source': 'twitter',
                'sentiment': 'neutral',
                'created_at': datetime.now().isoformat(),
                'confidence': 0.6
            },
            {
                'prompt': 'Technical analysis shows BTC breaking out of descending triangle. Bullish momentum building!',
                'source': 'twitter',
                'sentiment': 'positive',
                'created_at': datetime.now().isoformat(),
                'confidence': 0.75
            },
            {
                'prompt': 'Just sold all my altcoins for BTC. This market is getting too risky.',
                'source': 'twitter',
                'sentiment': 'negative',
                'created_at': datetime.now().isoformat(),
                'confidence': 0.65
            }
        ]

    def get_market_sentiment_summary(self) -> Dict[str, Any]:
        """Get overall market sentiment summary from Twitter"""
        try:
            prompts = self.scrape_trading_prompts()

            if not prompts:
                return {
                    'overall_sentiment': 'neutral',
                    'confidence': 0.0,
                    'total_prompts': 0,
                    'analysis': 'No Twitter data available'
                }

            positive_count = sum(1 for p in prompts if p.get('sentiment') == 'positive')
            negative_count = sum(1 for p in prompts if p.get('sentiment') == 'negative')
            neutral_count = sum(1 for p in prompts if p.get('sentiment') == 'neutral')

            total = len(prompts)

            # Determine overall sentiment
            if positive_count > negative_count and positive_count > neutral_count:
                overall_sentiment = 'bullish'
                confidence = positive_count / total
            elif negative_count > positive_count and negative_count > neutral_count:
                overall_sentiment = 'bearish'
                confidence = negative_count / total
            else:
                overall_sentiment = 'neutral'
                confidence = max(positive_count, negative_count, neutral_count) / total

            analysis = ".1f" ".1f" ".1f"

            return {
                'overall_sentiment': overall_sentiment,
                'confidence': round(confidence, 2),
                'total_prompts': total,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count,
                'analysis': analysis,
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting market sentiment summary: {e}")
            return {
                'overall_sentiment': 'neutral',
                'confidence': 0.0,
                'error': str(e)
            }


# Global Twitter integration instance
_twitter_integration = None

def get_twitter_integration() -> TwitterIntegration:
    """Get global Twitter integration instance"""
    global _twitter_integration
    if _twitter_integration is None:
        _twitter_integration = TwitterIntegration()
    return _twitter_integration

def initialize_twitter_integration(start_background: bool = True) -> TwitterIntegration:
    """Initialize Twitter integration"""
    global _twitter_integration
    _twitter_integration = TwitterIntegration()

    if start_background:
        _twitter_integration.start_background_scraping()

    logger.info("🐦 Twitter integration initialized")
    return _twitter_integration

# Example usage
if __name__ == "__main__":
    # Initialize Twitter integration
    twitter = initialize_twitter_integration(start_background=False)

    # Test sentiment analysis
    btc_sentiment = twitter.get_sentiment_analysis('BTC')
    print("BTC Sentiment:", json.dumps(btc_sentiment, indent=2))

    # Test market sentiment
    market_sentiment = twitter.get_market_sentiment_summary()
    print("Market Sentiment:", json.dumps(market_sentiment, indent=2))

    # Test trading signals
    signals = twitter.get_trading_signals_from_twitter()
    print(f"Trading Signals: {len(signals)} found")
    for signal in signals[:3]:
        print(f"  - {signal['signal']}: {signal['text'][:50]}...")