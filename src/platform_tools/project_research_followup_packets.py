from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import API_VERSION, envelope


COMMAND = "project-research-followup-packets"


def _load_json_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("json_payload_not_object")
    return payload


def _slugify(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    return "-".join(part for part in cleaned.split("-") if part)


def _platform_execplan_seed(followup: dict[str, Any]) -> dict[str, Any]:
    suggested = followup.get("suggested_execplan_seed", {})
    if not isinstance(suggested, dict):
        suggested = {}
    candidate_id = str(followup.get("source_candidate_id", "")).strip()
    target = str(followup.get("target", "")).strip()
    slug = _slugify(candidate_id or target or "research-followup") or "research-followup"
    title = str(suggested.get("title", "")).strip() or f"Promote ranked research candidate {candidate_id or target}"
    return {
        "seed_id": f"platform-seed-{candidate_id or slug}",
        "title": title,
        "initiative_branch": str(suggested.get("initiative_branch", "")).strip() or "initiative/research-control-plane",
        "implementation_branch_hint": str(suggested.get("implementation_branch_hint", "")).strip()
        or f"impl-execplan/{slug}",
        "source_request_id": str(followup.get("source_request_id", "")).strip(),
        "source_question_id": str(followup.get("source_question_id", "")).strip(),
        "source_candidate_id": candidate_id,
        "proposed_change": str(followup.get("proposed_change", "")).strip(),
        "expected_benefit": str(followup.get("expected_benefit", "")).strip(),
        "evidence_refs": [str(item).strip() for item in followup.get("evidence_refs", []) if str(item).strip()]
        if isinstance(followup.get("evidence_refs"), list)
        else [],
        "linked_follow_up_questions": followup.get("linked_follow_up_questions", [])
        if isinstance(followup.get("linked_follow_up_questions"), list)
        else [],
    }


def _external_repo_request(followup: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(followup.get("source_candidate_id", "")).strip()
    target_repo_hint = str(followup.get("target_repo_hint", "")).strip()
    target = str(followup.get("target", "")).strip()
    slug = _slugify(candidate_id or target or target_repo_hint or "research-followup") or "research-followup"
    return {
        "request_packet_id": f"{target_repo_hint or 'repo'}-{candidate_id or slug}",
        "target_repo_hint": target_repo_hint,
        "target": target,
        "suggested_branch_hint": f"feat/{slug}",
        "source_request_id": str(followup.get("source_request_id", "")).strip(),
        "source_question_id": str(followup.get("source_question_id", "")).strip(),
        "source_candidate_id": candidate_id,
        "source_hypothesis_ids": followup.get("source_hypothesis_ids", [])
        if isinstance(followup.get("source_hypothesis_ids"), list)
        else [],
        "proposed_change": str(followup.get("proposed_change", "")).strip(),
        "expected_benefit": str(followup.get("expected_benefit", "")).strip(),
        "delivery_mode": str(followup.get("delivery_mode", "")).strip() or "repo_followup_request",
        "evidence_refs": [str(item).strip() for item in followup.get("evidence_refs", []) if str(item).strip()]
        if isinstance(followup.get("evidence_refs"), list)
        else [],
        "linked_follow_up_questions": followup.get("linked_follow_up_questions", [])
        if isinstance(followup.get("linked_follow_up_questions"), list)
        else [],
    }


def _write_packets_artifact(
    *,
    output_root: Path,
    prepared_followups_path: Path,
    payload: dict[str, Any],
    platform_execplan_seeds: list[dict[str, Any]],
    repo_followup_requests: list[dict[str, Any]],
) -> Path:
    source_request_id = str(payload.get("source_request_id", "")).strip()
    artifact = {
        "api_version": API_VERSION,
        "source_command": "prepare-research-followups",
        "prepared_followups_path": prepared_followups_path.as_posix(),
        "source_request_id": source_request_id,
        "source_question_id": str(payload.get("source_question_id", "")).strip(),
        "source_question_origin": str(payload.get("source_question_origin", "")).strip(),
        "platform_execplan_seeds": platform_execplan_seeds,
        "repo_followup_requests": repo_followup_requests,
    }
    path = output_root / "execution" / "repo_followup_packets" / f"{source_request_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return path


def project_research_followup_packets(
    *,
    root: str = ".",
    prepared_followups_path: str,
    output_root: str,
) -> tuple[int, dict[str, Any]]:
    platform_root = Path(root).resolve()
    prepared_path = Path(prepared_followups_path).resolve()
    destination_root = Path(output_root).resolve()

    blockers: list[str] = []
    if not prepared_path.exists():
        blockers.append("prepared_followups_path_missing")
    if not str(output_root).strip():
        blockers.append("output_root_missing")

    payload: dict[str, Any] = {}
    if not blockers:
        try:
            payload = _load_json_file(prepared_path)
        except (OSError, ValueError, json.JSONDecodeError):
            blockers.append("prepared_followups_payload_invalid")

    if payload:
        if str(payload.get("source_command", "")).strip() != "run-research-capability":
            blockers.append("prepared_followups_source_command_invalid")
        draft_inputs = payload.get("draft_followup_inputs", [])
        if not isinstance(draft_inputs, list):
            blockers.append("prepared_followups_missing_inputs")

    if blockers:
        return 1, envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "platform_root": platform_root.as_posix(),
                "prepared_followups_path": prepared_path.as_posix(),
                "output_root": destination_root.as_posix(),
                "blockers": sorted(set(blockers)),
            },
        )

    draft_inputs = [item for item in payload.get("draft_followup_inputs", []) if isinstance(item, dict)]
    platform_execplan_seeds: list[dict[str, Any]] = []
    repo_followup_requests: list[dict[str, Any]] = []
    for followup in draft_inputs:
        delivery_mode = str(followup.get("delivery_mode", "")).strip()
        target_repo_hint = str(followup.get("target_repo_hint", "")).strip()
        if delivery_mode == "governed_execplan" and target_repo_hint == "codex_platform":
            platform_execplan_seeds.append(_platform_execplan_seed(followup))
        else:
            repo_followup_requests.append(_external_repo_request(followup))

    artifact_path = _write_packets_artifact(
        output_root=destination_root,
        prepared_followups_path=prepared_path,
        payload=payload,
        platform_execplan_seeds=platform_execplan_seeds,
        repo_followup_requests=repo_followup_requests,
    )

    return 0, envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "platform_root": platform_root.as_posix(),
            "prepared_followups_path": prepared_path.as_posix(),
            "output_root": destination_root.as_posix(),
            "source_request_id": str(payload.get("source_request_id", "")).strip(),
            "source_question_id": str(payload.get("source_question_id", "")).strip(),
            "source_question_origin": str(payload.get("source_question_origin", "")).strip(),
            "packets_path": artifact_path.as_posix(),
            "platform_execplan_seeds": platform_execplan_seeds,
            "repo_followup_requests": repo_followup_requests,
            "next_action": "review_repo_followup_packets",
            "blockers": [],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--prepared-followups-path", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    code, report = project_research_followup_packets(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
