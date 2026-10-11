from pathlib import Path

import pytest
import yaml

from kraken.core.workflow import (
    WorkflowError,
    _dig,
    _run_step,
    interpolate,
    load_workflow,
    run_workflow,
)


def test_load_workflow_success(tmp_path):
    p = tmp_path / "wf.yaml"
    p.write_text(yaml.dump({"name": "test", "steps": [{"id": "s1"}]}))
    data = load_workflow(p)
    assert data == {"name": "test", "steps": [{"id": "s1"}]}


def test_load_workflow_empty_file(tmp_path):
    p = tmp_path / "wf.yaml"
    p.write_text("")
    with pytest.raises(WorkflowError, match="needs a steps list"):
        load_workflow(p)


def test_load_workflow_non_dict_yaml(tmp_path):
    p = tmp_path / "wf.yaml"
    p.write_text("- just\n- a\n- list\n")
    with pytest.raises(WorkflowError, match="needs a steps list"):
        load_workflow(p)


def test_load_workflow_missing_steps_key(tmp_path):
    p = tmp_path / "wf.yaml"
    p.write_text(yaml.dump({"name": "test"}))
    with pytest.raises(WorkflowError, match="needs a steps list"):
        load_workflow(p)


def test_dig_success():
    obj = {"a": {"b": {"c": 42}}}
    assert _dig(obj, "a.b.c") == 42


def test_dig_single_key():
    obj = {"x": 1}
    assert _dig(obj, "x") == 1


def test_dig_missing_key():
    with pytest.raises(WorkflowError, match="no value at"):
        _dig({"a": {}}, "a.b")


def test_dig_non_dict_intermediate():
    with pytest.raises(WorkflowError, match="no value at"):
        _dig({"a": 1}, "a.b")


def test_interpolate_string_with_ref():
    results = {"step1": {"result": {"zip": "27284"}}}
    assert interpolate("$step1.result.zip", results) == "27284"


def test_interpolate_string_without_ref():
    assert interpolate("hello", {}) == "hello"


def test_interpolate_non_string():
    assert interpolate(42, {}) == 42
    assert interpolate(None, {}) is None
    assert interpolate(True, {}) is True


def test_interpolate_dict():
    results = {"s1": {"result": {"zip": "27284"}}}
    value = {"x": "$s1.result.zip", "y": "static"}
    assert interpolate(value, results) == {"x": "27284", "y": "static"}


def test_interpolate_list():
    results = {"s1": {"result": {"zip": "27284"}}}
    value = ["$s1.result.zip", "plain"]
    assert interpolate(value, results) == ["27284", "plain"]


def test_interpolate_nested_dict_in_list():
    results = {"s1": {"result": {"zip": "27284"}}}
    value = [{"a": "$s1.result.zip"}]
    assert interpolate(value, results) == [{"a": "27284"}]


def test_interpolate_missing_ref_raises():
    with pytest.raises(WorkflowError, match="no value at"):
        interpolate("$missing.path", {})


def test_run_step_parallel(tmp_path, monkeypatch):
    calls = []

    def fake_run_named(root, name, action, payload, compose=False, home=None):
        calls.append(name)
        return {"name": name}

    monkeypatch.setattr("kraken.core.workflow.run_named", fake_run_named)
    step = {
        "parallel": [
            {"id": "a", "tentacle": "t1"},
            {"id": "b", "tentacle": "t2"},
        ]
    }
    result = _run_step(tmp_path, step, {})
    assert set(result.keys()) == {"a", "b"}
    assert result["a"] == {"name": "t1"}
    assert result["b"] == {"name": "t2"}


def test_run_step_parallel_empty_list(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "kraken.core.workflow.run_named",
        lambda *a, **k: {},
    )
    step = {"parallel": []}
    result = _run_step(tmp_path, step, {})
    assert result == {}


def test_run_step_parallel_none_list(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "kraken.core.workflow.run_named",
        lambda *a, **k: {},
    )
    step = {"parallel": None}
    result = _run_step(tmp_path, step, {})
    assert result == {}


def test_run_step_parallel_child_without_id(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "kraken.core.workflow.run_named",
        lambda *a, **k: {"ok": True},
    )
    step = {"parallel": [{"tentacle": "t1"}]}
    result = _run_step(tmp_path, step, {})
    assert "0" in result


def test_run_step_tentacle_key(tmp_path, monkeypatch):
    captured = {}

    def fake_run_named(root, name, action, payload, compose=False, home=None):
        captured.update(name=name, action=action, payload=payload, compose=compose)
        return {"ok": True}

    monkeypatch.setattr("kraken.core.workflow.run_named", fake_run_named)
    step = {"id": "s1", "tentacle": "my_arm", "action": "build"}
    _run_step(tmp_path, step, {})
    assert captured["name"] == "my_arm"
    assert captured["action"] == "build"


def test_run_step_arm_fallback(tmp_path, monkeypatch):
    captured = {}

    def fake_run_named(root, name, action, payload, compose=False, home=None):
        captured["name"] = name
        return {"ok": True}

    monkeypatch.setattr("kraken.core.workflow.run_named", fake_run_named)
    step = {"id": "s1", "arm": "my_arm"}
    _run_step(tmp_path, step, {})
    assert captured["name"] == "my_arm"


def test_run_step_default_action_ping(tmp_path, monkeypatch):
    captured = {}

    def fake_run_named(root, name, action, payload, compose=False, home=None):
        captured["action"] = action
        return {"ok": True}

    monkeypatch.setattr("kraken.core.workflow.run_named", fake_run_named)
    step = {"id": "s1", "tentacle": "my_arm"}
    _run_step(tmp_path, step, {})
    assert captured["action"] == "ping"


def test_run_step_missing_tentacle_raises(tmp_path):
    step = {"id": "s1"}
    with pytest.raises(WorkflowError, match="missing tentacle"):
        _run_step(tmp_path, step, {})


def test_run_step_missing_tentacle_no_id_raises(tmp_path):
    step = {}
    with pytest.raises(WorkflowError, match="missing tentacle"):
        _run_step(tmp_path, step, {})


def test_run_step_interpolates_payload(tmp_path, monkeypatch):
    captured = {}

    def fake_run_named(root, name, action, payload, compose=False, home=None):
        captured["payload"] = payload
        return {"ok": True}

    monkeypatch.setattr("kraken.core.workflow.run_named", fake_run_named)
    step = {"id": "s2", "tentacle": "my_arm", "payload": {"zip": "$s1.result.zip"}}
    results = {"s1": {"result": {"zip": "27284"}}}
    _run_step(tmp_path, step, results)
    assert captured["payload"] == {"zip": "27284"}


def test_run_step_compose_true(tmp_path, monkeypatch):
    captured = {}

    def fake_run_named(root, name, action, payload, compose=False, home=None):
        captured["compose"] = compose
        return {"ok": True}

    monkeypatch.setattr("kraken.core.workflow.run_named", fake_run_named)
    step = {"id": "s1", "tentacle": "my_arm", "compose": True}
    _run_step(tmp_path, step, {})
    assert captured["compose"] is True


def test_run_step_compose_false(tmp_path, monkeypatch):
    captured = {}

    def fake_run_named(root, name, action, payload, compose=False, home=None):
        captured["compose"] = compose
        return {"ok": True}

    monkeypatch.setattr("kraken.core.workflow.run_named", fake_run_named)
    step = {"id": "s1", "tentacle": "my_arm", "compose": False}
    _run_step(tmp_path, step, {})
    assert captured["compose"] is False


def test_run_step_home_passed_through(tmp_path, monkeypatch):
    captured = {}

    def fake_run_named(root, name, action, payload, compose=False, home=None):
        captured["home"] = home
        return {"ok": True}

    monkeypatch.setattr("kraken.core.workflow.run_named", fake_run_named)
    step = {"id": "s1", "tentacle": "my_arm"}
    _run_step(tmp_path, step, {}, home=tmp_path)
    assert captured["home"] == tmp_path


def test_run_workflow_success(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "kraken.core.workflow.run_named",
        lambda root, name, action, payload, compose=False, home=None: {
            "ok": True,
            "echo": name,
        },
    )
    spec = {
        "name": "my-workflow",
        "goal": "test goal",
        "steps": [
            {"id": "s1", "tentacle": "arm1"},
            {"id": "s2", "tentacle": "arm2"},
        ],
    }
    result = run_workflow(tmp_path, spec)
    assert result["ok"] is True
    assert result["name"] == "my-workflow"
    assert result["goal"] == "test goal"
    assert result["results"]["s1"] == {"ok": True, "echo": "arm1"}
    assert result["results"]["s2"] == {"ok": True, "echo": "arm2"}


def test_run_workflow_empty_steps(tmp_path):
    spec = {"name": "empty"}
    result = run_workflow(tmp_path, spec)
    assert result["ok"] is True
    assert result["results"] == {}


def test_run_workflow_no_steps_key(tmp_path):
    spec = {}
    result = run_workflow(tmp_path, spec)
    assert result["ok"] is True
    assert result["name"] is None
    assert result["goal"] is None
    assert result["results"] == {}


def test_run_workflow_step_without_id(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "kraken.core.workflow.run_named",
        lambda root, name, action, payload, compose=False, home=None: {"ok": True},
    )
    spec = {"steps": [{"tentacle": "arm1"}]}
    result = run_workflow(tmp_path, spec)
    assert "step0" in result["results"]


def test_run_workflow_step_with_none_id(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "kraken.core.workflow.run_named",
        lambda root, name, action, payload, compose=False, home=None: {"ok": True},
    )
    spec = {"steps": [{"id": None, "tentacle": "arm1"}]}
    result = run_workflow(tmp_path, spec)
    assert "step0" in result["results"]


def test_run_workflow_emits_notification(tmp_path, monkeypatch):
    emitted = []
    monkeypatch.setattr(
        "kraken.core.workflow.emit",
        lambda event, payload: emitted.append((event, payload)),
    )
    monkeypatch.setattr(
        "kraken.core.workflow.run_named",
        lambda root, name, action, payload, compose=False, home=None: {"ok": True},
    )
    spec = {"name": "wf1", "steps": [{"id": "s1", "tentacle": "arm1"}]}
    run_workflow(tmp_path, spec)
    assert len(emitted) == 1
    assert emitted[0][0] == "workflow"
    assert emitted[0][1]["name"] == "wf1"
    assert "s1" in emitted[0][1]["steps"]


def test_run_workflow_home_passed_to_steps(tmp_path, monkeypatch):
    captured = []

    def fake_run_named(root, name, action, payload, compose=False, home=None):
        captured.append(home)
        return {"ok": True}

    monkeypatch.setattr("kraken.core.workflow.run_named", fake_run_named)
    spec = {"steps": [{"id": "s1", "tentacle": "arm1"}]}
    run_workflow(tmp_path, spec, home=tmp_path)
    assert captured == [tmp_path]


def test_run_workflow_parallel_step(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "kraken.core.workflow.run_named",
        lambda root, name, action, payload, compose=False, home=None: {
            "ok": True,
            "arm": name,
        },
    )
    spec = {
        "steps": [
            {
                "id": "fanout",
                "parallel": [
                    {"id": "a", "tentacle": "t1"},
                    {"id": "b", "tentacle": "t2"},
                ],
            }
        ]
    }
    result = run_workflow(tmp_path, spec)
    assert result["results"]["fanout"]["a"] == {"ok": True, "arm": "t1"}
    assert result["results"]["fanout"]["b"] == {"ok": True, "arm": "t2"}


def test_workflow_error_is_value_error():
    assert issubclass(WorkflowError, ValueError)
