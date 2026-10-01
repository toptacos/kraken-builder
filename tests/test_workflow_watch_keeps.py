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
ARMS = ROOT
WF = ROOT / "workflows" / "watch-keeps-notify.yaml"
KEEPS = ROOT / "kraken-tentacle-keeps" / "handler.sh"

sys.path.insert(0, str(ROOT / "kraken-builder"))


def run_workflow(path: Path, home: Path, arms: list[Path] | None = None) -> dict:
    """Actually execute the workflow through the core runner.

    Parsing the yaml proves it is well-formed. It does not prove the story
    runs — and this one did not: it referenced a `ledger` arm that was never
    built, while the test that "covered" it only ever called load_workflow.
    """
    run = os.environ.copy()
    run["KRAKEN_OFFLINE"] = "1"
    run["KRAKEN_HOME"] = str(home)
    run["KRAKEN_SYSTEM_DIR"] = str(home.parent / "system")
    run["PYTHONPATH"] = str(ARMS / "kraken-builder")

    root = home
    (root / ".kraken").mkdir(parents=True, exist_ok=True)
    # Installing an arm runs that arm's own suite, which is slow. Callers that
    # already have them installed pass arms=None.
    for arm in arms or []:
        subprocess.run(
            [sys.executable, "-m", "kraken", "tentacle", "add", str(arm)],
            capture_output=True,
            text=True,
            env=run,
            check=False,
        )

    proc = subprocess.run(
        [sys.executable, "-m", "kraken", "workflow", "run", str(path)],
        capture_output=True,
        text=True,
        env=run,
        cwd=str(root),
        check=False,
    )
    lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("{")]
    return json.loads(lines[-1]) if lines else {"ok": False, "error": proc.stderr[-400:]}


class WorkflowRuns(unittest.TestCase):
    """The story, end to end, on a throwaway home."""

    tmp: Path
    home: Path

    @classmethod
    def setUpClass(cls):
        # `kraken tentacle add` runs each arm's own test suite, so installing
        # per test turned three cases into seven minutes. Once per class.
        cls.tmp = Path(tempfile.mkdtemp())
        cls.home = cls.tmp / "installed"
        run = os.environ.copy()
        run["KRAKEN_OFFLINE"] = "1"
        run["KRAKEN_HOME"] = str(cls.home)
        run["KRAKEN_SYSTEM_DIR"] = str(cls.tmp / "system")
        run["PYTHONPATH"] = str(ARMS / "kraken-builder")
        (cls.home / ".kraken").mkdir(parents=True, exist_ok=True)
        for arm in ("watch", "keeps", "ledger"):
            subprocess.run(
                [sys.executable, "-m", "kraken", "tentacle", "add",
                 str(ARMS / f"kraken-tentacle-{arm}")],
                capture_output=True,
                text=True,
                env=run,
                check=False,
            )
        cls.run_env = run

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        self.home.mkdir()
        # Reuse the class-level install by copying it in, so the story runs
        # against arms that are present without paying for the install again.
        src = self.home / ".kraken" / "tentacles"
        src.parent.mkdir(parents=True, exist_ok=True)
        import shutil

        installed = type(self).home / ".kraken" / "tentacles"
        if installed.is_dir():
            shutil.copytree(installed, src)

    def test_the_story_actually_runs(self):
        result = run_workflow(WF, self.home)
        self.assertTrue(result.get("ok"), result)
        for step in result.get("steps", []):
            self.assertTrue(step.get("ok"), f"{step.get('id')}: {step}")

    def test_every_arm_the_workflow_names_exists(self):
        """A step naming an arm that was never built is an outage waiting to
        happen, and the yaml parses happily either way."""
        import yaml

        doc = yaml.safe_load(WF.read_text(encoding="utf-8"))
        for step in doc["steps"]:
            arm = step.get("tentacle")
            if not arm:
                continue
            path = ARMS / f"kraken-tentacle-{arm}"
            self.assertTrue(path.is_dir(), f"workflow step {step['id']}: no arm at {path}")
            self.assertTrue(
                (path / "handler.sh").is_file(), f"{arm} has no handler.sh"
            )

    def test_the_ledger_records_no_values(self):
        """The point of the story: the ledger records that watch ran, never
        what it saw."""
        run_workflow(WF, self.home)
        ledger = (
            self.home / ".kraken" / "data" / "ledger" / "ledger.jsonl"
        )
        self.assertTrue(ledger.is_file(), "the ledger step wrote nothing")
        text = ledger.read_text(encoding="utf-8")
        # The entry attributes the event to the arm that ran, not to the arm
        # that wrote it.
        self.assertIn("watch", text)
        self.assertIn("[redacted]", text)
        self.assertNotIn("must-be-redacted-if-present", text)

    def test_the_ledger_records_no_outbound_event(self):
        """Local-only: the story writes records, it does not make requests.

        Scanned over the ledger rather than every installed file, because a
        vendored README that mentions api.topta.co is prose, not a call.
        """
        run_workflow(WF, self.home)
        ledger = self.home / ".kraken" / "data" / "ledger" / "ledger.jsonl"
        self.assertNotIn(b"api.topta.co", ledger.read_bytes())


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
