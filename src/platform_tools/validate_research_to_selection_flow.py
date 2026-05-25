from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from platform_tools.materialize_research_candidate_tree import materialize_research_candidate_tree
from platform_tools.materialize_research_evaluations import materialize_research_evaluations
from platform_tools.materialize_research_hypotheses import materialize_research_hypotheses
from platform_tools.materialize_research_recommendation import materialize_research_recommendation
from platform_tools.materialize_selected_solution_scope import materialize_selected_solution_scope
from platform_tools.public_orchestration_api import envelope
from platform_tools.question_to_research_problem_transform import materialize_research_problem
from platform_tools.research_questions import write_json


COMMAND = "validate-research-to-selection-flow"
DEFAULT_OUTPUT_ROOT = Path("artifacts/validation/research-to-selection-runs")

EXPECTED_STEP_OUTPUTS = {
    "materialize_research_problem": ["research_problem_path", "transform_packet_path"],
    "materialize_research_hypotheses": ["hypothesis_packet_paths"],
    "materialize_research_candidate_tree": ["candidate_search_tree_path", "candidate_packet_paths"],
    "materialize_research_evaluations": [
        "evaluation_packet_paths",
        "evaluation_summary_packet_path",
    ],
    "materialize_research_recommendation": ["recommendation_packet_path"],
    "materialize_selected_solution_scope": ["selected_solution_scope_path"],
}

RESEARCH_BASIS = [
    {
        "source_id": "src-critic-2023",
        "url": "https://arxiv.org/abs/2305.11738",
        "use": "validates through tool-grounded critique and local artifacts",
    },
    {
        "source_id": "src-swe-bench-2023",
        "url": "https://arxiv.org/abs/2310.06770",
        "use": "keeps software validation task-grounded rather than plausibility-only",
    },
    {
        "source_id": "src-prov-overview",
        "url": "https://www.w3.org/TR/prov-overview/",
        "use": "preserves provenance through packet refs and handoff artifacts",
    },
    {
        "source_id": "src-self-refine-2023",
        "url": "https://arxiv.org/abs/2303.17651",
        "use": "supports bounded iterative feedback when explicit feedback is recorded",
    },
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("rts-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _step_record(step: str, code: int, report: dict[str, Any]) -> dict[str, Any]:
    return {
        "step": step,
        "status": str(report.get("status", "")).strip(),
        "ok": code == 0 and report.get("ok") is True,
        "report": report,
    }


def _step_blockers(step_reports: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for step_report in step_reports:
        if step_report.get("ok") is True:
            continue
        step = str(step_report.get("step", "")).strip()
        report = step_report.get("report", {})
        if not isinstance(report, dict):
            blockers.append(f"{step}:invalid_step_report")
            continue
        for blocker in _string_list(report.get("blockers", [])):
            blockers.append(f"{step}:{blocker}")
    return blockers


def _validate_step_outputs(step_reports: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for step_report in step_reports:
        step = str(step_report.get("step", "")).strip()
        report = step_report.get("report", {})
        if not isinstance(report, dict):
            blockers.append(f"{step}:report_not_object")
            continue
        for field in EXPECTED_STEP_OUTPUTS.get(step, []):
            value = report.get(field)
            if isinstance(value, list):
                if not value:
                    blockers.append(f"{step}:missing_{field}")
            elif not str(value or "").strip():
                blockers.append(f"{step}:missing_{field}")
    return blockers


def _packet_type(path: Path) -> str:
    return str(_load_json(path).get("packet_type", "")).strip()


def _validate_packet_types(repo_root: Path, refs: dict[str, Any]) -> list[str]:
    expected = {
        "research_problem_path": "research_problem_packet",
        "recommendation_packet_path": "research_recommendation_packet",
        "selected_solution_scope_path": "selected_solution_scope",
        "candidate_search_tree_path": "candidate_search_tree_packet",
        "evaluation_summary_packet_path": "candidate_evaluation_summary_packet",
    }
    blockers: list[str] = []
    for field, packet_type in expected.items():
        value = str(refs.get(field, "")).strip()
        if not value:
            blockers.append(f"missing_ref:{field}")
            continue
        observed = _packet_type(repo_root / value)
        if observed != packet_type:
            blockers.append(f"packet_type_mismatch:{field}:{observed}")
    for field, packet_type in (
        ("hypothesis_packet_paths", "research_hypothesis_packet"),
        ("candidate_packet_paths", "research_candidate_packet"),
        ("evaluation_packet_paths", "research_evaluation_packet"),
    ):
        paths = _string_list(refs.get(field, []))
        if not paths:
            blockers.append(f"missing_ref:{field}")
            continue
        for index, path in enumerate(paths, start=1):
            observed = _packet_type(repo_root / path)
            if observed != packet_type:
                blockers.append(f"packet_type_mismatch:{field}:{index}:{observed}")
    return blockers


def _validate_handoff_integrity(repo_root: Path, refs: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    recommendation = _load_json(repo_root / str(refs["recommendation_packet_path"]))
    selected_scope = _load_json(repo_root / str(refs["selected_solution_scope_path"]))
    evaluations = [_load_json(repo_root / path) for path in _string_list(refs["evaluation_packet_paths"])]

    ranked_candidates = recommendation.get("ranked_candidates", [])
    if not isinstance(ranked_candidates, list) or not ranked_candidates:
        blockers.append("recommendation_missing_ranked_candidates")
    selected_candidate_id = str(selected_scope.get("selected_candidate_id", "")).strip()
    recommended_candidate_id = str(recommendation.get("recommended_candidate_id", "")).strip()
    if selected_candidate_id != recommended_candidate_id:
        blockers.append("selected_candidate_does_not_match_recommendation")
    evaluation_candidate_ids = {
        str(evaluation.get("candidate_id", "")).strip()
        for evaluation in evaluations
        if str(evaluation.get("candidate_id", "")).strip()
    }
    if selected_candidate_id not in evaluation_candidate_ids:
        blockers.append("selected_candidate_missing_evaluation_packet")
    selection_policy = selected_scope.get("selection_policy", {})
    if not isinstance(selection_policy, dict):
        blockers.append("selected_scope_missing_selection_policy")
    elif str(selection_policy.get("policy_id", "")).strip() != "evaluation_backed_recommendation_gate_v1":
        blockers.append("selected_scope_selection_policy_invalid")
    if not _string_list(selected_scope.get("evidence_refs", [])):
        blockers.append("selected_scope_missing_evidence_refs")
    return blockers


def validate_research_to_selection_flow(
    *,
    root: str = ".",
    research_question_path: str,
    evidence_packet_path: str | None = None,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
    max_candidates: int = 8,
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    step_root = f"{output_root}/{run_id}/steps"
    step_reports: list[dict[str, Any]] = []

    problem_code, problem_report = materialize_research_problem(
        root=root,
        research_question_path=research_question_path,
        evidence_packet_path=evidence_packet_path,
        output_root=step_root,
    )
    step_reports.append(_step_record("materialize_research_problem", problem_code, problem_report))
    if problem_code != 0:
        return _blocked(repo_root, run_root, run_id, research_question_path, evidence_packet_path, step_reports)

    research_problem_path = str(problem_report.get("research_problem_path", "")).strip()
    hypotheses_code, hypotheses_report = materialize_research_hypotheses(
        root=root,
        research_problem_path=research_problem_path,
        output_root=step_root,
    )
    step_reports.append(
        _step_record("materialize_research_hypotheses", hypotheses_code, hypotheses_report)
    )
    if hypotheses_code != 0:
        return _blocked(repo_root, run_root, run_id, research_question_path, evidence_packet_path, step_reports)

    hypothesis_paths = _string_list(hypotheses_report.get("hypothesis_packet_paths", []))
    candidate_code, candidate_report = materialize_research_candidate_tree(
        root=root,
        research_problem_path=research_problem_path,
        hypothesis_paths=hypothesis_paths,
        output_root=step_root,
        max_candidates=max_candidates,
    )
    step_reports.append(
        _step_record("materialize_research_candidate_tree", candidate_code, candidate_report)
    )
    if candidate_code != 0:
        return _blocked(repo_root, run_root, run_id, research_question_path, evidence_packet_path, step_reports)

    candidate_tree_path = str(candidate_report.get("candidate_search_tree_path", "")).strip()
    candidate_paths = _string_list(candidate_report.get("candidate_packet_paths", []))
    evaluation_code, evaluation_report = materialize_research_evaluations(
        root=root,
        candidate_search_tree_path=candidate_tree_path,
        candidate_paths=candidate_paths,
        output_root=step_root,
    )
    step_reports.append(
        _step_record("materialize_research_evaluations", evaluation_code, evaluation_report)
    )
    if evaluation_code != 0:
        return _blocked(repo_root, run_root, run_id, research_question_path, evidence_packet_path, step_reports)

    evaluation_paths = _string_list(evaluation_report.get("evaluation_packet_paths", []))
    evaluation_summary_path = str(evaluation_report.get("evaluation_summary_packet_path", "")).strip()
    recommendation_code, recommendation_report = materialize_research_recommendation(
        root=root,
        candidate_search_tree_path=candidate_tree_path,
        candidate_paths=candidate_paths,
        evaluation_paths=evaluation_paths,
        evaluation_summary_path=evaluation_summary_path,
        output_root=step_root,
    )
    step_reports.append(
        _step_record("materialize_research_recommendation", recommendation_code, recommendation_report)
    )
    if recommendation_code != 0:
        return _blocked(repo_root, run_root, run_id, research_question_path, evidence_packet_path, step_reports)

    recommendation_path = str(recommendation_report.get("recommendation_packet_path", "")).strip()
    selection_code, selection_report = materialize_selected_solution_scope(
        root=root,
        recommendation_path=recommendation_path,
        output_root=step_root,
        in_scope=["validated research-to-selection flow"],
        out_of_scope=["planner DAG generation", "code generation"],
        acceptance_checks=["research-to-selection validation report is ok"],
    )
    step_reports.append(
        _step_record("materialize_selected_solution_scope", selection_code, selection_report)
    )
    if selection_code != 0:
        return _blocked(repo_root, run_root, run_id, research_question_path, evidence_packet_path, step_reports)

    refs = {
        "research_problem_path": research_problem_path,
        "transform_packet_path": problem_report.get("transform_packet_path", ""),
        "hypothesis_packet_paths": hypothesis_paths,
        "candidate_search_tree_path": candidate_tree_path,
        "candidate_packet_paths": candidate_paths,
        "evaluation_packet_paths": evaluation_paths,
        "evaluation_summary_packet_path": evaluation_summary_path,
        "recommendation_packet_path": recommendation_path,
        "selected_solution_scope_path": selection_report.get("selected_solution_scope_path", ""),
    }
    validation_blockers = []
    validation_blockers.extend(_validate_step_outputs(step_reports))
    validation_blockers.extend(_validate_packet_types(repo_root, refs))
    validation_blockers.extend(_validate_handoff_integrity(repo_root, refs))

    if validation_blockers:
        return _blocked(
            repo_root,
            run_root,
            run_id,
            research_question_path,
            evidence_packet_path,
            step_reports,
            extra_blockers=validation_blockers,
            refs=refs,
        )

    validation_report = {
        "packet_type": "research_to_selection_validation_report",
        "packet_version": "v1",
        "packet_id": f"{run_id}:research-to-selection-validation",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "run_id": run_id,
        "status": "ok",
        "validated_scope": "research_to_selection_only",
        "explicitly_not_validated": [
            "live external source retrieval",
            "execution-backed candidate evaluation",
            "planner DAG generation",
            "code generation",
            "governance execution intake",
        ],
        "research_basis": RESEARCH_BASIS,
        "artifact_refs": refs,
        "step_reports": step_reports,
        "validation_checks": [
            "all steps ok",
            "expected output refs present",
            "packet types match contracts",
            "selected candidate matches recommendation",
            "selected candidate has evaluation packet",
            "selected scope records selection policy",
        ],
        "blockers": [],
    }
    validation_report_path = write_json(
        run_root / "research-to-selection-validation.packet.json",
        validation_report,
    )
    report = envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "run_id": run_id,
            "validation_report_path": validation_report_path.as_posix(),
            "validated_scope": "research_to_selection_only",
            "explicitly_not_validated": validation_report["explicitly_not_validated"],
            **refs,
            "step_reports": step_reports,
            "blockers": [],
        },
    )
    write_json(run_root / "research-to-selection-validation.report.json", report)
    return 0, report


def _blocked(
    repo_root: Path,
    run_root: Path,
    run_id: str,
    research_question_path: str,
    evidence_packet_path: str | None,
    step_reports: list[dict[str, Any]],
    *,
    extra_blockers: list[str] | None = None,
    refs: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    blockers = _step_blockers(step_reports) + (extra_blockers or [])
    report = envelope(
        command=COMMAND,
        status="blocked",
        ok=False,
        payload={
            "run_id": run_id,
            "research_question_path": str((repo_root / research_question_path).resolve()),
            "evidence_packet_path": str((repo_root / evidence_packet_path).resolve())
            if evidence_packet_path
            else "",
            "validated_scope": "research_to_selection_only",
            "explicitly_not_validated": [
                "live external source retrieval",
                "execution-backed candidate evaluation",
                "planner DAG generation",
                "code generation",
                "governance execution intake",
            ],
            "artifact_refs": refs or {},
            "step_reports": step_reports,
            "blockers": sorted(set(blockers)),
        },
    )
    write_json(run_root / "research-to-selection-validation.report.json", report)
    return 1, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--research-question-path", required=True)
    parser.add_argument("--evidence-packet-path", default=None)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    parser.add_argument("--max-candidates", type=int, default=8)
    args = parser.parse_args()
    try:
        code, report = validate_research_to_selection_flow(
            root=args.root,
            research_question_path=args.research_question_path,
            evidence_packet_path=args.evidence_packet_path,
            output_root=args.output_root,
            max_candidates=args.max_candidates,
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
