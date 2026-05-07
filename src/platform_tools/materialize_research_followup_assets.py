from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import API_VERSION, envelope


COMMAND = "materialize-research-followup-assets"


def _load_json_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("json_payload_not_object")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _render_execplan_seed_markdown(seed: dict[str, Any]) -> str:
    linked_questions = seed.get("linked_follow_up_questions", [])
    if not isinstance(linked_questions, list):
        linked_questions = []
    evidence_refs = seed.get("evidence_refs", [])
    if not isinstance(evidence_refs, list):
        evidence_refs = []
    lines = [
        f"# Platform ExecPlan Seed: {str(seed.get('title', '')).strip() or str(seed.get('seed_id', '')).strip()}",
        "",
        "## Suggested Branching",
        f"- initiative_branch: `{str(seed.get('initiative_branch', '')).strip()}`",
        f"- implementation_branch_hint: `{str(seed.get('implementation_branch_hint', '')).strip()}`",
        "",
        "## Provenance",
        f"- source_request_id: `{str(seed.get('source_request_id', '')).strip()}`",
        f"- source_question_id: `{str(seed.get('source_question_id', '')).strip()}`",
        f"- source_candidate_id: `{str(seed.get('source_candidate_id', '')).strip()}`",
        "",
        "## Proposed Change",
        str(seed.get("proposed_change", "")).strip() or "No proposed change recorded.",
        "",
        "## Expected Benefit",
        str(seed.get("expected_benefit", "")).strip() or "No expected benefit recorded.",
        "",
        "## Evidence References",
    ]
    if evidence_refs:
        for ref in evidence_refs:
            ref_text = str(ref).strip()
            if ref_text:
                lines.append(f"- {ref_text}")
    else:
        lines.append("- none recorded")
    lines.extend(["", "## Linked Follow-up Questions"])
    if linked_questions:
        for item in linked_questions:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{str(item.get('question_id', '')).strip()}`: {str(item.get('topic', '')).strip() or 'no topic recorded'}"
            )
    else:
        lines.append("- none recorded")
    return "\n".join(lines) + "\n"


def _materialize_platform_seed(seed: dict[str, Any], *, output_root: Path) -> dict[str, str]:
    seed_id = str(seed.get("seed_id", "")).strip() or "platform-seed"
    json_path = output_root / "execution" / "platform_execplan_seeds" / f"{seed_id}.json"
    md_path = output_root / "execution" / "platform_execplan_seeds" / f"{seed_id}.md"
    _write_json(json_path, seed)
    _write_text(md_path, _render_execplan_seed_markdown(seed))
    return {
        "seed_id": seed_id,
        "json_path": json_path.as_posix(),
        "markdown_path": md_path.as_posix(),
    }


def _materialize_repo_request(packet: dict[str, Any], *, output_root: Path) -> dict[str, str]:
    packet_id = str(packet.get("request_packet_id", "")).strip() or "repo-followup"
    target_repo_hint = str(packet.get("target_repo_hint", "")).strip() or "external-repo"
    payload = {
        "request_kind": "repo_followup_request.v1",
        "request_packet_id": packet_id,
        "target_repo_hint": target_repo_hint,
        "target": str(packet.get("target", "")).strip(),
        "suggested_branch_hint": str(packet.get("suggested_branch_hint", "")).strip(),
        "source_request_id": str(packet.get("source_request_id", "")).strip(),
        "source_question_id": str(packet.get("source_question_id", "")).strip(),
        "source_candidate_id": str(packet.get("source_candidate_id", "")).strip(),
        "source_hypothesis_ids": packet.get("source_hypothesis_ids", [])
        if isinstance(packet.get("source_hypothesis_ids"), list)
        else [],
        "proposed_change": str(packet.get("proposed_change", "")).strip(),
        "expected_benefit": str(packet.get("expected_benefit", "")).strip(),
        "delivery_mode": str(packet.get("delivery_mode", "")).strip(),
        "evidence_refs": [str(item).strip() for item in packet.get("evidence_refs", []) if str(item).strip()]
        if isinstance(packet.get("evidence_refs"), list)
        else [],
        "linked_follow_up_questions": packet.get("linked_follow_up_questions", [])
        if isinstance(packet.get("linked_follow_up_questions"), list)
        else [],
    }
    json_path = output_root / "execution" / "repo_request_packets" / target_repo_hint / f"{packet_id}.json"
    _write_json(json_path, payload)
    return {
        "request_packet_id": packet_id,
        "target_repo_hint": target_repo_hint,
        "json_path": json_path.as_posix(),
    }


def _write_manifest(
    *,
    output_root: Path,
    packets_path: Path,
    payload: dict[str, Any],
    platform_seed_files: list[dict[str, str]],
    repo_request_files: list[dict[str, str]],
) -> Path:
    manifest = {
        "api_version": API_VERSION,
        "source_command": "project-research-followup-packets",
        "packets_path": packets_path.as_posix(),
        "source_request_id": str(payload.get("source_request_id", "")).strip(),
        "source_question_id": str(payload.get("source_question_id", "")).strip(),
        "source_question_origin": str(payload.get("source_question_origin", "")).strip(),
        "platform_seed_files": platform_seed_files,
        "repo_request_files": repo_request_files,
    }
    manifest_path = output_root / "execution" / "materialized_followup_assets" / f"{manifest['source_request_id']}.json"
    return _write_json(manifest_path, manifest)


def materialize_research_followup_assets(
    *,
    root: str = ".",
    packets_path: str,
    output_root: str,
) -> tuple[int, dict[str, Any]]:
    platform_root = Path(root).resolve()
    packets_file = Path(packets_path).resolve()
    destination_root = Path(output_root).resolve()

    blockers: list[str] = []
    if not packets_file.exists():
        blockers.append("packets_path_missing")
    if not str(output_root).strip():
        blockers.append("output_root_missing")

    payload: dict[str, Any] = {}
    if not blockers:
        try:
            payload = _load_json_file(packets_file)
        except (OSError, ValueError, json.JSONDecodeError):
            blockers.append("packets_payload_invalid")

    if payload:
        if str(payload.get("source_command", "")).strip() != "prepare-research-followups":
            blockers.append("packets_source_command_invalid")
        if not isinstance(payload.get("platform_execplan_seeds", []), list):
            blockers.append("packets_missing_platform_execplan_seeds")
        if not isinstance(payload.get("repo_followup_requests", []), list):
            blockers.append("packets_missing_repo_followup_requests")

    if blockers:
        return 1, envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "platform_root": platform_root.as_posix(),
                "packets_path": packets_file.as_posix(),
                "output_root": destination_root.as_posix(),
                "blockers": sorted(set(blockers)),
            },
        )

    platform_seed_files = [
        _materialize_platform_seed(item, output_root=destination_root)
        for item in payload.get("platform_execplan_seeds", [])
        if isinstance(item, dict)
    ]
    repo_request_files = [
        _materialize_repo_request(item, output_root=destination_root)
        for item in payload.get("repo_followup_requests", [])
        if isinstance(item, dict)
    ]
    manifest_path = _write_manifest(
        output_root=destination_root,
        packets_path=packets_file,
        payload=payload,
        platform_seed_files=platform_seed_files,
        repo_request_files=repo_request_files,
    )

    return 0, envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "platform_root": platform_root.as_posix(),
            "packets_path": packets_file.as_posix(),
            "output_root": destination_root.as_posix(),
            "source_request_id": str(payload.get("source_request_id", "")).strip(),
            "source_question_id": str(payload.get("source_question_id", "")).strip(),
            "source_question_origin": str(payload.get("source_question_origin", "")).strip(),
            "manifest_path": manifest_path.as_posix(),
            "platform_seed_files": platform_seed_files,
            "repo_request_files": repo_request_files,
            "next_action": "review_materialized_followup_assets",
            "blockers": [],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--packets-path", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    code, report = materialize_research_followup_assets(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
