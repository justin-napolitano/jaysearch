from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "materialize-selected-solution-scope"
DEFAULT_OUTPUT_ROOT = Path("artifacts/selection/runs")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("sss-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _candidate_index(recommendation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    ranked_candidates = recommendation.get("ranked_candidates", [])
    if not isinstance(ranked_candidates, list):
        return result
    for item in ranked_candidates:
        if not isinstance(item, dict):
            continue
        candidate_id = str(item.get("candidate_id", "")).strip() or str(item.get("option_id", "")).strip()
        if candidate_id:
            result[candidate_id] = item
    return result


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _nonempty_string(value: Any) -> str:
    return str(value).strip()


def materialize_selected_solution_scope(
    *,
    root: str = ".",
    recommendation_path: str,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
    selected_candidate_id: str | None = None,
    selection_reason: str | None = None,
    in_scope: list[str] | None = None,
    out_of_scope: list[str] | None = None,
    acceptance_checks: list[str] | None = None,
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    recommendation = _load_json(repo_root / recommendation_path)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    packet_type = str(recommendation.get("packet_type", "")).strip()
    problem_id = str(recommendation.get("problem_id", "")).strip()
    recommended_candidate = (
        (selected_candidate_id or "").strip()
        or str(recommendation.get("recommended_candidate_id", "")).strip()
    )
    if packet_type != "research_recommendation_packet":
        blockers.append("recommendation_packet_type_invalid")
    if not problem_id:
        blockers.append("recommendation_missing_problem_id")
    if not recommended_candidate:
        blockers.append("recommended_candidate_missing")

    evaluation_summary_ref = _nonempty_string(recommendation.get("evaluation_summary_ref", ""))
    evaluation_refs = _string_list(recommendation.get("evaluation_refs", []))
    if not evaluation_summary_ref:
        blockers.append("recommendation_missing_evaluation_summary_ref")
    if not evaluation_refs:
        blockers.append("recommendation_missing_evaluation_refs")
    ranked_candidates = recommendation.get("ranked_candidates", [])
    if not isinstance(ranked_candidates, list) or not ranked_candidates:
        blockers.append("recommendation_missing_ranked_candidates")

    candidates = _candidate_index(recommendation)
    selected_candidate = candidates.get(recommended_candidate, {})
    if recommended_candidate and not selected_candidate:
        blockers.append("recommended_candidate_not_found")
    if selected_candidate:
        if _nonempty_string(selected_candidate.get("promotion_status", "")) != "promoted":
            blockers.append("selected_candidate_not_promoted")
        if not _nonempty_string(selected_candidate.get("evaluation_ref", "")):
            blockers.append("selected_candidate_missing_evaluation_ref")
        if not _string_list(selected_candidate.get("evidence_refs", [])):
            blockers.append("selected_candidate_missing_evidence_refs")

    if blockers:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "recommendation_path": str((repo_root / recommendation_path).resolve()),
                "blockers": sorted(set(blockers)),
            },
        )
        write_json(run_root / "selected-solution-scope.report.json", report)
        return 1, report

    artifact_refs = _string_list(recommendation.get("artifact_refs", []))
    evidence_refs = _string_list(recommendation.get("evidence_refs", []))

    default_summary = (
        str(selected_candidate.get("summary", "")).strip()
        or str(selected_candidate.get("proposal_summary", "")).strip()
        or str(recommendation.get("recommendation_reason", "")).strip()
    )
    default_assumptions = [
        str(item).strip()
        for item in selected_candidate.get("assumptions", [])
        if str(item).strip()
    ] if isinstance(selected_candidate.get("assumptions"), list) else []
    default_risks = [
        str(item).strip()
        for item in selected_candidate.get("weaknesses", [])
        if str(item).strip()
    ] if isinstance(selected_candidate.get("weaknesses"), list) else []
    if not default_risks:
        default_risks = [
            str(item).strip()
            for item in selected_candidate.get("risks", [])
            if str(item).strip()
        ] if isinstance(selected_candidate.get("risks"), list) else []
    default_checks = [
        str(item).strip()
        for item in selected_candidate.get("strengths", [])
        if str(item).strip()
    ] if isinstance(selected_candidate.get("strengths"), list) else []
    implementation_intent = selected_candidate.get("implementation_intent", {})
    if not isinstance(implementation_intent, dict):
        implementation_intent = {}
    intent_expected_changes = (
        _string_list(selected_candidate.get("expected_changes", []))
        or _string_list(implementation_intent.get("contract_changes", []))
        + _string_list(implementation_intent.get("runtime_changes", []))
        + _string_list(implementation_intent.get("validation_changes", []))
        + _string_list(implementation_intent.get("docs_changes", []))
    )
    intent_validation_changes = (
        _string_list(selected_candidate.get("validation_changes", []))
        or _string_list(implementation_intent.get("validation_changes", []))
    )

    stable_packet_id = f"selected-scope:{problem_id}:{recommended_candidate}"
    normalized_in_scope = [
        str(item).strip()
        for item in (in_scope or intent_expected_changes)
        if str(item).strip()
    ]
    normalized_out_of_scope = [
        str(item).strip()
        for item in (out_of_scope or _string_list(selected_candidate.get("non_goals", [])))
        if str(item).strip()
    ]
    normalized_checks = [
        str(item).strip()
        for item in (acceptance_checks or intent_validation_changes or default_checks)
        if str(item).strip()
    ]
    scope_packet = {
        "packet_type": "selected_solution_scope",
        "packet_version": "v1",
        "packet_id": stable_packet_id,
        "created_at": _utc_now(),
        "producer": COMMAND,
        "selection_id": f"selection:{problem_id}:{recommended_candidate}",
        "problem_id": problem_id,
        "selected_candidate_id": recommended_candidate,
        "selection_reason": (selection_reason or str(recommendation.get("recommendation_reason", "")).strip()).strip(),
        "selection_policy": {
            "policy_id": "evaluation_backed_recommendation_gate_v1",
            "source_recommendation_ref": str((repo_root / recommendation_path).resolve()),
            "required_inputs": [
                "evaluation_summary_ref",
                "evaluation_refs",
                "ranked_candidates",
                "promoted selected candidate",
                "selected candidate evaluation_ref",
            ],
        },
        "selected_solution_summary": default_summary,
        "implementation_intent": implementation_intent,
        "expected_changes": intent_expected_changes,
        "contract_changes": _string_list(selected_candidate.get("contract_changes", [])),
        "runtime_changes": _string_list(selected_candidate.get("runtime_changes", [])),
        "validation_changes": _string_list(selected_candidate.get("validation_changes", [])),
        "docs_changes": _string_list(selected_candidate.get("docs_changes", [])),
        "handoff_requirements": _string_list(selected_candidate.get("handoff_requirements", [])),
        "in_scope": normalized_in_scope,
        "out_of_scope": normalized_out_of_scope,
        "scope_in": normalized_in_scope,
        "scope_out": normalized_out_of_scope,
        "assumptions": default_assumptions,
        "risks": default_risks,
        "acceptance_checks": normalized_checks,
        "acceptance_targets": normalized_checks,
        "artifact_refs": artifact_refs,
        "evidence_refs": evidence_refs,
        "open_questions": recommendation.get("open_questions", []) if isinstance(recommendation.get("open_questions"), list) else [],
    }
    scope_path = write_json(run_root / "selected-solution-scope.packet.json", scope_packet)
    report = envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "run_id": run_id,
            "recommendation_path": str((repo_root / recommendation_path).resolve()),
            "selected_solution_scope_path": scope_path.as_posix(),
            "selected_candidate_id": recommended_candidate,
            "blockers": [],
        },
    )
    write_json(run_root / "selected-solution-scope.report.json", report)
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--recommendation-path", required=True)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    parser.add_argument("--selected-candidate-id", default=None)
    parser.add_argument("--selection-reason", default=None)
    parser.add_argument("--in-scope", action="append", default=[])
    parser.add_argument("--out-of-scope", action="append", default=[])
    parser.add_argument("--acceptance-check", action="append", default=[])
    args = parser.parse_args()
    try:
        code, report = materialize_selected_solution_scope(
            root=args.root,
            recommendation_path=args.recommendation_path,
            output_root=args.output_root,
            selected_candidate_id=args.selected_candidate_id,
            selection_reason=args.selection_reason,
            in_scope=args.in_scope,
            out_of_scope=args.out_of_scope,
            acceptance_checks=args.acceptance_check,
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
