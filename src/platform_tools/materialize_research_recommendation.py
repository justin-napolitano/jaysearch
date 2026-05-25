from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "materialize-research-recommendation"
DEFAULT_OUTPUT_ROOT = Path("artifacts/research-recommendations/runs")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("rrc-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _score_value(evaluation: dict[str, Any]) -> float:
    metrics = evaluation.get("metrics", {})
    if not isinstance(metrics, dict):
        return 0.0
    total_score = metrics.get("total_score", {})
    if isinstance(total_score, dict):
        value = total_score.get("value", 0.0)
    else:
        value = total_score
    try:
        return round(max(0.0, min(float(value), 1.0)), 3)
    except (TypeError, ValueError):
        return 0.0


def _score_breakdown(evaluation: dict[str, Any]) -> dict[str, Any]:
    metrics = evaluation.get("metrics", {})
    if not isinstance(metrics, dict):
        return {}
    return {
        str(name): value
        for name, value in metrics.items()
        if str(name) != "total_score"
    }


def _evaluation_ref_for(candidate_id: str, evaluation_paths: list[str], evaluations: list[dict[str, Any]]) -> str:
    for path, evaluation in zip(evaluation_paths, evaluations, strict=True):
        if str(evaluation.get("candidate_id", "")).strip() == candidate_id:
            return path
    return ""


def _candidate_by_id(candidates: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id", "")).strip()
        if candidate_id:
            by_id[candidate_id] = candidate
    return by_id


def _candidate_intent_fields(candidate: dict[str, Any]) -> dict[str, Any]:
    implementation_intent = candidate.get("implementation_intent", {})
    if not isinstance(implementation_intent, dict):
        implementation_intent = {}
    return {
        "approach_summary": str(candidate.get("approach_summary", "")).strip(),
        "implementation_intent": implementation_intent,
        "contract_changes": _string_list(candidate.get("contract_changes", [])),
        "runtime_changes": _string_list(candidate.get("runtime_changes", [])),
        "validation_changes": _string_list(candidate.get("validation_changes", [])),
        "docs_changes": _string_list(candidate.get("docs_changes", [])),
        "expected_changes": _string_list(candidate.get("expected_changes", [])),
        "non_goals": _string_list(candidate.get("non_goals", [])),
        "assumptions": _string_list(candidate.get("assumptions", [])),
        "handoff_requirements": _string_list(candidate.get("handoff_requirements", [])),
        "planner_entry_notes": _string_list(candidate.get("planner_entry_notes", [])),
    }


def _rank_key(item: dict[str, Any]) -> tuple[int, float, str]:
    promoted_first = 0 if item["promotion_status"] == "promoted" else 1
    return (promoted_first, -float(item["total_score"]), str(item["candidate_id"]))


def materialize_research_recommendation(
    *,
    root: str = ".",
    candidate_search_tree_path: str,
    candidate_paths: list[str],
    evaluation_paths: list[str],
    evaluation_summary_path: str,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    search_tree = _load_json(repo_root / candidate_search_tree_path)
    candidates = [_load_json(repo_root / path) for path in candidate_paths]
    evaluations = [_load_json(repo_root / path) for path in evaluation_paths]
    evaluation_summary = _load_json(repo_root / evaluation_summary_path)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    if str(search_tree.get("packet_type", "")).strip() != "candidate_search_tree_packet":
        blockers.append("candidate_search_tree_packet_type_invalid")
    if str(evaluation_summary.get("packet_type", "")).strip() != "candidate_evaluation_summary_packet":
        blockers.append("candidate_evaluation_summary_packet_type_invalid")

    problem_id = str(search_tree.get("problem_id", "")).strip()
    if not problem_id:
        blockers.append("candidate_search_tree_missing_problem_id")
    if str(evaluation_summary.get("problem_id", "")).strip() != problem_id:
        blockers.append("candidate_evaluation_summary_problem_mismatch")
    if not candidates:
        blockers.append("research_candidate_packets_missing")
    if not evaluations:
        blockers.append("research_evaluation_packets_missing")

    candidate_ids: set[str] = set()
    for index, candidate in enumerate(candidates, start=1):
        if str(candidate.get("packet_type", "")).strip() != "research_candidate_packet":
            blockers.append(f"research_candidate_packet_type_invalid:{index}")
        candidate_id = str(candidate.get("candidate_id", "")).strip()
        if not candidate_id:
            blockers.append(f"research_candidate_missing_id:{index}")
            continue
        if str(candidate.get("problem_id", "")).strip() != problem_id:
            blockers.append(f"research_candidate_problem_mismatch:{index}")
        candidate_ids.add(candidate_id)

    evaluation_by_candidate_id: dict[str, dict[str, Any]] = {}
    for index, evaluation in enumerate(evaluations, start=1):
        if str(evaluation.get("packet_type", "")).strip() != "research_evaluation_packet":
            blockers.append(f"research_evaluation_packet_type_invalid:{index}")
        candidate_id = str(evaluation.get("candidate_id", "")).strip()
        if not candidate_id:
            blockers.append(f"research_evaluation_missing_candidate_id:{index}")
            continue
        if str(evaluation.get("problem_id", "")).strip() != problem_id:
            blockers.append(f"research_evaluation_problem_mismatch:{index}")
        if candidate_id in evaluation_by_candidate_id:
            blockers.append(f"duplicate_research_evaluation_for_candidate:{candidate_id}")
        evaluation_by_candidate_id[candidate_id] = evaluation

    missing_evaluations = sorted(candidate_ids - set(evaluation_by_candidate_id))
    for candidate_id in missing_evaluations:
        blockers.append(f"candidate_missing_evaluation:{candidate_id}")

    summary_refs = set(_string_list(evaluation_summary.get("evaluation_packet_refs", [])))
    missing_summary_refs = sorted(set(evaluation_paths) - summary_refs)
    if missing_summary_refs:
        blockers.append("evaluation_summary_missing_evaluation_refs")

    if blockers:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "run_id": run_id,
                "candidate_search_tree_path": str((repo_root / candidate_search_tree_path).resolve()),
                "candidate_paths": [str((repo_root / path).resolve()) for path in candidate_paths],
                "evaluation_paths": [str((repo_root / path).resolve()) for path in evaluation_paths],
                "evaluation_summary_path": str((repo_root / evaluation_summary_path).resolve()),
                "blockers": sorted(set(blockers)),
            },
        )
        write_json(run_root / "research-recommendation.report.json", report)
        return 1, report

    candidates_by_id = _candidate_by_id(candidates)
    ranked_items: list[dict[str, Any]] = []
    for candidate_id, evaluation in evaluation_by_candidate_id.items():
        candidate = candidates_by_id[candidate_id]
        promotion_status = str(evaluation.get("promotion_status", "")).strip() or "blocked"
        intent_fields = _candidate_intent_fields(candidate)
        ranked_items.append(
            {
                "candidate_id": candidate_id,
                "problem_id": problem_id,
                "rank": 0,
                "total_score": _score_value(evaluation),
                "score_breakdown": _score_breakdown(evaluation),
                "strengths": [
                    warning
                    for warning in [
                        "evaluation_promoted_candidate"
                        if promotion_status == "promoted"
                        else "",
                        "candidate_has_evidence_refs"
                        if _string_list(evaluation.get("evidence_refs", []))
                        else "",
                    ]
                    if warning
                ],
                "weaknesses": _string_list(evaluation.get("failures", []))
                + _string_list(evaluation.get("warnings", [])),
                "promotion_status": promotion_status,
                "evaluation_ref": _evaluation_ref_for(candidate_id, evaluation_paths, evaluations),
                "evidence_refs": _string_list(evaluation.get("evidence_refs", [])),
                "source_hypothesis_id": str(candidate.get("source_hypothesis_id", "")).strip(),
                **intent_fields,
            }
        )

    ranked_items.sort(key=_rank_key)
    for rank, item in enumerate(ranked_items, start=1):
        item["rank"] = rank

    promoted_items = [item for item in ranked_items if item["promotion_status"] == "promoted"]
    if not promoted_items:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "run_id": run_id,
                "blockers": ["no_promoted_research_candidates"],
                "ranked_candidates": ranked_items,
            },
        )
        write_json(run_root / "research-recommendation.report.json", report)
        return 1, report

    winner = promoted_items[0]
    rejected = [
        {
            "candidate_id": item["candidate_id"],
            "rank": item["rank"],
            "total_score": item["total_score"],
            "promotion_status": item["promotion_status"],
            "reason": "ranked_below_recommended_candidate",
        }
        for item in ranked_items
        if item["candidate_id"] != winner["candidate_id"]
    ]
    recommendation_packet = {
        "packet_type": "research_recommendation_packet",
        "packet_version": "v1",
        "packet_id": f"{problem_id}:research-recommendation",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "problem_id": problem_id,
        "candidate_search_tree_ref": str((repo_root / candidate_search_tree_path).resolve()),
        "evaluation_summary_ref": str((repo_root / evaluation_summary_path).resolve()),
        "evaluation_refs": [str((repo_root / path).resolve()) for path in evaluation_paths],
        "ranked_candidates": ranked_items,
        "recommended_candidate_id": winner["candidate_id"],
        "recommendation_reason": (
            "Top promoted candidate after evaluation-backed ranking by promotion status "
            "and total evaluation score."
        ),
        "winner_evidence_refs": winner["evidence_refs"],
        "rejected_candidate_summaries": rejected,
        "open_questions": [],
        "artifact_refs": _string_list(candidates_by_id[winner["candidate_id"]].get("artifact_refs", [])),
        "evidence_refs": sorted(
            {
                evidence_ref
                for item in ranked_items
                for evidence_ref in _string_list(item.get("evidence_refs", []))
            }
        ),
    }
    recommendation_path = write_json(
        run_root / "research-recommendation.packet.json",
        recommendation_packet,
    )

    report = envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "run_id": run_id,
            "candidate_search_tree_path": str((repo_root / candidate_search_tree_path).resolve()),
            "candidate_paths": [str((repo_root / path).resolve()) for path in candidate_paths],
            "evaluation_paths": [str((repo_root / path).resolve()) for path in evaluation_paths],
            "evaluation_summary_path": str((repo_root / evaluation_summary_path).resolve()),
            "recommendation_packet_path": recommendation_path.as_posix(),
            "recommended_candidate_id": winner["candidate_id"],
            "blockers": [],
        },
    )
    write_json(run_root / "research-recommendation.report.json", report)
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--candidate-search-tree-path", required=True)
    parser.add_argument("--candidate", action="append", dest="candidates", required=True)
    parser.add_argument("--evaluation", action="append", dest="evaluations", required=True)
    parser.add_argument("--evaluation-summary-path", required=True)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    args = parser.parse_args()
    try:
        code, report = materialize_research_recommendation(
            root=args.root,
            candidate_search_tree_path=args.candidate_search_tree_path,
            candidate_paths=args.candidates,
            evaluation_paths=args.evaluations,
            evaluation_summary_path=args.evaluation_summary_path,
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
