# Launch — two surfaces, one core

Users get **either**:

1. **Native shell** (Capacitor, bundled `panel` HTML) on the same device that runs `kraken`. Settings, paths, resources. No `server.url` in the store build.
2. **Secure portal** `https://kraken.topta.co/account.html` via `api.topta.co` login. Scourge / multi-device after license + `kraken grant`.

They are not two products. The CLI is the product. The app and the site are clients.

Do **not** add Flutter. Do **not** put a WebView on a phone pointed at a laptop’s `127.0.0.1`.

## Open source

- MIT core + free tentacles (`panel`, `notes`, `expose`, `hello-world`, …).
- Premium `scourge` stays in-tree as an example with `license: premium` (key gated).
- Public repo name: `kraken-builder` under your GitHub when Administration+Contents is enabled. Until then this tree is the source.
- Never commit `~/.kraken/keys`, `scopes.json`, licenses.

## Marketing (one sentence)

One binary for the scripts already on your disk. Premium is fleet + portal, not a fatter CLI.

Channels: X (@mmcachran + @kraken_topta when claimed), README first 20 lines, courses shorts, then Product Hunt after the public repo exists.

## SEO

Canonical `https://kraken.topta.co/`. Keywords: local CLI plugin runner, tentacle, self-hosted automation. Avoid “Kraken” alone (exchange collision). Keep `sitemap.xml` + JSON-LD. OG 1200×630 from kit.

## Week of launch (human)

1. Unzip handoff + scourge packs. `PYTHONPATH=. pytest` the grant/panel/expose tests.
2. rsync `website/` to the DigitalOcean vhost already on kraken.topta.co DNS.
3. Claim social names; post drafts from `docs/SOCIAL.md` only after a human click.
4. Create GitHub repo when the App can. Tag `v0.1.0-beta`.
5. Capacitor store build later; portal is enough for “advanced management” at ship.

## Money

Free forever: core + vanilla tentacles.  
Paid: Scourge seat / org key. No live Stripe from this tree.

Details: BUSINESS.md, SEO.md, SOCIAL.md, PROMPT_LAPTOP.md, WEBVIEW.md.
