# Launch — two surfaces, one core

Users get **either**:

1. **Native shell** (Capacitor, bundled `panel` HTML) on the same device that runs `kraken`. Settings, paths, resources. No `server.url` in the store build.
2. **Secure portal** `https://kraken.topta.co/account` via `api.topta.co` login. Scourge / multi-device after license + `kraken grant`.

They are not two products. The CLI is the product. The app and the site are clients.

Do **not** add Flutter. Do **not** put a WebView on a phone pointed at a laptop’s `127.0.0.1`.

## Open source

- MIT core + free tentacles (`panel`, `notes`, `expose`, `hello-world`, …).
- Premium `scourge` stays in-tree as an example with `license: premium` (key gated).
- Public repo name: `kraken-builder` under your GitHub when Administration+Contents is enabled. Until then this tree is the source.
- Never commit `~/.kraken/keys`, `scopes.json`, licenses.

## Marketing (one sentence)

One binary for the scripts already on your disk. Premium is fleet + portal, not a fatter CLI.

Channels: X (@mmcachran + @kraken_topta when claimed), README first 20 lines, `kraken demo` clip, then Product Hunt after Homebrew sha is filled. Do not create social accounts with injected JS.

## SEO

Canonical `https://kraken.topta.co/`. Keywords: local CLI plugin runner, tentacle, self-hosted automation. Avoid “Kraken” alone (exchange collision). Keep `sitemap.xml` + JSON-LD. OG 1200×630 from kit.

## Week of launch (human)

1. `PYTHONPATH=. python3 -m pytest tests/test_demo_first_json.py tests/test_expose.py tests/test_panel.py -q`
2. Build the live SPA (`applications/kraken` in the monorepo) — prerender writes crawlable HTML.
3. Search Console: property kraken.topta.co, submit sitemap.
4. Claim social names yourself; post drafts from `docs/SOCIAL.md` after a human click.
5. Tag `v0.1.1`. Fill Homebrew sha256. Capacitor store build later.

## Money

Free forever: core + vanilla tentacles.  
Paid: Scourge seat / org key. No live Stripe from this tree.

Details: BUSINESS.md, SEO.md, SOCIAL.md, PROMPT_LAPTOP.md, WEBVIEW.md.
