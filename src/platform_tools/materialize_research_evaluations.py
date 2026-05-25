from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "materialize-research-evaluations"
DEFAULT_OUTPUT_ROOT = Path("artifacts/research-evaluations/runs")
PROMOTION_THRESHOLD = 0.65


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("rev-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _metric(value: float, *, basis: str) -> dict[str, Any]:
    return {
        "value": round(max(0.0, min(1.0, value)), 3),
        "basis": basis,
    }


def _risk_penalty(candidate: dict[str, Any]) -> float:
    risk_notes = _string_list(candidate.get("risk_notes", []))
    priors = candidate.get("feasibility_priors", {})
    if not isinstance(priors, dict):
        priors = {}
    risk = 0.0
    risk += min(len(risk_notes) * 0.1, 0.3)
    if str(priors.get("implementation_risk", "")).strip() == "high":
        risk += 0.3
    elif str(priors.get("implementation_risk", "")).strip() == "medium":
        risk += 0.15
    if str(priors.get("dependency_risk", "")).strip() == "high":
        risk += 0.2
    elif str(priors.get("dependency_risk", "")).strip() == "medium":
        risk += 0.1
    return min(risk, 1.0)


def _feasibility_score(candidate: dict[str, Any]) -> float:
    priors = candidate.get("feasibility_priors", {})
    if not isinstance(priors, dict):
        return 0.0
    complexity = str(priors.get("expected_complexity", "")).strip()
    implementation_risk = str(priors.get("implementation_risk", "")).strip()
    score = 0.5
    if complexity == "low":
        score += 0.25
    elif complexity == "medium":
        score += 0.1
    elif complexity == "high":
        score -= 0.1
    if implementation_risk == "low":
        score += 0.2
    elif implementation_risk == "medium":
        score += 0.05
    elif implementation_risk == "high":
        score -= 0.15
    return max(0.0, min(score, 1.0))


def _evaluate_candidate(candidate: dict[str, Any]) -> tuple[dict[str, Any], list[str], list[str], float]:
    failures: list[str] = []
    warnings: list[str] = []
    required_fields = [
        "candidate_id",
        "problem_id",
        "source_hypothesis_id",
        "candidate_family",
        "approach_summary",
        "proposed_changes",
        "source_type",
        "evidence_refs",
        "feasibility_priors",
    ]
    present_required = 0
    for field in required_fields:
        value = candidate.get(field)
        exists = bool(value) if not isinstance(value, list) else bool(_string_list(value))
        if exists:
            present_required += 1
        else:
            failures.append(f"candidate_missing_{field}")

    evidence_refs = _string_list(candidate.get("evidence_refs", []))
    artifact_refs = _string_list(candidate.get("artifact_refs", []))
    traceability = 1.0 if str(candidate.get("source_hypothesis_id", "")).strip() else 0.0
    evidence_support = 1.0 if evidence_refs else 0.0
    artifact_readiness = 1.0 if artifact_refs else 0.5 if _string_list(candidate.get("proposed_changes", [])) else 0.0
    feasibility = _feasibility_score(candidate)
    risk_penalty = _risk_penalty(candidate)
    contract_completeness = present_required / len(required_fields)

    if not artifact_refs:
        warnings.append("candidate_has_no_materialized_artifacts")
    if not evidence_refs:
        warnings.append("candidate_has_no_evidence_refs")
    if risk_penalty >= 0.5:
        warnings.append("candidate_high_risk_priors")

    metrics = {
        "contract_completeness": _metric(contract_completeness, basis="required field presence"),
        "traceability": _metric(traceability, basis="source_hypothesis_id presence"),
        "evidence_support": _metric(evidence_support, basis="evidence_refs presence"),
        "feasibility": _metric(feasibility, basis="feasibility_priors"),
        "artifact_readiness": _metric(artifact_readiness, basis="artifact refs or proposed changes"),
        "risk_penalty": _metric(risk_penalty, basis="risk notes and feasibility priors"),
    }
    total_score = (
        0.25 * contract_completeness
        + 0.25 * traceability
        + 0.2 * evidence_support
        + 0.15 * feasibility
        + 0.15 * artifact_readiness
        - 0.2 * risk_penalty
    )
    return metrics, failures, warnings, round(max(0.0, min(total_score, 1.0)), 3)


def materialize_research_evaluations(
    *,
    root: str = ".",
    candidate_search_tree_path: str,
    candidate_paths: list[str],
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    search_tree = _load_json(repo_root / candidate_search_tree_path)
    candidates = [_load_json(repo_root / path) for path in candidate_paths]
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    if str(search_tree.get("packet_type", "")).strip() != "candidate_search_tree_packet":
        blockers.append("candidate_search_tree_packet_type_invalid")
    problem_id = str(search_tree.get("problem_id", "")).strip()
    if not problem_id:
        blockers.append("candidate_search_tree_missing_problem_id")
    if not candidates:
        blockers.append("research_candidate_packets_missing")

    for index, candidate in enumerate(candidates, start=1):
        if str(candidate.get("packet_type", "")).strip() != "research_candidate_packet":
            blockers.append(f"research_candidate_packet_type_invalid:{index}")
        if str(candidate.get("problem_id", "")).strip() != problem_id:
            blockers.append(f"research_candidate_problem_mismatch:{index}")

    if blockers:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "candidate_search_tree_path": str((repo_root / candidate_search_tree_path).resolve()),
                "candidate_paths": [str((repo_root / path).resolve()) for path in candidate_paths],
                "blockers": sorted(set(blockers)),
            },
        )
        write_json(run_root / "research-evaluation.report.json", report)
        return 1, report

    evaluation_packet_paths: list[str] = []
    promoted_candidate_ids: list[str] = []
    blocked_candidate_ids: list[str] = []
    for index, candidate in enumerate(candidates, start=1):
        candidate_id = str(candidate.get("candidate_id", "")).strip()
        metrics, failures, warnings, total_score = _evaluate_candidate(candidate)
        promotion_status = "promoted" if total_score >= PROMOTION_THRESHOLD and not failures else "blocked"
        if promotion_status == "promoted":
            promoted_candidate_ids.append(candidate_id)
        else:
            blocked_candidate_ids.append(candidate_id)
        evaluation_packet = {
            "packet_type": "research_evaluation_packet",
            "packet_version": "v1",
            "packet_id": f"{candidate_id}:evaluation:001",
            "created_at": _utc_now(),
            "producer": COMMAND,
            "evaluation_id": f"{candidate_id}:evaluation:001",
            "problem_id": problem_id,
            "candidate_id": candidate_id,
            "source_hypothesis_id": str(candidate.get("source_hypothesis_id", "")).strip(),
            "evaluation_method": "bounded_static_candidate_evaluation_v1",
            "metrics": {
                **metrics,
                "total_score": _metric(total_score, basis="weighted static evaluation"),
            },
            "failures": failures,
            "warnings": warnings,
            "artifact_refs": _string_list(candidate.get("artifact_refs", [])),
            "evidence_refs": _string_list(candidate.get("evidence_refs", [])),
            "promotion_status": promotion_status,
        }
        path = write_json(run_root / f"research-evaluation-{index:02d}.packet.json", evaluation_packet)
        evaluation_packet_paths.append(path.as_posix())

    summary_packet = {
        "packet_type": "candidate_evaluation_summary_packet",
        "packet_version": "v1",
        "packet_id": f"{problem_id}:candidate-evaluation-summary",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "problem_id": problem_id,
        "candidate_search_tree_ref": str((repo_root / candidate_search_tree_path).resolve()),
        "evaluation_packet_refs": evaluation_packet_paths,
        "promoted_candidate_ids": promoted_candidate_ids,
        "blocked_candidate_ids": blocked_candidate_ids,
        "evaluation_policy": {
            "method": "bounded_static_candidate_evaluation_v1",
            "promotion_threshold": PROMOTION_THRESHOLD,
            "dimensions": [
                "contract_completeness",
                "traceability",
                "evidence_support",
                "feasibility",
                "artifact_readiness",
                "risk_penalty",
            ],
        },
    }
    summary_path = write_json(run_root / "candidate-evaluation-summary.packet.json", summary_packet)

    report = envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "run_id": run_id,
            "candidate_search_tree_path": str((repo_root / candidate_search_tree_path).resolve()),
            "candidate_paths": [str((repo_root / path).resolve()) for path in candidate_paths],
            "evaluation_packet_paths": evaluation_packet_paths,
            "evaluation_summary_packet_path": summary_path.as_posix(),
            "promoted_candidate_ids": promoted_candidate_ids,
            "blocked_candidate_ids": blocked_candidate_ids,
            "blockers": [],
        },
    )
    write_json(run_root / "research-evaluation.report.json", report)
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--candidate-search-tree-path", required=True)
    parser.add_argument("--candidate", action="append", dest="candidates", required=True)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    args = parser.parse_args()
    try:
        code, report = materialize_research_evaluations(
            root=args.root,
            candidate_search_tree_path=args.candidate_search_tree_path,
            candidate_paths=args.candidates,
            output_root=args.output_root,
        )
    except (FileNotFoundError, PermissionError, ValueError, json.JSONDecodeError) as exc:
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
