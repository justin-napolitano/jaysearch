from __future__ import annotations

from typing import Any


API_VERSION = "public-orchestration.v1"


def envelope(*, command: str, status: str, ok: bool, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = {
        "api_version": API_VERSION,
        "command": command,
        "status": status,
        "ok": ok,
    }
    if payload:
        body.update(payload)
    return body
