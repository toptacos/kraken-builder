from pathlib import Path
from types import SimpleNamespace

import sys

import pytest

from kraken.core import runner
from kraken.core.hooks import HookAbort
from kraken.core.license import LicenseError
from kraken.core.runner import (
    DEFAULT_TIMEOUT_SEC,
    MAX_TIMEOUT_SEC,
    _default_action,
    _hook_patch,
    _invoke_one,
    _resolve_binary,
    in_process_registry,
    list_all,
    run_named,
    tentacle_timeout,
)


def _arm(name="arm1", version="1.0.0", actions=None, **raw_extra):
    raw = {"name": name, "version": version, "entrypoint": "mod:handle"}
    raw.update(raw_extra)
    return SimpleNamespace(
        name=name,
        version=version,
        actions=actions or [],
        raw=raw,
        invoke=lambda action, payload=None: {
            "ok": True,
            "name": name,
            "action": action,
        },
    )


def _patch_runner(monkeypatch, arms=None, config=None, specs=None, installed=None):
    monkeypatch.setattr(runner, "load_arms", lambda roots: arms or [])
    monkeypatch.setattr(
        runner, "load_config", lambda root: config if config is not None else {}
    )
    monkeypatch.setattr(
        runner,
        "spec_by_name",
        lambda root, name, home=None: (specs or {}).get(name),
    )
    monkeypatch.setattr(runner, "discover_installed", lambda home=None: installed or [])
    monkeypatch.setattr(runner, "assert_licensed", lambda name, spec: None)
    monkeypatch.setattr(runner, "fire_hooks", lambda *a, **kw: [])
    monkeypatch.setattr(runner, "emit", lambda event, payload: None)
    monkeypatch.setattr(
        runner,
        "resolve",
        lambda root, name, home=None: SimpleNamespace(order=[name]),
    )


def test_in_process_registry_loads_arms(tmp_path, monkeypatch):
    arms = [_arm("alpha"), _arm("beta")]
    monkeypatch.setattr(runner, "load_arms", lambda roots: arms)
    reg = in_process_registry(tmp_path)
    assert reg.names() == ["alpha", "beta"]


def test_in_process_registry_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "load_arms", lambda roots: [])
    reg = in_process_registry(tmp_path)
    assert reg.names() == []


def test_resolve_binary_no_binary_key(tmp_path):
    with pytest.raises(FileNotFoundError, match="has no binary"):
        _resolve_binary(tmp_path, {"name": "x"})


def test_resolve_binary_none_binary(tmp_path):
    with pytest.raises(FileNotFoundError, match="has no binary"):
        _resolve_binary(tmp_path, {"name": "x", "binary": None})


def test_resolve_binary_absolute_path(tmp_path):
    p = tmp_path / "tool"
    p.write_text("#!/bin/sh\n")
    result = _resolve_binary(tmp_path, {"binary": str(p)})
    assert result == p


def test_resolve_binary_relative_in_root(tmp_path):
    (tmp_path / "bin").write_text("#!/bin/sh\n")
    result = _resolve_binary(tmp_path, {"binary": "bin"})
    assert result == (tmp_path / "bin").resolve()


def test_resolve_binary_relative_in_cwd(tmp_path, monkeypatch):
    (tmp_path / "cwd_bin").write_text("#!/bin/sh\n")
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "other"
    root.mkdir()
    result = _resolve_binary(root, {"binary": "cwd_bin"})
    assert result == (tmp_path / "cwd_bin").resolve()


def test_resolve_binary_relative_in_spec_root(tmp_path):
    spec_root = tmp_path / "spec_root"
    spec_root.mkdir()
    (spec_root / "tool").write_text("#!/bin/sh\n")
    root = tmp_path / "root"
    root.mkdir()
    result = _resolve_binary(root, {"binary": "tool", "_root": str(spec_root)})
    assert result == (spec_root / "tool").resolve()


def test_resolve_binary_not_found_returns_root_path(tmp_path):
    result = _resolve_binary(tmp_path, {"binary": "missing"})
    assert result == (tmp_path / "missing").resolve()


def test_tentacle_timeout_none_returns_default():
    assert tentacle_timeout({}) == DEFAULT_TIMEOUT_SEC


def test_tentacle_timeout_explicit_none_returns_default():
    assert tentacle_timeout({"timeout_sec": None}) == DEFAULT_TIMEOUT_SEC


def test_tentacle_timeout_valid_value():
    assert tentacle_timeout({"timeout_sec": 60}) == 60


def test_tentacle_timeout_clamped_to_max():
    assert tentacle_timeout({"timeout_sec": 9999}) == MAX_TIMEOUT_SEC


def test_tentacle_timeout_clamped_to_min():
    assert tentacle_timeout({"timeout_sec": 0}) == 1


def test_tentacle_timeout_negative_clamped_to_min():
    assert tentacle_timeout({"timeout_sec": -5}) == 1


def test_tentacle_timeout_string_number():
    assert tentacle_timeout({"timeout_sec": "45"}) == 45


def test_tentacle_timeout_invalid_string_returns_default():
    assert tentacle_timeout({"timeout_sec": "abc"}) == DEFAULT_TIMEOUT_SEC


def test_tentacle_timeout_list_returns_default():
    assert tentacle_timeout({"timeout_sec": [1]}) == DEFAULT_TIMEOUT_SEC


def test_tentacle_timeout_dict_returns_default():
    assert tentacle_timeout({"timeout_sec": {"x": 1}}) == DEFAULT_TIMEOUT_SEC


def test_tentacle_timeout_float_string_returns_default():
    assert tentacle_timeout({"timeout_sec": "1.5"}) == DEFAULT_TIMEOUT_SEC


def test_invoke_one_in_process(tmp_path, monkeypatch):
    arms = [_arm("myarm", actions=["go"])]
    _patch_runner(monkeypatch, arms=arms)
    result = _invoke_one(tmp_path, "myarm", "go", {"x": 1})
    assert result == {"ok": True, "name": "myarm", "action": "go"}


def test_invoke_one_in_process_license_check(tmp_path, monkeypatch):
    arms = [_arm("paid", license="premium")]
    _patch_runner(monkeypatch, arms=arms)
    monkeypatch.setattr(
        runner,
        "assert_licensed",
        lambda name, spec: (_ for _ in ()).throw(LicenseError("no license")),
    )
    with pytest.raises(LicenseError):
        _invoke_one(tmp_path, "paid", "go", None)


def test_invoke_one_binary(tmp_path, monkeypatch):
    # The binary has to exist on the machine running the test; /usr/bin/true
    # is a POSIX path and Windows turns it into C:\usr\bin\true.
    _patch_runner(
        monkeypatch,
        specs={"ext": {"name": "ext", "binary": sys.executable}},
    )
    monkeypatch.setattr(
        runner,
        "invoke_binary",
        lambda binary, action, payload, timeout=30: {"ok": True},
    )
    result = _invoke_one(tmp_path, "ext", "run", None)
    assert result == {"ok": True}


def test_invoke_one_binary_passes_timeout(tmp_path, monkeypatch):
    _patch_runner(
        monkeypatch,
        specs={"ext": {"name": "ext", "binary": "/usr/bin/true", "timeout_sec": 10}},
    )
    captured = {}

    def fake_invoke(binary, action, payload, timeout=30):
        captured["timeout"] = timeout
        return {"ok": True}

    monkeypatch.setattr(runner, "invoke_binary", fake_invoke)
    _invoke_one(tmp_path, "ext", "run", None)
    assert captured["timeout"] == 10


def test_invoke_one_binary_missing_file(tmp_path, monkeypatch):
    _patch_runner(
        monkeypatch,
        specs={"ext": {"name": "ext", "binary": "/nonexistent/bin"}},
    )
    with pytest.raises(FileNotFoundError, match="binary missing"):
        _invoke_one(tmp_path, "ext", "run", None)


def test_invoke_one_not_found(tmp_path, monkeypatch):
    _patch_runner(monkeypatch)
    with pytest.raises(KeyError, match="arm not loaded"):
        _invoke_one(tmp_path, "ghost", "run", None)


def test_invoke_one_binary_license_check(tmp_path, monkeypatch):
    _patch_runner(
        monkeypatch,
        specs={
            "paid": {"name": "paid", "binary": "/usr/bin/true", "license": "premium"}
        },
    )
    monkeypatch.setattr(
        runner,
        "assert_licensed",
        lambda name, spec: (_ for _ in ()).throw(LicenseError("no license")),
    )
    with pytest.raises(LicenseError):
        _invoke_one(tmp_path, "paid", "run", None)


def test_default_action_in_process_with_actions(tmp_path, monkeypatch):
    arms = [_arm("a", actions=["deploy", "rollback"])]
    _patch_runner(monkeypatch, arms=arms)
    assert _default_action(tmp_path, "a") == "deploy"


def test_default_action_in_process_no_actions(tmp_path, monkeypatch):
    arms = [_arm("a", actions=[])]
    _patch_runner(monkeypatch, arms=arms)
    assert _default_action(tmp_path, "a") == "ping"


def test_default_action_spec_with_actions(tmp_path, monkeypatch):
    _patch_runner(monkeypatch, specs={"b": {"name": "b", "actions": ["build", "test"]}})
    assert _default_action(tmp_path, "b") == "build"


def test_default_action_spec_no_actions(tmp_path, monkeypatch):
    _patch_runner(monkeypatch, specs={"b": {"name": "b"}})
    assert _default_action(tmp_path, "b") == "ping"


def test_default_action_spec_empty_actions(tmp_path, monkeypatch):
    _patch_runner(monkeypatch, specs={"b": {"name": "b", "actions": []}})
    assert _default_action(tmp_path, "b") == "ping"


def test_default_action_no_spec(tmp_path, monkeypatch):
    _patch_runner(monkeypatch)
    assert _default_action(tmp_path, "ghost") == "ping"


def test_run_named_in_process_success(tmp_path, monkeypatch):
    arms = [_arm("a", actions=["go"])]
    _patch_runner(monkeypatch, arms=arms)
    result = run_named(tmp_path, "a", "go", {"k": "v"})
    assert result == {"ok": True, "name": "a", "action": "go"}


def test_run_named_binary_success(tmp_path, monkeypatch):
    _patch_runner(
        monkeypatch,
        specs={"ext": {"name": "ext", "binary": "/usr/bin/true"}},
    )
    monkeypatch.setattr(
        runner,
        "invoke_binary",
        lambda binary, action, payload, timeout=30: {"ok": True, "v": 1},
    )
    result = run_named(tmp_path, "ext", "run")
    assert result == {"ok": True, "v": 1}


def test_run_named_emits_run_event(tmp_path, monkeypatch):
    arms = [_arm("a")]
    _patch_runner(monkeypatch, arms=arms)
    emitted = []
    monkeypatch.setattr(
        runner, "emit", lambda event, payload: emitted.append((event, payload))
    )
    run_named(tmp_path, "a", "go")
    assert emitted == [("run", {"name": "a", "action": "go", "ok": True})]


def test_run_named_emits_run_event_not_ok(tmp_path, monkeypatch):
    arms = [_arm("a")]
    _patch_runner(monkeypatch, arms=arms)
    monkeypatch.setattr(
        runner,
        "load_arms",
        lambda roots: [
            SimpleNamespace(
                name="a",
                version="1",
                actions=["go"],
                raw={"name": "a"},
                invoke=lambda action, payload=None: {"ok": False},
            )
        ],
    )
    emitted = []
    monkeypatch.setattr(
        runner, "emit", lambda event, payload: emitted.append((event, payload))
    )
    run_named(tmp_path, "a", "go")
    assert emitted == [("run", {"name": "a", "action": "go", "ok": False})]


def test_run_named_before_run_hook_fires(tmp_path, monkeypatch):
    arms = [_arm("a")]
    _patch_runner(monkeypatch, arms=arms)
    calls = []
    monkeypatch.setattr(
        runner,
        "fire_hooks",
        lambda root, event, name, ctx, invoke: calls.append((event, name)) or [],
    )
    run_named(tmp_path, "a", "go")
    assert ("before_run", "a") in calls


def test_run_named_before_run_hook_abort(tmp_path, monkeypatch):
    arms = [_arm("a")]
    _patch_runner(monkeypatch, arms=arms)

    def abort_hooks(root, event, name, ctx, invoke):
        if event == "before_run":
            raise HookAbort("blocked")
        return []

    monkeypatch.setattr(runner, "fire_hooks", abort_hooks)
    with pytest.raises(HookAbort):
        run_named(tmp_path, "a", "go")


def test_run_named_on_error_hook_fires(tmp_path, monkeypatch):
    _patch_runner(monkeypatch)
    calls = []
    monkeypatch.setattr(
        runner,
        "fire_hooks",
        lambda root, event, name, ctx, invoke: calls.append(event) or [],
    )
    with pytest.raises(KeyError):
        run_named(tmp_path, "ghost", "go")
    assert "on_error" in calls


def test_run_named_on_error_hook_not_fires_when_in_hook(tmp_path, monkeypatch):
    _patch_runner(monkeypatch)
    runner._IN_HOOK = True
    calls = []
    monkeypatch.setattr(
        runner,
        "fire_hooks",
        lambda root, event, name, ctx, invoke: calls.append(event) or [],
    )
    try:
        with pytest.raises(KeyError):
            run_named(tmp_path, "ghost", "go")
        assert "on_error" not in calls
    finally:
        runner._IN_HOOK = False


def test_run_named_after_run_hook_fires(tmp_path, monkeypatch):
    arms = [_arm("a")]
    _patch_runner(monkeypatch, arms=arms)
    calls = []
    monkeypatch.setattr(
        runner,
        "fire_hooks",
        lambda root, event, name, ctx, invoke: calls.append(event) or [],
    )
    run_named(tmp_path, "a", "go")
    assert "after_run" in calls


def test_run_named_after_run_hook_not_fires_when_in_hook(tmp_path, monkeypatch):
    arms = [_arm("a")]
    _patch_runner(monkeypatch, arms=arms)
    runner._IN_HOOK = True
    calls = []
    monkeypatch.setattr(
        runner,
        "fire_hooks",
        lambda root, event, name, ctx, invoke: calls.append(event) or [],
    )
    try:
        run_named(tmp_path, "a", "go")
        assert "after_run" not in calls
    finally:
        runner._IN_HOOK = False


def test_run_named_compose_with_deps(tmp_path, monkeypatch):
    arms = [_arm("main"), _arm("dep1"), _arm("dep2")]
    _patch_runner(monkeypatch, arms=arms)
    monkeypatch.setattr(
        runner,
        "resolve",
        lambda root, name, home=None: SimpleNamespace(order=["dep1", "dep2", "main"]),
    )
    invoked = []
    original_invoke = _invoke_one

    def tracking_invoke(root, name, action, payload, home=None):
        invoked.append(name)
        return original_invoke(root, name, action, payload, home)

    monkeypatch.setattr(runner, "_invoke_one", tracking_invoke)
    result = run_named(tmp_path, "main", "go", compose=True)
    assert "dep1" in invoked
    assert "dep2" in invoked
    assert result["ok"] is True


def test_run_named_compose_single_dep_no_deps(tmp_path, monkeypatch):
    arms = [_arm("main")]
    _patch_runner(monkeypatch, arms=arms)
    invoked = []
    monkeypatch.setattr(
        runner,
        "_invoke_one",
        lambda root, name, action, payload, home=None: (
            invoked.append(name) or {"ok": True}
        ),
    )
    run_named(tmp_path, "main", "go", compose=True)
    assert invoked == ["main"]


def test_run_named_compose_deps_get_default_action(tmp_path, monkeypatch):
    arms = [_arm("main"), _arm("dep1", actions=["build"])]
    _patch_runner(monkeypatch, arms=arms)
    monkeypatch.setattr(
        runner,
        "resolve",
        lambda root, name, home=None: SimpleNamespace(order=["dep1", "main"]),
    )
    actions = []

    def tracking_invoke(root, name, action, payload, home=None):
        if name == "dep1":
            actions.append(action)
        return {"ok": True}

    monkeypatch.setattr(runner, "_invoke_one", tracking_invoke)
    run_named(tmp_path, "main", "go", compose=True)
    assert actions == ["build"]


def test_run_named_compose_deps_passed_via_deps_key(tmp_path, monkeypatch):
    arms = [_arm("main"), _arm("dep1")]
    _patch_runner(monkeypatch, arms=arms)
    monkeypatch.setattr(
        runner,
        "resolve",
        lambda root, name, home=None: SimpleNamespace(order=["dep1", "main"]),
    )
    captured_payload = {}

    def fake_invoke(root, name, action, payload, home=None):
        if name == "main":
            captured_payload.update(payload)
        return {"ok": True}

    monkeypatch.setattr(runner, "_invoke_one", fake_invoke)
    run_named(tmp_path, "main", "go", compose=True)
    assert "_deps" in captured_payload
    assert "dep1" in captured_payload["_deps"]


def test_run_named_after_run_hook_with_patch_and_finish(tmp_path, monkeypatch):
    arms = [_arm("a", actions=["go", "finish"])]
    _patch_runner(
        monkeypatch,
        arms=arms,
        specs={"a": {"name": "a", "actions": ["go", "finish"]}},
    )
    monkeypatch.setattr(
        runner,
        "fire_hooks",
        lambda root, event, name, ctx, invoke: (
            [{"result": {"result": {"patch": {"k": "v"}}}}]
            if event == "after_run"
            else []
        ),
    )
    result = run_named(tmp_path, "a", "go")
    assert result.get("finished") is True
    assert result.get("_hooks") == [{"result": {"result": {"patch": {"k": "v"}}}}]


def test_run_named_after_run_hook_with_patch_no_finish_action(tmp_path, monkeypatch):
    arms = [_arm("a", actions=["go"])]
    _patch_runner(monkeypatch, arms=arms)
    monkeypatch.setattr(
        runner,
        "fire_hooks",
        lambda root, event, name, ctx, invoke: (
            [{"result": {"result": {"patch": {"k": "v"}}}}]
            if event == "after_run"
            else []
        ),
    )
    result = run_named(tmp_path, "a", "go")
    assert "finished" not in result


def test_run_named_after_run_hook_with_patch_action_is_finish(tmp_path, monkeypatch):
    arms = [_arm("a", actions=["go", "finish"])]
    _patch_runner(monkeypatch, arms=arms)
    monkeypatch.setattr(
        runner,
        "fire_hooks",
        lambda root, event, name, ctx, invoke: (
            [{"result": {"result": {"patch": {"k": "v"}}}}]
            if event == "after_run"
            else []
        ),
    )
    result = run_named(tmp_path, "a", "finish")
    assert "finished" not in result


def test_run_named_after_run_hook_no_patch(tmp_path, monkeypatch):
    arms = [_arm("a", actions=["go", "finish"])]
    _patch_runner(monkeypatch, arms=arms)
    monkeypatch.setattr(
        runner,
        "fire_hooks",
        lambda root, event, name, ctx, invoke: (
            [{"result": {"result": {}}}] if event == "after_run" else []
        ),
    )
    result = run_named(tmp_path, "a", "go")
    assert "finished" not in result


def test_run_named_after_run_hook_result_not_dict(tmp_path, monkeypatch):
    arms = [_arm("a")]
    _patch_runner(monkeypatch, arms=arms)
    monkeypatch.setattr(
        runner,
        "fire_hooks",
        lambda root, event, name, ctx, invoke: (
            [{"result": {"result": {"patch": {"k": "v"}}}}]
            if event == "after_run"
            else []
        ),
    )
    monkeypatch.setattr(
        runner,
        "load_arms",
        lambda roots: [
            SimpleNamespace(
                name="a",
                version="1",
                actions=["go"],
                raw={"name": "a"},
                invoke=lambda action, payload=None: "not-a-dict",
            )
        ],
    )
    with pytest.raises(AttributeError):
        run_named(tmp_path, "a", "go")


def test_run_named_exception_propagates(tmp_path, monkeypatch):
    _patch_runner(monkeypatch)
    with pytest.raises(KeyError):
        run_named(tmp_path, "ghost", "go")


def test_run_named_payload_none_becomes_empty_dict(tmp_path, monkeypatch):
    arms = [_arm("a")]
    _patch_runner(monkeypatch, arms=arms)
    captured = {}

    def fake_invoke(root, name, action, payload, home=None):
        captured["payload"] = payload
        return {"ok": True}

    monkeypatch.setattr(runner, "_invoke_one", fake_invoke)
    run_named(tmp_path, "a", "go", None)
    assert captured["payload"] == {}


def test_run_named_payload_passthrough(tmp_path, monkeypatch):
    arms = [_arm("a")]
    _patch_runner(monkeypatch, arms=arms)
    captured = {}

    def fake_invoke(root, name, action, payload, home=None):
        captured["payload"] = payload
        return {"ok": True}

    monkeypatch.setattr(runner, "_invoke_one", fake_invoke)
    run_named(tmp_path, "a", "go", {"x": 1})
    assert captured["payload"] == {"x": 1}


def test_hook_patch_empty():
    assert _hook_patch([]) == {}


def test_hook_patch_with_patch():
    hooks = [{"result": {"result": {"patch": {"a": 1}}}}]
    assert _hook_patch(hooks) == {"a": 1}


def test_hook_patch_multiple_patches_merge():
    hooks = [
        {"result": {"result": {"patch": {"a": 1}}}},
        {"result": {"result": {"patch": {"b": 2}}}},
    ]
    assert _hook_patch(hooks) == {"a": 1, "b": 2}


def test_hook_patch_later_patch_overrides():
    hooks = [
        {"result": {"result": {"patch": {"a": 1}}}},
        {"result": {"result": {"patch": {"a": 2}}}},
    ]
    assert _hook_patch(hooks) == {"a": 2}


def test_hook_patch_no_patch_key():
    hooks = [{"result": {"result": {}}}]
    assert _hook_patch(hooks) == {}


def test_hook_patch_result_none():
    hooks = [{"result": None}]
    assert _hook_patch(hooks) == {}


def test_hook_patch_inner_not_dict():
    hooks = [{"result": {"result": "not-a-dict"}}]
    assert _hook_patch(hooks) == {}


def test_hook_patch_patch_not_dict():
    hooks = [{"result": {"result": {"patch": "not-a-dict"}}}]
    assert _hook_patch(hooks) == {}


def test_list_all_empty(tmp_path, monkeypatch):
    _patch_runner(monkeypatch)
    assert list_all(tmp_path) == []


def test_list_all_in_process_only(tmp_path, monkeypatch):
    arms = [_arm("alpha", version="2.0.0", actions=["go"], license="free")]
    _patch_runner(monkeypatch, arms=arms)
    rows = list_all(tmp_path)
    assert len(rows) == 1
    assert rows[0]["name"] == "alpha"
    assert rows[0]["version"] == "2.0.0"
    assert rows[0]["actions"] == ["go"]
    assert rows[0]["kind"] == "in-process"
    assert rows[0]["license"] == "free"
    assert rows[0]["platforms"] == ["any"]
    assert rows[0]["needs_docker"] is False


def test_list_all_in_process_defaults(tmp_path, monkeypatch):
    arms = [_arm("a")]
    _patch_runner(monkeypatch, arms=arms)
    rows = list_all(tmp_path)
    assert rows[0]["license"] == "free"
    assert rows[0]["platforms"] == ["any"]
    assert rows[0]["needs_docker"] is False


def test_list_all_in_process_with_platforms_and_docker(tmp_path, monkeypatch):
    arms = [_arm("a", platforms=["linux", "macos"], needs_docker=True)]
    _patch_runner(monkeypatch, arms=arms)
    rows = list_all(tmp_path)
    assert rows[0]["platforms"] == ["linux", "macos"]
    assert rows[0]["needs_docker"] is True


def test_list_all_config_tentacles(tmp_path, monkeypatch):
    _patch_runner(
        monkeypatch,
        config={
            "tentacles": [
                {
                    "name": "ext1",
                    "version": "1.0",
                    "binary": "/bin/true",
                    "actions": ["run"],
                }
            ]
        },
    )
    rows = list_all(tmp_path)
    assert len(rows) == 1
    assert rows[0]["name"] == "ext1"
    assert rows[0]["kind"] == "binary"
    assert rows[0]["binary"] == "/bin/true"


def test_list_all_installed_tentacles(tmp_path, monkeypatch):
    _patch_runner(
        monkeypatch,
        installed=[{"name": "inst1", "version": "0.1", "binary": "/usr/bin/false"}],
    )
    rows = list_all(tmp_path)
    assert len(rows) == 1
    assert rows[0]["name"] == "inst1"
    assert rows[0]["kind"] == "binary"


def test_list_all_mixed_sources(tmp_path, monkeypatch):
    arms = [_arm("local")]
    _patch_runner(
        monkeypatch,
        arms=arms,
        config={"tentacles": [{"name": "cfg1", "binary": "/bin/true"}]},
        installed=[{"name": "inst1", "binary": "/bin/false"}],
    )
    rows = list_all(tmp_path)
    names = [r["name"] for r in rows]
    assert names == ["local", "cfg1", "inst1"]


def test_list_all_dedup_in_process_wins(tmp_path, monkeypatch):
    arms = [_arm("dup", version="2.0")]
    _patch_runner(
        monkeypatch,
        arms=arms,
        config={
            "tentacles": [{"name": "dup", "version": "1.0", "binary": "/bin/true"}]
        },
    )
    rows = list_all(tmp_path)
    assert len(rows) == 1
    assert rows[0]["version"] == "2.0"
    assert rows[0]["kind"] == "in-process"


def test_list_all_dedup_config_wins_over_installed(tmp_path, monkeypatch):
    _patch_runner(
        monkeypatch,
        config={"tentacles": [{"name": "dup", "binary": "/bin/true"}]},
        installed=[{"name": "dup", "binary": "/bin/false"}],
    )
    rows = list_all(tmp_path)
    assert len(rows) == 1
    assert rows[0]["binary"] == "/bin/true"


def test_list_all_skips_spec_without_name(tmp_path, monkeypatch):
    _patch_runner(
        monkeypatch,
        config={"tentacles": [{"binary": "/bin/true"}, {"name": "valid"}]},
    )
    rows = list_all(tmp_path)
    assert len(rows) == 1
    assert rows[0]["name"] == "valid"


def test_list_all_tentacle_defaults(tmp_path, monkeypatch):
    _patch_runner(
        monkeypatch,
        config={"tentacles": [{"name": "x"}]},
    )
    rows = list_all(tmp_path)
    assert rows[0]["version"] == ""
    assert rows[0]["actions"] == []
    assert rows[0]["license"] == "free"
    assert rows[0]["platforms"] == ["any"]
    assert rows[0]["needs_docker"] is False


def test_list_all_tentacle_with_all_fields(tmp_path, monkeypatch):
    _patch_runner(
        monkeypatch,
        config={
            "tentacles": [
                {
                    "name": "x",
                    "version": "3.0",
                    "binary": "/bin/x",
                    "actions": ["a", "b"],
                    "license": "premium",
                    "platforms": ["linux"],
                    "needs_docker": True,
                }
            ]
        },
    )
    rows = list_all(tmp_path)
    assert rows[0]["version"] == "3.0"
    assert rows[0]["actions"] == ["a", "b"]
    assert rows[0]["license"] == "premium"
    assert rows[0]["platforms"] == ["linux"]
    assert rows[0]["needs_docker"] is True


def test_list_all_home_passed_to_discover(tmp_path, monkeypatch):
    captured = {}

    def fake_discover(home=None):
        captured["home"] = home
        return []

    _patch_runner(monkeypatch)
    monkeypatch.setattr(runner, "discover_installed", fake_discover)
    list_all(tmp_path, home=Path("/custom/home"))
    assert captured["home"] == Path("/custom/home")


def test_run_named_home_passed_through(tmp_path, monkeypatch):
    arms = [_arm("a")]
    _patch_runner(monkeypatch, arms=arms)
    captured = {}

    def fake_resolve(root, name, home=None):
        captured["home"] = home
        return SimpleNamespace(order=[name])

    monkeypatch.setattr(runner, "resolve", fake_resolve)
    run_named(tmp_path, "a", "go", home=Path("/h"))
    assert captured["home"] == Path("/h")


def test_run_named_invoke_receives_home(tmp_path, monkeypatch):
    arms = [_arm("a")]
    _patch_runner(monkeypatch, arms=arms)
    captured = {}

    def fake_invoke(root, name, action, payload, home=None):
        captured["home"] = home
        return {"ok": True}

    monkeypatch.setattr(runner, "_invoke_one", fake_invoke)
    run_named(tmp_path, "a", "go", home=Path("/h"))
    assert captured["home"] == Path("/h")


def test_run_named_after_run_finish_receives_payload_and_patch(tmp_path, monkeypatch):
    arms = [_arm("a", actions=["go", "finish"])]
    _patch_runner(
        monkeypatch,
        arms=arms,
        specs={"a": {"name": "a", "actions": ["go", "finish"]}},
    )
    monkeypatch.setattr(
        runner,
        "fire_hooks",
        lambda root, event, name, ctx, invoke: (
            [{"result": {"result": {"patch": {"k": "v"}}}}]
            if event == "after_run"
            else []
        ),
    )
    captured = {}

    def fake_invoke(root, name, action, payload, home=None):
        if action == "finish":
            captured.update(payload)
        return {"ok": True, "result": "done"}

    monkeypatch.setattr(runner, "_invoke_one", fake_invoke)
    run_named(tmp_path, "a", "go", {"orig": 1})
    assert captured.get("patch") == {"k": "v"}
    assert captured.get("orig") == 1


def test_run_named_after_run_finish_result_used(tmp_path, monkeypatch):
    arms = [_arm("a", actions=["go", "finish"])]
    _patch_runner(
        monkeypatch,
        arms=arms,
        specs={"a": {"name": "a", "actions": ["go", "finish"]}},
    )
    monkeypatch.setattr(
        runner,
        "fire_hooks",
        lambda root, event, name, ctx, invoke: (
            [{"result": {"result": {"patch": {"k": "v"}}}}]
            if event == "after_run"
            else []
        ),
    )

    def fake_invoke(root, name, action, payload, home=None):
        if action == "finish":
            return {"ok": True, "result": "finished-result"}
        return {"ok": True, "result": "original"}

    monkeypatch.setattr(runner, "_invoke_one", fake_invoke)
    result = run_named(tmp_path, "a", "go")
    assert result["result"] == "finished-result"
    assert result["finished"] is True


def test_run_named_after_run_finish_no_result_key(tmp_path, monkeypatch):
    arms = [_arm("a", actions=["go", "finish"])]
    _patch_runner(
        monkeypatch,
        arms=arms,
        specs={"a": {"name": "a", "actions": ["go", "finish"]}},
    )
    monkeypatch.setattr(
        runner,
        "fire_hooks",
        lambda root, event, name, ctx, invoke: (
            [{"result": {"result": {"patch": {"k": "v"}}}}]
            if event == "after_run"
            else []
        ),
    )

    def fake_invoke(root, name, action, payload, home=None):
        if action == "finish":
            return {"ok": True}
        return {"ok": True, "result": "original"}

    monkeypatch.setattr(runner, "_invoke_one", fake_invoke)
    result = run_named(tmp_path, "a", "go")
    assert result["result"] == {"ok": True}
    assert result["finished"] is True


def test_run_named_in_hook_flag_reset_on_exception(tmp_path, monkeypatch):
    _patch_runner(monkeypatch)
    runner._IN_HOOK = False
    with pytest.raises(KeyError):
        run_named(tmp_path, "ghost", "go")
    assert runner._IN_HOOK is False


def test_run_named_in_hook_flag_reset_after_success(tmp_path, monkeypatch):
    arms = [_arm("a")]
    _patch_runner(monkeypatch, arms=arms)
    runner._IN_HOOK = False
    run_named(tmp_path, "a", "go")
    assert runner._IN_HOOK is False


def test_run_named_after_run_hook_exception_propagates(tmp_path, monkeypatch):
    arms = [_arm("a")]
    _patch_runner(monkeypatch, arms=arms)

    def bad_hooks(root, event, name, ctx, invoke):
        if event == "after_run":
            raise RuntimeError("hook boom")
        return []

    monkeypatch.setattr(runner, "fire_hooks", bad_hooks)
    with pytest.raises(RuntimeError, match="hook boom"):
        run_named(tmp_path, "a", "go")


def test_run_named_before_run_hook_exception_propagates(tmp_path, monkeypatch):
    arms = [_arm("a")]
    _patch_runner(monkeypatch, arms=arms)

    def bad_hooks(root, event, name, ctx, invoke):
        if event == "before_run":
            raise RuntimeError("before boom")
        return []

    monkeypatch.setattr(runner, "fire_hooks", bad_hooks)
    with pytest.raises(RuntimeError, match="before boom"):
        run_named(tmp_path, "a", "go")


def test_run_named_on_error_hook_exception_propagates(tmp_path, monkeypatch):
    _patch_runner(monkeypatch)

    def bad_hooks(root, event, name, ctx, invoke):
        if event == "on_error":
            raise RuntimeError("error hook boom")
        return []

    monkeypatch.setattr(runner, "fire_hooks", bad_hooks)
    with pytest.raises(RuntimeError, match="error hook boom"):
        run_named(tmp_path, "ghost", "go")


def test_run_named_compose_false_no_deps(tmp_path, monkeypatch):
    arms = [_arm("main"), _arm("dep1")]
    _patch_runner(monkeypatch, arms=arms)
    monkeypatch.setattr(
        runner,
        "resolve",
        lambda root, name, home=None: SimpleNamespace(order=["dep1", "main"]),
    )
    invoked = []
    monkeypatch.setattr(
        runner,
        "_invoke_one",
        lambda root, name, action, payload, home=None: (
            invoked.append(name) or {"ok": True}
        ),
    )
    run_named(tmp_path, "main", "go", compose=False)
    assert invoked == ["main"]


def test_run_named_result_dict_copy_on_hooks(tmp_path, monkeypatch):
    arms = [_arm("a")]
    _patch_runner(monkeypatch, arms=arms)
    monkeypatch.setattr(
        runner,
        "fire_hooks",
        lambda root, event, name, ctx, invoke: (
            [{"result": {"result": {}}}] if event == "after_run" else []
        ),
    )
    result = run_named(tmp_path, "a", "go")
    assert "_hooks" in result


def test_run_named_no_hooks_key_when_no_after_run_hooks(tmp_path, monkeypatch):
    arms = [_arm("a")]
    _patch_runner(monkeypatch, arms=arms)
    result = run_named(tmp_path, "a", "go")
    assert "_hooks" not in result
