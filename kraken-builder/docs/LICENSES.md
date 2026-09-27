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
