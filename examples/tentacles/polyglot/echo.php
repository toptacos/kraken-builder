<?php
$req = json_decode(stream_get_contents(STDIN), true) ?: [];
echo json_encode([
  'v' => 1,
  'id' => $req['id'] ?? null,
  'ok' => true,
  'result' => [
    'arm' => 'echo-php',
    'lang' => 'php',
    'action' => $req['action'] ?? null,
    'echo' => $req['payload'] ?? new stdClass(),
  ],
]);
