You are finishing Kraken from this unzipped tree. Senior engineer + DevOps. Do not redesign the product.

Read first:
data/
docs/ARCHIVE.md
docs/HANDOFF.md
docs/LEAN.md
docs/LAUNCH.md
docs/ARCHITECTURE.md
docs/GRANT.md
docs/SCOURGE.md
docs/PANEL.md
docs/WEBVIEW.md
docs/BRAND_GUIDELINES.md
docs/SEO_PLAYBOOK.md
docs/VIDEO_INDEX.md

Product (fixed):
- One lean CLI: JSON in → policy → exec → JSON out. No compilers, Docker engine, LLM weights, or CA in core.
- Two clients only: (1) Capacitor shell with bundled panel HTML on the same device as kraken; (2) portal https://kraken.topta.co/account.html via api.topta.co.
- No Flutter. No server.url in store builds. No phone WebView to a laptop’s 127.0.0.1.
- Tentacles/suckers stay separate. Suckers are named hooks.
- Bind 127.0.0.1 unless docker-env public:true.
- Default deny: kraken grant before scourge, remote_config, tunnel, llm, expose.
- MIT core + free tentacles. scourge is license: premium.
- No live Stripe. No “SOC 2 certified.” No scripted social signups.
- GitHub create may 403 — stay local and keep going.

cd <unzipped>/kraken-builder
export PYTHONPATH=$PWD
python3 -m pytest tests/test_notes_tunnel_llm.py tests/test_expose.py tests/test_scopes_ca.py tests/test_panel.py tests/test_scourge_grant.py tests/test_suckers.py -q
python3 -m kraken init && python3 -m kraken vanilla && python3 -m kraken self plan

Finish only what is still missing:
1. Platform icons from kit-2026/icon-1024 (16, 32, 180, 192, 512 maskable, 1024, OG 1200x630, X 1200x600, Win 310, Linux 256). Tentacle-K, ink #0B1220 teal #2FD0C6 foam #E7F6F6 gold #e7c56a.
2. rsync website/ to existing kraken.topta.co DigitalOcean vhost. CLI is not the public site. The site should fit the existing toptaco architecture and be tested end to end for functionality, performance, and security.
3. If connectors work: public repo mmcachran/kraken-builder (no keys), Vercel preview of website/ only. Social drafts stay in docs/SOCIAL.md until a human posts.
4. api.topta.co Laravel: POST /api/kraken/contact, licenses verify/issue, GET /api/kraken/devices by org key. Not in the CLI.
5. Capacitor: webDir = bundled panel. Live JSON optional from 127.0.0.1:18181 on the same device.
6. The ~/Projects/Companies/TopTaco directory should be scanned for how subsites are created for the Kraken branding website.
7. The main Kraken core, tentacles, and sucker repositories should be created in the Toptaco repository under the Kraken group and use best practices for releases, open source, testing, and open source project engagement. The paid or premium repositories should be created as private.

Stop when tests pass and icons exist. Append docs/TESTLOG.md. Do not expand core.