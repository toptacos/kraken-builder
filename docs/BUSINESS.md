# Business next steps

Product: MIT core + free tentacles. Money: sync seats, premium tentacles, later hosted LLM.

## Site

Static `website/` → `kraken.topta.co` same pattern as `tacos.topta.co`. Login stays on `api.topta.co`.

## Paid

- License key in `~/.kraken/keys/licenses.json`
- Catalog row `license: premium`
- Do not turn on live Stripe from this tree

## Marketing (short)

- Promise: one command for scripts you already wrote
- Channels: X + README + courses shorts
- SEO: “local CLI plugin runner”, “multi language tentacles”, avoid “Kraken exchange”
- Social: 26s train-*.mp4 + tentacle-K stills in `website/img/kit-2026/`

## Install story

```
pipx install kraken-cli   # later
python3 -m kraken init && python3 -m kraken vanilla
```

Windows: same module path; binaries in `tentacle.yaml` `platforms:`.

## Surfaces

Native Capacitor shell **or** kraken.topta.co portal. Same grants and licenses. See docs/LAUNCH.md.

## Week one on the other laptop

1. Unzip, `export PYTHONPATH=$PWD`
2. `python3 -m pytest tests/test_notes_tunnel_llm.py tests/test_site_e2e.py -q`
3. Read `docs/HANDOFF.md` and implement the next tentacle you actually use daily
