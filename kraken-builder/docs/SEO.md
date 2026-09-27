# SEO and marketing — kraken.topta.co

## Positioning
One binary. Many tentacles. Local-first runner; premium arms licensed through api.topta.co.

Do not market it as “another AI agent framework.” Market it as a **device tool bus** for Pis, laptops, and small teams.

## On-page (in `website/`)
- Title + description on every page
- Canonical `https://kraken.topta.co/`
- `robots.txt` + `sitemap.xml`
- JSON-LD SoftwareApplication on the home page
- OG image = `img/mark.svg` (replace with 1200×630 PNG before launch)
- Internal links: docs, beta, register, catalog

## Keywords (realistic volume, not fantasy)
Primary: local tool runner, plugin CLI, tentacle, self-hosted automation  
Secondary: Raspberry Pi tools, offline CLI plugins, licensed CLI addons  
Avoid: generic “AI platform,” “kraken” alone (collision with exchange + sea beast)

## Channels
| Channel | Play |
|---|---|
| X / @mmcachran + topta | Short clips of `kraken monitor` and the typed demo |
| GitHub README | First 20 lines = install + one workflow |
| Race / DevOps circles | “runs on a Pi next to the race-clock box” |
| Product Hunt later | After public repo + one paid tentacle |
| Email | Beta list on register.html only |

## Upgrade funnel
1. `curl install` → `kraken doctor` (free)
2. Catalog card weather-pro → `license upgrade weather-pro --plan beta`
3. Control plane issues `beta-…` key, CLI stores `~/.kraken/keys/licenses.json`
4. `kraken run weather-pro forecast` works offline after that

No live Stripe in CI. Issue endpoint on laravel-lite returns deterministic beta keys.

## Measurement
- Site: page views on /, /docs, /register
- Product: `monitor.jsonl` count, tentacle add events (opt-in notify webhook)
- Do not phone home from free tentacles
