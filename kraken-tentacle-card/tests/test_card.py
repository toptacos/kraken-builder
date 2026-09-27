#!/usr/bin/env python3
import json, subprocess, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def invoke(action, payload=None):
    proc = subprocess.run(["sh", str(ROOT / "handler.sh")],
        input=json.dumps({"v": 1, "action": action, "payload": payload or {}}),
        text=True, capture_output=True, check=False)
    lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("{")]
    if not lines:
        raise AssertionError(proc.stderr or proc.stdout)
    return json.loads(lines[-1])

class Card(unittest.TestCase):
    def test_ping(self):
        b = invoke("ping")
        self.assertTrue(b["ok"])
        self.assertEqual(b["result"]["runtime"], "php")
    def test_unknown(self):
        b = invoke("nope")
        self.assertEqual(b["error"]["code"], "unknown_action")
    def test_render_escapes(self):
        b = invoke("render", {"title": "<x>", "body": "a & b"})
        self.assertIn("&lt;x&gt;", b["result"]["html"])
        self.assertIn("&amp;", b["result"]["html"])
    def test_finish(self):
        b = invoke("finish", {"raw": {"arm": "card"}, "patch": {"n": 1}})
        self.assertTrue(b["result"]["finished"])

if __name__ == "__main__":
    unittest.main()
