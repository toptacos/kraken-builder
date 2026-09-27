#!/usr/bin/env python3
import json, os, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = (ROOT / "examples" / "project.yaml").read_text(encoding="utf-8")


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


class Berth(unittest.TestCase):
    def setUp(self):
        self.env = {"KRAKEN_HOME": tempfile.mkdtemp()}

    def test_ping_lists_functions(self):
        b = invoke("ping", env=self.env)
        self.assertTrue(b["ok"])
        self.assertEqual(b["result"]["arm"], "berth")
        self.assertIn("up", b["result"]["functions"])
        self.assertEqual(b["result"]["core_command"], "up")

    def test_plan_from_yaml(self):
        b = invoke("plan", {"yaml": SAMPLE}, env=self.env)
        self.assertTrue(b["ok"])
        self.assertEqual(b["result"]["network"]["name"], "kraken")
        self.assertIn("api", b["result"]["services"])
        self.assertIn("networks:", b["result"]["compose"])
        self.assertFalse(b["result"]["daemon"])

    def test_up_status_down(self):
        invoke("up", {"yaml": SAMPLE}, env=self.env)
        st = invoke("status", env=self.env)
        self.assertTrue(st["result"]["up"])
        self.assertTrue(st["result"]["compose_present"])
        down = invoke("down", env=self.env)
        self.assertTrue(down["result"]["down"])
        st2 = invoke("status", {"yaml": SAMPLE}, env=self.env)
        self.assertFalse(st2["result"]["up"])

    def test_hooks_and_third_party(self):
        invoke("up", {"yaml": SAMPLE}, env=self.env)
        h = invoke("hook", env=self.env)
        self.assertIn("after_up", h["result"]["hooks"])
        s = invoke("services", env=self.env)
        names = [x["name"] for x in s["result"]["third_party"]]
        self.assertIn("topta-api", names)

    def test_scrubs_finish(self):
        b = invoke("finish", {"raw": {"token": "x", "ok": True}}, env=self.env)
        self.assertEqual(b["result"]["token"], "redacted")

    def test_jail(self):
        home = Path(self.env["KRAKEN_HOME"])
        b = invoke("plan", {"dir": str(home / ".kraken" / "keys")}, env=self.env)
        self.assertFalse(b["ok"])

    def test_json_config(self):
        b = invoke("plan", {"config": {"name": "x", "services": {"a": {"image": "busybox"}}}}, env=self.env)
        self.assertEqual(b["result"]["project"], "x")
        self.assertIn("a", b["result"]["services"])


if __name__ == "__main__":
    unittest.main()
