from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.public_orchestration_api import API_VERSION
from platform_tools.render_researcher_followup_handoffs import render_researcher_followup_handoffs


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_render_researcher_followup_handoffs_blocks_on_missing_manifest(tmp_path: Path) -> None:
    code, report = render_researcher_followup_handoffs(
        root=tmp_path.as_posix(),
        materialized_manifest_path=(tmp_path / "missing.json").as_posix(),
        output_root=(tmp_path / "out").as_posix(),
    )

    assert code == 1
    assert report["api_version"] == API_VERSION
    assert report["command"] == "render-researcher-followup-handoffs"
    assert report["status"] == "blocked"
    assert "materialized_manifest_path_missing" in report["blockers"]


def test_render_researcher_followup_handoffs_writes_researcher_requests(tmp_path: Path) -> None:
    packet_path = tmp_path / "researcher-packet.json"
    _write(
        packet_path,
        json.dumps(
            {
                "request_kind": "repo_followup_request.v1",
                "request_packet_id": "researcher-harness-cand-02",
                "target_repo_hint": "researcher-harness",
                "target": "researcher-harness",
                "suggested_branch_hint": "feat/cand-02",
                "source_request_id": "req-1",
                "source_question_id": "q-1",
                "source_candidate_id": "cand-02",
                "source_hypothesis_ids": ["hyp-2"],
                "proposed_change": "Add a richer governed-research study plugin.",
                "expected_benefit": "Broader research coverage.",
                "delivery_mode": "repo_followup_request",
                "evidence_refs": ["https://example.com/b"],
                "linked_follow_up_questions": [{"question_id": "fup-2"}],
            }
        ),
    )
    ignored_packet = tmp_path / "other-packet.json"
    _write(
        ignored_packet,
        json.dumps(
            {
                "request_kind": "repo_followup_request.v1",
                "request_packet_id": "other-cand",
                "target_repo_hint": "other-repo",
                "target": "other-repo",
            }
        ),
    )
    manifest_path = tmp_path / "materialized.json"
    _write(
        manifest_path,
        json.dumps(
            {
                "api_version": API_VERSION,
                "source_command": "project-research-followup-packets",
                "source_request_id": "req-1",
                "source_question_id": "q-1",
                "source_question_origin": "user",
                "platform_seed_files": [],
                "repo_request_files": [
                    {"json_path": packet_path.as_posix()},
                    {"json_path": ignored_packet.as_posix()},
                ],
            }
        ),
    )

    code, report = render_researcher_followup_handoffs(
        root=tmp_path.as_posix(),
        materialized_manifest_path=manifest_path.as_posix(),
        output_root=(tmp_path / "out").as_posix(),
    )

    assert code == 0
    assert report["command"] == "render-researcher-followup-handoffs"
    assert report["status"] == "ok"
    assert len(report["handoff_files"]) == 1

    request_path = Path(report["handoff_files"][0]["request_path"])
    instructions_path = Path(report["handoff_files"][0]["instructions_path"])
    assert request_path.exists()
    assert instructions_path.exists()

    request_payload = json.loads(request_path.read_text(encoding="utf-8"))
    assert request_payload["study_design"] == "option-comparison"
    assert request_payload["question_origin"] == "platform"
    assert request_payload["improvement_targets"] == ["researcher-harness"]
    assert len(request_payload["options"]) == 2
    assert "researcher-harness" in instructions_path.read_text(encoding="utf-8")
