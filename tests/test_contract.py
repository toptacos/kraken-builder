import json
from pathlib import Path

from kraken.core.contract import encode_request, invoke_binary


def test_round_trip_request():
    raw = encode_request("ping", {"n": 1}, "abc")
    body = json.loads(raw)
    assert body["op"] == "invoke"
    assert body["action"] == "ping"


def test_invoke_example_binary():
    script = Path(__file__).resolve().parents[1] / "examples" / "tentacles" / "echo-bin.py"
    result = invoke_binary(script, "ping", {})
    assert result["ok"] is True
    assert result["result"]["arm"] == "echo-bin"
