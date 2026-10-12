import json
import pytest
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import os


from kraken.core.contract import (
    PROTOCOL_VERSION,
    KINDS,
    _argv,
    decode_response,
    encode_request,
    envelope,
    invoke_binary,
    unwrap,
)


NT_SKIP = pytest.mark.skipif(
    os.name == "nt",
    reason="POSIX-only: needs a shell or exec bits Windows does not have",
)


def test_envelope_valid_kind():
    result = envelope("json", {"key": "value"}, source="test")
    assert result == {
        "kind": "json",
        "value": {"key": "value"},
        "meta": {"source": "test"},
    }


def test_envelope_all_valid_kinds():
    for kind in KINDS:
        result = envelope(kind, "val")
        assert result["kind"] == kind
        assert result["value"] == "val"
        assert result["meta"] == {}


def test_envelope_invalid_kind_defaults_to_json():
    result = envelope("invalid", "val")
    assert result["kind"] == "json"
    assert result["value"] == "val"


def test_envelope_no_meta():
    result = envelope("text", 42)
    assert result == {"kind": "text", "value": 42, "meta": {}}


def test_envelope_multiple_meta():
    result = envelope("file", "data", a=1, b=2)
    assert result["meta"] == {"a": 1, "b": 2}


def test_envelope_none_value():
    result = envelope("json", None)
    assert result["value"] is None


def test_envelope_false_value():
    result = envelope("json", False)
    assert result["value"] is False


def test_envelope_zero_value():
    result = envelope("json", 0)
    assert result["value"] == 0


def test_envelope_empty_string_value():
    result = envelope("text", "")
    assert result["value"] == ""


def test_envelope_empty_list_value():
    result = envelope("json", [])
    assert result["value"] == []


def test_envelope_empty_dict_value():
    result = envelope("json", {})
    assert result["value"] == {}


def test_unwrap_valid_envelope():
    payload = {"kind": "json", "value": {"x": 1}, "meta": {"src": "test"}}
    result = unwrap(payload)
    assert result == {"kind": "json", "value": {"x": 1}, "meta": {"src": "test"}}


def test_unwrap_all_valid_kinds():
    for kind in KINDS:
        payload = {"kind": kind, "value": "v", "meta": {"k": "v"}}
        result = unwrap(payload)
        assert result["kind"] == kind


def test_unwrap_dict_without_kind():
    payload = {"value": "v", "meta": {"k": "v"}}
    result = unwrap(payload)
    assert result == {"kind": "json", "value": payload, "meta": {}}


def test_unwrap_dict_with_invalid_kind():
    payload = {"kind": "invalid", "value": "v"}
    result = unwrap(payload)
    assert result == {"kind": "json", "value": payload, "meta": {}}


def test_unwrap_dict_with_kind_none():
    payload = {"kind": None, "value": "v"}
    result = unwrap(payload)
    assert result == {"kind": "json", "value": payload, "meta": {}}


def test_unwrap_dict_with_kind_empty_string():
    payload = {"kind": "", "value": "v"}
    result = unwrap(payload)
    assert result == {"kind": "json", "value": payload, "meta": {}}


def test_unwrap_dict_with_kind_integer():
    payload = {"kind": 123, "value": "v"}
    result = unwrap(payload)
    assert result == {"kind": "json", "value": payload, "meta": {}}


def test_unwrap_non_dict_string():
    result = unwrap("raw string")
    assert result == {"kind": "json", "value": "raw string", "meta": {}}


def test_unwrap_non_dict_list():
    result = unwrap([1, 2, 3])
    assert result == {"kind": "json", "value": [1, 2, 3], "meta": {}}


def test_unwrap_non_dict_none():
    result = unwrap(None)
    assert result == {"kind": "json", "value": None, "meta": {}}


def test_unwrap_non_dict_int():
    result = unwrap(42)
    assert result == {"kind": "json", "value": 42, "meta": {}}


def test_unwrap_non_dict_bool():
    result = unwrap(True)
    assert result == {"kind": "json", "value": True, "meta": {}}


def test_unwrap_non_dict_float():
    result = unwrap(3.14)
    assert result == {"kind": "json", "value": 3.14, "meta": {}}


def test_unwrap_non_dict_tuple():
    result = unwrap((1, 2))
    assert result == {"kind": "json", "value": (1, 2), "meta": {}}


def test_unwrap_missing_value():
    payload = {"kind": "json"}
    result = unwrap(payload)
    assert result == {"kind": "json", "value": None, "meta": {}}


def test_unwrap_missing_meta():
    payload = {"kind": "json", "value": "v"}
    result = unwrap(payload)
    assert result == {"kind": "json", "value": "v", "meta": {}}


def test_unwrap_none_meta():
    payload = {"kind": "json", "value": "v", "meta": None}
    result = unwrap(payload)
    assert result == {"kind": "json", "value": "v", "meta": {}}


def test_unwrap_empty_dict():
    result = unwrap({})
    assert result == {"kind": "json", "value": {}, "meta": {}}


def test_unwrap_meta_with_multiple_keys():
    payload = {"kind": "json", "value": "v", "meta": {"a": 1, "b": 2, "c": 3}}
    result = unwrap(payload)
    assert result["meta"] == {"a": 1, "b": 2, "c": 3}


def test_unwrap_preserves_value_identity():
    value = {"nested": [1, 2, 3]}
    payload = {"kind": "json", "value": value}
    result = unwrap(payload)
    assert result["value"] is value


def test_unwrap_value_containing_kind_key():
    payload = {"kind": "json", "value": {"kind": "inner"}}
    result = unwrap(payload)
    assert result["value"] == {"kind": "inner"}


def test_encode_request_with_payload():
    raw = encode_request("ping", {"n": 1}, "abc")
    body = json.loads(raw)
    assert body == {
        "v": PROTOCOL_VERSION,
        "id": "abc",
        "op": "invoke",
        "action": "ping",
        "payload": {"n": 1},
    }


def test_encode_request_default_payload():
    raw = encode_request("status")
    body = json.loads(raw)
    assert body["payload"] == {}


def test_encode_request_default_req_id():
    raw = encode_request("status")
    body = json.loads(raw)
    assert body["id"] == "1"


def test_encode_request_none_payload():
    raw = encode_request("status", None)
    body = json.loads(raw)
    assert body["payload"] == {}


def test_encode_request_empty_dict_payload():
    raw = encode_request("status", {})
    body = json.loads(raw)
    assert body["payload"] == {}


def test_encode_request_returns_bytes():
    raw = encode_request("ping")
    assert isinstance(raw, bytes)


def test_encode_request_protocol_version():
    raw = encode_request("ping")
    body = json.loads(raw)
    assert body["v"] == 1


def test_encode_request_unicode_action():
    raw = encode_request("ping")
    body = json.loads(raw)
    assert body["action"] == "ping"


def test_encode_request_unicode_payload():
    raw = encode_request("ping", {"msg": "hello"})
    body = json.loads(raw)
    assert body["payload"]["msg"] == "hello"


def test_encode_request_nested_payload():
    raw = encode_request("ping", {"a": {"b": {"c": [1, 2, 3]}}})
    body = json.loads(raw)
    assert body["payload"]["a"]["b"]["c"] == [1, 2, 3]


def test_encode_request_list_payload():
    raw = encode_request("ping", [1, 2, 3])
    body = json.loads(raw)
    assert body["payload"] == [1, 2, 3]


def test_encode_request_string_payload():
    raw = encode_request("ping", "raw string")
    body = json.loads(raw)
    assert body["payload"] == "raw string"


def test_encode_request_integer_payload():
    raw = encode_request("ping", 42)
    body = json.loads(raw)
    assert body["payload"] == 42


def test_encode_request_boolean_payload():
    raw = encode_request("ping", True)
    body = json.loads(raw)
    assert body["payload"] is True


def test_encode_request_special_chars_in_action():
    raw = encode_request("action/with:special@chars")
    body = json.loads(raw)
    assert body["action"] == "action/with:special@chars"


def test_encode_request_special_chars_in_req_id():
    raw = encode_request("ping", req_id="id-with:special@chars")
    body = json.loads(raw)
    assert body["id"] == "id-with:special@chars"


def test_encode_request_large_req_id():
    raw = encode_request("ping", req_id="x" * 10000)
    body = json.loads(raw)
    assert body["id"] == "x" * 10000


def test_encode_request_large_action():
    raw = encode_request("a" * 10000)
    body = json.loads(raw)
    assert body["action"] == "a" * 10000


def test_encode_request_large_payload():
    raw = encode_request("ping", {"data": "x" * 100000})
    body = json.loads(raw)
    assert len(body["payload"]["data"]) == 100000


def test_decode_response_valid_object():
    raw = json.dumps({"ok": True, "result": {}}).encode("utf-8")
    result = decode_response(raw)
    assert result == {"ok": True, "result": {}}


def test_decode_response_non_dict_list_raises():
    raw = json.dumps([1, 2, 3]).encode("utf-8")
    with pytest.raises(ValueError, match="must be a JSON object"):
        decode_response(raw)


def test_decode_response_non_dict_string_raises():
    raw = json.dumps("hello").encode("utf-8")
    with pytest.raises(ValueError, match="must be a JSON object"):
        decode_response(raw)


def test_decode_response_non_dict_number_raises():
    raw = json.dumps(42).encode("utf-8")
    with pytest.raises(ValueError, match="must be a JSON object"):
        decode_response(raw)


def test_decode_response_non_dict_bool_raises():
    raw = json.dumps(True).encode("utf-8")
    with pytest.raises(ValueError, match="must be a JSON object"):
        decode_response(raw)


def test_decode_response_non_dict_null_raises():
    raw = json.dumps(None).encode("utf-8")
    with pytest.raises(ValueError, match="must be a JSON object"):
        decode_response(raw)


def test_decode_response_invalid_json_raises():
    raw = b"not json"
    with pytest.raises(json.JSONDecodeError):
        decode_response(raw)


def test_decode_response_empty_bytes_raises():
    raw = b""
    with pytest.raises(json.JSONDecodeError):
        decode_response(raw)


def test_decode_response_with_extra_fields():
    raw = json.dumps({"ok": True, "extra": "field", "nested": {"a": 1}}).encode("utf-8")
    result = decode_response(raw)
    assert result["extra"] == "field"
    assert result["nested"] == {"a": 1}


def test_decode_response_preserves_key_order():
    raw = b'{"z": 1, "a": 2, "m": 3}'
    result = decode_response(raw)
    assert list(result.keys()) == ["z", "a", "m"]


def test_decode_response_with_empty_nested_objects():
    raw = json.dumps({"a": {}, "b": [], "c": None}).encode("utf-8")
    result = decode_response(raw)
    assert result == {"a": {}, "b": [], "c": None}


def test_decode_response_large_json():
    data = {"items": list(range(10000))}
    raw = json.dumps(data).encode("utf-8")
    result = decode_response(raw)
    assert len(result["items"]) == 10000


def test_decode_response_deeply_nested():
    depth = 100
    data = current = {}
    for _ in range(depth):
        current["nested"] = {}
        current = current["nested"]
    raw = json.dumps(data).encode("utf-8")
    result = decode_response(raw)
    node = result
    for _ in range(depth):
        node = node["nested"]
    assert node == {}


def test_argv_python(tmp_path):
    binary = tmp_path / "handler.py"
    result = _argv(binary)
    assert result == [sys.executable, str(binary)]


def test_argv_shell(tmp_path):
    binary = tmp_path / "handler.sh"
    result = _argv(binary)
    assert result == ["bash", str(binary)]


def test_argv_js(tmp_path):
    binary = tmp_path / "handler.js"
    result = _argv(binary)
    assert result == ["node", str(binary)]


def test_argv_mjs(tmp_path):
    binary = tmp_path / "handler.mjs"
    result = _argv(binary)
    assert result == ["node", str(binary)]


def test_argv_applescript(tmp_path):
    binary = tmp_path / "handler.applescript"
    result = _argv(binary)
    assert result == ["osascript", str(binary)]


def test_argv_scpt(tmp_path):
    binary = tmp_path / "handler.scpt"
    result = _argv(binary)
    assert result == ["osascript", str(binary)]


def test_argv_php(tmp_path):
    binary = tmp_path / "handler.php"
    result = _argv(binary)
    assert result == ["php", str(binary)]


def test_argv_ruby(tmp_path):
    binary = tmp_path / "handler.rb"
    result = _argv(binary)
    assert result == ["ruby", str(binary)]


def test_argv_perl(tmp_path):
    binary = tmp_path / "handler.pl"
    result = _argv(binary)
    assert result == ["perl", str(binary)]


def test_argv_go(tmp_path):
    binary = tmp_path / "handler.go"
    result = _argv(binary)
    assert result == ["go", "run", str(binary)]


def test_argv_no_extension(tmp_path):
    binary = tmp_path / "handler"
    result = _argv(binary)
    assert result == [str(binary)]


def test_argv_unknown_extension(tmp_path):
    binary = tmp_path / "handler.xyz"
    result = _argv(binary)
    assert result == [str(binary)]


def test_argv_uppercase_extension(tmp_path):
    binary = tmp_path / "handler.PY"
    result = _argv(binary)
    assert result == [str(binary)]


def test_argv_path_with_spaces(tmp_path):
    binary = tmp_path / "my handler.py"
    result = _argv(binary)
    assert result == [sys.executable, str(binary)]


def test_argv_path_with_special_chars(tmp_path):
    binary = tmp_path / "handler-v1.2.3_test.py"
    result = _argv(binary)
    assert result == [sys.executable, str(binary)]


def test_argv_dotfile(tmp_path):
    binary = tmp_path / ".handler.py"
    result = _argv(binary)
    assert result == [sys.executable, str(binary)]


def test_argv_double_extension(tmp_path):
    binary = tmp_path / "handler.test.py"
    result = _argv(binary)
    assert result == [sys.executable, str(binary)]


def test_argv_only_extension(tmp_path):
    binary = tmp_path / ".py"
    result = _argv(binary)
    assert result == [sys.executable, str(binary)]


def test_invoke_binary_success(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys, json\n"
        "data = json.load(sys.stdin)\n"
        "print(json.dumps({'ok': True, 'action': data['action']}))\n"
    )
    result = invoke_binary(script, "ping", {"n": 1})
    assert result == {"ok": True, "action": "ping"}


def test_invoke_binary_nonzero_exit_with_stderr(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error msg'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error msg"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_empty_stderr(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.exit(2)\n")
    with pytest.raises(RuntimeError, match="no stderr"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_whitespace_stderr(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('   '); sys.exit(3)\n")
    with pytest.raises(RuntimeError, match="no stderr"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_newlines_stderr(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('\\n\\n'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="no stderr"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_tabs_stderr(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('\\t\\t'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="no stderr"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_mixed_whitespace_stderr(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write(' \\t\\n '); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="no stderr"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_surrounding_whitespace(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('  real error  '); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="real error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_trailing_newline(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error\\n\\n'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_leading_newline(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('\\n\\nerror'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


@NT_SKIP
def test_invoke_binary_nonzero_exit_multiline_error(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys; sys.stderr.write('line1\\nline2\\nline3'); sys.exit(1)\n"
    )
    with pytest.raises(RuntimeError, match="line1\\nline2\\nline3"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_very_long_error(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('x' * 10000); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="x" * 100):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_unicode_error(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_special_chars(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys; sys.stderr.write('error: [test] (failed)'); sys.exit(1)\n"
    )
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_quotes(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys; sys.stderr.write('error: \"quoted\"'); sys.exit(1)\n"
    )
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_backslashes(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys; sys.stderr.write('error: path\\\\to\\\\file'); sys.exit(1)\n"
    )
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_braces(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys; sys.stderr.write('error: {key: value}'); sys.exit(1)\n"
    )
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_dollar_sign(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error: $VAR'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_asterisk(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error: *.py'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_question_mark(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error: what?'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_pipe(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error: a|b'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_caret(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error: ^start'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_plus(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error: a+b'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_equals(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error: key=val'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_colon(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys; sys.stderr.write('error: msg: detail'); sys.exit(1)\n"
    )
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_semicolon(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error; detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_comma(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error, detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_period(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error.detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_hyphen(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error-detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_underscore(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error_detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_tilde(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error~detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_at_sign(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error@detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_hash(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error#detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_percent(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error%detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_ampersand(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error&detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_exclamation(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error!detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_less_than(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error<detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_greater_than(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error>detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_parentheses(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error(detail)'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_brackets(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error[detail]'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_backtick(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error`detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_single_quote(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text('import sys; sys.stderr.write("error\'detail"); sys.exit(1)\n')
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_double_quote(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error\"detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_forward_slash(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error/detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_tab(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error\\tdetail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_carriage_return(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error\\rdetail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_form_feed(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error\\x0cdetail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_vertical_tab(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error\\x0bdetail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_escape(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error\\x1bdetail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_null(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error\\x00detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_bell(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error\\x07detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_backspace(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error\\x08detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_unicode_escape(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys; sys.stderr.write('error\\u0041detail'); sys.exit(1)\n"
    )
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_hex_escape(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error\\x41detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_with_octal_escape(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.stderr.write('error\\101detail'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="error"):
        invoke_binary(script, "ping")


def test_invoke_binary_nonzero_exit_error_containing_binary_path(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(f"import sys; sys.stderr.write('{script} failed'); sys.exit(1)\n")
    with pytest.raises(RuntimeError, match="failed"):
        invoke_binary(script, "ping")


def test_invoke_binary_timeout(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import time; time.sleep(60)\n")
    with pytest.raises(subprocess.TimeoutExpired):
        invoke_binary(script, "ping", timeout=1)


def test_invoke_binary_timeout_zero(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import time; time.sleep(60)\n")
    with pytest.raises(subprocess.TimeoutExpired):
        invoke_binary(script, "ping", timeout=0)


def test_invoke_binary_timeout_negative(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import time; time.sleep(60)\n")
    with pytest.raises(subprocess.TimeoutExpired):
        invoke_binary(script, "ping", timeout=-1)


def test_invoke_binary_very_short_timeout(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import time; time.sleep(1)\n")
    with pytest.raises(subprocess.TimeoutExpired):
        invoke_binary(script, "ping", timeout=0.001)


def test_invoke_binary_passes_payload(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys, json\n"
        "data = json.load(sys.stdin)\n"
        "print(json.dumps({'payload': data['payload']}))\n"
    )
    result = invoke_binary(script, "ping", {"key": "value"})
    assert result == {"payload": {"key": "value"}}


def test_invoke_binary_default_timeout(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys, json; print(json.dumps({'ok': True}))\n")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"ok": true}', stderr=b""
        )
        invoke_binary(script, "ping")
        assert mock_run.call_args[1]["timeout"] == 30


def test_invoke_binary_custom_timeout(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys, json; print(json.dumps({'ok': True}))\n")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"ok": true}', stderr=b""
        )
        invoke_binary(script, "ping", timeout=60)
        assert mock_run.call_args[1]["timeout"] == 60


def test_invoke_binary_sends_encoded_request(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys, json; print(json.dumps({'ok': True}))\n")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"ok": true}', stderr=b""
        )
        invoke_binary(script, "myaction", {"x": 1}, req_id="99")
        sent_input = mock_run.call_args[1]["input"]
        body = json.loads(sent_input)
        assert body["action"] == "myaction"
        assert body["payload"] == {"x": 1}
        assert body["id"] == "99"


@NT_SKIP
def test_invoke_binary_shell_script(tmp_path):
    script = tmp_path / "handler.sh"
    script.write_text("#!/bin/bash\necho '{\"ok\": true}'\n")
    result = invoke_binary(script, "ping")
    assert result == {"ok": True}


def test_invoke_binary_large_payload(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys, json\n"
        "data = json.load(sys.stdin)\n"
        "print(json.dumps({'size': len(data['payload']['items'])}))\n"
    )
    payload = {"items": list(range(10000))}
    result = invoke_binary(script, "ping", payload)
    assert result == {"size": 10000}


def test_invoke_binary_unicode_payload(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys, json\n"
        "data = json.load(sys.stdin)\n"
        "print(json.dumps({'msg': data['payload']['msg']}))\n"
    )
    result = invoke_binary(script, "ping", {"msg": "hello"})
    assert result == {"msg": "hello"}


def test_invoke_binary_none_payload(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys, json\n"
        "data = json.load(sys.stdin)\n"
        "print(json.dumps({'payload': data['payload']}))\n"
    )
    result = invoke_binary(script, "ping", None)
    assert result == {"payload": {}}


def test_invoke_binary_go_binary(tmp_path):
    binary = tmp_path / "handler.go"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"ok": true}', stderr=b""
        )
        invoke_binary(binary, "ping")
        cmd = mock_run.call_args[0][0]
        assert cmd == ["go", "run", str(binary)]


def test_invoke_binary_php_binary(tmp_path):
    binary = tmp_path / "handler.php"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"ok": true}', stderr=b""
        )
        invoke_binary(binary, "ping")
        cmd = mock_run.call_args[0][0]
        assert cmd == ["php", str(binary)]


def test_invoke_binary_ruby_binary(tmp_path):
    binary = tmp_path / "handler.rb"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"ok": true}', stderr=b""
        )
        invoke_binary(binary, "ping")
        cmd = mock_run.call_args[0][0]
        assert cmd == ["ruby", str(binary)]


def test_invoke_binary_perl_binary(tmp_path):
    binary = tmp_path / "handler.pl"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"ok": true}', stderr=b""
        )
        invoke_binary(binary, "ping")
        cmd = mock_run.call_args[0][0]
        assert cmd == ["perl", str(binary)]


def test_invoke_binary_node_binary(tmp_path):
    binary = tmp_path / "handler.js"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"ok": true}', stderr=b""
        )
        invoke_binary(binary, "ping")
        cmd = mock_run.call_args[0][0]
        assert cmd == ["node", str(binary)]


def test_invoke_binary_mjs_binary(tmp_path):
    binary = tmp_path / "handler.mjs"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"ok": true}', stderr=b""
        )
        invoke_binary(binary, "ping")
        cmd = mock_run.call_args[0][0]
        assert cmd == ["node", str(binary)]


def test_invoke_binary_applescript_binary(tmp_path):
    binary = tmp_path / "handler.applescript"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"ok": true}', stderr=b""
        )
        invoke_binary(binary, "ping")
        cmd = mock_run.call_args[0][0]
        assert cmd == ["osascript", str(binary)]


def test_invoke_binary_scpt_binary(tmp_path):
    binary = tmp_path / "handler.scpt"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"ok": true}', stderr=b""
        )
        invoke_binary(binary, "ping")
        cmd = mock_run.call_args[0][0]
        assert cmd == ["osascript", str(binary)]


def test_invoke_binary_no_extension_binary(tmp_path):
    binary = tmp_path / "handler"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"ok": true}', stderr=b""
        )
        invoke_binary(binary, "ping")
        cmd = mock_run.call_args[0][0]
        assert cmd == [str(binary)]


def test_invoke_binary_unknown_extension_binary(tmp_path):
    binary = tmp_path / "handler.xyz"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"ok": true}', stderr=b""
        )
        invoke_binary(binary, "ping")
        cmd = mock_run.call_args[0][0]
        assert cmd == [str(binary)]


def test_invoke_binary_uses_sys_executable_for_python(tmp_path):
    script = tmp_path / "handler.py"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"ok": true}', stderr=b""
        )
        invoke_binary(script, "ping")
        cmd = mock_run.call_args[0][0]
        assert cmd == [sys.executable, str(script)]


def test_invoke_binary_uses_bash_for_shell(tmp_path):
    script = tmp_path / "handler.sh"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"ok": true}', stderr=b""
        )
        invoke_binary(script, "ping")
        cmd = mock_run.call_args[0][0]
        assert cmd == ["bash", str(script)]


def test_invoke_binary_check_is_false(tmp_path):
    script = tmp_path / "handler.py"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"ok": true}', stderr=b""
        )
        invoke_binary(script, "ping")
        assert mock_run.call_args[1]["check"] is False


def test_invoke_binary_capture_output_is_true(tmp_path):
    script = tmp_path / "handler.py"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"ok": true}', stderr=b""
        )
        invoke_binary(script, "ping")
        assert mock_run.call_args[1]["capture_output"] is True


def test_invoke_binary_input_is_bytes(tmp_path):
    script = tmp_path / "handler.py"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"ok": true}', stderr=b""
        )
        invoke_binary(script, "ping")
        assert isinstance(mock_run.call_args[1]["input"], bytes)


def test_invoke_binary_action_passed_through(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys, json\n"
        "data = json.load(sys.stdin)\n"
        "print(json.dumps({'action': data['action']}))\n"
    )
    result = invoke_binary(script, "custom_action")
    assert result == {"action": "custom_action"}


def test_invoke_binary_req_id_passed_through(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys, json\n"
        "data = json.load(sys.stdin)\n"
        "print(json.dumps({'id': data['id']}))\n"
    )
    result = invoke_binary(script, "ping", req_id="custom-id")
    assert result == {"id": "custom-id"}


def test_invoke_binary_protocol_version_passed(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys, json\n"
        "data = json.load(sys.stdin)\n"
        "print(json.dumps({'v': data['v']}))\n"
    )
    result = invoke_binary(script, "ping")
    assert result == {"v": PROTOCOL_VERSION}


def test_invoke_binary_op_is_invoke(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys, json\n"
        "data = json.load(sys.stdin)\n"
        "print(json.dumps({'op': data['op']}))\n"
    )
    result = invoke_binary(script, "ping")
    assert result == {"op": "invoke"}


def test_invoke_binary_response_is_dict(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys, json; print(json.dumps({'ok': True}))\n")
    result = invoke_binary(script, "ping")
    assert isinstance(result, dict)


def test_invoke_binary_response_with_nested_json(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys, json\n"
        "print(json.dumps({'ok': True, 'result': {'nested': {'deep': [1, 2, 3]}}}))\n"
    )
    result = invoke_binary(script, "ping")
    assert result["result"]["nested"]["deep"] == [1, 2, 3]


def test_invoke_binary_response_with_unicode(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys, json\nprint(json.dumps({'msg': 'hello'}, ensure_ascii=False))\n"
    )
    result = invoke_binary(script, "ping")
    assert result["msg"] == "hello"


def test_invoke_binary_response_with_null_values(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys, json; print(json.dumps({'ok': None, 'v': 0}))\n")
    result = invoke_binary(script, "ping")
    assert result == {"ok": None, "v": 0}


def test_invoke_binary_response_with_boolean(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys, json; print(json.dumps({'ok': False}))\n")
    result = invoke_binary(script, "ping")
    assert result == {"ok": False}


def test_invoke_binary_response_with_empty_object(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys, json; print(json.dumps({}))\n")
    result = invoke_binary(script, "ping")
    assert result == {}


def test_invoke_binary_response_with_array_value(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys, json; print(json.dumps({'items': [1, 'two', None]}))\n"
    )
    result = invoke_binary(script, "ping")
    assert result == {"items": [1, "two", None]}


def test_invoke_binary_response_with_all_json_types(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys, json\n"
        "print(json.dumps({\n"
        "    'str': 'hello',\n"
        "    'int': 42,\n"
        "    'float': 3.14,\n"
        "    'bool': True,\n"
        "    'null': None,\n"
        "    'list': [1, 2],\n"
        "    'dict': {'nested': 'value'}\n"
        "}))\n"
    )
    result = invoke_binary(script, "ping")
    assert result["str"] == "hello"
    assert result["int"] == 42
    assert result["float"] == 3.14
    assert result["bool"] is True
    assert result["null"] is None
    assert result["list"] == [1, 2]
    assert result["dict"] == {"nested": "value"}


def test_invoke_binary_captures_stdout_only(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys\nsys.stderr.write('error output\\n')\nprint('{\"ok\": true}')\n"
    )
    result = invoke_binary(script, "ping")
    assert result == {"ok": True}


def test_invoke_binary_exit_code_zero_with_empty_stdout(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys; sys.exit(0)\n")
    with pytest.raises(json.JSONDecodeError):
        invoke_binary(script, "ping")


def test_invoke_binary_exit_code_zero_with_non_json_stdout(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("print('not json')\n")
    with pytest.raises(json.JSONDecodeError):
        invoke_binary(script, "ping")


def test_invoke_binary_exit_code_zero_with_whitespace_stdout(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("print('   ')\n")
    with pytest.raises(json.JSONDecodeError):
        invoke_binary(script, "ping")


def test_invoke_binary_large_response(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys, json\nprint(json.dumps({'data': 'x' * 100000}))\n")
    result = invoke_binary(script, "ping")
    assert len(result["data"]) == 100000


def test_invoke_binary_response_with_large_nested_structure(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys, json\n"
        "data = {'items': [{'id': i, 'name': f'item_{i}'} for i in range(1000)]}\n"
        "print(json.dumps(data))\n"
    )
    result = invoke_binary(script, "ping")
    assert len(result["items"]) == 1000
    assert result["items"][500]["name"] == "item_500"


def test_invoke_binary_binary_path_with_spaces(tmp_path):
    script = tmp_path / "my handler.py"
    script.write_text("import sys, json; print(json.dumps({'ok': True}))\n")
    result = invoke_binary(script, "ping")
    assert result == {"ok": True}


def test_invoke_binary_concurrent_calls(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text(
        "import sys, json\n"
        "data = json.load(sys.stdin)\n"
        "print(json.dumps({'action': data['action']}))\n"
    )
    result1 = invoke_binary(script, "action1")
    result2 = invoke_binary(script, "action2")
    assert result1["action"] == "action1"
    assert result2["action"] == "action2"


def test_invoke_binary_binary_not_found(tmp_path):
    binary = tmp_path / "nonexistent.py"
    with pytest.raises(FileNotFoundError):
        invoke_binary(binary, "ping")


@NT_SKIP
def test_invoke_binary_permission_denied(tmp_path):
    script = tmp_path / "handler.py"
    script.write_text("import sys, json; print(json.dumps({'ok': True}))\n")
    script.chmod(0o000)
    if script.exists():
        try:
            with pytest.raises(PermissionError):
                invoke_binary(script, "ping")
        finally:
            script.chmod(0o644)
