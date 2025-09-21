<?php
/**
 * Kraken Trading Bot API
 * RESTful API for trading operations and data
 */

header('Content-Type: application/json');

// Get request method and path
$method = $_SERVER['REQUEST_METHOD'];
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

// Remove /api prefix
$endpoint = str_replace('/api', '', $path);

// Parse query parameters
$query = $_GET;

// Get POST data
$input = json_decode(file_get_contents('php://input'), true) ?? [];

// Route API requests
switch ($endpoint) {
    case '/health':
        handleHealthCheck();
        break;

    case '/status':
        handleStatus();
        break;

    case '/portfolio':
        handlePortfolio();
        break;

    case '/trades':
        handleTrades();
        break;

    case '/analytics':
        handleAnalytics();
        break;

    case '/prompts':
        handlePrompts($method, $input);
        break;

    case '/trading/start':
        handleTradingStart($method, $input);
        break;

    case '/trading/stop':
        handleTradingStop($method);
        break;

    case '/settings':
        handleSettings($method, $input);
        break;

    default:
        http_response_code(404);
        echo json_encode(['error' => 'API endpoint not found']);
        break;
}

function handleHealthCheck() {
    $health = [
        'status' => 'healthy',
        'timestamp' => date('c'),
        'version' => '1.0.0',
        'services' => [
            'web' => 'running',
            'database' => 'connected',
            'trading_bot' => checkTradingBotStatus()
        ]
    ];

    echo json_encode($health);
}

function handleStatus() {
    $status = [
        'trading_active' => isTradingActive(),
        'current_balance' => getCurrentBalance(),
        'daily_pnl' => getDailyPnL(),
        'active_positions' => getActivePositions(),
        'last_trade' => getLastTrade(),
        'system_load' => getSystemLoad()
    ];

    echo json_encode($status);
}

function handlePortfolio() {
    $portfolio = [
        'total_balance' => getTotalBalance(),
        'positions' => getPositions(),
        'performance' => getPerformanceMetrics(),
        'allocations' => getAssetAllocations()
    ];

    echo json_encode($portfolio);
}

function handleTrades() {
    $limit = $_GET['limit'] ?? 50;
    $offset = $_GET['offset'] ?? 0;

    $trades = getRecentTrades($limit, $offset);

    echo json_encode([
        'trades' => $trades,
        'total' => count($trades),
        'limit' => $limit,
        'offset' => $offset
    ]);
}

function handleAnalytics() {
    $period = $_GET['period'] ?? '24h';

    $analytics = [
        'profit_loss' => getProfitLossData($period),
        'volume' => getVolumeData($period),
        'performance' => getPerformanceData($period),
        'risk_metrics' => getRiskMetrics($period)
    ];

    echo json_encode($analytics);
}

function handlePrompts($method, $input) {
    switch ($method) {
        case 'GET':
            $prompts = getSamplePrompts();
            echo json_encode(['prompts' => $prompts]);
            break;

        case 'POST':
            $result = scrapeTwitterPrompts($input);
            echo json_encode($result);
            break;

        default:
            http_response_code(405);
            echo json_encode(['error' => 'Method not allowed']);
    }
}

function handleTradingStart($method, $input) {
    if ($method !== 'POST') {
        http_response_code(405);
        echo json_encode(['error' => 'Method not allowed']);
        return;
    }

    $strategy = $input['strategy'] ?? 'default';
    $amount = $input['amount'] ?? 100;

    $result = startTradingBot($strategy, $amount);

    echo json_encode($result);
}

function handleTradingStop($method) {
    if ($method !== 'POST') {
        http_response_code(405);
        echo json_encode(['error' => 'Method not allowed']);
        return;
    }

    $result = stopTradingBot();

    echo json_encode($result);
}

function handleSettings($method, $input) {
    switch ($method) {
        case 'GET':
            $settings = getSettings();
            echo json_encode($settings);
            break;

        case 'PUT':
        case 'POST':
            $result = updateSettings($input);
            echo json_encode($result);
            break;

        default:
            http_response_code(405);
            echo json_encode(['error' => 'Method not allowed']);
    }
}

// Helper functions (implement these based on your trading bot)
function checkTradingBotStatus() {
    // Check if Python trading bot is running
    $output = shell_exec('pgrep -f "python3 trading_bot.py"');
    return $output ? 'running' : 'stopped';
}

function isTradingActive() {
    return checkTradingBotStatus() === 'running';
}

function getCurrentBalance() {
    // Read from trading bot status file or API
    return 1000.00; // Placeholder
}

function getDailyPnL() {
    return 25.50; // Placeholder
}

function getActivePositions() {
    return 3; // Placeholder
}

function getLastTrade() {
    return [
        'symbol' => 'BTC/USDT',
        'side' => 'buy',
        'amount' => 0.001,
        'price' => 45000,
        'timestamp' => date('c')
    ];
}

function getSystemLoad() {
    $load = sys_getloadavg();
    return [
        '1m' => $load[0],
        '5m' => $load[1],
        '15m' => $load[2]
    ];
}

function getTotalBalance() {
    return getCurrentBalance();
}

function getPositions() {
    return [
        ['symbol' => 'BTC', 'amount' => 0.5, 'value' => 22500],
        ['symbol' => 'ETH', 'amount' => 5.0, 'value' => 15000]
    ];
}

function getPerformanceMetrics() {
    return [
        'total_return' => 8.5,
        'win_rate' => 65.2,
        'sharpe_ratio' => 1.8,
        'max_drawdown' => -12.3
    ];
}

function getAssetAllocations() {
    return [
        'BTC' => 60,
        'ETH' => 25,
        'USDT' => 15
    ];
}

function getRecentTrades($limit, $offset) {
    // Return mock trade data
    return [
        [
            'id' => 1,
            'symbol' => 'BTC/USDT',
            'side' => 'buy',
            'amount' => 0.001,
            'price' => 45000,
            'timestamp' => date('c', strtotime('-1 hour'))
        ]
    ];
}

function getProfitLossData($period) {
    return [
        'labels' => ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        'data' => [100, 120, 115, 130, 125]
    ];
}

function getVolumeData($period) {
    return [
        'labels' => ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        'data' => [1000, 1200, 800, 1500, 1100]
    ];
}

function getPerformanceData($period) {
    return [
        'total_trades' => 25,
        'winning_trades' => 16,
        'losing_trades' => 9,
        'total_pnl' => 245.50
    ];
}

function getRiskMetrics($period) {
    return [
        'volatility' => 15.2,
        'beta' => 1.1,
        'value_at_risk' => -5.2
    ];
}

function getSamplePrompts() {
    return [
        "What's the current market sentiment for Bitcoin?",
        "Analyze the correlation between BTC and ETH",
        "What are the best altcoins to watch this week?",
        "Technical analysis for BTC/USD",
        "Market outlook for the next 24 hours"
    ];
}

function scrapeTwitterPrompts($input) {
    require_once __DIR__ . '/twitter_scraper.php';

    $scraper = new TwitterScraper();

    // Search for crypto tweets
    $tweets = $scraper->searchCryptoTweets(
        $input['query'] ?? 'crypto OR bitcoin OR ethereum',
        $input['max_results'] ?? 50
    );

    // Extract trading prompts
    $prompts = $scraper->extractTradingPrompts($tweets);

    return [
        'status' => 'success',
        'prompts' => $prompts,
        'scraped_at' => date('c'),
        'total_tweets' => count($tweets),
        'query' => $input['query'] ?? 'crypto OR bitcoin OR ethereum'
    ];
}

function startTradingBot($strategy, $amount) {
    // Start the Python trading bot
    $command = "python3 trading_bot.py --strategy=$strategy --amount=$amount > /dev/null 2>&1 &";
    exec($command, $output, $returnCode);

    return [
        'status' => $returnCode === 0 ? 'started' : 'failed',
        'strategy' => $strategy,
        'amount' => $amount,
        'pid' => $returnCode === 0 ? getmypid() : null
    ];
}

function stopTradingBot() {
    // Stop the Python trading bot
    exec('pkill -f "python3 trading_bot.py"', $output, $returnCode);

    return [
        'status' => $returnCode === 0 ? 'stopped' : 'failed',
        'message' => 'Trading bot stop signal sent'
    ];
}

function getSettings() {
    return [
        'risk_level' => 'medium',
        'max_trades_per_day' => 10,
        'stop_loss_percentage' => 2.0,
        'take_profit_percentage' => 5.0,
        'enabled_exchanges' => ['binance', 'kraken'],
        'notification_email' => ''
    ];
}

function updateSettings($settings) {
    // Save settings to file/database
    file_put_contents(__DIR__ . '/../storage/settings.json', json_encode($settings));

    return [
        'status' => 'updated',
        'settings' => $settings
    ];
}