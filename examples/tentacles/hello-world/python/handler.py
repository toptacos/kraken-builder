#!/usr/bin/env python3
import json, sys

req = json.loads(sys.stdin.read() or "{}")
name = (req.get("payload") or {}).get("name", "world")
sys.stdout.write(json.dumps({
    "v": 1, "id": req.get("id"), "ok": True,
    "result": {"arm": "hello-py", "lang": "python", "hello": f"hello, {name}"},
}))
