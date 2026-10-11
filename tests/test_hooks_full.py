from pathlib import Path
from types import SimpleNamespace

import pytest

from kraken.core.hooks import HookAbort, collect_hooks, fire_hooks


def _patch_hooks(monkeypatch, config=None, spec=None, nodes=None):
    monkeypatch.setattr(
        "kraken.core.hooks.load_config",
        lambda root: config if config is not None else {},
    )
    monkeypatch.setattr(
        "kraken.core.hooks.spec_by_name",
        lambda root, name: spec,
    )
    monkeypatch.setattr(
        "kraken.core.hooks.catalog",
        lambda root: nodes if nodes is not None else {},
    )
    monkeypatch.setattr("kraken.core.hooks.emit", lambda event, payload: None)


def _node(spec):
    return SimpleNamespace(spec=spec)


def test_matches_none_when_returns_true(monkeypatch):
    _patch_hooks(
        monkeypatch, config={"hooks": {"after_run": [{"tentacle": "a", "when": None}]}}
    )
    hooks = collect_hooks(Path("/x"), "after_run", "target")
    assert [h["tentacle"] for h in hooks] == ["a"]


def test_matches_empty_list_when_returns_true(monkeypatch):
    _patch_hooks(
        monkeypatch, config={"hooks": {"after_run": [{"tentacle": "a", "when": []}]}}
    )
    hooks = collect_hooks(Path("/x"), "after_run", "target")
    assert [h["tentacle"] for h in hooks] == ["a"]


def test_matches_star_matches_any_target(monkeypatch):
    _patch_hooks(
        monkeypatch, config={"hooks": {"after_run": [{"tentacle": "a", "when": "*"}]}}
    )
    hooks = collect_hooks(Path("/x"), "after_run", "anything")
    assert [h["tentacle"] for h in hooks] == ["a"]


def test_matches_string_when_matching_target(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "when": "geo"}]}},
    )
    hooks = collect_hooks(Path("/x"), "after_run", "geo")
    assert [h["tentacle"] for h in hooks] == ["a"]


def test_matches_string_when_not_matching_target(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "when": "geo"}]}},
    )
    hooks = collect_hooks(Path("/x"), "after_run", "other")
    assert hooks == []


def test_matches_list_when_contains_target(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "when": ["x", "geo"]}]}},
    )
    hooks = collect_hooks(Path("/x"), "after_run", "geo")
    assert [h["tentacle"] for h in hooks] == ["a"]


def test_matches_list_when_without_target(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "when": ["x", "y"]}]}},
    )
    hooks = collect_hooks(Path("/x"), "after_run", "geo")
    assert hooks == []


def test_collect_hooks_empty_config_returns_empty(monkeypatch):
    _patch_hooks(monkeypatch)
    assert collect_hooks(Path("/x"), "after_run", "target") == []


def test_collect_hooks_config_without_hooks_key(monkeypatch):
    _patch_hooks(monkeypatch, config={"version": 1})
    assert collect_hooks(Path("/x"), "after_run", "target") == []


def test_collect_hooks_event_not_in_config(monkeypatch):
    _patch_hooks(monkeypatch, config={"hooks": {"before_run": [{"tentacle": "a"}]}})
    assert collect_hooks(Path("/x"), "after_run", "target") == []


def test_collect_hooks_from_config(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "action": "ping"}]}},
    )
    hooks = collect_hooks(Path("/x"), "after_run", "target")
    assert hooks == [{"tentacle": "a", "action": "ping"}]


def test_collect_hooks_string_entry_becomes_dict(monkeypatch):
    _patch_hooks(monkeypatch, config={"hooks": {"after_run": ["a"]}})
    hooks = collect_hooks(Path("/x"), "after_run", "target")
    assert hooks == [{"tentacle": "a", "action": "ping"}]


def test_collect_hooks_skips_self_reference(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={
            "hooks": {"after_run": [{"tentacle": "target"}, {"tentacle": "other"}]}
        },
    )
    hooks = collect_hooks(Path("/x"), "after_run", "target")
    assert [h["tentacle"] for h in hooks] == ["other"]


def test_collect_hooks_from_spec_by_name(monkeypatch):
    _patch_hooks(
        monkeypatch,
        spec={"hooks": {"after_run": [{"tentacle": "spec-hook"}]}},
    )
    hooks = collect_hooks(Path("/x"), "after_run", "target")
    assert [h["tentacle"] for h in hooks] == ["spec-hook"]


def test_collect_hooks_merges_catalog_node_spec(monkeypatch):
    _patch_hooks(
        monkeypatch,
        nodes={"target": _node({"hooks": {"after_run": [{"tentacle": "cat-hook"}]}})},
    )
    hooks = collect_hooks(Path("/x"), "after_run", "target")
    assert [h["tentacle"] for h in hooks] == ["cat-hook"]


def test_collect_hooks_spec_overrides_catalog(monkeypatch):
    _patch_hooks(
        monkeypatch,
        spec={"hooks": {"after_run": [{"tentacle": "spec-hook"}]}},
        nodes={"target": _node({"hooks": {"after_run": [{"tentacle": "cat-hook"}]}})},
    )
    hooks = collect_hooks(Path("/x"), "after_run", "target")
    assert [h["tentacle"] for h in hooks] == ["spec-hook"]


def test_collect_hooks_combines_config_and_spec(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "cfg"}]}},
        spec={"hooks": {"after_run": [{"tentacle": "spec"}]}},
    )
    hooks = collect_hooks(Path("/x"), "after_run", "target")
    assert {h["tentacle"] for h in hooks} == {"cfg", "spec"}


def test_collect_hooks_sorts_by_priority(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={
            "hooks": {
                "after_run": [
                    {"tentacle": "late", "priority": 50},
                    {"tentacle": "early", "priority": 1},
                    {"tentacle": "mid"},
                ]
            }
        },
    )
    hooks = collect_hooks(Path("/x"), "after_run", "target")
    assert [h["tentacle"] for h in hooks] == ["early", "late", "mid"]


def test_collect_hooks_invalid_priority_string_defaults_100(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={
            "hooks": {
                "after_run": [
                    {"tentacle": "p50", "priority": 50},
                    {"tentacle": "bad", "priority": "high"},
                ]
            }
        },
    )
    hooks = collect_hooks(Path("/x"), "after_run", "target")
    assert [h["tentacle"] for h in hooks] == ["p50", "bad"]


def test_collect_hooks_none_priority_defaults_100(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={
            "hooks": {
                "after_run": [
                    {"tentacle": "p50", "priority": 50},
                    {"tentacle": "nonepri", "priority": None},
                ]
            }
        },
    )
    hooks = collect_hooks(Path("/x"), "after_run", "target")
    assert [h["tentacle"] for h in hooks] == ["p50", "nonepri"]


def test_fire_hooks_empty_returns_empty(monkeypatch):
    _patch_hooks(monkeypatch)
    results = fire_hooks(Path("/x"), "after_run", "target", {}, lambda *a: {})
    assert results == []


def test_fire_hooks_success(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "action": "ping"}]}},
    )
    calls = []

    def invoke(root, name, action, payload):
        calls.append((root, name, action, payload))
        return {"ok": True}

    results = fire_hooks(Path("/x"), "after_run", "target", {}, invoke)
    assert results == [{"tentacle": "a", "ok": True, "result": {"ok": True}}]
    assert calls[0][1] == "a"
    assert calls[0][2] == "ping"


def test_fire_hooks_default_action_is_ping(monkeypatch):
    _patch_hooks(monkeypatch, config={"hooks": {"after_run": [{"tentacle": "a"}]}})
    actions = []

    def invoke(root, name, action, payload):
        actions.append(action)
        return {}

    fire_hooks(Path("/x"), "after_run", "target", {}, invoke)
    assert actions == ["ping"]


def test_fire_hooks_payload_contents(monkeypatch):
    _patch_hooks(monkeypatch, config={"hooks": {"after_run": [{"tentacle": "a"}]}})
    payloads = []

    def invoke(root, name, action, payload):
        payloads.append(payload)
        return {}

    fire_hooks(
        Path("/x"),
        "after_run",
        "target",
        {"action": "deploy", "ok": True, "result": {"x": 1}, "plan": ["p"]},
        invoke,
    )
    assert payloads == [
        {
            "hook": "after_run",
            "target": "target",
            "target_action": "deploy",
            "ok": True,
            "result": {"x": 1},
            "plan": ["p"],
        }
    ]


def test_fire_hooks_skips_hook_without_name(monkeypatch):
    _patch_hooks(monkeypatch, config={"hooks": {"after_run": [{"action": "ping"}]}})
    results = fire_hooks(Path("/x"), "after_run", "target", {}, lambda *a: {})
    assert results == []


def test_fire_hooks_if_condition_false_skips(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "if": "ok"}]}},
    )
    results = fire_hooks(
        Path("/x"), "after_run", "target", {"ok": False}, lambda *a: {}
    )
    assert results == [{"tentacle": "a", "ok": True, "skipped": True, "reason": "if"}]


def test_fire_hooks_if_condition_true_runs(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "if": "ok"}]}},
    )
    results = fire_hooks(
        Path("/x"), "after_run", "target", {"ok": True}, lambda *a: {"ok": True}
    )
    assert results == [{"tentacle": "a", "ok": True, "result": {"ok": True}}]


def test_fire_hooks_if_success_condition(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "if": "success"}]}},
    )
    results = fire_hooks(
        Path("/x"), "after_run", "target", {"ok": True}, lambda *a: {"ok": True}
    )
    assert results[0]["ok"] is True


def test_fire_hooks_if_not_ok_condition(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "if": "not_ok"}]}},
    )
    results = fire_hooks(
        Path("/x"), "after_run", "target", {"ok": False}, lambda *a: {"ok": True}
    )
    assert results[0]["ok"] is True


def test_fire_hooks_if_error_condition(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "if": "error"}]}},
    )
    results = fire_hooks(
        Path("/x"), "after_run", "target", {"ok": True}, lambda *a: {"ok": True}
    )
    assert results == [{"tentacle": "a", "ok": True, "skipped": True, "reason": "if"}]


def test_fire_hooks_if_action_match(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "if": "action=deploy"}]}},
    )
    results = fire_hooks(
        Path("/x"), "after_run", "target", {"action": "deploy"}, lambda *a: {"ok": True}
    )
    assert results[0]["ok"] is True


def test_fire_hooks_if_action_no_match(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "if": "action=deploy"}]}},
    )
    results = fire_hooks(
        Path("/x"), "after_run", "target", {"action": "ping"}, lambda *a: {}
    )
    assert results == [{"tentacle": "a", "ok": True, "skipped": True, "reason": "if"}]


def test_fire_hooks_if_action_falls_back_to_target_action(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "if": "action=deploy"}]}},
    )
    results = fire_hooks(
        Path("/x"),
        "after_run",
        "target",
        {"target_action": "deploy"},
        lambda *a: {"ok": True},
    )
    assert results[0]["ok"] is True


def test_fire_hooks_if_action_missing_in_context(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "if": "action=deploy"}]}},
    )
    results = fire_hooks(Path("/x"), "after_run", "target", {}, lambda *a: {})
    assert results == [{"tentacle": "a", "ok": True, "skipped": True, "reason": "if"}]


def test_fire_hooks_if_unknown_condition_runs(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "if": "whatever"}]}},
    )
    results = fire_hooks(Path("/x"), "after_run", "target", {}, lambda *a: {"ok": True})
    assert results[0]["ok"] is True


def test_fire_hooks_invoke_raises_optional_skips(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "optional": True}]}},
    )

    def invoke(root, name, action, payload):
        raise RuntimeError("boom")

    results = fire_hooks(Path("/x"), "after_run", "target", {}, invoke)
    assert results == [{"tentacle": "a", "ok": False, "skipped": True, "error": "boom"}]


def test_fire_hooks_invoke_raises_default_optional_skips(monkeypatch):
    _patch_hooks(monkeypatch, config={"hooks": {"after_run": [{"tentacle": "a"}]}})

    def invoke(root, name, action, payload):
        raise RuntimeError("boom")

    results = fire_hooks(Path("/x"), "after_run", "target", {}, invoke)
    assert results == [{"tentacle": "a", "ok": False, "skipped": True, "error": "boom"}]


def test_fire_hooks_invoke_raises_not_optional_before_run_aborts(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"before_run": [{"tentacle": "a", "optional": False}]}},
    )

    def invoke(root, name, action, payload):
        raise RuntimeError("boom")

    with pytest.raises(HookAbort, match="before_run hook 'a' aborted target: boom"):
        fire_hooks(Path("/x"), "before_run", "target", {}, invoke)


def test_fire_hooks_invoke_raises_not_optional_after_run_records_error(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "optional": False}]}},
    )

    def invoke(root, name, action, payload):
        raise RuntimeError("boom")

    results = fire_hooks(Path("/x"), "after_run", "target", {}, invoke)
    assert results == [{"tentacle": "a", "ok": False, "error": "boom"}]


def test_fire_hooks_before_run_result_not_ok_aborts(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"before_run": [{"tentacle": "a", "optional": False}]}},
    )

    def invoke(root, name, action, payload):
        return {"ok": False, "error": "nope"}

    with pytest.raises(HookAbort, match="before_run hook 'a' aborted target: nope"):
        fire_hooks(Path("/x"), "before_run", "target", {}, invoke)


def test_fire_hooks_before_run_result_not_ok_optional_does_not_abort(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"before_run": [{"tentacle": "a", "optional": True}]}},
    )

    def invoke(root, name, action, payload):
        return {"ok": False, "error": "nope"}

    results = fire_hooks(Path("/x"), "before_run", "target", {}, invoke)
    assert results == [
        {"tentacle": "a", "ok": True, "result": {"ok": False, "error": "nope"}}
    ]


def test_fire_hooks_before_run_result_ok_does_not_abort(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"before_run": [{"tentacle": "a", "optional": False}]}},
    )
    results = fire_hooks(
        Path("/x"), "before_run", "target", {}, lambda *a: {"ok": True}
    )
    assert results[0]["ok"] is True


def test_fire_hooks_after_run_result_not_ok_does_not_abort(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={"hooks": {"after_run": [{"tentacle": "a", "optional": False}]}},
    )

    def invoke(root, name, action, payload):
        return {"ok": False, "error": "nope"}

    results = fire_hooks(Path("/x"), "after_run", "target", {}, invoke)
    assert results == [
        {"tentacle": "a", "ok": True, "result": {"ok": False, "error": "nope"}}
    ]


def test_fire_hooks_emit_called_on_success(monkeypatch):
    _patch_hooks(monkeypatch, config={"hooks": {"after_run": [{"tentacle": "a"}]}})
    emitted = []
    monkeypatch.setattr(
        "kraken.core.hooks.emit",
        lambda event, payload: emitted.append((event, payload)),
    )
    fire_hooks(Path("/x"), "after_run", "target", {}, lambda *a: {"ok": True})
    assert emitted == [
        ("hook", {"event": "after_run", "tentacle": "a", "target": "target"})
    ]


def test_fire_hooks_multiple_hooks_all_fire(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={
            "hooks": {
                "after_run": [
                    {"tentacle": "a", "priority": 1},
                    {"tentacle": "b", "priority": 2},
                ]
            }
        },
    )
    names = []

    def invoke(root, name, action, payload):
        names.append(name)
        return {}

    fire_hooks(Path("/x"), "after_run", "target", {}, invoke)
    assert names == ["a", "b"]


def test_fire_hooks_stops_after_before_run_abort(monkeypatch):
    _patch_hooks(
        monkeypatch,
        config={
            "hooks": {
                "before_run": [
                    {"tentacle": "a", "priority": 1, "optional": False},
                    {"tentacle": "b", "priority": 2},
                ]
            }
        },
    )
    names = []

    def invoke(root, name, action, payload):
        names.append(name)
        return {"ok": False}

    with pytest.raises(HookAbort):
        fire_hooks(Path("/x"), "before_run", "target", {}, invoke)
    assert names == ["a"]
