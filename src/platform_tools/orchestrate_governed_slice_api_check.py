from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from platform_tools.orchestrate_governed_slice import COMMAND, run_orchestrate_governed_slice


CHECK_COMMAND = "orchestrate-governed-slice-api-check"
SCHEMA_PATH = Path("spec/orchestrate-governed-slice-api.schema.yaml")


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def _required_fields(schema: dict[str, Any]) -> list[str]:
    return [str(item).strip() for item in schema.get("required", []) if str(item).strip()]


def _check_required_fields(report: dict[str, Any], required: list[str], errors: list[str]) -> None:
    for field in required:
        if field not in report:
            errors.append(f"missing_field:{field}")


def check_orchestrate_governed_slice_api(*, root: str = ".") -> tuple[int, dict[str, Any]]:
    base = Path(root).resolve()
    schema_path = base / SCHEMA_PATH
    if not schema_path.exists():
        return 1, {
            "command": CHECK_COMMAND,
            "status": "blocked",
            "ok": False,
            "errors": ["missing_orchestrate_governed_slice_api_schema"],
            "error_count": 1,
            "evidence_refs": [],
        }

    schema = _load_yaml(schema_path)
    code, report = run_orchestrate_governed_slice(root=base.as_posix())
    errors: list[str] = []
    _check_required_fields(report, _required_fields(schema), errors)
    if str(report.get("command", "")).strip() != COMMAND:
        errors.append(f"invalid_command:{report.get('command', '')}")
    if str(report.get("status", "")).strip() not in {"ok", "blocked"}:
        errors.append(f"invalid_status:{report.get('status', '')}")
    if not isinstance(report.get("ok"), bool):
        errors.append("invalid_ok_type")
    if not isinstance(report.get("blockers", []), list):
        errors.append("invalid_blockers_type")
    if not isinstance(report.get("next_actions", []), list):
        errors.append("invalid_next_actions_type")

    final_report = {
        "command": CHECK_COMMAND,
        "status": "ok" if code in {0, 1} and not errors else "blocked",
        "ok": code in {0, 1} and not errors,
        "checks": [
            {
                "name": "orchestrate_governed_slice",
                "ok": code in {0, 1} and not errors,
                "errors": errors,
            }
        ],
        "errors": sorted(errors),
        "error_count": len(sorted(errors)),
        "evidence_refs": [schema_path.as_posix()],
    }
    return (0 if not errors else 1), final_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    code, report = check_orchestrate_governed_slice_api(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
