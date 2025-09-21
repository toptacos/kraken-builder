<?php
/**
 * Twitter/X Scraper for Trading Prompts
 * Scrapes Twitter for market sentiment and trading insights
 */

class TwitterScraper
{
    private $bearerToken;
    private $baseUrl = 'https://api.twitter.com/2';

    public function __construct()
    {
        // You'll need to get a Twitter API Bearer Token
        $this->bearerToken = getenv('TWITTER_BEARER_TOKEN') ?: '';
    }

    /**
     * Search for recent tweets about crypto trading
     */
    public function searchCryptoTweets($query = 'crypto OR bitcoin OR ethereum', $maxResults = 100)
    {
        if (empty($this->bearerToken)) {
            return $this->getMockTweets();
        }

        $url = $this->baseUrl . '/tweets/search/recent';
        $params = [
            'query' => $query . ' -is:retweet lang:en',
            'max_results' => min($maxResults, 100),
            'tweet.fields' => 'created_at,public_metrics,text,author_id',
            'user.fields' => 'username,name,verified'
        ];

        $response = $this->makeRequest($url, $params);

        if ($response && isset($response['data'])) {
            return $this->processTweets($response['data']);
        }

        return $this->getMockTweets();
    }

    /**
     * Extract trading prompts from tweets
     */
    public function extractTradingPrompts($tweets)
    {
        $prompts = [];

        foreach ($tweets as $tweet) {
            $text = $tweet['text'];

            // Look for trading-related keywords and patterns
            if ($this->isTradingRelated($text)) {
                $prompt = $this->generatePromptFromTweet($text);
                if ($prompt) {
                    $prompts[] = [
                        'prompt' => $prompt,
                        'source' => 'twitter',
                        'tweet_id' => $tweet['id'] ?? null,
                        'created_at' => $tweet['created_at'] ?? date('c'),
                        'sentiment' => $this->analyzeSentiment($text)
                    ];
                }
            }
        }

        return array_slice($prompts, 0, 20); // Limit to 20 prompts
    }

    /**
     * Check if tweet is trading-related
     */
    private function isTradingRelated($text)
    {
        $tradingKeywords = [
            'buy', 'sell', 'trading', 'trade', 'crypto', 'bitcoin', 'btc', 'ethereum', 'eth',
            'altcoin', 'bullish', 'bearish', 'moon', 'dump', 'pump', 'hodl', 'diamond hands',
            'breakout', 'resistance', 'support', 'technical analysis', 'ta', 'indicator',
            'rsi', 'macd', 'bollinger', 'fibonacci', 'chart', 'pattern', 'signal'
        ];

        $text = strtolower($text);

        foreach ($tradingKeywords as $keyword) {
            if (strpos($text, $keyword) !== false) {
                return true;
            }
        }

        return false;
    }

    /**
     * Generate trading prompt from tweet
     */
    private function generatePromptFromTweet($text)
    {
        // Clean the text
        $text = preg_replace('/https?:\/\/[^\s]+/', '', $text); // Remove URLs
        $text = preg_replace('/@\w+/', '', $text); // Remove mentions
        $text = preg_replace('/#\w+/', '', $text); // Remove hashtags
        $text = trim($text);

        // Limit length
        if (strlen($text) > 200) {
            $text = substr($text, 0, 197) . '...';
        }

        return $text;
    }

    /**
     * Analyze sentiment of tweet
     */
    private function analyzeSentiment($text)
    {
        $positiveWords = ['bullish', 'moon', 'pump', 'buy', 'up', 'green', 'profit', 'gain', 'breakout', 'surge'];
        $negativeWords = ['bearish', 'dump', 'sell', 'down', 'red', 'loss', 'crash', 'drop', 'decline'];

        $text = strtolower($text);
        $positiveCount = 0;
        $negativeCount = 0;

        foreach ($positiveWords as $word) {
            $positiveCount += substr_count($text, $word);
        }

        foreach ($negativeWords as $word) {
            $negativeCount += substr_count($text, $word);
        }

        if ($positiveCount > $negativeCount) {
            return 'positive';
        } elseif ($negativeCount > $positiveCount) {
            return 'negative';
        } else {
            return 'neutral';
        }
    }

    /**
     * Make HTTP request to Twitter API
     */
    private function makeRequest($url, $params = [])
    {
        $ch = curl_init();

        $queryString = http_build_query($params);
        $fullUrl = $url . '?' . $queryString;

        curl_setopt_array($ch, [
            CURLOPT_URL => $fullUrl,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER => [
                'Authorization: Bearer ' . $this->bearerToken,
                'Content-Type: application/json'
            ],
            CURLOPT_SSL_VERIFYPEER => true,
            CURLOPT_TIMEOUT => 30
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);

        curl_close($ch);

        if ($error) {
            error_log("Twitter API Error: $error");
            return null;
        }

        if ($httpCode !== 200) {
            error_log("Twitter API HTTP $httpCode: $response");
            return null;
        }

        return json_decode($response, true);
    }

    /**
     * Process tweets from API response
     */
    private function processTweets($tweets)
    {
        $processed = [];

        foreach ($tweets as $tweet) {
            $processed[] = [
                'id' => $tweet['id'],
                'text' => $tweet['text'],
                'created_at' => $tweet['created_at'],
                'author_id' => $tweet['author_id'],
                'metrics' => $tweet['public_metrics'] ?? []
            ];
        }

        return $processed;
    }

    /**
     * Get mock tweets for testing (when API is not available)
     */
    private function getMockTweets()
    {
        return [
            [
                'id' => '1',
                'text' => 'Bitcoin showing strong bullish signals with RSI above 70. Expecting breakout soon! #BTC #Crypto',
                'created_at' => date('c'),
                'author_id' => 'mock_user_1'
            ],
            [
                'id' => '2',
                'text' => 'Ethereum upgrade next week could pump ETH prices significantly. Getting ready for the moon! 🚀',
                'created_at' => date('c'),
                'author_id' => 'mock_user_2'
            ],
            [
                'id' => '3',
                'text' => 'Market analysis: BTC dominance increasing, altcoins might face pressure. Time to accumulate BTC?',
                'created_at' => date('c'),
                'author_id' => 'mock_user_3'
            ],
            [
                'id' => '4',
                'text' => 'Technical analysis shows BTC breaking out of descending triangle. Bullish momentum building!',
                'created_at' => date('c'),
                'author_id' => 'mock_user_4'
            ],
            [
                'id' => '5',
                'text' => 'Just sold all my altcoins for BTC. This market is getting too risky. Better safe than sorry.',
                'created_at' => date('c'),
                'author_id' => 'mock_user_5'
            ]
        ];
    }

    /**
     * Get trending crypto topics from Twitter
     */
    public function getTrendingTopics()
    {
        // This would require Twitter API v1.1 for trends
        // For now, return mock trending topics
        return [
            'Bitcoin',
            'Ethereum',
            'Crypto',
            'BTC',
            'ETH',
            'Altcoins',
            'DeFi',
            'NFT'
        ];
    }
}

// Usage example
if (basename(__FILE__) === basename($_SERVER['PHP_SELF'])) {
    $scraper = new TwitterScraper();

    // Search for crypto tweets
    $tweets = $scraper->searchCryptoTweets();

    // Extract trading prompts
    $prompts = $scraper->extractTradingPrompts($tweets);

    // Return as JSON
    header('Content-Type: application/json');
    echo json_encode([
        'status' => 'success',
        'prompts' => $prompts,
        'scraped_at' => date('c'),
        'total_tweets' => count($tweets)
    ]);
}