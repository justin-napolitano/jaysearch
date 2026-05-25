from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "select-implementation-attempt"
DEFAULT_OUTPUT_ROOT = Path("artifacts/attempt-selections/runs")
SELECTION_POLICY_REF = "docs/execution-era-multi-attempt-selection-research-v1.md#v1-selector-policy"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("ais-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _has_command_evidence(evaluation: dict[str, Any]) -> bool:
    evidence_refs = _string_list(evaluation.get("evidence_refs", []))
    if any("validation-command" in ref for ref in evidence_refs):
        return True
    for result in evaluation.get("validation_results", []):
        if isinstance(result, dict) and result.get("command") and result.get("status") in {
            "passed",
            "executed",
        }:
            return True
    return False


def _has_patch_evidence(evaluation: dict[str, Any]) -> bool:
    evidence_refs = _string_list(evaluation.get("evidence_refs", []))
    return any("patch-validation" in ref for ref in evidence_refs)


def _candidate_score(
    *,
    attempt_ref: str,
    attempt: dict[str, Any],
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    blockers = _string_list(evaluation.get("blockers", []))
    promoted = str(evaluation.get("promotion_status", "")).strip() == "promoted"
    eligible = promoted and not blockers
    command_evidence = _has_command_evidence(evaluation)
    patch_evidence = _has_patch_evidence(evaluation)
    changed_artifact_count = len(_string_list(attempt.get("changed_artifact_refs", [])))
    evidence_count = len(_string_list(evaluation.get("evidence_refs", [])))
    score_tuple = [
        1 if eligible else 0,
        1 if promoted else 0,
        1 if command_evidence else 0,
        1 if patch_evidence else 0,
        -changed_artifact_count,
        evidence_count,
    ]
    return {
        "attempt_ref": attempt_ref,
        "eligible": eligible,
        "promotion_status": str(evaluation.get("promotion_status", "")).strip(),
        "evaluation_blockers": blockers,
        "command_evidence": command_evidence,
        "patch_validation_evidence": patch_evidence,
        "changed_artifact_count": changed_artifact_count,
        "evidence_count": evidence_count,
        "score_tuple": score_tuple,
    }


def select_implementation_attempt(
    *,
    root: str = ".",
    execution_unit_path: str,
    attempt_paths: list[str],
    evaluation_paths: list[str],
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    execution_unit = _load_json(repo_root / execution_unit_path)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    if str(execution_unit.get("packet_type", "")).strip() != "execution_unit":
        blockers.append("execution_unit_packet_type_invalid")
    if len(attempt_paths) != len(evaluation_paths):
        blockers.append("attempt_evaluation_count_mismatch")
    if len(attempt_paths) < 1:
        blockers.append("attempt_paths_missing")

    execution_ref = str((repo_root / execution_unit_path).resolve())
    candidate_scores: list[dict[str, Any]] = []
    evidence_refs: list[str] = []
    loaded_attempts: list[tuple[str, dict[str, Any]]] = []
    loaded_evaluations: list[tuple[str, dict[str, Any]]] = []
    if not blockers:
        for attempt_path, evaluation_path in zip(attempt_paths, evaluation_paths):
            attempt_ref = str((repo_root / attempt_path).resolve())
            evaluation_ref = str((repo_root / evaluation_path).resolve())
            attempt = _load_json(repo_root / attempt_path)
            evaluation = _load_json(repo_root / evaluation_path)
            loaded_attempts.append((attempt_ref, attempt))
            loaded_evaluations.append((evaluation_ref, evaluation))
            if str(attempt.get("packet_type", "")).strip() != "implementation_attempt":
                blockers.append(f"implementation_attempt_packet_type_invalid:{attempt_path}")
            if str(evaluation.get("packet_type", "")).strip() != "attempt_evaluation":
                blockers.append(f"attempt_evaluation_packet_type_invalid:{evaluation_path}")
            if str(attempt.get("source_execution_unit_ref", "")).strip() != execution_ref:
                blockers.append(f"attempt_source_execution_unit_ref_mismatch:{attempt_path}")
            if str(evaluation.get("source_execution_unit_ref", "")).strip() != execution_ref:
                blockers.append(f"evaluation_source_execution_unit_ref_mismatch:{evaluation_path}")
            if str(evaluation.get("source_attempt_ref", "")).strip() != attempt_ref:
                blockers.append(f"evaluation_source_attempt_ref_mismatch:{evaluation_path}")
            evidence_refs.extend(_string_list(evaluation.get("evidence_refs", [])))
            candidate_scores.append(
                {
                    **_candidate_score(
                        attempt_ref=attempt_ref,
                        attempt=attempt,
                        evaluation=evaluation,
                    ),
                    "evaluation_ref": evaluation_ref,
                }
            )

    eligible_candidates = [candidate for candidate in candidate_scores if candidate["eligible"]]
    if not blockers and not eligible_candidates:
        blockers.append("no_eligible_attempts")

    selected_attempt_ref = ""
    selected_evaluation_ref = ""
    if not blockers:
        best_score = max(candidate["score_tuple"] for candidate in eligible_candidates)
        selected = sorted(
            (candidate for candidate in eligible_candidates if candidate["score_tuple"] == best_score),
            key=lambda candidate: candidate["attempt_ref"],
        )[0]
        selected_attempt_ref = str(selected["attempt_ref"])
        selected_evaluation_ref = str(selected["evaluation_ref"])

    rejected_attempt_refs = [
        ref for ref, _attempt in loaded_attempts if ref != selected_attempt_ref
    ]
    rejected_evaluation_refs = [
        ref for ref, _evaluation in loaded_evaluations if ref != selected_evaluation_ref
    ]

    selection_path = ""
    if not blockers:
        selection_id = f"attempt-selection:{str(execution_unit.get('execution_unit_id', 'execution')).replace(':', '-')}"
        selection = {
            "packet_type": "attempt_selection",
            "packet_version": "v1",
            "packet_id": f"{selection_id}:packet",
            "created_at": _utc_now(),
            "producer": COMMAND,
            "selection_id": selection_id,
            "source_execution_unit_ref": execution_ref,
            "selected_attempt_ref": selected_attempt_ref,
            "selected_evaluation_ref": selected_evaluation_ref,
            "rejected_attempt_refs": rejected_attempt_refs,
            "rejected_evaluation_refs": rejected_evaluation_refs,
            "candidate_score_breakdown": candidate_scores,
            "selection_policy_ref": SELECTION_POLICY_REF,
            "evidence_refs": sorted(set(evidence_refs)),
            "blockers": [],
        }
        selection_path = write_json(run_root / "attempt-selection.packet.json", selection).as_posix()

    report = envelope(
        command=COMMAND,
        status="ok" if not blockers else "blocked",
        ok=not blockers,
        payload={
            "run_id": run_id,
            "execution_unit_path": execution_ref,
            "attempt_selection_path": selection_path,
            "selected_attempt_ref": selected_attempt_ref,
            "selected_evaluation_ref": selected_evaluation_ref,
            "rejected_attempt_refs": rejected_attempt_refs,
            "rejected_evaluation_refs": rejected_evaluation_refs,
            "candidate_score_breakdown": candidate_scores,
            "blockers": sorted(set(blockers)),
        },
    )
    write_json(run_root / "attempt-selection.report.json", report)
    return (0 if not blockers else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--execution-unit-path", required=True)
    parser.add_argument("--attempt-path", action="append", default=[])
    parser.add_argument("--evaluation-path", action="append", default=[])
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    args = parser.parse_args()
    try:
        code, report = select_implementation_attempt(
            root=args.root,
            execution_unit_path=args.execution_unit_path,
            attempt_paths=args.attempt_path,
            evaluation_paths=args.evaluation_path,
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
