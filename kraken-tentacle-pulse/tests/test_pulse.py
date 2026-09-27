#!/usr/bin/env python3
import json, subprocess, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def invoke(action, payload=None):
    proc = subprocess.run(["sh", str(ROOT / "handler.sh")],
        input=json.dumps({"v": 1, "action": action, "payload": payload or {}}),
        text=True, capture_output=True, check=False)
    return json.loads([ln for ln in proc.stdout.splitlines() if ln.startswith("{")][-1])

class Pulse(unittest.TestCase):
    def test_ping(self):
        b = invoke("ping")
        self.assertEqual(b["result"]["runtime"], "javascript")
    def test_unknown(self):
        self.assertEqual(invoke("nope")["error"]["code"], "unknown_action")
    def test_check_valid(self):
        b = invoke("check", {"envelope": {"v": 1, "ok": True, "result": {}}})
        self.assertTrue(b["result"]["valid"])
    def test_check_invalid(self):
        b = invoke("check", {"envelope": {"ok": True}})
        self.assertFalse(b["result"]["valid"])
    def test_wrap_finish(self):
        self.assertEqual(invoke("wrap", {"note": "n"})["result"]["note"], "n")
        self.assertTrue(invoke("finish")["result"]["finished"])

if __name__ == "__main__":
    unittest.main()
