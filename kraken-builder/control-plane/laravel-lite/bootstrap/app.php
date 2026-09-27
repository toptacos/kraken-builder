<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');

$uri = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
$routes = require dirname(__DIR__) . '/routes/api.php';

foreach ($routes as $pattern => $handler) {
    if ($pattern === $uri) {
        $result = $handler();
        echo json_encode($result);
        exit;
    }
}

http_response_code(404);
echo json_encode(['ok' => false, 'error' => ['code' => 'not_found']]);
