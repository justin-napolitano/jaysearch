from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import API_VERSION, envelope


COMMAND = "render-researcher-followup-handoffs"


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


def _source_refs_from_packet(packet: dict[str, Any]) -> list[dict[str, str]]:
    refs = packet.get("evidence_refs", [])
    if not isinstance(refs, list):
        return []
    source_refs: list[dict[str, str]] = []
    for index, item in enumerate(refs, start=1):
        url = str(item).strip()
        if not url:
            continue
        source_refs.append(
            {
                "title": f"Evidence Reference {index}",
                "url": url,
                "note": "Imported from platform-ranked follow-up candidate evidence references.",
            }
        )
    return source_refs


def _candidate_request_payload(packet: dict[str, Any], *, packet_path: Path, output_root: Path) -> dict[str, Any]:
    packet_id = str(packet.get("request_packet_id", "")).strip() or packet_path.stem
    source_request_id = str(packet.get("source_request_id", "")).strip()
    source_question_id = str(packet.get("source_question_id", "")).strip()
    source_candidate_id = str(packet.get("source_candidate_id", "")).strip()
    proposed_change = str(packet.get("proposed_change", "")).strip()
    expected_benefit = str(packet.get("expected_benefit", "")).strip()
    request_id = f"followup-{source_request_id}-{source_candidate_id or packet_id}"
    topic = (
        "Evaluate the proposed researcher-harness improvement candidate "
        f"`{source_candidate_id or packet_id}` and determine whether it should be promoted."
    )
    output_path = output_root / "execution" / "researcher_harness_runs" / request_id
    source_refs = _source_refs_from_packet(packet)
    return {
        "request_id": request_id,
        "question_id": f"followup-{source_question_id}-{source_candidate_id or packet_id}",
        "question_origin": "platform",
        "topic": topic,
        "study_design": "option-comparison",
        "artifact_contract": "v1",
        "output_root": output_path.as_posix(),
        "domain_plugins": ["governed-research-ops"],
        "improvement_targets": ["researcher-harness"],
        "hypotheses": [
            {
                "hypothesis_id": f"hyp-{source_candidate_id or packet_id}",
                "statement": proposed_change or "Evaluate the proposed change against the current harness state.",
                "expected_outcome": expected_benefit or "Determine whether the proposed change improves the harness.",
                "falsifiable_condition": "The proposed change cannot be supported with bounded evidence and a reviewable implementation path.",
                "evidence_required": [ref["url"] for ref in source_refs],
            }
        ],
        "required_sources": source_refs,
        "options": [
            {
                "option_id": "baseline-current-state",
                "summary": "Keep the current researcher-harness implementation and gather more evidence before changing it.",
                "strengths": ["No immediate implementation churn.", "Preserves current validated contracts."],
                "risks": ["Known gaps may persist longer.", "Improvement opportunity is deferred."],
            },
            {
                "option_id": "proposed-followup-change",
                "summary": proposed_change or "Apply the proposed follow-up change to researcher-harness.",
                "strengths": [expected_benefit or "Potential to improve the harness."],
                "risks": ["May introduce new contract or maintenance burden if poorly scoped."],
            },
        ],
        "findings": [],
        "stable_recommendation": False,
        "recommendation": "",
        "recommendation_rationale": "",
        "self_review_focus": "Critically review feasibility, evidence quality, contract fit, and testability before recommending implementation.",
    }


def _render_handoff_markdown(request_payload: dict[str, Any], *, request_path: Path) -> str:
    required_sources = request_payload.get("required_sources", [])
    if not isinstance(required_sources, list):
        required_sources = []
    hypotheses = request_payload.get("hypotheses", [])
    if not isinstance(hypotheses, list):
        hypotheses = []
    lines = [
        f"# Researcher Handoff: {request_payload.get('request_id', '')}",
        "",
        "## Execution",
        "- target_repo: `researcher-harness`",
        f"- request_path: `{request_path.as_posix()}`",
        "- command: `python3 -m researcher_harness.cli run --request <request_path>`",
        "",
        "## Topic",
        str(request_payload.get("topic", "")).strip() or "No topic recorded.",
        "",
        "## Hypotheses",
    ]
    if hypotheses:
        for item in hypotheses:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{str(item.get('hypothesis_id', '')).strip()}`: {str(item.get('statement', '')).strip() or 'no statement recorded'}"
            )
    else:
        lines.append("- none recorded")
    lines.extend(["", "## Required Sources"])
    if required_sources:
        for item in required_sources:
            if not isinstance(item, dict):
                continue
            lines.append(f"- {str(item.get('title', '')).strip() or 'source'}: {str(item.get('url', '')).strip()}")
    else:
        lines.append("- none recorded")
    lines.extend(
        [
            "",
            "## Notes",
            "- This asset is a supervised handoff packet, not an automatic repo mutation.",
            "- Run it through the researcher harness, then route the resulting candidates back through the platform control plane.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_packet_file(packet_path: Path, *, output_root: Path) -> dict[str, str]:
    packet = _load_json_file(packet_path)
    request_payload = _candidate_request_payload(packet, packet_path=packet_path, output_root=output_root)
    request_id = str(request_payload.get("request_id", "")).strip() or packet_path.stem
    request_path = output_root / "execution" / "researcher_handoff_requests" / f"{request_id}.request.json"
    instructions_path = output_root / "execution" / "researcher_handoff_requests" / f"{request_id}.md"
    _write_json(request_path, request_payload)
    _write_text(instructions_path, _render_handoff_markdown(request_payload, request_path=request_path))
    return {
        "request_id": request_id,
        "source_packet_path": packet_path.as_posix(),
        "request_path": request_path.as_posix(),
        "instructions_path": instructions_path.as_posix(),
    }


def _write_manifest(
    *,
    output_root: Path,
    source_manifest_path: Path,
    payload: dict[str, Any],
    handoff_files: list[dict[str, str]],
) -> Path:
    manifest = {
        "api_version": API_VERSION,
        "source_command": "materialize-research-followup-assets",
        "source_manifest_path": source_manifest_path.as_posix(),
        "source_request_id": str(payload.get("source_request_id", "")).strip(),
        "source_question_id": str(payload.get("source_question_id", "")).strip(),
        "source_question_origin": str(payload.get("source_question_origin", "")).strip(),
        "handoff_files": handoff_files,
    }
    path = output_root / "execution" / "researcher_handoff_requests" / f"{manifest['source_request_id']}.manifest.json"
    return _write_json(path, manifest)


def render_researcher_followup_handoffs(
    *,
    root: str = ".",
    materialized_manifest_path: str,
    output_root: str,
) -> tuple[int, dict[str, Any]]:
    platform_root = Path(root).resolve()
    manifest_path = Path(materialized_manifest_path).resolve()
    destination_root = Path(output_root).resolve()

    blockers: list[str] = []
    if not manifest_path.exists():
        blockers.append("materialized_manifest_path_missing")
    if not str(output_root).strip():
        blockers.append("output_root_missing")

    payload: dict[str, Any] = {}
    repo_request_files: list[dict[str, Any]] = []
    if not blockers:
        try:
            payload = _load_json_file(manifest_path)
        except (OSError, ValueError, json.JSONDecodeError):
            blockers.append("materialized_manifest_payload_invalid")

    if payload:
        if str(payload.get("source_command", "")).strip() != "project-research-followup-packets":
            blockers.append("materialized_manifest_source_command_invalid")
        repo_request_files = payload.get("repo_request_files", [])
        if not isinstance(repo_request_files, list):
            blockers.append("materialized_manifest_missing_repo_request_files")
            repo_request_files = []

    if blockers:
        return 1, envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "platform_root": platform_root.as_posix(),
                "materialized_manifest_path": manifest_path.as_posix(),
                "output_root": destination_root.as_posix(),
                "blockers": sorted(set(blockers)),
            },
        )

    handoff_files = []
    for item in repo_request_files:
        if not isinstance(item, dict):
            continue
        packet_json_path = str(item.get("json_path", "")).strip()
        if not packet_json_path:
            continue
        packet_path = Path(packet_json_path)
        try:
            packet_payload = _load_json_file(packet_path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        target_repo_hint = str(packet_payload.get("target_repo_hint", "")).strip()
        target = str(packet_payload.get("target", "")).strip()
        if target_repo_hint != "researcher-harness" and target != "researcher-harness":
            continue
        handoff_files.append(_render_packet_file(packet_path, output_root=destination_root))

    handoff_manifest_path = _write_manifest(
        output_root=destination_root,
        source_manifest_path=manifest_path,
        payload=payload,
        handoff_files=handoff_files,
    )

    return 0, envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "platform_root": platform_root.as_posix(),
            "materialized_manifest_path": manifest_path.as_posix(),
            "output_root": destination_root.as_posix(),
            "source_request_id": str(payload.get("source_request_id", "")).strip(),
            "source_question_id": str(payload.get("source_question_id", "")).strip(),
            "source_question_origin": str(payload.get("source_question_origin", "")).strip(),
            "handoff_manifest_path": handoff_manifest_path.as_posix(),
            "handoff_files": handoff_files,
            "next_action": "run_researcher_handoff_requests",
            "blockers": [],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--materialized-manifest-path", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    code, report = render_researcher_followup_handoffs(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
