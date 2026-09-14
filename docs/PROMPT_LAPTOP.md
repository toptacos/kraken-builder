# Optimized laptop prompt

Paste this after unzipping `kraken-handoff.zip` then `kraken-scourge-pack.zip` over the same tree.

---

You are implementing Kraken from this unzipped tree. Act as senior engineer + DevOps. Do not redesign the product.

Read first, in order:
docs/HANDOFF.md
docs/LEAN.md
docs/ARCHITECTURE.md
docs/INSTALL.md
docs/CUSTOM_TENTACLES.md
docs/SUCKERS.md
docs/EXPOSE.md
docs/SSL.md
docs/SCOPES.md
docs/GRANT.md
docs/PANEL.md
docs/SCOURGE.md
docs/DEPLOY_TOPTA.md
docs/SOCIAL.md
docs/COST_ESTIMATE.md
docs/CONTRACT.md
docs/SECURITY.md

Rules that do not change:
- Core is request → policy → exec → JSON response. No compilers, Docker engine, LLM weights, or CA inside core.
- Tentacles and suckers are separate binaries/folders. Suckers are named hooks.
- Bind 127.0.0.1 unless the operator set public:true on docker-env only.
- Default deny. Use `kraken grant <name>` before scourge/remote_config/tunnel/llm/expose.
- Do not live-charge Stripe. Do not claim SOC 2 certified.
- Do not create social accounts from a script. Draft posts only.
- GitHub create_repository may 403; if so, skip repo create and keep working locally.
- Prefer existing tentacles over new core modules.

Working directory: the unzipped kraken-builder root.
```
export PYTHONPATH=$PWD
python3 -m pytest tests/test_notes_tunnel_llm.py tests/test_expose.py tests/test_scopes_ca.py tests/test_panel.py tests/test_scourge_grant.py tests/test_suckers.py tests/test_site_e2e.py -q
python3 -m kraken init
python3 -m kraken vanilla
python3 -m kraken self plan
```

Then implement only what is still missing:

1. Platform icons (overwrite website/img/kit-2026 and website/img):
   - favicon.ico 32 and 16
   - apple-touch-icon 180
   - android/chrome 192 and 512
   - PWA maskable 512
   - OG 1200x630
   - X/Twitter card 1200x600
   - App Store 1024
   - Play Store 512
   - Windows tile 310
   - macOS icns source 1024 transparent
   - Linux 256 png
   Brand: ink #0B1220, teal #2FD0C6, foam #E7F6F6, gold #e7c56a. Mark is the tentacle-K. No extra mascot in icons.

2. DigitalOcean: rsync website/ to the kraken.topta.co vhost already on DNS. Do not move the CLI onto that box as the public site.

3. If third-party connectors work on this laptop (GitHub with Administration+Contents, Vercel team, Gmail, X):
   - create mmcachran/kraken-builder public if 403 is gone
   - push source without secrets or ~/.kraken/keys
   - Vercel preview of website/ only
   - do not post live social until a human approves drafts in docs/SOCIAL.md

4. Control plane on api.topta.co (Laravel/Postgres already used by topta):
   - POST /api/kraken/contact (from panel plan)
   - POST /api/kraken/licenses/verify and /issue
   - GET /api/kraken/devices scoped by org key
   Keep these out of the CLI binary.

5. Capacitor shell in apps/native: WebView → http://127.0.0.1:18181 from panel ui. No public bind.

Stop when tests pass and icons exist. Write a short TESTLOG line. Do not expand core.

---
