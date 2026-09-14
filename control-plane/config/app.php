<?php
return [
    'name' => 'kraken-control',
    'url' => 'https://kraken.topta.co',
    'db' => getenv('KRAKEN_DATABASE_URL') ?: null,
];
