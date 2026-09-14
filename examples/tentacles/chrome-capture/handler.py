#!/usr/bin/env python3
"""Premium tentacle. Live Chrome when KRAKEN_CHROME=1, else fixture."""

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[2] / "scripts" / "chrome"


def fixture(url: str) -> dict:
    return {
        "arm": "chrome-capture",
        "engine": "fixture",
        "url": url,
        "title": "Kraken CLI · One binary. Many tentacles.",
        "mit": True,
        "note": "Set KRAKEN_CHROME=1 and kraken license set chrome-capture KEY for live Chrome Default.",
    }


def live_probe(url: str) -> dict:
    js = (SCRIPTS / "inject.js").read_text(encoding="utf-8")
    applescript = str(SCRIPTS / "chrome-ops.applescript")
    proc = subprocess.run(
        ["osascript", applescript, url, js],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    raw = (proc.stdout or "").strip()
    try:
        probe = json.loads(raw)
    except json.JSONDecodeError:
        probe = {"raw": raw[:2000], "stderr": (proc.stderr or "")[:500]}
    probe["arm"] = "chrome-capture"
    probe["engine"] = "chrome-default"
    probe["url"] = url
    return probe


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    payload = req.get("payload") or {}
    url = str(payload.get("url") or "https://kraken.topta.co")
    action = req.get("action") or "probe"
    live = os.environ.get("KRAKEN_CHROME") == "1"
    if action == "capture" and live:
        subprocess.run(["sh", str(SCRIPTS / "capture.sh")], check=False, timeout=20)
    result = live_probe(url) if live else fixture(url)
    sys.stdout.write(
        json.dumps({"v": 1, "id": req.get("id"), "ok": True, "result": result})
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
