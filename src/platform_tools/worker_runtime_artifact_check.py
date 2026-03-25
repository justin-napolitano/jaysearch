from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


COMMAND = "worker-runtime-artifact-check"
RUNTIME_EVENT_LOG = Path("artifacts/governance/worker-runtime-events.jsonl")
RUN_DIR = Path("artifacts/governance/worker-runs")
PROBLEM_DIR = Path("artifacts/governance/problems")
EVENT_SCHEMA = Path("spec/worker-runtime-event.schema.yaml")
PROBLEM_SCHEMA = Path("spec/worker-problem-artifact.schema.yaml")


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def check_worker_runtime_artifacts(*, root: str = ".") -> tuple[int, dict[str, Any]]:
    base = Path(root)
    event_log_path = base / RUNTIME_EVENT_LOG
    run_dir = base / RUN_DIR
    problem_dir = base / PROBLEM_DIR
    event_schema_path = base / EVENT_SCHEMA
    problem_schema_path = base / PROBLEM_SCHEMA

    errors: list[str] = []
    evidence_refs = [path.as_posix() for path in [event_log_path, run_dir, problem_dir, event_schema_path, problem_schema_path] if path.exists()]

    if not event_schema_path.exists():
        errors.append("missing_worker_runtime_event_schema")
    if not problem_schema_path.exists():
        errors.append("missing_worker_problem_artifact_schema")
    if errors:
        return 1, {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "errors": sorted(errors),
            "error_count": len(sorted(errors)),
            "evidence_refs": sorted(evidence_refs),
        }

    event_schema = _load_yaml(event_schema_path)
    problem_schema = _load_yaml(problem_schema_path)
    event_records: list[dict[str, Any]] = []
    if event_log_path.exists():
        for index, line in enumerate(event_log_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                errors.append(f"invalid_runtime_event_record_type:{index}")
                continue
            event_records.append(payload)

    required_event_fields = set(event_schema.get("event_envelope", {}).get("required_fields", []))
    required_data_fields = set(event_schema.get("data", {}).get("required_fields", []))
    summary_max = int(event_schema.get("token_economy", {}).get("summary_max_chars", 160))
    allowed_type_prefixes = tuple(event_schema.get("event_envelope", {}).get("type_prefixes_allowed", []))
    allowed_specversions = set(event_schema.get("event_envelope", {}).get("specversion_allowed", []))
    allowed_content_types = set(event_schema.get("event_envelope", {}).get("datacontenttype_allowed", []))

    for index, event in enumerate(event_records, start=1):
        for field in required_event_fields:
            if field not in event:
                errors.append(f"missing_runtime_event_field:{index}:{field}")
        if allowed_specversions and str(event.get("specversion", "")).strip() not in allowed_specversions:
            errors.append(f"invalid_runtime_event_specversion:{index}:{event.get('specversion', '')}")
        if allowed_content_types and str(event.get("datacontenttype", "")).strip() not in allowed_content_types:
            errors.append(f"invalid_runtime_event_datacontenttype:{index}:{event.get('datacontenttype', '')}")
        event_type = str(event.get("type", "")).strip()
        if allowed_type_prefixes and not event_type.startswith(allowed_type_prefixes):
            errors.append(f"invalid_runtime_event_type:{index}:{event_type}")
        data = event.get("data", {})
        if not isinstance(data, dict):
            errors.append(f"invalid_runtime_event_data_type:{index}")
            continue
        for field in required_data_fields:
            if field not in data:
                errors.append(f"missing_runtime_event_data_field:{index}:{field}")
        summary = str(data.get("summary", "")).strip()
        if len(summary) > summary_max:
            errors.append(f"runtime_event_summary_too_long:{index}")

    problem_paths = sorted(problem_dir.glob("*.problem.json")) if problem_dir.exists() else []
    required_problem_fields = set(problem_schema.get("required_fields", []))
    detail_max = int(problem_schema.get("token_economy", {}).get("detail_max_chars", 280))
    for path in problem_paths:
        payload = _load_json(path)
        if not isinstance(payload, dict):
            errors.append(f"invalid_problem_record_type:{path.as_posix()}")
            continue
        for field in required_problem_fields:
            if field not in payload:
                errors.append(f"missing_problem_field:{path.name}:{field}")
        if not isinstance(payload.get("status"), int):
            errors.append(f"invalid_problem_status_type:{path.name}")
        detail = str(payload.get("detail", "")).strip()
        if len(detail) > detail_max:
            errors.append(f"problem_detail_too_long:{path.name}")
        markdown_path = path.with_suffix(".md")
        if not markdown_path.exists():
            errors.append(f"missing_problem_markdown:{markdown_path.name}")

    run_paths = sorted(run_dir.glob("*.json")) if run_dir.exists() else []
    for path in run_paths:
        payload = _load_json(path)
        if not isinstance(payload, dict):
            errors.append(f"invalid_run_record_type:{path.as_posix()}")
            continue
        for field in ("run_id", "trace_id", "worker_id", "branch", "executor_backend", "push_targets", "token_economy_policy"):
            if field not in payload:
                errors.append(f"missing_run_field:{path.name}:{field}")
        if str(payload.get("run_id", "")).strip() != path.stem:
            errors.append(f"run_id_path_mismatch:{path.name}")
        if payload.get("problem_ref"):
            problem_ref = base / str(payload.get("problem_ref", "")).strip()
            if not problem_ref.exists():
                errors.append(f"missing_run_problem_ref:{path.name}")

    report = {
        "command": COMMAND,
        "status": "ok" if not errors else "blocked",
        "ok": not errors,
        "counts": {
            "runtime_events": len(event_records),
            "runs": len(run_paths),
            "problems": len(problem_paths),
        },
        "errors": sorted(errors),
        "error_count": len(sorted(errors)),
        "evidence_refs": sorted(evidence_refs),
    }
    return (1 if errors else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    code, report = check_worker_runtime_artifacts(root=args.root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
