# Optimized implementation prompt

Copy everything below the line into a new agent or engineer brief.

---

You are implementing **TopTaco** (company) on zone **topta.co**, product **Kraken** at https://kraken.topta.co.

## What you are building

A small DigitalOcean droplet serves branded frontends (`*.topta.co`).  
https://api.topta.co owns data and job queues.  
**Kraken** is one small local binary: JSON-in / JSON-out tentacles, hooks, optional shared Docker network named `kraken`. Core never imports tentacle source. Core verb for local compose is **`kraken up`**.

Do not confuse this with Payward / api.kraken.com. Do not call the site “Topta”. Always write full hosts.

## Names

| String | Use |
|---|---|
| TopTaco | company |
| topta.co | DNS + hub |
| Kraken | CLI only |
| tentacle | plugin (CLI child process **or** site yaml) |
| reef | set of arms |
| berth | tentacle that parses project.yaml into a network plan |

Brand: ink `#0B1220`, teal `#2FD0C6`, foam `#E7F6F6`, gold `#e7c56a`.  
Line: *One binary. Many tentacles.*

## Policy

- MIT the CLI arms and static frontends.
- Meter listings, hub Pro, optional seats, API quota — not the git tree.
- Secrets never in `sites/*.yaml` or tentacle config.
- Inbound integrations only. No vendor pull, no public Slack daemon, no MLS scrape.
- `KRAKEN_OFFLINE=1` default for telemetry. Opt-in events only: install_ok, demo_ok, second_cmd, arm_add, d7_return. No argv, no paths.
- Path jail: refuse `keys/`, `licenses.json`, catalog dumps.
- Redact `token`, `secret`, `password`, `client_secret`.
- Premium actions (`give`, `ingest`, `redeem`, `init` writes) return `error.code: payment_required` until core verifies license. `ping`/`help` stay free.
- Sign releases with **minisign**. HMAC fixtures are CI-only.
- Go arms: `CGO_ENABLED=0`, `-trimpath`, `-ldflags=-s -w`, GOOS/GOARCH matrix. Prefer GoReleaser + checksums.txt + `.minisig`.
- Python/PHP/JS/bash arms: `handler.sh` → interpreter. Same JSON envelope.

## JSON envelope v1

Request: `{"v":1,"id":null,"action":"ping","payload":{}}`  
Success: `{"v":1,"id":null,"ok":true,"result":{}}`  
Error: `{"v":1,"id":null,"ok":false,"error":{"code":"…","message":"…"}}`  
stdin one object, stdout one object. Core execs `tentacle.yaml` `binary`.

`tentacle.yaml` minimum: `name`, `version`, `license`, `runtime`, `binary`, `actions`.  
Optional: `hooks.after_install`, `init`, `needs_docker`, `platforms`, `mount: site|cli|both`.

A tentacle may expose **any number of functions**.

## Two mounts

**CLI:** `$KRAKEN_HOME/.kraken/data/<name>` + child handler.  
**Site:** `sites/<name>.yaml` → droplet vhost + API collection + allowed jobs. Droplet does not run workers.

## Implementation order (do not skip)

1. `GET https://api.topta.co/health` returns 200.
2. Droplet vhosts from `sites/*.yaml` (tacos, kraken, music, blog, discgolf, profile, portfolio).
3. Profile login gates those hosts.
4. Document and wire `kraken up` to berth’s `compose.yaml` + network `kraken`.
5. `POST /v1/kraken/license/verify` → 200 or 402; taco write paths stay gated.
6. Catalog register: sha256 + minisig. install.sh verifies before PATH.
7. Collect featured listing / hub Pro (already priced on the hub).
8. Seats after verify works.
9. Receipts add-on only if a paying org asks.

## Do not build

Second Stripe inside a tentacle. Docker on the public droplet. Family/real-estate apps. Public chat bots that steal `/taco`. Closed paid tentacles. HMAC sold as Ed25519.

## Done when

- `echo '{"v":1,"action":"ping"}' | handler` prints `ok:true` for each arm.
- Unlicensed taco `give` → `payment_required`.
- `berth plan` emits network name `kraken` and compose without starting a daemon.
- install.sh / goreleaser artifacts verify with minisign.
- A new site is adding a yaml, not a new droplet.

## Tests

JSON stdin tests per arm. Jail + redact cases. No live vendor calls. Offline first.

Work from the archive next to this file. Prefer extending existing handlers over new frameworks.
---
