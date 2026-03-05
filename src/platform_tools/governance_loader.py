from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import yaml

ENGINE_CONFIG_PATH = Path("platform.engine.yaml")


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _dedup_strings(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = str(item).strip()
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _load_local_policy() -> dict[str, Any]:
    ruleset = _load_yaml(Path("spec/ruleset.yaml"))
    workflow = _load_yaml(Path("spec/workflow.yaml"))
    governance = _load_yaml(Path("spec/governance.yaml"))

    allowed: list[str] = []
    exec_constraints = ruleset.get("execution_constraints", {})
    allowed.extend(str(p).strip() for p in exec_constraints.get("allowed_branch_patterns", []) or [])

    exec_requirements = workflow.get("execution_requirements", {})
    workflow_patterns = exec_requirements.get("workflow_branch_patterns", {}) or {}
    if isinstance(workflow_patterns, dict):
        allowed.extend(str(v).strip() for v in workflow_patterns.values())

    forbidden = {""}
    protected = exec_requirements.get("protected_branches_disallowed_for_execution", []) or []
    forbidden.update(str(v).strip() for v in protected if str(v).strip())

    required_contract = ((governance.get("required_checks") or {}).get("contract", []) or [])
    required_names = []
    for item in required_contract:
        if isinstance(item, dict):
            name = str(item.get("name", "")).strip()
            if name:
                required_names.append(name)

    return {
        "allowed_branch_patterns": _dedup_strings(allowed),
        "forbidden_branches": sorted(forbidden),
        "required_check_names": _dedup_strings(required_names),
    }


def _load_external_baseline(path: Path) -> dict[str, Any]:
    profile = _load_yaml(path)
    controls = profile.get("controls", [])
    if not isinstance(controls, list):
        controls = []

    protected_branches: list[str] = []
    required_checks: list[str] = []
    for control in controls:
        if not isinstance(control, dict):
            continue
        cid = str(control.get("id", "")).strip()
        details = control.get("details", {}) if isinstance(control.get("details"), dict) else {}
        if cid == "branch.protection":
            branch = str(details.get("protected_branch", "")).strip()
            if branch:
                protected_branches.append(branch)
        if cid == "checks.required":
            checks = details.get("checks", [])
            if isinstance(checks, list):
                required_checks.extend(str(item).strip() for item in checks)

    return {
        "protected_branches": _dedup_strings(protected_branches),
        "required_check_names": _dedup_strings(required_checks),
    }


def resolve_runtime_mode(
    mode_override: str | None = None,
    source_override: str | None = None,
) -> dict[str, str]:
    config = _load_yaml(ENGINE_CONFIG_PATH)
    runtime = config.get("runtime", {}) if isinstance(config.get("runtime"), dict) else {}
    mode = (
        mode_override
        or os.environ.get("PLATFORM_ENGINE_MODE")
        or str(runtime.get("mode", "standalone")).strip()
        or "standalone"
    )
    source = (
        source_override
        or os.environ.get("PLATFORM_GOVERNANCE_SOURCE")
        or str(runtime.get("governance_source", "")).strip()
    )
    return {"mode": mode, "governance_source": source}


def build_effective_policy(
    mode_override: str | None = None,
    source_override: str | None = None,
) -> tuple[int, dict[str, Any]]:
    runtime = resolve_runtime_mode(mode_override=mode_override, source_override=source_override)
    mode = runtime["mode"]
    source = runtime["governance_source"]
    findings: list[str] = []

    local = _load_local_policy()
    effective = {
        "allowed_branch_patterns": list(local["allowed_branch_patterns"]),
        "forbidden_branches": list(local["forbidden_branches"]),
        "required_check_names": list(local["required_check_names"]),
    }
    external: dict[str, Any] = {}

    if mode not in {"standalone", "managed"}:
        findings.append(f"invalid_runtime_mode:{mode}")
        mode = "standalone"

    if mode == "managed":
        if not source:
            findings.append("managed_mode_missing_governance_source")
        else:
            source_path = Path(source)
            if not source_path.exists():
                findings.append(f"managed_mode_governance_source_missing:{source}")
            else:
                external = _load_external_baseline(source_path)
                effective["forbidden_branches"] = sorted(
                    set(effective["forbidden_branches"]) | set(external["protected_branches"])
                )
                ext_checks = set(external["required_check_names"])
                local_checks = set(local["required_check_names"])
                missing = sorted(ext_checks - local_checks)
                if missing:
                    for check in missing:
                        findings.append(f"managed_mode_weakening_missing_local_required_check:{check}")
                effective["required_check_names"] = sorted(local_checks | ext_checks)

    report = {
        "tool": "governance_loader",
        "runtime": {"mode": mode, "governance_source": source},
        "local_policy": local,
        "external_baseline": external,
        "effective_policy": effective,
        "finding_count": len(findings),
        "findings": sorted(set(findings)),
    }
    return (1 if findings else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default=None)
    parser.add_argument("--governance-source", default=None)
    args = parser.parse_args()
    code, report = build_effective_policy(mode_override=args.mode, source_override=args.governance_source)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
