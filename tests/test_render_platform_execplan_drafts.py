from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.public_orchestration_api import API_VERSION
from platform_tools.render_platform_execplan_drafts import render_platform_execplan_drafts


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_render_platform_execplan_drafts_blocks_on_missing_manifest(tmp_path: Path) -> None:
    code, report = render_platform_execplan_drafts(
        root=tmp_path.as_posix(),
        materialized_manifest_path=(tmp_path / "missing.json").as_posix(),
        output_root=(tmp_path / "out").as_posix(),
    )

    assert code == 1
    assert report["api_version"] == API_VERSION
    assert report["command"] == "render-platform-execplan-drafts"
    assert report["status"] == "blocked"
    assert "materialized_manifest_path_missing" in report["blockers"]


def test_render_platform_execplan_drafts_blocks_on_invalid_manifest(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    _write(manifest_path, json.dumps({"source_command": "wrong"}))

    code, report = render_platform_execplan_drafts(
        root=tmp_path.as_posix(),
        materialized_manifest_path=manifest_path.as_posix(),
        output_root=(tmp_path / "out").as_posix(),
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "materialized_manifest_source_command_invalid" in report["blockers"]


def test_render_platform_execplan_drafts_writes_draft_files(tmp_path: Path) -> None:
    seed_path = tmp_path / "seed.json"
    _write(
        seed_path,
        json.dumps(
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
                "platform_seed_files": [
                    {
                        "seed_id": "platform-seed-cand-01",
                        "json_path": seed_path.as_posix(),
                        "markdown_path": (tmp_path / "seed.md").as_posix(),
                    }
                ],
                "repo_request_files": [],
            }
        ),
    )

    code, report = render_platform_execplan_drafts(
        root=tmp_path.as_posix(),
        materialized_manifest_path=manifest_path.as_posix(),
        output_root=(tmp_path / "out").as_posix(),
    )

    assert code == 0
    assert report["api_version"] == API_VERSION
    assert report["command"] == "render-platform-execplan-drafts"
    assert report["status"] == "ok"
    assert report["source_request_id"] == "req-1"
    assert len(report["draft_files"]) == 1

    draft_manifest_path = Path(report["draft_manifest_path"])
    draft_manifest = json.loads(draft_manifest_path.read_text(encoding="utf-8"))
    assert draft_manifest["source_request_id"] == "req-1"

    draft_json_path = Path(report["draft_files"][0]["draft_json_path"])
    draft_md_path = Path(report["draft_files"][0]["draft_markdown_path"])
    assert draft_json_path.exists()
    assert draft_md_path.exists()
    assert "Promote ranked research candidate cand-01" in draft_md_path.read_text(encoding="utf-8")
