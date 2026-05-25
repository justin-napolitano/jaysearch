from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from platform_tools.public_orchestration_api import envelope


COMMAND = "validate-node-readiness"
DEFAULT_POLICY_PATH = "spec/node-readiness-policy.yaml"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"policy_not_object:{path.as_posix()}")
    return payload


def _has_value(payload: dict[str, Any], field: str) -> bool:
    if field not in payload:
        return False
    value = payload[field]
    if value is None or value == "":
        return False
    if isinstance(value, (list, dict)) and not value:
        return False
    return True


def _missing_required(payload: dict[str, Any], fields: list[Any]) -> list[str]:
    return [str(field) for field in fields if not _has_value(payload, str(field))]


def _alternative_satisfied(payload: dict[str, Any], rule: dict[str, Any]) -> bool:
    field = str(rule.get("field", "")).strip()
    alternate_field = str(rule.get("alternate_field", "")).strip()
    marker = str(rule.get("missing_field_marker", "")).strip()
    missing_fields = payload.get("missing_fields", [])
    if _has_value(payload, field):
        return True
    if alternate_field and _has_value(payload, alternate_field):
        return True
    return bool(marker and isinstance(missing_fields, list) and marker in missing_fields)


def _missing_alternatives(payload: dict[str, Any], rules: list[Any]) -> list[str]:
    missing: list[str] = []
    for raw_rule in rules:
        if not isinstance(raw_rule, dict):
            continue
        if not _alternative_satisfied(payload, raw_rule):
            field = str(raw_rule.get("field", "")).strip()
            alternate_field = str(raw_rule.get("alternate_field", "")).strip()
            missing.append(f"{field}_or_{alternate_field}" if alternate_field else field)
    return missing


def validate_node_readiness(
    *,
    root: str = ".",
    node_path: str,
    target_state: str,
    policy_path: str = DEFAULT_POLICY_PATH,
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    payload = _load_json(repo_root / node_path)
    policy = _load_yaml(repo_root / policy_path)
    states = policy.get("states", {})
    if not isinstance(states, dict) or target_state not in states:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "target_state": target_state,
                "ready": False,
                "missing_fields": [],
                "blockers": [f"unknown_target_state:{target_state}"],
            },
        )
        return 1, report

    state_policy = states[target_state]
    if not isinstance(state_policy, dict):
        raise ValueError(f"state_policy_not_object:{target_state}")

    blockers: list[str] = []
    required_packet_type = str(state_policy.get("required_packet_type", "")).strip()
    packet_type = str(payload.get("packet_type", "")).strip()
    if required_packet_type and packet_type != required_packet_type:
        blockers.append(f"packet_type_mismatch:{packet_type or 'missing'}:{required_packet_type}")
        if packet_type == "selected_solution_scope" and target_state == "implementation_ready":
            blockers.append("selected_solution_scope_is_not_execution_unit")

    missing_fields = _missing_required(payload, state_policy.get("required_fields", []))
    missing_fields.extend(_missing_alternatives(payload, state_policy.get("alternative_required", [])))

    ready = not blockers and not missing_fields
    report = envelope(
        command=COMMAND,
        status="ok" if ready else "blocked",
        ok=ready,
        payload={
            "node_path": str((repo_root / node_path).resolve()),
            "policy_path": str((repo_root / policy_path).resolve()),
            "packet_type": packet_type,
            "readiness_state": str(payload.get("readiness_state", "")).strip(),
            "target_state": target_state,
            "ready": ready,
            "missing_fields": sorted(set(missing_fields)),
            "blockers": sorted(set(blockers)),
        },
    )
    return (0 if ready else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--node-path", required=True)
    parser.add_argument("--target-state", required=True)
    parser.add_argument("--policy-path", default=DEFAULT_POLICY_PATH)
    args = parser.parse_args()
    try:
        code, report = validate_node_readiness(
            root=args.root,
            node_path=args.node_path,
            target_state=args.target_state,
            policy_path=args.policy_path,
        )
    except (FileNotFoundError, PermissionError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={"blockers": [f"{exc.__class__.__name__}:{exc}"]},
        )
        code = 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
