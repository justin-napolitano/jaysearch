from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
from typing import Any

from platform_tools.public_orchestration_api import API_VERSION, envelope


COMMAND = "run-research-capability"


def _load_request(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("request_payload_not_object")
    return payload


def _validate_researcher_root(path: Path) -> list[str]:
    blockers: list[str] = []
    if not path.exists():
        return ["researcher_root_missing"]
    if not (path / "pyproject.toml").exists():
        blockers.append("researcher_root_missing_pyproject")
    if not (path / "src" / "researcher_harness" / "cli.py").exists():
        blockers.append("researcher_root_missing_cli")
    return blockers


def _validate_request_payload(payload: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    required = ["request_id", "question_id", "study_design", "artifact_contract", "output_root"]
    for field in required:
        if not str(payload.get(field, "")).strip():
            blockers.append(f"request_missing_{field}")
    return blockers


def run_research_capability(
    *,
    root: str = ".",
    researcher_root: str,
    request_path: str,
    python_executable: str = "python3",
) -> tuple[int, dict[str, Any]]:
    platform_root = Path(root).resolve()
    researcher_repo = Path(researcher_root).resolve()
    request_file = Path(request_path).resolve()

    blockers: list[str] = []
    blockers.extend(_validate_researcher_root(researcher_repo))
    if not request_file.exists():
        blockers.append("request_path_missing")

    payload: dict[str, Any] = {}
    if not blockers:
        try:
            payload = _load_request(request_file)
        except (json.JSONDecodeError, OSError, ValueError):
            blockers.append("request_payload_invalid")
    if payload:
        blockers.extend(_validate_request_payload(payload))

    if blockers:
        return 1, envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "api_version": API_VERSION,
                "platform_root": platform_root.as_posix(),
                "researcher_root": researcher_repo.as_posix(),
                "request_path": request_file.as_posix(),
                "blockers": sorted(set(blockers)),
            },
        )

    env = os.environ.copy()
    pythonpath = str(researcher_repo / "src")
    env["PYTHONPATH"] = pythonpath if not env.get("PYTHONPATH") else f"{pythonpath}:{env['PYTHONPATH']}"
    completed = subprocess.run(
        [
            python_executable,
            "-m",
            "researcher_harness.cli",
            "run",
            "--request",
            request_file.as_posix(),
        ],
        cwd=researcher_repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        return 1, envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "platform_root": platform_root.as_posix(),
                "researcher_root": researcher_repo.as_posix(),
                "request_path": request_file.as_posix(),
                "blockers": ["researcher_execution_failed"],
                "stderr": stderr,
            },
        )

    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return 1, envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "platform_root": platform_root.as_posix(),
                "researcher_root": researcher_repo.as_posix(),
                "request_path": request_file.as_posix(),
                "blockers": ["researcher_response_invalid_json"],
            },
        )

    if not isinstance(response, dict):
        return 1, envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "platform_root": platform_root.as_posix(),
                "researcher_root": researcher_repo.as_posix(),
                "request_path": request_file.as_posix(),
                "blockers": ["researcher_response_not_object"],
            },
        )

    artifact_paths = response.get("artifact_paths", {})
    summary_path = str(artifact_paths.get("summary", "")).strip() if isinstance(artifact_paths, dict) else ""
    return 0, envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "platform_root": platform_root.as_posix(),
            "researcher_root": researcher_repo.as_posix(),
            "request_path": request_file.as_posix(),
            "request_id": str(response.get("request_id", "")).strip(),
            "research_status": str(response.get("status", "")).strip(),
            "output_root": str(response.get("output_root", "")).strip(),
            "recommendation": str(response.get("recommendation", "")).strip(),
            "summary_path": summary_path,
            "self_review_path": str(response.get("self_review_path", "")).strip(),
            "artifact_paths": artifact_paths if isinstance(artifact_paths, dict) else {},
            "warnings": [str(item).strip() for item in response.get("warnings", []) if str(item).strip()],
            "blockers": [],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--researcher-root", required=True)
    parser.add_argument("--request-path", required=True)
    parser.add_argument("--python-executable", default="python3")
    args = parser.parse_args()
    code, report = run_research_capability(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
