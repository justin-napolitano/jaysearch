from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def check_adoption() -> tuple[int, dict[str, Any]]:
    spec_path = Path("spec/adoption.yaml")
    spec = _load_yaml(spec_path)
    findings: list[str] = []

    pilot_cfg = spec.get("pilot", {})
    registry_path = Path(str(pilot_cfg.get("registry_path", ".agent/adoption/pilot-status.yaml")))
    required_fields = pilot_cfg.get("required_pilot_fields", [])
    allowed_risk_tiers = set(pilot_cfg.get("allowed_risk_tiers", ["low", "medium", "high"]))

    registry = _load_yaml(registry_path)
    pilots = registry.get("pilots", [])
    if not isinstance(pilots, list):
        findings.append("invalid_pilot_registry")
        pilots = []

    seen_repos: set[str] = set()
    passing = 0
    for idx, pilot in enumerate(pilots):
        tag = f"pilot[{idx}]"
        if not isinstance(pilot, dict):
            findings.append(f"{tag}:invalid_entry")
            continue
        for field in required_fields:
            if field not in pilot or pilot.get(field) in ("", None, []):
                findings.append(f"{tag}:missing_field:{field}")

        repo = str(pilot.get("repo", "")).strip()
        if repo in seen_repos:
            findings.append(f"{tag}:duplicate_repo:{repo}")
        if repo:
            seen_repos.add(repo)

        risk_tier = str(pilot.get("risk_tier", "")).strip()
        if risk_tier and risk_tier not in allowed_risk_tiers:
            findings.append(f"{tag}:invalid_risk_tier:{risk_tier}")

        evidence = pilot.get("evidence", [])
        if not isinstance(evidence, list) or not evidence:
            findings.append(f"{tag}:missing_evidence")
        else:
            missing_evidence = [p for p in evidence if not Path(str(p)).exists()]
            findings.extend(f"{tag}:missing_evidence_path:{p}" for p in sorted(missing_evidence))

        checks_passed = int(pilot.get("checks_passed", 0))
        checks_total = int(pilot.get("checks_total", 0))
        if checks_total <= 0 or checks_passed < 0 or checks_passed > checks_total:
            findings.append(f"{tag}:invalid_check_counts")
        elif checks_passed == checks_total:
            passing += 1

    gate = spec.get("promotion_gate", {})
    min_pilot_count = int(gate.get("min_pilot_count", 1))
    min_pass_rate = float(gate.get("min_pass_rate", 1.0))
    required_decision = gate.get("required_decision_fields", [])

    if len(pilots) < min_pilot_count:
        findings.append("insufficient_pilot_count")

    pass_rate = (passing / len(pilots)) if pilots else 0.0
    if pass_rate < min_pass_rate:
        findings.append("promotion_gate_not_met")

    decision = registry.get("decision", {})
    if not isinstance(decision, dict):
        findings.append("missing_decision")
        decision = {}
    for field in required_decision:
        if field not in decision or decision.get(field) in ("", None):
            findings.append(f"missing_decision_field:{field}")

    findings = sorted(set(findings))
    report = {
        "tool": "adoption_check",
        "spec_path": spec_path.as_posix(),
        "registry_path": registry_path.as_posix(),
        "pilot_count": len(pilots),
        "pass_rate": round(pass_rate, 3),
        "finding_count": len(findings),
        "findings": findings,
    }
    return (1 if findings else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    code, report = check_adoption()
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
