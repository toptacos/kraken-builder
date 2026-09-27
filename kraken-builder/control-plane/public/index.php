<?php
declare(strict_types=1);

header('Content-Type: application/json');
$uri = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';

$catalog = [
    ['name' => 'echo', 'kind' => 'in-process', 'license' => 'MIT'],
    ['name' => 'pi-host', 'kind' => 'in-process', 'license' => 'MIT'],
    ['name' => 'echo-bin', 'kind' => 'binary', 'license' => 'MIT'],
];

if ($uri === '/health') {
    echo json_encode(['ok' => true, 'service' => 'kraken-control', 'db' => 'deferred']);
    exit;
}

if ($uri === '/catalog' || $uri === '/') {
    echo json_encode(['ok' => true, 'tentacles' => $catalog]);
    exit;
}

http_response_code(404);
echo json_encode(['ok' => false, 'error' => ['code' => 'not_found']]);
