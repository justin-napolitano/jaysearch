from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.project_research_followup_packets import project_research_followup_packets
from platform_tools.public_orchestration_api import API_VERSION


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_project_followup_packets_blocks_on_missing_input(tmp_path: Path) -> None:
    code, report = project_research_followup_packets(
        root=tmp_path.as_posix(),
        prepared_followups_path=(tmp_path / "missing.json").as_posix(),
        output_root=(tmp_path / "out").as_posix(),
    )

    assert code == 1
    assert report["api_version"] == API_VERSION
    assert report["command"] == "project-research-followup-packets"
    assert report["status"] == "blocked"
    assert "prepared_followups_path_missing" in report["blockers"]


def test_project_followup_packets_blocks_on_invalid_payload(tmp_path: Path) -> None:
    prepared_path = tmp_path / "prepared.json"
    _write(prepared_path, json.dumps({"source_command": "wrong", "draft_followup_inputs": []}))

    code, report = project_research_followup_packets(
        root=tmp_path.as_posix(),
        prepared_followups_path=prepared_path.as_posix(),
        output_root=(tmp_path / "out").as_posix(),
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "prepared_followups_source_command_invalid" in report["blockers"]


def test_project_followup_packets_emits_platform_and_repo_packets(tmp_path: Path) -> None:
    prepared_path = tmp_path / "prepared.json"
    _write(
        prepared_path,
        json.dumps(
            {
                "api_version": API_VERSION,
                "source_command": "run-research-capability",
                "source_request_id": "req-1",
                "source_question_id": "q-1",
                "source_question_origin": "user",
                "draft_followup_inputs": [
                    {
                        "source_request_id": "req-1",
                        "source_question_id": "q-1",
                        "source_candidate_id": "cand-01",
                        "target": "platform-control-plane",
                        "target_repo_hint": "codex_platform",
                        "proposed_change": "Prepare governed seed material.",
                        "expected_benefit": "Platform can route follow-up work.",
                        "delivery_mode": "governed_execplan",
                        "evidence_refs": ["https://example.com/a"],
                        "linked_follow_up_questions": [{"question_id": "fup-1"}],
                        "suggested_execplan_seed": {
                            "title": "Promote ranked research candidate cand-01",
                            "initiative_branch": "initiative/research-control-plane",
                            "implementation_branch_hint": "impl-execplan/cand-01",
                        },
                    },
                    {
                        "source_request_id": "req-1",
                        "source_question_id": "q-1",
                        "source_candidate_id": "cand-02",
                        "target": "researcher-harness",
                        "target_repo_hint": "researcher-harness",
                        "source_hypothesis_ids": ["hyp-2"],
                        "proposed_change": "Add a new plugin.",
                        "expected_benefit": "Broader research coverage.",
                        "delivery_mode": "repo_followup_request",
                        "evidence_refs": ["https://example.com/b"],
                        "linked_follow_up_questions": [{"question_id": "fup-2"}],
                    },
                ],
            }
        ),
    )

    code, report = project_research_followup_packets(
        root=tmp_path.as_posix(),
        prepared_followups_path=prepared_path.as_posix(),
        output_root=(tmp_path / "out").as_posix(),
    )

    assert code == 0
    assert report["api_version"] == API_VERSION
    assert report["command"] == "project-research-followup-packets"
    assert report["status"] == "ok"
    assert report["source_request_id"] == "req-1"
    assert len(report["platform_execplan_seeds"]) == 1
    assert report["platform_execplan_seeds"][0]["source_candidate_id"] == "cand-01"
    assert len(report["repo_followup_requests"]) == 1
    assert report["repo_followup_requests"][0]["target_repo_hint"] == "researcher-harness"

    packets_path = Path(report["packets_path"])
    payload = json.loads(packets_path.read_text(encoding="utf-8"))
    assert payload["source_request_id"] == "req-1"
    assert payload["platform_execplan_seeds"][0]["initiative_branch"] == "initiative/research-control-plane"
    assert payload["repo_followup_requests"][0]["suggested_branch_hint"] == "feat/cand-02"
