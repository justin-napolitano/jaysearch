from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from platform_tools.branch_policy import get_current_branch
from platform_tools.get_graph_state import get_graph_state
from platform_tools.get_worker_status import get_worker_status
from platform_tools.resolve_worker_contract import resolve_worker_contract
from platform_tools.run_worker_contract import run_worker_contract
from platform_tools.start_next_worker import start_next_worker


COMMAND = "public-orchestration-api-check"
SCHEMA_PATH = Path("spec/public-orchestration-api.schema.yaml")


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def _schema_defs(schema: dict[str, Any]) -> dict[str, Any]:
    defs = schema.get("$defs", {})
    return defs if isinstance(defs, dict) else {}


def _required_fields(schema: dict[str, Any], def_name: str) -> list[str]:
    defs = _schema_defs(schema)
    definition = defs.get(def_name, {})
    if not isinstance(definition, dict):
        return []
    required: list[str] = []
    for entry in definition.get("allOf", []):
        if not isinstance(entry, dict):
            continue
        required.extend([str(item).strip() for item in entry.get("required", []) if str(item).strip()])
    required.extend([str(item).strip() for item in definition.get("required", []) if str(item).strip()])
    seen: set[str] = set()
    ordered: list[str] = []
    for item in required:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def _const_command(schema: dict[str, Any], def_name: str) -> str:
    defs = _schema_defs(schema)
    definition = defs.get(def_name, {})
    if not isinstance(definition, dict):
        return ""
    for entry in definition.get("allOf", []):
        if not isinstance(entry, dict):
            continue
        command = entry.get("properties", {}).get("command", {})
        if isinstance(command, dict):
            return str(command.get("const", "")).strip()
    return ""


def _require_fields(payload: dict[str, Any], fields: list[str], prefix: str, errors: list[str]) -> None:
    for field in fields:
        if field not in payload:
            errors.append(f"missing_field:{prefix}:{field}")


def _validate_projection(payload: dict[str, Any], fields: list[str], prefix: str, errors: list[str]) -> None:
    if not isinstance(payload, dict):
        errors.append(f"invalid_object:{prefix}")
        return
    _require_fields(payload, fields, prefix, errors)


def _validate_response(
    *,
    schema: dict[str, Any],
    response_def: str,
    report: dict[str, Any],
    errors: list[str],
) -> None:
    expected_command = _const_command(schema, response_def)
    required_top = _required_fields(schema, response_def)
    _require_fields(report, required_top, response_def, errors)
    if expected_command and str(report.get("command", "")).strip() != expected_command:
        errors.append(f"invalid_command:{response_def}:{report.get('command', '')}")
    api_version = str(report.get("api_version", "")).strip()
    expected_version = str(schema.get("properties", {}).get("api_version", {}).get("const", "")).strip()
    if expected_version and api_version != expected_version:
        errors.append(f"invalid_api_version:{response_def}:{api_version}")
    if str(report.get("status", "")).strip() not in {"ok", "blocked"}:
        errors.append(f"invalid_status:{response_def}:{report.get('status', '')}")
    if not isinstance(report.get("ok"), bool):
        errors.append(f"invalid_ok_type:{response_def}")

    defs = _schema_defs(schema)
    graph_fields = [str(item).strip() for item in defs.get("graph_node_projection", {}).get("required", []) if str(item).strip()]
    contract_fields = [str(item).strip() for item in defs.get("worker_contract_projection", {}).get("required", []) if str(item).strip()]
    run_contract_fields = [
        str(item).strip() for item in defs.get("worker_contract_run_projection", {}).get("required", []) if str(item).strip()
    ]

    if response_def == "response_get_graph_state":
        counts = report.get("counts", {})
        _validate_projection(counts if isinstance(counts, dict) else {}, ["nodes", "completed", "pending"], "counts", errors)
        for key in ("initiative_nodes", "queued_nodes"):
            items = report.get(key, [])
            if not isinstance(items, list):
                errors.append(f"invalid_list:{key}")
                continue
            for index, item in enumerate(items, start=1):
                _validate_projection(item, graph_fields, f"{key}:{index}", errors)
        active = report.get("active_node")
        if active is not None:
            _validate_projection(active if isinstance(active, dict) else {}, graph_fields, "active_node", errors)

    if response_def == "response_resolve_worker_contract":
        selected = report.get("selected")
        if selected is not None:
            _validate_projection(selected if isinstance(selected, dict) else {}, contract_fields, "selected", errors)
        blockers = report.get("blockers")
        if blockers is not None and not isinstance(blockers, list):
            errors.append("invalid_list:blockers")

    if response_def == "response_run_worker_contract":
        selected = report.get("selected")
        if isinstance(selected, dict) and selected:
            _validate_projection(selected, run_contract_fields, "selected", errors)
        if "worker_run" in report and not isinstance(report.get("worker_run"), dict):
            errors.append("invalid_object:worker_run")

    if response_def == "response_start_next_worker":
        if not isinstance(report.get("resolution"), dict):
            errors.append("invalid_object:resolution")
        if "worker_run" in report and not isinstance(report.get("worker_run"), dict):
            errors.append("invalid_object:worker_run")

    if response_def == "response_get_worker_status":
        for key in ("active_workers", "failed_workers", "abandoned_workers", "recent_runs", "blockers"):
            value = report.get(key)
            if value is not None and not isinstance(value, list):
                errors.append(f"invalid_list:{key}")


def check_public_orchestration_api(
    *,
    root: str = ".",
    initiative_branch: str | None = None,
    worker_id: str | None = None,
) -> tuple[int, dict[str, Any]]:
    base = Path(root).resolve()
    schema_path = base / SCHEMA_PATH
    if not schema_path.exists():
        return 1, {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "errors": ["missing_public_orchestration_api_schema"],
            "error_count": 1,
            "evidence_refs": [],
        }

    schema = _load_yaml(schema_path)
    current_branch = get_current_branch(root=base)
    resolved_initiative = (initiative_branch or "").strip()
    if not resolved_initiative and current_branch.startswith("initiative/"):
        resolved_initiative = current_branch

    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    code, report = get_graph_state(root=base.as_posix(), initiative_branch=resolved_initiative or None)
    check_errors: list[str] = []
    _validate_response(schema=schema, response_def="response_get_graph_state", report=report, errors=check_errors)
    checks.append({"name": "get_graph_state", "ok": code in {0, 1} and not check_errors, "errors": check_errors})
    errors.extend(f"get_graph_state:{item}" for item in check_errors)

    code, report = resolve_worker_contract(root=base.as_posix(), initiative_branch=resolved_initiative or None)
    check_errors = []
    _validate_response(schema=schema, response_def="response_resolve_worker_contract", report=report, errors=check_errors)
    checks.append({"name": "resolve_worker_contract", "ok": code in {0, 1} and not check_errors, "errors": check_errors})
    errors.extend(f"resolve_worker_contract:{item}" for item in check_errors)

    code, report = get_worker_status(root=base.as_posix(), worker_id=worker_id)
    check_errors = []
    _validate_response(schema=schema, response_def="response_get_worker_status", report=report, errors=check_errors)
    checks.append({"name": "get_worker_status", "ok": code in {0, 1} and not check_errors, "errors": check_errors})
    errors.extend(f"get_worker_status:{item}" for item in check_errors)

    code, report = run_worker_contract(
        root=base.as_posix(),
        initiative_branch=resolved_initiative or None,
        executor="local_clone",
        push_mode="github",
    )
    check_errors = []
    _validate_response(schema=schema, response_def="response_run_worker_contract", report=report, errors=check_errors)
    checks.append({"name": "run_worker_contract", "ok": code in {0, 1} and not check_errors, "errors": check_errors})
    errors.extend(f"run_worker_contract:{item}" for item in check_errors)

    code, report = start_next_worker(
        root=base.as_posix(),
        initiative_branch=resolved_initiative or None,
        executor="local_clone",
        push_mode="staging",
    )
    check_errors = []
    _validate_response(schema=schema, response_def="response_start_next_worker", report=report, errors=check_errors)
    checks.append({"name": "start_next_worker", "ok": code in {0, 1} and not check_errors, "errors": check_errors})
    errors.extend(f"start_next_worker:{item}" for item in check_errors)

    report = {
        "command": COMMAND,
        "status": "ok" if not errors else "blocked",
        "ok": not errors,
        "checks": checks,
        "errors": sorted(errors),
        "error_count": len(sorted(errors)),
        "evidence_refs": [schema_path.as_posix()],
    }
    return (0 if not errors else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--initiative-branch", default=None)
    parser.add_argument("--worker-id", default=None)
    args = parser.parse_args()
    code, report = check_public_orchestration_api(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
