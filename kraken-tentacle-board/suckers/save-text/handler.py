#!/usr/bin/env python3
import json, sys
from pathlib import Path


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "ping"
    ident = req.get("id")
    if action == "ping":
        json.dump({"v": 1, "id": ident, "ok": True, "result": {"arm": "save-text"}}, sys.stdout)
        sys.stdout.write("\n")
        return 0
    payload = req.get("payload") or {}
    raw = dict(payload.get("raw") or {})
    raw["sucker"] = "save-text"
    dest = Path(payload.get("out") or Path.home() / ".kraken" / "data" / "board" / "last.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    json.dump({"v": 1, "id": ident, "ok": True, "result": {"path": str(dest), "sucker": "save-text"}}, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
