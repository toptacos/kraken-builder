"""Tests for the jev-ai tentacle (Jev JSON editor + local AI models)."""
import json
import os
import sys
from pathlib import Path

# Ensure the handler is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples" / "tentacles" / "jev-ai"))

from handler import main as handler_main, _jev_edit, _check_jev, _check_ollama, _check_llamacpp


def _run_handler(action: str, payload: dict) -> dict:
    """Run the handler with a given action and payload, return parsed JSON response."""
    import io
    from contextlib import redirect_stdout

    req = {"v": 1, "id": "test-1", "op": "invoke", "action": action, "payload": payload}
    stdin_data = json.dumps(req)

    old_stdin = sys.stdin
    sys.stdin = io.StringIO(stdin_data)
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            code = handler_main()
    finally:
        sys.stdin = old_stdin

    assert code == 0, f"handler exited with code {code}"
    return json.loads(buf.getvalue())


def test_jev_edit_set():
    """Test setting a value in nested JSON via Jev path operations."""
    data = {"a": {"b": {"c": 1}}}
    operations = [{"op": "set", "path": "a.b.c", "value": 42}]
    result = _jev_edit(data, operations)
    assert result["a"]["b"]["c"] == 42


def test_jev_edit_get():
    """Test getting a value from nested JSON via Jev path operations."""
    data = {"a": {"b": {"c": 1}}}
    operations = [{"op": "get", "path": "a.b.c"}]
    result = _jev_edit(data, operations)
    assert result == 1


def test_jev_edit_delete():
    """Test deleting a key from nested JSON via Jev path operations."""
    data = {"a": {"b": {"c": 1, "d": 2}}}
    operations = [{"op": "delete", "path": "a.b.c"}]
    result = _jev_edit(data, operations)
    assert "c" not in result["a"]["b"]
    assert result["a"]["b"]["d"] == 2


def test_jev_edit_merge():
    """Test merging a dict into nested JSON via Jev path operations."""
    data = {"a": {"b": {"c": 1}}}
    operations = [{"op": "merge", "path": "a.b", "value": {"d": 2}}]
    result = _jev_edit(data, operations)
    assert result["a"]["b"]["c"] == 1
    assert result["a"]["b"]["d"] == 2


def test_handler_status():
    """Test the status action returns backend availability info."""
    resp = _run_handler("status", {})
    assert resp["ok"] is True
    assert "jev" in resp["result"]
    assert "ollama" in resp["result"]
    assert "llamacpp" in resp["result"]
    assert "data_dir" in resp["result"]


def test_handler_edit_with_data():
    """Test the edit action with inline data."""
    resp = _run_handler("edit", {
        "data": {"name": "test", "value": 1},
        "operations": [{"op": "set", "path": "name", "value": "updated"}],
    })
    assert resp["ok"] is True
    assert resp["result"]["result"]["name"] == "updated"


def test_handler_edit_save():
    """Test the edit action with save=True persists to disk."""
    resp = _run_handler("edit", {
        "data": {"key": "value"},
        "operations": [{"op": "set", "path": "key", "value": "saved"}],
        "save": True,
    })
    assert resp["ok"] is True
    assert resp["result"]["saved"] is True
    assert resp["result"]["result"]["key"] == "saved"


def test_handler_edit_no_operations():
    """Test the edit action returns error when no operations provided."""
    resp = _run_handler("edit", {"data": {}})
    assert resp["ok"] is False
    assert "error" in resp["result"]


def test_handler_infer_no_prompt():
    """Test the infer action returns error when no prompt provided."""
    resp = _run_handler("infer", {})
    assert resp["ok"] is False
    assert "error" in resp["result"]


def test_handler_unknown_action():
    """Test the handler returns error for unknown actions."""
    resp = _run_handler("nonexistent", {})
    assert resp["ok"] is False
    assert "error" in resp["result"]


def test_check_jev_returns_dict():
    """Test _check_jev returns a dict with 'available' key."""
    result = _check_jev()
    assert isinstance(result, dict)
    assert "available" in result


def test_check_ollama_returns_dict():
    """Test _check_ollama returns a dict with 'available' key."""
    result = _check_ollama()
    assert isinstance(result, dict)
    assert "available" in result


def test_check_llamacpp_returns_dict():
    """Test _check_llamacpp returns a dict with 'available' key."""
    result = _check_llamacpp()
    assert isinstance(result, dict)
    assert "available" in result
