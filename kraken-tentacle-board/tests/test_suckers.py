#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Suckers(unittest.TestCase):
    def test_save_text(self) -> None:
        dest = Path(tempfile.mkdtemp()) / "last.json"
        req = {"action": "convert", "payload": {"raw": {"arm": "board"}, "out": str(dest)}}
        proc = subprocess.run(
            ["python3", str(ROOT / "suckers" / "save-text" / "handler.py")],
            input=json.dumps(req),
            text=True,
            capture_output=True,
            check=False,
        )
        body = json.loads(proc.stdout)
        self.assertTrue(body["ok"])
        self.assertTrue(dest.exists())

    def test_after_board_row(self) -> None:
        text = (ROOT / "tentacle.yaml").read_text(encoding="utf-8")
        self.assertIn("save-text", text)


if __name__ == "__main__":
    unittest.main()
