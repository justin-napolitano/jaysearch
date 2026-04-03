from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LocalRuntimeError(RuntimeError):
    pass


class RuntimeUnavailableError(LocalRuntimeError):
    pass


class LocalRuntimeAdapter(ABC):
    @abstractmethod
    def runtime_probe(self, *, required_models: list[str] | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def generate_json(
        self,
        *,
        model: str,
        prompt: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        raise NotImplementedError
