# SEO playbook — kraken.topta.co

Live surface is the Vue SPA (`toptaco-monorepo/applications/kraken`). `website/` is the brand kit + static archive. Canonical paths have no `.html`.

## Positioning
Local CLI plugin runner. Not the crypto exchange.

**Title pattern:** `{Page} · Kraken CLI`  
**Home title:** `Kraken CLI · One binary. Many tentacles.`  
**Meta:** Local CLI plugin runner. Not the crypto exchange. Attach tentacles in any language. MIT core.

Canonical every page: `https://kraken.topta.co/{path}`  
`robots.txt` allow `/` disallow keys/admin. `npm run build` prerenders HTML + regenerates `sitemap.xml`.

## Primary queries (realistic)
local CLI plugin runner, self-hosted tentacle CLI, multi-language CLI plugins, Raspberry Pi local tools, licensed CLI addons

## Avoid
Ranking for “Kraken” alone, “Kraken exchange,” “AI platform,” “n8n killer.”

## On-page checklist
- Unique H1 that says Kraken CLI
- One H2 that repeats the query in plain English
- Internal links: docs, pricing, /blog, /register, /use-cases
- JSON-LD `SoftwareApplication` + `disambiguatingDescription` on home
- OG 1200×630
- Images: width + alt “Kraken tentacle-K mark”

## Journal (shipped on /blog)
1. Panel vs Scourge (`/blog/panel-scourge`)
2. Write a tentacle in bash and Go (`/blog/tentacle-bash-go`)
3. Grants: default deny (`/blog/grants-default-deny`)
4. Expose *.kraken.localhost (`/blog/kraken-localhost`)
5. Why the core stays small (`/blog/why-core-stays-small`)
6. Org API keys (`/blog/org-api-keys`)

Mirror to blog.topta.co via `scripts/publish-journal.sh` when `BLOG_API_TOKEN` is set. Category: DevOps.

## Measurement
Search Console property `https://kraken.topta.co/` — submit sitemap after deploy. Track `/`, `/cli`, `/docs`, `/catalog/*`, `/blog/*`, install.sh hits. Product events stay opt-in (`notify`).
