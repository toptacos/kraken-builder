# Control plane (kraken.topta.co)

**The canonical control plane lives in the TopTacos API** (`toptaco-api/`).
This directory contains reference copies only — do NOT deploy from here.

## Canonical source

| Component | Canonical path |
|-----------|---------------|
| Routes | `toptaco-api/routes/kraken.php` |
| Migrations | `toptaco-api/database/migrations/kraken/` |
| Tests | `toptaco-api/tests/Feature/KrakenApiTest.php` |
| Billing plans | `toptaco-api/database/seeders/BillingSeeder.php` |

## What is in this directory

- `laravel-api/routes/kraken.php` — stub that throws if deployed
- `laravel-api/migrations/*.php` — stubs that throw if deployed
- `laravel-lite/` — standalone PHP micro-framework (no Composer)
- `public/index.php` — health + catalog JSON endpoint
- `config/app.php` — app config
- `database/schema.sql` — Postgres schema

## Local smoke (no Postgres required)

```bash
php -S 127.0.0.1:8081 -t control-plane/public
curl http://127.0.0.1:8081/health
```

## Deployment

The Kraken API is served by the TopTacos API at `api.topta.co`. To deploy
changes:

1. Edit the canonical files in `toptaco-api/`
2. Run the PHP tests: `cd toptaco-api && ./vendor/bin/pest tests/Feature/KrakenApiTest.php`
3. Deploy the TopTacos API

Do not deploy from this directory — the stubs will throw runtime exceptions.
