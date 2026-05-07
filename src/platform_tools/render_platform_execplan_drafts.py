from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import API_VERSION, envelope


COMMAND = "render-platform-execplan-drafts"


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


def _render_draft_markdown(seed: dict[str, Any]) -> str:
    linked_questions = seed.get("linked_follow_up_questions", [])
    if not isinstance(linked_questions, list):
        linked_questions = []
    evidence_refs = seed.get("evidence_refs", [])
    if not isinstance(evidence_refs, list):
        evidence_refs = []
    lines = [
        f"# Draft ExecPlan Candidate: {str(seed.get('title', '')).strip() or str(seed.get('seed_id', '')).strip()}",
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
    lines.extend(
        [
            "",
            "## Drafting Notes",
            "- This artifact is non-authoritative seed material.",
            "- Promote it into a real ExecPlan only after governed review.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_draft_payload(seed: dict[str, Any]) -> dict[str, Any]:
    return {
        "draft_kind": "platform_execplan_candidate.v1",
        "seed_id": str(seed.get("seed_id", "")).strip(),
        "title": str(seed.get("title", "")).strip(),
        "initiative_branch": str(seed.get("initiative_branch", "")).strip(),
        "implementation_branch_hint": str(seed.get("implementation_branch_hint", "")).strip(),
        "source_request_id": str(seed.get("source_request_id", "")).strip(),
        "source_question_id": str(seed.get("source_question_id", "")).strip(),
        "source_candidate_id": str(seed.get("source_candidate_id", "")).strip(),
        "proposed_change": str(seed.get("proposed_change", "")).strip(),
        "expected_benefit": str(seed.get("expected_benefit", "")).strip(),
        "evidence_refs": [str(item).strip() for item in seed.get("evidence_refs", []) if str(item).strip()]
        if isinstance(seed.get("evidence_refs"), list)
        else [],
        "linked_follow_up_questions": seed.get("linked_follow_up_questions", [])
        if isinstance(seed.get("linked_follow_up_questions"), list)
        else [],
    }


def _render_seed_file(seed_path: Path, *, output_root: Path) -> dict[str, str]:
    seed = _load_json_file(seed_path)
    seed_id = str(seed.get("seed_id", "")).strip() or seed_path.stem
    json_path = output_root / "execution" / "draft_execplan_candidates" / f"{seed_id}.json"
    markdown_path = output_root / "execution" / "draft_execplan_candidates" / f"{seed_id}.md"
    _write_json(json_path, _render_draft_payload(seed))
    _write_text(markdown_path, _render_draft_markdown(seed))
    return {
        "seed_id": seed_id,
        "source_seed_path": seed_path.as_posix(),
        "draft_json_path": json_path.as_posix(),
        "draft_markdown_path": markdown_path.as_posix(),
    }


def _write_manifest(
    *,
    output_root: Path,
    source_manifest_path: Path,
    payload: dict[str, Any],
    draft_files: list[dict[str, str]],
) -> Path:
    manifest = {
        "api_version": API_VERSION,
        "source_command": "materialize-research-followup-assets",
        "source_manifest_path": source_manifest_path.as_posix(),
        "source_request_id": str(payload.get("source_request_id", "")).strip(),
        "source_question_id": str(payload.get("source_question_id", "")).strip(),
        "source_question_origin": str(payload.get("source_question_origin", "")).strip(),
        "draft_files": draft_files,
    }
    path = output_root / "execution" / "draft_execplan_candidates" / f"{manifest['source_request_id']}.manifest.json"
    return _write_json(path, manifest)


def render_platform_execplan_drafts(
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
    if not blockers:
        try:
            payload = _load_json_file(manifest_path)
        except (OSError, ValueError, json.JSONDecodeError):
            blockers.append("materialized_manifest_payload_invalid")

    if payload:
        if str(payload.get("source_command", "")).strip() != "project-research-followup-packets":
            blockers.append("materialized_manifest_source_command_invalid")
        if not isinstance(payload.get("platform_seed_files", []), list):
            blockers.append("materialized_manifest_missing_platform_seed_files")

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

    draft_files = []
    for item in payload.get("platform_seed_files", []):
        if not isinstance(item, dict):
            continue
        seed_json_path = str(item.get("json_path", "")).strip()
        if not seed_json_path:
            continue
        draft_files.append(_render_seed_file(Path(seed_json_path), output_root=destination_root))

    draft_manifest_path = _write_manifest(
        output_root=destination_root,
        source_manifest_path=manifest_path,
        payload=payload,
        draft_files=draft_files,
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
            "draft_manifest_path": draft_manifest_path.as_posix(),
            "draft_files": draft_files,
            "next_action": "review_draft_execplan_candidates",
            "blockers": [],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--materialized-manifest-path", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    code, report = render_platform_execplan_drafts(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
