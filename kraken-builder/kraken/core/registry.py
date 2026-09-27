from __future__ import annotations

from kraken.core.schema import ArmManifest


class Registry:
    def __init__(self) -> None:
        self._arms: dict[str, ArmManifest] = {}

    def register(self, arm: ArmManifest) -> None:
        self._arms[arm.name] = arm

    def load_all(self, arms: list[ArmManifest]) -> None:
        for arm in arms:
            self.register(arm)

    def get(self, name: str) -> ArmManifest:
        if name not in self._arms:
            raise KeyError(f"arm not loaded: {name}")
        return self._arms[name]

    def names(self) -> list[str]:
        return sorted(self._arms)

    def run(self, arm_name: str, action: str, payload: dict | None = None) -> dict:
        return self.get(arm_name).invoke(action, payload)
