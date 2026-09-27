#!/usr/bin/env python3
import json, os, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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


class Inlet(unittest.TestCase):
    def setUp(self):
        self.env = {"KRAKEN_HOME": tempfile.mkdtemp()}

    def test_ping(self):
        b = invoke("ping", env=self.env)
        self.assertEqual(b["result"]["arm"], "inlet")
        self.assertEqual(b["result"]["brand"], "TopTaco")
        self.assertFalse(b["result"]["shell"])
        self.assertEqual(b["result"]["bind"], "127.0.0.1")

    def test_unknown(self):
        self.assertEqual(invoke("shell", env=self.env)["error"]["code"], "unknown_action")

    def test_grant_list_hides_token(self):
        g = invoke("grant", {"name": "laptop"}, env=self.env)
        self.assertIn("token", g["result"]["device"])
        listed = invoke("devices", env=self.env)
        self.assertEqual(listed["result"]["count"], 1)
        self.assertNotIn("token", listed["result"]["devices"][0])

    def test_listen_requires_loopback(self):
        b = invoke("listen", {"bind": "0.0.0.0"}, env=self.env)
        self.assertEqual(b["error"]["code"], "forbidden")

    def test_tunnel_needs_device(self):
        b = invoke("listen", {"tunnel": True}, env=self.env)
        self.assertIn(b["error"]["code"], ("need_bin", "no_device"))

    def test_status_no_topta_control(self):
        s = invoke("status", env=self.env)
        self.assertFalse(s["result"]["topta_register"])
        self.assertFalse(s["result"]["shell"])

    def test_finish_strips_token(self):
        b = invoke("finish", {"raw": {"token": "secret", "arm": "inlet"}}, env=self.env)
        self.assertNotIn("token", b["result"])

    def test_forbid_keys(self):
        home = Path(self.env["KRAKEN_HOME"])
        b = invoke("devices", {"dir": str(home / ".kraken" / "keys")}, env=self.env)
        self.assertFalse(b["ok"])


if __name__ == "__main__":
    unittest.main()
