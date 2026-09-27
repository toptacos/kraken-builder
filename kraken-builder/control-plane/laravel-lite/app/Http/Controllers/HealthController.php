<?php
namespace KrakenControl;

function HealthController_index(): array
{
    return ['ok' => true, 'service' => 'kraken-control', 'framework' => 'laravel-lite', 'db' => getenv('KRAKEN_DATABASE_URL') ? 'configured' : 'deferred'];
}

namespace KrakenControl\HealthController;

function index(): array
{
    return \KrakenControl\HealthController_index();
}
