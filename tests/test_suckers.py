from pathlib import Path

import yaml

from kraken.core.hooks import collect_hooks
from kraken.core.runner import run_named


ROOT = Path(__file__).resolve().parents[1]
SUCKER = ROOT / "examples" / "suckers" / "after-echo.yaml"


def test_sucker_is_named_hook_row():
    row = yaml.safe_load(SUCKER.read_text())
    assert row["sucker"] == "after-echo"
    assert row["tentacle"] == "echo-bin"
    assert "kraken.core" not in SUCKER.read_text()


def test_sucker_hooks_do_not_reenter():
    result = run_named(ROOT, "echo", "ping")
    hooks = result.get("_hooks") or []
    assert any(h.get("tentacle") == "echo-bin" and h.get("ok") for h in hooks)
    assert "_hooks" not in hooks[0]["result"]


def test_collect_hooks_skips_self_as_sucker():
    hooks = collect_hooks(ROOT, "after_run", "echo-bin")
    assert all(h.get("tentacle") != "echo-bin" for h in hooks)
