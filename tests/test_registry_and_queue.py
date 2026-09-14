from pathlib import Path

from kraken.core.loader import load_arms
from kraken.core.queue import Job, WorkflowQueue
from kraken.core.registry import Registry

ROOT = Path(__file__).resolve().parents[1]


def _registry() -> Registry:
    registry = Registry()
    registry.load_all(load_arms([ROOT / "arms"]))
    return registry


def test_ping_action():
    result = _registry().run("echo", "ping")
    assert result["ok"] is True
    assert result["arm"] == "echo"


def test_unknown_action_rejected():
    try:
        _registry().run("echo", "explode")
        assert False, "expected PermissionError"
    except PermissionError:
        pass


def test_queue_drains_in_order():
    registry = _registry()
    queue = WorkflowQueue()
    queue.enqueue(Job(arm="echo", action="echo", payload={"n": 1}))
    queue.enqueue(Job(arm="echo", action="echo", payload={"n": 2}))
    results = queue.drain(lambda job: registry.run(job.arm, job.action, job.payload))
    assert [r["echo"]["n"] for r in results] == [1, 2]
    assert len(queue) == 0
