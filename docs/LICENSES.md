# Premium licenses

Core stays free. A tentacle is premium only if its manifest or `.kraken` spec sets `license: premium`.

## Device flow

1. `kraken license set <tentacle> <key>` writes `~/.kraken/keys/licenses.json`
2. `kraken run <tentacle> …` calls `assert_licensed`
3. Free tentacles skip the check and never use the network
4. Remote verify (opt-in): `KRAKEN_LICENSE_REMOTE=1` or `kraken license verify <tentacle>`
   - `POST https://api.topta.co/api/kraken/licenses/verify`
   - `{ "tentacle", "key", "product": "kraken" }`
5. Offline allow: `KRAKEN_LICENSE_OFFLINE=1` after a key is stored

## Server

Existing Laravel + Postgres at api.topta.co. Drop in:

- `control-plane/laravel-api/routes/kraken.php`
- `control-plane/laravel-api/migrations/2026_09_10_000001_kraken_licenses.php`

The Vue site at `website/` is branding only. It does not issue keys.

## HTTP contract

`POST /api/kraken/licenses/verify` is a two-state contract:

| Status | Meaning | CLI behavior |
|--------|---------|--------------|
| 200 | Seat is paid and current | Proceeds |
| 402 | No seat (invalid, revoked, or expired) | Raises `LicenseError` with actionable message |
| Other | Broken API | Raises `LicenseError` with generic message |

The canonical source is `toptaco-api/routes/kraken.php`. The copy in
`control-plane/laravel-api/routes/kraken.php` must stay in sync — a 403 from
the copy would be indistinguishable from a broken endpoint.

## Benchmark

23 license-related tests pass in ~4.7s (Python 3.14, pytest 8.4.2).
The PHP feature tests in `toptaco-api/tests/Feature/KrakenApiTest.php`
cover the same contract from the server side.
