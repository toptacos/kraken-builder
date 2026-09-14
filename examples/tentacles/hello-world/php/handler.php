<?php
$req = json_decode(stream_get_contents(STDIN), true) ?: [];
$name = $req['payload']['name'] ?? 'world';
echo json_encode([
    'v' => 1, 'id' => $req['id'] ?? null, 'ok' => true,
    'result' => ['arm' => 'hello-php', 'lang' => 'php', 'hello' => "hello, $name"],
]);
