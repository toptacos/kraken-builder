<?php
declare(strict_types=1);

use function KrakenControl\CatalogController\index as catalog;
use function KrakenControl\HealthController\index as health;
use function KrakenControl\LicenseController\beta as beta;
use function KrakenControl\LicenseController\issue as issue;
use function KrakenControl\LicenseController\verify as verify;

require_once dirname(__DIR__) . '/app/Http/Controllers/CatalogController.php';
require_once dirname(__DIR__) . '/app/Http/Controllers/HealthController.php';
require_once dirname(__DIR__) . '/app/Http/Controllers/LicenseController.php';

return [
    '/health' => health(...),
    '/catalog' => catalog(...),
    '/' => catalog(...),
    '/api/kraken/licenses/issue' => issue(...),
    '/api/kraken/licenses/verify' => verify(...),
    '/api/kraken/beta' => beta(...),
];
