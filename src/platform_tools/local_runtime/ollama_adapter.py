from __future__ import annotations

import json
import os
import time
from typing import Any, Callable
from urllib import error, request

from platform_tools.local_runtime.adapter import LocalRuntimeAdapter, RuntimeUnavailableError


JsonRequest = Callable[[str, str, dict[str, Any] | None], dict[str, Any]]


def _default_request(base_url: str, method: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = request.Request(
        base_url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "platform-template-bootstrap/local-runtime"},
        method=method,
    )
    with request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


class OllamaAdapter(LocalRuntimeAdapter):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        requester: JsonRequest | None = None,
    ) -> None:
        host = (base_url or os.environ.get("OLLAMA_HOST", "").strip() or "http://127.0.0.1:11434").rstrip("/")
        self.base_url = host
        self._requester = requester or _default_request

    def _request(self, path: str, *, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            return self._requester(f"{self.base_url}{path}", method, payload)
        except (TimeoutError, error.URLError, ConnectionError, json.JSONDecodeError, OSError) as exc:
            raise RuntimeUnavailableError(str(exc)) from exc

    def runtime_probe(self, *, required_models: list[str] | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        response = self._request("/api/tags", method="GET")
        latency_ms = int((time.perf_counter() - started) * 1000)
        models = response.get("models", [])
        available = {
            str(item.get("name", "")).strip()
            for item in models
            if isinstance(item, dict) and str(item.get("name", "")).strip()
        }
        requested = [item for item in (required_models or []) if item.strip()]
        return {
            "backend": "ollama",
            "reachable": True,
            "models_checked": requested,
            "endpoint": f"{self.base_url}/api/tags",
            "latency_ms": latency_ms,
            "available_models": sorted(available),
            "missing_models": [item for item in requested if item not in available],
        }

    def generate_json(
        self,
        *,
        model: str,
        prompt: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        response = self._request(
            "/api/generate",
            method="POST",
            payload={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": temperature},
            },
        )
        raw = str(response.get("response", "")).strip()
        if not raw:
            raise RuntimeUnavailableError("empty_ollama_response")
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise RuntimeUnavailableError("invalid_ollama_json_object")
        return parsed
