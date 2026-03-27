from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from platform_tools.control_plane import API_VERSION
from platform_tools.get_control_plane_status import get_control_plane_status
from platform_tools.get_next_orchestration_action import get_next_orchestration_action


COMMAND = "control-plane-api-check"
SCHEMA_PATH = Path("spec/control-plane-api.schema.yaml")


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
        if isinstance(entry, dict):
            required.extend([str(item).strip() for item in entry.get("required", []) if str(item).strip()])
    required.extend([str(item).strip() for item in definition.get("required", []) if str(item).strip()])
    seen: set[str] = set()
    ordered: list[str] = []
    for item in required:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
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


def _validate_response(*, schema: dict[str, Any], response_def: str, report: dict[str, Any], errors: list[str]) -> None:
    expected_command = _const_command(schema, response_def)
    _require_fields(report, _required_fields(schema, response_def), response_def, errors)
    if expected_command and str(report.get("command", "")).strip() != expected_command:
        errors.append(f"invalid_command:{response_def}:{report.get('command', '')}")
    if str(report.get("api_version", "")).strip() != API_VERSION:
        errors.append(f"invalid_api_version:{response_def}:{report.get('api_version', '')}")
    if str(report.get("status", "")).strip() not in {"ok", "blocked"}:
        errors.append(f"invalid_status:{response_def}:{report.get('status', '')}")
    if not isinstance(report.get("ok"), bool):
        errors.append(f"invalid_ok_type:{response_def}")
    blockers = report.get("blockers")
    if blockers is not None and not isinstance(blockers, list):
        errors.append(f"invalid_list:{response_def}:blockers")


def check_control_plane_api(*, root: str = ".") -> tuple[int, dict[str, Any]]:
    base = Path(root).resolve()
    schema_path = base / SCHEMA_PATH
    if not schema_path.exists():
        return 1, {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "errors": ["missing_control_plane_api_schema"],
            "error_count": 1,
            "evidence_refs": [],
        }

    schema = _load_yaml(schema_path)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    code, report = get_control_plane_status(root=base.as_posix())
    check_errors: list[str] = []
    _validate_response(schema=schema, response_def="response_get_control_plane_status", report=report, errors=check_errors)
    checks.append({"name": "get_control_plane_status", "ok": code in {0, 1} and not check_errors, "errors": check_errors})
    errors.extend(f"get_control_plane_status:{item}" for item in check_errors)

    code, report = get_next_orchestration_action(root=base.as_posix())
    check_errors = []
    _validate_response(schema=schema, response_def="response_get_next_orchestration_action", report=report, errors=check_errors)
    checks.append({"name": "get_next_orchestration_action", "ok": code in {0, 1} and not check_errors, "errors": check_errors})
    errors.extend(f"get_next_orchestration_action:{item}" for item in check_errors)

    final_report = {
        "command": COMMAND,
        "status": "ok" if not errors else "blocked",
        "ok": not errors,
        "checks": checks,
        "errors": sorted(errors),
        "error_count": len(sorted(errors)),
        "evidence_refs": [schema_path.as_posix()],
    }
    return (0 if not errors else 1), final_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    code, report = check_control_plane_api(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
