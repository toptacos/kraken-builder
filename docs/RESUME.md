# Resume — Kraken launch (2026-09-14)

Pick up here. Do not redesign the product. Lean CLI: JSON in → policy → exec → JSON out.

## Surfaces

- Site (Vue SPA, toptaco architecture): https://kraken.topta.co  
  Dist: `toptaco-monorepo/applications/kraken/dist` → frontend `/var/www/topta-monorepo/applications/kraken/dist`
- CLI tree: `TopTacos/Kraken/kraken-builder`
- Canonical git: https://github.com/toptacos/kraken-builder
- API: `toptaco-api/routes/kraken.php` live on `/var/www/toptaco-api` (`api.topta.co`)
- Billing: profile.topta.co/pricing → `POST /api/v1/billing/checkout`. Dashboard: `/admin/billing/subscriptions`
- topta.co is the brand hub. Taco Finder stays tacos.topta.co

## Repos (org team Kraken)

Public: kraken-builder, kraken-core, kraken-tentacles, kraken-suckers  
Private: kraken-scourge, kraken-premium  
CI green on all six. Fine-grained PAT in gitignored `TopTacos/toptaco-creds.env` (`GITHUB_TOKEN` / `GH_TOKEN`, mode 600). Org-private visibility needs the keyring classic token (`gh` without `GH_TOKEN`).

## Product facts

- PATH: `kraken` and alias `k` (symlink, not a tentacle name). `k run wx`.
- Envelopes: `kind` = json | text | file | media | params. Core does not interpret bytes.
- after_run sucker `patch` → tentacle `finish` if that action exists.
- Examples: `wx` + `wx-units` (Open-Meteo); `browse-js` + `save-text` (osascript/JS, Node fixture unless `KRAKEN_CHROME=1`).
- Playground is client-side only. No remote exec.
- `/brand` is off the public router. Brand docs stay in `docs/BRAND.md` (internal).
- Legal: TopTaco is a brand of McAchran Consulting LLC. Not “TopTa”.

## Last live fix

CSP on kraken.topta.co now allows `script-src`/`connect-src` for googletagmanager, google-analytics, static.cloudflareinsights (same pattern as tacos/blog). Repo copy: `toptaco-monorepo/shared/docker/nginx/sites-enabled/kraken.topta.co.conf`. Live file: `/etc/nginx/conf.d/kraken.topta.co.conf` on 161.35.113.140.

## Still human / later

- Live Stripe checkout with a real Sanctum session (plans exist; `KRAKEN_BILLING` was off for the stub route; real checkout is `/api/v1/billing/checkout`).
- Capacitor store build (webDir=www, no server.url).
- Post `docs/SOCIAL.md` (do not auto-post).
- Optional: prune ai/admin/support/auth if they should not 200 as dashboard clones.
- Push `workflow` files if a token lacks `workflow` scope (builder already has them).

## Verify

```
cd Kraken/kraken-builder
export PYTHONPATH=$PWD
python3 -m pytest tests/test_browse_js.py tests/test_wx_sucker.py tests/test_suckers.py tests/test_notes_tunnel_llm.py tests/test_expose.py tests/test_scopes_ca.py tests/test_panel.py tests/test_scourge_grant.py tests/test_install_wrapper.py -q
```
