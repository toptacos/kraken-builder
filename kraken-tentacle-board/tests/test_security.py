#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def invoke(action: str, payload: dict, env: dict | None = None) -> dict:
    run_env = os.environ.copy()
    run_env["KRAKEN_OFFLINE"] = "1"
    if env:
        run_env.update(env)
    proc = subprocess.run(
        ["python3", str(ROOT / "handler.py")],
        input=json.dumps({"v": 1, "action": action, "payload": payload}),
        text=True,
        capture_output=True,
        env=run_env,
        check=False,
    )
    return json.loads(proc.stdout)


class BoardSecurity(unittest.TestCase):
    def test_apply_denied_without_grant(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        body = invoke(
            "apply",
            {"root": str(tmp), "file": "app.json", "operations": []},
            env={"KRAKEN_BOARD_APPLY": "0"},
        )
        self.assertFalse(body["ok"])
        self.assertEqual(body["error"]["code"], "no_grant")

    def test_loopback_helper(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("board", ROOT / "handler.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with self.assertRaises(PermissionError):
            mod.loopback_url("https://api.openai.com/v1")
        mod.loopback_url("http://127.0.0.1:11434/api/generate")


if __name__ == "__main__":
    unittest.main()
