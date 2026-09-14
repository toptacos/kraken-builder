#!/usr/bin/env python3
"""Local panel for the Capacitor shell. Bind 127.0.0.1 only."""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

CONTACT = "https://api.topta.co/api/kraken/contact"


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result}))
    return 0


def _home() -> Path:
    return Path(os.environ.get("KRAKEN_HOME", str(Path.home()))) / ".kraken"


def _resources() -> dict:
    mem = {}
    mi = Path("/proc/meminfo")
    if mi.exists():
        data = {}
        for line in mi.read_text().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                data[k] = v.strip()
        mem = {
            "mem_total": data.get("MemTotal"),
            "mem_available": data.get("MemAvailable"),
        }
    disk = shutil.disk_usage(str(_home().anchor or "/"))
    return {
        "cpu_count": os.cpu_count(),
        "load": os.getloadavg() if hasattr(os, "getloadavg") else None,
        "disk_total": disk.total,
        "disk_used": disk.used,
        "disk_free": disk.free,
        **mem,
        "pid": os.getpid(),
    }


def _paths() -> dict:
    h = _home()
    return {
        "KRAKEN_HOME": str(h.parent if h.name == ".kraken" else h),
        "config": str(h / "config.yaml"),
        "data": str(h / "data"),
        "keys": str(h / "keys"),
        "tentacles": str(h / "tentacles"),
        "logs": str(h / "logs"),
        "scopes": str(h / "keys" / "scopes.json"),
        "ca": str(h / "data" / "ca"),
    }


def _ui_html(bind: str) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kraken panel</title>
<style>
body{{margin:0;font:16px/1.4 system-ui;background:#0B1220;color:#E7F6F6}}
main{{max-width:40rem;margin:2rem auto;padding:1rem}}
h1{{color:#2FD0C6}} pre{{background:#111827;padding:1rem;overflow:auto}}
button,input,textarea{{font:inherit;width:100%;margin:.3rem 0;padding:.4rem}}
</style></head>
<body><main>
<h1>Kraken panel</h1>
<p>Local only · {bind}</p>
<pre id="status">loading…</pre>
<form id="c">
<input name="email" placeholder="email" required>
<textarea name="body" placeholder="message" rows="4"></textarea>
<button type="submit">Plan contact to api.topta.co</button>
</form>
<pre id="out"></pre>
<script>
const payload = {{}};
fetch("/").catch(()=>{{}});
document.getElementById("status").textContent = JSON.stringify({json.dumps({"bind": bind})}, null, 2);
document.getElementById("c").onsubmit = (e) => {{
  e.preventDefault();
  document.getElementById("out").textContent = "Use: kraken run panel contact --payload ...";
}};
</script>
</main></body></html>
"""


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "status"
    p = req.get("payload") or {}
    bind = str(p.get("bind") or "127.0.0.1:18181")
    if not bind.startswith("127.0.0.1"):
        bind = "127.0.0.1:18181"

    if action == "paths":
        return _ok(req, {"paths": _paths()})

    if action == "status":
        return _ok(req, {"paths": _paths(), "resources": _resources(), "bind": bind})

    if action == "ui":
        dest = _home() / "data" / "panel" / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(_ui_html(bind))
        return _ok(req, {"path": str(dest), "bind": bind, "serve": f"python3 -m http.server --bind 127.0.0.1 {bind.split(':')[-1]}"})

    if action == "contact":
        email = str(p.get("email") or "")
        body = str(p.get("body") or "")
        if not email or "@" not in email:
            return _ok(req, {"error": "email required"}, ok=False)
        plan = {
            "method": "POST",
            "url": CONTACT,
            "json": {
                "email": email,
                "body": body[:4000],
                "scope": p.get("scope") or "global",
                "source": "panel",
            },
            "sent": False,
            "note": "CLI does not POST unless KRAKEN_CONTACT_SEND=1. Capacitor shell may POST after login.",
        }
        if os.environ.get("KRAKEN_CONTACT_SEND") == "1":
            plan["sent"] = False
            plan["skipped"] = "live POST disabled in this tree"
        return _ok(req, plan)

    return _ok(req, {"error": f"unknown action {action}"}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
