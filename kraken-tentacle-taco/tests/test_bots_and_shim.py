#!/usr/bin/env python3
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bots.loopback import handle_body  # noqa: E402


def invoke(action, payload=None, env=None):
    run = os.environ.copy()
    run["KRAKEN_OFFLINE"] = "1"
    run["KRAKEN_LICENSE"] = (env or {}).get("KRAKEN_LICENSE") or "premium"
    if env:
        run.update(env)
    run.setdefault("KRAKEN_LICENSE", "premium")
    proc = subprocess.run(
        ["python3", str(ROOT / "handler.py")],
        input=json.dumps({"v": 1, "action": action, "payload": payload or {}}),
        text=True, capture_output=True, env=run, check=False,
    )
    return json.loads([ln for ln in proc.stdout.splitlines() if ln.startswith("{")][-1])


class BotsShim(unittest.TestCase):
    def setUp(self):
        self.env = {"KRAKEN_HOME": tempfile.mkdtemp()}

    def test_shim_after_install(self):
        proc = subprocess.run(
            ["python3", str(ROOT / "bin" / "kraken"), "taco", "after_install"],
            text=True, capture_output=True,
            env={**os.environ, "KRAKEN_HOME": self.env["KRAKEN_HOME"], "KRAKEN_LICENSE": "premium"},
        )
        self.assertEqual(proc.returncode, 0)
        body = json.loads([ln for ln in proc.stdout.splitlines() if ln.startswith("{")][-1])
        self.assertTrue(body["result"]["configured"])
        self.assertEqual(body["result"]["hook"], "after_install")

    def test_oauth_rejects_secret(self):
        b = invoke("oauth", {"vendor": "slack", "client_secret": "x"}, env=self.env)
        self.assertEqual(b["error"]["code"], "forbidden")

    def test_oauth_plan(self):
        b = invoke("oauth", {"vendor": "slack", "client_id": "W123"}, env=self.env)
        self.assertTrue(b["ok"])
        self.assertIn("slack.com", b["result"]["oauth"]["url"])

    def test_bare_taco_ignored(self):
        out = handle_body("slack", {"command": "/taco", "text": "@bev", "user_name": "ada"})
        self.assertFalse(out["ok"])

    def test_loopback_slack_map(self):
        out = handle_body("slack", {"command": "/kraken", "text": "taco bev", "user_name": "ada"})
        self.assertTrue(out["ok"])
        self.assertEqual(out["event"]["to"], "bev")


if __name__ == "__main__":
    unittest.main()
