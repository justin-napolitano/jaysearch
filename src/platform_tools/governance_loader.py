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


def _load_local_policy(root: Path) -> dict[str, Any]:
    ruleset = _load_yaml(root / "spec" / "ruleset.yaml")
    workflow = _load_yaml(root / "spec" / "workflow.yaml")
    governance = _load_yaml(root / "spec" / "governance.yaml")

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
            name = str(item.get("check_id", "")).strip() or str(item.get("name", "")).strip()
            if name:
                required_names.append(name)

    if not allowed and isinstance(workflow.get("allowed_branch_patterns"), list):
        allowed.extend(str(p).strip() for p in workflow.get("allowed_branch_patterns", []) or [])
    if forbidden == {""} and isinstance(workflow.get("forbidden_branches"), list):
        forbidden.update(str(v).strip() for v in workflow.get("forbidden_branches", []) if str(v).strip())

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


def _load_rule_layering_spec(root: Path) -> dict[str, Any]:
    return _load_yaml(root / "spec" / "rule-layering.yaml")


def _load_project_overlay(path: Path) -> dict[str, Any]:
    data = _load_yaml(path)
    overlay = data.get("overlay", {}) if isinstance(data.get("overlay"), dict) else {}
    return overlay if isinstance(overlay, dict) else {}


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
    project_rules_source = (
        os.environ.get("PLATFORM_PROJECT_RULES_SOURCE")
        or str(runtime.get("project_rules_source", "project.rules.yaml")).strip()
        or "project.rules.yaml"
    )
    return {
        "mode": mode,
        "governance_source": source,
        "project_rules_source": project_rules_source,
    }


def build_effective_policy(
    mode_override: str | None = None,
    source_override: str | None = None,
    *,
    root: str | Path = ".",
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root)
    runtime = resolve_runtime_mode(mode_override=mode_override, source_override=source_override)
    mode = runtime["mode"]
    source = runtime["governance_source"]
    project_rules_source = runtime["project_rules_source"]
    findings: list[str] = []

    local = _load_local_policy(root_path)
    effective = {
        "allowed_branch_patterns": list(local["allowed_branch_patterns"]),
        "forbidden_branches": list(local["forbidden_branches"]),
        "required_check_names": list(local["required_check_names"]),
    }
    external: dict[str, Any] = {}
    project_overlay: dict[str, Any] = {}

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

    layering = _load_rule_layering_spec(root_path)
    project_overlay_path = root_path / project_rules_source
    if project_overlay_path.exists():
        project_overlay = _load_project_overlay(project_overlay_path)
        allowed_keys = set(
            str(item).strip()
            for item in ((layering.get("project_overlay") or {}).get("allowed_keys", []) or [])
            if str(item).strip()
        )
        forbidden_keys = set(
            str(item).strip()
            for item in ((layering.get("project_overlay") or {}).get("forbidden_keys", []) or [])
            if str(item).strip()
        )
        for key in sorted(project_overlay):
            if allowed_keys and key not in allowed_keys and key not in forbidden_keys:
                findings.append(f"project_overlay_unknown_key:{key}")
            if key in forbidden_keys:
                findings.append(f"project_overlay_forbidden_key:{key}")

        add_required = project_overlay.get("required_check_names_add", [])
        add_forbidden = project_overlay.get("forbidden_branches_add", [])
        remove_allowed = project_overlay.get("allowed_branch_patterns_remove", [])

        if not isinstance(add_required, list):
            findings.append("project_overlay_invalid_required_check_names_add")
            add_required = []
        if not isinstance(add_forbidden, list):
            findings.append("project_overlay_invalid_forbidden_branches_add")
            add_forbidden = []
        if not isinstance(remove_allowed, list):
            findings.append("project_overlay_invalid_allowed_branch_patterns_remove")
            remove_allowed = []

        effective["required_check_names"] = sorted(
            set(effective["required_check_names"]) | {str(item).strip() for item in add_required if str(item).strip()}
        )
        effective["forbidden_branches"] = sorted(
            set(effective["forbidden_branches"]) | {str(item).strip() for item in add_forbidden if str(item).strip() or item == ""}
        )
        remove_set = {str(item).strip() for item in remove_allowed if str(item).strip()}
        effective["allowed_branch_patterns"] = [
            pattern for pattern in effective["allowed_branch_patterns"] if pattern not in remove_set
        ]
    else:
        if (root_path / "platform.engine.yaml").exists():
            findings.append(f"project_rules_source_missing:{project_rules_source}")

    report = {
        "tool": "governance_loader",
        "runtime": {
            "mode": mode,
            "governance_source": source,
            "project_rules_source": project_rules_source,
        },
        "local_policy": local,
        "external_baseline": external,
        "project_overlay": project_overlay,
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
