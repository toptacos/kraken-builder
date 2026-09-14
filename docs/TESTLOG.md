# Test log

2026-09-10 19:45 EDT

```
tests/test_free_apis.py
tests/test_sync.py
tests/test_notify_ntfy.py
tests/test_example_packs.py
tests/test_runtime.py
........  8 passed
```

Covered: offline Open-Meteo + ip-api fixtures, account session, ntfy quiet emit, pi-net/filesort/sites, runtime plan with data `:ro`.

2026-09-12 13:33 EDT

```
tests/test_sync.py test_runtime.py test_hooks.py test_contract.py
test_free_apis.py test_tentacle_install.py test_cli_e2e.py test_site_e2e.py
test_dev_tentacles.py
.......................... + site/dev  passed
```

Added website/security.html, website/docker.html, docs/USERNS.md. Brand kit in website/img/kit-2026/. Training shorts train-*.mp4.

Not run in this slice: full site E2E + hello-world compilers (slow on this image).

2026-09-14 EDT

```
PYTHONPATH=. python3 -m pytest tests/test_notes_tunnel_llm.py tests/test_expose.py tests/test_scopes_ca.py tests/test_panel.py tests/test_scourge_grant.py tests/test_suckers.py tests/test_site_e2e.py -q
......................  22 passed
python3 -m kraken init && python3 -m kraken vanilla && python3 -m kraken self plan
php artisan test tests/Feature/KrakenApiTest.php  # 3 tests, 10 assertions
```

Icons from kit-2026/icon-1024: 16, 32, 180, 192, 512 maskable, 1024, OG 1200x630, X 1200x600, Win 310, Linux 256.

Site is the Vue SPA at applications/kraken/dist (not the CLI). Live https://kraken.topta.co `/` `/docs` `/pricing` `/cli` `/account` `/features` `/blog/panel-scourge` 200. CSP + nosniff. Same-origin `/api/kraken/contact` 200. api.topta.co licenses/issue + devices 401 without org key.

Public: https://github.com/mmcachran/kraken-builder v0.1.0-beta
Org team Kraken: kraken-core, kraken-tentacles, kraken-suckers (public); kraken-scourge, kraken-premium (private).
Vercel CLI not installed. Social drafts stay in docs/SOCIAL.md.
Capacitor webDir=www, no server.url.

2026-09-14 later

Vue SPA routes live 200: /tentacles /suckers /grants /brand /security. catalog.json 23 tentacles.
Brand tokens ink #0B1220 teal #2FD0C6 foam #E7F6F6 gold #e7c56a on SPA.
topta.co Products + FeaturesGrid copy aligned to lean CLI (not Docker stack).
22 pytest still passed.
