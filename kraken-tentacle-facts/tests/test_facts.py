#!/usr/bin/env python3
import json, subprocess, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def invoke(action, payload=None):
    proc = subprocess.run(["bash", str(ROOT / "handler.sh")],
        input=json.dumps({"v": 1, "action": action, "payload": payload or {}}),
        text=True, capture_output=True, check=False)
    return json.loads([ln for ln in proc.stdout.splitlines() if ln.startswith("{")][-1])

class Facts(unittest.TestCase):
    def test_ping(self):
        b = invoke("ping")
        self.assertEqual(b["result"]["runtime"], "bash")
    def test_unknown(self):
        self.assertEqual(invoke("nope")["error"]["code"], "unknown_action")
    def test_host_snapshot(self):
        h = invoke("host")
        self.assertIn("hostname", h["result"])
        s = invoke("snapshot")
        self.assertEqual(s["result"]["arm"], "facts")
    def test_finish(self):
        self.assertTrue(invoke("finish")["result"]["finished"])

if __name__ == "__main__":
    unittest.main()
