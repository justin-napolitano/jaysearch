from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import API_VERSION, envelope


COMMAND = "prepare-research-followups"
DEFAULT_MINIMUM_TOTAL_SCORE = 4.0
DEFAULT_MAX_PROMOTIONS = 3
PLATFORM_INITIATIVE_BRANCH = "initiative/research-control-plane"


def _load_json_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("json_payload_not_object")
    return payload


def _slugify(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    return "-".join(part for part in cleaned.split("-") if part)


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalized_disposition(value: Any) -> str:
    return str(value or "").strip().lower().replace("_", "-")


def _candidate_gate(candidate_payload: dict[str, Any], minimum_total_score: float | None) -> dict[str, float]:
    ranking_rubric = candidate_payload.get("ranking_rubric", {})
    promotion_gate = ranking_rubric.get("promotion_gate", {}) if isinstance(ranking_rubric, dict) else {}
    min_rigor = float(promotion_gate.get("minimum_rigor", 3.0))
    min_feasibility = float(promotion_gate.get("minimum_feasibility", 3.0))
    min_total = float(
        minimum_total_score
        if minimum_total_score is not None
        else promotion_gate.get("minimum_total_score", DEFAULT_MINIMUM_TOTAL_SCORE)
    )
    return {
        "minimum_rigor": min_rigor,
        "minimum_feasibility": min_feasibility,
        "minimum_total_score": min_total,
    }


def _evaluate_candidate(candidate: dict[str, Any], gate: dict[str, float]) -> dict[str, Any]:
    scores = candidate.get("scores", {})
    if not isinstance(scores, dict):
        scores = {}
    rigor = _coerce_float(scores.get("rigor", 0.0))
    feasibility = _coerce_float(scores.get("feasibility", 0.0))
    total_score = _coerce_float(candidate.get("total_score", 0.0))
    evidence_refs = candidate.get("evidence_refs", [])
    proposed_change = str(candidate.get("proposed_change", "")).strip()
    target_repo_hint = str(candidate.get("target_repo_hint", "")).strip()
    normalized_evidence_refs = (
        [str(item).strip() for item in evidence_refs if str(item).strip()]
        if isinstance(evidence_refs, list)
        else []
    )
    checks = {
        "disposition_ok": _normalized_disposition(candidate.get("disposition", "")) == "promote-to-execplan",
        "rigor_ok": rigor >= gate["minimum_rigor"],
        "feasibility_ok": feasibility >= gate["minimum_feasibility"],
        "total_score_ok": total_score >= gate["minimum_total_score"],
        "evidence_refs_ok": bool(normalized_evidence_refs),
        "proposed_change_ok": bool(proposed_change),
        "target_repo_hint_ok": bool(target_repo_hint),
    }
    failure_reasons = [key for key, value in checks.items() if not value]
    return {
        "normalized_disposition": _normalized_disposition(candidate.get("disposition", "")),
        "scores": {
            "rigor": rigor,
            "feasibility": feasibility,
            "total_score": total_score,
        },
        "checks": checks,
        "failure_reasons": failure_reasons,
        "promotable": not failure_reasons,
        "usable_evidence_refs": normalized_evidence_refs,
    }


def _candidate_selection_status(
    *,
    evaluation: dict[str, Any],
    selected: bool,
    promotion_cap_reached: bool,
) -> str:
    if selected:
        return "selected_for_followup"
    if bool(evaluation.get("promotable")) and promotion_cap_reached:
        return "deferred_promotion_cap"
    if not bool(evaluation.get("promotable")):
        return "failed_gate"
    return "deferred"


def _selection_summary(selected: list[dict[str, Any]], deferred: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    failure_reason_counts: dict[str, int] = {}
    for candidate in [*selected, *deferred]:
        status = str(candidate.get("selection_status", "")).strip() or "unknown"
        status_counts[status] = status_counts.get(status, 0) + 1
        gate_evaluation = candidate.get("gate_evaluation", {})
        if not isinstance(gate_evaluation, dict):
            continue
        for reason in gate_evaluation.get("failure_reasons", []):
            failure_reason = str(reason).strip()
            if failure_reason:
                failure_reason_counts[failure_reason] = failure_reason_counts.get(failure_reason, 0) + 1
    return {
        "selected_count": len(selected),
        "deferred_count": len(deferred),
        "selection_status_counts": status_counts,
        "failure_reason_counts": failure_reason_counts,
    }


def _suggested_execplan_seed(candidate: dict[str, Any], *, source_request_id: str, source_question_id: str) -> dict[str, Any] | None:
    target_repo_hint = str(candidate.get("target_repo_hint", "")).strip()
    target = str(candidate.get("target", "")).strip()
    candidate_id = str(candidate.get("candidate_id", "")).strip()
    if target_repo_hint != "codex_platform":
        return None
    slug = _slugify(candidate_id or target or source_request_id) or "research-followup"
    return {
        "title": f"Promote ranked research candidate {candidate_id or target}",
        "initiative_branch": PLATFORM_INITIATIVE_BRANCH,
        "implementation_branch_hint": f"impl-execplan/{slug}",
        "source_request_id": source_request_id,
        "source_question_id": source_question_id,
        "source_candidate_id": candidate_id,
    }


def _follow_up_seed(
    candidate: dict[str, Any],
    *,
    source_request_id: str,
    source_question_id: str,
    source_question_origin: str,
    linked_questions: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "followup_id": f"{source_request_id}-{str(candidate.get('candidate_id', '')).strip() or 'candidate'}",
        "source_request_id": source_request_id,
        "source_question_id": source_question_id,
        "source_question_origin": source_question_origin,
        "source_candidate_id": str(candidate.get("candidate_id", "")).strip(),
        "source_hypothesis_ids": candidate.get("source_hypothesis_ids", [])
        if isinstance(candidate.get("source_hypothesis_ids"), list)
        else [],
        "target": str(candidate.get("target", "")).strip(),
        "target_repo_hint": str(candidate.get("target_repo_hint", "")).strip(),
        "proposed_change": str(candidate.get("proposed_change", "")).strip(),
        "expected_benefit": str(candidate.get("expected_benefit", "")).strip(),
        "total_score": float(candidate.get("total_score", 0.0)),
        "delivery_mode": (
            "governed_execplan"
            if str(candidate.get("target_repo_hint", "")).strip() == "codex_platform"
            else "repo_followup_request"
        ),
        "evidence_refs": [str(item).strip() for item in candidate.get("evidence_refs", []) if str(item).strip()]
        if isinstance(candidate.get("evidence_refs"), list)
        else [],
        "linked_follow_up_questions": linked_questions,
        "suggested_execplan_seed": _suggested_execplan_seed(
            candidate,
            source_request_id=source_request_id,
            source_question_id=source_question_id,
        ),
    }


def _write_followup_artifact(
    *,
    output_root: Path,
    report_path: Path,
    report: dict[str, Any],
    candidate_payload: dict[str, Any],
    gate: dict[str, float],
    selected: list[dict[str, Any]],
    deferred: list[dict[str, Any]],
    max_promotions: int,
) -> Path:
    request_id = str(report.get("request_id", "")).strip()
    question_id = str(candidate_payload.get("question_id", "")).strip()
    question_origin = str(candidate_payload.get("question_origin", "")).strip()
    follow_up_questions = candidate_payload.get("follow_up_questions", [])
    if not isinstance(follow_up_questions, list):
        follow_up_questions = []

    followup_inputs = []
    for candidate in selected:
        candidate_id = str(candidate.get("candidate_id", "")).strip()
        linked_questions = []
        for item in follow_up_questions:
            if not isinstance(item, dict):
                continue
            linked = item.get("linked_candidate_ids", [])
            linked_ids = {str(ref).strip() for ref in linked if str(ref).strip()} if isinstance(linked, list) else set()
            if candidate_id and candidate_id in linked_ids:
                linked_questions.append(item)
        followup_inputs.append(
            _follow_up_seed(
                candidate,
                source_request_id=request_id,
                source_question_id=question_id,
                source_question_origin=question_origin,
                linked_questions=linked_questions,
            )
        )

    payload = {
        "api_version": API_VERSION,
        "source_command": "run-research-capability",
        "source_report_path": report_path.as_posix(),
        "source_request_id": request_id,
        "source_question_id": question_id,
        "source_question_origin": question_origin,
        "promotion_gate": gate,
        "max_promotions": max_promotions,
        "selected_candidates": selected,
        "deferred_candidates": deferred,
        "selection_summary": _selection_summary(selected, deferred),
        "follow_up_questions": follow_up_questions,
        "draft_followup_inputs": followup_inputs,
    }
    artifact_path = output_root / "execution" / "draft_followups" / f"{request_id}.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return artifact_path


def prepare_research_followups(
    *,
    root: str = ".",
    report_path: str,
    output_root: str,
    max_promotions: int = DEFAULT_MAX_PROMOTIONS,
    minimum_total_score: float | None = None,
) -> tuple[int, dict[str, Any]]:
    platform_root = Path(root).resolve()
    report_file = Path(report_path).resolve()
    destination_root = Path(output_root).resolve()

    blockers: list[str] = []
    if not report_file.exists():
        blockers.append("report_path_missing")
    if not str(output_root).strip():
        blockers.append("output_root_missing")
    if max_promotions < 1:
        blockers.append("max_promotions_invalid")
    if minimum_total_score is not None and minimum_total_score <= 0:
        blockers.append("minimum_total_score_invalid")

    report: dict[str, Any] = {}
    candidate_payload: dict[str, Any] = {}
    if not blockers:
        try:
            report = _load_json_file(report_file)
        except (OSError, ValueError, json.JSONDecodeError):
            blockers.append("report_payload_invalid")

    if report:
        if str(report.get("command", "")).strip() != "run-research-capability":
            blockers.append("report_command_invalid")
        if report.get("ok") is not True or str(report.get("status", "")).strip() != "ok":
            blockers.append("report_status_not_ok")
        candidates_path = str(report.get("improvement_candidates_path", "")).strip()
        if not candidates_path:
            blockers.append("report_missing_improvement_candidates_path")
        else:
            try:
                candidate_payload = _load_json_file(Path(candidates_path))
            except (OSError, ValueError, json.JSONDecodeError):
                blockers.append("candidate_payload_invalid")

    if blockers:
        return 1, envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "platform_root": platform_root.as_posix(),
                "report_path": report_file.as_posix(),
                "output_root": destination_root.as_posix(),
                "blockers": sorted(set(blockers)),
            },
        )

    gate = _candidate_gate(candidate_payload, minimum_total_score)
    ranked_candidates = candidate_payload.get("candidates", [])
    if not isinstance(ranked_candidates, list):
        ranked_candidates = []
    ranked_candidates = [
        item for item in ranked_candidates if isinstance(item, dict)
    ]
    ranked_candidates.sort(key=lambda item: (_coerce_float(item.get("total_score", 0.0)), str(item.get("candidate_id", ""))), reverse=True)

    selected = []
    deferred = []
    for candidate in ranked_candidates:
        candidate_record = dict(candidate)
        evaluation = _evaluate_candidate(candidate_record, gate)
        candidate_record["gate_evaluation"] = evaluation
        candidate_record["normalized_disposition"] = evaluation["normalized_disposition"]
        promotion_cap_reached = len(selected) >= max_promotions
        is_selected = bool(evaluation.get("promotable")) and not promotion_cap_reached
        candidate_record["selection_status"] = _candidate_selection_status(
            evaluation=evaluation,
            selected=is_selected,
            promotion_cap_reached=promotion_cap_reached,
        )
        if is_selected:
            selected.append(candidate_record)
        else:
            deferred.append(candidate_record)

    artifact_path = _write_followup_artifact(
        output_root=destination_root,
        report_path=report_file,
        report=report,
        candidate_payload=candidate_payload,
        gate=gate,
        selected=selected,
        deferred=deferred,
        max_promotions=max_promotions,
    )

    follow_up_questions = candidate_payload.get("follow_up_questions", [])
    if not isinstance(follow_up_questions, list):
        follow_up_questions = []

    return 0, envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "platform_root": platform_root.as_posix(),
            "report_path": report_file.as_posix(),
            "output_root": destination_root.as_posix(),
            "source_request_id": str(report.get("request_id", "")).strip(),
            "source_question_id": str(candidate_payload.get("question_id", "")).strip(),
            "source_question_origin": str(candidate_payload.get("question_origin", "")).strip(),
            "promotion_gate": gate,
            "max_promotions": max_promotions,
            "draft_followups_path": artifact_path.as_posix(),
            "selected_candidates": selected,
            "deferred_candidates": deferred,
            "selection_summary": _selection_summary(selected, deferred),
            "follow_up_questions": follow_up_questions,
            "next_action": "review_draft_followups",
            "blockers": [],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--report-path", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--max-promotions", type=int, default=DEFAULT_MAX_PROMOTIONS)
    parser.add_argument("--minimum-total-score", type=float, default=None)
    args = parser.parse_args()
    code, report = prepare_research_followups(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
