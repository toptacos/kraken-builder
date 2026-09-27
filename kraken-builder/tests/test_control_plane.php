<?php
$_SERVER['REQUEST_URI'] = '/health';
ob_start();
require __DIR__ . '/../control-plane/public/index.php';
$out = ob_get_clean();
$data = json_decode($out, true);
if (empty($data['ok'])) {
    fwrite(STDERR, "health failed: $out\n");
    exit(1);
}
echo "control-plane health ok\n";
