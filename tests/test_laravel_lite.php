<?php
$_SERVER['REQUEST_URI'] = '/health';
ob_start();
require __DIR__ . '/../control-plane/laravel-lite/public/index.php';
$out = ob_get_clean();
$data = json_decode($out, true);
if (empty($data['ok']) || ($data['framework'] ?? '') !== 'laravel-lite') {
    fwrite(STDERR, "laravel-lite health failed: $out\n");
    exit(1);
}
echo "laravel-lite ok\n";
