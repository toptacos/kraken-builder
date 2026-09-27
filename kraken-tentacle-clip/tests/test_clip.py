#!/usr/bin/env python3
import json, os, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FB = "https://www.facebook.com/share/r/1Bwr73ZXXL/?mibextid=wwXIfr"


def invoke(action, payload=None, env=None):
    run = os.environ.copy()
    run["KRAKEN_OFFLINE"] = "1"
    if env:
        run.update(env)
    proc = subprocess.run(
        ["python3", str(ROOT / "handler.py")],
        input=json.dumps({"v": 1, "action": action, "payload": payload or {}}),
        text=True, capture_output=True, env=run, check=False,
    )
    return json.loads([ln for ln in proc.stdout.splitlines() if ln.startswith("{")][-1])


class Clip(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.env = {"KRAKEN_HOME": self.home}

    def test_ping(self):
        b = invoke("ping", env=self.env)
        self.assertEqual(b["result"]["arm"], "clip")
        self.assertFalse(b["result"]["fetches"])

    def test_unknown(self):
        self.assertEqual(invoke("scrape", env=self.env)["error"]["code"], "unknown_action")

    def test_add_list_note(self):
        b = invoke("add", {"url": FB, "title": "reel share", "note": "could not view behind login"}, env=self.env)
        self.assertTrue(b["ok"])
        self.assertEqual(b["result"]["clip"]["host"], "www.facebook.com")
        self.assertFalse(b["result"]["clip"]["fetched"])
        listed = invoke("list", env=self.env)
        self.assertEqual(listed["result"]["count"], 1)
        noted = invoke("note", {"url": FB, "note": "user-supplied caption only"}, env=self.env)
        self.assertIn("user-supplied", noted["result"]["clip"]["note"])

    def test_reject_file_scheme(self):
        b = invoke("add", {"url": "file:///etc/passwd"}, env=self.env)
        self.assertFalse(b["ok"])

    def test_forbidden_dir(self):
        b = invoke("add", {"dir": str(Path(self.home) / ".kraken" / "keys"), "url": FB}, env=self.env)
        self.assertFalse(b["ok"])

    def test_finish(self):
        self.assertTrue(invoke("finish", {"raw": {"arm": "clip"}}, env=self.env)["result"]["finished"])


if __name__ == "__main__":
    unittest.main()
