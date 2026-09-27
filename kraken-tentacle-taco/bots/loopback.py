#!/usr/bin/env python3
"""Loopback slash-command receiver. Bind 127.0.0.1 only. No public tunnel."""
from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from connectors import parse as parse_channel  # noqa: E402


def handle_body(channel: str, body: dict) -> dict:
    mapped = parse_channel(channel, body)
    if not mapped:
        return {"ok": False, "error": "unmapped"}
    return {"ok": True, "event": mapped}


class Handler(BaseHTTPRequestHandler):
    channel = "slack"

    def log_message(self, fmt, *args):
        return

    def do_POST(self):
        host = (self.headers.get("Host") or "").split(":")[0]
        if host not in {"127.0.0.1", "localhost"}:
            self.send_error(403)
            return
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n).decode("utf-8") if n else ""
        ctype = self.headers.get("Content-Type") or ""
        if "json" in ctype:
            body = json.loads(raw or "{}")
        else:
            body = {k: v[0] for k, v in parse_qs(raw).items()}
        result = handle_body(self.channel, body)
        data = json.dumps(result).encode()
        self.send_response(200 if result.get("ok") else 422)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def serve(channel: str, port: int) -> None:
    Handler.channel = channel
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    httpd.serve_forever()


if __name__ == "__main__":
    ch = sys.argv[1] if len(sys.argv) > 1 else "slack"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 7421
    serve(ch, port)
