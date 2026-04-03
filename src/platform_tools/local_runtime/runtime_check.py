from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.local_runtime.adapter import RuntimeUnavailableError
from platform_tools.local_runtime.config import load_local_orchestration_config, validate_repo_target
from platform_tools.local_runtime.ollama_adapter import OllamaAdapter
from platform_tools.local_runtime.types import API_VERSION, PROBLEM_TYPES


COMMAND = "local-runtime-check"


def _evidence(kind: str, value: str) -> str:
    return f"{kind}:{value}"


def _problem(*, blocker: str, command: str, detail: str) -> dict[str, Any]:
    return {
        "type": PROBLEM_TYPES[blocker],
        "title": blocker.replace("_", " "),
        "status": 503 if blocker in {"required_local_runtime_missing", "runtime_endpoint_unreachable"} else 400,
        "detail": detail,
        "command": command,
        "api_version": API_VERSION,
        "blockers": [blocker],
    }


def _adapter_for_backend(backend: str) -> OllamaAdapter:
    if backend != "ollama":
        raise ValueError("unsupported_backend")
    return OllamaAdapter()


def check_local_runtime(
    *,
    root: str = ".",
    repo_root: str | None = None,
    backend: str | None = None,
    model: str | None = None,
    required_models: list[str] | None = None,
    verify_managed_repo: bool = False,
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    config = load_local_orchestration_config(root=root_path.as_posix())
    selected_backend = (backend or str(config.get("runtime_profile", {}).get("default_backend", "ollama"))).strip()
    blockers = validate_repo_target(config=config, repo_root=repo_root if verify_managed_repo else None)
    if selected_backend != "ollama":
        blockers.append("unsupported_backend")
    if blockers:
        report = {
            "api_version": API_VERSION,
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "backend": selected_backend,
            "runtime": {"backend": selected_backend, "reachable": False, "models_checked": []},
            "repo_root": (repo_root or "").strip(),
            "blockers": sorted(set(blockers)),
            "next_validations": ["bin/local-runtime-check"],
            "evidence_refs": [_evidence("spec", "spec/local-orchestration.yaml")],
            "problem": _problem(blocker=blockers[0], command=COMMAND, detail="runtime check preconditions failed"),
        }
        return 1, report

    requested_models = [item for item in (required_models or []) if str(item).strip()]
    if model and model.strip() and model.strip() not in requested_models:
        requested_models.append(model.strip())
    adapter = _adapter_for_backend(selected_backend)
    try:
        probe = adapter.runtime_probe(required_models=requested_models)
    except RuntimeUnavailableError as exc:
        blocker = "runtime_endpoint_unreachable"
        report = {
            "api_version": API_VERSION,
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "backend": selected_backend,
            "runtime": {"backend": selected_backend, "reachable": False, "models_checked": requested_models},
            "repo_root": (repo_root or "").strip(),
            "blockers": [blocker],
            "next_validations": ["bin/local-runtime-check"],
            "evidence_refs": [
                _evidence("spec", "spec/local-orchestration.yaml"),
                _evidence("command", "bin/local-runtime-check"),
            ],
            "problem": _problem(blocker=blocker, command=COMMAND, detail=str(exc)),
        }
        return 1, report

    missing = probe.pop("missing_models", [])
    blockers = ["configured_model_unavailable"] if missing else []
    report = {
        "api_version": API_VERSION,
        "command": COMMAND,
        "status": "ok" if not blockers else "blocked",
        "ok": not blockers,
        "backend": selected_backend,
        "runtime": probe,
        "repo_root": (repo_root or "").strip(),
        "blockers": blockers,
        "next_validations": ["bin/local-task-router"] if not blockers else ["bin/local-runtime-check"],
        "evidence_refs": [
            _evidence("spec", "spec/local-orchestration.yaml"),
            _evidence("spec", "spec/local-orchestration-api.schema.yaml"),
            _evidence("command", "bin/local-runtime-check"),
        ],
    }
    if blockers:
        report["problem"] = _problem(
            blocker=blockers[0],
            command=COMMAND,
            detail=f"missing configured models: {', '.join(missing)}",
        )
    return (0 if not blockers else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--backend", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--required-model", action="append", dest="required_models")
    parser.add_argument("--verify-managed-repo", action="store_true")
    args = parser.parse_args()
    code, report = check_local_runtime(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
