"""Comprehensive tests for kraken.core.compose — all functions and branches."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from kraken.core.compose import (
    ComposeError,
    _docker_available,
    _docker_compose_up,
    _driver_for,
    _offline,
    _project_name,
    find_plan,
    parse_compose,
    plan_dir,
    up,
)
from kraken.core.network import SHARED_NETWORK

BERTH_COMPOSE = """\
services:
  api:
    image: nginx:alpine
    networks:
      - kraken
    ports:
      - "8080:80"
  worker:
    image: busybox:latest
    networks:
      - kraken
networks:
  kraken:
    name: kraken
    driver: bridge
"""

MINIMAL_COMPOSE = """\
services:
  web:
    image: nginx
"""


def _seed_berth(home: Path, compose: str = BERTH_COMPOSE) -> Path:
    d = home / ".kraken" / "data" / "berth"
    d.mkdir(parents=True, exist_ok=True)
    (d / "compose.yaml").write_text(compose, encoding="utf-8")
    (d / "project.json").write_text(json.dumps({"name": "demo"}), encoding="utf-8")
    return d


# --- plan_dir ----------------------------------------------------------------


def test_plan_dir_default_arm(tmp_path):
    result = plan_dir(home=tmp_path)
    assert result == tmp_path / ".kraken" / "data" / "berth"


def test_plan_dir_custom_arm(tmp_path):
    result = plan_dir(arm="board", home=tmp_path)
    assert result == tmp_path / ".kraken" / "data" / "board"


def test_plan_dir_no_home_uses_user_home(monkeypatch, tmp_path):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    result = plan_dir(arm="inlet")
    assert result == tmp_path / ".kraken" / "data" / "inlet"


# --- find_plan ---------------------------------------------------------------


def test_find_plan_finds_berth(tmp_path):
    _seed_berth(tmp_path)
    result = find_plan(tmp_path)
    assert result is not None
    assert result.name == "compose.yaml"
    assert result.parent.name == "berth"


def test_find_plan_specific_arm(tmp_path):
    _seed_berth(tmp_path)
    result = find_plan(tmp_path, "berth")
    assert result is not None
    assert result.is_file()


def test_find_plan_missing_arm_returns_none(tmp_path):
    result = find_plan(tmp_path, "nonexistent")
    assert result is None


def test_find_plan_no_plan_returns_none(tmp_path):
    result = find_plan(tmp_path)
    assert result is None


def test_find_plan_prefers_berth_over_board(tmp_path):
    berth_dir = tmp_path / ".kraken" / "data" / "berth"
    board_dir = tmp_path / ".kraken" / "data" / "board"
    berth_dir.mkdir(parents=True)
    board_dir.mkdir(parents=True)
    (berth_dir / "compose.yaml").write_text(BERTH_COMPOSE)
    (board_dir / "compose.yaml").write_text(BERTH_COMPOSE)
    result = find_plan(tmp_path)
    assert result is not None
    assert result.parent.name == "berth"


def test_find_plan_board_when_no_berth(tmp_path):
    board_dir = tmp_path / ".kraken" / "data" / "board"
    board_dir.mkdir(parents=True)
    (board_dir / "compose.yaml").write_text(BERTH_COMPOSE)
    result = find_plan(tmp_path)
    assert result is not None
    assert result.parent.name == "board"


def test_find_plan_inlet_when_no_berth_or_board(tmp_path):
    inlet_dir = tmp_path / ".kraken" / "data" / "inlet"
    inlet_dir.mkdir(parents=True)
    (inlet_dir / "compose.yaml").write_text(BERTH_COMPOSE)
    result = find_plan(tmp_path)
    assert result is not None
    assert result.parent.name == "inlet"


# --- parse_compose ------------------------------------------------------------


def test_parse_compose_full_document():
    parsed = parse_compose(BERTH_COMPOSE)
    assert parsed["source"] == "<inline>"
    assert parsed["network"] == "kraken"
    assert parsed["network_driver"] == "bridge"
    assert parsed["service_names"] == ["api", "worker"]
    api = next(s for s in parsed["services"] if s["name"] == "api")
    assert api["image"] == "nginx:alpine"
    assert api["networks"] == ["kraken"]
    assert api["ports"] == ["8080:80"]
    assert api["build"] is False


def test_parse_compose_custom_source():
    parsed = parse_compose(BERTH_COMPOSE, source="/path/to/compose.yaml")
    assert parsed["source"] == "/path/to/compose.yaml"


def test_parse_compose_empty_string():
    parsed = parse_compose("")
    assert parsed["network"] == ""
    assert parsed["services"] == []
    assert parsed["service_names"] == []


def test_parse_compose_null_document():
    parsed = parse_compose("---\n")
    assert parsed["services"] == []


def test_parse_compose_invalid_yaml():
    with pytest.raises(ComposeError, match="not valid YAML"):
        parse_compose(":\n  - bad\n  : indent\n")


def test_parse_compose_non_mapping():
    with pytest.raises(ComposeError, match="must be a mapping"):
        parse_compose("- just\n- a list\n")


def test_parse_compose_scalar():
    with pytest.raises(ComposeError, match="must be a mapping"):
        parse_compose("just_a_string\n")


def test_parse_compose_services_not_mapping():
    with pytest.raises(ComposeError, match="services must be a mapping"):
        parse_compose("services: [oops]\n")


def test_parse_compose_networks_not_mapping():
    with pytest.raises(ComposeError, match="networks must be a mapping"):
        parse_compose("services:\n  a: 1\nnetworks: nope\n")


def test_parse_compose_network_name_from_spec():
    text = """\
services:
  web:
    image: nginx
networks:
  custom_net:
    name: my_network
    driver: overlay
"""
    parsed = parse_compose(text)
    assert parsed["network"] == "kraken_my_network"
    assert parsed["network_driver"] == "bridge"


def test_parse_compose_network_name_from_key():
    text = """\
services:
  web:
    image: nginx
networks:
  custom_net:
    driver: bridge
"""
    parsed = parse_compose(text)
    assert parsed["network"] == "kraken_custom_net"
    assert parsed["network_driver"] == "bridge"


def test_parse_compose_network_empty_spec_uses_key():
    text = """\
services:
  web:
    image: nginx
networks:
  custom_net: {}
"""
    parsed = parse_compose(text)
    assert parsed["network"] == "kraken_custom_net"


def test_parse_compose_network_null_spec_uses_key():
    text = """\
services:
  web:
    image: nginx
networks:
  custom_net:
"""
    parsed = parse_compose(text)
    assert parsed["network"] == "kraken_custom_net"


def test_parse_compose_service_networks_as_string():
    text = """\
services:
  web:
    image: nginx
    networks: kraken
networks:
  kraken:
    name: kraken
"""
    parsed = parse_compose(text)
    web = parsed["services"][0]
    assert web["networks"] == ["kraken"]


def test_parse_compose_service_networks_as_dict():
    text = """\
services:
  web:
    image: nginx
    networks:
      kraken:
        ipv4_address: 172.20.0.2
networks:
  kraken:
    name: kraken
"""
    parsed = parse_compose(text)
    web = parsed["services"][0]
    assert web["networks"] == ["kraken"]


def test_parse_compose_service_networks_as_list():
    text = """\
services:
  web:
    image: nginx
    networks:
      - kraken
      - other
networks:
  kraken:
    name: kraken
"""
    parsed = parse_compose(text)
    web = parsed["services"][0]
    assert web["networks"] == ["kraken", "other"]


def test_parse_compose_service_networks_as_tuple():
    text = """\
services:
  web:
    image: nginx
    networks: !!python/tuple [kraken, other]
networks:
  kraken:
    name: kraken
"""
    with pytest.raises(ComposeError):
        parse_compose(text)


def test_parse_compose_service_networks_none():
    text = """\
services:
  web:
    image: nginx
    networks:
networks:
  kraken:
    name: kraken
"""
    parsed = parse_compose(text)
    web = parsed["services"][0]
    assert web["networks"] == []


def test_parse_compose_service_networks_missing():
    text = """\
services:
  web:
    image: nginx
networks:
  kraken:
    name: kraken
"""
    parsed = parse_compose(text)
    web = parsed["services"][0]
    assert web["networks"] == []


def test_parse_compose_service_spec_as_string():
    text = """\
services:
  web: nginx:latest
networks:
  kraken:
    name: kraken
"""
    parsed = parse_compose(text)
    web = parsed["services"][0]
    assert web["image"] == "nginx:latest"
    assert web["networks"] == []


def test_parse_compose_service_no_image():
    text = """\
services:
  web:
    build: .
networks:
  kraken:
    name: kraken
"""
    parsed = parse_compose(text)
    web = parsed["services"][0]
    assert web["image"] == ""
    assert web["build"] is True


def test_parse_compose_service_ports():
    text = """\
services:
  web:
    image: nginx
    ports:
      - "8080:80"
      - "443:443"
networks:
  kraken:
    name: kraken
"""
    parsed = parse_compose(text)
    web = parsed["services"][0]
    assert web["ports"] == ["8080:80", "443:443"]


def test_parse_compose_service_no_ports():
    text = """\
services:
  web:
    image: nginx
networks:
  kraken:
    name: kraken
"""
    parsed = parse_compose(text)
    web = parsed["services"][0]
    assert web["ports"] == []


def test_parse_compose_services_sorted():
    text = """\
services:
  zebra:
    image: nginx
  alpha:
    image: busybox
  middle:
    image: redis
networks:
  kraken:
    name: kraken
"""
    parsed = parse_compose(text)
    assert parsed["service_names"] == ["alpha", "middle", "zebra"]


def test_parse_compose_network_normalization():
    text = """\
services:
  web:
    image: nginx
networks:
  custom_net:
    name: my_lab
"""
    parsed = parse_compose(text)
    assert parsed["network"] == "kraken_my_lab"


def test_parse_compose_network_already_namespaced():
    text = """\
services:
  web:
    image: nginx
networks:
  custom_net:
    name: kraken_lab
"""
    parsed = parse_compose(text)
    assert parsed["network"] == "kraken_lab"


def test_parse_compose_network_bare_kraken():
    text = """\
services:
  web:
    image: nginx
networks:
  custom_net:
    name: kraken
"""
    parsed = parse_compose(text)
    assert parsed["network"] == "kraken"


# --- _driver_for -------------------------------------------------------------


def test_driver_for_bridge_default():
    networks = {"kraken": {"name": "kraken"}}
    assert _driver_for(networks, "kraken") == "bridge"


def test_driver_for_custom_driver():
    networks = {"kraken": {"name": "kraken", "driver": "overlay"}}
    assert _driver_for(networks, "kraken") == "overlay"


def test_driver_for_missing_network():
    assert _driver_for({}, "kraken") == "bridge"


def test_driver_for_empty_name():
    networks = {"kraken": {"name": "kraken", "driver": "overlay"}}
    assert _driver_for(networks, "") == "bridge"


def test_driver_for_non_dict_spec():
    networks = {"kraken": "not_a_dict"}
    assert _driver_for(networks, "kraken") == "bridge"


def test_driver_for_driver_none():
    networks = {"kraken": {"name": "kraken", "driver": None}}
    assert _driver_for(networks, "kraken") == "bridge"


# --- _offline ----------------------------------------------------------------


def test_offline_true(monkeypatch):
    monkeypatch.setenv("KRAKEN_OFFLINE", "1")
    assert _offline() is True


def test_offline_false(monkeypatch):
    monkeypatch.delenv("KRAKEN_OFFLINE", raising=False)
    assert _offline() is False


def test_offline_other_value(monkeypatch):
    monkeypatch.setenv("KRAKEN_OFFLINE", "yes")
    assert _offline() is False


# --- _docker_available -------------------------------------------------------


def test_docker_available_true(monkeypatch):
    monkeypatch.setattr(
        "shutil.which", lambda cmd: "/usr/bin/docker" if cmd == "docker" else None
    )
    assert _docker_available() is True


def test_docker_available_false(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda cmd: None)
    assert _docker_available() is False


# --- up() --------------------------------------------------------------------


def test_up_inline_compose(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    result = up({"compose": BERTH_COMPOSE}, home=tmp_path)
    assert result["ok"] is True
    assert result["verb"] == "up"
    assert result["daemon"] is False
    assert result["plan_source"] == "<inline>"
    assert result["network"]["name"] == "kraken"
    assert result["network"]["driver"] == "bridge"
    assert result["network"]["enabled"] is True
    assert result["orphan_networks"] == []
    assert result["public_ports"] == ["8080:80"]
    assert result["offline"] is False
    assert any("kraken up --start" in n for n in result["next"])


def test_up_from_file(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    plan = tmp_path / "custom.yaml"
    plan.write_text(BERTH_COMPOSE, encoding="utf-8")
    result = up({"file": str(plan)}, home=tmp_path)
    assert result["ok"] is True
    assert result["plan_source"] == str(plan)


def test_up_from_plan_key(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    plan = tmp_path / "custom.yaml"
    plan.write_text(BERTH_COMPOSE, encoding="utf-8")
    result = up({"plan": str(plan)}, home=tmp_path)
    assert result["ok"] is True
    assert result["plan_source"] == str(plan)


def test_up_from_path_key(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    plan = tmp_path / "custom.yaml"
    plan.write_text(BERTH_COMPOSE, encoding="utf-8")
    result = up({"path": str(plan)}, home=tmp_path)
    assert result["ok"] is True
    assert result["plan_source"] == str(plan)


def test_up_file_not_found(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with pytest.raises(ComposeError, match="no compose plan at"):
        up({"file": str(tmp_path / "missing.yaml")}, home=tmp_path)


def test_up_no_plan_found(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with pytest.raises(ComposeError, match="no compose plan found"):
        up({}, home=tmp_path)


def test_up_no_plan_found_with_arm(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with pytest.raises(ComposeError, match="no compose plan found"):
        up({}, home=tmp_path)


def test_up_discovers_plan_from_berth(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    _seed_berth(tmp_path)
    result = up({}, root=tmp_path, home=tmp_path)
    assert result["ok"] is True
    assert result["project"] == "demo"


def test_up_discovers_plan_from_board(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    board_dir = tmp_path / ".kraken" / "data" / "board"
    board_dir.mkdir(parents=True)
    (board_dir / "compose.yaml").write_text(BERTH_COMPOSE)
    result = up({}, root=tmp_path, home=tmp_path)
    assert result["ok"] is True


def test_up_discovers_plan_from_inlet(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    inlet_dir = tmp_path / ".kraken" / "data" / "inlet"
    inlet_dir.mkdir(parents=True)
    (inlet_dir / "compose.yaml").write_text(BERTH_COMPOSE)
    result = up({}, root=tmp_path, home=tmp_path)
    assert result["ok"] is True


def test_up_orphan_networks(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    bad = BERTH_COMPOSE.replace("      - kraken", "      - somewhere_else")
    result = up({"compose": bad}, home=tmp_path)
    assert result["ok"] is False
    assert result["error"]["code"] == "network_mismatch"
    assert "api" in result["error"]["message"]
    assert "worker" in result["error"]["message"]
    assert set(result["orphan_networks"]) == {"api", "worker"}


def test_up_partial_orphan_networks(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    text = """\
services:
  api:
    image: nginx
    networks:
      - kraken
  worker:
    image: busybox
    networks:
      - other_net
networks:
  kraken:
    name: kraken
"""
    result = up({"compose": text}, home=tmp_path)
    assert result["ok"] is False
    assert result["orphan_networks"] == ["worker"]


def test_up_start_offline(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_OFFLINE", "1")
    _seed_berth(tmp_path)
    result = up({}, root=tmp_path, home=tmp_path, start=True)
    assert result["ok"] is False
    assert result["error"]["code"] == "offline"
    assert result["daemon"] is False


def test_up_start_no_docker(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.delenv("KRAKEN_OFFLINE", raising=False)
    monkeypatch.setattr("kraken.core.compose._docker_available", lambda: False)
    _seed_berth(tmp_path)
    result = up({}, root=tmp_path, home=tmp_path, start=True)
    assert result["ok"] is False
    assert result["error"]["code"] == "no_docker"
    assert result["daemon"] is False


def test_up_start_success(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.delenv("KRAKEN_OFFLINE", raising=False)
    monkeypatch.setattr("kraken.core.compose._docker_available", lambda: True)
    _seed_berth(tmp_path)

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout="done", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    result = up({}, root=tmp_path, home=tmp_path, start=True)
    assert result["ok"] is True
    assert result["daemon"] is True


def test_up_start_network_create_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.delenv("KRAKEN_OFFLINE", raising=False)
    monkeypatch.setattr("kraken.core.compose._docker_available", lambda: True)
    _seed_berth(tmp_path)

    def fake_run(cmd, **kwargs):
        if "network" in cmd and "inspect" in cmd:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")
        if "network" in cmd and "create" in cmd:
            return subprocess.CompletedProcess(
                cmd, 1, stdout="", stderr="permission denied"
            )
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    result = up({}, root=tmp_path, home=tmp_path, start=True)
    assert result["ok"] is False
    assert result["error"]["code"] == "network_create_failed"
    assert "permission denied" in result["error"]["message"]


def test_up_start_network_create_fails_no_stderr(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.delenv("KRAKEN_OFFLINE", raising=False)
    monkeypatch.setattr("kraken.core.compose._docker_available", lambda: True)
    _seed_berth(tmp_path)

    def fake_run(cmd, **kwargs):
        if "network" in cmd and "inspect" in cmd:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")
        if "network" in cmd and "create" in cmd:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    result = up({}, root=tmp_path, home=tmp_path, start=True)
    assert result["ok"] is False
    assert result["error"]["code"] == "network_create_failed"
    assert result["error"]["message"] == "docker network create failed"


def test_up_start_compose_up_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.delenv("KRAKEN_OFFLINE", raising=False)
    monkeypatch.setattr("kraken.core.compose._docker_available", lambda: True)
    _seed_berth(tmp_path)

    def fake_run(cmd, **kwargs):
        if "network" in cmd and "inspect" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout="exists", stderr="")
        if "compose" in cmd:
            return subprocess.CompletedProcess(
                cmd, 1, stdout="", stderr="compose error"
            )
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    result = up({}, root=tmp_path, home=tmp_path, start=True)
    assert result["ok"] is False
    assert result["daemon"] is False
    assert result["compose_stderr"] == "compose error"


def test_up_start_compose_up_success(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.delenv("KRAKEN_OFFLINE", raising=False)
    monkeypatch.setattr("kraken.core.compose._docker_available", lambda: True)
    _seed_berth(tmp_path)

    def fake_run(cmd, **kwargs):
        if "network" in cmd and "inspect" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout="exists", stderr="")
        if "compose" in cmd:
            return subprocess.CompletedProcess(
                cmd, 0, stdout="container started", stderr=""
            )
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    result = up({}, root=tmp_path, home=tmp_path, start=True)
    assert result["ok"] is True
    assert result["daemon"] is True
    assert result["compose_stdout"] == "container started"
    assert "docker compose" in result["command"]


def test_up_offline_flag_in_plan(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_OFFLINE", "1")
    result = up({"compose": BERTH_COMPOSE}, home=tmp_path)
    assert result["offline"] is True


def test_up_not_offline_flag_in_plan(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.delenv("KRAKEN_OFFLINE", raising=False)
    result = up({"compose": BERTH_COMPOSE}, home=tmp_path)
    assert result["offline"] is False


def test_up_project_name_from_compose(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    text = "name: my_project\n" + BERTH_COMPOSE
    result = up({"compose": text}, home=tmp_path)
    assert result["project"] == "my_project"


def test_up_project_name_from_sibling_json(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    d = _seed_berth(tmp_path)
    (d / "project.json").write_text(
        json.dumps({"name": "json_project"}), encoding="utf-8"
    )
    result = up({}, root=tmp_path, home=tmp_path)
    assert result["project"] == "json_project"


def test_up_project_name_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    result = up({"compose": MINIMAL_COMPOSE}, home=tmp_path)
    assert result["project"] == "kraken"


def test_up_project_name_from_file_sibling(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    plan = tmp_path / "compose.yaml"
    plan.write_text(MINIMAL_COMPOSE, encoding="utf-8")
    (tmp_path / "project.json").write_text(
        json.dumps({"name": "file_project"}), encoding="utf-8"
    )
    result = up({"file": str(plan)}, home=tmp_path)
    assert result["project"] == "file_project"


def test_up_network_disabled(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_DOCKER_NETWORK", "")
    result = up({"compose": BERTH_COMPOSE}, home=tmp_path)
    assert result["network"]["enabled"] is True


def test_up_with_root(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    result = up({"compose": BERTH_COMPOSE}, root=tmp_path, home=tmp_path)
    assert result["ok"] is True


def test_up_empty_payload(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with pytest.raises(ComposeError):
        up({}, home=tmp_path)


def test_up_none_payload(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with pytest.raises(ComposeError):
        up(None, home=tmp_path)


def test_up_compose_key_empty_string(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with pytest.raises(ComposeError):
        up({"compose": ""}, home=tmp_path)


def test_up_file_key_empty_string(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with pytest.raises(ComposeError):
        up({"file": ""}, home=tmp_path)


# --- _project_name -----------------------------------------------------------


def test_project_name_from_yaml():
    text = "name: test_project\nservices:\n  web:\n    image: nginx\n"
    assert _project_name(text, "<inline>") == "test_project"


def test_project_name_yaml_no_name():
    text = "services:\n  web:\n    image: nginx\n"
    assert _project_name(text, "<inline>") == "kraken"


def test_project_name_yaml_empty_name():
    text = "name: ''\nservices:\n  web:\n    image: nginx\n"
    assert _project_name(text, "<inline>") == "kraken"


def test_project_name_yaml_whitespace_name():
    text = "name: '  '\nservices:\n  web:\n    image: nginx\n"
    assert _project_name(text, "<inline>") == "kraken"


def test_project_name_yaml_invalid():
    text = ":\n  bad\n"
    assert _project_name(text, "<inline>") == "kraken"


def test_project_name_yaml_non_dict():
    text = "- a\n- list\n"
    assert _project_name(text, "<inline>") == "kraken"


def test_project_name_from_sibling_json(tmp_path):
    d = tmp_path / "plans"
    d.mkdir()
    (d / "project.json").write_text(
        json.dumps({"name": "sibling_proj"}), encoding="utf-8"
    )
    text = "services:\n  web:\n    image: nginx\n"
    assert _project_name(text, str(d / "compose.yaml")) == "sibling_proj"


def test_project_name_sibling_json_no_name(tmp_path):
    d = tmp_path / "plans"
    d.mkdir()
    (d / "project.json").write_text(json.dumps({"other": "value"}), encoding="utf-8")
    text = "services:\n  web:\n    image: nginx\n"
    assert _project_name(text, str(d / "compose.yaml")) == "kraken"


def test_project_name_sibling_json_empty_name(tmp_path):
    d = tmp_path / "plans"
    d.mkdir()
    (d / "project.json").write_text(json.dumps({"name": ""}), encoding="utf-8")
    text = "services:\n  web:\n    image: nginx\n"
    assert _project_name(text, str(d / "compose.yaml")) == "kraken"


def test_project_name_sibling_json_invalid_json(tmp_path):
    d = tmp_path / "plans"
    d.mkdir()
    (d / "project.json").write_text("not json{{{", encoding="utf-8")
    text = "services:\n  web:\n    image: nginx\n"
    assert _project_name(text, str(d / "compose.yaml")) == "kraken"


def test_project_name_sibling_json_not_dict(tmp_path):
    d = tmp_path / "plans"
    d.mkdir()
    (d / "project.json").write_text(json.dumps(["a", "list"]), encoding="utf-8")
    text = "services:\n  web:\n    image: nginx\n"
    assert _project_name(text, str(d / "compose.yaml")) == "kraken"


def test_project_name_no_sibling(tmp_path):
    text = "services:\n  web:\n    image: nginx\n"
    assert (
        _project_name(text, str(tmp_path / "nonexistent" / "compose.yaml")) == "kraken"
    )


def test_project_name_inline_source_no_sibling():
    text = "services:\n  web:\n    image: nginx\n"
    assert _project_name(text, "<inline>") == "kraken"


# --- _docker_compose_up ------------------------------------------------------


def test_docker_compose_up_network_exists():
    def fake_run(cmd, **kwargs):
        if "inspect" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout="exists", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="started", stderr="")

    with patch("subprocess.run", side_effect=fake_run):
        result = _docker_compose_up("/tmp/compose.yaml", "kraken", "bridge")
    assert result["ok"] is True
    assert result["started"] is True
    assert result["compose_stdout"] == "started"


def test_docker_compose_up_network_create_success():
    def fake_run(cmd, **kwargs):
        if "inspect" in cmd:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")
        if "create" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout="created", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="started", stderr="")

    with patch("subprocess.run", side_effect=fake_run):
        result = _docker_compose_up("/tmp/compose.yaml", "kraken", "bridge")
    assert result["ok"] is True
    assert result["started"] is True


def test_docker_compose_up_network_create_failure():
    def fake_run(cmd, **kwargs):
        if "inspect" in cmd:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")
        if "create" in cmd:
            return subprocess.CompletedProcess(
                cmd, 1, stdout="", stderr="error creating"
            )
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    with patch("subprocess.run", side_effect=fake_run):
        result = _docker_compose_up("/tmp/compose.yaml", "kraken", "bridge")
    assert result["ok"] is False
    assert result["started"] is False
    assert result["error"]["code"] == "network_create_failed"
    assert "error creating" in result["error"]["message"]


def test_docker_compose_up_network_create_failure_empty_stderr():
    def fake_run(cmd, **kwargs):
        if "inspect" in cmd:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")
        if "create" in cmd:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    with patch("subprocess.run", side_effect=fake_run):
        result = _docker_compose_up("/tmp/compose.yaml", "kraken", "bridge")
    assert result["ok"] is False
    assert result["error"]["message"] == "docker network create failed"


def test_docker_compose_up_compose_failure():
    def fake_run(cmd, **kwargs):
        if "inspect" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout="exists", stderr="")
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="compose failed")

    with patch("subprocess.run", side_effect=fake_run):
        result = _docker_compose_up("/tmp/compose.yaml", "kraken", "bridge")
    assert result["ok"] is False
    assert result["started"] is False
    assert result["compose_stderr"] == "compose failed"


def test_docker_compose_up_truncates_long_output():
    long_stdout = "x" * 5000
    long_stderr = "e" * 3000

    def fake_run(cmd, **kwargs):
        if "inspect" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout="exists", stderr="")
        return subprocess.CompletedProcess(
            cmd, 0, stdout=long_stdout, stderr=long_stderr
        )

    with patch("subprocess.run", side_effect=fake_run):
        result = _docker_compose_up("/tmp/compose.yaml", "kraken", "bridge")
    assert len(result["compose_stdout"]) == 2000
    assert len(result["compose_stderr"]) == 1000


def test_docker_compose_up_command_format():
    captured_cmds = []

    def fake_run(cmd, **kwargs):
        captured_cmds.append(cmd)
        if "inspect" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout="exists", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    with patch("subprocess.run", side_effect=fake_run):
        _docker_compose_up("/tmp/my_compose.yaml", "kraken", "overlay")
    assert captured_cmds[0] == ["docker", "network", "inspect", "kraken"]
    assert captured_cmds[1] == [
        "docker",
        "compose",
        "-f",
        "/tmp/my_compose.yaml",
        "up",
        "-d",
    ]


def test_docker_compose_up_creates_network_with_driver():
    captured_cmds = []

    def fake_run(cmd, **kwargs):
        captured_cmds.append(cmd)
        if "inspect" in cmd:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")
        if "create" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout="created", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    with patch("subprocess.run", side_effect=fake_run):
        _docker_compose_up("/tmp/compose.yaml", "kraken", "overlay")
    assert captured_cmds[1] == [
        "docker",
        "network",
        "create",
        "--driver",
        "overlay",
        "kraken",
    ]


# --- ComposeError ------------------------------------------------------------


def test_compose_error_is_runtime_error():
    assert issubclass(ComposeError, RuntimeError)


def test_compose_error_message():
    err = ComposeError("test message")
    assert str(err) == "test message"


# --- Integration-style tests -------------------------------------------------


def test_up_full_flow_with_start(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.delenv("KRAKEN_OFFLINE", raising=False)
    monkeypatch.setattr("kraken.core.compose._docker_available", lambda: True)
    _seed_berth(tmp_path)

    def fake_run(cmd, **kwargs):
        if "inspect" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout="exists", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="started", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    result = up({}, root=tmp_path, home=tmp_path, start=True)
    assert result["ok"] is True
    assert result["daemon"] is True
    assert result["project"] == "demo"
    assert result["network"]["name"] == "kraken"
    assert len(result["services"]) == 2


def test_up_plan_only_no_docker_calls(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    _seed_berth(tmp_path)
    call_count = 0

    def fake_run(cmd, **kwargs):
        nonlocal call_count
        call_count += 1
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    result = up({}, root=tmp_path, home=tmp_path, start=False)
    assert result["ok"] is True
    assert call_count == 0


def test_up_orphan_check_happens_before_start(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.delenv("KRAKEN_OFFLINE", raising=False)
    monkeypatch.setattr("kraken.core.compose._docker_available", lambda: True)
    bad = BERTH_COMPOSE.replace("      - kraken", "      - other")
    _seed_berth(tmp_path, compose=bad)

    call_count = 0

    def fake_run(cmd, **kwargs):
        nonlocal call_count
        call_count += 1
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    result = up({}, root=tmp_path, home=tmp_path, start=True)
    assert result["ok"] is False
    assert result["error"]["code"] == "network_mismatch"
    assert call_count == 0


def test_up_offline_check_happens_before_docker_check(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_OFFLINE", "1")
    monkeypatch.setattr("kraken.core.compose._docker_available", lambda: False)
    _seed_berth(tmp_path)
    result = up({}, root=tmp_path, home=tmp_path, start=True)
    assert result["ok"] is False
    assert result["error"]["code"] == "offline"
