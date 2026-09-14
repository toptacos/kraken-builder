from kraken.core.notify import emit


def test_emit_without_topic_is_quiet(monkeypatch):
    monkeypatch.delenv("KRAKEN_NTFY_TOPIC", raising=False)
    monkeypatch.delenv("KRAKEN_NOTIFY_WEBHOOK", raising=False)
    emit("run.done", {"id": "t"})
