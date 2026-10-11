# Offline first, grants before exposure

*Kraken's posture: it works with the network cable cut, it degrades instead
of crashing, and the one class of action that can reach a network is refused
until a human grants it. Every command on this page was executed by
`scripts/verify_articles.py` on a machine with no internet at all.*

## What "offline first" buys

Two different guarantees, often confused:

1. **No phone-home.** The CLI makes no outbound request on a normal run.
   Telemetry is off by default (`KRAKEN_OFFLINE=1`), and the only code that
   can talk to a server is license verification, which a user initiates.
2. **No hard dependency on the network.** A tentacle can still answer when
   its API is unreachable — from a fixture, marked as such.

We will prove both below, with the network genuinely absent: this page was
generated on a disconnected machine.

## Proof 1 — the first-run experience works with no network

Fresh home, nothing installed:

```run,sh
python3 -m kraken vanilla >/dev/null
python3 -m kraken demo
```

```output
{"v": 1, "id": "1", "ok": true, "result": {"arm": "geo", "zip": "00000", "city": "Los Angeles", "lat": 34.05, "lon": -118.24, "ip": "1.1.1.1"}}
  Tests skipped: no tests/ directory
  Tests skipped: no tests/ directory
  Tests skipped: no tests/ directory
  Tests skipped: no tests/ directory
  Tests skipped: no tests/ directory
  Tests skipped: no tests/ directory
  Tests skipped: no tests/ directory
  Tests skipped: no tests/ directory
```

`demo` is the "first JSON in 60 seconds" path. It succeeded with no DNS, no
route, nothing — because the bundled tentacles answer from local data. The
`ip: "1.1.1.1"` in the payload is an argument, not a request.

## The fixture pattern

A tentacle that calls an API should decide what happens when the API does
not answer. The pattern this repo's own tentacles use (`wx`, `openmeteo`)
is: try the network, fall back to a fixture, and **say which one answered**.
Write it:

```run,sh
mkdir -p weather
cat > weather/tentacle.yaml <<'EOF'
name: weather
version: 0.1.0
license: free
runtime: binary
binary: handler.py
actions: [now]
description: A tentacle that says where its answer came from.
EOF

cat > weather/handler.py <<'EOF'
import json
import os
import sys

req = json.load(sys.stdin)
payload = req.get("payload") or {}

# Fixture first by default, so the answer is reproducible anywhere. A real
# tentacle inverts this: live first, fixture as the fallback, and the
# "source" field tells the caller which one it got.
if os.environ.get("WEATHER_LIVE") == "1":
    try:
        import urllib.request

        with urllib.request.urlopen(
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=52.5&lon=13.4&current_weather=true",
            timeout=5,
        ) as resp:
            data = json.loads(resp.read().decode())
        result = {
            "source": "live",
            "temperature_c": data["current_weather"]["temperature"],
        }
    except Exception:
        result = None
else:
    result = None

if result is None:
    result = {"source": "fixture", "temperature_c": 20.0}

sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": True, "result": result}))
EOF

python3 -m kraken tentacle add weather >/dev/null && echo "installed weather"
```

```output
installed weather
  Tests skipped: no tests/ directory
```

Run it. The machine running this page has no network, so the fallback
branch is what you see — and note it says `fixture` rather than failing:

```run,sh
python3 -m kraken run weather now
```

```output
{"v": 1, "id": "1", "ok": true, "result": {"source": "fixture", "temperature_c": 20.0}}
```

The contract's rule does the rest of the work: a network failure is *data*,
not a crash. An unreachable API and a refused action both answer with
`"ok": false` or a marked fallback and **exit 0** — a caller can always tell
the difference between "no answer" and "the tentacle broke".

## Proof 2 — nothing leaves the box

The claim is checkable, so check it. Which modules in core even import an
HTTP client, and what do they talk to?

```run,sh
cd "$KRAKEN_REPO_ROOT"
# Parse instead of grep: a comment mentioning urllib is not a phone-home.
python3 - <<'EOF'
import ast
import pathlib

for f in sorted(pathlib.Path("kraken").rglob("*.py")):
    tree = ast.parse(f.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "urllib" in node.module:
            print(f"{f}:{node.lineno}: from {node.module} import ...")
        elif isinstance(node, ast.Import):
            for a in node.names:
                if "urllib" in a.name:
                    print(f"{f}:{node.lineno}: import {a.name}")
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                if "urllib" in (a.name or ""):
                    print(f"{f}:{node.lineno}: from {node.module} import {a.name}")
EOF
echo "---"
grep -rn "topta.co" kraken/core/license.py kraken/core/sync.py | head -4
```

```output
kraken/core/license.py:69: import urllib.error
kraken/core/license.py:70: import urllib.request
kraken/core/license.py:139: import urllib.error
kraken/core/license.py:140: import urllib.request
kraken/core/network.py:16: import urllib.request
kraken/core/notify.py:17: import urllib.request
kraken/core/notify.py:36: import urllib.request
kraken/core/sync.py:22: from urllib import ...
---
kraken/core/license.py:5:Default api_base: https://api.topta.co
kraken/core/license.py:17:DEFAULT_API = "https://api.topta.co"
kraken/core/license.py:166:                f"Seats: https://kraken.topta.co/pricing"
kraken/core/sync.py:1:"""Local session + optional api.topta.co account. No push vendor in core.
```

Read that list: `notify` (your webhook, only if you set
`KRAKEN_NOTIFY_WEBHOOK`), `network` and `sync` (only when a user asks for a
remote session), and `license`/`billing` (only on `kraken license verify`).
None of them run during `kraken run` unless you point them at a URL. And on
the tentacle side, the `keeps` tentacle — the one that handles bookmarks and
secrets — refuses to even *store* anything under a path containing
`topta.co`, `keys/`, or `licenses.json`.

## Proof 3 — exposure is refused before it is granted

The other half of the posture: anything that can expose a port is
default-deny. Install the tentacle that plans an expose and ask for a plan:

```run,sh
python3 -m kraken tentacle add "$KRAKEN_REPO_ROOT/examples/tentacles/expose" >/dev/null
python3 -m kraken run expose plan --payload '{"host":"panel.kraken.localhost"}'
```

```output
{"v": 1, "id": "1", "ok": false, "result": {"error": "grant expose first: kraken grant expose"}}
  Tests skipped: no tests/ directory
```

That is a refusal, not an error: `"ok": false`, the exact command to fix it,
and exit 0. Grant it, and the same command answers with a plan — note what
it is willing to bind:

```run,sh
python3 -m kraken grant expose >/dev/null
python3 -m kraken run expose plan --payload '{"host":"panel.kraken.localhost"}'
```

```output
{"v": 1, "id": "1", "ok": true, "result": {"host": "panel.kraken.localhost", "bind": "127.0.0.1:18181", "public": false, "argv": ["python3", "-m", "http.server", "--bind", "127.0.0.1", "18181"], "note": "Loopback only. Pair with ca for HTTPS. Not 0.0.0.0."}}
```

`127.0.0.1:18181` — loopback, with a note that says so. `public: true` or a
`0.0.0.0` bind is a separate, explicit decision this tentacle does not make
for you (see `docs/GRANT.md`).

## The posture, stated once

- No tentacle calls home unless you aim it at a URL.
- No run fails because the network did.
- No port opens until a grant exists, and the grant is one line in a config
  file you can read and delete.

Verified by `scripts/verify_articles.py`, on a machine with no network, in
an isolated `KRAKEN_HOME` with `KRAKEN_OFFLINE=1`.
