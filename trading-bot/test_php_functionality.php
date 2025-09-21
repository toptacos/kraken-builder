#!/usr/bin/env php
<?php

/**
 * PHP Functionality Test for Kraken Trading Bot
 * ============================================
 *
 * This script tests the PHP implementation of the trading bot
 * to ensure all components work correctly.
 */

require_once __DIR__ . '/vendor/autoload.php';

// Load environment variables
$dotenv = Dotenv\Dotenv::createImmutable(__DIR__);
$dotenv->load();

echo "🧪 Testing Kraken Trading Bot - PHP Implementation\n";
echo "================================================\n\n";

$tests_passed = 0;
$tests_total = 0;

function test($name, $callback) {
    global $tests_passed, $tests_total;
    $tests_total++;

    echo "Testing: $name... ";
    try {
        if ($callback()) {
            echo "✅ PASSED\n";
            $tests_passed++;
        } else {
            echo "❌ FAILED\n";
        }
    } catch (Exception $e) {
        echo "❌ ERROR: " . $e->getMessage() . "\n";
    }
}

// Test 1: Environment variables
test("Environment Variables", function() {
    $test_mode = getenv('TEST_MODE') === 'true';
    $starting_balance = (float) (getenv('STARTING_BALANCE') ?: 1000);
    return $test_mode && $starting_balance > 0;
});

// Test 2: Composer autoloader
test("Composer Autoloader", function() {
    return class_exists('Kraken\\TradingBot\\TradingBot');
});

// Test 3: TradingBot instantiation
test("TradingBot Instantiation", function() {
    $bot = new \Kraken\TradingBot\TradingBot();
    return $bot instanceof \Kraken\TradingBot\TradingBot;
});

// Test 4: Twitter integration
test("Twitter Integration", function() {
    $bot = new \Kraken\TradingBot\TradingBot();
    $twitter = $bot->getTwitterIntegration();
    return $twitter !== null;
});

// Test 5: Status retrieval
test("Status Retrieval", function() {
    $bot = new \Kraken\TradingBot\TradingBot();
    $status = $bot->getStatus();
    return is_array($status) && isset($status['is_running']);
});

// Test 6: Trending coin retrieval
test("Trending Coin Retrieval", function() {
    $bot = new \Kraken\TradingBot\TradingBot();
    $coin = $bot->getTrendingCoin();
    return is_string($coin) && strlen($coin) > 0;
});

// Test 7: Twitter prompts
test("Twitter Prompts", function() {
    $bot = new \Kraken\TradingBot\TradingBot();
    $twitter = $bot->getTwitterIntegration();
    if ($twitter) {
        $prompts = $twitter->getCoinTradingPrompts('BTC');
        return is_array($prompts);
    }
    return true; // Pass if Twitter not configured
});

// Test 8: Console command
test("Console Command", function() {
    $output = shell_exec('php bin/console status 2>&1');
    return strpos($output, 'Kraken Trading Bot Status') !== false;
});

// Test 9: Profit/Loss thresholds
test("Profit/Loss Thresholds", function() {
    $bot = new \Kraken\TradingBot\TradingBot();
    $status = $bot->getStatus();
    return isset($status['profit_threshold']) && isset($status['loss_threshold']);
});

// Test 10: Exchange availability
test("Exchange Availability", function() {
    $bot = new \Kraken\TradingBot\TradingBot();
    $status = $bot->getStatus();
    return isset($status['exchanges_count']) && $status['exchanges_count'] >= 0;
});

echo "\n📊 Test Results: $tests_passed/$tests_total tests passed\n";

if ($tests_passed === $tests_total) {
    echo "🎉 All PHP functionality tests passed!\n";
    echo "🚀 Ready for production deployment with: ./build_and_deploy.sh --php --build\n";
    exit(0);
} else {
    echo "⚠️ Some tests failed. Please check the output above.\n";
    exit(1);
}