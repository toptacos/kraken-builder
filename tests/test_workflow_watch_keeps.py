#!/usr/bin/env python3
"""The cross-arm story: watch ticks, keeps lists names, notify stays local.

Also runs the story through the real core workflow runner so the yaml is
proven loadable, not just greppable.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / "workflows" / "watch-keeps-notify.yaml"
KEEPS = ROOT / "kraken-tentacle-keeps" / "handler.sh"

sys.path.insert(0, str(ROOT / "kraken-builder"))


class Workflow(unittest.TestCase):
    def test_story_names(self):
        text = WF.read_text(encoding="utf-8")
        for needle in (
            "tentacle: watch",
            "tentacle: keeps",
            "tentacle: ledger",
            "channel: local",
        ):
            self.assertIn(needle, text)

    def test_story_never_calls_the_hub(self):
        """Local-first. This story must not reach api.topta.co."""
        text = WF.read_text(encoding="utf-8")
        self.assertNotIn("api.topta.co", text)

    def test_story_declares_its_steps_in_order(self):
        import yaml

        doc = yaml.safe_load(WF.read_text(encoding="utf-8"))
        self.assertEqual(
            [s["id"] for s in doc["steps"]], ["tick", "names", "notify", "ledger"]
        )

    def test_steps_depend_on_the_previous_one(self):
        import yaml

        doc = yaml.safe_load(WF.read_text(encoding="utf-8"))
        steps = {s["id"]: s for s in doc["steps"]}
        self.assertEqual(steps["names"]["needs"], ["tick"])
        self.assertEqual(steps["notify"]["needs"], ["names"])
        self.assertEqual(steps["ledger"]["needs"], ["notify"])

    def test_workflow_is_loadable_by_core(self):
        from kraken.core.workflow import load_workflow

        spec = load_workflow(WF)
        self.assertTrue(spec.get("steps"))

    def test_workflow_yaml_is_valid(self):
        import yaml

        doc = yaml.safe_load(WF.read_text(encoding="utf-8"))
        self.assertIsInstance(doc, dict)
        self.assertEqual(len(doc["steps"]), 4)
        for step in doc["steps"]:
            self.assertIn("tentacle", step)
            self.assertIn("action", step)


class KeepsNamesNotValues(unittest.TestCase):
    """`keeps list` returns names. A value must never appear in the envelope."""

    def invoke(self, action, payload=None, home=None):
        run = os.environ.copy()
        run["KRAKEN_OFFLINE"] = "1"
        run["KRAKEN_HOME"] = home or tempfile.mkdtemp()
        body = json.dumps({"v": 1, "action": action, "payload": payload or {}})
        proc = subprocess.run(
            ["sh", str(KEEPS)],
            input=body,
            text=True,
            capture_output=True,
            env=run,
            check=False,
        )
        lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("{")]
        self.assertTrue(lines, f"no JSON: {proc.stderr[:300]}")
        return json.loads(lines[-1])

    def test_list_returns_names_without_values(self):
        home = tempfile.mkdtemp()
        secret = "sk-live-do-not-leak-1234567890"
        self.invoke("put", {"name": "openai", "value": secret}, home=home)

        listed = self.invoke("list", home=home)
        self.assertTrue(listed["ok"])
        self.assertNotIn(secret, json.dumps(listed))

    def test_get_without_reveal_masks_the_value(self):
        home = tempfile.mkdtemp()
        secret = "sk-live-mask-me-abcdef"
        self.invoke("put", {"name": "openai", "value": secret}, home=home)

        masked = self.invoke("get", {"name": "openai"}, home=home)
        self.assertNotIn(secret, json.dumps(masked))

        revealed = self.invoke("get", {"name": "openai", "reveal": True}, home=home)
        self.assertEqual(revealed["result"]["value"], secret)


if __name__ == "__main__":
    unittest.main()
