<?php

namespace Kraken\TradingBot;

use GuzzleHttp\Client;
use Exception;

/**
 * Twitter/X Integration for Trading Signals
 */
class TwitterIntegration
{
    private Client $httpClient;
    private ?string $bearerToken;

    public function __construct()
    {
        $this->httpClient = new Client([
            'timeout' => 10.0,
            'headers' => [
                'User-Agent' => 'Kraken-Trading-Bot/1.0'
            ]
        ]);

        $this->bearerToken = getenv('TWITTER_BEARER_TOKEN');
    }

    /**
     * Get trading prompts for a specific coin
     */
    public function getCoinTradingPrompts(string $coin): array
    {
        if (!$this->bearerToken) {
            return $this->getMockTradingPrompts($coin);
        }

        try {
            // In production, you'd implement actual Twitter API calls
            // For now, return mock data
            return $this->getMockTradingPrompts($coin);
        } catch (Exception $e) {
            error_log("Twitter API error: " . $e->getMessage());
            return $this->getMockTradingPrompts($coin);
        }
    }

    /**
     * Get mock trading prompts for development/testing
     */
    private function getMockTradingPrompts(string $coin): array
    {
        $prompts = [
            [
                'text' => "{$coin} looking bullish! Momentum building 📈 #{$coin} #trading",
                'sentiment' => 'positive',
                'timestamp' => date('c'),
                'author' => 'CryptoTrader123'
            ],
            [
                'text' => "{$coin} breaking resistance levels! 🚀 #{$coin}",
                'sentiment' => 'positive',
                'timestamp' => date('c'),
                'author' => 'MarketWatcher'
            ],
            [
                'text' => "Accumulating {$coin} for the long term 💎 #HODL",
                'sentiment' => 'neutral',
                'timestamp' => date('c'),
                'author' => 'DiamondHands'
            ]
        ];

        // Add some negative sentiment occasionally
        if (rand(1, 10) > 7) {
            $prompts[] = [
                'text' => "{$coin} showing weakness, might need to retest support 📉",
                'sentiment' => 'negative',
                'timestamp' => date('c'),
                'author' => 'BearishBetty'
            ];
        }

        return $prompts;
    }

    /**
     * Analyze sentiment from prompts
     */
    public function analyzeSentiment(array $prompts): array
    {
        $positive = 0;
        $negative = 0;
        $neutral = 0;

        foreach ($prompts as $prompt) {
            $sentiment = $prompt['sentiment'] ?? 'neutral';
            switch ($sentiment) {
                case 'positive':
                    $positive++;
                    break;
                case 'negative':
                    $negative++;
                    break;
                default:
                    $neutral++;
                    break;
            }
        }

        $total = count($prompts);
        return [
            'positive' => $total > 0 ? ($positive / $total) * 100 : 0,
            'negative' => $total > 0 ? ($negative / $total) * 100 : 0,
            'neutral' => $total > 0 ? ($neutral / $total) * 100 : 0,
            'overall_score' => $positive - $negative,
            'total_prompts' => $total
        ];
    }
}