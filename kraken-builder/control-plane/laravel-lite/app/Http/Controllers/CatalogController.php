<?php
namespace KrakenControl\CatalogController;

function index(): array
{
    return [
        'ok' => true,
        'tentacles' => [
            ['name' => 'echo', 'kind' => 'in-process', 'license' => 'free'],
            ['name' => 'pi-host', 'kind' => 'in-process', 'license' => 'free'],
            ['name' => 'echo-bin', 'kind' => 'binary', 'license' => 'free'],
            ['name' => 'geo', 'kind' => 'binary', 'license' => 'free'],
            ['name' => 'weather-pro', 'kind' => 'binary', 'license' => 'premium'],
        ],
    ];
}
