# Handoff prompt (read this on the other computer)

Copy into the next Grok/Cursor session:

```
You are implementing Kraken from this unzipped tree.
Read docs/wiki/Home.md, docs/PLUGINS.md, docs/CONTRACT.md, docs/SECURITY.md,
docs/SOC2.md, docs/BUSINESS.md, docs/USERNS.md, docs/DEVICE_GROUP.md,
examples/config/user.config.yaml.
Do not call live Stripe. Do not publish Docker ports off 127.0.0.1.
Run: PYTHONPATH=. python3 -m pytest tests/test_notes_tunnel_llm.py
tests/test_runtime.py tests/test_sync.py tests/test_site_e2e.py -q
Then python3 -m kraken init && python3 -m kraken vanilla
Serve website/ on :8080 if you need to restyle kraken.topta.co.
Add tentacles as folders with tentacle.yaml + handler; never import kraken.core
from a tentacle. Notes, tunnel, and llm already exist under examples/tentacles/.
```
