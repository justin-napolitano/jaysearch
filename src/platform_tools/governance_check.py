from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from platform_tools.governance_loader import build_effective_policy
from platform_tools.plan_utils import list_execplans, parse_plan


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _parse_iso8601(value: str) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        if value.endswith("Z"):
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(value).astimezone(timezone.utc)
    except ValueError:
        return None


def _collect_execplan_tests() -> list[dict[str, Any]]:
    tests: list[dict[str, Any]] = []
    for path in list_execplans(tracked_only=True):
        parsed = parse_plan(path)
        fm = parsed.frontmatter
        if not fm:
            continue
        plan_id = str(fm.get("id", "")).strip() or path.stem
        validation = fm.get("validation", {})
        if not isinstance(validation, dict):
            continue
        raw_tests = validation.get("tests", [])
        if not isinstance(raw_tests, list):
            continue
        for idx, item in enumerate(raw_tests):
            if not isinstance(item, dict):
                continue
            tests.append(
                {
                    "plan_id": plan_id,
                    "order": idx,
                    "name": str(item.get("name", "")).strip(),
                    "command": str(item.get("command", "")).strip(),
                    "expected_exit": int(item.get("expected_exit", 0)),
                }
            )
    tests.sort(key=lambda x: (x["name"], x["command"], x["plan_id"], x["order"]))
    return tests


def check_governance() -> tuple[int, dict[str, Any]]:
    spec_path = Path("spec/governance.yaml")
    spec = _load_yaml(spec_path)
    findings: list[str] = []
    loader_code, loader_report = build_effective_policy()
    if loader_code != 0:
        findings.extend(str(f) for f in loader_report.get("findings", []))

    required_checks = spec.get("required_checks", {})
    name_regex = str(required_checks.get("name_regex", r"^[a-z][a-z0-9_]*$"))
    pattern = re.compile(name_regex)
    contract = required_checks.get("contract", [])
    local_contract_map: dict[str, tuple[str, int]] = {}
    if isinstance(contract, list):
        for item in contract:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            command = str(item.get("command", "")).strip()
            expected_exit = int(item.get("expected_exit", 0))
            if name and command:
                local_contract_map[name] = (command, expected_exit)

    effective = loader_report.get("effective_policy", {})
    effective_required_names = []
    if isinstance(effective, dict):
        raw_names = effective.get("required_check_names", [])
        if isinstance(raw_names, list):
            effective_required_names = sorted(
                {str(item).strip() for item in raw_names if str(item).strip()}
            )

    tests = _collect_execplan_tests()
    by_name: dict[str, set[str]] = {}
    by_tuple: set[tuple[str, str, int]] = set()
    for item in tests:
        name = item["name"]
        command = item["command"]
        expected_exit = item["expected_exit"]
        by_name.setdefault(name, set()).add(command)
        by_tuple.add((name, command, expected_exit))
        if not pattern.match(name):
            findings.append(f"required_check_name_invalid:{name}")

    for name, commands in by_name.items():
        if len(commands) > 1:
            findings.append(f"required_check_name_command_drift:{name}")

    if not effective_required_names:
        findings.append("missing_effective_required_checks")
    for name in effective_required_names:
        if not pattern.match(name):
            findings.append(f"required_check_name_invalid:{name}")
        if name in local_contract_map:
            cmd, expected_exit = local_contract_map[name]
            if (name, cmd, expected_exit) not in by_tuple:
                findings.append(f"required_check_contract_missing:{name}")
        elif name not in by_name:
            findings.append(f"required_check_contract_missing:{name}")

    lifecycle = spec.get("exception_lifecycle", {})
    registry_path = Path(str(lifecycle.get("registry_path", ".agent/governance/exceptions.yaml")))
    required_fields = lifecycle.get("required_fields", [])
    valid_statuses = set(lifecycle.get("statuses", ["active", "expired", "revoked"]))
    renewal_window = int(lifecycle.get("renewal_window_days", 7))
    bypass_min_items = int(lifecycle.get("bypass_evidence_min_items", 1))

    registry = _load_yaml(registry_path)
    exceptions = registry.get("exceptions", [])
    if not isinstance(exceptions, list):
        findings.append("invalid_exception_registry")
        exceptions = []

    now = datetime.now(timezone.utc)
    for idx, exc in enumerate(exceptions):
        tag = f"exception[{idx}]"
        if not isinstance(exc, dict):
            findings.append(f"{tag}:invalid_entry")
            continue
        for field in required_fields:
            if field not in exc or exc.get(field) in ("", None, []):
                findings.append(f"{tag}:missing_field:{field}")

        status = str(exc.get("status", "")).strip()
        if status and status not in valid_statuses:
            findings.append(f"{tag}:invalid_status:{status}")

        created = _parse_iso8601(str(exc.get("created_at", "")))
        expires = _parse_iso8601(str(exc.get("expires_at", "")))
        if created is None:
            findings.append(f"{tag}:invalid_created_at")
        if expires is None:
            findings.append(f"{tag}:invalid_expires_at")
        if created and expires and expires <= created:
            findings.append(f"{tag}:expires_before_created")

        if status == "active" and expires and expires < now:
            findings.append(f"{tag}:active_but_expired")

        bypass_evidence = exc.get("bypass_evidence", [])
        if not isinstance(bypass_evidence, list) or len(bypass_evidence) < bypass_min_items:
            findings.append(f"{tag}:insufficient_bypass_evidence")

        if status == "active" and expires is not None:
            days_left = (expires - now).days
            renewal = exc.get("renewal", {})
            renewal_evidence = renewal.get("evidence", []) if isinstance(renewal, dict) else []
            if days_left <= renewal_window and (not isinstance(renewal_evidence, list) or not renewal_evidence):
                findings.append(f"{tag}:renewal_evidence_required")

    findings = sorted(set(findings))
    report = {
        "tool": "governance_check",
        "spec_path": spec_path.as_posix(),
        "registry_path": registry_path.as_posix(),
        "required_check_count": len(contract),
        "effective_required_check_count": len(effective_required_names),
        "observed_test_count": len(tests),
        "exception_count": len(exceptions),
        "finding_count": len(findings),
        "findings": findings,
    }
    return (1 if findings else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    code, report = check_governance()
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
