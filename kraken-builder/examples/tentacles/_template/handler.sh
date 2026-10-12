#!/bin/sh
set -eu
# `python3 - <<'PY'` would make the heredoc the script *and* stdin, so the
# request JSON on stdin could never be read. `python3 -c` keeps stdin for
# the envelope, which is the whole contract.
exec python3 -c '
import json, sys

req = json.loads(sys.stdin.read() or "{}")
sys.stdout.write(json.dumps({
    "v": 1,
    "id": req.get("id"),
    "ok": True,
    "result": {"arm": "hello", "action": req.get("action") or "ping"},
}))
'
