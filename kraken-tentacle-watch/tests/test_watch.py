#!/usr/bin/env python3
"""watch contract tests. Offline, temp KRAKEN_HOME, no live browser.

The Go binary and the Python fallback must speak the same envelope, so every
case here runs against whichever runtime `handler.sh` dispatches to.
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def invoke(action, payload=None, env=None, raw=None):
    run = os.environ.copy()
    run["KRAKEN_OFFLINE"] = "1"
    run.pop("KRAKEN_WATCH_LIVE", None)
    if env:
        run.update(env)
    body = (
        raw
        if raw is not None
        else json.dumps(
            {"v": 1, "id": None, "action": action, "payload": payload or {}}
        )
    )
    proc = subprocess.run(
        ["sh", str(ROOT / "handler.sh")],
        input=body,
        text=True,
        capture_output=True,
        env=run,
        check=False,
    )
    lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("{")]
    if not lines:
        raise AssertionError(
            f"no JSON on stdout: rc={proc.returncode} err={proc.stderr[:400]}"
        )
    return json.loads(lines[-1])


class Watch(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.env = {"KRAKEN_HOME": self.home}
        self.store = Path(self.home) / ".kraken" / "data" / "watch"

    def call(self, action, payload=None, **kw):
        kw.setdefault("env", self.env)
        return invoke(action, payload, **kw)

    # --- envelope ---------------------------------------------------------

    def test_ping(self):
        r = self.call("ping")
        self.assertTrue(r["ok"])
        self.assertEqual(r["v"], 1)
        self.assertEqual(r["result"]["arm"], "watch")
        self.assertEqual(r["result"]["protocol"], 1)
        self.assertIn("engine", r["result"])
        self.assertIn("platform", r["result"])

    def test_empty_stdin_is_ping(self):
        r = invoke(None, env=self.env, raw="")
        self.assertTrue(r["ok"])
        self.assertEqual(r["result"]["arm"], "watch")

    def test_error_envelope_shape(self):
        r = self.call("definitely-not-an-action")
        self.assertFalse(r["ok"])
        self.assertEqual(set(r["error"]), {"code", "message"})
        self.assertNotIn("result", r)

    def test_malformed_stdin_is_an_envelope_not_a_crash(self):
        for raw in ("{not json", "[]", '"a string"', "null"):
            r = invoke(None, env=self.env, raw=raw)
            self.assertFalse(r["ok"], raw)
            self.assertIn(r["error"]["code"], ("bad_json",), raw)

    # --- plan is not a build ----------------------------------------------

    def test_plan_points_at_config_without_building(self):
        r = self.call("plan", {"name": "ci"})
        self.assertTrue(r["ok"])
        self.assertIn("ci.json", r["result"]["config_path"])
        self.assertIn("hint", r["result"])

    def test_build_is_dry_run_without_toolchain(self):
        """No daemon, no surprise network fetch, no implicit compile."""
        r = self.call("build")
        self.assertTrue(r["ok"])
        self.assertIn("mode", r["result"])

    # --- browse stays a fixture unless opted in ---------------------------

    def test_browse_is_fixture_by_default(self):
        r = self.call("browse", {"url": "https://kraken.topta.co"})
        self.assertTrue(r["ok"])
        self.assertEqual(r["result"]["engine"], "fixture")
        self.assertFalse(r["result"]["live"])
        self.assertIn("hash", r["result"])

    def test_browse_fixture_hash_is_deterministic(self):
        a = self.call("browse", {"url": "https://kraken.topta.co"})["result"]["hash"]
        b = self.call("browse", {"url": "https://kraken.topta.co"})["result"]["hash"]
        self.assertEqual(a, b)

    def test_browse_default_url_is_kraken(self):
        r = self.call("browse")
        self.assertEqual(r["result"]["url"], "https://kraken.topta.co")

    # --- capture writes under the jail ------------------------------------

    def test_capture_writes_into_data_dir(self):
        r = self.call("capture")
        self.assertTrue(r["ok"])
        path = Path(r["result"]["path"])
        self.assertTrue(path.is_file())
        self.assertTrue(str(path).startswith(str(self.store)))

    # --- notify is local only ---------------------------------------------

    def test_notify_is_local(self):
        r = self.call("notify", {"summary": "tick"})
        self.assertTrue(r["ok"])
        channels = {n["channel"] for n in r["result"]["notify"]}
        self.assertIn("stdout", channels)

    def test_notify_does_not_call_out(self):
        r = self.call("notify", {"summary": "tick"})
        blob = json.dumps(r)
        self.assertNotIn("webhook", blob)
        self.assertNotIn("ntfy", blob)

    # --- snapshot ----------------------------------------------------------

    def test_snapshot(self):
        r = self.call("snapshot")
        self.assertTrue(r["ok"])
        snap = r["result"]["snapshot"]
        for key in ("hostname", "os", "arch"):
            self.assertIn(key, snap)

    # --- task state machine ------------------------------------------------

    def test_task_actions_persist_state(self):
        for action in ("add", "tick", "start", "list", "task", "apply", "status"):
            r = self.call(action, {"name": "nightly"})
            self.assertTrue(r["ok"], action)
        state = json.loads((self.store / "nightly.state.json").read_text())
        self.assertEqual(state["name"], "nightly")
        self.assertIn("last", state)

    def test_task_names_are_isolated(self):
        self.call("add", {"name": "alpha"})
        self.call("add", {"name": "beta"})
        self.assertTrue((self.store / "alpha.state.json").is_file())
        self.assertTrue((self.store / "beta.state.json").is_file())

    def test_clear_removes_state(self):
        self.call("add", {"name": "temp"})
        self.assertTrue((self.store / "temp.state.json").is_file())
        self.assertTrue(self.call("clear", {"name": "temp"})["ok"])
        self.assertFalse((self.store / "temp.state.json").exists())

    def test_remove_then_list_does_not_crash(self):
        self.call("remove", {"name": "ghost"})
        self.assertTrue(self.call("list", {"name": "ghost"})["ok"])

    # --- finish ------------------------------------------------------------

    def test_finish_merges_patch(self):
        r = self.call("finish", {"raw": {"arm": "watch", "a": 1}, "patch": {"b": 2}})
        self.assertTrue(r["ok"])
        self.assertTrue(r["result"]["finished"])
        self.assertEqual(r["result"]["a"], 1)
        self.assertEqual(r["result"]["b"], 2)
        self.assertEqual(r["result"]["arm"], "watch")

    def test_finish_tolerates_missing_raw(self):
        r = self.call("finish", {})
        self.assertTrue(r["ok"])
        self.assertEqual(r["result"]["arm"], "watch")

    # --- no secrets on disk in the envelope --------------------------------

    def test_state_file_holds_no_credentials(self):
        env = {**self.env, "KRAKEN_TOKEN": "sk-should-not-persist"}
        self.call("add", {"name": "x"}, env=env)
        blob = (self.store / "x.state.json").read_text()
        self.assertNotIn("sk-should-not-persist", blob)


if __name__ == "__main__":
    unittest.main()
