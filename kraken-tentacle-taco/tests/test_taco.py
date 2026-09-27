#!/usr/bin/env python3
import json, os, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def invoke(action, payload=None, env=None):
    run = os.environ.copy()
    run["KRAKEN_OFFLINE"] = "1"
    run.setdefault("KRAKEN_LICENSE", "premium")
    if env:
        run.update(env)
    run.setdefault("KRAKEN_LICENSE", "premium")
    proc = subprocess.run(
        ["python3", str(ROOT / "handler.py")],
        input=json.dumps({"v": 1, "action": action, "payload": payload or {}}),
        text=True, capture_output=True, env=run, check=False,
    )
    return json.loads([ln for ln in proc.stdout.splitlines() if ln.startswith("{")][-1])


class Taco(unittest.TestCase):
    def setUp(self):
        self.env = {"KRAKEN_HOME": tempfile.mkdtemp()}

    def test_ping_premium(self):
        b = invoke("ping", env=self.env)
        self.assertEqual(b["result"]["arm"], "taco")
        self.assertEqual(b["result"]["license"], "premium")
        self.assertEqual(b["result"]["brand"], "TopTaco")
        self.assertEqual(b["result"]["site"], "https://kraken.topta.co")
        self.assertEqual(b["result"]["api"], "https://api.topta.co")
        self.assertFalse(b["result"]["pulls_vendors"])

    def test_help(self):
        h = invoke("help", env=self.env)
        self.assertIn("give", h["result"]["commands"])

    def test_redacts_secret_note(self):
        b = invoke("event", {"user": "ada", "kind": "custom", "tacos": 0, "note": "token=sk-live-secret"}, env=self.env)
        self.assertEqual(b["result"]["event"]["note"], "redacted")

    def test_unlicensed_give(self):
        env = {"KRAKEN_HOME": self.env["KRAKEN_HOME"], "KRAKEN_LICENSE": ""}
        # invoke() forces premium; call handler raw
        import subprocess
        proc = subprocess.run(
            ["python3", str(ROOT / "handler.py")],
            input='{"v":1,"action":"give","payload":{"from":"a","to":"b"}}',
            text=True, capture_output=True,
            env={**os.environ, "KRAKEN_HOME": self.env["KRAKEN_HOME"], "KRAKEN_LICENSE": "free"},
        )
        body = json.loads([ln for ln in proc.stdout.splitlines() if ln.startswith("{")][-1])
        self.assertEqual(body["error"]["code"], "payment_required")

    def test_unknown(self):
        self.assertEqual(invoke("stripe", env=self.env)["error"]["code"], "unknown_action")

    def test_pr_and_score(self):
        invoke("event", {"user": "ada", "kind": "pr"}, env=self.env)
        s = invoke("score", {"user": "ada"}, env=self.env)
        self.assertEqual(s["result"]["user"]["tacos"], 3)

    def test_give_and_cap(self):
        invoke("set-policy", {"policy": {"peer_cap_per_day": 1}}, env=self.env)
        g = invoke("give", {"from": "ada", "to": "bev"}, env=self.env)
        self.assertTrue(g["ok"])
        cap = invoke("give", {"from": "ada", "to": "bev"}, env=self.env)
        self.assertEqual(cap["error"]["code"], "cap")
        self.assertEqual(invoke("give", {"from": "ada", "to": "ada"}, env=self.env)["error"]["code"], "bad_give")

    def test_redeem(self):
        invoke("event", {"user": "ada", "kind": "security"}, env=self.env)
        invoke("event", {"user": "ada", "kind": "security"}, env=self.env)
        r = invoke("redeem", {"user": "ada", "id": "sticker"}, env=self.env)
        self.assertTrue(r["ok"])
        self.assertEqual(r["result"]["balance"], 6)

    def test_ingest_github_pr(self):
        body = {
            "action": "closed",
            "pull_request": {"merged": True, "user": {"login": "ada"}, "html_url": "https://example.com/p/1"},
        }
        b = invoke("ingest", {"channel": "github", "payload": body}, env=self.env)
        self.assertTrue(b["ok"], b)
        self.assertEqual(b["result"]["event"]["kind"], "pr")
        self.assertEqual(invoke("score", {"user": "ada"}, env=self.env)["result"]["user"]["tacos"], 3)

    def test_ingest_gchat_give(self):
        body = {"message": {"text": "kraken taco bev", "sender": {"displayName": "ada"}}}
        b = invoke("ingest", {"channel": "gchat", "payload": body}, env=self.env)
        self.assertTrue(b["ok"], b)
        self.assertEqual(invoke("score", {"user": "bev"}, env=self.env)["result"]["user"]["tacos"], 1)

    def test_init_prompts_then_answers(self):
        q = invoke("init", env=self.env)
        self.assertTrue(q["result"]["interactive"])
        self.assertTrue(q["result"]["prompts"])
        a = invoke("init", {"answers": {"org": "reef", "peer_cap_per_day": 2, "channels": "slack,teams"}}, env=self.env)
        self.assertTrue(a["result"]["configured"])
        self.assertEqual(a["result"]["policy"]["org"], "reef")

    def test_after_install_defaults(self):
        b = invoke("after_install", {"defaults": True}, env=self.env)
        self.assertTrue(b["result"]["configured"])

    def test_ingest_slack(self):
        b = invoke("ingest", {"channel": "slack", "payload": {"command": "/kraken", "text": "taco bev", "user_name": "ada"}}, env=self.env)
        self.assertTrue(b["ok"], b)

    def test_ingest_unknown_channel(self):
        self.assertEqual(
            invoke("ingest", {"channel": "stripe", "payload": {}}, env=self.env)["error"]["code"],
            "unmapped",
        )

    def test_per_hour_limit(self):
        invoke("set-policy", {"policy": {"peer_cap_per_day": 99, "limits": {"taco": {"per_hour": 1, "per_day": 99}}}}, env=self.env)
        self.assertTrue(invoke("give", {"from": "ada", "to": "bev"}, env=self.env)["ok"])
        again = invoke("give", {"from": "ada", "to": "cam"}, env=self.env)
        self.assertEqual(again["error"]["code"], "cap")
        self.assertEqual(again["error"]["message"], "per_hour")

    def test_custom_kind_rule(self):
        invoke("set-policy", {"policy": {"rules": [{"id": "kinds", "type": "allow_kinds", "kinds": ["taco"]}]}}, env=self.env)
        b = invoke("event", {"user": "ada", "kind": "pr"}, env=self.env)
        self.assertEqual(b["error"]["code"], "cap")
        self.assertEqual(b["error"]["message"], "kind_denied")

    def test_host_modes(self):
        local = invoke("host", {"mode": "local"}, env=self.env)
        self.assertEqual(local["result"]["hosting"]["mode"], "local")
        bad = invoke("host", {"mode": "third", "url": "http://insecure"}, env=self.env)
        self.assertEqual(bad["error"]["code"], "bad_host")
        cloud = invoke("host", {"mode": "toptaco"}, env=self.env)
        self.assertEqual(cloud["result"]["hosting"]["mode"], "toptaco")
        self.assertFalse(cloud["result"]["pushed"])

    def test_finish_and_jail(self):
        self.assertNotIn("token", invoke("finish", {"raw": {"token": "x"}}, env=self.env)["result"])
        home = Path(self.env["KRAKEN_HOME"])
        self.assertFalse(invoke("score", {"dir": str(home / ".kraken" / "keys")}, env=self.env)["ok"])


if __name__ == "__main__":
    unittest.main()
