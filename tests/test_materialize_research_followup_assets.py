from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.materialize_research_followup_assets import materialize_research_followup_assets
from platform_tools.public_orchestration_api import API_VERSION


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_materialize_followup_assets_blocks_on_missing_packets(tmp_path: Path) -> None:
    code, report = materialize_research_followup_assets(
        root=tmp_path.as_posix(),
        packets_path=(tmp_path / "missing.json").as_posix(),
        output_root=(tmp_path / "out").as_posix(),
    )

    assert code == 1
    assert report["api_version"] == API_VERSION
    assert report["command"] == "materialize-research-followup-assets"
    assert report["status"] == "blocked"
    assert "packets_path_missing" in report["blockers"]


def test_materialize_followup_assets_blocks_on_invalid_payload(tmp_path: Path) -> None:
    packets_path = tmp_path / "packets.json"
    _write(packets_path, json.dumps({"source_command": "wrong"}))

    code, report = materialize_research_followup_assets(
        root=tmp_path.as_posix(),
        packets_path=packets_path.as_posix(),
        output_root=(tmp_path / "out").as_posix(),
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "packets_source_command_invalid" in report["blockers"]


def test_materialize_followup_assets_writes_platform_and_repo_assets(tmp_path: Path) -> None:
    packets_path = tmp_path / "packets.json"
    _write(
        packets_path,
        json.dumps(
            {
                "api_version": API_VERSION,
                "source_command": "prepare-research-followups",
                "source_request_id": "req-1",
                "source_question_id": "q-1",
                "source_question_origin": "user",
                "platform_execplan_seeds": [
                    {
                        "seed_id": "platform-seed-cand-01",
                        "title": "Promote ranked research candidate cand-01",
                        "initiative_branch": "initiative/research-control-plane",
                        "implementation_branch_hint": "impl-execplan/cand-01",
                        "source_request_id": "req-1",
                        "source_question_id": "q-1",
                        "source_candidate_id": "cand-01",
                        "proposed_change": "Prepare governed seed material.",
                        "expected_benefit": "Platform can route follow-up work.",
                        "evidence_refs": ["https://example.com/a"],
                        "linked_follow_up_questions": [{"question_id": "fup-1", "topic": "What next?"}],
                    }
                ],
                "repo_followup_requests": [
                    {
                        "request_packet_id": "researcher-harness-cand-02",
                        "target_repo_hint": "researcher-harness",
                        "target": "researcher-harness",
                        "suggested_branch_hint": "feat/cand-02",
                        "source_request_id": "req-1",
                        "source_question_id": "q-1",
                        "source_candidate_id": "cand-02",
                        "source_hypothesis_ids": ["hyp-2"],
                        "proposed_change": "Add a new plugin.",
                        "expected_benefit": "Broader research coverage.",
                        "delivery_mode": "repo_followup_request",
                        "evidence_refs": ["https://example.com/b"],
                        "linked_follow_up_questions": [{"question_id": "fup-2"}],
                    }
                ],
            }
        ),
    )

    code, report = materialize_research_followup_assets(
        root=tmp_path.as_posix(),
        packets_path=packets_path.as_posix(),
        output_root=(tmp_path / "out").as_posix(),
    )

    assert code == 0
    assert report["api_version"] == API_VERSION
    assert report["command"] == "materialize-research-followup-assets"
    assert report["status"] == "ok"
    assert report["source_request_id"] == "req-1"
    assert len(report["platform_seed_files"]) == 1
    assert len(report["repo_request_files"]) == 1

    manifest_path = Path(report["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["source_request_id"] == "req-1"

    seed_json_path = Path(report["platform_seed_files"][0]["json_path"])
    seed_md_path = Path(report["platform_seed_files"][0]["markdown_path"])
    repo_json_path = Path(report["repo_request_files"][0]["json_path"])
    assert seed_json_path.exists()
    assert seed_md_path.exists()
    assert repo_json_path.exists()

    repo_payload = json.loads(repo_json_path.read_text(encoding="utf-8"))
    assert repo_payload["request_kind"] == "repo_followup_request.v1"
    assert repo_payload["target_repo_hint"] == "researcher-harness"
