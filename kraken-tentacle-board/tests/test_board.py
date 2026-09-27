#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def invoke(action: str, payload: dict | None = None, env: dict | None = None, cwd: Path | None = None) -> dict:
    req = {"v": 1, "action": action, "payload": payload or {}}
    run_env = os.environ.copy()
    run_env["KRAKEN_OFFLINE"] = "1"
    run_env.setdefault("KRAKEN_BOARD_APPLY", "1")
    if env:
        run_env.update(env)
    proc = subprocess.run(
        ["sh", str(ROOT / "handler.sh")],
        input=json.dumps(req),
        text=True,
        capture_output=True,
        cwd=str(cwd or ROOT),
        env=run_env,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(proc.stderr)
    line = [ln for ln in proc.stdout.splitlines() if ln.startswith("{")][-1]
    return json.loads(line)


class BoardContract(unittest.TestCase):
    def test_ping(self) -> None:
        body = invoke("ping")
        self.assertTrue(body["ok"])
        self.assertEqual(body["result"]["arm"], "board")

    def test_unknown(self) -> None:
        body = invoke("explode")
        self.assertFalse(body["ok"])
        self.assertEqual(body["error"]["code"], "unknown_action")

    def test_init_and_open(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        body = invoke("init", {"root": str(tmp)})
        self.assertTrue(Path(body["result"]["wrote"]).exists())
        opened = invoke("open", {"root": str(tmp)}, cwd=tmp)
        self.assertIn("frame", opened["result"])
        self.assertIn("board", opened["result"]["frame"])
        ids = [p["id"] for p in opened["result"]["panels"]]
        self.assertIn("repo", ids)
        self.assertIn("ai", ids)

    def test_apply_jev_ops(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        target = tmp / "app.json"
        target.write_text('{"name":"demo","flags":{"x":1}}\n', encoding="utf-8")
        body = invoke(
            "apply",
            {
                "root": str(tmp),
                "file": "app.json",
                "operations": [
                    {"op": "set", "path": "flags.y", "value": True},
                    {"op": "merge", "path": "flags", "value": {"z": 3}},
                ],
            },
            cwd=tmp,
        )
        self.assertTrue(body["ok"])
        data = json.loads(target.read_text())
        self.assertTrue(data["flags"]["y"])
        self.assertEqual(data["flags"]["z"], 3)

    def test_apply_rejects_escape(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        body = invoke("apply", {"root": str(tmp), "file": "../secret.json", "operations": []}, cwd=tmp)
        self.assertFalse(body["ok"])
        self.assertEqual(body["error"]["code"], "path_escape")

    def test_analyze_offline_fixture(self) -> None:
        body = invoke("analyze", {"root": str(ROOT), "prompt": "health"})
        self.assertTrue(body["ok"])
        self.assertEqual(body["result"]["analysis"]["backend"], "fixture")

    def test_finish(self) -> None:
        body = invoke("finish", {"raw": {"arm": "board"}, "patch": {"sucker": "save-text"}})
        self.assertTrue(body["result"]["finished"])


if __name__ == "__main__":
    unittest.main()
