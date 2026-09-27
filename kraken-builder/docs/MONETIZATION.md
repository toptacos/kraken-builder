# Open source + money

| Layer | License | Price |
|---|---|---|
| kraken-core CLI + contract | MIT | Free |
| Official fixtures (`echo`, `pi-host`, `geo`) | MIT | Free |
| Dev funnel (`docker-env`, `hotreload`) | MIT | Free — they sell the habit |
| `vault` / `store` | MIT now, premium later if hosted sync | Free local; paid if we run the pack relay |
| Catalog listing | — | Free for OSS; paid featured slot |
| Hosted control plane (keys, catalog, billing) | Service | $/month when Stripe is live |
| Paid tentacles (`weather-pro` pattern) | Author chooses | Author price; optional revenue share |
| Fleet install / Pi images / support | Services | Invoice |

Core does not phone home. Paid arms check a key. A school image can ship the runner without an account.

## What can actually make money

1. **Premium tentacles** — vertical data (weather, markets, OSINT enrichment) that is expensive to keep fresh. Pattern already in `weather-pro` + `license set`.
2. **Hosted catalog + issue/verify** — `api.topta.co` is the meter. Featured rows on kraken.topta.co.
3. **Pack relay** — encrypted `store` packs synced between two Kraken homes without the user standing up S3. Charge for the relay, not the CLI.
4. **Fleet / services** — install on a row of boxes, write the first three arms, retain. Fits McAchran Consulting work.
5. **Support / courses** — Nyx tracks + `website/courses.html` + `tutorial-tentacles.html` already exist. Paid cohort later.

## What should stay free

- Contract, doctor, hooks, workflows, docker-env plan/share, hotreload tick.
- Those are the install wedge. Charging for `kraken doctor` kills the funnel.

## What not to charge for yet

- Stripe Connect is not wired. Do not take cards in CI.
- Do not put ads in the CLI.
- Do not lock `vault` behind a key until openssl-on-argv and the XOR fallback are gone.

## Pricing sketch (not live)

| SKU | Who | Why they pay |
|---|---|---|
| Featured catalog slot | Tentacle author | Discoverability on kraken.topta.co |
| License seat | End user of a premium arm | Data / SLA |
| Pack relay | Two-box teams | Share without public S3 |
| Install day | Ops shop | Jump host + first workflow |

## Security that protects the business

A leaked `licenses.json` or a malicious `tentacle add` burns trust faster than a missing feature. See `docs/SECURITY.md`. Catalog rows need a source URL. Offline license is a feature for air-gap, not a way to skip paying when `KRAKEN_LICENSE_REMOTE=1` is set at work.

## Next wiring

- `POST /api/kraken/catalog/register` (stub in `control-plane/laravel-api/routes/kraken.php`)
- Stripe only after issue/verify is on the real api.topta.co
- Signed catalog checksums before we promote third-party binaries
