# Changelog

## 0.1.1 — 2026-09-14

### Product
- `kraken demo` runs vanilla `geo lookup` so first JSON lands in under 60s.
- `install.sh` runs `init` + `vanilla` + `demo` after putting `kraken`/`k` on PATH.
- `kraken doctor` and `kraken self plan` print `next` actions: geo, filesort, grant expose.
- `geo` fixture returns `city` + `ip` for 1.1.1.1 / 8.8.8.8 (offline, no network).

### Site
- Live SPA pages: use-cases, changelog, blog posts, register, long-form geo/filesort.
- Playground demos the geo contract with a city result (still does not exec on the host).
- JSON-LD disambiguates Kraken CLI from the crypto exchange.
- Prerender script writes crawlable HTML for home, docs, catalog, blog.

### Distribution
- Homebrew formula at `Formula/kraken-cli.rb` (tap: toptacos/kraken).
- GitHub release workflow body includes install + CHANGELOG excerpt.
- Discussions templates: install, write-a-tentacle, showcase.

Not the Kraken exchange. Brand: tentacle-K, ink `#0B1220`, teal `#2FD0C6`.
