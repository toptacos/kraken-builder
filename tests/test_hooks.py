from pathlib import Path

from kraken.core.hooks import collect_hooks
from kraken.core.runner import run_named


ROOT = Path(__file__).resolve().parents[1]


def test_after_run_echo_hook():
    result = run_named(ROOT, "echo", "ping")
    hooks = result.get("_hooks") or []
    assert any(h.get("tentacle") == "echo-bin" and h.get("ok") for h in hooks)


def test_hook_does_not_recurse():
    result = run_named(ROOT, "echo", "ping")
    hooks = result.get("_hooks") or []
    # echo-bin after_run must not attach another _hooks chain
    inner = hooks[0]["result"]
    assert "_hooks" not in inner


def test_collect_skips_self():
    hooks = collect_hooks(ROOT, "after_run", "echo-bin")
    assert all(h.get("tentacle") != "echo-bin" for h in hooks)
