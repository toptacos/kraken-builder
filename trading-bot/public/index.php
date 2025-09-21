<?php
/**
 * Kraken Trading Bot - Dynamic Frontend
 * Ultra-fast PHP application with FrankenPHP
 */

// Enable error reporting for development
ini_set('display_errors', 1);
error_reporting(E_ALL);

// Autoload classes
require_once __DIR__ . '/../vendor/autoload.php';

// Load environment variables (with fallback)
try {
    if (class_exists('Dotenv\Dotenv')) {
        $dotenv = Dotenv\Dotenv::createImmutable(__DIR__ . '/..');
        $dotenv->load();
    }
} catch (Exception $e) {
    // Fallback: environment variables already loaded by Docker
    error_log('Dotenv not available, using system environment variables');
}

// Start session
session_start();

// Simple routing
$request = $_SERVER['REQUEST_METHOD'] . ' ' . $_SERVER['REQUEST_URI'];
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

// API Routes
if (strpos($path, '/api/') === 0) {
    header('Content-Type: application/json');
    header('Access-Control-Allow-Origin: *');
    header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, Authorization');

    if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
        exit(0);
    }

    require_once __DIR__ . '/../src/api.php';
    exit;
}

// WebSocket for real-time updates
if (strpos($path, '/ws/') === 0) {
    require_once __DIR__ . '/../src/websocket.php';
    exit;
}

// Static pages
switch ($path) {
    case '/':
    case '/dashboard':
        require_once __DIR__ . '/../templates/dashboard.php';
        break;

    case '/status':
        // Return JSON status for API calls
        header('Content-Type: application/json');
        echo json_encode([
            'status' => 'running',
            'timestamp' => date('c'),
            'version' => '1.0.0',
            'message' => 'Kraken Trading Bot PHP API'
        ]);
        break;

    case '/health':
        // Return simple health check
        header('Content-Type: application/json');
        echo json_encode([
            'status' => 'healthy',
            'timestamp' => date('c'),
            'version' => '1.0.0'
        ]);
        break;

    case '/trading':
        require_once __DIR__ . '/../templates/trading.php';
        break;

    case '/analytics':
        require_once __DIR__ . '/../templates/analytics.php';
        break;

    case '/settings':
        require_once __DIR__ . '/../templates/settings.php';
        break;

    case '/logs':
        require_once __DIR__ . '/../templates/logs.php';
        break;

    default:
        http_response_code(404);
        echo json_encode(['error' => 'Page not found']);
        break;
}