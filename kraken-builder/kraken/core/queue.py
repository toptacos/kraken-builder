"""In-process workflow queue. Persistent backends are an arm, not core."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Job:
    arm: str
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    trigger: str = "manual"


class WorkflowQueue:
    def __init__(self) -> None:
        self._pending: deque[Job] = deque()
        self._done: list[tuple[Job, dict[str, Any]]] = []

    def enqueue(self, job: Job) -> None:
        self._pending.append(job)

    def __len__(self) -> int:
        return len(self._pending)

    def drain(self, runner: Callable[[Job], dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        while self._pending:
            job = self._pending.popleft()
            result = runner(job)
            self._done.append((job, result))
            results.append(result)
        return results
