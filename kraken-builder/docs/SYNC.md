# Kraken CLI ↔ TopTacos Network Sync

This document describes every integration point between the Kraken CLI and the
TopTacos multi-domain network, the canonical source for each, and how to keep
them in sync.

## Architecture overview

```
Kraken CLI (Python)                     TopTacos Network
─────────────────                     ─────────────────
kraken/core/sync.py  ──────────────►  api.topta.co/api/kraken/session/*
kraken/core/license.py ────────────►  api.topta.co/api/kraken/licenses/*
kraken/billing/client.py ──────────►  api.topta.co/api/v1/billing/*
kraken/core/network.py ────────────►  Docker network "kraken" (local only)
install.sh ────────────────────────►  kraken.topta.co/install.sh (copy)
```

## Integration points

### 1. API routes

| Component | Canonical source | Copy location |
|-----------|-----------------|---------------|
| Kraken routes | `toptaco-api/routes/kraken.php` | `control-plane/laravel-api/routes/kraken.php` (stub) |
| Migrations | `toptaco-api/database/migrations/kraken/` | `control-plane/laravel-api/migrations/` (stubs) |
| Tests | `toptaco-api/tests/Feature/KrakenApiTest.php` | `tests/test_license_contract.py` |

**Sync rule:** Edit the canonical source in `toptaco-api/`. The copies in
`control-plane/` are stubs that throw if deployed. Run the PHP tests in the
TopTacos API to verify.

### 2. License contract

`POST /api/kraken/licenses/verify` returns:
- **200** — seat is paid and current
- **402** — no seat (invalid, revoked, or expired)
- **Other** — broken API

The CLI's `kraken/core/license.py` handles 402 with an actionable error message.
A 403 would be indistinguishable from a broken endpoint.

**Test:** `tests/test_license_contract.py` (8 tests, ~4.7s)

### 3. Billing plans

Plans are defined in `toptaco-api/database/seeders/BillingSeeder.php`:

| Plan | Price | CLI slug |
|------|-------|----------|
| Free | $0 | `beta` |
| Starter | $19/mo | `kraken-starter` |
| Pro | $49/mo | `kraken-pro` |
| Enterprise | $149/mo | `kraken-enterprise` |

The CLI validates slugs in `kraken/core/license.py:PLAN_SLUGS`. The API
enforces them in `POST /api/kraken/licenses/issue`.

### 4. Auth

Two auth modes:

| Mode | Token source | Use case |
|------|-------------|----------|
| Local | `dev_` UUID | Offline-first, no account needed |
| Sanctum | `KRAKEN_SANCTUM_TOKEN` env var | Reuse TopTacos SSO session |

`login_with_sanctum()` in `kraken/core/sync.py` accepts a Sanctum token from
the TopTacos SSO. The token is stored in `~/.kraken/keys/session.json` and
used for all API calls.

**Test:** `tests/test_sync.py` (7 tests, ~0.2s)

### 5. Install script

| Component | Canonical source | Copy location |
|-----------|-----------------|---------------|
| Installer | `install.sh` | `toptaco-monorepo/applications/kraken/public/install.sh` |

**Sync rule:** Edit `install.sh`, then copy to the monorepo. Run
`scripts/check-installer.sh` to verify sync.

### 6. Frontend

| Component | Location | Purpose |
|-----------|----------|---------|
| Vue 3 SPA | `toptaco-monorepo/applications/kraken/` | Production `kraken.topta.co` |
| Static site | `website/` | Marketing fallback, no build step |

The Vue SPA is the production frontend. The static site is a fallback for
environments where the SPA cannot be deployed.

### 7. Docker network

The Kraken CLI's `kraken/core/network.py` manages a local Docker network named
`kraken` for tentacle isolation. This is separate from the TopTacos
infrastructure's `infra/local/docker-compose.yml` (Postgres + Redis + API).

**Sync rule:** The CLI's Docker network is for local tentacle isolation only.
It does not affect the TopTacos production infrastructure.

### 8. Config

| Component | System | Location |
|-----------|--------|----------|
| Kraken CLI | 3-scope YAML | `.kraken/config.yaml` |
| TopTacos | JSON | `.opencode/config.json`, `config/ecosystem.json` |

These are separate systems. The Kraken CLI's config is for CLI behavior. The
TopTacos config is for the multi-domain network.

### 9. User model

| Component | Model | Location |
|-----------|-------|----------|
| TopTacos | `User` (Sanctum) | `toptaco-api/app/Models/User.php` |
| Kraken CLI | `kraken_users` table | `toptaco-api/database/migrations/kraken/` |

The Kraken CLI's `kraken_users` table is a separate, minimal user table for
CLI-specific data (device tracking, pinboard). It does not replace the
TopTacos `User` model. Sanctum auth via `login_with_sanctum()` bridges the two.

## Benchmark

| Test suite | Tests | Time | Coverage |
|------------|-------|------|----------|
| `test_license_contract.py` | 8 | ~4.7s | CLI↔API license contract |
| `test_license.py` | 4 | ~0.1s | Local license store |
| `test_license_cli.py` | 2 | ~0.1s | CLI license commands |
| `test_license_upgrade.py` | 3 | ~0.1s | License upgrade flow |
| `test_billing_package.py` | 6 | ~0.1s | Billing client |
| `test_sync.py` | 7 | ~0.2s | Session + auth |
| **Total** | **30** | **~5.3s** | |

## Checklist for new features

When adding a new Kraken CLI feature that touches the TopTacos network:

1. [ ] Add the API endpoint to `toptaco-api/routes/kraken.php`
2. [ ] Add a migration to `toptaco-api/database/migrations/kraken/`
3. [ ] Add a PHP test to `toptaco-api/tests/Feature/KrakenApiTest.php`
4. [ ] Add the CLI client method to `kraken/core/` or `kraken/billing/`
5. [ ] Add a Python test to `tests/`
6. [ ] Update `docs/SYNC.md` with the new integration point
7. [ ] Run both test suites: `pytest tests/` and `./vendor/bin/pest tests/Feature/KrakenApiTest.php`
