#!/bin/sh
set -eu
python3 - <<'PY'
import json, sys
req = json.loads(sys.stdin.read() or "{}")
sys.stdout.write(json.dumps({
    "v": 1,
    "id": req.get("id"),
    "ok": True,
    "result": {"arm": "hello", "action": req.get("action") or "ping"},
}))
PY
