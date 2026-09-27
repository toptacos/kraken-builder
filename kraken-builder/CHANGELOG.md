# Changelog

## 0.2.0 — 2026-09-27

### Added
- **`kraken up`** — the shared-network verb. Reads the compose plan `berth`
  wrote, reconciles its network against core's policy, and prints the result.
  Plan-only unless `--start` is passed, so it is safe in a script. See
  `docs/UP.md`.
  - Refuses to start under `KRAKEN_OFFLINE=1` (error code `offline`).
  - Refuses to start with no `docker` on `PATH` (error code `no_docker`).
  - Reports `network_mismatch` and names the offending services when a
    container in the plan is attached to a different network than core's — the
    failure mode where a service silently never joins.
  - Accepts an inline `compose`, a `file` path, or falls back to whichever
    planning arm wrote a plan (`berth`, `board`, `inlet`).
- `docs/OPEN-SOURCE.md` — what is MIT, what is metered, and the five
  integrations this project refuses, each with its local substitute.
- `docs/UP.md` — the `kraken up` contract.
- `tests/test_up_verb.py` (15 tests), `tests/test_license_contract.py` (8).

### Changed
- **The shared network is the bare name `kraken`.** Core previously normalized
  every name into `kraken_*`, which meant `kraken` became `kraken_kraken` and
  could never match the `kraken` network that `berth`, `sites/kraken.yaml`,
  and the docs all declare. Arbitrary labels are still namespaced
  (`lab` → `kraken_lab`), so two projects still cannot collide.
- `kraken/core/network.py` exports `normalize_network_name()` and
  `SHARED_NETWORK` instead of the private `_normalize_name()`.
- README restructured around an explicit open-source / metered split, plus a
  `kraken up` section. MIT badge, trove classifiers, and an `open-source`
  keyword added to `pyproject.toml`.
- `kraken tentacle add` progress moved from stdout to stderr, so install output
  no longer breaks the "stdout is one JSON object" contract.
- A `402` from the license API is now reported as an actionable message naming
  the seat and the pricing page, rather than a raw status line. A `5xx` still
  reads as a broken API, not a sales problem.

### Fixed
- **`KRAKEN_OFFLINE=1` no longer skips the remote `config_url` fetch.** The
  network resolver reached out regardless, which contradicted the documented
  offline-first posture. It now reports `fetch_skipped: offline` and keeps the
  local config.
- The polyglot example test pointed at flat `polyglot/echo.sh` paths after the
  fixtures were reorganised into per-language directories.

## 0.1.1 — 2026-09-14

### Product
- `kraken demo` runs vanilla `geo lookup` so first JSON lands in under 60s.
- `install.sh` runs `init` + `vanilla` + `demo` after putting `kraken`/`k` on PATH.
- `kraken doctor` and `kraken self plan` print `next` actions: geo, filesort, grant expose.
- `geo` fixture returns `city` + `ip` for 1.1.1.1 / 8.8.8.8 (offline, no network).

### Site
- Live SPA pages: use-cases, changelog, blog posts, register, long-form geo/filesort.
- Playground demos the geo contract with a city result (still does not exec on the host).
- Prerender script writes crawlable HTML for home, docs, catalog, blog.
- Optional `kraken.billing` package: local keys, hooks, verbose logs. MIT core does not require it.

### Distribution
- Homebrew formula at `Formula/kraken-cli.rb` (tap: toptacos/kraken).
- GitHub release workflow body includes install + CHANGELOG excerpt.
- Discussions templates: install, write-a-tentacle, showcase.

Brand: tentacle-K, ink `#0B1220`, teal `#2FD0C6`.
