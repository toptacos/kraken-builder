#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def invoke(action, payload=None, cwd=None):
    env = os.environ.copy()
    env["KRAKEN_OFFLINE"] = "1"
    proc = subprocess.run(
        ["sh", str(ROOT / "handler.sh")],
        input=json.dumps({"action": action, "payload": payload or {}}),
        text=True,
        capture_output=True,
        cwd=str(cwd or ROOT),
        env=env,
        check=False,
    )
    return json.loads([ln for ln in proc.stdout.splitlines() if ln.startswith("{")][-1])


class Scenarios(unittest.TestCase):
    def test_custom_yaml_panels(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / ".kraken").mkdir()
        (tmp / ".kraken" / "board.yaml").write_text(
            "name: acme\npanels:\n  - {id: repo, kind: repo}\n  - {id: ai, kind: ai}\n",
            encoding="utf-8",
        )
        snap = invoke("snapshot", {"root": str(tmp)}, cwd=tmp)
        self.assertEqual(snap["result"]["name"], "acme")
        self.assertEqual([p["id"] for p in snap["result"]["panels"]], ["repo", "ai"])

    def test_open_frame_has_boxes(self):
        frame = invoke("open", {"root": str(ROOT)})["result"]["frame"]
        self.assertIn("┌", frame)
        self.assertIn("repository", frame)

    def test_workflow_present(self):
        text = (ROOT / "workflows" / "open-and-analyze.yaml").read_text(encoding="utf-8")
        self.assertIn("tentacle: board", text)


if __name__ == "__main__":
    unittest.main()
