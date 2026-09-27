<?php
namespace KrakenControl\LicenseController;

function issue(): array
{
    $body = json_decode(file_get_contents('php://input') ?: '{}', true) ?: [];
    $tentacle = (string) ($body['tentacle'] ?? '');
    if ($tentacle === '') {
        return ['ok' => false, 'error' => 'missing tentacle'];
    }
    return [
        'ok' => true,
        'tentacle' => $tentacle,
        'plan' => $body['plan'] ?? 'beta',
        'key' => 'beta-' . substr(sha1($tentacle . ($body['email'] ?? '')), 0, 12),
    ];
}

function beta(): array
{
    $body = json_decode(file_get_contents('php://input') ?: '{}', true) ?: [];
    return ['ok' => true, 'queued' => true, 'email' => $body['email'] ?? null];
}

function verify(): array
{
    $body = json_decode(file_get_contents('php://input') ?: '{}', true) ?: [];
    $key = (string) ($body['key'] ?? '');
    if ($key === '' || !str_starts_with($key, 'beta-')) {
        return ['ok' => false, 'error' => ['message' => 'invalid license']];
    }
    return ['ok' => true, 'tentacle' => $body['tentacle'] ?? ''];
}
