import json
import urllib.request

from kraken.core import notify
from kraken.core.notify import (
    emit,
    enabled_channels,
    notify_ntfy,
    notify_stdout,
    notify_webhook,
)


def test_notify_stdout_prints_when_enabled(monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_NOTIFY_STDOUT", "1")
    notify_stdout("run.done", {"id": "t"})
    assert json.loads(capsys.readouterr().out) == {"notify": "run.done", "id": "t"}


def test_notify_stdout_silent_when_unset(monkeypatch, capsys):
    monkeypatch.delenv("KRAKEN_NOTIFY_STDOUT", raising=False)
    notify_stdout("run.done", {"id": "t"})
    assert capsys.readouterr().out == ""


def test_notify_stdout_silent_when_not_one(monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_NOTIFY_STDOUT", "yes")
    notify_stdout("run.done", {"id": "t"})
    assert capsys.readouterr().out == ""


def test_notify_webhook_no_url_returns(monkeypatch):
    monkeypatch.delenv("KRAKEN_NOTIFY_WEBHOOK", raising=False)
    called = []
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: called.append(1))
    notify_webhook("run.done", {"id": "t"})
    assert called == []


def test_notify_webhook_empty_url_returns(monkeypatch):
    monkeypatch.setenv("KRAKEN_NOTIFY_WEBHOOK", "")
    called = []
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: called.append(1))
    notify_webhook("run.done", {"id": "t"})
    assert called == []


def test_notify_webhook_posts_json(monkeypatch):
    monkeypatch.setenv("KRAKEN_NOTIFY_WEBHOOK", "https://example.com/hook")
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["req"] = req
        captured["timeout"] = timeout

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    notify_webhook("run.done", {"id": "t"})
    req = captured["req"]
    assert req.full_url == "https://example.com/hook"
    assert req.get_method() == "POST"
    assert json.loads(req.data) == {
        "event": "run.done",
        "payload": {"id": "t"},
        "product": "kraken",
    }
    assert req.get_header("Content-type") == "application/json"
    assert captured["timeout"] == 4


def test_notify_webhook_oserror_returns(monkeypatch):
    monkeypatch.setenv("KRAKEN_NOTIFY_WEBHOOK", "https://example.com/hook")

    def fake_urlopen(req, timeout=None):
        raise OSError("boom")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    notify_webhook("run.done", {"id": "t"})


def test_notify_ntfy_no_topic_returns(monkeypatch):
    monkeypatch.delenv("KRAKEN_NTFY_TOPIC", raising=False)
    called = []
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: called.append(1))
    notify_ntfy("run.done", {"id": "t"})
    assert called == []


def test_notify_ntfy_posts_to_default_url(monkeypatch):
    monkeypatch.setenv("KRAKEN_NTFY_TOPIC", "mytopic")
    monkeypatch.delenv("KRAKEN_NTFY_URL", raising=False)
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["req"] = req
        captured["timeout"] = timeout

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    notify_ntfy("run.done", {"id": "t"})
    req = captured["req"]
    assert req.full_url == "https://ntfy.sh/mytopic"
    assert req.get_method() == "POST"
    assert req.get_header("Title") == "kraken run.done"
    assert req.get_header("Content-type") == "text/plain"
    assert json.loads(req.data) == {"id": "t"}
    assert captured["timeout"] == 4


def test_notify_ntfy_custom_url_trailing_slash(monkeypatch):
    monkeypatch.setenv("KRAKEN_NTFY_TOPIC", "mytopic")
    monkeypatch.setenv("KRAKEN_NTFY_URL", "https://ntfy.example.com/")
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["req"] = req

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    notify_ntfy("run.done", {"id": "t"})
    assert captured["req"].full_url == "https://ntfy.example.com/mytopic"


def test_notify_ntfy_truncates_body(monkeypatch):
    monkeypatch.setenv("KRAKEN_NTFY_TOPIC", "mytopic")
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["req"] = req

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    notify_ntfy("run.done", {"data": "x" * 500})
    assert len(captured["req"].data) == 400


def test_notify_ntfy_oserror_returns(monkeypatch):
    monkeypatch.setenv("KRAKEN_NTFY_TOPIC", "mytopic")

    def fake_urlopen(req, timeout=None):
        raise OSError("boom")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    notify_ntfy("run.done", {"id": "t"})


def test_enabled_channels_config_raises(monkeypatch):
    def boom():
        raise RuntimeError("no config")

    monkeypatch.setattr("kraken.core.config.load_config", boom)
    assert enabled_channels() == ["stdout"]


def test_enabled_channels_config_none(monkeypatch):
    monkeypatch.setattr("kraken.core.config.load_config", lambda: None)
    assert enabled_channels() == ["stdout"]


def test_enabled_channels_config_empty_dict(monkeypatch):
    monkeypatch.setattr("kraken.core.config.load_config", lambda: {})
    assert enabled_channels() == ["stdout"]


def test_enabled_channels_dict_with_channels(monkeypatch):
    monkeypatch.setattr(
        "kraken.core.config.load_config",
        lambda: {"notify": {"channels": ["stdout", "ntfy"]}},
    )
    assert enabled_channels() == ["stdout", "ntfy"]


def test_enabled_channels_dict_filters_unknown(monkeypatch):
    monkeypatch.setattr(
        "kraken.core.config.load_config",
        lambda: {"notify": {"channels": ["carrier_pigeon", "stdout"]}},
    )
    assert enabled_channels() == ["stdout"]


def test_enabled_channels_dict_unknown_only(monkeypatch):
    monkeypatch.setattr(
        "kraken.core.config.load_config",
        lambda: {"notify": {"channels": ["carrier_pigeon"]}},
    )
    assert enabled_channels() == []


def test_enabled_channels_dict_channels_not_list(monkeypatch):
    monkeypatch.setattr(
        "kraken.core.config.load_config",
        lambda: {"notify": {"channels": "stdout"}},
    )
    assert enabled_channels() == ["stdout"]


def test_enabled_channels_dict_channels_empty_list(monkeypatch):
    monkeypatch.setattr(
        "kraken.core.config.load_config",
        lambda: {"notify": {"channels": []}},
    )
    assert enabled_channels() == []


def test_enabled_channels_str_local(monkeypatch):
    monkeypatch.setattr("kraken.core.config.load_config", lambda: {"notify": "local"})
    assert enabled_channels() == ["stdout"]


def test_enabled_channels_str_stdout(monkeypatch):
    monkeypatch.setattr("kraken.core.config.load_config", lambda: {"notify": "stdout"})
    assert enabled_channels() == ["stdout"]


def test_enabled_channels_str_none(monkeypatch):
    monkeypatch.setattr("kraken.core.config.load_config", lambda: {"notify": "none"})
    assert enabled_channels() == []


def test_enabled_channels_str_unknown(monkeypatch):
    monkeypatch.setattr(
        "kraken.core.config.load_config", lambda: {"notify": "everything"}
    )
    assert enabled_channels() == ["stdout"]


def test_enabled_channels_other_type(monkeypatch):
    monkeypatch.setattr("kraken.core.config.load_config", lambda: {"notify": 42})
    assert enabled_channels() == ["stdout"]


def test_enabled_channels_from_real_config_file(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".kraken").mkdir(parents=True)
    (home / ".kraken" / "config.yaml").write_text(
        "notify:\n  channels:\n    - ntfy\n    - webhook\n"
    )
    monkeypatch.setenv("KRAKEN_HOME", str(home))
    monkeypatch.setenv("KRAKEN_SYSTEM_DIR", str(tmp_path / "system"))
    monkeypatch.chdir(tmp_path)
    assert enabled_channels() == ["ntfy", "webhook"]


def test_enabled_channels_default_from_schema(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("KRAKEN_SYSTEM_DIR", str(tmp_path / "system"))
    monkeypatch.chdir(tmp_path)
    assert enabled_channels() == ["stdout"]


def test_emit_calls_each_channel(monkeypatch):
    calls = []
    monkeypatch.setattr(notify, "enabled_channels", lambda: ["stdout", "ntfy"])
    monkeypatch.setattr(
        notify,
        "CHANNELS",
        {
            "stdout": lambda e, p: calls.append(("stdout", e, p)),
            "ntfy": lambda e, p: calls.append(("ntfy", e, p)),
        },
    )
    emit("run.done", {"id": "t"})
    assert calls == [
        ("stdout", "run.done", {"id": "t"}),
        ("ntfy", "run.done", {"id": "t"}),
    ]


def test_emit_default_payload_empty_dict(monkeypatch):
    calls = []
    monkeypatch.setattr(notify, "enabled_channels", lambda: ["stdout"])
    monkeypatch.setattr(
        notify, "CHANNELS", {"stdout": lambda e, p: calls.append((e, p))}
    )
    emit("run.done")
    assert calls == [("run.done", {})]


def test_emit_continues_after_channel_exception(monkeypatch):
    calls = []

    def bad(event, payload):
        raise RuntimeError("boom")

    def good(event, payload):
        calls.append(event)

    monkeypatch.setattr(notify, "enabled_channels", lambda: ["bad", "good"])
    monkeypatch.setattr(notify, "CHANNELS", {"bad": bad, "good": good})
    emit("run.done", {"id": "t"})
    assert calls == ["run.done"]


def test_emit_no_channels(monkeypatch):
    monkeypatch.setattr(notify, "enabled_channels", lambda: [])
    emit("run.done", {"id": "t"})


def test_emit_end_to_end_stdout(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("KRAKEN_SYSTEM_DIR", str(tmp_path / "system"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("KRAKEN_NOTIFY_STDOUT", "1")
    emit("run.done", {"id": "t"})
    assert json.loads(capsys.readouterr().out) == {"notify": "run.done", "id": "t"}
